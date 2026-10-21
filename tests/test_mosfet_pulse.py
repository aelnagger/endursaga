import unittest
from unittest.mock import Mock, patch

from endursaga.mosfet_pulse import MosfetPulseController


class MosfetPulseControllerTests(unittest.TestCase):
    def test_pulse_once_turns_pin_on_and_then_off(self):
        gpio = Mock()
        controller = MosfetPulseController(gpio_driver=gpio, pin=18)

        controller.pulse_once(duration_seconds=0.2, off_duration_seconds=0.1)

        gpio.on.assert_called_once_with()
        gpio.off.assert_called_once_with()

    def test_run_emits_requested_number_of_pulses(self):
        gpio = Mock()
        controller = MosfetPulseController(gpio_driver=gpio, pin=18)

        controller.run(pulse_count=3, duration_seconds=0.1, off_duration_seconds=0.01)

        self.assertEqual(gpio.on.call_count, 3)
        self.assertEqual(gpio.off.call_count, 3)

    def test_invalid_duration_is_rejected(self):
        gpio = Mock()
        controller = MosfetPulseController(gpio_driver=gpio, pin=18)

        with self.assertRaises(ValueError):
            controller.pulse_once(duration_seconds=0)

    @patch("endursaga.mosfet_pulse.OutputDevice")
    def test_default_driver_uses_gpiozero_output_device(self, output_device_class):
        controller = MosfetPulseController(pin=18)

        output_device_class.assert_called_once_with(pin=18, active_high=True, initial_value=False)
        controller.pulse_once(duration_seconds=0.2)

        output_device = output_device_class.return_value
        output_device.on.assert_called_once_with()
        output_device.off.assert_called_once_with()
        controller.close()
        output_device.close.assert_called_once_with()

    def test_pulse_turns_output_off_if_wait_is_interrupted(self):
        gpio = Mock()
        controller = MosfetPulseController(gpio_driver=gpio)

        with patch("endursaga.mosfet_pulse.time.sleep", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                controller.pulse_once(duration_seconds=0.2)

        gpio.on.assert_called_once_with()
        gpio.off.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
