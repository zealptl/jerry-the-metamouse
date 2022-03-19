'''
Enum class to define all the hand landmarks - coming from mediapipe
Replicate this class: https://github.com/xenon-19/Gesture-Controlled-Virtual-Mouse/blob/main/src/Gesture_Controller.py#L19
'''
from enum import IntEnum

class HandLandmarks(IntEnum):
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8
    
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12
    
    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16
    
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20
    
    FIRST_TWO_OPEN = INDEX_TIP + MIDDLE_TIP
    FIRST_THREE_OPEN = INDEX_TIP + MIDDLE_TIP + RING_TIP
    FIRST_FOUR_OPEN = INDEX_TIP + MIDDLE_TIP + RING_TIP + PINKY_TIP
    PALM = INDEX_TIP + MIDDLE_TIP + RING_TIP + PINKY_TIP + THUMB_TIP
    
    FIRST_TWO_CLOSE = INDEX_TIP - MIDDLE_TIP
    FIRST_THREE_CLOSE = INDEX_TIP - MIDDLE_TIP - RING_TIP
    FIRST_FOUR_CLOSE = INDEX_TIP - MIDDLE_TIP - RING_TIP - PINKY_TIP
    FIST = 0
    
    PINCH = INDEX_TIP + THUMB_TIP
    SPIDER_MAN = INDEX_TIP + PINKY_TIP
    ROCK_AND_ROLL = INDEX_TIP + PINKY_TIP + THUMB_TIP
    
    