import time
from typing import Optional


class GPIOStub:
    """Minimal GPIO abstraction for tests and local development."""

    def set_high(self, pin: int) -> None:
        raise NotImplementedError

    def set_low(self, pin: int) -> None:
        raise NotImplementedError


class MosfetPulseController:
    def __init__(self, gpio_driver: Optional[GPIOStub] = None, pin: int = 18) -> None:
        self.gpio_driver = gpio_driver
        self.pin = pin

    def _set_high(self) -> None:
        if self.gpio_driver is None:
            raise RuntimeError("No GPIO driver configured")
        self.gpio_driver.set_high(self.pin)

    def _set_low(self) -> None:
        if self.gpio_driver is None:
            raise RuntimeError("No GPIO driver configured")
        self.gpio_driver.set_low(self.pin)

    def pulse_once(self, duration_seconds: float, off_duration_seconds: float = 0.0) -> None:
        if duration_seconds <= 0:
            raise ValueError("duration_seconds must be greater than 0")
        if off_duration_seconds < 0:
            raise ValueError("off_duration_seconds must be greater than or equal to 0")

        self._set_high()
        time.sleep(duration_seconds)
        self._set_low()

        if off_duration_seconds > 0:
            time.sleep(off_duration_seconds)

    def run(self, pulse_count: int, duration_seconds: float, off_duration_seconds: float = 0.0) -> None:
        if pulse_count <= 0:
            raise ValueError("pulse_count must be greater than 0")

        for _ in range(pulse_count):
            self.pulse_once(duration_seconds=duration_seconds, off_duration_seconds=off_duration_seconds)


if __name__ == "__main__":
    import sys

    controller = MosfetPulseController(pin=18)
    try:
        controller.run(int(sys.argv[1]) if len(sys.argv) > 1 else 1, duration_seconds=1.0)
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}")
        sys.exit(1)
