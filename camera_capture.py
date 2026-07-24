import argparse
import sys
from pathlib import Path
from typing import Optional, Protocol, Sequence


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture an image from a Raspberry Pi camera")
    parser.add_argument("output_dir", nargs="?", default=".", help="Directory where the captured image will be saved")
    parser.add_argument("--filename", default="capture.jpg", help="Name of the captured image file")
    return parser


def main(args: Optional[Sequence[str]] = None, camera: Optional[CameraProtocol] = None) -> int:
    parser = build_parser()
    parsed_args = parser.parse_args(list(args) if args is not None else None)

    try:
        image_path = capture_image(parsed_args.output_dir, filename=parsed_args.filename, camera=camera)
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(str(image_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
