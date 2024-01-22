import cv2

# Open a connection to the webcam (usually 0 for the default camera)
cap = cv2.VideoCapture(0)

# Define the codec and create a VideoWriter object with MP4 format
fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # You can also use 'XVID' for AVI
out = cv2.VideoWriter("output.mp4", fourcc, 20.0, (1920, 1080))

while cap.isOpened():
    # Capture frame-by-frame
    ret, frame = cap.read()

    if ret:
        # Resize the frame to match the desired resolution
        frame = cv2.resize(frame, (1920, 1080))

        # Write the frame to the video file
        out.write(frame)

        # Display the resulting frame
        cv2.imshow("Frame", frame)

        # Break the loop if 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        break

# Release everything when the job is done
cap.release()
out.release()
cv2.destroyAllWindows()
