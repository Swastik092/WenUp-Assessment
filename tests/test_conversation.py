import pytest
from backend.services.conversation_service import ConversationService
from backend.services.llm_service import MockLLMService
from backend.models.llm_models import LLMExtractionResult, FieldExtraction

@pytest.mark.asyncio
async def test_end_to_end_flow_with_mock():
    # Setup mock service
    mock_llm = MockLLMService()
    conv_service = ConversationService(mock_llm)
    
    # 1. Create/start a session
    session_id = conv_service.create_session()
    
    # 2. Test 1: Basic name extraction (uses the new dynamic regex)
    res1 = await conv_service.process_message(session_id, "My name is John Smith")
    assert res1["state"]["full_name"] == "John Smith"
    
    # 3. Test 2: Multiple fields in one answer (use override for complex combo not covered by regex)
    mock_llm.set_next_response(LLMExtractionResult(extractions=[
        FieldExtraction(field="home_address", value="10 Main Street", status="confirmed"),
        FieldExtraction(field="covers_worldwide_assets", value=True, status="confirmed")
    ]))
    res2 = await conv_service.process_message(session_id, "I live at 10 Main Street and it covers worldwide assets")
    assert res2["state"]["home_address"] == "10 Main Street"
    assert res2["state"]["covers_worldwide_assets"] is True
    
    # 4. Test 7: Correction
    mock_llm.set_next_response(LLMExtractionResult(extractions=[
        FieldExtraction(field="home_address", value="20 Main Street", status="confirmed")
    ]))
    res3 = await conv_service.process_message(session_id, "Actually my address is 20 Main Street")
    assert res3["state"]["home_address"] == "20 Main Street" # Must be overwritten
    assert "20 Main Street" in res3["document"]
    
@pytest.mark.asyncio
async def test_malformed_retry_fallback():
    mock_llm = MockLLMService()
    conv_service = ConversationService(mock_llm)
    session_id = conv_service.create_session()
    
    # Grab initial state
    initial_state = conv_service.get_session(session_id)["state"].model_dump()
    
    res = await conv_service.process_message(session_id, "TRIGGER_MALFORMED")
    
    # Should fallback to 200 with unchanged state
    assert res["status"] == "success"
    assert res["state"] == initial_state
    assert res["assistant_message"] == "Sorry, I didn't quite catch that \u2014 could you rephrase?"
    assert mock_llm.call_count == 2

@pytest.mark.asyncio
async def test_orchestrator_retry_with_gemini_client():
    from backend.services.gemini_client import GeminiLLMService
    from unittest.mock import AsyncMock, patch
    
    # Create a real conversation service, but inject a mocked Gemini client
    mock_gemini = GeminiLLMService(api_key="fake")
    
    # Setup the mock to fail on the first call, and succeed on the second
    mock_gemini.extract_information = AsyncMock(
        side_effect=[
            ConnectionError("Network timeout on first try"),
            LLMExtractionResult(extractions=[
                FieldExtraction(field="full_name", value="Retry Success", status="confirmed")
            ])
        ]
    )
    
    conv_service = ConversationService(mock_gemini)
    session_id = conv_service.create_session()
    
    res = await conv_service.process_message(session_id, "Hello")
    
    # Assert that it succeeded because the orchestrator caught the ConnectionError and retried
    assert res["status"] == "success"
    assert res["state"]["full_name"] == "Retry Success"
    assert mock_gemini.extract_information.call_count == 2
