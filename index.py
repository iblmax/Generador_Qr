import os
import qrcode
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from tkinter import messagebox, ttk

# --- FUNCIONES DE LÓGICA DE IMAGEN ---

def generar_imagen_marcado(texto_qr, texto_lateral=None):
    """Genera la imagen en blanco y negro optimizada para la L4Pro."""
    ancho_total = 1000
    alto_total = 1000
    margen = 50
    ancho_qr = (ancho_total // 2) - (2 * margen)
    ancho_texto = ancho_total - ancho_qr - (3 * margen)

    # Configuración del QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=15,
        border=4,
    )
    qr.add_data(texto_qr)
    qr.make(fit=True)
    img_qr_pil = qr.make_image(fill_color="black", back_color="white").convert('L')
    img_qr_pil = img_qr_pil.resize((ancho_qr, ancho_qr), resample=Image.NEAREST)

    # Lienzo final en escala de grises (255 = Blanco)
    imagen_final = Image.new('L', (ancho_total, alto_total), color=255)
    imagen_final.paste(img_qr_pil, (margen, margen))

    # Renderizado del texto lateral si existe
    if texto_lateral:
        draw = ImageDraw.Draw(imagen_final)
        try:
            # Buscando fuentes estándar del sistema
            font_path = "arial.ttf" 
            font = ImageFont.truetype(font_path, size=55)
        except IOError:
            font = ImageFont.load_default()

        # Ajuste de línea automático (Word Wrap)
        lines = []
        words = texto_lateral.split(' ')
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            # Compatibilidad con versiones de Pillow antiguas y nuevas
            try:
                w = draw.textlength(test_line, font=font)
            except AttributeError:
                w = font.getsize(test_line)[0]

            if w <= ancho_texto:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))

        # Dibujar texto
        x_texto = ancho_qr + (2 * margen)
        y_texto = margen
        line_height = 70 

        for line in lines:
            draw.text((x_texto, y_texto), line, fill=0, font=font)
            y_texto += line_height

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