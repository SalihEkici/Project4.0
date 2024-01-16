import cv2
import mediapipe as mp
import math
import time
import numpy as np

# global variables
threshold_line = "------------------------------------------------------------------------------------------------"
previous_y_nose = 1
previous_timestamp = time.time()
status = "Everything OK"

# initialize pose estimator
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)
while cap.isOpened():
    # read frame
    _, frame = cap.read()
    try:
        # resize the frame for portrait video
        frame = cv2.resize(frame, (1920, 1080))

        # convert to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # process the frame for pose detection
        pose_results = pose.process(frame_rgb)

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

        # calculation for the variable threshold height (0,0 is top left)
        y_center_top = (y_left_shoulder + y_right_shoulder) / 2
        y_center_bottom = (y_left_hip + y_right_hip) / 2
        average_height = y_center_bottom - y_center_top
        distanceToLaptop = -(math.log(968) - math.log(average_height)) / -0.314
        threshold_height = 800 - (20 * distanceToLaptop - 20)

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
            if -100 < velocity < 100:
                return 0
            return velocity

        # calculate nose keypoint velocity
        prev_keypoint_position = previous_y_nose
        prev_timestamp = previous_timestamp
        current_keypoint_position = y_nose
        current_timestamp = time.time()

        current_velocity = calculate_instantaneous_velocity(
            prev_keypoint_position,
            current_keypoint_position,
            prev_timestamp,
            current_timestamp,
        )

        # modify status when an incident occurs - addition 'recovered from fall'
        if y_nose > threshold_height and current_velocity > 1000:
            status = "!FALL DETECTED - ALERT SEND!"
        if status == "!FALL DETECTED - ALERT SEND!" and y_nose < threshold_height:
            status = "RECOVERED FROM FALL"

        # show status in top left corner
        cv2.putText(
            frame,
            status,
            (20, 80),
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
        previous_y_nose = y_nose
        previous_timestamp = current_timestamp
    except:
        pass

    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()