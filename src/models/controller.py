import pyautogui
import mediapipe as mp
from constants.gest import Gest
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import numpy as np
import os
from datetime import datetime
import time
import win32api
import win32gui

from models.hand_recog import HandRecog

# Executes commands according to detected gestures
class Controller:
    tx_old = 0
    ty_old = 0
    trial = True
    flag = False
    grabflag = False
    mutedflag = False
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


    def getpinchylv(hand_result):
        dist = round((Controller.pinchstartycoord - hand_result.landmark[8].y) * 10, 1)
        return dist

    def getpinchxlv(hand_result):
        dist = round((hand_result.landmark[8].x - Controller.pinchstartxcoord) * 10, 1)
        return dist

    # def changesystembrightness():
    #     currentBrightnessLv = sbcontrol.get_brightness() / 100.0
    #     currentBrightnessLv += Controller.pinchlv / 50.0
    #     if currentBrightnessLv > 1.0:
    #         currentBrightnessLv = 1.0
    #     elif currentBrightnessLv < 0.0:
    #         currentBrightnessLv = 0.0
    #     sbcontrol.fade_brightness(int(100 * currentBrightnessLv), start=sbcontrol.get_brightness())

    def changesystemvolume(lmList):

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        # volume.GetMute()
        # volume.GetMasterVolumeLevel()
        volRange = volume.GetVolumeRange()
        minVol = volRange[0]
        maxVol = volRange[1]
        vol = 0
        
        x1, y1 = lmList[4][1], lmList[4][2]
        x2, y2 = lmList[8][1], lmList[8][2]

        length = math.hypot(x2 - x1, y2 - y1)

        vol = np.interp(length, [10, 100], [minVol, maxVol])
        #print(int(length), vol)
        volume.SetMasterVolumeLevel(vol, None)
    
    def takeScreenshot(leftlmList, rightlmList):

        x1 = leftlmList[4][1]
        y1 = leftlmList[4][2]

        x2 = rightlmList[4][1]
        y2 = rightlmList[4][2]

        x3 = leftlmList[8][1]
        y3 = leftlmList[8][2]

        x4 = rightlmList[8][1]
        y4 = rightlmList[8][2]

        thumbDistance = math.hypot(x2 - x1, y2 - y1)
        indexDistance = math.hypot(x4 - x3, y4 - y3)
        
        if  math.isclose(thumbDistance, 0, abs_tol = 30):
            desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
            now = datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
            pyautogui.screenshot(desktop + '\\Jerry_Screenshots\\' + now + '.png')
            print("Screenshot Taken")
            #print ("Thumb: ", thumbDistance, " Index: ", indexDistance)
            Controller.flag = False

    #
    # def scrollVertical():
    #     pyautogui.scroll(120 if Controller.pinchlv > 0.0 else -120)
    #
    # def scrollHorizontal():
    #     pyautogui.keyDown('shift')
    #     pyautogui.keyDown('ctrl')
    #     pyautogui.scroll(-120 if Controller.pinchlv > 0.0 else 120)
    #     pyautogui.keyUp('ctrl')
    #     pyautogui.keyUp('shift')

    # Locate Hand to get Cursor Position
    # Stabilize cursor by Dampening
    def get_position(hand_result):
        point = 9
        position = [hand_result.landmark[point].x, hand_result.landmark[point].y]
        sx, sy = pyautogui.size()
        x_old, y_old = pyautogui.position()
        x = int(position[0] * sx)
        y = int(position[1] * sy)
        if Controller.prev_hand is None:
            Controller.prev_hand = x, y
        delta_x = x - Controller.prev_hand[0]
        delta_y = y - Controller.prev_hand[1]

        distsq = delta_x ** 2 + delta_y ** 2
        ratio = 1
        Controller.prev_hand = [x, y]

        if distsq <= 25:
            ratio = 0
        elif distsq <= 900:
            ratio = 0.07 * (distsq ** (1 / 2))
        else:
            ratio = 2.1
        x, y = x_old + delta_x * ratio, y_old + delta_y * ratio
        return (x, y)

    def pinch_control_init(hand_result):
        Controller.pinchstartxcoord = hand_result.landmark[8].x
        Controller.pinchstartycoord = hand_result.landmark[8].y
        Controller.pinchlv = 0
        Controller.prevpinchlv = 0
        Controller.framecount = 0

    # Hold final position for 5 frames to change status
    def pinch_control(hand_result, controlHorizontal, controlVertical):
        if Controller.framecount == 5:
            Controller.framecount = 0
            Controller.pinchlv = Controller.prevpinchlv

            if Controller.pinchdirectionflag == True:
                controlHorizontal()  # x

            elif Controller.pinchdirectionflag == False:
                controlVertical()  # y

        lvx = Controller.getpinchxlv(hand_result)
        lvy = Controller.getpinchylv(hand_result)

        if abs(lvy) > abs(lvx) and abs(lvy) > Controller.pinch_threshold:
            Controller.pinchdirectionflag = False
            if abs(Controller.prevpinchlv - lvy) < Controller.pinch_threshold:
                Controller.framecount += 1
            else:
                Controller.prevpinchlv = lvy
                Controller.framecount = 0

        elif abs(lvx) > Controller.pinch_threshold:
            Controller.pinchdirectionflag = True
            if abs(Controller.prevpinchlv - lvx) < Controller.pinch_threshold:
                Controller.framecount += 1
            else:
                Controller.prevpinchlv = lvx
                Controller.framecount = 0

    def handle_controls(gesture, hand_result, lmList):
        x, y = None, None
        if gesture != Gest.PALM:
            x, y = Controller.get_position(hand_result)

        # flag reset
        if gesture != Gest.FIST and Controller.grabflag:
            Controller.grabflag = False
            pyautogui.mouseUp(button="left")

        # if gesture != Gest.PINCH_MAJOR and Controller.pinchmajorflag:
        #     Controller.pinchmajorflag = False

        # if gesture != Gest.PINCH_MINOR and Controller.pinchminorflag:
        #     Controller.pinchminorflag = False

        # implementation
        if gesture == Gest.PALM:
            Controller.flag = True
            #if Controller.tabflag:
            #    pyautogui.keyUp('alt')
            #    pyautogui.keyUp('tab')
            #    Controller.tabflag = False

        if gesture == Gest.V_GEST:
            #if Controller.tabflag:
            #    pyautogui.keyUp('alt')
            #    pyautogui.keyUp('tab')
            #    Controller.tabflag = False            
            Controller.flag = True
            pyautogui.moveTo(x, y, duration=0.1)

        elif gesture == Gest.FIST:
            if not Controller.grabflag:
                Controller.grabflag = True
                pyautogui.mouseDown(button="left")
            pyautogui.moveTo(x, y, duration=0.1)

        elif gesture == Gest.MID and Controller.flag:
            pyautogui.click()
            Controller.flag = False

        elif gesture == Gest.INDEX and Controller.flag:
            pyautogui.click(button='right')
            Controller.flag = False

        elif gesture == Gest.TWO_FINGER_CLOSED and Controller.flag:
            pyautogui.doubleClick()
            Controller.flag = False

        elif gesture == Gest.PINCH:
            Controller.changesystemvolume(lmList)
            #Controller.flag = False

        elif gesture == Gest.LAST4:
            pyautogui.scroll(200)

        elif gesture == Gest.LAST3:
            pyautogui.scroll(-200)

        elif gesture == Gest.PINKY_RING_SPREAD and Controller.flag:
            pyautogui.hotkey('alt', 'tab')
            #pyautogui.keyDown('alt')
            #pyautogui.keyDown('tab')
            #Controller.tabflag = True
            Controller.flag = False
        
        elif gesture == Gest.PINKY and Controller.flag:
            pyautogui.hotkey('Delete')
            Controller.flag = False
        
        elif gesture == Gest.FIRST3 and Controller.flag:
            pyautogui.hotkey('ctrl', 'z')
            Controller.flag = False


        # elif gesture == Gest.PINCH_MINOR:
        #     if Controller.pinchminorflag == False:
        #         Controller.pinch_control_init(hand_result)
        #         Controller.pinchminorflag = True
        #     Controller.pinch_control(hand_result, Controller.scrollHorizontal, Controller.scrollVertical)

        # elif gesture == Gest.PINCH_MAJOR:
        #     if Controller.pinchmajorflag == False:
        #         Controller.pinch_control_init(hand_result)
        #         Controller.pinchmajorflag = True
        #     Controller.pinch_control(hand_result, Controller.changesystembrightness, Controller.changesystemvolume)

    def two_handle_controls (right_gest_name, left_gest_name, right_hand_results, left_hand_results, leftlmList, rightlmList):
        if right_gest_name  == Gest.PALM and left_gest_name == Gest.PALM and not Controller.flag:
            Controller.flag = True
        
        if right_gest_name == Gest.PINCH and left_gest_name == Gest.PINCH and Controller.flag:
            Controller.takeScreenshot(leftlmList, rightlmList)
            Controller.flag = False
        
        elif right_gest_name == Gest.PINKY and left_gest_name == Gest.PINKY and Controller.flag:
            pyautogui.hotkey('alt','f4')
            Controller.flag = False
        
        elif right_gest_name == Gest.FIST and left_gest_name == Gest.FIST and Controller.flag and not Controller.mutedflag:
            WM_APPCOMMAND = 0x319
            APPCOMMAND_MICROPHONE_VOLUME_MUTE = 0x180000
            hwnd_active = win32gui.GetForegroundWindow()
            win32api.SendMessage(hwnd_active, WM_APPCOMMAND, None, APPCOMMAND_MICROPHONE_VOLUME_MUTE)
            print("Your Microphone Has Been Muted")
            Controller.flag = False
            Controller.mutedflag = True

        elif right_gest_name == Gest.FIST and left_gest_name == Gest.FIST and Controller.flag and Controller.mutedflag:
            WM_APPCOMMAND = 0x319
            APPCOMMAND_MICROPHONE_VOLUME_MUTE = 0x180000
            hwnd_active = win32gui.GetForegroundWindow()
            win32api.SendMessage(hwnd_active, WM_APPCOMMAND, None, APPCOMMAND_MICROPHONE_VOLUME_MUTE)
            print("Your Microphone Has Been Unmuted!")
            Controller.flag = False
            Controller.mutedflag = False


           
                

           
