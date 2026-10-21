import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from endursaga.dice_vision import OrbDieRecognizer


class DiceVisionTests(unittest.TestCase):
    def test_recognizes_d20_label_after_color_change(self):
        with tempfile.TemporaryDirectory() as output_dir:
            template_root = Path(output_dir) / "templates"
            self._write_d20_templates(template_root)
            image_path = Path(output_dir) / "query.png"
            query = np.full((240, 360, 3), (0, 220, 255), dtype=np.uint8)
            cv2.putText(query, "20", (45, 175), cv2.FONT_HERSHEY_SIMPLEX, 4, (200, 0, 0), 8)
            self.assertTrue(cv2.imwrite(str(image_path), query))

            recognizer = OrbDieRecognizer(template_root, sides=20)
            self.assertEqual(recognizer.evaluate(image_path), 20)

    def test_returns_none_for_unmatched_image(self):
        with tempfile.TemporaryDirectory() as output_dir:
            template_root = Path(output_dir) / "templates"
            self._write_d20_templates(template_root)
            image_path = Path(output_dir) / "blank.png"
            self.assertTrue(cv2.imwrite(str(image_path), np.full((240, 360), 255, dtype=np.uint8)))

            recognizer = OrbDieRecognizer(template_root, sides=20)
            self.assertIsNone(recognizer.evaluate(image_path))

    def test_evaluate_die_image_returns_none_for_unreadable_image(self):
        with tempfile.TemporaryDirectory() as output_dir:
            template_root = Path(output_dir) / "templates"
            self._write_d20_templates(template_root)
            recognizer = OrbDieRecognizer(template_root, sides=20)
            self.assertIsNone(recognizer.evaluate(Path(output_dir) / "missing.png"))

    @staticmethod
    def _write_d20_templates(template_root):
        for face in range(1, 21):
            face_directory = template_root / str(face)
            face_directory.mkdir(parents=True)
            image = np.full((240, 360), 255, dtype=np.uint8)
            cv2.putText(image, str(face), (45, 175), cv2.FONT_HERSHEY_SIMPLEX, 4, 0, 8)
            if not cv2.imwrite(str(face_directory / "sample.png"), image):
                raise AssertionError(f"Could not write template for face {face}")


if __name__ == "__main__":
    unittest.main()