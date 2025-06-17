from pathlib import Path
import json
from pydantic_settings import BaseSettings
from typing import List, Iterator
from .models import LegalParagraph   # lo definimos abajo

def iter_paragraphs(json_dir: Path) -> Iterator[LegalParagraph]:
    for file in json_dir.rglob("*.json"):
        docs = json.loads(file.read_text(encoding="utf-8"))
        for doc in docs:
            expte = _extract_expte(doc["CONTENIDO"]["INICIO"][0])
            for section, paras in doc["CONTENIDO"].items():
                for idx, text in enumerate(paras):
                    yield LegalParagraph(
                        expediente=expte,
                        section=section,
                        paragraph_id=idx,
                        text=text,
                        path=file.relative_to(json_dir).as_posix()
                    )

def _extract_expte(header: str) -> str:
    # «… - Expte. Nº 8344» → 8344
    return header.split("Expte. Nº")[-1].strip()
