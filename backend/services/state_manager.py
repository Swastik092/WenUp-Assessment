from backend.models.state import PersonalWishesState
from backend.models.llm_models import LLMExtractionResult

from backend.models.llm_models import FieldExtraction

def apply_updates(state: PersonalWishesState, extractions: list[FieldExtraction]) -> tuple[PersonalWishesState, list[str]]:
    """
    Safely applies confirmed extracted updates to the state independently.
    Returns: (new_state, list_of_ambiguous_notes)
    """
    new_state = state.model_copy(deep=True)
    ambiguous_notes = []

    for extraction in extractions:
        if extraction.status == "ambiguous":
            if extraction.note:
                ambiguous_notes.append(extraction.note)
            else:
                ambiguous_notes.append(f"I need clarification regarding: {extraction.field}")
            continue
            
        # Status is 'confirmed', apply immediately by dot-path
        field = extraction.field
        val = extraction.value
        
        if field == "full_name":
            new_state.full_name = val
        elif field == "home_address":
            new_state.home_address = val
        elif field == "covers_worldwide_assets":
            new_state.covers_worldwide_assets = val
        elif field == "has_children":
            new_state.has_children = val
        elif field == "children_names":
            new_state.children_names = val
        elif field == "executor.name":
            new_state.executor.name = val
        elif field == "executor.relationship":
            new_state.executor.relationship = val
        elif field == "specific_gifts":
            # For gifts, the LLM might extract an array of new gifts or the whole array.
            # Based on standard extraction patterns, it's typically an array of gifts.
            # To overwrite properly:
            new_state.specific_gifts = val
        elif field == "additional_wishes":
            new_state.additional_wishes = val

    # Safety constraint: if they don't have children, clear the children names
    if new_state.has_children is False:
        new_state.children_names = []

    return new_state, ambiguous_notes

def get_missing_fields(state: PersonalWishesState) -> list[str]:
    """
    Returns a list of field names that are still required.
    Accounts for conditional dependencies.
    """
    missing = []
    if state.full_name is None:
        missing.append("full_name")
        
    if state.home_address is None:
        missing.append("home_address")
        
    if state.covers_worldwide_assets is None:
        missing.append("covers_worldwide_assets")
        
    if state.has_children is None:
        missing.append("has_children")
    elif state.has_children is True and not state.children_names:
        missing.append("children_names")
        
    if state.executor.name is None:
        missing.append("executor.name")
        
    if state.executor.relationship is None:
        missing.append("executor.relationship")
        
    if state.specific_gifts is None:
        missing.append("specific_gifts")
        
    if state.additional_wishes is None:
        missing.append("additional_wishes")
        
    return missing

def get_next_question(missing_fields: list[str]) -> str | None:
    """
    Given a list of missing fields, returns the next natural language question.
    """
    if not missing_fields:
        return None
        
    field = missing_fields[0]
    questions = {
        "full_name": "What is your full name?",
        "home_address": "What is your home address?",
        "covers_worldwide_assets": "Does this document cover your worldwide assets? (Yes/No)",
        "has_children": "Do you have any children?",
        "children_names": "What are the names of your children?",
        "executor.name": "Who would you like to appoint as your executor?",
        "executor.relationship": "What is your relationship to your executor?",
        "specific_gifts": "Do you have any specific gifts you would like to make? (If none, just say 'no gifts')",
        "additional_wishes": "Do you have any additional wishes or instructions for this document? (If none, just say 'no additional wishes')"
    }
    return questions.get(field, "Could you provide more information?")
