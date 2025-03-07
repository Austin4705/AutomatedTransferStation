import cv2

cap = cv2.VideoCapture(0)
ret, frame = cap.read()
cv2.imshow('Camera', frame)
cv2.waitKey(0)  # Wait for any key press
cap.release()
cv2.destroyAllWindows() 