from pathlib import Path
from typing import Optional, Protocol


class CameraProtocol(Protocol):
    def capture(self, output_path: str, use_video_port: bool = False) -> None:
        ...


def capture_image(output_dir: str, filename: str = "capture.jpg", camera: Optional[CameraProtocol] = None) -> Path:
    if not output_dir or not output_dir.strip():
        raise ValueError("output_dir must be a non-empty string")

    target_dir = Path(output_dir).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    image_path = target_dir / filename

    if camera is None:
        try:
            from picamera import PiCamera
        except ImportError as exc:
            raise RuntimeError("picamera is required for real captures on a Raspberry Pi") from exc

        camera = PiCamera()

    camera.capture(str(image_path), use_video_port=False)
    return image_path
