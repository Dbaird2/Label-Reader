from pydantic import BaseModel, Field
from typing import Literal, Optional

class OCRModel(BaseModel):
    ocr: bool = Field(..., description="Flag to indicate this is an OCR request")
    image: str = Field(..., description="URL of the image to be processed for OCR")


class AddPersonModel(BaseModel):
    addPerson: Literal[True] = True
    name: str
    building: str | None = None
    room: str | None = None
    school: str
    department: str

class EditPersonModel(BaseModel):
    editPerson: Literal[True] = True
    name: str
    building: Optional[str] = None
    room: Optional[str] = None
    school: str
    department: str
    id: int

class SearchPersonModel(BaseModel):
    searchPerson: bool = Field(..., description="Flag to indicate this is a request to search for a person")
    search: str

class OCRResult(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    building: Optional[str] = None
    room: Optional[str] = None
    department: Optional[str] = None
    confidence: Optional[float] = None
    school: Optional[str] = None
