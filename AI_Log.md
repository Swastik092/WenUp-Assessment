# AI Log

## Overview
This document serves as a log of AI assistance and prompt engineering strategies utilized during the development of the Wenup Document Intake Assistant.

## Day 2 Prompts & AI Interactions

### The `value: object` Schema Limitation
**Context**: During Day 2, we integrated the real `google-genai` SDK for Gemini. However, Gemini's controlled-generation (`response_schema`) feature only reliably supports concrete JSON-schema types (string, boolean, array, object) and struggles with untyped or polymorphic fields like our domain schema's `value: object` type in `FieldExtraction`. 

**Action Taken**: I questioned the initial instinct to feed the domain schema straight into Gemini. Instead, I created an internal "wire schema" (`WireExtractionResult` and `WireFieldExtraction`) where the `value` field is strictly typed as a string on the wire.

**Translation Layer Implementation**:
Because `apply_updates` expects `list`-valued fields (like `children_names` and `specific_gifts`) to be assigned as full lists in a single extraction, but the wire schema forces a string `value`, I modified the system prompt to instruct Gemini:
*`For "children_names" or "gifts", if multiple items are given, return a SEPARATE extraction entry per item, each with field="children_names" (or "gifts") and value=<single item>.`*

I then implemented a `_to_domain()` translation method inside the `GeminiLLMService` client. This method receives the multiple wire entries, parses boolean strings (`"true"`/`"false"`) back into Python `bool` types, and accumulates any list-field wire entries into a single domain `FieldExtraction` containing a native Python `list`. This allowed the real LLM output to match the exact same pipeline footprint as the mock LLM, ensuring `state_manager.py` did not need to be refactored.
