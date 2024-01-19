import cv2
import mediapipe as mp
import math
import time
import numpy as np

# global variables - positions
x_nose = 0
y_nose = 0
x_left_shoulder = 0
y_left_shoulder = 0
x_right_shoulder = 0
y_right_shoulder = 0
x_left_hip = 0
y_left_hip = 0
x_right_hip = 0
y_right_hip = 0
current_x_velocity = 0
current_y_velocity = 0
x_average_position = 0
current_timestamp = None

# global variables - previous positions
previous_y_nose = 1
previous_x_hip = 1

threshold_height = 800
threshold_line = "------------------------------------------------------------------------------------------------"
previous_timestamp = time.time()
status = "EVERYTHING OK"
movement_counter = 0
frame_counter = 0
# initialize pose estimator
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap = cv2.VideoCapture("fall_5.mp4")

fps_start_time = time.time()
fps_frame_count = 0
fps = 1

while cap.isOpened():
    # read frame
    _, frame = cap.read()
    # cv2.waitKey(15)

    # resize the frame for portrait video
    frame = cv2.resize(frame, (1920, 1080))

    # convert to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # process the frame for pose detection
    pose_results = pose.process(frame_rgb)

    try: 

        # draw skeleton on the frame
        mp_drawing.draw_landmarks(
            frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS
        )

        # get coordinates from desired keypoints
        image_height, image_width, _ = frame.shape
        x_nose = (
            pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].x
            * image_width
        )
        y_nose = (
            pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].y
            * image_height
        )
        x_left_shoulder = (
            pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x
            * image_width
        )
        y_left_shoulder = (
            pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y
            * image_height
        )
        x_right_shoulder = (
            pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x
            * image_width
        )
        y_right_shoulder = (
            pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y
            * image_height
        )
        x_left_hip = (
            pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP].x
            * image_width
        )
        y_left_hip = (
            pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP].y
            * image_height
        )
        x_right_hip = (
            pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP].x
            * image_width
        )
        y_right_hip = (
            pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP].y
            * image_height
        )

        # calculation for the variable threshold y (0,0 is top left)
        y_center_top = (y_left_shoulder + y_right_shoulder) / 2
        y_center_bottom = (y_left_hip + y_right_hip) / 2
        average_height = y_center_bottom - y_center_top
        distanceToLaptop = -(math.log(968) - math.log(average_height)) / -0.314
        threshold_height = 800 - (20 * distanceToLaptop - 20)

        # calculation for the variable center x (0,0 is top left)
        x_center_top = (x_left_shoulder + x_right_shoulder) / 2
        x_center_bottom = (x_left_hip + x_right_hip) / 2
        x_average_position = (x_center_top + x_center_bottom) / 2

        # velocity of a keypoint -> nose
        def calculate_instantaneous_velocity(
            previous_position, current_position, previous_time, current_time
        ):
            delta_position = current_position - previous_position
            delta_time = current_time - previous_time

            # Check for division by zero to avoid errors
            if delta_time == 0:
                return np.zeros_like(
                    delta_position
                )  # Return zero velocity if no time has passed
            velocity = delta_position / delta_time
            return velocity

        # calculate nose keypoint velocity
        prev_keypoint_position = previous_y_nose
        prev_timestamp = previous_timestamp
        current_keypoint_position = y_nose
        current_timestamp = time.time()

        current_y_velocity = calculate_instantaneous_velocity(
            prev_keypoint_position,
            current_keypoint_position,
            prev_timestamp,
            current_timestamp,
        )

        # calculate hip center keypoint velocity
        prev_keypoint_position = previous_x_hip
        prev_timestamp = previous_timestamp
        current_keypoint_position = x_average_position
        current_timestamp = time.time()

        current_x_velocity = calculate_instantaneous_velocity(
            prev_keypoint_position,
            current_keypoint_position,
            prev_timestamp,
            current_timestamp,
        )
    
    except:
        pass

    # modify status when an incident occurs - addition 'recovered from fall'
    if -200 < current_y_velocity < 200:
        current_y_velocity = 0
    if y_nose > threshold_height and current_y_velocity > 1000:
        status = "!FALL DETECTED - ALERT SEND!"
    if status == "!FALL DETECTED - ALERT SEND!" and y_nose < threshold_height:
        status = "RECOVERED FROM FALL"
    
    if -100 < current_x_velocity < 100:
        current_x_velocity = 0
    if current_x_velocity != 0 and x_average_position != previous_x_hip:
            movement_counter += 1

    if y_nose == previous_y_nose and current_y_velocity != 0: # adjust sensitivity
        status = "!OCCLUDED FALL DETECTED!"

    if status == "!OCCLUDED FALL DETECTED!" and y_nose != previous_y_nose:
        status = "RECOVERED FROM OCCLUDED FALL"
    
    fps_frame_count += 1
    if time.time() - fps_start_time >= 1:
        fps = fps_frame_count / (time.time() - fps_start_time)
        fps_start_time = time.time()
        fps_frame_count = 0

    # show status in top left corner
    cv2.putText(
        frame,
        f"{status}",
        (20, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (255, 255, 255),
        5,
    )

    # cv2.putText(
    #     frame,
    #     f"{current_y_velocity}",
    #     (20, 200),
    #     cv2.FONT_HERSHEY_SIMPLEX,
    #     2,
    #     (255, 255, 255),
    #     5,
    # )

    cv2.putText(
        frame,
        f"FPS: {math.floor(fps)}",
        (20, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (0, 255, 0),
        5,
    )

    cv2.putText(
        frame,
        f"Time moving: {math.floor(movement_counter / 30)} s",
        (20, 300),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (0, 0, 255),
        5,
    )

    # draw threshold line
    cv2.putText(
        frame,
        threshold_line,
        (0, round(threshold_height)),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (0, 255, 0),
        2,
    )

    cv2.imshow("Output", frame)
    print(current_y_velocity)
    previous_y_nose = y_nose
    previous_x_hip = x_average_position
    previous_timestamp = current_timestamp
    previous_frame_counter = frame_counter
    frame_counter += 1

    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()