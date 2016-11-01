# Copyright 2016, FlySorter LLC

import fsSerial
import numpy as np
import cv2

# Outline of camera calibration steps:
# 0. Use pylon viewer to set exposure, gain, etc.
# 1. Direct robot to move to 2 points.
# 2. At each point, direct user to attach corner
#    of printed calibration pattern
# 3. Capture image with camera
# 4. Detect location of calibration points within image.
# 5. Create homography transformation from points.
# 6. Output homography matrix to config file.


robot = fsSerial.findSmoothie()

if robot is None:
    print "Couldn't find SmoothieBoard. Exiting."
    exit()

cornerPoints = [ np.array([50.0, 50.0]),
               np.array([200.0, 200.0]) ]

circlePointsRobot = np.array( [[75.0, 75.0],
                              [150.0, 100.0],
                              [60.0, 175.0],
                              [175.0, 190.0]])

colorList = [ (255, 0, 0),
              (0, 255, 0),
              (0, 0, 255),
              (255, 255, 255) ]

zHeight = -28
transitSpeed = 1000

### Home robot, set to absolute coords
##robot.sendSyncCmd("G28\n")
##robot.sendSyncCmd("G90\n")
##
### Move to first corner of calibration image
##robot.sendSyncCmd("G01 F{0} X{1} Y{2}\n".format(2*transitSpeed, cornerPoints[0][0], cornerPoints[0][1]))
##robot.sendSyncCmd("G01 F{0} Z{1}\n".format(transitSpeed, zHeight))
##robot.sendSyncCmd("G04 P100\n")
##print "Place corner #1 of calibration pattern under tip, and press [enter] to continue."
##t = raw_input()
##
### Move to second corner of calibration image
##robot.sendSyncCmd("G01 F{0} Z{1}\n".format(transitSpeed, zHeight+10))
##robot.sendSyncCmd("G01 F{0} X{1} Y{2}\n".format(2*transitSpeed, cornerPoints[1][0], cornerPoints[1][1]))
##robot.sendSyncCmd("G01 F{0} Z{1}\n".format(transitSpeed, zHeight))
##robot.sendSyncCmd("G04 P100\n")
##print "Place corner #2 of calibration pattern under tip, and press [enter] to continue."
##t = raw_input()
##
### Now image has been placed. Get robot out of the camera's view
##robot.sendSyncCmd("G28\n")
##robot.sendSyncCmd("M84\n")

# Done with the robot, for now.
robot.close()

# Open the camera
webcam = cv2.VideoCapture(2)

# Set the w/h
webcam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 2592)
webcam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 1944)

# Grab an image and flip it around
res, img = webcam.read()
img = cv2.flip(img, -1)

# Find circles
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
circles = cv2.HoughCircles(gray, cv2.cv.CV_HOUGH_GRADIENT, 1.5, 100)

cv2.namedWindow("Calibration")

circlePointsImage = np.zeros((4, 2))

if circles is None:
    print "No circles found."
else:
    icircles = np.round(circles[0, :]).astype("int")
    c = circles.astype(float)[0]
    print "Circles found:", c
    # Sort the circle coordinates 
    s = np.argsort(c, 0)
    # We're interested in the y coords, which is the second column
    sortList = s[:,1]
    # Confirm we found the 4 circles
    if len(sortList) != 4:
        print "Should have found 4 circles, instead found:", len(sortList)
    # Now fill in the list of circlePoints in the image based
    # on the order in sortList.
    for x in range(len(sortList)):
        circlePointsImage[x] = c[sortList[x]][0:2]
        # While we're at it, draw the circles on the original image
        cv2.circle(img, (icircles[sortList[x]][0], icircles[sortList[x]][1]),
                   icircles[sortList[x]][2], colorList[x], 4)        

print "Circle points in image:", circlePointsImage

# At this point, we should have our two arrays, and can create a homography
h, status = cv2.findHomography(circlePointsImage, circlePointsRobot)
print h

# Make a scaled copy to display
scaled = cv2.resize(img, (2592/4, 1944/4))
cv2.imshow("Calibration", scaled)
cv2.waitKey()

webcam.release()
cv2.destroyAllWindows()

