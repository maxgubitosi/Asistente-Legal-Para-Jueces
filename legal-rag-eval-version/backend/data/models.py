from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class LegalParagraph(BaseModel):
    """Modelo para párrafos legales extraídos de documentos"""
    expediente: str = Field(..., description="Número de expediente")
    section: str = Field(..., description="Sección del documento")
    paragraph_id: int = Field(..., ge=0, description="ID del párrafo dentro de la sección")
    text: str = Field(..., min_length=1, description="Contenido del párrafo")
    path: str = Field(..., description="Ruta relativa del archivo fuente")
    
    @validator('expediente')
    def validate_expediente(cls, v):
        """Valida que el expediente no esté vacío"""
        if not v or v.strip() == "":
            raise ValueError("Expediente no puede estar vacío")
        return v.strip()
    
    @validator('text')
    def validate_text(cls, v):
        """Valida y limpia el texto"""
        if not v or len(v.strip()) < 10:
            raise ValueError("Texto debe tener al menos 10 caracteres")
        return v.strip()
    
    def to_search_dict(self) -> Dict[str, Any]:
        """Convierte a formato para búsqueda"""
        return {
            "expte": self.expediente,
            "section": self.section,
            "paragraph": self.text,
            "path": self.path,
            "paragraph_id": self.paragraph_id
        }

class Hit(BaseModel):
    """Resultado de búsqueda individual"""
    expte: str = Field("", description="Número de expediente")
    section: str = Field("", description="Sección del documento") 
    paragraph: str = Field("", description="Texto del párrafo")
    path: str = Field("", description="Ruta del archivo fuente")
    paragraph_id: int = Field(0, description="ID del párrafo")
    score: float = Field(0.0, description="Score de relevancia (puede ser negativo)")
    search_type: Optional[str] = Field("hybrid", description="Tipo de búsqueda")
    idea_central: Optional[str] = Field(None, description="Idea central del fallo")
    articulos_citados: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Artículos citados en el fallo")
    materia_preliminar: Optional[str] = Field(None, description="Materia preliminar del fallo")
    sections: Optional[List[str]] = Field(default_factory=list, description="Lista de secciones asociadas al párrafo/expediente")
    extractos: Optional[List[str]] = Field(default_factory=list, description="Lista de extractos asociados al expediente")

class QueryRequest(BaseModel):
    """Solicitud de consulta"""
    question: str = Field(..., min_length=3, max_length=500, description="Pregunta del usuario")
    top_n: int = Field(8, ge=1, le=20, description="Número de resultados a devolver")
    enable_reranking: Optional[bool] = Field(None, description="Habilitar re-ranking")
    search_type: Optional[str] = Field("hybrid", description="Tipo de búsqueda")
    
    @validator('question')
    def validate_question(cls, v):
        """Limpia y valida la pregunta"""
        if isinstance(v, str):
            cleaned = v.strip()
            if len(cleaned) < 3:
                raise ValueError("La pregunta debe tener al menos 3 caracteres")
            return cleaned
        raise ValueError("La pregunta debe ser una cadena de texto")

class QueryResponse(BaseModel):
    """Respuesta completa de consulta"""
    question: str = Field(..., description="Pregunta original")
    markdown: str = Field(..., description="Respuesta en formato Markdown")
    results: List[Hit] = Field(..., description="Resultados de búsqueda")
    total_time: float = Field(..., ge=0, description="Tiempo total de procesamiento en segundos")
    search_time: float = Field(..., ge=0, description="Tiempo de búsqueda en segundos")
    llm_time: float = Field(..., ge=0, description="Tiempo de generación LLM en segundos")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp de la consulta")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProcessingStats(BaseModel):
    """Estadísticas de procesamiento de datos"""
    total_files: int = Field(..., ge=0, description="Total de archivos procesados")
    total_paragraphs: int = Field(..., ge=0, description="Total de párrafos extraídos")
    total_expedientes: int = Field(..., ge=0, description="Total de expedientes únicos")
    avg_paragraphs_per_file: float = Field(..., ge=0, description="Promedio de párrafos por archivo")
    processing_time: float = Field(..., ge=0, description="Tiempo de procesamiento en segundos")
    errors: List[str] = Field(default_factory=list, description="Lista de errores encontrados")