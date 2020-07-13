# expects a one channel image, puts the pen down if the value is equal to 0 
def area_fill_horizontal(image):
    point = None
    points = [[]]
    line_number = 0
    for i, x in enumerate(image):
        for j, col in enumerate(x):
            nextpoint = (j, i)
            if point is not None:
                if image[point[1]][point[0]] == 0:
                    points[line_number].append(point)
                if image[point[1]][point[0]] == 0 and image[nextpoint[1]][nextpoint[0]] > 0:
                    line_number += 1
                    points.append([])
            point = nextpoint
    del points[-1]
    return points


