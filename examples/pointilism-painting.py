import json
from line_generators.pointilism_color import pointilism

from uart_api import uart
import cv2

import random

##
#
# example program for making a pointilism style painting
# 
##

# opens color from a json
with open('./data.json') as fp:
    data = fp.read()
colors = json.loads(data)

color_dict = {key : value['rgb'] for key, value in colors.items()}
print(color_dict)

# load image using opencv
image = cv2.imread('./lorelai-crop-gs-100.png')

# generate uart object
uart = uart.uart(image, color_dict)

# get points and colors
#  looks like: [
#  				['COLOR_NAME', (x, y)],
#  				...
#  			   ]
lines = pointilism.generate(image, color_dict, 300)

current_color = None
points_painted = 0
for key, value in colors.items():
    #set current_color to key
    current_color = key
    print(current_color)

    # dip brush in water
    uart.move_to_file("./move_commands/watercup.uar")

    # dip brush in paint of current_color
    uart.move_to_file("./move_commands/colorrail" + colors[current_color]['location'] + ".uar")

    points_painted = 0
    print(len(lines))
    for line in lines:
        if current_color == line[0]:
            uart.draw_point(line)
            points_painted += 1
            del line
            if (points_painted % 25) == 0 and points_painted != 0:
                # every 25 points dip in water again
                uart.move_to_file("./move_commands/watercup.uar")

            if (points_painted % 5) == 0 and points_painted != 0:
                # every 5 points dip in the paint again
                uart.move_to_file("./move_commands/colorrail" + colors[current_color]['location'] + ".uar")


# dip in water a bunch of times to make sure no paint is on the brush
uart.move_to_file("./move_commands/watercup.uar")
uart.move_to_file("./move_commands/watercup.uar")
uart.move_to_file("./move_commands/watercup.uar")
