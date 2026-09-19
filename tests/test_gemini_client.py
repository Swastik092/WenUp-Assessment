import pytest
import unittest.mock
from backend.services.gemini_client import GeminiLLMService
from backend.models.state import PersonalWishesState

class MockResponse:
    def __init__(self, text: str):
        self.text = text

@pytest.fixture
def mock_genai():
    with unittest.mock.patch("backend.services.gemini_client.genai") as mock_module:
        yield mock_module

@pytest.mark.asyncio
async def test_boolean_translation(mock_genai):
    # Setup mock response with "false" string
    mock_client_instance = mock_genai.Client.return_value
    mock_client_instance.aio.models.generate_content = unittest.mock.AsyncMock(
        return_value=MockResponse('{"extractions": [{"field": "has_children", "value": "false", "status": "confirmed"}]}')
    )
    
    service = GeminiLLMService(api_key="test-key")
    state = PersonalWishesState()
    result = await service.extract_information(state, "I have no children", [])
    
    # Assert it translates to a real bool
    assert len(result.extractions) == 1
    assert result.extractions[0].field == "has_children"
    assert result.extractions[0].value is False

@pytest.mark.asyncio
async def test_list_accumulation(mock_genai):
    # Setup mock response with multiple wire entries for the same list field
    mock_client_instance = mock_genai.Client.return_value
    mock_client_instance.aio.models.generate_content = unittest.mock.AsyncMock(
        return_value=MockResponse(
            '{"extractions": ['
            '{"field": "children_names", "value": "Alice", "status": "confirmed"},'
            '{"field": "children_names", "value": "Bob", "status": "confirmed"}'
            ']}'
        )
    )
    
    service = GeminiLLMService(api_key="test-key")
    state = PersonalWishesState()
    result = await service.extract_information(state, "My kids are Alice and Bob", [])
    
    # Assert it aggregates them into a single domain extraction with a list value
    assert len(result.extractions) == 1
    assert result.extractions[0].field == "children_names"
    assert result.extractions[0].value == ["Alice", "Bob"]
    assert result.extractions[0].status == "confirmed"

@pytest.mark.asyncio
async def test_exception_propagation(mock_genai):
    # Setup mock to raise an exception
    mock_client_instance = mock_genai.Client.return_value
    mock_client_instance.aio.models.generate_content = unittest.mock.AsyncMock(
        side_effect=ConnectionError("timeout")
    )
    
    service = GeminiLLMService(api_key="test-key")
    state = PersonalWishesState()
    
    # Assert the exception propagates out, so the orchestrator can catch it
    with pytest.raises(ConnectionError, match="timeout"):
        await service.extract_information(state, "Hello", [])
