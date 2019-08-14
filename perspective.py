# USAGE
# python click_and_crop.py --image jurassic_park_kitchen.jpg

# import the necessary packages
import argparse
import cv2
import numpy as np
from PIL import Image
import os
class PerspectiveTransform:
	def __init__(self, image):
		width,height,channels = image.shape
		print(width, height, channels)
		oneXone = cv2.imread(os.path.split(os.path.abspath(__file__))[0] + "/images/1x1.png")
		print("cv2",oneXone)

		self.selection = cv2.resize(oneXone, (height, width))
		self.image = image
		self.warped = None
		self.points = []
		self.set_corners()
		self.perspective_transform()


	def order_points(self, pts):
		rect = np.zeros((4, 2), dtype = "float32")
		s = np.sum(pts,axis = 1)
		rect[0] = pts[np.argmin(s)]
		rect[2] = pts[np.argmax(s)]
		diff = np.diff(pts, axis = 1)
		rect[1] = pts[np.argmin(diff)]
		rect[3] = pts[np.argmax(diff)]
		return rect
	
	def click_and_place(event, x, y, flags, self):
		if event == cv2.EVENT_LBUTTONDOWN and len(self.points) < 4:
	        	print("click!")
	        	self.points.append((x,y))
	        	print(self.points)
	        	cv2.circle(self.selection, self.points[-1], 5, (0,0,255), -1)

	def set_corners(self):
		clone = self.image.copy()
		sclone = self.selection.copy()
		added = self.selection.copy()

		cv2.namedWindow("image")
		#cv2.setMouseCallback("image", click_and_crop)
		cv2.setMouseCallback("image", PerspectiveTransform.click_and_place, self)
		# keep looping until the 'c' key is pressed
		lines = False
		while True:
			# display the image and wait for a keypress
			if len(self.points) == 4 and lines == False:
				self.selection = sclone.copy()
				rect = self.order_points(self.points)
				cv2.line(self.selection,tuple(rect[0]),tuple(rect[1]),(0,255,0), thickness=3, lineType=8)
				cv2.line(self.selection,tuple(rect[1]),tuple(rect[2]),(0,255,0), thickness=3, lineType=8)
				cv2.line(self.selection,tuple(rect[2]),tuple(rect[3]),(0,255,0), thickness=3, lineType=8)
				cv2.line(self.selection,tuple(rect[3]),tuple(rect[0]),(0,255,0), thickness=3, lineType=8)
				lines = True
			cv2.addWeighted(self.selection, .4, self.image, 0.6, 0, added)
			cv2.imshow("image", added)
			key = cv2.waitKey(1) & 0xFF
			# if the 'r' key is pressed, reset the cropping region
			if key == ord("r"):
				self.image = clone.copy()
				self.points.clear()
				selection = cv2.resize(cv2.imread("./images/1x1.png"), (height, width))	# if the 'c' key is pressed, break from the loop
				lines = False
			elif key == ord("c"):
				break

	def perspective_transform(self):
		rect = self.order_points(self.points)
		(tl, tr, br, bl) = rect
		widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
		widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
		maxWidth = max(int(widthA), int(widthB))
		heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
		heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
		maxHeight = max(int(heightA), int(heightB))

		dst = np.array([
			[0,0],
			[maxWidth-1,0],
			[maxWidth-1, maxHeight-1],
			[0,maxHeight-1]], dtype="float32")
		M = cv2.getPerspectiveTransform(rect, dst)
		self.warped = cv2.warpPerspective(self.image, M, (maxWidth, maxHeight))

		
	def update_warped(self,image):
    		self.image = image
    		self.perspective_transform()

	def get_warped(self):
		return self.warped


