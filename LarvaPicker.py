# Copyright 2016, FlySorter LLC

import fsSerial
import os
import glob
import cv2
import numpy as np
import sys

# General structure of this program:
#
# 1. Initialize serial port to communicate with SmoothieBoard
# 2. Read in config information for transformation between
#    image coordinates and robot coordinates, and also Z heights.
# 3. Watch for change in designated image file
# 4. When change occurs:
#       a. Open image file
#       b. Find larva(e) around perimeter of agar bed
#       c. If found:
#           i. Find open space(s) near center of agar bed
#           ii. Direct robot to reposition larva(e)
#           iii. Move robot out of view
# Ongoing - listen for interrupt; quit cleanly.

if ( len(sys.argv) != 2 ) or ( int(sys.argv[1]) < 1 ) or ( int(sys.argv[1]) > 3 ):
    print "Usage: {0} N".format(sys.argv[0])
    print "Where N is the size/age of the larvae -- 1, 2, or 3"
    exit()

# Configuration parameters

COMPort = "COM3"
homographyFile = "homography.npy"
zHeightMapFile = "zHeightMap.npy"
imageFile = "TestImage.png"
instar = int(sys.argv[1])

ZTravel = -10.
ZPickups = [0.5, 1.1, 1.7]
ZDropoffs = [0.7, 1.2, 1.7]

# Import homography
h = np.load(homographyFile)
hInv = np.linalg.inv(h)

# Import z height points and find plane equation for agar bed
measuredHeights = np.load(zHeightMapFile)

# Equation of a plane is a*x + b*y * c*z = d

# These three points are in the plane
p1 = measuredHeights[0]
p2 = measuredHeights[1]
p3 = measuredHeights[2]

# Therefore, these two vectors are in the plane
v1 = p3 - p1
v2 = p2 - p1

# The cross product is a vector normal to the plane
cp = np.cross(v1, v2)
a, b, c = cp

# This evaluates a * x3 + b * y3 + c * z3 which equals d
d = np.dot(cp, p3)

print('The equation is {0}x + {1}y + {2}z = {3}'.format(a, b, c, d))


# Define a few functions. Program continues below.

# To calculate the Z height of the agar bed at any X/Y coordinate:
# Use plane equation, solve for Z.
# z = (d - a*x - b*y)/c
def getZHeight(pt, a, b, c, d):
    x = pt[0]
    y = pt[1]
    if c == 0:
        return None
    return (d - a*x - b*y)/c

# Function to reposition larvae given:
#   source (np array, X & Y coordinates)
#   dest   (np array, X & Y coordinates)
#   instar (integer -- 1, 2 or 3)
def pickLarva(source, dest, z, instar):
    global ZTravel, ZPickups, ZDropoffs, robot
    assert (type(source) is numpy.ndarray and source.shape == (2L,) ), "source should be numpy array of shape (2L,)"
    assert (type(dest) is numpy.ndarray and dest.shape == (2L,) ), "dest should be numpy array of shape (2L,)"
    assert (instar == 1 or instar == 2 or instar == 3), "instar should be 1, 2 or 3"

    robot.sendSyncCmd("G01 F12000\n")
    robot.sendSyncCmd("G01 X{0} Y{1}\n".format(source[0], source[1]))
    robot.sendSyncCmd("G01 Z{0}\n".format(z+ZPickups[instar-1]))
    robot.sendSyncCmd("G04 P100\n")
    robot.sendSyncCmd("M42\n")
    robot.sendSyncCmd("G01 Z{0}\n".format(z+ZPickups[instar-1]+0.1))
    robot.sendSyncCmd("G04 P250\n")
    robot.sendSyncCmd("G01 F500 Z{0}\n".format(ZTravel))
    robot.sendSyncCmd("G01 F12000 X{0} Y{1}\n".format(dest[0], dest[1]))
    robot.sendSyncCmd("G01 F4000 Z{0}\n".format(z+ZDropoffs[instar-1]))
    robot.sendSyncCmd("M106\n")
    robot.sendSyncCmd("G04 P15\n")
    robot.sendSyncCmd("M43\n")
    robot.sendSyncCmd("M107\n")
    robot.sendSyncCmd("G04 P1000\n")
    robot.sendSyncCmd("G01 Z{0}\n".format(ZTravel))

def parseImage(img):
    larvaList = []
    return larvaList

robot = fsSerial.findSmoothie()

if robot is None:
    print "Couldn't find SmoothieBoard. Exiting."
    exit()

robot.sendSyncCmd("G28\n")
robot.sendSyncCmd("G90\n")

prevTime = os.path.getmtime(imageFile)

while True:
    try:
        # Check file time
        if ( os.path.getmtime(imageFile) != prevTime ):
            # Load image from file
            latestImage = cv2.imread(imageFile)
            # Parse image and move larvae (if necessary)
            larvaList = parseImage(latestImage)
            n = len(larvaList)
            larvaListRobot = cv2.perspectiveTransform(larvaList.reshape((n, 1, 2)), h).reshape((n, 2))
            for larva in larvaListRobot:
                zHeightAtLarva = getZHeight(larva, a, b, c, d)
                pickLarva(larva[0], larva[1], zHeightAtLarva, instar)
            robot.sendSyncCmd("G01 F12000 X0 Y0\n")
            robot.sendSyncCmd("M84\n")
        time.sleep(0.25)
    except KeyboardInterrupt:
        break

robot.sendSyncCmd("G28\n")
robot.sendSyncCmd("M84\n")
robot.close()
print "Exiting!"
time.sleep(3)
