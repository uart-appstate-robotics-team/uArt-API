class uart_api:
    	def __init__():


	#
	#	HEAT MAP
	#
	def generate_heatmap(image, canvas)
		image = image.astype(dtype='int32')
		canvas = canvas.astype(dtype='int32')

		subtraction = np.subtract(image,canvas)
		print(subtraction)

		im = np.asarray(Image.open('images/Future-human-Face.png').convert('RGB')) 
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


