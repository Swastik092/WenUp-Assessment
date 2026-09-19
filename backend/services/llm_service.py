from abc import ABC, abstractmethod
import json
from openai import AsyncOpenAI
from backend.models.state import PersonalWishesState
from backend.models.llm_models import LLMExtractionResult, FieldExtraction
from backend.prompts.extraction_prompt import EXTRACTION_SYSTEM_PROMPT
from backend.config import settings


class BaseLLMService(ABC):
    @abstractmethod
    async def extract_information(
        self, state: PersonalWishesState, user_message: str, history: list[dict]
    ) -> LLMExtractionResult:
        pass


class OpenAILLMService(BaseLLMService):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.llm_api_key)

    async def extract_information(
        self, state: PersonalWishesState, user_message: str, history: list[dict]
    ) -> LLMExtractionResult:
        schema = LLMExtractionResult.model_json_schema()
        system_content = (
            EXTRACTION_SYSTEM_PROMPT 
            + f"\n\nCURRENT CONFIRMED STATE:\n{state.model_dump_json(indent=2)}"
            + f"\n\nIMPORTANT: You must return ONLY valid JSON matching this schema:\n{json.dumps(schema)}"
        )
        
        messages = [{"role": "system", "content": system_content}]
        # Include a short history for context (e.g. knowing what question was asked)
        for msg in history[-5:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        messages.append({"role": "user", "content": user_message})

        try:
            completion = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            raw_content = completion.choices[0].message.content
            return LLMExtractionResult.model_validate_json(raw_content)
        except Exception as e:
            raise ValueError(f"LLM API Error: {str(e)}")


class GroqLLMService(BaseLLMService):
    def __init__(self, api_key: str, model: str):
        self.client = AsyncOpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        self.model = model

    async def extract_information(
        self, state: PersonalWishesState, user_message: str, history: list[dict]
    ) -> LLMExtractionResult:
        schema = LLMExtractionResult.model_json_schema()
        system_content = (
            EXTRACTION_SYSTEM_PROMPT 
            + f"\n\nCURRENT CONFIRMED STATE:\n{state.model_dump_json(indent=2)}"
            + f"\n\nIMPORTANT: You must return ONLY valid JSON matching this schema:\n{json.dumps(schema)}"
        )
        
        messages = [{"role": "system", "content": system_content}]
        for msg in history[-5:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        messages.append({"role": "user", "content": user_message})

        try:
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            raw_content = completion.choices[0].message.content
            return LLMExtractionResult.model_validate_json(raw_content)
        except Exception as e:
            raise ValueError(f"Groq API Error: {str(e)}")


class MockLLMService(BaseLLMService):
    def __init__(self):
        self.next_response: LLMExtractionResult | None = None
        self.should_error: bool = False
        self.call_count: int = 0

    def set_next_response(self, response: LLMExtractionResult):
        self.next_response = response
        self.should_error = False
        self.call_count = 0

    def set_error(self):
        self.should_error = True

    async def extract_information(
        self, state: PersonalWishesState, user_message: str, history: list[dict]
    ) -> LLMExtractionResult:
        self.call_count += 1
        
        if self.should_error or "TRIGGER_MALFORMED" in user_message:
            raise ValueError("Intentional Mock LLM Error/Malformed Output")
        
        if self.next_response:
            return self.next_response
            
        import re
        msg = user_message.lower()
        extractions = []
        
        # Corrections (supercedes other patterns if present)
        # Note: A real LLM handles this via prompt logic. For the mock, we just process it as a normal extraction
        # since apply_updates overwrites state.
        
        # Full name
        if re.search(r"my name is (.+)|i'm (.+)|i am (.+)", msg):
            match = re.search(r"my name is (.+?)(?:\.| and|$)|i'm (.+?)(?:\.| and|$)|i am (.+?)(?:\.| and|$)", msg)
            if match:
                name = next(g for g in match.groups() if g).strip().title()
                extractions.append(FieldExtraction(field="full_name", value=name, status="confirmed"))
                
        # Home address
        if re.search(r"i live at (.+)|my address is (.+)", msg):
            match = re.search(r"i live at (.+?)(?:\.| and|$)|my address is (.+?)(?:\.| and|$)", msg)
            if match:
                addr = next(g for g in match.groups() if g).strip().title()
                extractions.append(FieldExtraction(field="home_address", value=addr, status="confirmed"))
                
        # Worldwide assets
        if "worldwide" in msg or "everywhere" in msg or re.search(r"\byes\b", msg) and "asset" in msg:
            if "not" in msg or "only in" in msg or "just in" in msg:
                extractions.append(FieldExtraction(field="covers_worldwide_assets", value=None, status="ambiguous", note="Worldwide assets ambiguous"))
            else:
                extractions.append(FieldExtraction(field="covers_worldwide_assets", value=True, status="confirmed"))
        elif "no" in msg and "asset" in msg:
            extractions.append(FieldExtraction(field="covers_worldwide_assets", value=False, status="confirmed"))
        elif "only in" in msg or "just in" in msg:
            extractions.append(FieldExtraction(field="covers_worldwide_assets", value=False, status="confirmed"))
            
        # Has children
        if re.search(r"i have \d+ kids|i have \d+ children|two children|some children", msg):
            extractions.append(FieldExtraction(field="has_children", value=True, status="confirmed"))
        elif re.search(r"no children|don't have kids|none", msg):
            extractions.append(FieldExtraction(field="has_children", value=False, status="confirmed"))
            
        # Children names
        if ("and" in msg or "," in msg) and any(kw in msg for kw in ["names are", "they are", "called"]):
            match = re.search(r"(?:names are|they are|called) (.+?)(?:\.|$)", msg)
            if match:
                names_str = match.group(1)
                names = [n.strip().title() for n in re.split(r' and |, ', names_str) if n.strip()]
                extractions.append(FieldExtraction(field="children_names", value=names, status="confirmed"))
        # Special case for "Their names are Sarah and Michael."
        elif "sarah and michael" in msg:
            extractions.append(FieldExtraction(field="children_names", value=["Sarah", "Michael"], status="confirmed"))
            
        # Executor
        if "my brother james" in msg:
            extractions.append(FieldExtraction(field="executor.name", value="James", status="confirmed"))
            extractions.append(FieldExtraction(field="executor.relationship", value="Brother", status="confirmed"))
        else:
            # Check for known relationships to avoid false positives like "my car to"
            rel_match = re.search(r"my (brother|sister|friend|husband|wife|son|daughter|spouse|father|mother|uncle|aunt|cousin) (\w+)", msg)
            if rel_match:
                rel = rel_match.group(1).title()
                name = rel_match.group(2).title()
                extractions.append(FieldExtraction(field="executor.name", value=name, status="confirmed"))
                extractions.append(FieldExtraction(field="executor.relationship", value=rel, status="confirmed"))
                
        # Gifts
        if "give my car to sarah" in msg:
            extractions.append(FieldExtraction(field="specific_gifts", value=["Car to Sarah"], status="confirmed"))
        elif "no gifts" in msg:
            extractions.append(FieldExtraction(field="specific_gifts", value=[], status="confirmed"))
            
        # Additional wishes
        if "no additional wishes" in msg:
            extractions.append(FieldExtraction(field="additional_wishes", value="None", status="confirmed"))

        return LLMExtractionResult(extractions=extractions)
