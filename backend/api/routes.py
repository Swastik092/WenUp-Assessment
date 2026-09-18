from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.services.conversation_service import ConversationService
from backend.services.llm_service import OpenAILLMService, MockLLMService
from backend.models.state import PersonalWishesState

router = APIRouter()

from backend.config import settings

# If no real API key is provided, fallback to MockLLMService to allow the manual demo path to work.
if settings.llm_api_key == "mock-api-key":
    llm_service_instance = MockLLMService()
else:
    llm_service_instance = OpenAILLMService()
    
conversation_service_instance = ConversationService(llm_service_instance)

def get_conversation_service() -> ConversationService:
    return conversation_service_instance

class SessionResponse(BaseModel):
    session_id: str
    state: dict

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    assistant_message: str
    state: dict
    document: str
    status: str

@router.post("/api/session", response_model=SessionResponse)
def create_session(service: ConversationService = Depends(get_conversation_service)):
    session_id = service.create_session()
    session = service.get_session(session_id)
    return SessionResponse(session_id=session_id, state=session["state"].model_dump())

@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, service: ConversationService = Depends(get_conversation_service)):
    try:
        # Check session existence directly here for a cleaner 404
        if not service.get_session(request.session_id):
            raise HTTPException(status_code=404, detail="Session not found")
            
        result = await service.process_message(request.session_id, request.message)
        return ChatResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        # Unexpected errors only
        raise HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."})
