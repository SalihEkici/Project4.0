import cv2
import mediapipe as mp
import math
import time
from datetime import datetime
import numpy as np
import json
from azure.storage.blob import (
    ContentSettings,
    BlobServiceClient,
)
from dotenv import load_dotenv
import os
import requests
import schedule
import threading
# === USER SETTINGS ===
patient_name = "sarah"
camera_id = 1
user_id = 1

# === GLOBAL VARIABLES === #
# keypoint positions
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

previous_y_nose = 1
previous_x_hip = 1
x_average_position = 0

# velocity
current_x_velocity = 0
current_y_velocity = 0

# timestamps
current_timestamp = None
previous_timestamp = time.time()

# video feed
buffer_amount = 100
buffer_array = []
videoTitle = ""
formatted_datetime = []

# other
fall_detected = False
threshold_height = 800
threshold_line = "------------------------------------------------------------------------------------------------"
status = "EVERYTHING OK"
movement_counter = 0
frame_counter = 0
alert_json = None
movement_json = None
tracked_time = None
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
send_movement_boolean = False
cap = cv2.VideoCapture(0)
out = None

fps_start_time = time.time()
fps_frame_count = 0
fps = 1
fourcc = cv2.VideoWriter_fourcc(*'X264')

load_dotenv()

account_name = os.getenv("AZURE_STORAGE_ACCOUNT")
account_key = os.getenv("ACCOUNT_KEY")
container_name = os.getenv("AZURE_STORAGE_CONTAINER")
connection_string = os.getenv("CONNECTION_STRING")



# === FUNCTIONS === #


# create video
def createVideo(array):
    out = cv2.VideoWriter(f"{videoTitle}", fourcc, 20.0, (1920, 1080))
    for array_frame in array:
        out.write(array_frame)
    out.release()


# send video
def sendVideo(videoTitle):
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container_name, videoTitle)
    with open(f"{videoTitle}", "rb") as data:
        content_settings = ContentSettings(content_type="video/mp4")
        try:
            blob_client.upload_blob(data, content_settings=content_settings,timeout = 3600)
            print("Video upload successful")
        except Exception as e:
            print(f"Error uploading video: {e}")
    sendAlert(
            camera_id,
            formatted_datetime,
            videoTitle,
        )
    


# send alert
def sendAlert(cameraId, triggerTime, videoData):
    url = "https://elderguardiansbackend.azurewebsites.net/api/alerts"

    # JSON data to be sent in the POST request
    data = {
        "cameraId": cameraId,
        "triggerTime": triggerTime,
        "videoData": f"https://stelderguardians.blob.core.windows.net/blobelderguardians/{videoData}",
    }

    # Convert the data dictionary to a JSON string
    json_data = json.dumps(data)

    # Set the headers to indicate that we are sending JSON
    headers = {"Content-Type": "application/json"}

    # Make the POST request
    requests.post(url, data=json_data, headers=headers)


# send movement
def sendMovement(cameraId, trackedTime):
    url = "https://elderguardiansbackend.azurewebsites.net/api/movements"

    # JSON data to be sent in the POST request
    data = {
        "cameraId": cameraId,
        "trackedTime": trackedTime
    }
    print(data)
    # Convert the data dictionary to a JSON string
    json_data = json.dumps(data)

    # Set the headers to indicate that we are sending JSON
    headers = {"Content-Type": "application/json"}

    # Make the POST request
    requests.post(url, data=json_data, headers=headers)
def setSendMovementBool():
    global send_movement_boolean 
    send_movement_boolean = True
schedule.every().day.at("23:59").do(setSendMovementBool)


