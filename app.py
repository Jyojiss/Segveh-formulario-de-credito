# app.py
from pathlib import Path
from fastapi import FastAPI, Request, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader, PdfWriter, PageObject
from PIL import Image
import io, os

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
env = Environment(loader=FileSystemLoader("."))

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_PDF = BASE_DIR / "plantillas" / "SOLICITUD_DE_CREDITO_SEGV_PN.pdf"

if not TEMPLATE_PDF.exists():
    raise FileNotFoundError(f"No existe la plantilla: {TEMPLATE_PDF}")

OUT_DIR = BASE_DIR / "salidas"
os.makedirs(OUT_DIR, exist_ok=True)

# =========================
# MAPEO DE CAMPOS -> X/Y
# =========================
FIELD_MAP = {
    # ===== ENCABEZADO / META =====
    "vitrina_asesor":            {"page": 0, "x": 105,  "y": 785},
    "cc_asesor":                 {"page": 0, "x": 210, "y": 785},
    "fecha_rad":                 {"page": 0, "x": 308, "y": 785},  # dd/mm/aaaa

    "linea_financiacion":        {"page": 0, "x": 100,  "y": 771},  # Vehiculo/Motos/Poliza/Otros
    "tipo_solicitante":          {"page": 0, "x": 440, "y": 771},  # Deudor/Codeudor

    "tipo_bien":                 {"page": 0, "x": 35,  "y": 380},
    "direccion_servicio":        {"page": 0, "x": 210, "y": 380},
    "vr_comercial_bien":         {"page": 0, "x": 380, "y": 380},

    # ===== IDENTIFICACIÓN SOLICITANTE =====
    "apellidos_nombres":         {"page": 0, "x": 35,  "y": 708},
    "tipo_id":                   {"page": 0, "x": 390, "y": 708},
    "numero_id":                 {"page": 0, "x": 430, "y": 708},

    "fecha_expedicion":          {"page": 0, "x": 85, "y": 690},
    "ciudad_expedicion":         {"page": 0, "x": 135, "y": 690},

    "fecha_nac":                 {"page": 0, "x": 265, "y": 690},
    "ciudad_nac":                {"page": 0, "x": 314, "y": 690},

    "sexo":                      {"page": 0, "x": 310,  "y": 708},
    "nacionalidad":              {"page": 0, "x": 380, "y": 690},
    "estado_civil":              {"page": 0, "x": 459, "y": 690},
    "nivel_estudios":            {"page": 0, "x": 35, "y": 675},

    "tipo_vivienda":             {"page": 0, "x": 380,  "y": 675},
    "personas_a_cargo":          {"page": 0, "x": 460, "y": 675},

    "direccion":                 {"page": 0, "x": 35,  "y": 657},
    "ciudad":                    {"page": 0, "x": 310, "y": 657},

    "celular":                   {"page": 0, "x": 210,  "y": 675},
    "email":                     {"page": 0, "x": 380, "y": 657},

    # ===== ACTIVIDAD ECONÓMICA =====
    "actividad_economica":       {"page": 0, "x": 35,  "y": 570},
    "empresa":                   {"page": 0, "x": 210, "y": 570},
    "cargo":                     {"page": 0, "x": 380, "y": 535},
    "tipo_contrato":             {"page": 0, "x": 460, "y": 535},
    "antiguedad":                {"page": 0, "x": 460, "y": 553},
    "ingresos_mensuales":        {"page": 0, "x": 460, "y": 623},
    "otros_ingresos":            {"page": 0, "x": 210, "y": 415},
    "pep":                       {"page": 0, "x": 338, "y": 520},

    # ===== VEHÍCULO / SERVICIO =====
    "marca":                     {"page": 0, "x": 35,  "y": 750},
    "linea":                     {"page": 0, "x": 105, "y": 750},
    "tipo_servicio":             {"page": 0, "x": 210, "y": 750},
    "modelo":                    {"page": 0, "x": 308, "y": 750},

    "estado_bien":               {"page": 0, "x": 380, "y": 757},
    "plazo":                     {"page": 0, "x": 505, "y": 757},
    "vr_comercial":              {"page": 0, "x": 395, "y": 745},
    "vr_financiacion":           {"page": 0, "x": 502, "y": 745},

    # ===== INFORMACIÓN CÓNYUGE =====
    "conyuge_nombre":            {"page": 0, "x": 210, "y": 640},
    "conyuge_tipo_id":           {"page": 0, "x": 45, "y": 621},
    "conyuge_numero_id":         {"page": 0, "x": 80, "y": 621},
    "conyuge_celular":           {"page": 0, "x": 55, "y": 605},

    # ===== INGRESOS Y EGRESOS =====
    "sueldo_basico":             {"page": 0, "x": 210,  "y": 483},
    "comisiones":                {"page": 0, "x": 210, "y": 467},
    "otros_ingresos_valor":      {"page": 0, "x": 210, "y": 448},
    "total_ingresos":            {"page": 0, "x": 210, "y": 432},

    "gastos_familiares":         {"page": 0, "x": 460,  "y": 483},
    "prestamos_bancarios":       {"page": 0, "x": 460, "y": 467},
    "detalle_otros_gastos":      {"page": 0, "x": 460, "y": 415},
    "otros_gastos":              {"page": 0, "x": 460, "y": 448},
    "total_egresos":             {"page": 0, "x": 460, "y": 432},

    # ===== REFERENCIAS =====
    "ref_familiar":              {"page": 0, "x": 125, "y": 327},
    "ref_familiar_parentesco":   {"page": 0, "x": 487, "y": 327},
    "ref_familiar_cel":          {"page": 0, "x": 325, "y": 327},

    "ref_personal":              {"page": 0, "x": 125,  "y": 310},
    "ref_personal_parentesco":   {"page": 0, "x": 487, "y": 310},
    "ref_personal_cel":          {"page": 0, "x": 325, "y": 310},

    "ref_comercial":             {"page": 0, "x": 125,  "y": 293},
    "ref_comercial_cel":         {"page": 0, "x": 487, "y": 293},
    "ref_comercial2":            {"page": 0, "x": 125, "y": 276},
    "ref_comercial2_cel":        {"page": 0, "x": 487, "y": 276},

    # ===== CAMPOS ADICIONALES (NUEVOS) =====
    "empresa_trabajo_alt":       {"page": 0, "x": 210,  "y": 622},  # Empresa donde trabaja (extra)
    "email_conyuge":             {"page": 0, "x": 210, "y": 605},  # Correo electrónico cónyuge
    "direccion_trabajo":         {"page": 0, "x": 210,  "y": 553},  # Dirección trabajo
    "ciudad_trabajo":            {"page": 0, "x": 375, "y": 553},  # Ciudad trabajo
    "nit_trabajo":               {"page": 0, "x": 460, "y": 575},  # NIT trabajo
    "telefono_trabajo":          {"page": 0, "x": 210, "y": 535},  # Teléfono trabajo

    "tipo_bien_respaldo2":       {"page": 0, "x": 35,  "y": 362},  # Tipo bien (respaldo 2)
    "tipo_servicio_respaldo2":   {"page": 0, "x": 210, "y": 362},  # Tipo servicio (respaldo 2)
    "vr_comercial_respaldo2":    {"page": 0, "x": 380, "y": 362},  # Vr comercial (respaldo 2)

    "nit_ref1":                  {"page": 0, "x": 325, "y": 293},   # NIT ref1
    "nit_ref2":                  {"page": 0, "x": 325, "y": 276},
    
    

    "firma":                     {"page": 0, "x": 105, "y": 60},
}

