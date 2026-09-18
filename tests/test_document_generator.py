from backend.models.state import PersonalWishesState, Executor
from backend.services.document_generator import generate_document

def test_document_generation():
    # TEST 10 - Document generation
    state = PersonalWishesState(
        full_name="Jane Smith",
        home_address="123 Example St",
        covers_worldwide_assets=True,
        has_children=False,
        executor=Executor(name="John Doe", relationship="Friend"),
        specific_gifts=["A gold watch"],
        additional_wishes="Bury me in the forest."
    )
    doc = generate_document(state)
    assert "FICTIONAL DOCUMENT" in doc
    assert "NOT LEGAL ADVICE" in doc
    assert "Jane Smith" in doc
    assert "123 Example St" in doc
    assert "Friend" in doc
    assert "A gold watch" in doc
    assert "Bury me in the forest." in doc
    
def test_document_generation_unknowns():
    # TEST 12 - Unknowns remain unknown
    state = PersonalWishesState()
    doc = generate_document(state)
    assert "Not provided" in doc
    # Shouldn't fabricate
    assert "Jane Smith" not in doc
    assert "Yes" not in doc
