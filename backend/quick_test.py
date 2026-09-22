import cv2

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
print('Opened:', cap.isOpened())
ret, frame = cap.read()
print('Read:', ret)
if ret:
    print('Shape:', frame.shape)
cap.release()
print("Camera 0 works fine!")
