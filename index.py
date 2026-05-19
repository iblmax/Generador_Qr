import os
import qrcode
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from tkinter import messagebox, ttk

# --- FUNCIONES DE LÓGICA DE IMAGEN ---

def generar_imagen_marcado(texto_qr, texto_abajo=None, resolucion=1000):
    """Genera la imagen optimizada para la L4Pro con el QR arriba y el texto gigante centrado abajo."""
    # El lienzo siempre es cuadrado según las especificaciones del láser
    ancho_total = resolucion
    alto_total = resolucion
    
    # --- CONFIGURACIÓN DEL QR ---
    # Usamos versión 2 y corrección L para bloques grandes (máxima velocidad de marcado)
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=int(resolucion * 0.015), 
        border=1, # Menor borde para aprovechar más el espacio
    )
    qr.add_data(texto_qr)
    qr.make(fit=True)

    # Generar el QR directamente en escala de grises ('L') para evitar errores de conversión
    img_qr_pil = qr.make_image(fill_color="black", back_color="white").convert("L")
    
    # El QR ocupará el 75% del alto total del lienzo cuadrado
    alto_destinado_qr = int(alto_total * 0.75)
    img_qr_pil = img_qr_pil.resize((alto_destinado_qr, alto_destinado_qr), resample=Image.NEAREST)
    
    # Lienzo final en escala de grises (255 = Blanco)
    imagen_final = Image.new('L', (ancho_total, alto_total), color=255)
    
    # Centrar el QR horizontalmente en la parte superior
    x_qr = (ancho_total - alto_destinado_qr) // 2
    y_qr = int(alto_total * 0.02) # Un pequeño margen del 2% arriba
    imagen_final.paste(img_qr_pil, (x_qr, y_qr))

    # --- RENDERIZADO DEL TEXTO GIGANTE ABAJO ---
    if texto_abajo:
        draw = ImageDraw.Draw(imagen_final)
        
        # Súper fuente: 11% de la resolución total (alrededor de 110px si la resolución es 1000)
        # Esto hace que el texto sea masivo y ultra legible para el operador
        tamanio_fuente = int(resolucion * 0.11)
        
        try:
            font_path = "arial.ttf" 
            font = ImageFont.truetype(font_path, size=tamanio_fuente)
        except IOError:
            font = ImageFont.load_default()

        # Limpiamos el texto eliminando saltos de línea innecesarios
        texto_limpio = texto_abajo.replace('\n', ' ').replace('\r', ' ').strip()
        
        # Calcular el tamaño exacto del texto para centrarlo perfectamente
        try:
            bbox = draw.textbbox((0, 0), texto_limpio, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            # Soporte para versiones antiguas de Pillow
            text_width, text_height = font.getsize(texto_limpio)

        # Posición X: Centrado matemático horizontal
        x_texto = (ancho_total - text_width) // 2
        
        # Posición Y: En el centro del 25% de espacio restante abajo
        espacio_restante_y = alto_total - (y_qr + alto_destinado_qr)
        y_texto = (y_qr + alto_destinado_qr) + (espacio_restante_y - text_height) // 2 - int(resolucion * 0.02)

        # Dibujar el texto en negro puro (0)
        draw.text((x_texto, y_texto), texto_limpio, fill=0, font=font)

    return imagen_final
# --- FUNCIÓN DEL BOTÓN GENERAR ---

def procesar_y_guardar():
    t_qr = entry_qr.get().strip()
    t_lat = entry_lateral.get("1.0", tk.END).strip()
    formato = combo_formato.get()
    nombre_archivo = entry_nombre.get().strip()

    # Validaciones básicas
    if not t_qr:
        messagebox.showerror("Error", "El texto para el código QR es obligatorio.")
        return
    if not nombre_archivo:
        messagebox.showerror("Error", "Debes asignarle un nombre al archivo.")
        return

    try:
        # Forzar que se guarde en la carpeta 'qr' relativa a la ubicación del script
        ruta_carpeta = os.path.join(os.path.dirname(__file__), 'qr')
        
        # Si por alguna razón no existe la carpeta 'qr', el programa la crea sola
        if not os.path.exists(ruta_carpeta):
            os.makedirs(ruta_carpeta)

        # Definir la ruta completa del archivo final
        extension = f".{formato.lower()}"
        ruta_final = os.path.join(ruta_carpeta, f"{nombre_archivo}{extension}")

        # Generar la imagen con la lógica previa
        img = generar_imagen_marcado(t_qr, t_lat if t_lat else None)

        # Ajuste de guardado según formato para compatibilidad con la pistola L4Pro
        if formato in ["JPG", "JPEG"]:
            img_guardar = img.convert("RGB")
            img_guardar.save(ruta_final, "JPEG", quality=100)
        elif formato == "PNG":
            img.save(ruta_final, "PNG")
        elif formato == "BMP":
            img.save(ruta_final, "BMP")

        messagebox.showinfo("¡Éxito!", f"Imagen guardada correctamente en:\n{ruta_final}")
        
        # Limpiar campos después de guardar (Opcional, para el siguiente tanque)
        entry_qr.delete(0, tk.END)
        entry_lateral.delete("1.0", tk.END)
        entry_nombre.delete(0, tk.END)

    except Exception as e:
        messagebox.showerror("Error inesperado", f"No se pudo guardar la imagen: {e}")


# --- DISEÑO DE INTERFAZ GRÁFICA (TKINTER) ---

root = tk.Tk()
root.title("Generador de Códigos - Láser L4Pro")
root.geometry("460x520")
root.resizable(False, False)

# Estilos limpios usando ttk
style = ttk.Style()
style.theme_use('clam')

frame = ttk.Frame(root, padding="20")
frame.pack(fill=tk.BOTH, expand=True)

# Título
lbl_titulo = ttk.Label(frame, text="Configuración de Marcado", font=("Arial", 14, "bold"))
lbl_titulo.pack(pady=(0, 15))

# Campo 1: Texto QR
lbl_qr = ttk.Label(frame, text="Texto o Código para el QR (Obligatorio):", font=("Arial", 10, "bold"))
lbl_qr.pack(anchor=tk.W, pady=(5, 2))
entry_qr = ttk.Entry(frame, width=50)
entry_qr.pack(fill=tk.X, pady=(0, 10))

# Campo 2: Texto Lateral
lbl_lateral = ttk.Label(frame, text="Texto Lateral (Información del Tanque):", font=("Arial", 10, "bold"))
lbl_lateral.pack(anchor=tk.W, pady=(5, 2))
entry_lateral = tk.Text(frame, width=50, height=4, font=("Arial", 10))
entry_lateral.pack(fill=tk.X, pady=(0, 10))

# Campo 3: Nombre del archivo de salida
lbl_nombre = ttk.Label(frame, text="Nombre del archivo a guardar (sin extensión):", font=("Arial", 10, "bold"))
lbl_nombre.pack(anchor=tk.W, pady=(5, 2))
entry_nombre = ttk.Entry(frame, width=50)
entry_nombre.pack(fill=tk.X, pady=(0, 10))

# Campo 4: Selector de Formato
lbl_formato = ttk.Label(frame, text="Formato de Imagen para la Pistola:", font=("Arial", 10, "bold"))
lbl_formato.pack(anchor=tk.W, pady=(5, 2))
combo_formato = ttk.Combobox(frame, values=["BMP", "PNG", "JPG"], state="readonly") 