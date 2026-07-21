import unittest
from unittest.mock import Mock

from mosfet_pulse import MosfetPulseController


class MosfetPulseControllerTests(unittest.TestCase):
    def test_pulse_once_turns_pin_on_and_then_off(self):
        gpio = Mock()
        controller = MosfetPulseController(gpio_driver=gpio, pin=18)

        controller.pulse_once(duration_seconds=0.2, off_duration_seconds=0.1)

        self.assertEqual(gpio.set_high.call_count, 1)
        self.assertEqual(gpio.set_low.call_count, 1)
        gpio.set_high.assert_called_once_with(18)
        gpio.set_low.assert_called_once_with(18)

    def test_run_emits_requested_number_of_pulses(self):
        gpio = Mock()
        controller = MosfetPulseController(gpio_driver=gpio, pin=18)

        controller.run(pulse_count=3, duration_seconds=0.1, off_duration_seconds=0.01)

        self.assertEqual(gpio.set_high.call_count, 3)
        self.assertEqual(gpio.set_low.call_count, 3)

    def test_invalid_duration_is_rejected(self):
        gpio = Mock()
        controller = MosfetPulseController(gpio_driver=gpio, pin=18)

        with self.assertRaises(ValueError):
            controller.pulse_once(duration_seconds=0)


if __name__ == "__main__":
    unittest.main()
