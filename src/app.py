import cv2
from enum import IntEnum
import math
import mediapipe as mp
import pyautogui
import sys
import pprint
from google.protobuf.json_format import MessageToDict

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands


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


class Gestures(IntEnum):
    FIST = 0
    PINKY = 1
    RING = 2
    MID = 4
    LAST3 = 7
    INDEX = 8
    FIRST2 = 12
    LAST4 = 15
    THUMB = 16
    PALM = 31

    V_GEST = 33
    TWO_FINGER_CLOSED = 34
    PINCH_MAJOR = 35
    PINCH_MINOR = 36


class GestureAnalysis:
    def __init__(self):
        self.finger_state = 0
        self.frame_count = 0
        self.hand_result = None
        self.original_gesture = Gestures.PALM
        self.previous_gesture = Gestures.PALM

    def set_hand_result(self, hand_result):
        self.hand_result = hand_result

    def get_hand_result(self):
        return self.hand_result

    def get_signed_distance(self, point):
        sign = -1
        if self.hand_result.landmark[point[0]].y < self.hand_result.landmark[point[1]].y:
            sign = 1
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x) ** 2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y) ** 2
        dist = math.sqrt(dist)
        return dist * sign

    def get_distance(self, point):
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x) ** 2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y) ** 2
        dist = math.sqrt(dist)
        return dist

    def get_dz(self, point):
        return abs(self.hand_result.landmark[point[0]].z - self.hand_result.landmark[point[1]].z)

    def set_finger_state(self):
        if self.hand_result is None:
            print('hand_result is None')
            return

        points = [
            [HandLandmarks.INDEX_TIP, HandLandmarks.INDEX_MCP, HandLandmarks.WRIST],
            [HandLandmarks.MIDDLE_TIP, HandLandmarks.MIDDLE_MCP, HandLandmarks.WRIST],
            [HandLandmarks.RING_TIP, HandLandmarks.RING_MCP, HandLandmarks.WRIST],
            [HandLandmarks.PINKY_TIP, HandLandmarks.PINKY_MCP, HandLandmarks.WRIST]
        ]

        self.finger_state = 0
        self.finger_state = self.finger_state | 0

        for idx, point in enumerate(points):
            dist = self.get_signed_distance(point[:2])  # dist between tip & mcp
            dist2 = self.get_signed_distance(point[1:])  # dist between mcp & wrist

            try:
                ratio = round(dist / dist2, 1)
            except ValueError:
                print('cannot divide by 0')
                ratio = round(dist / 0.01, 1)

            self.finger_state << 1
            if ratio > 0.5:
                self.finger_state = self.finger_state | 1

    def get_finger_state(self):
        return self.finger_state

    def get_gesture(self):
        if self.hand_result is None:
            print('hand_result is None')
            return Gestures.PALM

        current_gesture = Gestures.PALM

        if self.finger_state == Gestures.FIRST2:
            points = [
                [HandLandmarks.INDEX_TIP, HandLandmarks.MIDDLE_TIP],
                [HandLandmarks.INDEX_MCP, HandLandmarks.MIDDLE_MCP]
            ]

            dist1 = self.get_distance(points[0])
            dist2 = self.get_distance(points[1])
            ratio = dist1 / dist2
            if ratio > 1.7:
                current_gesture = Gestures.V_GEST
            else:
                if self.get_dz([points[0]]) < 0.1:
                    current_gesture = Gestures.FIRST_TWO_CLOSED
                else:
                    current_gesture = Gestures.MID
        else:
            current_gesture = self.finger_state

        if current_gesture == self.previous_gesture:
            self.frame_count += 1
        else:
            self.frame_count = 0

        self.previous_gesture = current_gesture

        if self.frame_count > 4:
            self.original_gesture = current_gesture

        print('FINGER_STATE', Gestures(self.finger_state).name)
        print('ORIGINAL_GESTURE', Gestures(self.original_gesture).name)
        print('*' * 100)
        return self.original_gesture


class App:
    cap = None
    CAM_HEIGHT = None
    CAM_WIDTH = None

    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.CAM_HEIGHT = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.CAM_WIDTH = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)

    def classify_hands(self, results):
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

        return left, right

    def start(self):
        left_hand = GestureAnalysis()
        right_hand = GestureAnalysis()

        with mp_hands.Hands(
                max_num_hands=2,
                model_complexity=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
        ) as hands:
            while self.cap.isOpened():
                success, image = self.cap.read()

                if not success:
                    print('Ignoring empty camera frame.')

                image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = hands.process(image)

                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                if results.multi_hand_landmarks:
                    left, right = self.classify_hands(results)
                    left_hand.set_hand_result(left)
                    right_hand.set_hand_result(right)

                    if left_hand.get_hand_result() and right_hand.get_hand_result():
                        # do TWO HANDED gesture
                        pass
                    elif left_hand.get_hand_result() and not right_hand.get_hand_result():
                        # gestures with LEFT_HAND only
                        pass
                    elif not left_hand.get_hand_result() and right_hand.get_hand_result():
                        # gestures with RIGHT_HAND only
                        right_hand.set_finger_state()
                        gesture_name = right_hand.get_gesture()
                        # print('gesture_name:', Gestures(gesture_name).name)

                    else:
                        print('do nothing')

                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(image,
                                                  hand_landmarks,
                                                  mp_hands.HAND_CONNECTIONS,
                                                  )
                cv2.imshow('Jerry the MetaMouse', image)
                if cv2.waitKey(5) & 0xFF == 13:
                    break

        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    app = App()
    app.start()
