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