from typing import Any, Optional
from pydantic import BaseModel, Field

class FieldExtraction(BaseModel):
    field: str = Field(description="The field name to update, e.g., 'full_name', 'executor.name', 'has_children'.")
    value: Any = Field(description="The extracted value for this field.")
    status: str = Field(description="'confirmed' if the user was clear, or 'ambiguous' if unclear or contradictory.")
    note: Optional[str] = Field(default=None, description="Explanation or follow-up question if the status is ambiguous.")

class LLMExtractionResult(BaseModel):
    extractions: list[FieldExtraction] = Field(
        default_factory=list, 
        description="List of extracted fields from the user's message."
    )