# Caja donde irá la imagen de la firma (usa la X/Y de FIELD_MAP["firma"])
SIGNATURE_BOX = {
    "page": FIELD_MAP["firma"]["page"],
    "x": FIELD_MAP["firma"]["x"],
    "y": FIELD_MAP["firma"]["y"],
    "w": 200,   # ancho máximo de la firma (ajusta a tu plantilla)
    "h": 45,    # alto máximo de la firma
}

# Offset por página (si necesitas mover todo un poco)
PAGE_OFFSETS = {
    0: {"dx": 0, "dy": 0},
}

def crear_overlay_debug_page(w: float, h: float, step: int = 20, label_step: int = 100) -> PdfReader:
    buf = io.BytesIO()
    can = canvas.Canvas(buf, pagesize=(w, h))
    # Rejilla
    can.setStrokeColorRGB(0.85, 0.85, 0.85)
    for x in range(0, int(w), step):
        can.line(x, 0, x, h)
    for y in range(0, int(h), step):
        can.line(0, y, w, y)
    # Marcas numeradas
    can.setFillColor(colors.black)
    can.setFont("Helvetica", 7)
    for x in range(0, int(w), label_step):
        can.drawString(x + 2, 2, str(x))
    for y in range(0, int(h), label_step):
        can.drawString(2, y + 2, str(y))
    can.showPage()
    can.save()
    buf.seek(0)
    return PdfReader(buf)

