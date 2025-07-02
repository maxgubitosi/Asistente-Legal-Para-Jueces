from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class LegalParagraphEnriched(BaseModel):
    """Modelo enriquecido para párrafos legales con contexto adicional"""
    expediente: str = Field(..., description="Número de expediente")
    section: str = Field(..., description="Sección del documento")
    paragraph_id: int = Field(..., ge=0, description="ID del párrafo dentro de la sección")
    text: str = Field(..., min_length=1, description="Contenido del párrafo")
    path: str = Field(..., description="Ruta relativa del archivo fuente")
    idea_central: Optional[str] = Field(None, description="Idea central del fallo")
    articulos_citados: Optional[List[Dict[str, Any]]] = Field(None, description="Artículos citados en el fallo")
    materia_preliminar: Optional[str] = Field(None, description="Materia preliminar del fallo")
    metadatos: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales del fallo")

    def to_search_dict(self) -> Dict[str, Any]:
        """Convierte a formato para búsqueda"""
        return {
            "expte": self.expediente,
            "section": self.section,
            "paragraph": self.text,
            "path": self.path,
            "paragraph_id": self.paragraph_id,
            "idea_central": self.idea_central,
            "articulos_citados": self.articulos_citados,
            "materia_preliminar": self.materia_preliminar,
            "metadatos": self.metadatos
        }
