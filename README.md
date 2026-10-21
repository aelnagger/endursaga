# endursaga
Application for testing the fairness of my dice using a roller.

# Components

  * [Rumble Plate Dice Roller](https://github.com/makersmakingchange/Rumble-Plate-Dice-Roller)
  * Raspberry Pi
  * Camera
  * mosfet

# What are we doing?

  * Using the mosfet, run the rumble plate for 1 second.
  * Wait for the die to settle.
  * Capture an image of the die.
  * Record the result.
  * Repeat for a set number of trials
  * Once we have completed our number of trials, generate a histogram of die states, and perform a basic statistical analysis of fairness.

# ORB face templates

The default evaluator uses OpenCV ORB feature matching. Put clear, tightly framed sample images into one subdirectory per face label. Include several samples for different rotations and lighting when available.

```text
templates/
  1/sample-01.png
  1/sample-02.png
  2/sample-01.png
  ...
  20/sample-01.png
```

Every label for the selected die must have at least one usable template. The CLI supports d4, d6, d8, d10, d12, and d20; use `--sides 20` for a d20. A d10 labeled 0-9 also needs `--first-face 0`.

```sh
uv run endursaga 100 --sides 20 --templates-dir templates
```

ORB compares grayscale visual features rather than reading text. It is intended as a starting point for consistently printed labels; validate it against the actual die images and treat ambiguous matches as unrecognized.