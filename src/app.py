# Imports

import cv2
import mediapipe as mp
from numpy import result_type
import pyautogui
import math
from enum import IntEnum
from google.protobuf.json_format import MessageToDict

from constants.hand_landmarks import HandLandmarks
from constants.gest import Gest
from models.hand_recog import HandRecog
from models.controller import Controller

# from ctypes import cast, POINTER
# from comtypes import CLSCTX_ALL
# from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
# import screen_brightness_control as sbcontrol

pyautogui.FAILSAFE = False
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands


# Multi-handedness Labels
class HLabel(IntEnum):
    LEFT = 0
    RIGHT = 1

class GestureController:
    gc_mode = 0
    cap = None
    CAM_HEIGHT = None
    CAM_WIDTH = None
    right_hand_result = None  # Right Hand by default
    left_hand_result = None  # Left hand by default
    dom_hand = True

    def __init__(self):
        GestureController.gc_mode = 1
        GestureController.cap = cv2.VideoCapture(0)
        GestureController.CAM_HEIGHT = GestureController.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        GestureController.CAM_WIDTH = GestureController.cap.get(cv2.CAP_PROP_FRAME_WIDTH)

    def classify_hands(results):
        left, right = None, None
        try:
            handedness_dict = MessageToDict(results.multi_handedness[0])
            if handedness_dict['classification'][0]['label'] == 'Right':
                right = results.multi_hand_landmarks[0]
            else:
                left = results.multi_hand_landmarks[0]
        except:
            pass

        try:
            handedness_dict = MessageToDict(results.multi_handedness[1])
            if handedness_dict['classification'][0]['label'] == 'Right':
                right = results.multi_hand_landmarks[1]
            else:
                left = results.multi_hand_landmarks[1]
        except:
            pass

        GestureController.right_hand_result = right
        GestureController.left_hand_result = left

    def start(self):

        right_hand = HandRecog(HLabel.RIGHT)
        left_hand = HandRecog(HLabel.LEFT)

        with mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.7) as hands:
            while GestureController.cap.isOpened() and GestureController.gc_mode:
                success, image = GestureController.cap.read()

                if not success:
                    print("Ignoring empty camera frame.")
                    continue

                image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = hands.process(image)

                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    GestureController.classify_hands(results)
                    right_hand.set_hand_result(GestureController.right_hand_result)
                    left_hand.set_hand_result(GestureController.left_hand_result)

                    if right_hand.hand_result and left_hand.hand_result:
                        # Do two-handed gesture
                        right_hand.set_finger_state()
                        right_gest_name = right_hand.get_gesture()

                        left_hand.set_finger_state()
                        left_gest_name = left_hand.get_gesture()
                        
                        # print('left finger state: ', left_hand.finger, 'right finger state: ', right_hand.finger)
                        print('left gesture: ', left_gest_name, 'right gesture: ', right_gest_name)
                        
                        leftlmList, rightlmList = HandRecog.findPosition2Hands(results, image, 1)
                        Controller.two_handle_controls(right_gest_name, left_gest_name, right_hand.hand_result, left_hand.hand_result, leftlmList, rightlmList)
                    elif right_hand.hand_result and not left_hand.hand_result:
                        # Do one-handed gesture with right hand
                        right_hand.set_finger_state()
                        gest_name = right_hand.get_gesture()
                        
                        # print('right finger state: ', right_hand.finger)
                        print('right gesture: ', gest_name)
                        
                        lmList = HandRecog.findPosition(results, image, 0)
                        Controller.handle_controls(gest_name, right_hand.hand_result, lmList)

                    elif not right_hand.hand_result and left_hand.hand_result:
                        # Do one-handed gesture with left hand
                        left_hand.set_finger_state()
                        gest_name = left_hand.get_gesture()
                        
                        # print('left finger state: ', left_hand.finger)
                        print('left gesture: ', gest_name)
                        
                        lmList = HandRecog.findPosition(results, image, 0)
                        Controller.handle_controls(gest_name, left_hand.hand_result, lmList)
                    else:
                        pass
                else:
                    Controller.prev_hand = None
                cv2.imshow('Gesture Controller', image)
                if cv2.waitKey(5) & 0xFF == 13:
                    break
        GestureController.cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    gc1 = GestureController()
    gc1.start()

