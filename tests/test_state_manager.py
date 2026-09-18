from backend.models.state import PersonalWishesState
from backend.models.llm_models import LLMExtractionResult, FieldExtraction
from backend.services.state_manager import apply_updates, get_missing_fields

def test_missing_fields():
    state = PersonalWishesState()
    missing = get_missing_fields(state)
    assert "full_name" in missing
    assert "home_address" in missing

def test_apply_updates_basic():
    state = PersonalWishesState()
    extractions = [
        FieldExtraction(field="full_name", value="John Smith", status="confirmed"),
        FieldExtraction(field="home_address", value="10 Main Street", status="confirmed")
    ]
    new_state, notes = apply_updates(state, extractions)
    assert new_state.full_name == "John Smith"
    assert new_state.home_address == "10 Main Street"
    assert not notes

def test_apply_updates_children_dependency():
    state = PersonalWishesState()
    
    # Children = false
    extractions = [FieldExtraction(field="has_children", value=False, status="confirmed")]
    new_state, _ = apply_updates(state, extractions)
    assert new_state.has_children is False
    assert "children_names" not in get_missing_fields(new_state)

    # Children = true
    extractions2 = [FieldExtraction(field="has_children", value=True, status="confirmed")]
    new_state2, _ = apply_updates(state, extractions2)
    assert new_state2.has_children is True
    assert "children_names" in get_missing_fields(new_state2)
    
    # Correction: was true, now false
    new_state2.children_names = ["Sarah"]
    extractions3 = [FieldExtraction(field="has_children", value=False, status="confirmed")]
    new_state3, _ = apply_updates(new_state2, extractions3)
    assert new_state3.has_children is False
    assert new_state3.children_names == [] # Should be cleared
    
def test_partial_application():
    state = PersonalWishesState(full_name=None, covers_worldwide_assets=None)
    extractions = [
        FieldExtraction(field="full_name", value="John", status="confirmed"),
        FieldExtraction(field="covers_worldwide_assets", value=True, status="ambiguous", note="Worldwide assets ambiguous")
    ]
    new_state, notes = apply_updates(state, extractions)
    assert new_state.full_name == "John" # Confirmed applies
    assert new_state.covers_worldwide_assets is None # Ambiguous does not apply
    assert notes == ["Worldwide assets ambiguous"] # Note returned
