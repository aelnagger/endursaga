import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from endursaga.camera_capture import capture_image, main


class FakeCamera:
    def __init__(self):
        self.saved_paths = []

    def capture(self, output_path, use_video_port=False):
        self.saved_paths.append(str(output_path))
        Path(output_path).write_bytes(b"fake-image")


class CameraCaptureTests(unittest.TestCase):
    def test_capture_image_saves_file_to_requested_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            camera = FakeCamera()
            image_path = capture_image(tmpdir, filename="die.jpg", camera=camera)

            self.assertTrue(image_path.exists())
            self.assertEqual(image_path.name, "die.jpg")
            self.assertEqual(camera.saved_paths, [str(image_path)])

    def test_capture_image_uses_default_filename_when_not_provided(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            camera = FakeCamera()
            image_path = capture_image(tmpdir, camera=camera)

            self.assertTrue(image_path.exists())
            self.assertEqual(image_path.name, "capture.jpg")

    def test_capture_image_requires_a_directory(self):
        with self.assertRaises(ValueError):
            capture_image("   ", camera=FakeCamera())

    def test_main_captures_image_from_cli_arguments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            camera = FakeCamera()
            output_dir = Path(tmpdir)
            exit_code = main([str(output_dir), "--filename", "cli.jpg"], camera=camera)

            self.assertEqual(exit_code, 0)
            self.assertEqual(camera.saved_paths, [str(output_dir / "cli.jpg")])
            self.assertTrue((output_dir / "cli.jpg").exists())

    def test_capture_image_uses_picamzero_when_available(self):
        class FakePicamZeroCamera:
            def __init__(self):
                self.calls = []

            def capture(self, output_path, use_video_port=False):
                self.calls.append((output_path, use_video_port))
                Path(output_path).write_bytes(b"picamzero")

        fake_module = types.SimpleNamespace(Camera=FakePicamZeroCamera)

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict("sys.modules", {"picamzero": fake_module}):
                image_path = capture_image(tmpdir)

            self.assertTrue(image_path.exists())
            self.assertEqual(image_path.name, "capture.jpg")
            self.assertEqual(image_path.read_bytes(), b"picamzero")


if __name__ == "__main__":
    unittest.main()
