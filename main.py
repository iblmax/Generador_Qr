import os
import io
import qrcode
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Generador de QR - Láser L4Pro",
    page_icon="⚡",
    layout="centered"
)

# --- LÓGICA DE GENERACIÓN DE IMAGEN ---
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
# --- INTERFAZ DE USUARIO (STREAMLIT) ---

st.title("⚡ Generador de Códigos para L4Pro")
st.subheader("Configuración de Marcado de Tanques Especiales")
st.write("Configura el tamaño y formato antes de exportar el diseño a la pistola industrial.")

# Formulario de entrada de datos
with st.form("generador_form"):
    t_qr = st.text_input("Texto o Código para el QR (Obligatorio):", placeholder="Ej. LOTE-2026-A")
    t_lat = st.text_area("Texto Lateral (Información del Tanque):", placeholder="Ej. VINA MARCA TANQUE\nCODI: 1234\nFECHA: 2026-05-19")
    nombre_archivo = st.text_input("Nombre del archivo (sin extensión):", value="codigo_marcado")
    
    # NUEVA MEJORA: Selección de área de marcado y resolución
    opcion_tamano = st.radio(
        "Dimensiones del área de grabado:",
        [
            "Estándar (Área común: 50mm x 50mm | Resolución: 1000 x 1000 px)",
            "Recomendado (Alta definición: 100mm x 100mm | Resolución: 2000 x 2000 px)"
        ]
    )
    
    # Selectbox con los formatos solicitados (Formatos limpios de imagen)
    formato = st.selectbox("Formatos de Imagen compatibles:", ["BMP", "PNG", "JPG", "JPEG"])
    
    # Botón del formulario
    submitted = st.form_submit_button("Generar Diseño Optimizado")

# Procesamiento cuando se presiona el botón
if submitted:
    if not t_qr:
        st.error("❌ El texto para el código QR es obligatorio.")
    elif not nombre_archivo:
        st.error("❌ Debes asignarle un nombre al archivo.")
    else:
        # Definir los píxeles según la opción seleccionada
        res_elegida = 1000 if "Estándar" in opcion_tamano else 2000
        
        # Generar la imagen con la resolución dinámica
        img_resultado = generar_imagen_marcado(t_qr, t_lat if t_lat else None, resolucion=res_elegida)
        
        # Mostrar vista previa en la página web
        st.write("### 👁️ Vista Previa del Marcado:")
        # Reducimos visualmente el ancho en la web para que no ocupe toda la pantalla, pero el archivo mantendrá sus px reales
        st.image(img_resultado, caption=f"Lienzo Cuadrado configurado a {res_elegida}x{res_elegida}px", width=350)
        
        # 1. Guardar automáticamente en la carpeta local '/qr' del proyecto
        try:
            ruta_carpeta = os.path.join(os.path.dirname(__file__), 'qr')
            if not os.path.exists(ruta_carpeta):
                os.makedirs(ruta_carpeta)
                
            extension = f".{formato.lower()}"
            ruta_final = os.path.join(ruta_carpeta, f"{nombre_archivo}{extension}")
            
            if formato in ["JPG", "JPEG"]:
                img_guardar = img_resultado.convert("RGB")
                img_guardar.save(ruta_final, "JPEG", quality=100)
            else:
                img_resultado.save(ruta_final, formato)
                
            st.success(f"💾 Archivo de alta claridad guardado localmente en: `{ruta_final}`")
        except Exception as e:
            st.warning(f"No se pudo escribir automáticamente en el directorio local: {e}")

        # 2. Habilitar botón de descarga directa desde el navegador
        buffer = io.BytesIO()
        if formato in ["JPG", "JPEG"]:
            img_resultado.convert("RGB").save(buffer, format="JPEG")
            mime_type = "image/jpeg"
        else:
            img_resultado.save(buffer, format=formato)
            mime_type = f"image/{formato.lower()}"
            
        st.download_button(
            label=f"📥 Descargar Archivo .{formato} ({res_elegida}x{res_elegida} px)",
            data=buffer.getvalue(),
            file_name=f"{nombre_archivo}.{formato.lower()}",
            mime=mime_type
        )