"""
clean_pdfs.py  ·  Limpia PDF jurídicos para RAG
------------------------------------------------
correr con: 
$ python clean_pdfs.py --pdf_dir ./2024 --out_dir ./clean_txt
"""


import re, os, argparse, pdfplumber
from pathlib import Path
from tqdm import tqdm
import logging


for name in ("pdfminer", "pdfminer.layout", "pdfminer.pdfpage"):
    logging.getLogger(name).setLevel(logging.ERROR)


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



def clean_page(text: str) -> str:
    return '\n'.join([ln for ln in (text or "").splitlines() if not REGEX.match(ln)]).strip()


def clean_pdf(pdf_path: Path) -> str:
    pages_clean = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            pages_clean.append(clean_page(page.extract_text()))
    return "\n\n".join(pages_clean)


def main(pdf_dir: str, out_dir: str):
    pdf_root = Path(pdf_dir).resolve()
    out_root = Path(out_dir).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    pdf_files = list(pdf_root.rglob("*.pdf"))
    if not pdf_files:
        print(f"No se encontraron PDFs en {pdf_dir}")
        return

    for path in tqdm(pdf_files, desc="Cleaning PDFs"):
        # —— NUEVO: ruta relativa para reproducir subcarpetas ——
        rel_path = path.relative_to(pdf_root).with_suffix(".txt")
        dst = out_root / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)  # crea la subcarpeta si falta
        # --------------------------------------------------------
        dst.write_text(clean_pdf(path), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf_dir", required=True, help="Carpeta raíz con PDFs (incluye subcarpetas)")
    ap.add_argument("--out_dir", required=True, help="Destino de .txt limpios")
    args = ap.parse_args()
    main(args.pdf_dir, args.out_dir)