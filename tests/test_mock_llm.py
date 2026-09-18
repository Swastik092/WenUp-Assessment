import pytest
from backend.services.llm_service import MockLLMService
from backend.models.state import PersonalWishesState

@pytest.mark.asyncio
async def test_mock_llm_regex_patterns():
    mock = MockLLMService()
    state = PersonalWishesState()
    
    # 1. Multi-field: "My name is Jane Smith and I don't have kids"
    res1 = await mock.extract_information(state, "My name is Jane Smith and I don't have kids", [])
    assert len(res1.extractions) == 2
    
    name_ext = next(e for e in res1.extractions if e.field == "full_name")
    assert name_ext.value == "Jane Smith"
    assert name_ext.status == "confirmed"
    
    kids_ext = next(e for e in res1.extractions if e.field == "has_children")
    assert kids_ext.value is False
    assert kids_ext.status == "confirmed"
    
    # 2. Executor: "My brother James"
    res2 = await mock.extract_information(state, "My brother James", [])
    assert len(res2.extractions) == 2
    
    exec_name = next(e for e in res2.extractions if e.field == "executor.name")
    assert exec_name.value == "James"
    assert exec_name.status == "confirmed"
    
    exec_rel = next(e for e in res2.extractions if e.field == "executor.relationship")
    assert exec_rel.value == "Brother"
    assert exec_rel.status == "confirmed"
    
    # 3. Ambiguous worldwide-assets
    res3 = await mock.extract_information(state, "Yes worldwide asset but not everywhere", [])
    assert len(res3.extractions) == 1
    asset_ext = res3.extractions[0]
    assert asset_ext.field == "covers_worldwide_assets"
    assert asset_ext.value is None
    assert asset_ext.status == "ambiguous"
    assert asset_ext.note == "Worldwide assets ambiguous"
    
    # 4. Correction sentence
    res4 = await mock.extract_information(state, "Actually my name is John Smith", [])
    assert len(res4.extractions) == 1
    corr_ext = res4.extractions[0]
    assert corr_ext.field == "full_name"
    assert corr_ext.value == "John Smith"
    assert corr_ext.status == "confirmed"
