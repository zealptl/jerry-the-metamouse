from enum import IntEnum

# Gesture Encodings
class Gest(IntEnum):
    # Binary Encoded
    FIST = 0
    PINKY = 1
    RING = 2
    MID = 20
    LAST3 = 23
    INDEX = 8
    FIRST2 = 12
    LAST4 = 15
    THUMB = 16
    PALM = 31

    # Extra Mappings
    V_GEST = 28
    TWO_FINGER_CLOSED = 34
    PINCH = 24
    SPIDER = 25
    FIRST3 = 14
    PINKY_RING_SPREAD = 3

