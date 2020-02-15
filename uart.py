import numpy as np
import os
import sys
import time
import threading

#from perspective import PerspectiveTransform

import cv2

from PIL import Image


# sys.path.append(os.path.join(os.path.dirname(_file_), '../../..'))
from uarm.wrapper import SwiftAPI
from uarm.tools.list_ports import get_ports


class uart:
    # rgb values of all the paints
    available_pixel = {}

    # robot arm object
    swift = None
    device_info = None
    firmware_version = None

    # image you're trying to paint
    image = None

    # image of the canvas as you're working on it
    canvas = None

    # points of the four corners of the canvas (in robot arm coords)
    canvas_corners = None

    # contains the warped image of
    ptransform = None

    # transformation matrix
    xScale = None
    yScale = None

    DRAW_SPEED = 5000
    LIFT_SPEED = 10000

    """
    __init__
        im = the image you're trying to paint/draw
        pixels = the dictionary of colors you have access to
        initialized = a list of booleans determining which values you will initialize
            0: available_pixel uses pixels parameter otherwise use defaults,
            1: set swift to SwiftAPI object otherwise set them to None,
            2: set image to a blank white 200x200 image,
            3: calibrate canvas_corners using setFourCorners otherwise set to a preset
            4: set ptransform using the webcam
            ]
    """

    def __init__(self, im, pixels, initialized):
        if initialized[0]:
            self.available_pixel = pixels
        else:
            self.available_pixel = {
                "red": [255, 0, 0],
                "green": [0, 255, 0],
                "blue": [0, 0, 255],
                "magenta": [255, 0, 255],
                "tomato": [255, 99, 71],
                "lawn green": [124, 252, 0],
            }

        if initialized[1]:
            self.swift = SwiftAPI(filters={"hwid": "USB VID:PID=2341:0042"})
            self.device_info = self.swift.get_device_info()
            self.firmware_version = self.device_info["firmware_version"]
            self.swift.set_mode(0)

        if initialized[2]:
            self.image = im

        if initialized[3] and initialized[1]:
            print("moving")
            self.go_home()
            print("Setting four corners; input tl, tr, bl or br")
            self.canvas_corners = self.setFourCorners()
        else:
            # painting corners
            self.canvas_corners = [
             [230, 80, 168],  # tl
             [230, -85, 168],  # tr
             [228, 80, -40],  # bl
             [228, -85, -40], #br
            ]

            # stippling/drawing corners
            #self.canvas_corners = [
            #    [230	,50	,153], 		#tl
            #    [229.5	,-48.5	,154.5],	#tr
            #    [233	,47.5	,29],		#bl
            #    [232.5	,-50.5	,31]		#br
            #]

            print("Setting four corners to default coordinates")

        if initialized[4]:
            _, cap = cv2.VideoCapture(0).read()
            self.ptransform = perspective.PerspectiveTransform(cap)


        #print(self.canvas_corners)
        #print(im)
        self.xScale = self.get_scale(
            len(im[0]), [self.canvas_corners[0], self.canvas_corners[1]]
        )
        self.yScale = self.get_scale(
            len(im), [self.canvas_corners[0], self.canvas_corners[2]]
        )

        print("Arm all set up!")

    """
    GO HOME
    sends the robot to it's home coordinate
    """
    def go_home(self):
        self.go_to_position([125,0,50],10000)

    """
    new xy to xyz function using algebra/geometry
    """

    def xy_to_xyz_geom(self, xy):
        # print("xy", xy)
        # print("xscale", self.xScale)
        # print("yscale", self.yScale)
        out = np.add(
            np.multiply(xy[0], self.xScale) + np.multiply(xy[1], self.yScale),
            self.canvas_corners[0],
        )
        #print(out)
        return out

    """
    GET SCALE
    """

    def get_scale(self, pix, corners):
        dif = np.subtract(corners[0], corners[1])
        return -(dif / pix)

    """
    HEAT MAP
    """

    def perspective_heatmap(self):
        image = self.image.astype(dtype="int32")
        canvas = self.ptransform.warped.astype(dtype="int32")
        return generate_heatmap(image, canvas)

    def generate_heatmap(self, image1, image2):
        image1 = image1.astype(dtype="int32")
        image2 = image2.astype(dtype="int32")
        subtraction = np.subtract(image1, image2)
        #print(subtraction)

        heatmap = np.full(im.shape, 255, dtype="uint8")
        #print(heatmap.shape)

        for i in range(subtraction.shape[0]):
            for j in range(subtraction.shape[1]):
                if subtraction[i][j] < 0:
                    heatmap[i][j][0] -= abs(subtraction[i][j])
                    heatmap[i][j][1] -= abs(subtraction[i][j])
                elif subtraction[i][j] > 0:
                    heatmap[i][j][2] -= abs(subtraction[i][j])
                    heatmap[i][j][1] -= abs(subtraction[i][j])
        return heatmap

    def grayscale_heatmap(self, image1, image2):
        image1 = image1.astype(dtype="int32")
        image2 = image2.astype(dtype="int32")
        subtraction = np.subtract(image1, image2)
        return subtraction

    """
    GETS CLOSEST COLOR
    """

    def get_closest_color(self, chosen_pixel):
        available_pixel = self.available_pixel
        distances = []

        for key, value in available_pixel.items():
            a1 = np.asarray(value)
            c1 = np.asarray(chosen_pixel)
            curr_dist = np.linalg.norm(a1 - c1)
            distances += [curr_dist]
            if curr_dist == min(distances):
                curr_key = key

        return curr_key

    """
    move_to_file
    """

    def move_to_file(self, filename):
        var = []
        count = 0
        lines = open(filename, "r").read().split("\n")
        del lines[-1]
        x, y, z, f, angle = 0,0,0,0,0
        moveArm = False
        #print(lines)

        for i in range(len(lines)):
            for word in lines[i].split(" "):
                #print(word)
                if word == "":
                    pass
                elif word[0] == "X":
                    x = float(word[1:])
                elif word[0] == "Y":
                    y = float(word[1:])
                elif word[0] == "Z":
                    z = float(word[1:])
                elif word[0] == "F":
                    f = float(word[1:])

            #print("GO GO GO")
            #print(x,y,z,f)
            self.swift.set_position(x, y, z, speed=f, cmd="G0")
            #time.sleep(1)

    """
    SETTING FOUR CORNERS
    """

    def setFourCorners(self):
        speed_s = 10000
        delay = 1
        cmd_s = "G0"
        todo = 4
        coords = [[], [], [], []]
        while todo > 0:
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

    """
    SAVED COORDS TO FILE

    """

    def save_coords_to_file(self, fn):
        delay = 1

        xinput = 0
        yinput = 0
        zinput = 0
        x = 0
        y = 0
        z = 0

        coords = []
        while True:
            newCoord = self.swift.get_position() 
            print("current coord:",newCoord)
            key = input("type save to save current position\ntype done to break\nhit enter to do nothing\n")
            if key == "save":
                coords.append(newCoord)
                print(coords)
                print("New coordinate saved as" + str(newCoord))
            elif key == "done":
                print("hello world")
                print(coords)
                with open(fn + ".uar", "a+") as fp:
                    for c in coords:
                        print("writing")
                        fp.write("G0 X{} Y{} Z{} F5000\n".format(c[0], c[1], c[2]))
                break

            print(self.swift.get_position())
            xinput = input('input for x')
            try:
                x = float(xinput)
            except:
                x = x

            yinput = input('input for y')
            try:
                y = float(yinput)
            except:
                y = y

            zinput = input('input for z')
            try:
                z = float(zinput)
            except:
                z = z

            self.go_to_position([x,y,z],10000)

        #self.move_to_file(str(fn + ".uar"))
        return coords

    """
    go to position
    """

    def go_to_position(self, xyz, f):
        #print("going to : ", xyz)
        self.swift.set_position(x=xyz[0], y=xyz[1], z=xyz[2], speed=f, cmd="G0")

    """
    draw a line

    start and end: [x,y]
    """

    def draw_line(self, start_point, end_point):
        startxyz = self.xy_to_xyz_geom(start_point)
        endxyz = self.xy_to_xyz_geom(end_point)

        start_pre = [startxyz[0] - 20, startxyz[1], startxyz[2]]
        end_post = [endxyz[0] - 20, endxyz[1], endxyz[2]]
        #print("going to start pre")
        self.go_to_position(start_pre, self.LIFT_SPEED)
        #print("going to start")
        self.go_to_position(startxyz, self.DRAW_SPEED)
        #print("going to end")
        self.go_to_position(endxyz, self.DRAW_SPEED)
        #print("going to end post")
        self.go_to_position(end_post, self.LIFT_SPEED)

    """
    draw_point draws a point on the canvas
    """

    def draw_point(self, point):
        point = point[0]
