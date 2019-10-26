import uart
#from inverseEdgePoints import inverse_edgepoints as iep
import cv2
import numpy as np
from PIL import Image

from area_fill_horizontal import area_fill_horizontal


im = cv2.imread("./signature.png", cv2.IMREAD_GRAYSCALE)
im = np.array(im)
#im = sp.darken_edges(im, 200)
#lines = iep.generate_edgepoints(im)
#print(lines)


lis = [True, True, False, False, False]
colors = {"red": [255, 0, 0]}

uart = uart.uart(im, colors, lis)
#
#uart.fill_solid(im)

#lines = area_fill_horizontal(im)

uart.draw_signature(im)

