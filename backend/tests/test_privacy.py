import pytest
from services.privacy_service import PrivacyService

def test_privacy_masking_unmasking():
    service = PrivacyService()
    
    text = (
        "Contact John Doe at john.doe@acme.org or call +1-555-0199. "
        "The project budget is $2.5 million. Acme Corp is the lead partner."
    )
    
    masked, mapping = service.mask_text(text)
    
    # Assert placeholders are injected
    assert "[EMAIL_1]" in masked
    assert "[PHONE_1]" in masked
    assert "[BUDGET_1]" in masked
    
    # Assert sensitive values are removed
    assert "john.doe@acme.org" not in masked
    assert "+1-555-0199" not in masked
    assert "$2.5 million" not in masked
    
    # Test inverse operation
    unmasked = service.unmask_text(masked, mapping)
    assert unmasked == text
