<<<<<<< Updated upstream
'''
Will be the entry point of the app. Will open camera using cv2 then use mediapipe to get hand mappings
Given the handmappings call the methods in HandGestures to get gestures and perform task.
'''
import sys
import cv2
import mediapipe as mp
import pyautogui
from enum import IntEnum
import math

#Zeal Code

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


class GestureAnalysis:
    def __init__(self):
        self.finger = 0
        self.original_gesture = HandLandmarks.PALM
        self.previous_gesture = HandLandmarks.PALM
        self.frame_count = 0
        self.hand_result = None
    
    def update_hand_result(self, results):
        try:
            self.hand_result = results.multi_hand_landmarks[0]
        except:
            return
        
    def get_signed_dist(self, point):
        sign = -1
        if self.hand_result.landmark[point[0]].y < self.hand_result.landmark[point[1]].y:
            sign = 1
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
        dist = math.sqrt(dist)
        return dist*sign
    
    def get_dist(self, point):
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
        dist = math.sqrt(dist)
        return dist
    
    def get_dz(self,point):
        return abs(self.hand_result.landmark[point[0]].z - self.hand_result.landmark[point[1]].z)
    
    def set_finger_state(self):
        if not self.hand_result:
            print('NO HAND RESULT')
            return
        
        points = [
            [HandLandmarks.INDEX_TIP, HandLandmarks.INDEX_MCP, HandLandmarks.WRIST],
            [HandLandmarks.MIDDLE_TIP, HandLandmarks.MIDDLE_MCP, HandLandmarks.WRIST],
            [HandLandmarks.RING_TIP, HandLandmarks.RING_MCP, HandLandmarks.WRIST],
            [HandLandmarks.PINKY_TIP, HandLandmarks.PINKY_MCP, HandLandmarks.WRIST],
        ] 
        
        self.finger = 0
        self.finger = self.finger | 0
        for idx, point in enumerate(points):
            dist = self.get_signed_dist(point[:2])
            dist2 = self.get_signed_dist(point[1:])

            try:
                ratio = round(dist/dist2, 1)
            except:
                ratio = round(dist1/0.01, 1)
                
            self.finger = self.finger << 1
            if ratio > 0.5:
                self.finger = self.finger | 1
            
                
    def get_gesture(self):
        if self.hand_result == None:
            return HandLandmarks.PALM
        
        current_gesture = HandLandmarks.PALM
        if self.finger == HandLandmarks.FIRST_TWO_OPEN:
            points = [
                [HandLandmarks.INDEX_TIP, HandLandmarks.MIDDLE_TIP],
                [HandLandmarks.INDEX_MCP, HandLandmarks.MIDDLE_MCP],
            ]
            
            dist1 = self.get_dist(points[0])
            dist2 = self.get_dist(points[1])
            ratio = dist1 / dist2
            
            if ratio > 1.7:
                current_gesture = HandLandmarks.FIRST_TWO_OPEN
            else:
                if self.get_dz(points[0]) < 0.1:
                    current_gesture = HandLandmarks.FIRST_TWO_CLOSED
        else:
            current_gesture = self.finger
            
        if current_gesture == self.previous_gesture:
            self.frame_count += 1
        else:
            self.frame_count = 0
            
        self.prevous_gesture = current_gesture
        
        if self.frame_count > 4:
            self.original_gesture = current_gesture

        return self.original_gesture
            

class GestureController:
    tx_old = 0
    ty_old = 0
    trial = True
    flag = False
    grabflag = False
    pinchmajorflag = False
    pinchminorflag = False
    pinchstartxcoord = None
    pinchstartycoord = None
    pinchdirectionflag = None
    prevpinchlv = 0
    pinchlv = 0
    framecount = 0
    prev_hand = None
    pinch_threshold = 0.3
    
    def get_position(self, hand_result):
        point = HandLandmarks.MIDDLE_MCP
        position = [hand_result.landmark[point].x, hand_result.landmark[point].y]
        print('position:', position)
        sx, sy = pyautogui.size()
        x_old, y_old = pyautogui.position()
        x = int(position[0] * sx)
        y = int(position[1] * sy)
        
        if self.prev_hand is None:
            self.prev_hand = x,y
        
        delta_x = x - self.prev_hand[0]
        delta_y = y - self.prev_hand[1]
        
        distsq = delta_x**2 + delta_y**2
        ratio = 1
        self.prev_hand = [x, y]
        
        if distsq <= 25:
            ratio = 0
        elif distsq <= 900:
            ratio = 0.07 * (distsq ** (1/2))
        else:
            ratio = 2.1
        x, y = x_old + delta_x*ratio, y_old + delta_y*ratio
        
        print('new x_y:', [x,y])
        return (x, y)
    
    def handle_controls(self, gesture, hand_result): 
        x, y = None, None
        if gesture != HandLandmarks.PALM:
            x, y = self.get_position(hand_result)
        
        print('x_y in handle_controls', [x,y])
        if gesture == 12:
            print('GESTURE CAUGHT')
            self.flag = True
            pyautogui.moveTo(x, y, duration=0.1)
            

class App:
    cap = None
    CAM_HEIGHT = None
    CAM_WIDTH = None
    
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.CAM_HEIGHT = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.CAM_WIDTH = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        
    def start(self):
        hand = GestureAnalysis()
        
        with mp_hands.Hands(
            max_num_hands=2,
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as hands:
            while self.cap.isOpened():
                success, image = self.cap.read()
                
                if not success:
                    print("Ignoring empty camera frame.")
                
                image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = hands.process(image)
                                
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                
                if results.multi_hand_landmarks:
                    hand.update_hand_result(results)
                    hand.set_finger_state()
                    gesture_name = hand.get_gesture()
                    
                    controller = GestureController()
                    print('gesture:', gesture_name)
                    controller.handle_controls(12, hand.hand_result)
                    
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                cv2.imshow('Jerry the MetaMouse', image)
                if cv2.waitKey(5) & 0xFF == 13:
                    break
                    
        self.cap.release()
        cv2.destroyAllWindows() 
  
if __name__ == '__main__':            
    app = App()
    app.start()
=======
# Imports

import cv2
import mediapipe as mp
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

    def findPosition(results, img, handNo):
        xList = []
        yList = []
        lmList = []
        if results.multi_hand_landmarks:
            myHand = results.multi_hand_landmarks[handNo]
        for id, lm in enumerate(myHand.landmark):
            # print(id, lm)
            h, w, c = img.shape
            cx, cy = int(lm.x * w), int(lm.y * h)
            xList.append(cx)
            yList.append(cy)
            # print(id, cx, cy)
            lmList.append([id, cx, cy])
        
        return lmList
        
    def start(self):

        right_hand = HandRecog(HLabel.RIGHT)
        left_hand = HandRecog(HLabel.LEFT)

        with mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
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
                        pass
                    elif right_hand.hand_result and not left_hand.hand_result:
                        # Do one-handed gesture with right hand
                        right_hand.set_finger_state()
                        gest_name = right_hand.get_gesture()
                        #print(gest_name)
                        Controller.handle_controls(gest_name, right_hand.hand_result)
                        lmList = GestureController.findPosition(results, image, 0)
                        if len(lmList) != 0:
                            print(lmList)

                    elif not right_hand.hand_result and left_hand.hand_result:
                        # Do one-handed gesture with left hand
                        left_hand.set_finger_state()
                        gest_name = left_hand.get_gesture()
                        #print(gest_name)
                        Controller.handle_controls(gest_name, left_hand.hand_result)
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
>>>>>>> Stashed changes
