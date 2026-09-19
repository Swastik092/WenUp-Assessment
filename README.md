# Wenup Document Intake Assistant

## 1. Project Overview
This project is a technical assessment for Wenup, building a Personal Wishes Document Intake Assistant. It conducts a multi-turn conversation with a user to extract structured personal wishes, validate them, and generate a fictional document. 

## 2. Assessment Objective
The goal is to demonstrate robust LLM application engineering with a focus on structured state management, validation, handling of ambiguities and contradictions, rather than a sophisticated frontend or over-engineered infrastructure.

## 3. Architecture
### Crucial Architectural Principle
**"The LLM is treated as an untrusted information extraction component. The validated structured state is the source of truth."**

The architecture follows a strict, unidirectional flow:
`UI ↔ FastAPI routes ↔ orchestrator ↔ (state manager + LLM client interface + document generator)`

**Note on LLM Swappability**: The `LLMClient` interface is completely swappable. `MockLLMService` (a local regex-based fallback) and `GeminiLLMService` (calling Google Gemini) are interchangeable implementations of the same interface.

## 4. Technology Stack
- **Python 3.11+**
- **FastAPI** for API endpoints and static file serving
- **Pydantic** for structured data validation and state modeling
- **pytest** for automated testing
- **Google GenAI (Gemini)** (or a mock service) for NLP extraction
- **Vanilla JS/CSS** for the frontend

## 5. Local Setup

### Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Getting a Gemini API Key
To run the application with a real LLM, you need a Google Gemini API key.
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account and click "Get API key".
3. Create a new API key.
4. Open your local `.env` file and set:
```
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_actual_api_key_here
```

### Switching between Mock and Real mode
The application supports running without a real API key for testing purposes.
- To use the real LLM: Set `LLM_PROVIDER=gemini` in your `.env`.
- To use the local Mock (no API key required): Set `LLM_PROVIDER=mock` in your `.env`.

## 6. How to run
```bash
source .venv/bin/activate
uvicorn backend.main:app --reload
```
Then open [http://localhost:8000](http://localhost:8000) in your browser to interact with the frontend UI.
API Documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## 7. How to run tests
```bash
source .venv/bin/activate
pytest -v
```

## 8. Known Limitations
- In-memory sessions (data is lost on restart).
- Missing authentication.
- No persistent database.
