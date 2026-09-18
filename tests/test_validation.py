import pytest
from pydantic import ValidationError
from backend.models.llm_models import LLMExtractionResult, FieldExtraction

def test_missing_fields_logic():
    # Empty extractions
    res = LLMExtractionResult()
    assert res.extractions == []

def test_validation_malformed():
    # Intentionally pass bad type (e.g. dict for field string)
    with pytest.raises(ValidationError):
        FieldExtraction(field={"bad": "type"}, value="test", status="confirmed")
    
    # Missing required field
    with pytest.raises(ValidationError):
        FieldExtraction(value="test", status="confirmed")
