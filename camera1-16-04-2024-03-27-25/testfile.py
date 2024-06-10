import cv2
import numpy as np
from skimage import color

# file = cv2.imread("testFile.png", cv2.IMREAD_ANYCOLOR)
# file = cv2.imread("testFile.png")
# ret, thresh = cv2.threshold(file, 127, 255, 0)
# contours, hierarchy = cv2.findContours(thresh, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE)
                                      
# # draw contours on the original image
# image_copy = file.copy()
# cv2.drawContours(image=image_copy, contours=contours, contourIdx=-1, color=(0, 255, 0), thickness=2, lineType=cv2.LINE_AA)
                
# see the results
# cv2.imshow('None approximation', image_copy)
# Assume equal size in file
file1 = cv2.imread("overlapp41.png")
file2 = cv2.imread("overlapp42.png")
file1Grey = color.rgb2gray(file1)
file2Grey = color.rgb2gray(file2)


y, x, channels = file1.shape
size = 3*2*x*y
sizeGrey = 2*x*y       
A = np.zeros(shape=(sizeGrey,2))
B = np.empty(size)
# A = np.zeros(shape=(size,2))
# B = np.empty(size)

for t in range (size):
    if t % 2 == 0:
        A[t][0] = 1
        A[t][1] = 0
    else:
        A[t][0] = 0
        A[t][1] = 1
for i in range(x):
    for j in range(y):
#         for c in range(3):
#             B[3*2*i*j+c] =  file1[i:j:c] = file2
        B[2(i*x+j)] = file1Grey[i]
print("Done!")
# C = np.multiply(A, A.T)

# cv2.waitKey(0) 