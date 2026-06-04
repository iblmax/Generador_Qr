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
def generar_imagen_marcado(texto_qr, texto_abajo=None, resolucion=472):
    """
    Genera una imagen de 472x472 px, que a 300 DPI equivale exactamente 
    a 4 cm x 4 cm físicos, optimizada con fondo blanco real para la L4Pro.
    """
    # Forzamos a que el lienzo sea de 472x472 píxeles (4cm x 4cm)
    ancho_total = 472
    alto_total = 472
    
    # 1. LIENZO CON FONDO BLANCO PURO REAL ('L' = 255 es blanco, sin transparencias)
    imagen_final = Image.new('L', (ancho_total, alto_total), color=255)
    
    # 2. CONFIGURACIÓN DEL QR
    qr = qrcode.QRCode(
        version=None, # Calcula automáticamente el tamaño según el texto
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,   # Bloques más pequeños para que quepa bien en 4 cm
        border=1,     # Borde mínimo para aprovechar el espacio de 4 cm
    )
    qr.add_data(texto_qr)
    qr.make(fit=True)

    # Generar el QR en blanco y negro puro
    img_qr_pil = qr.make_image(fill_color="black", back_color="white").convert("L")
    
    # El QR ocupará el 65% del espacio vertical (unos 300 px) para dejar espacio abajo
    tamano_qr = int(alto_total * 0.65)
    img_qr_pil = img_qr_pil.resize((tamano_qr, tamano_qr), resample=Image.NEAREST)
    
    # Centrar el QR horizontalmente en la mitad superior
    x_qr = (ancho_total - tamano_qr) // 2
    y_qr = int(alto_total * 0.05) # Margen superior del 5%
    imagen_final.paste(img_qr_pil, (x_qr, y_qr))

    # 3. RENDERIZADO DEL TEXTO INFERIOR
    if texto_abajo:
        draw = ImageDraw.Draw(imagen_final)
        
        # Tamaño de fuente proporcional para el lienzo de 4cm (aprox. 45px de alto)
        tamanio_fuente = int(resolucion * 0.095)
        
        try:
            font_path = "arial.ttf" 
            font = ImageFont.truetype(font_path, size=tamanio_fuente)
        except IOError:
            font = ImageFont.load_default()

        # Limpiar saltos de línea para que entre en una sola tira horizontal
        texto_limpio = texto_abajo.replace('\n', ' ').replace('\r', ' ').strip()
        
        # Calcular dimensiones exactas para el centrado
        try:
            bbox = draw.textbbox((0, 0), texto_limpio, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            text_width, text_height = font.getsize(texto_limpio)

        # Reducir la fuente dinámicamente si el texto es muy largo para los 4 cm
        while text_width > (ancho_total * 0.95) and tamanio_fuente > 12:
            tamanio_fuente -= 2
            try:
                font = ImageFont.truetype("arial.ttf", size=tamanio_fuente)
                bbox = draw.textbbox((0, 0), texto_limpio, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                break

        # Posición X: Centrado matemático absoluto
        x_texto = (ancho_total - text_width) // 2
        
        # Posición Y: Ubicado firmemente en el espacio inferior restante
        y_texto = int(alto_total * 0.76) 

        # Dibujar el texto en negro puro (0) sobre el fondo blanco
        draw.text((x_texto, y_texto), texto_limpio, fill=0, font=font)

    return imagen_final








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