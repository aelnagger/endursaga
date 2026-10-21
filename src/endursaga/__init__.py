import argparse
import sys
import time
from importlib import import_module
from pathlib import Path
from typing import Callable, Optional, Sequence

from gpiozero.exc import GPIOZeroError

from endursaga.camera_capture import CameraProtocol, capture_image
from endursaga.dice_vision import OrbDieRecognizer, SUPPORTED_SIDES
from endursaga.mosfet_pulse import GPIOOutput, MosfetPulseController

Evaluator = Callable[[Path], Optional[int]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run dice fairness trials")
    parser.add_argument("iterations", type=int, help="Number of trials to run")
    parser.add_argument("--output-dir", default="captures", help="Directory for captured images")
    parser.add_argument("--pulse-seconds", type=float, default=1.0, help="Duration of each GPIO pulse")
    parser.add_argument("--settle-seconds", type=float, default=1.0, help="Delay between the pulse and image capture")
    parser.add_argument(
        "--evaluator",
        help="Custom image evaluator as module:function; it should return a face label or None",
    )
    parser.add_argument("--templates-dir", default="templates", help="Directory containing labeled face templates")
    parser.add_argument("--sides", type=int, choices=SUPPORTED_SIDES, default=6, help="Number of die faces")
    parser.add_argument(
        "--first-face",
        type=int,
        choices=(0, 1),
        default=1,
        help="Lowest face label (use 0 for a d10 labeled 0-9)",
    )
    return parser


def _load_evaluator(specification: str) -> Evaluator:
    module_name, separator, function_name = specification.partition(":")
    if not separator or not module_name or not function_name:
        raise ValueError("evaluator must use the format module:function")

    evaluator = getattr(import_module(module_name), function_name, None)
    if not callable(evaluator):
        raise ValueError(f"evaluator {specification!r} is not callable")
    return evaluator


def run_trials(
    iterations: int,
    evaluator: Evaluator,
    output_dir: str = "captures",
    camera: Optional[CameraProtocol] = None,
    gpio_driver: Optional[GPIOOutput] = None,
    pulse_seconds: float = 1.0,
    settle_seconds: float = 1.0,
    sides: int = 6,
    first_face: int = 1,
    pause: Optional[Callable[[float], None]] = None,
) -> dict[int, Optional[int]]:
    if iterations <= 0:
        raise ValueError("iterations must be greater than 0")
    if pulse_seconds <= 0:
        raise ValueError("pulse_seconds must be greater than 0")
    if settle_seconds < 0:
        raise ValueError("settle_seconds must be greater than or equal to 0")
    if sides not in SUPPORTED_SIDES:
        raise ValueError(f"sides must be one of {SUPPORTED_SIDES}")
    if first_face not in (0, 1):
        raise ValueError("first_face must be 0 or 1")

    wait = pause or time.sleep
    controller = MosfetPulseController(gpio_driver=gpio_driver)
    results: dict[int, Optional[int]] = {}
    try:
        for iteration in range(1, iterations + 1):
            controller.pulse_once(duration_seconds=pulse_seconds)
            if settle_seconds > 0:
                wait(settle_seconds)

            image_path = capture_image(
                output_dir,
                filename=f"trial_{iteration:04d}.jpg",
                camera=camera,
            )
            face = evaluator(image_path)
            if face is not None and (
                not isinstance(face, int)
                or isinstance(face, bool)
                or face not in range(first_face, first_face + sides)
            ):
                raise ValueError(f"evaluator returned invalid d{sides} face: {face!r}")
            results[iteration] = face
    finally:
        controller.close()

    return results


def analyze_results(
    results: dict[int, Optional[int]], sides: int = 6, first_face: int = 1
) -> tuple[dict[int, int], Optional[float]]:
    if sides not in SUPPORTED_SIDES:
        raise ValueError(f"sides must be one of {SUPPORTED_SIDES}")
    if first_face not in (0, 1):
        raise ValueError("first_face must be 0 or 1")

    face_counts = {face: 0 for face in range(first_face, first_face + sides)}
    for face in results.values():
        if face is not None:
            face_counts[face] += 1

    recognized = sum(face_counts.values())
    if recognized == 0:
        return face_counts, None

    expected = recognized / sides
    chi_square = sum((count - expected) ** 2 / expected for count in face_counts.values())
    return face_counts, chi_square


def main(
    args: Optional[Sequence[str]] = None,
    camera: Optional[CameraProtocol] = None,
    gpio_driver: Optional[GPIOOutput] = None,
    evaluator: Optional[Evaluator] = None,
    pause: Optional[Callable[[float], None]] = None,
) -> int:
    parsed_args = build_parser().parse_args(list(args) if args is not None else None)

    if evaluator is None and parsed_args.evaluator:
        try:
            evaluator = _load_evaluator(parsed_args.evaluator)
        except (ImportError, AttributeError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
    if evaluator is None:
        try:
            recognizer = OrbDieRecognizer(
                Path(parsed_args.templates_dir),
                sides=parsed_args.sides,
                first_face=parsed_args.first_face,
            )
        except (FileNotFoundError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        evaluator = recognizer.evaluate

    try:
        results = run_trials(
            iterations=parsed_args.iterations,
            evaluator=evaluator,
            output_dir=parsed_args.output_dir,
            camera=camera,
            gpio_driver=gpio_driver,
            pulse_seconds=parsed_args.pulse_seconds,
            settle_seconds=parsed_args.settle_seconds,
            sides=parsed_args.sides,
            first_face=parsed_args.first_face,
            pause=pause,
        )
    except (GPIOZeroError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    face_counts, chi_square = analyze_results(
        results,
        sides=parsed_args.sides,
        first_face=parsed_args.first_face,
    )
    recognized = sum(face_counts.values())
    print(f"Completed {len(results)} iterations; recognized {recognized}, unrecognized {len(results) - recognized}.")
    print("Face counts: " + ", ".join(f"{face}: {count}" for face, count in face_counts.items()))
    if chi_square is not None:
        print(f"Chi-square statistic (df={parsed_args.sides - 1}): {chi_square:.3f}")
    else:
        print("Chi-square statistic unavailable: no results were recognized.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
