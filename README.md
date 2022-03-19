# Jerry The MetaMouse

Jerry is a virtual mouse that allows you to use your camera to control your computer using gestures. The python based code allows your camera to recognize your hand as a mouse to do computer fucntions such as adjusting volume, brightness, left click, right click, and other functions. These hand gestures are movements that you do with your hands and fingers, you do need to physically touch your computer mouse. With the use of this virtual mouse, there are many gestures that can be added for comfortability, flexibility, and usability.

## Project Organization

    ├── LICENSE
    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    ├── README.md          <- The top-level README for developers using this project.
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── constants              <- For Enum classes
    │   │   └── gest.py            <- Enum class for defining Gesture values
    |   |   └── hand_landmarks.py  <- Enum class for defining Hand Landmarks coming from Mediapipe
    │   │
    │   ├── models
    │   │   ├── controller.py
    │   │   └── hand_recog.py
    │   │
    │   └── app.py         <- Entry point of the application
