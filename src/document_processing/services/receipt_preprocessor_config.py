from dataclasses import dataclass

import numpy as np


@dataclass
class ReceiptPreprocessorConfig:
    # Perspective correction parameters
    # approximation_ratio: Controls how aggressively the algorithm approximates contours to polygons.
    #   Lower values (0.01-0.03) = more precise but may miss some boundaries.
    #   Higher values (0.05-0.1) = more aggressive approximation, may miss details.
    #   Default 0.02 is a good balance for most receipts.
    approximation_ratio: float = 0.02

    # min_area_ratio: Minimum area threshold for considering a contour as a receipt boundary.
    #   Lower values (0.2-0.3) = detect smaller receipts but may include noise.
    #   Higher values (0.5-0.7) = more strict, only detect large, clear receipts.
    #   Default 0.4 works well for most standard receipts.
    min_area_ratio: float = 0.4

    # boundary_tolerance: Tolerance for boundary detection to avoid incomplete boundaries.
    #   Lower values (1-3) = stricter, may miss slightly cropped receipts.
    #   Higher values (8-10) = more lenient, may include some false positives.
    #   Default 5 is good for most scenarios.
    boundary_tolerance: int = 5

    # Deskew parameters
    # canny_threshold1: Lower threshold for Canny edge detection in deskew.
    #   Lower values (20-40) = detect more edges, may include noise.
    #   Higher values (80-120) = detect fewer edges, may miss some text lines.
    #   Default 50 is a good middle ground.
    canny_threshold1: int = 50

    # canny_threshold2: Upper threshold for Canny edge detection in deskew.
    #   Lower values (100-120) = detect more edges, may include noise.
    #   Higher values (200-250) = detect fewer edges, may miss text lines.
    #   Default 150 balances sensitivity and accuracy.
    canny_threshold2: int = 150

    # hough_rho: Distance resolution of the Hough transform accumulator.
    #   Smaller values (0.5-1) = higher resolution, more accurate lines.
    #   Larger values (2-3) = lower resolution, may miss fine details.
    #   Default 1 is suitable for most receipts.
    hough_rho: int = 1

    # hough_theta: Angle resolution of the Hough transform accumulator.
    #   Smaller values (π/1800 - π/900) = higher angular resolution.
    #   Larger values (π/600 - π/300) = lower angular resolution.
    #   Default π/1800 provides good balance.
    hough_theta: float = np.pi / 1800

    # hough_threshold: Minimum votes for a line to be considered valid.
    #   Lower values (30-50) = detect more lines, may include false positives.
    #   Higher values (80-100) = more strict, fewer false positives.
    #   Default 60 works well for most receipts.
    hough_threshold: int = 60

    # min_line_length: Minimum line length in deskew detection.
    #   Lower values (15-25) = detect shorter lines, may include noise.
    #   Higher values (40-60) = detect longer lines, more reliable.
    #   Default 30 works well for most cases.
    min_line_length: int = 30

    # max_line_gap: Maximum gap between line segments to treat as one line.
    #   Lower values (5-15) = stricter line grouping, may miss some lines.
    #   Higher values (25-35) = more lenient, may include noise.
    #   Default 20 is suitable for most receipts.
    max_line_gap: int = 20

    # angle_tolerance: Maximum angle deviation from vertical/horizontal for deskew.
    #   Lower values (5-8) = stricter angle detection, may miss slight rotations.
    #   Higher values (15-20) = more lenient, may include slight rotations.
    #   Default 10 degrees works well for most receipts.
    angle_tolerance: float = 10.0

    # Text-line detection parameters
    # adaptive_threshold_block_size_min: Minimum block size for adaptive thresholding.
    #   Smaller values (15-25) = more sensitive to local contrast, may include noise.
    #   Larger values (35-45) = smoother thresholding, more robust to noise.
    #   Default 31 works well for most receipt text.
    adaptive_threshold_block_size_min: int = 31

    # adaptive_threshold_block_size_max: Maximum block size for adaptive thresholding.
    #   Smaller values (50-60) = more local thresholding, may include noise.
    #   Larger values (70-80) = more global thresholding, smoother results.
    #   Default 61 provides good balance.
    adaptive_threshold_block_size_max: int = 61

    # adaptive_threshold_offset: Offset value for adaptive thresholding.
    #   Negative values (-20 to -5) = more aggressive thresholding.
    #   Positive values (5-20) = more conservative thresholding.
    #   Default 15 works well for most receipts.
    adaptive_threshold_offset: int = 15

    # min_component_area: Minimum area for text components to be considered valid.
    #   Lower values (3-5) = detect smaller characters, may include noise.
    #   Higher values (10-15) = filter out smaller noise components.
    #   Default 8 is suitable for most receipt text.
    min_component_area: int = 8

    # min_component_height: Minimum height for text components to be considered valid.
    #   Lower values (2-4) = detect shorter characters.
    #   Higher values (6-8) = filter out very short components.
    #   Default 5 works well for typical receipt fonts.
    min_component_height: int = 5

    # max_component_height_ratio: Maximum height ratio relative to image height.
    #   Lower values (0.03-0.05) = filter out very tall components.
    #   Higher values (0.08-0.1) = allow taller components.
    #   Default 0.06 is good for most receipts.
    max_component_height_ratio: float = 0.06

    # max_component_width_ratio: Maximum width ratio relative to image width.
    #   Lower values (0.1-0.12) = filter out very wide components.
    #   Higher values (0.18-0.2) = allow wider components.
    #   Default 0.15 works well for most receipts.
    max_component_width_ratio: float = 0.15

    # max_aspect_ratio: Maximum width-to-height ratio for text components.
    #   Lower values (5-7) = stricter aspect ratio filtering.
    #   Higher values (10-12) = more lenient, allow more varied shapes.
    #   Default 8 works for most receipt text.
    max_aspect_ratio: int = 8

    # grouping_distance_ratio: Ratio for grouping text components into lines.
    #   Lower values (0.5-0.6) = stricter grouping, fewer lines.
    #   Higher values (0.7-0.8) = more lenient grouping, more lines.
    #   Default 0.65 is good for most receipts.
    grouping_distance_ratio: float = 0.65

    # Text-line dewarping parameters
    # min_line_span_ratio: Minimum span ratio for text lines to be considered for dewarping.
    #   Lower values (0.15-0.2) = detect shorter lines, may include noise.
    #   Higher values (0.25-0.3) = stricter detection, only longer lines.
    #   Default 0.20 works well for most receipts.
    min_line_span_ratio: float = 0.20

    # bin_count_min: Minimum number of bins for text-line dewarping.
    #   Lower values (3-5) = coarser analysis, faster.
    #   Higher values (8-10) = finer analysis, more accurate.
    #   Default 6 works well for most receipts.
    bin_count_min: int = 6

    # bin_count_max: Maximum number of bins for text-line dewarping.
    #   Lower values (50-60) = coarser analysis.
    #   Higher values (85-95) = finer analysis, more detailed.
    #   Default 80 is suitable for most receipts.
    bin_count_max: int = 80

    # taper_ratio: Ratio for tapering displacement at line edges.
    #   Lower values (0.02-0.03) = more gradual tapering.
    #   Higher values (0.05-0.07) = sharper tapering, less edge influence.
    #   Default 0.04 works well for most receipts.
    taper_ratio: float = 0.04

    # max_deviation_threshold: Minimum deviation threshold for text-line dewarping.
    #   Lower values (0.5-0.8) = detect smaller curvatures.
    #   Higher values (1.2-1.5) = stricter detection, only significant curvatures.
    #   Default 1.0 is good for most receipts.
    max_deviation_threshold: float = 1.0

    # max_deviation_limit: Maximum deviation limit for text-line dewarping.
    #   Lower values (0.01-0.03) = stricter limits, fewer corrections.
    #   Higher values (0.04-0.06) = more lenient, allow larger corrections.
    #   Default 0.02 is suitable for most receipts.
    max_deviation_limit: float = 0.02

    # Enhanced text-line dewarping parameters
    # min_line_quality_score: Minimum quality score for processing text lines
    min_line_quality_score: float = 0.7

    # curvature_adaptation_threshold: Threshold for adaptive correction scaling
    curvature_adaptation_threshold: float = 2.0

    # artifact_prevention_strength: Strength of artifact prevention measures
    artifact_prevention_strength: float = 0.8

    # multi_resolution_levels: Number of resolution levels for multi-resolution processing
    multi_resolution_levels: int = 3

    # Intentional ordering tilt
    # Positive values tilt text lines downwards towards the right.
    # 0.0 = disabled
    # 0.1-0.2 = very subtle tilt
    # 0.3-0.5 = more noticeable tilt
    ordering_tilt_degrees: float = 0.5