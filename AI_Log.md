# AI Log

## Overview
This document serves as a log of the AI assistance, architectural decisions, and prompt engineering strategies utilized during the development of the Wenup Document Intake Assistant. The project was broken down into two distinct phases to isolate domain logic from LLM integration.

---

## Day 1: Domain Logic, State Management, and Mocking

### 1. Robust State Management
**Prompt Used:**
> *"Build a state manager in `state_manager.py` that incrementally updates a Pydantic schema using dot-notation. Ensure it handles partial application correctly: confirmed fields must be merged immediately, while ambiguous fields in the same message should be rejected back to the orchestrator for clarification."*

**Context & Action Taken**: 
The initial task was to create a robust state manager that could incrementally update a legal document schema (`PersonalWishesState`) from conversational input. I designed a flexible `state_manager.py` that utilizes dictionary dot-notation updates (e.g., `executor.name`). I handled edge cases such as partial application so that valid extractions are never discarded simply because another field in the same message was ambiguous.

### 2. High-Fidelity Mocking
**Prompt Used:**
> *"Write a `MockLLMService` that uses complex regex to map conversational input directly to our extraction schema. This will allow us to test the full orchestrator loop, including error handling and retry logic, without burning through live API tokens or dealing with LLM latency."*

**Context & Action Taken**: 
To test the conversational loop deterministically, we needed a robust mock. I built the `MockLLMService` to detect specific phrases (e.g., "My brother James") and map them to fields like `executor.name` and `executor.relationship`. This allowed us to build out the entire FastAPI backend and the testing suite (`pytest`) in pure isolation.

---

## Day 2: Real LLM Integration, Provider Pivots, and UI Polish

### 1. The Pivot from Gemini to Groq
**Prompt Used:**
> *"We are hitting rate limits with the Gemini Free Tier. Let's pivot the backend to use the Groq provider via the OpenAI Python SDK. Set the model to `openai/gpt-oss-20b`. Use `response_format={"type": "json_object"}` and pass the JSON schema directly into the system prompt so we can natively extract arrays and nested objects."*

**Context & Action Taken**: 
During Day 2, the initial integration utilized the Gemini API. However, strict Free-Tier rate limits (20 requests per day) on `gemini-2.5-flash` caused `429 RESOURCE_EXHAUSTED` errors during manual testing. To keep the project moving, we pivoted to **Groq**. 
* Integrated the standard `openai` Python SDK pointing to `https://api.groq.com/openai/v1`. 
* Swapped the LLM model to `openai/gpt-oss-20b`.
* Injected the JSON schema directly into the system prompt. This drastically simplified the extraction pipeline, allowing the model to natively return arrays (like `children_names`), bypassing the strict schema-typing limitations we initially faced with Gemini.

### 2. Frontend Layout and Markdown Rendering
**Prompt Used:**
> *"The frontend layout needs to look like a premium SaaS dashboard. Completely rewrite `styles.css` into a 2-column dark-mode layout with glassmorphism effects. Also, the document is currently rendering raw markdown asterisks—integrate `marked.js` to parse it into native HTML and style the output."*

**Context & Action Taken**: 
The default frontend layout was functional but lacked the "wow" factor required for a professional application. Additionally, the document generation returned raw Markdown (e.g., `**Full Name:**`), which rendered poorly. 
* **UI Redesign**: I completely overhauled `styles.css` into a premium 2-column dark-mode dashboard featuring a responsive flex layout, custom `Inter` typography, and soft borders.
* **Markdown Parsing**: I integrated `marked.js` via CDN to parse the LLM's raw markdown response on the client side, rendering native HTML bold tags, bulleted lists, and headers seamlessly.
* **Cache Busting**: To solve persistent browser-caching issues during the UI update, I appended version query strings (`?v=4`) to the CSS and JS imports.