def _prepare_signature(img_bytes: bytes, max_w: float, max_h: float) -> io.BytesIO:
    """Redimensiona la firma manteniendo proporción para encajar en (max_w, max_h)."""
    im = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    # quitar fondo blanco si viene con borde (opcional simple): no lo recortamos aquí para evitar errores
    w, h = im.size
    scale = min(max_w / w, max_h / h)
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    im = im.resize(new_size, Image.LANCZOS)

    # Si trae transparencia, poner fondo blanco
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bg.paste(im, mask=im.split()[3] if im.mode == "RGBA" else None)

    out = io.BytesIO()
    bg.save(out, format="PNG", optimize=True)
    out.seek(0)
    return out

def make_overlay(data: dict, template_reader: PdfReader, firma_img_bytes: bytes | None = None):
    """Crea una capa por página pintando textos y, si hay, la imagen de firma."""
    packets = []
    for page_idx in range(len(template_reader.pages)):
        page = template_reader.pages[page_idx]
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(w, h))
        can.setFont("Times-Roman", 8)

        dx = PAGE_OFFSETS.get(page_idx, {}).get("dx", 0)
        dy = PAGE_OFFSETS.get(page_idx, {}).get("dy", 0)

        # Texto de campos mapeados para esta página
        for key, meta in FIELD_MAP.items():
            if meta["page"] != page_idx:
                continue
            val = data.get(key)
            if val is None or str(val).strip() == "":
                continue
            x = meta["x"] + dx
            y = meta["y"] + dy
            # No dibujamos texto en la zona de firma (la imagen va allí)
            if key == "firma":
                continue
            can.drawString(x, y, str(val))

        # Firma como imagen, si está en esta página
        if firma_img_bytes and page_idx == SIGNATURE_BOX["page"]:
            x = SIGNATURE_BOX["x"] + dx
            y = SIGNATURE_BOX["y"] + dy
            buf_img = _prepare_signature(firma_img_bytes, SIGNATURE_BOX["w"], SIGNATURE_BOX["h"])
            can.drawImage(ImageReader(buf_img), x, y, width=SIGNATURE_BOX["w"], height=SIGNATURE_BOX["h"], mask="auto")

        can.save()
        packet.seek(0)
        packets.append(PdfReader(packet))
    return packets

@app.get("/", response_class=HTMLResponse)
def form():
    tpl = env.get_template("templates/form.html")
    return tpl.render()

@app.get("/preview-debug", response_class=FileResponse)
def preview_debug():
    base = PdfReader(TEMPLATE_PDF)
    writer = PdfWriter()

    for i, page in enumerate(base.pages):
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)

        merged = PageObject.create_blank_page(width=w, height=h)
        merged.merge_page(page)  # plantilla
        grid_pdf = crear_overlay_debug_page(w, h, step=20, label_step=100)
        merged.merge_page(grid_pdf.pages[0])  # rejilla
        writer.add_page(merged)

    out_path = OUT_DIR / "preview_debug.pdf"
    with open(out_path, "wb") as f:
        writer.write(f)

    return FileResponse(str(out_path), media_type="application/pdf", filename=out_path.name)

@app.post("/generar", response_class=FileResponse)
async def generar(request: Request, debug: bool = Query(False, description="Superponer rejilla de depuración")):
    """
    Lee todos los campos enviados por el formulario y solo utiliza
    los que están en FIELD_MAP. Además, si se sube 'firma_img', la coloca
    en la caja de firma.
    """
    form = await request.form()

    # Normaliza y toma solo campos mapeados (texto)
    data = {}
    for k in FIELD_MAP.keys():
        v = form.get(k)
        if v is not None:
            data[k] = v

    # Lee la imagen de firma si viene
    firma_upload = form.get("firma_img")
    firma_bytes = None
    if getattr(firma_upload, "read", None):
        # Starlette UploadFile
        firma_bytes = await firma_upload.read()
        # saneo mínimo: si el input estaba vacío no hacemos nada
        if not firma_bytes:
            firma_bytes = None

    base = PdfReader(TEMPLATE_PDF)
    overlays = make_overlay(data, base, firma_img_bytes=firma_bytes)

    writer = PdfWriter()
    for i, page in enumerate(base.pages):
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        page_merged = PageObject.create_blank_page(width=w, height=h)
        page_merged.merge_page(page)                 # fondo: plantilla
        page_merged.merge_page(overlays[i].pages[0]) # texto + firma

        if debug:
            grid_pdf = crear_overlay_debug_page(w, h, step=20, label_step=100)
            page_merged.merge_page(grid_pdf.pages[0])  # rejilla opcional

        writer.add_page(page_merged)

    # Nombre de salida
    numero_id = (data.get("numero_id") or "NA").strip().replace(" ", "_")
    out_path = OUT_DIR / f"solicitud_{numero_id}.pdf"
    with open(out_path, "wb") as f:
        writer.write(f)

    return FileResponse(str(out_path), media_type="application/pdf", filename=out_path.name)
