import numpy 

i = 0
j = 0
arr =  numpy.zeros((4, 4))

c = 0
for k in range(4):
    print(f"i{i}, j{j}")
    c += 1
    arr[i][j] = c

    if(k % 2 == 0):
        for a in range(3):
            j += 1
            print(f"i{i}, j{j}")
            c += 1
            arr[i][j] = c
            
            
    else:
        for a in range(3):
            j -= 1
            print(f"i{i}, j{j}")
            c+=1
            arr[i][j] = c
            
    i += 1

    for a in arr:
        print(a)
