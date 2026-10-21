import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from endursaga import analyze_results, main, run_trials


class FakeCamera:
    def __init__(self, events):
        self.events = events

    def capture(self, output_path, use_video_port=False):
        self.events.append("capture")
        Path(output_path).write_bytes(b"fake-image")


class TrialRunnerTests(unittest.TestCase):
    @patch("endursaga.MosfetPulseController")
    def test_run_trials_pulses_pauses_captures_and_evaluates_each_iteration(self, controller_class):
        events = []
        controller_class.return_value.pulse_once.side_effect = lambda **kwargs: events.append("pulse")
        evaluator = Mock(side_effect=lambda path: events.append("evaluate") or 4)
        camera = FakeCamera(events)

        with tempfile.TemporaryDirectory() as output_dir:
            results = run_trials(
                iterations=2,
                evaluator=evaluator,
                output_dir=output_dir,
                camera=camera,
                pause=lambda seconds: events.append("pause"),
            )

        self.assertEqual(results, {1: 4, 2: 4})
        self.assertEqual(events, ["pulse", "pause", "capture", "evaluate"] * 2)
        self.assertEqual(evaluator.call_args_list[0].args[0].name, "trial_0001.jpg")
        self.assertEqual(evaluator.call_args_list[1].args[0].name, "trial_0002.jpg")
        controller_class.return_value.close.assert_called_once_with()

    def test_run_trials_rejects_non_d6_evaluator_result(self):
        with patch("endursaga.MosfetPulseController"):
            with tempfile.TemporaryDirectory() as output_dir:
                with self.assertRaises(ValueError):
                    run_trials(
                        iterations=1,
                        evaluator=lambda image_path: 7,
                        output_dir=output_dir,
                        camera=FakeCamera([]),
                        settle_seconds=0,
                    )

    def test_analyze_results_counts_faces_and_computes_chi_square(self):
        counts, chi_square = analyze_results({1: 1, 2: 2, 3: None})

        self.assertEqual(counts, {1: 1, 2: 1, 3: 0, 4: 0, 5: 0, 6: 0})
        self.assertAlmostEqual(chi_square, 4.0)

    def test_main_requires_an_evaluator(self):
        self.assertEqual(main(["2"]), 2)


if __name__ == "__main__":
    unittest.main()