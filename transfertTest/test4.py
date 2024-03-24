import numpy 

# i = 0
# j = 0
# arr =  numpy.zeros((4, 4))

# c = 0
# for k in range(4):
#     print(f"i{i}, j{j}")
#     c += 1
#     arr[i][j] = c

#     if(k % 2 == 0):
#         for a in range(3):
#             j += 1
#             print(f"i{i}, j{j}")
#             c += 1
#             arr[i][j] = c
            
            
#     else:
#         for a in range(3):
#             j -= 1
#             print(f"i{i}, j{j}")
#             c+=1
#             arr[i][j] = c
            
#     i += 1

#     for a in arr:
#         print(a)

def runSquareGrid(n, func, inc):
    i = 0
    j = 0
    c = 0
    for k in range(n):
        func(i, j, c)
        c += inc
        if(k % 2 == 0):
            for a in range(n-1):
                j += 1
                func(i, j, c)
                c += inc
        else:
            for a in range(n-1):
                j -= 1
                func(i, j, c)
                c += inc   
        i += 1

n=20
arr =  numpy.zeros((n, n))
for a in arr:
    print(a)
def fu(i, j, c):
    # print(f"i{i}, j{j}")
    # c += 1
    arr[i][j] = c
    
runSquareGrid(n, fu, 1)
print("")
for a in arr:
    print(a)
