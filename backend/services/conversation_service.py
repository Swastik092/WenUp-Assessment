import uuid
import logging
from backend.models.state import PersonalWishesState
from backend.services.llm_service import BaseLLMService
from backend.services.state_manager import apply_updates, get_missing_fields, get_next_question
from backend.services.document_generator import generate_document

# In-memory session store for assessment purposes
sessions: dict[str, dict] = {}

class ConversationService:
    def __init__(self, llm_service: BaseLLMService):
        self.llm_service = llm_service

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "state": PersonalWishesState(),
            "history": []
        }
        return session_id

    def get_session(self, session_id: str) -> dict | None:
        return sessions.get(session_id)

    async def process_message(self, session_id: str, user_message: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        state: PersonalWishesState = session["state"]
        history: list[dict] = session["history"]

        # Append user message to history
        history.append({"role": "user", "content": user_message})

        # 1. Ask LLM to extract information, with exactly one retry on validation/parsing failure
        extraction_result = None
        for attempt in range(2):
            try:
                extraction_result = await self.llm_service.extract_information(state, user_message, history)
                break # Success
            except Exception as e:
                logging.warning(f"LLM extraction failed on attempt {attempt + 1}: {e}")
                if attempt == 1:
                    # Retry also failed, fallback
                    pass
        
        if extraction_result is None:
            # Fallback path: unchanged state, generic response
            assistant_message = "Sorry, I didn't quite catch that — could you rephrase?"
            history.append({"role": "assistant", "content": assistant_message})
            document = generate_document(state)
            return {
                "assistant_message": assistant_message,
                "state": state.model_dump(),
                "document": document,
                "status": "success"
            }

        # 2. Validate and apply updates
        new_state, ambiguous_notes = apply_updates(state, extraction_result.extractions)

        # Update the session state
        session["state"] = new_state
        state = new_state

        # 3. Determine next assistant question or response
        if ambiguous_notes:
            # Use the first note for clarification
            assistant_message = ambiguous_notes[0]
        else:
            missing = get_missing_fields(state)
            if missing:
                assistant_message = get_next_question(missing)
            else:
                assistant_message = "Thank you. I have collected all the necessary information. Your document is ready!"

        # Append assistant message to history
        history.append({"role": "assistant", "content": assistant_message})

        # 4. Generate document
        document = generate_document(state)

        return {
            "assistant_message": assistant_message,
            "state": state.model_dump(),
            "document": document,
            "status": "success"
        }
