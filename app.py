import cv2
import mediapipe as mp
import numpy as np
import pyautogui as pg
import time

class handDetector():
    def __init__(self,mode=False,max_num_hands=2,min_detection_confidence=0.5,min_track_confidence = 0.5):
        self.mode = mode
        self.max_num_hands= max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_track_confidence = min_track_confidence

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(mode,max_num_hands, min_detection_confidence, min_track_confidence)
        self.mpDraw = mp.solutions.drawing_utils

    def findHands(self,frame,draw=True):
        frameRGB = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(frameRGB)
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(frame,handLms,self.mpHands.HAND_CONNECTIONS)
        return frame

    def getPosition(self,frame,handNum = 0):
        lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNum]
            for id,lm in enumerate(myHand.landmark):
                h,w,c = frame.shape
                cx,cy,cz = int(lm.x*w),int(lm.y*h),int(lm.z*c)
                lmList.append([id,cx,cy,cz])
        return lmList

    def fingersUp(self,frame):
        pos = self.getPosition(frame)
        fingers = [8,12,16,20]
        which_up = [0,0,0,0]
        for i in range(4):
            if (pos[fingers[i]][2] < pos[fingers[i]-2][2]):
                which_up[i] = 1
        return which_up

    def inZone(self,frame,x_left,y_top,x_right,y_bot):
        pos = self.getPosition(frame)
        pointOfInterest = [0,4,12,20]
        check = 0
        for i in pointOfInterest:
            if (pos[i][1] > x_left and pos[i][1] < x_right) and (pos[i][2] < y_bot and pos[i][2] > y_top) :
                check += 1
        if check == 4:
            return True
        else:
            return False

# KEEP HAND IN ZONE
# 4 Fingers UP = PLAY
# TWO FINGERS = SKIP 5 SECONDS
# ONE FINGERS = GO BACK 5 SECONDS
# ROCK SIGN = FULLSCREEN

def main():
    #GET WEBCAM
    cap = cv2.VideoCapture(0)
    cap.set(3,1280)
    cap.set(4,720)
    detector = handDetector(min_detection_confidence=0.8,min_track_confidence=0.65)

    X_left = 800
    X_right = 1200
    Y_top = 200
    Y_bot = 500

    prevPause = time.time()
    pauseTime = 1

    prevSkip = time.time()
    prevBack = time.time()
    skipTime = 0.5

    prevFull = time.time()
    skipFull = 1

    frameCheck = 0  

    while True:
        _,frame = cap.read()
        frame = cv2.flip(frame,1)
        frame = detector.findHands(frame,draw=True)
        lmList = detector.getPosition(frame)
        frame = cv2.rectangle(frame, (X_left,Y_top), (X_right,Y_bot),(0,0,255),4)
        cv2.putText(frame, 'Active Zone', (X_left, Y_top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)

        frameCheck += 1
        
        if len(lmList) != 0 and frameCheck % 5 == 0:
            frameCheck = 0
            #IF HAND IN ACTIVE ZONE
            if detector.inZone(frame,X_left,Y_top,X_right,Y_bot):
                fingUp = detector.fingersUp(frame)

                #PLAY/PAUSE VIDEO = ALL FINGERS UP
                if fingUp == [1,1,1,1] and time.time() - prevPause > pauseTime: 
                    pg.press('space')
                    prevPause = time.time()

                #GO FORWARD 5 SECONDS
                elif fingUp == [1,1,0,0] and time.time() - prevSkip > skipTime:
                    pg.press('right')
                    prevSkip = time.time()

                #GO BACKWARDS FIVE SECONDS
                elif fingUp == [1,0,0,0] and time.time() - prevBack > skipTime:
                    pg.press('left')
                    prevBack = time.time()

                #GO FULLSCREEN
                elif fingUp == [1,0,0,1] and time.time() - prevFull > skipFull:
                    pg.press('f')
                    prevFull = time.time()


        cv2.imshow("Tracking", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

if __name__ == "__main__":
    main()

    