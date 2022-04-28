import cv2
import time
import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib
from threading import Thread

class Robocam:
    stepMotor = RpiMotorLib.BYJMotor("MyMotorOne", "28BYJ") # Create stepmotor object
    threadExists = False # Track existence of motor running thread
    pins = [2, 3, 4, 17] # Motor driver pins
    buzzerPin = 26 # Pin for piezo passive buzzer
    GPIO.setup(buzzerPin, GPIO.OUT)

    def turn(turnCCW): # Turns robot full rotation in either direction
        Robocam.stepMotor.motor_run(Robocam.pins, 0.015, 512, turnCCW, False, "full", 0.001)
        Robocam.threadExists = False
        
    def startThread(CCW): # Creates motor running thread and calls turn()
        if not Robocam.threadExists:
            Robocam.threadExists = True
            t = Thread(target = Robocam.turn, args = (CCW, ))
            t.start()

    def buzz(noteFreq, duration): # Plays notes using buzzer
        halfWaveTime = 1 / (noteFreq * 2)
        waves = int(duration * noteFreq)
        for i in range(waves):
            GPIO.output(Robocam.buzzerPin, True)
            time.sleep(halfWaveTime)
            GPIO.output(Robocam.buzzerPin, False)
            time.sleep(halfWaveTime)
        
    def play(notes):
        for n in notes:
            Robocam.buzz(n, 0.1)
            time.sleep(0.01)
        
    def main():

        faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml") # Create CascadeClassifier object with generic Haar face model

        video = cv2.VideoCapture(0)

        screenWidth = 640
        screenHeight = 480

        video.set(3, screenWidth)
        video.set(4, screenHeight)
        time.sleep(2) # Sleep to allow image sensor to warm up

        GPIO.setmode(GPIO.BCM)
        leftBtnPin = 21
        GPIO.setup(leftBtnPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        rightBtnPin = 20
        GPIO.setup(rightBtnPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        offBtnPin = 16
        GPIO.setup(offBtnPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        startTracking = True
        Robocam.play([500, 600, 800]) 
        
        while True:
            
            # Button inputs
            leftBtnPressed = not GPIO.input(leftBtnPin)
            rightBtnPressed = not GPIO.input(rightBtnPin)
            offBtnPressed = not GPIO.input(offBtnPin)
            
            # If off button is pressed, stop motor and stop face tracking            
            if (offBtnPressed):
                offBtnPressed = not GPIO.input(offBtnPin)
                startTracking = not startTracking
                Robocam.stepMotor.motor_stop()
                
                # Play appropriate notes
                if (startTracking):
                    notes = [500, 600, 800]
                else:
                    notes = [600, 500, 400]
                    
                Robocam.play(notes)
            
            # If moving manually or not tracking, give control only to buttons
            if ((leftBtnPressed or rightBtnPressed) or not startTracking):
                if (leftBtnPressed):
                    Robocam.stepMotor.motor_run(Robocam.pins, 0.015, 1, False, False, "full", 0.001)
                elif (rightBtnPressed):
                    Robocam.stepMotor.motor_run(Robocam.pins, 0.015, 1, True, False, "full", 0.001) 
            else:
                # Capture frame-by-frame
                ret, frame = video.read()

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                faces = faceCascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                if (len(faces) > 0):
                    
                    maxFaceArea = 0
                    
                    # Closest face (greatest face area) will be the face tracked
                    for face in faces:
                        faceArea = face[2] * face[3]
                        if (faceArea > maxFaceArea):
                            maxFaceArea = faceArea
                            currentFace = face
                    
                    # Find X-coordinate of face middle
                    faceWidth = currentFace[2]
                    x = (int) (currentFace[0] + (faceWidth / 2))
                    
                    # Depending on where face is respective to middle, start thread moving motor in corresponding direction
                    if (x < (screenWidth / 2) - 50):
                        Robocam.startThread(True)
                    elif (x > (screenWidth / 2) + 50):
                        Robocam.startThread(False)
                    else:
                        Robocam.stepMotor.motor_stop() # If face is centered, stop motor
                else:
                    Robocam.stepMotor.motor_stop() # If no faces found, stop motor

        # When everything is done, release the capture
        video_capture.release()
        cv2.destroyAllWindows()

Robocam.main()
