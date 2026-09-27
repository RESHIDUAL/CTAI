from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class FHIRIdentifier(BaseModel):
    system: str = "urn:ietf:rfc:3986"
    value: str

class FHIRCoding(BaseModel):
    system: str
    code: str
    display: str

class FHIRCodeableConcept(BaseModel):
    coding: List[FHIRCoding]
    text: Optional[str] = None

class FHIRQuantity(BaseModel):
    value: float
    unit: str
    system: str = "http://unitsofmeasure.org"
    code: str

class FHIREntry(BaseModel):
    fullUrl: str
    resource: Dict[str, Any]

class FHIRBundle(BaseModel):
    resourceType: str = "Bundle"
    id: str
    type: str = "collection"
    timestamp: str
    entry: List[FHIREntry] = []
