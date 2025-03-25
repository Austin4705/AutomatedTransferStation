import cv2

# Initialize video capture from default camera (usually 0)
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

# Check if camera opened successfully
if not cap.isOpened():
    print("Error: Could not open camera")
    exit()

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2048)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1536)
    
    # If frame is read correctly ret is True
    if not ret:
        print("Error: Can't receive frame")
        break

    cv2.imshow('Video Stream', frame)
    
    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture and destroy windows
cap.release()
cv2.destroyAllWindows()