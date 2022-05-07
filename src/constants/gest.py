from enum import IntEnum

# Gesture Encodings
class Gest(IntEnum):
    # Binary Encoded
    FIST = 0
    PINKY = 1
    RING = 2
    MID = 4
    INDEX = 8
    THUMB = 16
    
    FIRST2 = INDEX + MID
    FIRST3 = INDEX + MID + RING
    LAST2 = RING + PINKY
    LAST3 = MID + RING + PINKY
    LAST4 = INDEX + MID + RING + PINKY
    PALM = THUMB + INDEX + MID + RING + PINKY 
    PINCH = INDEX + THUMB
    SPIDER = THUMB + INDEX + PINKY
    V_GEST = 28
    TWO_FINGER_CLOSED = 34