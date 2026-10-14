"""
Test file for ReceiptPreprocessor functionality.
"""
from src.document_processing.services.receipt_preprocessor import (
    ReceiptPreprocessor,
    ReceiptPreprocessorConfig,
)


def test_receipt_preprocessor_default_config():
    """Test that the default configuration works as expected."""
    preprocessor = ReceiptPreprocessor()

    # Check that default config is used
    assert isinstance(preprocessor.config, ReceiptPreprocessorConfig)

    # Check default values
    assert preprocessor.config.approximation_ratio == 0.02
    assert preprocessor.config.min_area_ratio == 0.4
    assert preprocessor.config.boundary_tolerance == 5


def test_receipt_preprocessor_custom_config():
    """Test that custom configuration works."""
    config = ReceiptPreprocessorConfig(
        approximation_ratio=0.05,
        min_area_ratio=0.3,
        boundary_tolerance=10
    )

    preprocessor = ReceiptPreprocessor(config=config)

    # Check that custom config is used
    assert preprocessor.config.approximation_ratio == 0.05
    assert preprocessor.config.min_area_ratio == 0.3
    assert preprocessor.config.boundary_tolerance == 10


def test_receipt_preprocessor_backward_compatibility():
    """Test that the old constructor syntax still works."""
    # This should work exactly as before
    preprocessor = ReceiptPreprocessor(
        perspective=True,
        textline_dewarp=True,
        deskew=True
    )

    # Should have default config
    assert isinstance(preprocessor.config, ReceiptPreprocessorConfig)
    assert preprocessor.config.approximation_ratio == 0.02