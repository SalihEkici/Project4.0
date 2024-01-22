import cv2

# Open a connection to the webcam (usually 0 for the default camera)
cap = cv2.VideoCapture(0)

# Define the codec and create a VideoWriter object with MP4 format
fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # You can also use 'XVID' for AVI
out = cv2.VideoWriter(
    "output.mp4", fourcc, 30.0, (1920, 1080)
)  # Assuming 30 frames per second

buffer_amount = 450  # equal to 15 seconds at 30 fps
buffer_amount_incident = 1000
buffer_array = []


def createVideo(buffer_array, out):
    for buffer_frame in buffer_array:
        out.write(buffer_frame)


while cap.isOpened():
    # Capture frame-by-frame
    ret, frame = cap.read()

    if ret:
        # Resize the frame to match the desired resolution
        frame = cv2.resize(frame, (1920, 1080))

        if len(buffer_array) >= buffer_amount:
            buffer_array.pop(0)
            buffer_array.append(frame)
        else:
            buffer_array.append(frame)

        # Display the resulting frame
        cv2.imshow("Frame", frame)
        print(len(buffer_array))

        # Break the loop if 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        # Create a video from the buffered frames
        break

createVideo(buffer_array, out)

# Release everything when the job is done
cap.release()
out.release()
cv2.destroyAllWindows()
