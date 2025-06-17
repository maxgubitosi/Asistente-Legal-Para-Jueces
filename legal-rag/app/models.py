from pydantic import BaseModel

class LegalParagraph(BaseModel):
    expediente: str
    section:   str
    paragraph_id: int
    text: str
    path: str