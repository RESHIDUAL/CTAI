import pytest
from app.services.adversarial_runner import AdversarialTestRunner

def test_adversarial_suite_execution():
    results = AdversarialTestRunner.run_all_tests()
    assert len(results) == 8
    for test in results:
        assert test["all_passed"] is True, f"Failed test {test['name']}: {test}"
