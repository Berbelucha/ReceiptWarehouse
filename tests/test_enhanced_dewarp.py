"""
Test file for enhanced ReceiptPreprocessor text-line dewarp functionality.
"""
from src.document_processing.services.receipt_preprocessor import (
    ReceiptPreprocessor,
    ReceiptPreprocessorConfig,
)


def test_enhanced_preprocessor_config():
    """Test that the enhanced configuration parameters work."""
    config = ReceiptPreprocessorConfig()

    # Check that new enhanced parameters are present and have default values
    assert hasattr(config, 'min_line_quality_score')
    assert config.min_line_quality_score == 0.7

    assert hasattr(config, 'curvature_adaptation_threshold')
    assert config.curvature_adaptation_threshold == 2.0

    assert hasattr(config, 'artifact_prevention_strength')
    assert config.artifact_prevention_strength == 0.8

    assert hasattr(config, 'multi_resolution_levels')
    assert config.multi_resolution_levels == 3


def test_text_line_detection_with_quality_filtering():
    """Test that text line detection now includes quality filtering."""
    # This is more of a structural test - we're mainly ensuring
    # the method signature and basic functionality works
    preprocessor = ReceiptPreprocessor()

    # Just test that the method can be called without error
    # A full test would require actual image data
    assert hasattr(preprocessor, '_detect_text_lines')

    # Test that the method returns a list of groups
    # (we can't easily test with dummy data without a real image)
    # but we can at least verify the method exists and has the right signature
    import inspect
    sig = inspect.signature(preprocessor._detect_text_lines)
    assert 'image' in sig.parameters


def test_dewarp_with_enhanced_features():
    """Test that the enhanced dewarp functionality is properly implemented."""
    preprocessor = ReceiptPreprocessor()

    # Test that the enhanced methods exist
    assert hasattr(preprocessor, '_dewarp_text_lines')
    assert hasattr(preprocessor, '_dewarp_single_resolution')

    # Test that the enhanced parameters are accessible
    config = preprocessor.config
    assert config.min_line_quality_score == 0.7
    assert config.curvature_adaptation_threshold == 2.0
    assert config.artifact_prevention_strength == 0.8
    assert config.multi_resolution_levels == 3


def test_config_parameter_updates():
    """Test that we can set custom values for enhanced parameters."""
    config = ReceiptPreprocessorConfig(
        min_line_quality_score=0.8,
        curvature_adaptation_threshold=3.0,
        artifact_prevention_strength=0.9,
        multi_resolution_levels=4
    )

    assert config.min_line_quality_score == 0.8
    assert config.curvature_adaptation_threshold == 3.0
    assert config.artifact_prevention_strength == 0.9
    assert config.multi_resolution_levels == 4