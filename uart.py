import numpy as np
import os
import sys
import time
import threading

import perspective

import cv2

#sys.path.append(os.path.join(os.path.dirname(_file_), '../../..'))
#from uarm.wrapper import SwiftAPI
#from uarm.tools.list_ports import get_ports

class uart_api:
    available_pixel = {} #rgb values of all the paints
    swift = None #robot arm object
    device_info = None 
    firmware_version = None
    image = None #image you're trying to paint
    canvas = None #image of the canvas as you're working on it
    canvas_corners = None #points of the four corners of the canvas (in robot arm coords)
    ptransform = None #contains the warped image of
    M = None #transformation matrix
    def __init__(self, im):
        self.available_pixel = {'red':[255,0,0], 'green':[0,255,0], 'blue':[0,0,255],'magenta':[255,0,255], 'tomato':[255,99,71], 'lawn green':[124,252,0]}
        self.swift = SwiftAPI(filters={'hwid': 'USB VID:PID=2341:0042'})
        self.device_info = swift.get_device_info()
        self.firmware_version = device_info['firmware_version']
        self.swift.set_mode(0)
        self.image = im
        self.canvas_corners = self.setFourCorners()
        _, cap = cv2.VideoCapture(0).read()
        self.ptransform = perspective.PerspectiveTransform(self.image)        
        self.M = self.get_m()

#
#	HEAT MAP
#
    def generate_heatmap(self):
        image = self.image.astype(dtype='int32')
        canvas = self.canvas.astype(dtype='int32')

        subtraction = np.subtract(image,canvas)
        print(subtraction)

        heatmap = np.full(im.shape,255, dtype='uint8')

        print(heatmap.shape)
        for i in range(subtraction.shape[0]):
            for j in range(subtraction.shape[1]):
                if (subtraction[i][j] < 0):
                    heatmap[i][j][0] -= abs(subtraction[i][j])
                    heatmap[i][j][1] -= abs(subtraction[i][j])
                elif (subtraction[i][j] > 0):
                    heatmap[i][j][2] -= abs(subtraction[i][j])
                    heatmap[i][j][1] -= abs(subtraction[i][j])

        return heatmap

#
#       GETS CLOSEST COLOR
#
    def get_closest_color(self, chosen_pixel):
        available_pixel = self.available_pixel
        distances = []

        for key, value in available_pixel.items():
            a1 = np.asarray(value)
            c1 = np.asarray(chosen_pixel)
            curr_dist = np.linalg.norm(a1 - c1)
            distances += [curr_dist]
            if(curr_dist == min(distances)):
                curr_key = key

        return curr_key



#
# GoTOList
#
    def move_to_file(filename):
        var = []
        count = 0
        lines = open(filename, "r").read().split('\n')
        x,y,z,f = 0

        for i in range(len(lines)):
            for word in lines[i].split(' '):
                if(word[0] is 'X'):
                    x = float(word[1:])
                elif(word[0] is 'Y'):
                    y = float(word[1:])
                elif(word[0] is 'Z'):
                    z = float(word[1:])
                elif(word[0] is 'F'):
                    f = float(word[1:])
            self.swift.set_position(x=x, y=y, z=z, speed =f, cmd = "G0")
            time.sleep(1)
        coordinates.close()

#
# SETTING FOUR CORNERS
#
    def setFourCorners(self):
         speed_s = 10000
         delay = 1
         cmd_s = 'G0'
         todo = 4
         coords = [[], [], [], []]
         while todo >0:
             key = input()
             if key == "tr":
                 newCoord = self.swift.get_position()
                 coords[1] = newCoord
                 todo -= 1
                 print("Top right coordinate saved as ", newCoord)
             elif key == "tl":
                 newCoord = self.swift.get_position()
                 coords[0] = newCoord
                 todo -= 1
                 print("Top left coordinate saved as", newCoord)
             elif key == "bl":
                 newCoord = self.swift.get_position()
                 coords[2] = newCoord
                 todo -= 1
                 print("Bottom left coordinate saved as", newCoord)
             elif key == "br":
                 newCoord = self.swift.get_position()
                 coords[3] = newCoord
                 todo -= 1
                 print("Bottom right coodirnate saved as", newCoord)

         return coords



#
# SAVED COORDS TO FILE
#
    def saveCoordsToFile(self):
        delay = 1
        cmd_s = 'G0'

        coords = []
        while True:
            key = input()
            if key == "save":
                newCoord = swift.get_position()
                coords.append(newCoord)
                print("New coordinate saved as" + str(newCoord))
            if key == "done":
                break

        if os.path.exists("Coordinates.txt"):
            os.remove("Coordinates.txt")
        file = open("Coordinates.txt", "w+")
        for c in coords:
            file.write("G0 X%f Y%f Z%f F5000\n" %(c[0], c[1], c[2]))
        coordinates.close()
        moveTo("Coordinates.txt")
        return coords
#
# GET M
#
    def get_m(corners):
        A = np.transpose(corners)
        B = [[0,0,1],[200,0,1],[0,200,1],[200,200,1]]
        B = np.transpose(B)
        pinvB = np.linalg.pinv(B)
        print(pinvB.shape)
        M = np.matmul(A, np.linalg.pinv(B))
        print(M.shape)
        return M

#
#    xytoxyz
#
    def xy_to_xyz1(xy):
        xyz = [xy[0],xy[1],1]
        xyz = np.transpose(xyz)
        return np.matmul(self.M,xyz)

_,im = cv2.VideoCapture(0).read()
uart = uart_api(im)

