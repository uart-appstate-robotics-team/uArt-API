import numpy as np
import os
import sys
import time
import threading

import perspective

import cv2

from PIL import Image

#sys.path.append(os.path.join(os.path.dirname(_file_), '../../..'))
from uarm.wrapper import SwiftAPI
from uarm.tools.list_ports import get_ports

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
    #
    #  __init__
    #      im = the image you're trying to paint
    #      pixels = the dictionary of colors you have access to
    #      initialized = a list of booleans determining which values you will initialize
    #          [ True = available_pixel uses pixels parameter otherwise use defaults,
    #            True = set swift to SwiftAPI object otherwise set them to None,
    #            True = set image to a blank white 200x200 image,
    #            True = calibrate canvas_corners using setFourCorners otherwise set to a preset 
    #          ]
    #    
    def __init__(self, im, pixels, initialized):
        if initialized[0]:
            self.available_pixel = pixels
        else:
            self.available_pixel = {'red':[255,0,0], 'green':[0,255,0], 'blue':[0,0,255],'magenta':[255,0,255], 'tomato':[255,99,71], 'lawn green':[124,252,0]}
        if initialized[1]:
            self.swift = SwiftAPI(filters={'hwid': 'USB VID:PID=2341:0042'})
            self.device_info = self.swift.get_device_info()
            self.firmware_version = self.device_info['firmware_version']
            self.swift.set_mode(0)
        if initialized[2]:
            self.image = im
        print("Setting four corners; input tl, tr, bl or br")
        if initialized[3] and initialized[1]:
            self.canvas_corners = self.setFourCorners()
        else:
            self.canvas_corners =  [[271.41, 100.41, 160.48], [271.48, -88.76, 162.2], [196.59, 85.7, -97.66], [195.83, -82.88, -90.02]]

        _, cap = cv2.VideoCapture(0).read()
        self.ptransform = perspective.PerspectiveTransform(self.image)        
        self.M = self.get_m()
        print("Arm all set up!")

    
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

            swift.set_position(x=x, y=y, z=z, speed =f, cmd = "G0")
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
    def get_m(self):
        A = np.transpose(self.canvas_corners)
        print(A)
        B = [[0,0,1],[200,0,1],[0,200,1],[200,200,1]]
        B = np.transpose(B)
        print(B)
        pinvB = np.linalg.pinv(B)
        print(pinvB)
        M = np.matmul(A, np.linalg.pinv(B))
        print(M)
        return M

#
#    xytoxyz
#
    def xy_to_xyz(self,xy):
        xyz = [xy[0],xy[1],1]
        xyz = np.transpose(xyz)
        return np.matmul(self.M,xyz)

#
#    go to position
#
    def go_to_position(self, xyz, f):
        self.swift.set_position(x=xyz[0], y=xyz[1], z=xyz[2], speed = f, cmd = "G0")
#:        time.sleep(1)

#
#    draw a line
#
#    start and end: [x,y]
    def draw_line(self, start, end):
        startxyz = self.xy_to_xyz(start)
        endxyz = self.xy_to_xyz(end)

        start_pre = [startxyz[0]-50, startxyz[1], startxyz[2]]
        end_post = [endxyz[0]-50, endxyz[1], endxyz[2]]
        print("going to start pre")
        self.go_to_position(start_pre, 10000)
        print("going to start")
        self.go_to_position(startxyz, 5000)
        print("going to end")
        self.go_to_position(endxyz, 5000)
        print("going to end post")
        self.go_to_position(end_post, 10000)


    def draw_line2(self, points):
        startxyz = self.xy_to_xyz(points[0])
        endxyz = self.xy_to_xyz(points[-1])
        start_pre = [startxyz[0]-20, startxyz[1], startxyz[2]]
        end_post = [endxyz[0]-20, endxyz[1], endxyz[2]]

        print("going to start pre")
        self.go_to_position(start_pre, 10000)
        for point in points:
            point_xyz = self.xy_to_xyz(point)
            self.go_to_position(point_xyz, 5000)
        print("going to end post")
        self.go_to_position(end_post, 10000)

image = cv2.resize(cv2.imread("./images/1x1.png"), (200,200))
uart = uart_api(image)

print("head")
uart.draw_line2([[139,61],[159,61],[166,52],[166,38],[159,33],[141,33],[132,38],[132,55],[139,61]])

print("neck")
uart.draw_line2([[148,63],[148,71]])

print("body")
uart.draw_line2([[148,71],[148,122]])

print("right leg")
uart.draw_line2([[148,122],[175,183]])

print("left leg")
uart.draw_line2([[148,122],[121,183]])

print("left arm")
uart.draw_line2([[148,71],[114,104]])

print("right arm")
uart.draw_line2([[148,71],[176,108]])

asdf = input("go y/n")

uart.draw_line2([[139,61],[159,61],[166,52],[166,38],[159,33],[141,33],[132,38],[132,55],[139,61]])

uart.draw_line2([[148,63],[148,71]])

uart.draw_line2([[148,71],[148,122]])

uart.draw_line2([[148,122],[121,183]])

uart.draw_line2([[148,122],[175,183]])

uart.draw_line2([[148,71],[114,104]])

uart.draw_line2([[148,71],[176,108]])
