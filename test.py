lis = ["1","2",[3,4,5],"6",[7,8]]
print(lis)
for element in lis:
    print( element)

def check(inp):
    try:
        num_float = float(inp)
        return True 
    except:
        return False

print([check(s) for s in lis])
