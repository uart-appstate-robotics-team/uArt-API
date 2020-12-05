from uart_api import uart
from line_generators.stippling_points import stippling as sp
import cv2
import numpy as np
from PIL import Image

import random

###
#
# Example program for making a stippling image
#
###

# load image using opencv2 in grayscale mode
im = cv2.imread("./STIPPLING-IMAGE.png", cv2.IMREAD_GRAYSCALE)

# assert that it is a numpy array
im = np.array(im)
im = sp.darken_edges(im, 120)

jpoints = sp.stippling_points_jitter(im)

uart = uart.uart(im)
uart.go_home()
uart.draw_points(jpoints)

