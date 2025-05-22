"""
clean_pdfs.py  ·  Limpia PDF jurídicos para RAG
------------------------------------------------
correr con: 
$ python pre-processing/clean_format_pdfs.py --pdf_dir datasets/2024 --out_dir datasets/clean_txt
"""


import re, argparse, logging
from pathlib import Path
from collections import defaultdict
import pdfplumber
from tqdm import tqdm


# ---------- silenciar "CropBox missing" -----------------
for name in ("pdfminer", "pdfminer.layout", "pdfminer.pdfpage"):
    logging.getLogger(name).setLevel(logging.ERROR)


# ---------- patrones de ruido a eliminar ----------------
PATTERNS = [
    r'^Superior Tribunal.*$',
    r'^Sala Civil y Comercial.*$',
    r'^\s*\d+\s*$',
    r'^Poder Judicial.*$',
    r'^Firmado digitalmente.*$',
    r'^Página \s*\d+(\s*de\s*\d+)?',
    r'^\s*\d{4}-\d{2}-\d{2}T\d{2}:',
]
REGEX = re.compile('|'.join(PATTERNS), re.IGNORECASE)


# ---------- helpers de estilo ---------------------------
def get_style(fontname: str) -> str:
    name = fontname.lower()
    bold = "bold" in name
    italic = "italic" in name or "oblique" in name
    if bold and italic:
        return "bolditalic"
    if bold:
        return "bold"
    if italic:
        return "italic"
    return "normal"


def style_mark(style: str, opening=True) -> str:
    if style == "bold":
        return "**" if opening else "**"
    if style == "italic":
        return "_" if opening else "_"
    if style == "bolditalic":
        return "***" if opening else "***"
    return ""


# ---------- limpieza y marcado página a página ----------
def page_to_markdown(page) -> str:
    """Devuelve el texto de la página con ** y _ según estilo."""
    lines = defaultdict(list)

    # Agrupar por coordenada vertical (líneas)
    for ch in page.chars:
        line_key = round(ch["top"], 1)
        lines[line_key].append(ch)
    out_lines = []
    for _, chars in sorted(lines.items()):
        segment = []
        for ch in sorted(chars, key=lambda c: c["x0"]):
            txt = ch["text"] or ""          # puede ser ""
            style = get_style(ch["fontname"])

            # ------ heredar estilo si es únicamente whitespace ------
            if txt.strip() == "" and segment:
                style = segment[-1][1]      # copia el último estilo real
            # --------------------------------------------------------

            segment.append((txt, style))
                
        # Construir la línea con marcadores
        rendered = []
        prev_style = "normal"
        for txt, style in segment:
            if style != prev_style:
                # cerrar estilo anterior
                if prev_style != "normal":
                    rendered.append(style_mark(prev_style, opening=False))
                # abrir nuevo
                if style != "normal":
                    rendered.append(style_mark(style, opening=True))
                prev_style = style
            rendered.append(txt)
        # cerrar estilo al final de línea
        if prev_style != "normal":
            rendered.append(style_mark(prev_style, opening=False))
        out_lines.append("".join(rendered))
    return "\n".join(out_lines)


def clean_page_text(raw_text: str) -> str:
    cleaned = []
    for ln in raw_text.splitlines():
        plain = re.sub(r'^[\*_ ]+', '', ln).strip()
        if not REGEX.match(plain):
            cleaned.append(ln)
    return "\n".join(cleaned).strip()

def merge_markers(text: str) -> str:
    # 1. une _foo_ _bar_  → _foo bar_
    pattern_inline = re.compile(r'_(\S[^_]*?)_\s+_(\S[^_]*?)_', flags=re.MULTILINE)
    # 2. une _foo_\n_bar_ → _foo bar_
    pattern_cross = re.compile(r'_(\S[^_]*?)_\s*\n\s*_(\S[^_]*?)_', flags=re.MULTILINE)

    merged = text
    for _ in range(3):  # itera hasta que no quede nada por unir
        merged_new = pattern_inline.sub(r'_\1 \2_', merged)
        merged_new = pattern_cross.sub(r'_\1 \2_', merged_new)
        if merged_new == merged:
            break
        merged = merged_new
    return merged

def clean_pdf(pdf_path: Path) -> str:
    pages = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            md = page_to_markdown(page)
            pages.append(clean_page_text(md))
    return merge_markers("\n\n".join(pages))


# ---------- main ---------------------------------------
def main(pdf_dir: str, out_dir: str):
    pdf_root = Path(pdf_dir).resolve()
    out_root = Path(out_dir).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    pdf_files = list(pdf_root.rglob("*.pdf"))
    if not pdf_files:
        print(f"No se encontraron PDFs en {pdf_dir}")
        return

    for src in tqdm(pdf_files, desc="Cleaning PDFs"):
        rel_path = src.relative_to(pdf_root).with_suffix(".txt")
        dst = out_root / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(clean_pdf(src), encoding="utf-8")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf_dir", required=True, help="Carpeta raíz con PDFs")
    ap.add_argument("--out_dir", required=True, help="Destino de .txt limpios")
    args = ap.parse_args()
    main(args.pdf_dir, args.out_dir)

# ver: quizas es mejor que ponga muchos bloques de italica cuando hay mucho texto junto en ese formato, por si se separa en chunks
# o usar una librería para pasar texto a markdown 
# vale la pena conservar el formato o mejor solo texto plano?