# === PROGRAM === #
while cap.isOpened():
    schedule.run_pending()
    
    _, frame = cap.read()
    frame = cv2.resize(frame, (1920, 1080))

    if fall_detected:
        buffer_amount = 200
        if len(buffer_array) >= buffer_amount:
            createVideo(buffer_array)
            threading.Thread(target=sendVideo, args=(videoTitle,)).start()
            
            buffer_array = []
            buffer_amount = 100
            fall_detected = False
        else:
            buffer_array.append(frame)

    else:
        if len(buffer_array) >= buffer_amount:
            buffer_array.pop(0)
            buffer_array.append(frame)
        else:
            buffer_array.append(frame)

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pose_results = pose.process(frame_rgb)

    try:
        mp_drawing.draw_landmarks(
            frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS
        )

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

        y_center_top = (y_left_shoulder + y_right_shoulder) / 2
        y_center_bottom = (y_left_hip + y_right_hip) / 2
        average_height = y_center_bottom - y_center_top
        distanceToLaptop = -(math.log(968) - math.log(average_height)) / -0.314
        threshold_height = 800 - (20 * distanceToLaptop - 20)

        x_center_top = (x_left_shoulder + x_right_shoulder) / 2
        x_center_bottom = (x_left_hip + x_right_hip) / 2
        x_average_position = (x_center_top + x_center_bottom) / 2

        def calculate_instantaneous_velocity(
            previous_position, current_position, previous_time, current_time
        ):
            delta_position = current_position - previous_position
            delta_time = current_time - previous_time

            if delta_time == 0:
                return np.zeros_like(delta_position)
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

    # monitor status
    if -200 < current_y_velocity < 200:
        current_y_velocity = 0
    if y_nose > threshold_height and current_y_velocity > 1000:
        status = "!FALL DETECTED - ALERT SEND!"
        fall_detected = True
        current_datetime = datetime.fromtimestamp(
            math.floor(current_timestamp)
        ).strftime("%Y%m%d%H%M%S")
        datetime_object = datetime.strptime(current_datetime, "%Y%m%d%H%M%S")
        formatted_datetime = [
            datetime_object.year,
            datetime_object.month,
            datetime_object.day,
            datetime_object.hour,
            datetime_object.minute,
            datetime_object.second,
            datetime_object.microsecond // 1000,  # Convert microsecond to millisecond
        ]
        videoTitle = f"{patient_name}_{camera_id}_{current_datetime}.mp4"

        

    if status == "!FALL DETECTED - ALERT SEND!" and y_nose < threshold_height:
        status = "RECOVERED FROM FALL"
        fall_detected = False
        buffer_array = []
        buffer_amount = 100

    if -100 < current_x_velocity < 100:
        current_x_velocity = 0
    if current_x_velocity != 0 and x_average_position != previous_x_hip:
        movement_counter += 1

    if y_nose == previous_y_nose and current_y_velocity != 0:  # adjust sensitivity
        status = "!OCCLUDED FALL DETECTED!"
        fall_detected = True
        current_datetime = datetime.fromtimestamp(
            math.floor(current_timestamp)
        ).strftime("%Y%m%d%H%M%S")
        datetime_object = datetime.strptime(current_datetime, "%Y%m%d%H%M%S")
        formatted_datetime = [
            datetime_object.year,
            datetime_object.month,
            datetime_object.day,
            datetime_object.hour,
            datetime_object.minute,
            datetime_object.second,
            datetime_object.microsecond // 1000,  # Convert microsecond to millisecond
        ]
        videoTitle = f"{patient_name}_{camera_id}_{current_datetime}.mp4"

        


    if status == "!OCCLUDED FALL DETECTED!" and y_nose != previous_y_nose:
        status = "RECOVERED FROM OCCLUDED FALL"
        fall_detected = False
        buffer_array = []
        buffer_amount = 100 

    # calculate fps (use for correcting movement tracking count)
    fps_frame_count += 1
    if time.time() - fps_start_time >= 1:
        fps = fps_frame_count / (time.time() - fps_start_time)
        fps_start_time = time.time()
        fps_frame_count = 0

    # show status in top left corner
    cv2.putText(
        frame,
        f"{formatted_datetime}",
        (20, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        5,
    )

    # show length of buffer array
    cv2.putText(
        frame,
        f"BufLen: {len(buffer_array)}",
        (20, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (255, 255, 255),
        5,
    )

    # show fps
    cv2.putText(
        frame,
        f"FPS: {math.floor(fps)}",
        (20, 300),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (0, 255, 0),
        5,
    )

    # movement time in sec
    cv2.putText(
        frame,
        f"Time moving: {tracked_time} s",
        (20, 400),
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

    # output frame to show video
    cv2.imshow("Output", frame)

    if(send_movement_boolean == True):
        threading.Thread(target=(sendMovement), args =(camera_id,tracked_time)).start()
        
        send_movement_boolean = False
    # update previous variables
    previous_y_nose = y_nose
    previous_x_hip = x_average_position
    previous_timestamp = current_timestamp
    previous_frame_counter = frame_counter
    frame_counter += 1
    tracked_time = math.floor(movement_counter / 30)
    # cancel program on q pressed
    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
