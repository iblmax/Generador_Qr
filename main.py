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
def generar_imagen_marcado(texto_qr, texto_lateral=None, resolucion=1000):
    """Genera la imagen en blanco y negro optimizada para la L4Pro."""
    # El lienzo siempre es cuadrado según las especificaciones del láser
    ancho_total = resolucion
    alto_total = resolucion
    
    # Márgenes y tamaños proporcionales a la resolución elegida
    margen = int(resolucion * 0.05)       # 5% de la resolución
    ancho_qr = (ancho_total // 2) - (2 * margen)
    ancho_texto = ancho_total - ancho_qr - (3 * margen)

    # Configuración del QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=int(resolucion * 0.015), # Escala el tamaño del punto del QR
        border=4,
    )
    qr.add_data(texto_qr)
    qr.make(fit=True)
    img_qr_pil = qr.make_image(fill_color="black", back_color="white").convert('L')
    img_qr_pil = img_qr_pil.resize((ancho_qr, ancho_qr), resample=Image.NEAREST)

    # Lienzo final en escala de grises (255 = Blanco)
    imagen_final = Image.new('L', (ancho_total, alto_total), color=255)
    imagen_final.paste(img_qr_pil, (margen, margen))

    # Renderizado del texto lateral
    if texto_lateral:
        draw = ImageDraw.Draw(imagen_final)
        
        # Tamaño de fuente proporcional a la resolución
        tamanio_fuente = int(resolucion * 0.055)
        line_height = int(tamanio_fuente * 1.3)
        
        try:
            font_path = "arial.ttf" 
            font = ImageFont.truetype(font_path, size=tamanio_fuente)
        except IOError:
            font = ImageFont.load_default()

        # --- CORRECCIÓN AQUÍ: Reemplazamos saltos de línea por espacios para medir correctamente ---
        texto_limpio = texto_lateral.replace('\n', ' ').replace('\r', ' ')
        
        # Ajuste de línea automático (Word Wrap)
        lines = []
        words = texto_limpio.split(' ')
        current_line = []
        for word in words:
            if not word: # Evita espacios dobles vacíos
                continue
            test_line = ' '.join(current_line + [word])
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

        for line in lines:
            draw.text((x_texto, y_texto), line, fill=0, font=font)
            y_texto += line_height

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