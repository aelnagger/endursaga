import time
from typing import Optional, Protocol

from gpiozero import OutputDevice
from gpiozero.exc import GPIOZeroError


class GPIOOutput(Protocol):
    def on(self) -> None:
        ...

    def off(self) -> None:
        ...


class MosfetPulseController:
    def __init__(self, gpio_driver: Optional[GPIOOutput] = None, pin: int = 18) -> None:
        self._gpiozero_device: Optional[OutputDevice] = None
        if gpio_driver is None:
            self._gpiozero_device = OutputDevice(pin=pin, active_high=True, initial_value=False)
            self.gpio_driver: GPIOOutput = self._gpiozero_device
        else:
            self.gpio_driver = gpio_driver

    def _set_high(self) -> None:
        self.gpio_driver.on()

    def _set_low(self) -> None:
        self.gpio_driver.off()

    def close(self) -> None:
        if self._gpiozero_device is not None:
            self._gpiozero_device.close()

    def pulse_once(self, duration_seconds: float, off_duration_seconds: float = 0.0) -> None:
        if duration_seconds <= 0:
            raise ValueError("duration_seconds must be greater than 0")
        if off_duration_seconds < 0:
            raise ValueError("off_duration_seconds must be greater than or equal to 0")

        self._set_high()
        try:
            time.sleep(duration_seconds)
        finally:
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

    controller: Optional[MosfetPulseController] = None
    try:
        controller = MosfetPulseController(pin=18)
        controller.run(int(sys.argv[1]) if len(sys.argv) > 1 else 1, duration_seconds=1.0)
    except (GPIOZeroError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}")
        sys.exit(1)
    finally:
        if controller is not None:
            controller.close()
