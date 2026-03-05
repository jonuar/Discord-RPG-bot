import unicodedata
from PIL import Image
import os
import tempfile
import uuid

def quitar_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def obtener_imagen_raza(raza):
    return f"assets/raza_{quitar_acentos(raza.lower())}.png"

def obtener_imagen_clase(clase):
    return f"assets/clase_{quitar_acentos(clase.lower())}.png"

def _guardar_temp_png(img, prefix):
    temp_dir = tempfile.gettempdir()
    nombre = f"{prefix}_{uuid.uuid4().hex}.png"
    ruta = os.path.join(temp_dir, nombre)
    img.save(ruta)
    return ruta

def borrar_temp(ruta):
    try:
        os.remove(ruta)
    except FileNotFoundError:
        pass

def combinar_tres_horizontal(ruta1, ruta2, ruta3, alto):
    imgs = [Image.open(ruta).convert("RGBA") for ruta in [ruta1, ruta2, ruta3]]
    imgs = [img.resize((int(img.width * alto / img.height), alto)) for img in imgs]
    ancho_total = sum(img.width for img in imgs)
    nueva = Image.new('RGBA', (ancho_total, alto))
    x = 0
    for img in imgs:
        nueva.paste(img, (x, 0), img)
        x += img.width
    nueva_ruta = _guardar_temp_png(nueva, "duelo_versus")
    return nueva_ruta

def combinar_imagenes_misma_altura(ruta1, ruta2, alto):
    img1 = Image.open(ruta1)
    img2 = Image.open(ruta2)
    proporcion1 = alto / img1.height
    ancho1 = int(img1.width * proporcion1)
    img1 = img1.resize((ancho1, alto))

    proporcion2 = alto / img2.height
    ancho2 = int(img2.width * proporcion2)
    img2 = img2.resize((ancho2, alto))

    nueva = Image.new('RGBA', (ancho1 + ancho2, alto))
    nueva.paste(img1, (0, 0))
    nueva.paste(img2, (ancho1, 0))
    nueva_ruta = _guardar_temp_png(nueva, "combinada")
    return nueva_ruta

def redimensionar_por_alto(ruta, alto=100):
    img = Image.open(ruta)
    proporcion = alto / img.height
    ancho = int(img.width * proporcion)
    img = img.resize((ancho, alto))
    nueva_ruta = _guardar_temp_png(img, f"temp_{ruta.replace('/', '_')}")
    return nueva_ruta