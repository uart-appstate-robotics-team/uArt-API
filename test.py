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
        newCoord = [x, y, z]
        print("current coord:",newCoord)
        key = input("type save to save current position\ntype done to break\nhit enter to do nothing\n")
        if key == "save":
            coords.append(newCoord)
            print(coords)
            print("New coordinate saved as" + str(newCoord))
        elif key == "done":
            print("hello world")
            print(coords)
            with open(fn + ".uar", "w+") as fp:
                for c in coords:
                    print("writing")
                    fp.write("G0 X{} Y{} Z{} F5000\n".format(c[0], c[1], c[2]))
            break

        print()
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
#            self.swift.set_position(x=x,y=y,z=z, speed = 10000, cmd = "G0")


    #move_to_file(str(fn + ".uar"))
    return coords

save_coords_to_file(1, "test")
