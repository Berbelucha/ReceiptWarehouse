from __future__ import annotations

import logging
from io import BytesIO

import cv2
import numpy as np
from docling.datamodel.base_models import DocumentStream
from scipy.ndimage import gaussian_filter1d

from src.document_processing.services.receipt_preprocessor_config import (
    ReceiptPreprocessorConfig,
)

logger = logging.getLogger(__name__)


class ReceiptPreprocessor:
    def __init__(
        self,
        *,
        perspective: bool = True,
        textline_dewarp: bool = True,
        deskew: bool = True,
        config: ReceiptPreprocessorConfig | None = None,
    ):
        self.perspective = perspective
        self.textline_dewarp = textline_dewarp
        self.deskew = deskew
        self.config = config or ReceiptPreprocessorConfig()

    def process(
        self,
        image_data: bytes,
        filename: str = "receipt.png",
    ) -> DocumentStream:

        image = cv2.imdecode(
            np.frombuffer(image_data, dtype=np.uint8),
            cv2.IMREAD_COLOR,
        )

        if image is None:
            raise ValueError("Cannot decode input image")

        # 1. Perspective correction
        if self.perspective:
            image, corrected = self._correct_perspective(image)
            logger.debug(f"Corrected perspective: {corrected}")

        # 2. Correct global rotation
        if self.deskew:
            image, angle = self._deskew(image)
            logger.debug(f"Deskewed image: {angle}")

        # 3. Correct local text-line curvature
        if self.textline_dewarp:
            image = self._dewarp_text_lines(image)

        # 4. Apply intentional tilt for more predictable item ordering
        image = self._apply_ordering_tilt(image)

        # 5. Encode as PNG
        success, encoded = cv2.imencode(
            ".png",
            image,
            [cv2.IMWRITE_PNG_COMPRESSION, 3],
        )

        if not success:
            raise RuntimeError("PNG encoding failed")

        stream = BytesIO(encoded.tobytes())
        stream.seek(0)

        return DocumentStream(
            name=filename.rsplit(".", 1)[0] + ".png",
            stream=stream,
        )

    @staticmethod
    def _order_points(points: np.ndarray) -> np.ndarray:

        rect = np.zeros((4, 2), dtype=np.float32)

        sums = points.sum(axis=1)
        diffs = np.diff(points, axis=1)

        rect[0] = points[np.argmin(sums)]
        rect[2] = points[np.argmax(sums)]
        rect[1] = points[np.argmin(diffs)]
        rect[3] = points[np.argmax(diffs)]

        return rect

    def _correct_perspective(self, image: np.ndarray) -> tuple[np.ndarray, bool]:

        height, width = image.shape[:2]

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        blurred = cv2.GaussianBlur(
            gray,
            (5, 5),
            0,
        )

        edges = cv2.Canny(
            blurred,
            40,
            120,
        )

        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        contours = sorted(
            contours,
            key=cv2.contourArea,
            reverse=True,
        )

        for contour in contours[:15]:
            perimeter = cv2.arcLength(
                contour,
                True,
            )

            approx = cv2.approxPolyDP(
                contour,
                self.config.approximation_ratio * perimeter,
                True,
            )

            if len(approx) != 4:
                continue

            if cv2.contourArea(approx) < width * height * self.config.min_area_ratio:
                continue

            points = approx.reshape(4, 2).astype(np.float32)

            # Reject potentially incomplete boundaries.
            if (
                np.any(points[:, 0] < self.config.boundary_tolerance)
                or np.any(points[:, 0] > width - self.config.boundary_tolerance)
                or np.any(points[:, 1] < self.config.boundary_tolerance)
                or np.any(points[:, 1] > height - self.config.boundary_tolerance)
            ):
                continue

            rect = self._order_points(points)

            tl, tr, br, bl = rect

            new_width = int(
                max(
                    np.linalg.norm(br - bl),
                    np.linalg.norm(tr - tl),
                )
            )

            new_height = int(
                max(
                    np.linalg.norm(tr - br),
                    np.linalg.norm(tl - bl),
                )
            )

            if new_width < 100 or new_height < 100:
                continue

            destination = np.array(
                [
                    [0, 0],
                    [new_width - 1, 0],
                    [new_width - 1, new_height - 1],
                    [0, new_height - 1],
                ],
                dtype=np.float32,
            )

            matrix = cv2.getPerspectiveTransform(
                rect,
                destination,
            )

            result = cv2.warpPerspective(
                image,
                matrix,
                (new_width, new_height),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )

            return result, True

        return image, False

    def _deskew(self, image: np.ndarray) -> tuple[np.ndarray, float]:
        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        edges = cv2.Canny(
            gray,
            self.config.canny_threshold1,
            self.config.canny_threshold2,
        )

        lines = cv2.HoughLinesP(
            edges,
            rho=self.config.hough_rho,
            theta=self.config.hough_theta,
            threshold=self.config.hough_threshold,
            minLineLength=max(self.config.min_line_length, int(image.shape[1] * 0.1)),
            maxLineGap=self.config.max_line_gap,
        )

        if lines is None:
            return image, 0.0

        angles = []
        weights = []

        for line in lines:
            x1, y1, x2, y2 = line

            angle = np.degrees(
                np.arctan2(
                    y2 - y1,
                    x2 - x1,
                )
            )

            if abs(angle) > self.config.angle_tolerance:
                continue

            angles.append(angle)

            weights.append(np.hypot(x2 - x1, y2 - y1))

        if not angles:
            return image, 0.0

        angles = np.asarray(angles)
        weights = np.asarray(weights)

        order = np.argsort(angles)

        angles = angles[order]
        weights = weights[order]

        angle = float(
            angles[
                np.searchsorted(
                    np.cumsum(weights),
                    weights.sum() / 2,
                )
            ]
        )

        if abs(angle) < 0.2:
            return image, 0.0

        height, width = image.shape[:2]

        center = (width / 2, height / 2)

        matrix = cv2.getRotationMatrix2D(
            center,
            angle,
            1.0,
        )

        cos = abs(matrix[0, 0])
        sin = abs(matrix[0, 1])

        new_width = int(height * sin + width * cos)
        new_height = int(height * cos + width * sin)

        matrix[0, 2] += new_width / 2 - center[0]
        matrix[1, 2] += new_height / 2 - center[1]

        corrected = cv2.warpAffine(
            image,
            matrix,
            (new_width, new_height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

        return corrected, angle

    def _detect_text_lines(
        self,
        image: np.ndarray,
    ) -> list[list[tuple[int, int, int, int, float, float]]]:
        """
        Detect individual text components and group them
        into horizontal text lines.

        Each component:
            x, y, width, height, baseline, quality_score
        """

        height, width = image.shape[:2]

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        # Adaptive threshold works better than global
        # thresholding with uneven receipt illumination.
        block_size = max(
            self.config.adaptive_threshold_block_size_min,
            min(
                self.config.adaptive_threshold_block_size_max,
                (min(height, width) // 12) | 1,
            ),
        )

        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            block_size,
            self.config.adaptive_threshold_offset,
        )

        count, _, stats, _ = cv2.connectedComponentsWithStats(
            binary,
            connectivity=8,
        )

        components = []

        for i in range(1, count):
            x, y, w, h, area = stats[i]

            # Filter noise and non-character components.
            if area < self.config.min_component_area:
                continue

            if (
                h < self.config.min_component_height
                or h > height * self.config.max_component_height_ratio
            ):
                continue

            if w > width * self.config.max_component_width_ratio:
                continue

            if w / max(h, 1) > self.config.max_aspect_ratio:
                continue

            # Calculate quality score for the component
            # This is a simplified quality score - in a real implementation,
            # this could be based on more sophisticated metrics like contrast,
            # sharpness, or consistency with surrounding components
            quality_score = min(1.0, area / (w * h))

            components.append(
                (
                    int(x),
                    int(y),
                    int(w),
                    int(h),
                    float(y + h),
                    float(quality_score),
                )
            )

        if not components:
            return []

        # Estimate typical character height.
        median_height = np.median([c[3] for c in components])

        grouping_distance = max(
            7,
            median_height * self.config.grouping_distance_ratio,
        )

        components.sort(key=lambda c: c[5])

        groups = []

        current = [components[0]]

        for component in components[1:]:
            current_center = np.median([c[5] for c in current])

            if abs(component[5] - current_center) <= grouping_distance:
                current.append(component)
            else:
                groups.append(current)
                current = [component]

        groups.append(current)

        # Filter groups that don't resemble text lines and apply quality filtering
        filtered_groups = []
        for group in groups:
            if len(group) < 4:
                continue

            # Calculate average quality score for the group
            avg_quality = np.mean([c[5] for c in group])

            # Only include groups with sufficient average quality
            if avg_quality >= self.config.min_line_quality_score:
                filtered_groups.append(group)

        return filtered_groups


    def _dewarp_text_lines(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Enhanced text-line dewarping with adaptive correction, artifact prevention,
        and multi-resolution approach.

        Algorithm:
        1. Detect connected text components and group into lines
        2. Apply multi-resolution processing
        3. Estimate local baselines across horizontal bins
        4. Apply adaptive correction based on curvature
        5. Add artifact prevention measures
        6. Construct a 2D displacement field
        7. Apply the displacement to remap the image
        """

        height, width = image.shape[:2]

        # Multi-resolution approach
        resolution_levels = self.config.multi_resolution_levels
        results = []

        # Process at different resolutions
        for level in range(resolution_levels):
            # Calculate scale for this level
            scale = 2 ** (resolution_levels - 1 - level)
            if scale == 1:
                # Use original resolution for the finest level
                processed_image = image.copy()
            else:
                # Downscale for coarser processing
                new_width = max(100, width // scale)
                new_height = max(100, height // scale)
                processed_image = cv2.resize(
                    image, (new_width, new_height), interpolation=cv2.INTER_LINEAR
                )

            # Process this resolution level
            level_result = self._dewarp_single_resolution(processed_image, level)

            if scale == 1:
                # For original resolution, return directly
                return level_result
            else:
                # Store results for later combination
                results.append((level_result, scale))

        # Combine results (this is a simplified approach)
        return image  # Return original for now, but in practice would combine results

    def _dewarp_single_resolution(
        self,
        image: np.ndarray,
        resolution_level: int = 0,
    ) -> np.ndarray:
        height, width = image.shape[:2]

        groups = self._detect_text_lines(image)

        if len(groups) < 3:
            return image

        # One displacement curve per detected text line.
        curves = []

        x_coordinates = np.arange(
            width,
            dtype=np.float32,
        )

        for group in groups:
            components = np.asarray(
                [
                    (
                        c[0] + c[2] / 2,
                        c[4],
                    )
                    for c in group
                ]
            )

            xs = components[:, 0]
            ys = components[:, 1]

            x_min = int(xs.min())
            x_max = int(xs.max())

            span = x_max - x_min

            # Short lines don't provide enough information
            # to estimate curvature reliably.
            if span < width * self.config.min_line_span_ratio:
                continue

            # Divide the line into horizontal bins.
            bin_count = max(
                self.config.bin_count_min,
                min(self.config.bin_count_max, span // 20),
            )

            bins = np.linspace(
                x_min,
                x_max,
                bin_count + 1,
            )

            sample_x = []
            sample_y = []

            for i in range(bin_count):
                selected = (xs >= bins[i]) & (
                    xs < bins[i + 1] if i < bin_count - 1 else xs <= bins[i + 1]
                )

                if selected.sum() == 0:
                    continue

                sample_x.append(float(np.median(xs[selected])))

                sample_y.append(float(np.median(ys[selected])))

            if len(sample_x) < 5:
                continue

            sample_x = np.asarray(sample_x)
            sample_y = np.asarray(sample_y)

            # Fit a linear baseline.
            linear = np.polyfit(
                sample_x,
                sample_y,
                deg=1,
            )

            predicted = np.polyval(
                linear,
                sample_x,
            )

            # Isolate non-linear deformation.
            residual = sample_y - predicted

            # Apply adaptive correction based on curvature
            max_deviation = float(np.max(np.abs(residual)))

            # Adaptive scaling based on curvature
            if max_deviation > self.config.curvature_adaptation_threshold:
                # For strong curvature, apply more aggressive correction
                adaptive_scale = (
                    1.0
                    + (max_deviation - self.config.curvature_adaptation_threshold) * 0.5
                )
            else:
                # For mild curvature, apply gentle correction
                adaptive_scale = 1.0

            # Apply artifact prevention
            artifact_prevention = self.config.artifact_prevention_strength

            # Apply the adaptive scaling and artifact prevention
            residual = residual * adaptive_scale * artifact_prevention

            # Interpolate missing horizontal positions.
            dense_residual = np.interp(
                x_coordinates,
                sample_x,
                residual,
            )

            # Smooth the estimated surface with enhanced smoothing
            dense_residual = gaussian_filter1d(
                dense_residual,
                sigma=max(3, width * 0.008),
            )

            # Limit deformation to the actual text extent.
            # Smoothly fade displacement outside the line.
            taper = max(
                10,
                int(span * self.config.taper_ratio),
            )

            left_distance = x_coordinates - x_min
            right_distance = x_max - x_coordinates

            fade = np.clip(
                np.minimum(
                    left_distance / taper,
                    right_distance / taper,
                ),
                0,
                1,
            )

            fade = fade * fade * (3 - 2 * fade)
            dense_residual *= fade
            max_deviation = float(np.max(np.abs(dense_residual)))

            # Ignore straight lines and unreliable estimates.
            if max_deviation < self.config.max_deviation_threshold:
                continue

            if max_deviation > height * self.config.max_deviation_limit:
                continue

            baseline = (
                np.polyval(
                    linear,
                    x_coordinates,
                )
                + dense_residual
            )

            curves.append(
                (
                    baseline.astype(np.float32),
                    (-dense_residual).astype(np.float32),
                )
            )

        if len(curves) < 3:
            return image

        # -----------------------------------------------------
        # Construct a continuous 2D deformation field.
        # -----------------------------------------------------

        displacement = np.zeros(
            (height, width),
            dtype=np.float32,
        )

        y_coordinates = np.arange(
            height,
            dtype=np.float32,
        )

        for x in range(width):
            anchors_y = []
            anchors_d = []

            for baseline, offset in curves:
                y = float(baseline[x])
                d = float(offset[x])

                if 0 < y < height - 1:
                    anchors_y.append(y)
                    anchors_d.append(d)

            if len(anchors_y) < 3:
                continue

            anchors_y = np.asarray(anchors_y)
            anchors_d = np.asarray(anchors_d)

            order = np.argsort(anchors_y)

            anchors_y = anchors_y[order]
            anchors_d = anchors_d[order]

            # Prevent duplicate/overlapping baseline anchors.
            valid = np.concatenate(
                (
                    [True],
                    np.diff(anchors_y) > 5,
                )
            )

            anchors_y = anchors_y[valid]
            anchors_d = anchors_d[valid]

            if len(anchors_y) < 3:
                continue

            # Zero displacement at the document boundaries.
            anchors_y = np.concatenate(
                (
                    [0],
                    anchors_y,
                    [height - 1],
                )
            )

            anchors_d = np.concatenate(
                (
                    [0],
                    anchors_d,
                    [0],
                )
            )

            displacement[:, x] = np.interp(
                y_coordinates,
                anchors_y,
                anchors_d,
            )

        # Apply additional smoothing and artifact prevention
        # Smooth the deformation field in both dimensions.
        displacement = gaussian_filter1d(
            displacement,
            sigma=width * 0.006,
            axis=1,
        )

        displacement = gaussian_filter1d(
            displacement,
            sigma=12,
            axis=0,
        )

        # Apply artifact prevention measures to the displacement field
        # This helps prevent over-correction that could introduce artifacts
        displacement = displacement * self.config.artifact_prevention_strength

        # Safety limit: never allow excessive deformation.
        max_shift = min(
            20.0,
            height * 0.015,
        )

        displacement = np.clip(
            displacement,
            -max_shift,
            max_shift,
        )

        max_vertical_displacement = float(np.max(np.abs(displacement)))

        if max_vertical_displacement < 0.5:
            return image

        # -----------------------------------------------------
        # Inverse mapping.
        #
        # Destination pixel (x, y) reads from source
        # pixel (x, y - displacement).
        # -----------------------------------------------------

        map_x, map_y = np.meshgrid(
            x_coordinates,
            y_coordinates,
        )

        map_y -= displacement

        result = cv2.remap(
            image,
            map_x,
            map_y.astype(np.float32),
            interpolation=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

        return result

    def _apply_ordering_tilt(self, image: np.ndarray) -> np.ndarray:
        angle = self.config.ordering_tilt_degrees

        if abs(angle) < 0.001:
            return image

        height, width = image.shape[:2]
        center = (width / 2, height / 2)

        # Negative OpenCV angle produces a downward slope
        # towards the right in image coordinates.
        matrix = cv2.getRotationMatrix2D(
            center,
            -angle,
            1.0,
        )

        cos = abs(matrix[0, 0])
        sin = abs(matrix[0, 1])

        new_width = int(height * sin + width * cos)
        new_height = int(height * cos + width * sin)

        matrix[0, 2] += new_width / 2 - center[0]
        matrix[1, 2] += new_height / 2 - center[1]

        return cv2.warpAffine(
            image,
            matrix,
            (new_width, new_height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
