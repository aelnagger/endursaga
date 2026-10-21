from pathlib import Path
from typing import Optional

import cv2
import numpy as np

SUPPORTED_SIDES = (4, 6, 8, 10, 12, 20)
IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


class OrbDieRecognizer:
    """Recognize die labels by matching ORB features against labeled image templates."""

    def __init__(self, templates_dir: Path, sides: int = 6, first_face: int = 1) -> None:
        if sides not in SUPPORTED_SIDES:
            raise ValueError(f"sides must be one of {SUPPORTED_SIDES}")
        if first_face not in (0, 1):
            raise ValueError("first_face must be 0 or 1")

        self.sides = sides
        self.first_face = first_face
        self._orb = cv2.ORB_create(nfeatures=1500, fastThreshold=7)
        self._matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        self._templates: dict[int, list[np.ndarray]] = {}

        template_root = Path(templates_dir).expanduser()
        if not template_root.is_dir():
            raise FileNotFoundError(f"Template directory not found: {template_root}")

        for face in range(first_face, first_face + sides):
            descriptors_for_face = []
            face_directory = template_root / str(face)
            if face_directory.is_dir():
                for image_path in sorted(face_directory.iterdir()):
                    if image_path.suffix.lower() not in IMAGE_SUFFIXES:
                        continue
                    image = self._read_image(image_path)
                    if image is None:
                        continue
                    descriptors = self._descriptors(image)
                    if descriptors is not None and len(descriptors) >= 4:
                        descriptors_for_face.append(descriptors)
            if descriptors_for_face:
                self._templates[face] = descriptors_for_face

        missing_faces = sorted(set(range(first_face, first_face + sides)) - self._templates.keys())
        if missing_faces:
            raise ValueError(f"No usable ORB templates found for face labels: {missing_faces}")

    @staticmethod
    def _read_image(image_path: Path) -> Optional[np.ndarray]:
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            return None
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)

    def _descriptors(self, image: np.ndarray) -> Optional[np.ndarray]:
        _, descriptors = self._orb.detectAndCompute(image, None)
        return descriptors

    def evaluate(self, image_path: Path) -> Optional[int]:
        image = self._read_image(image_path)
        if image is None:
            return None
        query_descriptors = self._descriptors(image)
        if query_descriptors is None or len(query_descriptors) < 4:
            return None

        scores: dict[int, float] = {}
        for face, template_descriptors_list in self._templates.items():
            best_face_score = 0.0
            for template_descriptors in template_descriptors_list:
                if len(query_descriptors) < 2 or len(template_descriptors) < 2:
                    continue
                matches = self._matcher.knnMatch(template_descriptors, query_descriptors, k=2)
                good_matches = [
                    first_match
                    for pair in matches
                    if len(pair) == 2
                    for first_match, second_match in [pair]
                    if first_match.distance < 0.75 * second_match.distance
                ]
                score = len(good_matches) / len(template_descriptors)
                best_face_score = max(best_face_score, score)
            scores[face] = best_face_score

        ranked_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        if not ranked_scores or ranked_scores[0][1] < 0.12:
            return None
        if len(ranked_scores) > 1 and ranked_scores[0][1] - ranked_scores[1][1] < 0.02:
            return None
        return ranked_scores[0][0]