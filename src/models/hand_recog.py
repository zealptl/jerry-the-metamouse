import math
from constants.gest import Gest
from google.protobuf.json_format import MessageToDict

# Convert Mediapipe Landmarks to recognizable Gestures
class HandRecog:

    def __init__(self, hand_label):
        self.finger = 0
        self.ori_gesture = Gest.PALM
        self.prev_gesture = Gest.PALM
        self.frame_count = 0
        self.hand_result = None
        self.hand_label = hand_label

    def set_hand_result(self, hand_result):
        self.hand_result = hand_result

    def get_hand_result(self):
        return self.hand_result

    def get_signed_dist(self, point):
        sign = -1
        if self.hand_result.landmark[point[0]].y < self.hand_result.landmark[point[1]].y:
            sign = 1
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x) ** 2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y) ** 2
        dist = math.sqrt(dist)
        return dist * sign

    def get_dist(self, point):
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x) ** 2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y) ** 2
        dist = math.sqrt(dist)
        return dist

    def get_dz(self, point):
        return abs(self.hand_result.landmark[point[0]].z - self.hand_result.landmark[point[1]].z)

    # Function to find Gesture Encoding using current finger_state.
    # Finger_state: 1 if finger is open, else 0
    def set_finger_state(self):
        if self.hand_result == None:
            return

        points = [[4, 1, 0], [8, 5, 0], [12, 9, 0], [16, 13, 0], [20, 17, 0]]
        self.finger = 0
        self.finger = self.finger | 0  # thumb
        for idx, point in enumerate(points):

            dist = self.get_signed_dist(point[:2])
            dist2 = self.get_signed_dist(point[1:])

            try:
                ratio = round(dist / dist2, 1)
            except:
                ratio = round(dist1 / 0.01, 1)

            self.finger = self.finger << 1
            if ratio > 0.5:
                self.finger = self.finger | 1

    # Handling Fluctations due to noise
    def get_gesture(self):
        if self.hand_result == None:
            return Gest.PALM

        # current_gesture = Gest.PALM
        # if self.finger in [Gest.LAST3, Gest.LAST4] and self.get_dist([8, 4]) < 0.05:
        #     if self.hand_label == HLabel.MINOR:
        #         current_gesture = Gest.PINCH_MINOR
        #     else:
        #         current_gesture = Gest.PINCH_MAJOR

        if self.finger == Gest.PALM:
            current_gesture = Gest.PALM

        if self.get_dist([8,4]) < 0.3 and self.finger == Gest.PINCH:
            current_gesture = Gest.PINCH

        if self.get_dist([8,4]) < 0.3 and self.finger == Gest.SPIDER:
            current_gesture = Gest.SPIDER

        elif Gest.FIRST2 == self.finger:
            point = [[8, 12], [5, 9]]
            dist1 = self.get_dist(point[0])
            dist2 = self.get_dist(point[1])
            ratio = dist1 / dist2
            if ratio > 1.7:
                current_gesture = Gest.V_GEST
            else:
                if self.get_dz([8, 12]) < 0.1:
                    current_gesture = Gest.TWO_FINGER_CLOSED
                else:
                    current_gesture = Gest.MID

        else:
            current_gesture = self.finger

        if current_gesture == self.prev_gesture:
            self.frame_count += 1
        else:
            self.frame_count = 0

        self.prev_gesture = current_gesture

        if self.frame_count > 4:
            self.ori_gesture = current_gesture
        return self.ori_gesture

    def findPosition(results, img, handNo):
        xList = []
        yList = []
        lmList = []
        if results.multi_hand_landmarks:
            myHand = results.multi_hand_landmarks[handNo]
            myH = results.multi_handedness

            # index = results.multi_handedness[handNo].classification[handNo].index
            # for id, classification in enumerate(results.multi_handedness):
            #     if classification.classification[handNo].index == index:
            #         label = classification.classification[handNo].label

        for id, lm in enumerate(myHand.landmark):
            # print(id, lm)
            h, w, c = img.shape
            cx, cy = int(lm.x * w), int(lm.y * h)
            xList.append(cx)
            yList.append(cy)
            # print(id, cx, cy)
            lmList.append([id, cx, cy])
        
        return lmList
    
    def findPosition2Hands(results, img, handNo):
        leftxList = []
        leftyList = []
        leftlmList = []

        rightxList = []
        rightyList = []
        rightlmList = []

        if results.multi_hand_landmarks:
            myHand = results.multi_hand_landmarks[handNo]
            myH = results.multi_handedness

            if results.multi_handedness:
                for idx, hand_handedness in enumerate(results.multi_handedness):
                    handedness_dict = MessageToDict(hand_handedness)
                    whichhand = hand_handedness.classification[0].label
                    print(whichhand)

        # for id, lm in enumerate(myHand.landmark):
        #     # print(id, lm)
        #     h, w, c = img.shape
        #     cx, cy = int(lm.x * w), int(lm.y * h)
        #     xList.append(cx)
        #     yList.append(cy)
        #     # print(id, cx, cy)
        #     lmList.append([id, cx, cy])
        
        # return lmList
    
    