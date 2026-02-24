from typing import List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

class FieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    FILE = "file"
    DATE = "date"
    UNKNOWN = "unknown"

class FormField(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    label: Optional[str] = None
    field_type: FieldType
    options: List[str] = []  # For select, radio
    required: bool = False
    selector: str  # CSS selector to interact with the element
    value: Optional[Any] = None  # The value we intend to fill
    description: Optional[str] = None # Help text or context

class ApplicationForm(BaseModel):
    url: str
    fields: List[FormField] = []
    submit_selector: Optional[str] = None