#        print(point)
        point_xyz = self.xy_to_xyz_geom(point)

        point_lifted = [point_xyz[0] - 6, point_xyz[1], point_xyz[2]]
#        print("going to pre point")
        self.go_to_position(point_lifted, self.LIFT_SPEED)
#        print("going to point")
        self.go_to_position(point_xyz, self.DRAW_SPEED)
#        print("lifting")
        self.go_to_position(point_lifted, self.LIFT_SPEED)

    """
    Fill black prints by scanning over an image
    """

    def fill_solid(self, image):
        lifted = False
        point = None
        for i, x in enumerate(image):
            for j, col in enumerate(x):
                nextpoint = (j, i)
                if point is not None:
                    if col == 0:
                        point_xyz = self.xy_to_xyz_geom(point)

                        # If you are previously lifted, go to a pre-position
                        if lifted:
                            lifted_pos = [point_xyz[0] - 20, point_xyz[1], point_xyz[2]]
                            self.go_to_position(lifted_pos, self.LIFT_SPEED)

                        self.go_to_position(point_xyz, self.DRAW_SPEED)
                        lifted = False
                    else:
                        if not lifted:
                            point_xyz = self.xy_to_xyz_geom(point)
                            lifted_pos = [point_xyz[0] - 20, point_xyz[1], point_xyz[2]]
                            self.go_to_position(lifted_pos, self.LIFT_SPEED)
                        lifted = True
                point = nextpoint

    """
    draws the signature passed in
    """
    def xy_to_xyz_sig(self, xy, xscale, yscale):
        out = np.add(
            np.multiply(xy[0], xscale) + np.multiply(xy[1], yscale),
            self.canvas_corners[0],
        )
        print(out)
        return out

    """
    draws a line, by moving across a list of points
    does NOT go to pre and post painting position

    CALLS SIGNATURE FUNCTIONS
    """

    def draw_line_sig(self, points, xscale, yscale):
        startxyz = self.xy_to_xyz_sig(points[0],xscale,yscale)
        endxyz = self.xy_to_xyz_sig(points[-1],xscale,yscale)
        start_pre = [startxyz[0] - 8, startxyz[1], startxyz[2]]
        end_post = [endxyz[0] - 8, endxyz[1], endxyz[2]]

        self.go_to_position(start_pre, self.LIFT_SPEED)

        for point in points:
            point_xyz = self.xy_to_xyz_sig(point,xscale,yscale)
            self.go_to_position(point_xyz, self.DRAW_SPEED*.5)

        self.go_to_position(end_post, self.LIFT_SPEED)

    def draw_signature(self, image):
        from area_fill_horizontal import area_fill_horizontal
        lines = area_fill_horizontal(image)
        xscale = self.get_scale(
            115, [self.canvas_corners[0], self.canvas_corners[1]]
        )
        yscale = self.get_scale(
            115, [self.canvas_corners[0], self.canvas_corners[2]]
        )
        for line in lines:
            self.draw_line_sig(line, xscale, yscale)

    """
    draw_points calls draw_point over a list of points
    """

    def draw_points(self, points):
        point_counter = 0
        num_points = len(points)
        for point in points:
            point_counter += 1
            self.draw_point(point)
            if (point_counter % (num_points//10)) == 0:
                print(int((point_counter/num_points)*100),"% complete...")

    """
    draws a line, by moving across a list of points
    """

    def draw_line2(self, points):
        startxyz = self.xy_to_xyz_geom(points[0])
        endxyz = self.xy_to_xyz_geom(points[-1])
        start_pre = [startxyz[0] - 8, startxyz[1], startxyz[2]]
        end_post = [endxyz[0] - 8, endxyz[1], endxyz[2]]

        self.go_to_position(start_pre, self.LIFT_SPEED)

        for point in points:
            point_xyz = self.xy_to_xyz_geom(point)
            self.go_to_position(point_xyz, self.DRAW_SPEED)

        self.go_to_position(end_post, self.LIFT_SPEED)

    """
    draws a line, by moving across a list of points
    does NOT go to pre and post painting position
    """

    def draw_line3(self, points):
        startxyz = self.xy_to_xyz_geom(points[0])
        endxyz = self.xy_to_xyz_geom(points[-1])
        for point in points:
            point_xyz = self.xy_to_xyz_geom(point)
            self.go_to_position(point_xyz, self.DRAW_SPEED)


