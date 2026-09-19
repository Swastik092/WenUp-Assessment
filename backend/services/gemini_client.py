from typing import Literal, Optional
from pydantic import BaseModel
from google import genai
from google.genai import types

from backend.services.llm_service import BaseLLMService
from backend.models.state import PersonalWishesState
from backend.models.llm_models import LLMExtractionResult, FieldExtraction

class WireFieldExtraction(BaseModel):
    field: str          # dot-path, matches domain field names exactly, e.g. "executor.name"
    value: str          # ALWAYS a string on the wire
    status: Literal["confirmed", "ambiguous"]
    note: Optional[str] = None

class WireExtractionResult(BaseModel):
    extractions: list[WireFieldExtraction] = []

BOOLEAN_FIELDS = {"covers_worldwide_assets", "has_children"}
LIST_FIELDS = {"children_names", "specific_gifts"}

SYSTEM_INSTRUCTION = """You are the extraction engine for a Personal Wishes Document intake form.
Given the user's latest message, the current known state, and the conversation so far,
extract ONLY information the user has clearly and explicitly stated in their latest message.

Rules:
- NEVER invent, infer, or guess a value the user did not state.
- If a value is unclear, contradictory, or ambiguous, set status="ambiguous" and explain why in "note" — do not guess a value.
- If the user's message provides multiple fields at once, return one extraction entry per field.
- If the user is correcting a previously given value (e.g. "actually", "I meant", "change that to"), return it as status="confirmed" — corrections are allowed to overwrite.
- For "children_names" or "specific_gifts", if multiple items are given, return a SEPARATE extraction entry per item, each with field="children_names" (or "specific_gifts") and value=<single item>.
- For boolean fields (covers_worldwide_assets, has_children), value must be exactly the string "true" or "false".
- Valid field names are exactly: full_name, home_address, covers_worldwide_assets, has_children, children_names, executor.name, executor.relationship, specific_gifts, additional_wishes.
- If nothing extractable is in the message, return an empty extractions list.
- Return ONLY the JSON matching the schema. No prose, no markdown fences.
"""

class GeminiLLMService(BaseLLMService):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        # We must initialize async client using async method if we want to use Async API? 
        # Actually, genai.Client() has synchronous methods and async methods. Wait, genai client structure in python:
        # `genai.Client()` provides `.models.generate_content` (sync) and `.aio.models.generate_content` (async).
        # Our BaseLLMService interface expects `async def extract_information`.
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def extract_information(
        self, state: PersonalWishesState, user_message: str, history: list[dict]
    ) -> LLMExtractionResult:
        prompt = self._build_prompt(user_message, state, history)

        # We must use async client call `aio` if available, or just standard. The prompt didn't specify `aio` for GeminiLLMClient but the method is async.
        # google-genai async support is through `client.aio`.
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=WireExtractionResult,
                temperature=0.1,
            ),
        )
        
        # Let any exception here propagate up for the orchestrator to catch and retry
        wire_result = WireExtractionResult.model_validate_json(response.text)
        return self._to_domain(wire_result)

    def _build_prompt(self, message: str, current_state: PersonalWishesState, history: list[dict]) -> str:
        history_text = "\n".join(f"{turn['role']}: {turn['content']}" for turn in history)
        return (
            f"Conversation so far:\n{history_text}\n\n"
            f"Current known state (JSON):\n{current_state.model_dump_json()}\n\n"
            f"User's latest message:\n{message}"
        )

    def _to_domain(self, wire_result: WireExtractionResult) -> LLMExtractionResult:
        domain_extractions: list[FieldExtraction] = []
        list_accumulators = {k: [] for k in LIST_FIELDS}
        ambiguous_list_notes = {k: [] for k in LIST_FIELDS}

        for item in wire_result.extractions:
            if item.field in LIST_FIELDS:
                if item.status == "confirmed":
                    list_accumulators[item.field].append(item.value)
                else:
                    ambiguous_list_notes[item.field].append(item.note)
            else:
                value: object = item.value
                if item.field in BOOLEAN_FIELDS:
                    value = item.value.strip().lower() in {"true", "yes", "1"}
                domain_extractions.append(
                    FieldExtraction(field=item.field, value=value, status=item.status, note=item.note)
                )

        # Aggregate list fields into single domain extractions since state_manager overrides lists fully
        for field, items in list_accumulators.items():
            if items:
                domain_extractions.append(
                    FieldExtraction(field=field, value=items, status="confirmed", note=None)
                )
        
        # Add ambiguous notes for list fields if any
        for field, notes in ambiguous_list_notes.items():
            for note in notes:
                if note:
                    domain_extractions.append(
                        FieldExtraction(field=field, value=[], status="ambiguous", note=note)
                    )

        return LLMExtractionResult(extractions=domain_extractions)
