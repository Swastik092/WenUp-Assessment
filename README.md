# Wenup Document Intake Assistant

## 1. Project Overview
This project is a technical assessment for Wenup, building a Personal Wishes Document Intake Assistant. It conducts a multi-turn conversation with a user to extract structured personal wishes, validate them, and generate a fictional document. 

## 2. Assessment Objective
The goal is to demonstrate robust LLM application engineering with a focus on structured state management, validation, handling of ambiguities and contradictions, rather than a sophisticated frontend or over-engineered infrastructure.

## 3. Architecture
### Crucial Architectural Principle
**"The LLM is treated as an untrusted information extraction component. The validated structured state is the source of truth."**

Conversation history is merely contextual information. The architecture follows a strict, unidirectional flow:
User Message -> LLM Extraction -> Validation -> State Update -> Missing Field Detection -> Next Question Generation -> Document Generation.

## 4. Technology Stack
- **Python 3.11+**
- **FastAPI** for API endpoints
- **Pydantic** for structured data validation and state modeling
- **pytest** for automated testing
- **OpenAI** (or a mock service) for NLP extraction

## 5. Project Structure
- `backend/models/`: Pydantic definitions for State (`PersonalWishesState`) and LLM extraction schema (`LLMExtractionResult`).
- `backend/services/`: 
  - `llm_service.py`: LLM provider abstraction (OpenAI and Mock).
  - `state_manager.py`: Validation, missing field logic, and state mutation.
  - `conversation_service.py`: Orchestrates the message processing flow.
  - `document_generator.py`: Generates the document based entirely on state.
- `backend/api/`: FastAPI routes (`/api/session`, `/api/chat`).
- `tests/`: Automated test suite.

## 6. Structured State Model
`PersonalWishesState` explicitly represents unknown/unconfirmed fields with `None` rather than assuming falsy defaults. It includes nested models like `Executor` and handles dependencies (e.g., `children_names` is conditionally required based on `has_children`).

## 7. LLM Architecture
The LLM is not an authoritative database. It merely extracts structured `CandidateUpdates` from the user's latest message, alongside identifying any ambiguities or contradictions.

## 8. Validation Approach
Extracted data is first structurally validated using Pydantic. Then, application-level logic in `state_manager.py` rejects updates if there are explicit contradictions or ambiguities, prompting the user for clarification instead of corrupting state.

## 9. State-Management Approach
State is safely updated through deep copying and specific field merging in the `state_manager.py`. Dependent states (like `children_names`) are sanitized if conditions change (e.g., changing `has_children` from `True` to `False`).

## 10. API Endpoints
- **`POST /api/session`**: Starts a session and returns `{session_id, state}`
- **`POST /api/chat`**: Accepts `{session_id, message}` and returns `{assistant_message, state, document, status}`

## 11. Environment Variables
Stored in `.env`:
- `LLM_API_KEY`: API key for the LLM provider.

## 12. Local Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your LLM_API_KEY
```

## 13. How to run
```bash
source .venv/bin/activate
uvicorn backend.main:app --reload
```
API Documentation is available at `http://127.0.0.1:8000/docs`.

## 14. How to run tests
```bash
source .venv/bin/activate
pytest tests/
```

## 15. Known Limitations
- In-memory sessions (data is lost on restart).
- Relies exclusively on `gpt-4o-mini` with strict structured JSON output parsing.
- Missing authentication.
- No persistent database.
