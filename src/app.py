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