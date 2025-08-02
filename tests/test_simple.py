"""
Simple tests to demonstrate the test infrastructure is working.
"""

import pytest


def test_simple_addition():
    """Simple test to verify pytest is working."""
    assert 2 + 2 == 4


def test_simple_string():
    """Simple string test."""
    assert "hello" + " world" == "hello world"


class TestSimpleClass:
    """Simple test class."""
    
    def test_class_method(self):
        """Test class method."""
        assert True
    
    def test_another_method(self):
        """Test another method."""
        assert 1 + 1 == 2


@pytest.mark.unit
def test_marked_test():
    """Test with pytest marker."""
    assert True


if __name__ == "__main__":
    pytest.main([__file__]) 