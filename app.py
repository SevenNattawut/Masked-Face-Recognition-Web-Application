# import flask web frameword libraries + SQL
import random
from flask import Flask, render_template, url_for, request, redirect, session, flash, jsonify, send_file, Response
from datetime import datetime, timedelta
from flask_login import UserMixin
from flask_socketio import SocketIO, emit
import pymysql

# import openCV2 library (real time face recognition)
import cv2 as cv
from glob import glob
from keras.models import load_model
from keras_vggface.utils import preprocess_input
from PIL import Image

# external functions (from Pavat's part)
from util_build_small_model import train

# import other libraries (i.e. numpy for mathematics canculation, base64 for converting image content to string, hashlib for password hashing, etc.)
import io
import zipfile
import json
import os
import base64
import numpy as np
import hashlib
import shutil
import threading

# create app object, with login session setup
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = "realtimemaskedfacerecog"

# connect to database (mysql)
conn = pymysql.connect(host = 'localhost', user = 'root', passwd = '', database = 'rmfr_db')

# socket
socketio = SocketIO(app)

# webapp routes
# index
@app.route("/")
def index():
    return render_template('index.html')

# about
@app.route("/about")
def about():
    return render_template('about.html')

#Live camera
@app.route("/liveCam")
def liveCam():
    global model_name

    pingDb()
    cur = conn.cursor()
    # fetch positions with id
    sql = "SELECT * FROM positions"
    cur.execute(sql)
    positions = cur.fetchall()
    # fetch departments with id
    sql = "SELECT * FROM departments"
    cur.execute(sql)
    departments = cur.fetchall()

    return render_template('rtfr.html', model_used = model_name, posList = positions, depList = departments)

# help
@app.route("/help")
def help():
    pingDb()
    cur = conn.cursor()
    cur.execute("SELECT * FROM question")
    result = cur.fetchall()
    return render_template('help.html', qna_list = result)

# login
@app.route("/login")
def login():
    pingDb()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM user_account WHERE is_admin = 1")
    result = cur.fetchone()[0]

    # check if there is any user exist in the database (for setup the web application and create the first user)
    # normal login page (there is at least 1 admin user in the database)
    if result != 0:
        return render_template('login.html')
    # there is no user in the database, go to setup page instead to create an admin account
    else:
        return redirect("/setup")

# create first user
@app.route("/setup")
def setUp():
    pingDb()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM user_account WHERE is_admin = 1")
    result = cur.fetchone()[0]

    # if the user try to 'illegally' enter by entering url, send them back to index page instead!
    if result != 0:
        return redirect('/')
    else:
        return render_template('setup.html')

# login submit
@app.route("/signin", methods=["GET", "POST"])
def signin():
    if(request.method == "POST"):
        femail = request.form["femail"]
        fpass = hashlib.sha256(request.form["fpass"].encode()).hexdigest()
        femail = "\'" + femail + "\'"
        
        pingDb()

        # create curser in database then perform query function
        cur = conn.cursor()
        cur.execute("SELECT user_account.id, user_account.pass_code, user_account.is_admin, user_info.first_name, user_info.email FROM user_account LEFT JOIN user_info ON user_account.id = user_info.id WHERE user_info.email = " + femail + "AND user_account.is_admin = 1")
        result = cur.fetchone()

        # correct password
        if result and fpass == result[1]:
            session["user"] = result[3]
            session["id"] = result[0]
            return redirect("/")
        # incorrect password
        elif result and fpass != result[1]:
            flash('Invalid email or password, or you are not allowed to login.   ', 'error')
            return redirect("/login")
        else:
            flash('Invalid email or password, or you are not allowed to login.   ', 'error')
            return redirect("/login")

# logout submit
@app.route("/signout")
def signout():
    session.pop("user", None)
    return redirect("/")

# user list
@app.route("/userList")
def userList():
    pingDb()
    cur = conn.cursor()
    sql = "SELECT user_account.id, user_account.is_admin, user_info.first_name, user_info.last_name, user_info.gender, user_info.birthday, user_info.email, positions.pos_name, departments.dep_name FROM user_account \
        LEFT JOIN user_info ON user_account.id = user_info.id \
        LEFT JOIN positions ON user_info.pos_id = positions.pos_id \
        LEFT JOIN departments ON user_info.dep_id = departments.dep_id"
    cur.execute(sql)
    result = cur.fetchall()
    result = sorted(result, key=lambda x: x[0])
    resultArray = []
    # transform a datetime to a prefered date time form
    for row in result:
        rowList = list(row)
        rowList[5] = rowList[5].strftime("%d/%m/%Y")
        resultArray.append(rowList)
    return render_template('userList.html', users = resultArray)

# open add new user page
@app.route("/newUser")
def userAdd():
    pingDb()
    cur = conn.cursor()
    # fetch positions with id
    sql = "SELECT * FROM positions"
    cur.execute(sql)
    positions = cur.fetchall()
    # fetch departments with id
    sql = "SELECT * FROM departments"
    cur.execute(sql)
    departments = cur.fetchall()
    return render_template('userAdd.html', posList = positions, depList = departments)

# add new user
@app.route("/addUser", methods=["GET", "POST"])
def addNewUser():
    if(request.method == "POST"):
        userID = request.args.get('commit_id')
        newFirstName = request.form["firstName"]
        newLastName = request.form["lastName"]
        newGender = request.form["gender"]
        newAdmin = 0
        if request.form["isAdmin"] == "True":
            newAdmin = 1
        else:
            newAdmin = 0
        birthday_str = request.form["birthday"]
        birthday = datetime.strptime(birthday_str, "%d/%m/%Y")
        newBd = birthday.strftime("%Y-%m-%d")
        newEmail = request.form["email"]
        newPasscode = ""
        if newAdmin == 1:
            newPasscode = hashlib.sha256(request.form["password"].encode()).hexdigest()
        newDep = request.form["department"]
        newPos = request.form["position"]
        newContact = request.form["contact"]
        newImgsData = json.loads(request.form["captured_data"])
        newMaskedImgsData = json.loads(request.form["masked_captured_data"])
        random.shuffle(newImgsData)
        random.shuffle(newMaskedImgsData)

        pingDb()
        cur = conn.cursor()

        # check if the email does not exist (The emails must be distinct from each other)
        sql = "SELECT user_info.email FROM user_info WHERE user_info.email = %s"
        cur.execute(sql, (newEmail,))
        conn.commit()
        result = cur.fetchone()
        if result is not None:
            # if email exists, go back to /newUser page and display flash message
            flash('Error: Email already exists.', 'error')
            return redirect("/newUser")

        # insert values into user_account table
        sql = "INSERT INTO user_account (pass_code, is_admin) VALUES (%s, %s)"
        values = (newPasscode, int(newAdmin))
        cur.execute(sql, values)

        # get the last id from user_account table (use to refer the recently added info in user_account)
        newId = cur.lastrowid
        # insert values into user_info table
        sql = "INSERT INTO user_info (id, first_name, last_name, gender, birthday, email, pos_id, dep_id, contacts) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = (newId, newFirstName, newLastName, newGender, newBd, newEmail, newPos, newDep, newContact)
        cur.execute(sql, values)

        # create image directory if it does not exist (the images will be divided into 70:30, 70 for training, and 30 for testing)
        os.makedirs(f"static/faceImgs/masked/train/{newId}")
        os.makedirs(f"static/faceImgs/masked/test/{newId}")
        for i, img in enumerate(newMaskedImgsData):
            # convert the base64 string to binary data
            decoded_img = base64.b64decode(img['image_base64'])
            # convert the binary data to a numpy array
            np_arr = np.frombuffer(decoded_img, np.uint8)
            img = cv.imdecode(np_arr, cv.IMREAD_UNCHANGED)
            # save the binary data to a file
            if i < 70:
                file_name = f"static/faceImgs/masked/train/{newId}/{i+1}.jpg"
            else:
                file_name = f"static/faceImgs/masked/test/{newId}/{i+1}.jpg"
            if not cv.imwrite(file_name, img):
                print("Could not save image")

        os.makedirs(f"static/faceImgs/unmasked/train/{newId}")
        os.makedirs(f"static/faceImgs/unmasked/test/{newId}")
        for i, img in enumerate(newImgsData):
            # convert the base64 string to binary data
            decoded_img = base64.b64decode(img['image_base64'])
            # convert the binary data to a numpy array
            np_arr = np.frombuffer(decoded_img, np.uint8)
            img = cv.imdecode(np_arr, cv.IMREAD_UNCHANGED)
            # save the binary data to a file
            if i < 70:
                file_name = f"static/faceImgs/unmasked/train/{newId}/{i+1}.jpg"
            else:
                file_name = f"static/faceImgs/unmasked/test/{newId}/{i+1}.jpg"
            if not cv.imwrite(file_name, img):
                print("Could not save image")
        
        sql = "INSERT INTO user_images (id, last_update) VALUES (%s, %s)"
        currentTime = datetime.now()
        values = (newId, currentTime)
        cur.execute(sql, values)

        # commit the changes to the database, then create commit log
        try:
            conn.commit()
        finally:
            # Define the data dictionary
            data = {
                "type": "ADD",
                "target": newId
            }

            # Convert the dictionary to a JSON string
            json_data = json.dumps(data)

            # Insert the JSON string into the database
            sql = "INSERT INTO commit_log (commit_id, action) VALUES (%s, %s)"
            values = (userID, json_data)
            cur.execute(sql, values)
            conn.commit()

    return redirect("/userList")

# video object reference (prevent duplicated camera object error when switching page)
cap = None

# Face collector part
# capture images mode trigger
@app.route("/start_capture", methods=["POST"])
def start_capture():
    global capture
    capture = True
    return jsonify({"message": "Capture started"})

@app.route("/stop_capture", methods=["POST"])
def stop_capture():
    global capture
    capture = False
    return jsonify({"message": "Capture stopped"})

# live video feed (on user add/edit pages)
@app.route('/video_feed')
@app.route('/editUser/<int:user_id>/video_feed')
def video_feed():
    return Response(live_camera(), mimetype='multipart/x-mixed-replace; boundary=frame')

# release video (use when unloading the camera page)
@app.route('/release_camera')
def release_camera(methods=["GET"]):
    if request.method == "GET":
        global cap
        if cap is not None:
            cap.release()
            cap = None

# face detector models
face_cascade = cv.CascadeClassifier('static/models/haar_cascade/haarcascade_frontalface_default.xml')
# mouth_cascade = cv.CascadeClassifier('static/models/haar_cascade/haarcascade_mcs_mouth.xml')

# capture video from the server
# client-based method has a performance issue (occaionally laggy video, and face detector algorithms (both opencv.js and face-api.js) not working properly)
@app.route("/captureFace")
def live_camera():
    # Enable capture process
    global capture
    global cap
    capture = False
    # Store value
    count = 0
    face_images = []

    # Lighting threshold
    bw_threshold = 80

    # Read video
    cap = cv.VideoCapture(0)

    width = 1152
    height = 648
    cap.set(cv.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, height)

    # Display webcam video
    while True:
        # Get individual frame
        ret, img = cap.read()
        img = cv.flip(img,1)
        if capture == False:
            # Concat frame one by one and show result
            cv.putText(img, "NO CAPTURE", (50, 50), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            # transform frame to binary and send to web page
            buffer = cv.imencode('.jpg', img)[1]
        # Start to capture
        else:
            # Convert Image into gray
            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

            # Convert image in black and white
            (thresh, black_and_white) = cv.threshold(gray, bw_threshold, 255, cv.THRESH_BINARY)

            # Detect face
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            # Face prediction for black and white
            faces_bw = face_cascade.detectMultiScale(black_and_white, 1.1, 4)

            # Case 1a: Face not detected
            if(len(faces) == 0 and len(faces_bw) == 0):
                pass

            # Case 1b: Face not detected (actually wearing white mask)
            elif(len(faces) == 0 and len(faces_bw) == 1):
                # It has been observed that for white mask covering mouth, with gray image face prediction is not happening
                pass

            # Case 2: Face detected
            else:
                # Save face images
                face_images_send = []
                detected = None
                for (x, y, w, h) in faces:
                    if w > 130:
                        x -= 10
                        y -= 10
                        detected = img[y:y+h+50, x:x+w+50]

                if detected is not None:
                    count += 1
                    detected = cv.resize(detected, (400, 400))

                    file_name = str(count) + ".jpg"
                    image = cv.imencode('.jpg', detected)[1]
                    image_base64 = base64.b64encode(image).decode('utf-8')
                    face_images.append({"file_name": file_name, "image_base64": image_base64})

            # Show frame with results
            cv.putText(img, "NOW CAPTURING: " + str(count) + "/100", (50, 50), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            # Having collected 100 images
            if count >= 100 or capture == False:
                if count >= 100:
                    random.shuffle(face_images)
                    face_images_send = face_images
                    capture = False
                    socketio.emit('face_data', json.dumps(face_images_send))
                    # Store value
                face_images = []
                face_images_send = []
                count = 0
            buffer = cv.imencode('.jpg', img)[1]
        frame = buffer.tobytes()

        # yield/return the current frame to the web page
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# face recognition part
# Constants
BW_THRESHOLD = 80
# using mask
CONFIDENCE_THRESHOLD = 0.8
# cropped image size
IMAGE_SIZE = (224, 224)

# model name
model_name = 'VGG16'
model_dir = 'static/models/face_recognition/' + model_name + '.h5'

@app.route("/changeModel", methods=["POST"])
def changeModel():
    if request.method == "POST":
        global model_name
        data = request.get_json()
        model_name = data['model']
        print(model_name)
        return jsonify({"model_name": model_name})

# video feed for face recognition page
@app.route('/video_feed_recog')
def video_feed_recog():
    return Response(face_recognition(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Detect and crop face area
def face_extractor(img):
    cropped_face = None
    gray_scale = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    (thresh, black_and_white) = cv.threshold(gray_scale, BW_THRESHOLD, 255, cv.THRESH_BINARY)

    faces = face_cascade.detectMultiScale(gray_scale, 1.1, 4)
    faces_bw = face_cascade.detectMultiScale(black_and_white, 1.1, 4)

    # No face detected
    if (len(faces) == 0 and len(faces_bw) == 0):
        return None

    elif(len(faces) == 0 and len(faces_bw) == 1):
        return None
    
    # Face detected
    else:
        for (x,y,w,h) in faces:
            if w > 130:
                x -= 10
                y -= 10
                cv.rectangle(img, (x,y), (x+w,y+h), (255,255,255), 2)
                cropped_face = img[y:y+h, x:x+w]
        return cropped_face

# stores the information of recently detected user
recently_detected_user = {}
# stores a list of detected user (it will be in the list for 1 hour as long as the video page is online)
detected_users = {}

# Recognize face (similar to live camera, but it needs different parameter setting and some additional functions)
@app.route("/faceRecog")
def face_recognition():

    global recently_detected_user
    global detected_users
    global model_dir
    global cap

    recently_detected_user = {}
    detected_users = {}

    cap = cv.VideoCapture(0)

    # width = 864
    # height = 486
    # cap.set(cv.CAP_PROP_FRAME_WIDTH, width)
    # cap.set(cv.CAP_PROP_FRAME_HEIGHT, height)

    model = load_model(model_dir)
    # print(f"\nModel selected: {model}\n")

    # create a cursor to execute the query
    cur = conn.cursor()
    
    pingDb()
    # Retrieve the id, full name, position id, and department id
    sql = "SELECT u.id, u.first_name, u.last_name, p.pos_name as pos_name, d.dep_name as dep_name \
        FROM user_info u \
        INNER JOIN positions p ON u.pos_id = p.pos_id \
        INNER JOIN departments d ON u.dep_id = d.dep_id \
        ORDER BY u.id ASC"
    cur.execute(sql)
    result = cur.fetchall()
    
    # list of id, full name, pos, dep (after fectching from database, it was tuple, so we modify the content and change its datatype to list)
    user_list = list(tuple([row[0], f"{row[1]} {row[2]}", row[3], row[4]] for row in result))

    while True:
        ret, frame = cap.read()
        frame = cv.flip(frame,1)
        try:
            face = face_extractor(frame)
        except:
            # No face detected
            cv.putText(frame, "Unknown", (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 128, 0), 2, cv.LINE_AA)
        else:
            if face is not None and type(face) is np.ndarray:
                id = 0
                face = cv.resize(face, IMAGE_SIZE)
                img = Image.fromarray(face, 'RGB')
                img_array = np.array(img)
                # float32 image content type for more precise face image comparison than base64
                img_array = img_array.astype('float32')
                img_array = np.expand_dims(img_array, axis=0)
                img_array = preprocess_input(img_array, version=1)

                predict = model.predict(img_array)
                name = "Unknown"

                max_value = max(predict[0])
                if(max_value > CONFIDENCE_THRESHOLD):
                    max_index = np.argmax(predict[0])
                    name = str(user_list[max_index][1])
                    id = user_list[max_index][0]
                    max_percent = "{:.1f}".format(max_value*100)
                    # detect recognized face
                    if(name != "Unknown"):
                        cv.putText(frame, str(max_percent), (50, 80), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 128, 0), 2, cv.LINE_AA)

                # put name and add the user timeline
                cv.putText(frame, name, (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 128, 0), 2, cv.LINE_AA)
                current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                # The detected user hasn't been in the detected list for a while (1 hour), record to the timeline
                if id not in detected_users or detected_users[id] is None:
                    detected_users[id] = current_time
                    
                    # resize cropped detect face image and save in a recently detected user information
                    image = cv.imencode('.jpg', face)[1]
                    image_base64 = base64.b64encode(image).decode('utf-8')
                    
                    # if id is more then 0 = fround detected user, else, it is unknown user
                    if id > 0:
                        recently_detected_user = {
                            "id" : id,
                            "name" : name,
                            "timestamp" : current_time,
                            "position" : str(user_list[max_index][2]),
                            "department" : str(user_list[max_index][3]),
                            "base64": image_base64
                        }
                        data = {
                        "id": id,
                        "name": name,
                        "position" : str(user_list[max_index][2]),
                        "department" : str(user_list[max_index][3])
                        }
                    else:
                        recently_detected_user = {
                            "id" : "UNKNOWN",
                            "name" : "UNKNOWN",
                            "timestamp" : current_time,
                            "position" : "UNKNOWN",
                            "department" : "UNKNOWN",
                            "base64": image_base64
                        }
                        data = {
                        "id": "UNKNOWN",
                        "name": "UNKNOWN",
                        "position" : "UNKNOWN",
                        "department" : "UNKNOWN"
                        }

                    pingDb()
                    sql = "INSERT INTO weekly_timestamp (detected_user) VALUES (%s)"
                    json_data = json.dumps(data)
                    cur.execute(sql, json_data)
                    conn.commit()

                    pingDb()
                    # Get the current auto-increment value
                    cur.execute("SELECT MAX(id) FROM weekly_timestamp")
                    result = cur.fetchone()
                    auto_increment = result[0]

                    # save the binary data to a file
                    file_name = f"static/detectedFaces/{str(auto_increment)}.jpg"
                    if not cv.imwrite(file_name, face):
                        print("Could not save image")

                # more than 1 minute after last appearance, delete the detected user timestamp from dictionary
                # P.S. the user record will be created in the next frame
                if datetime.now() - datetime.strptime(detected_users[id], "%d/%m/%Y %H:%M:%S") > timedelta(hours=1):
                    del detected_users[id]
            else:
                # No face detected
                cv.putText(frame, "Unknown", (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 128, 0), 2, cv.LINE_AA)
        
        buffer = cv.imencode('.jpg', frame)[1]
        # transform frame to binary and send to web page
        fbyte = buffer.tobytes()
        # yield/return the current frame to the web page
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + fbyte + b'\r\n')

# echo back to client that connection is ok
@socketio.on('connect')
def on_connect():
    return jsonify({"status": "Success"})

# send the recently detected user to a client
@socketio.on('recentInfo')
def on_recent_info():
    global recently_detected_user
    if recently_detected_user != {}:
        socketio.emit('recentInfo', json.dumps(recently_detected_user))
        return jsonify({"status": "Success"})
    else:
        return jsonify({"status": "Unsuccess"})

# open edit page of the selected user
@app.route("/editUser/<user_id>", methods=["GET", "POST"])
def editInfo(user_id):
    # create a cursor to execute the query
    cur = conn.cursor()
    
    pingDb()
    # Retrieve the user's information from the database based on the user ID
    sql = "SELECT user_info.first_name, user_info.last_name, user_info.gender, user_info.birthday, user_info.email, user_account.pass_code, user_info.pos_id, user_info.dep_id, user_info.contacts, user_account.is_admin FROM user_info \
        JOIN user_account ON user_account.id = user_info.id \
        WHERE user_info.id = %s"
    cur.execute(sql, (user_id,))
    result = cur.fetchone()
    if result is None:
        return jsonify({"error": "No user found with the given ID"}), 404
    user = {
        "first_name": result[0],
        "last_name": result[1],
        "gender": result[2],
        "birthday": result[3].strftime("%d/%m/%Y"),
        "email": result[4],
        "pass_code": result[5],
        "pos_id": result[6],
        "dep_id": result[7],
        "contacts": result[8],
        "is_admin": result[9]
    }

    # fetch positions with id
    sql = "SELECT * FROM positions"
    cur.execute(sql)
    positions = cur.fetchall()
    # fetch departments with id
    sql = "SELECT * FROM departments"
    cur.execute(sql)
    departments = cur.fetchall()
    
    # check if the user was found
    if not user:
        return "User not found", 404
    return render_template("userEdit.html", user = user, user_id = user_id, posList = positions, depList = departments)

# update the data of the selected user (must have POST method from the form, cannot directly type in URL)
@app.route("/confirmEdit/<user_id>", methods=["GET", "POST"])
def updateInfo(user_id):
    if request.method == "POST":
        userID = request.args.get('commit_id')
        editFirstName = request.form["firstName"]
        editLastName = request.form["lastName"]
        editGender = request.form["gender"]
        editAdmin = 0
        if request.form["isAdmin"] == "True" and len(request.form["password"]) > 0:
            editAdmin = 1
            editPasscode = hashlib.sha256(request.form["password"].encode()).hexdigest()
        else:
            editAdmin = 0
            editPasscode = ""
        birthday_str = request.form["birthday"]
        birthday = 0
        editBd = ""
        if len(birthday_str) > 0:
            birthday = datetime.strptime(birthday_str, "%d/%m/%Y")
            editBd = birthday.strftime("%Y-%m-%d")
        editEmail = request.form["email"]
        editDep = request.form["department"]
        editPos = request.form["position"]
        editContact = request.form["contact"]
        editImgs_str = request.form["captured_data"]
        editMaskedImgs_str = request.form["masked_captured_data"]
        updateImg = False
        updateMaskedImg = False

        update_info = False

        sql = ""
        values = ()

        if len(editImgs_str) > 0:
            editImgs = json.loads(editImgs_str)
            updateImg = True
        if len(editMaskedImgs_str) > 0:
            editMaskedImgs = json.loads(editMaskedImgs_str)
            updateMaskedImg = True
        pingDb()
        cur = conn.cursor()

        # check if the email does not exist in different account
        if len(editEmail) > 0:
            sql = "SELECT email FROM user_info WHERE user_info.email = %s AND user_info.id <> %s"
            values = (editEmail, int(user_id))
            cur.execute(sql, values)
            result = cur.fetchone()
            if result is not None:
                # if email exists, go back to /editUser page and display flash message
                flash('Error: Email already exists in another account.', 'error')
                return redirect("/editUser/{}".format(user_id))

        # update values in user_account table
        
        sql = "UPDATE user_account SET is_admin=%s"
        values = (int(editAdmin),)
        # if admin update their password
        if editAdmin == 1 and len(editPasscode) > 0:
            sql += ", pass_code=%s"
            values += (editPasscode,)
        # if the user isn't admin (either non admin in the first place, or is no longer an admin) -> password = ""
        elif editAdmin == 0:
            sql += ", pass_code=%s"
            values += (editPasscode,)
        sql += " WHERE id=%s"
        values += (user_id,)
        cur.execute(sql, values)

        values = ()
        # update values in user_info table
        sql = "UPDATE user_info SET"
        if len(editFirstName) > 0:
            sql += " first_name=%s,"
            values += (editFirstName,)
            update_info = True
        if len(editLastName) > 0:
            sql += " last_name=%s,"
            values += (editLastName,)
            update_info = True
        if len(editGender) > 0:
            sql += " gender=%s,"
            values += (editGender,)
            update_info = True
        if len(birthday_str) > 0:
            sql += " birthday=%s,"
            values += (editBd,)
            update_info = True
        if len(editEmail) > 0:
            sql += " email=%s,"
            values += (editEmail,)
            update_info = True
        if len(editPos) > 0:
            sql += " pos_id=%s,"
            values += (editPos,)
            update_info = True
        if len(editDep) > 0:
            sql += " dep_id=%s,"
            values += (editDep,)
            update_info = True
        if len(editContact) > 0:
            sql += " contacts=%s,"
            values += (editContact,)
            update_info = True
        
        sql = sql.rstrip(',') + " WHERE id=%s"
        values += (user_id,)

        if update_info == True:
            cur.execute(sql, values)
        
        # update images here
        if updateImg == True and updateMaskedImg == True:
            # update image taken datetime
            currentTime = datetime.now()
            sql = "UPDATE user_images SET last_update=%s WHERE id=%s"
            values = (currentTime, user_id)
            cur.execute(sql, values)

            for i, img in enumerate(editImgs):
                # convert the base64 string to binary data
                decoded_img = base64.b64decode(img['image_base64'])
                # convert the binary data to a numpy array
                np_arr = np.frombuffer(decoded_img, np.uint8)
                img = cv.imdecode(np_arr, cv.IMREAD_UNCHANGED)
                # save the binary data to a file
                if i < 70:
                    file_name = f"static/faceImgs/unmasked/train/{user_id}/{i+1}.jpg"
                else:
                    file_name = f"static/faceImgs/unmasked/test/{user_id}/{i+1}.jpg"
                if not cv.imwrite(file_name, img):
                    print("Could not save image")

            for i, img in enumerate(editMaskedImgs):
                # convert the base64 string to binary data
                decoded_img = base64.b64decode(img['image_base64'])
                # convert the binary data to a numpy array
                np_arr = np.frombuffer(decoded_img, np.uint8)
                img = cv.imdecode(np_arr, cv.IMREAD_UNCHANGED)
                # save the binary data to a file
                if i < 70:
                    file_name = f"static/faceImgs/masked/train/{user_id}/{i+1}.jpg"
                else:
                    file_name = f"static/faceImgs/masked/test/{user_id}/{i+1}.jpg"
                if not cv.imwrite(file_name, img):
                    print("Could not save image")

        # commit the changes to the database, then create commit log
        try:
            conn.commit()
        finally:
            # Define the data dictionary
            data = {
                "type": "EDIT",
                "target": user_id
            }

            # Convert the dictionary to a JSON string
            json_data = json.dumps(data)

            # Insert the JSON string into the database
            sql = "INSERT INTO commit_log (commit_id, action) VALUES (%s, %s)"
            values = (userID, json_data)
            cur.execute(sql, values)
            conn.commit()

    return redirect("/userList")

# delete the selected user information and images
@app.route("/confirmDel/<user_id>", methods=["GET", "POST"])
def delUser(user_id):
    if request.method == "POST":
        userID = request.json.get('commit_id')
        pingDb()
        cur = conn.cursor()

        # get the name and email before delete (to record in commit log)
        sql = "SELECT email, first_name, last_name FROM user_info WHERE user_info.id = %s"
        values = (user_id,)
        cur.execute(sql, values)
        conn.commit()
        result = cur.fetchone()
        delEmail = result[0]
        delFirstName = result[1]
        delLastName = result[2]

        # delete user in user_info table
        sql = "DELETE FROM user_info WHERE id=%s;"
        values = (user_id,)
        cur.execute(sql, values)

        # delete user in user_info table
        sql = "DELETE FROM user_images WHERE id=%s;"
        values = (user_id,)
        cur.execute(sql, values)

        # delete user in user_account table
        sql = "DELETE FROM user_account WHERE id=%s;"
        values = (user_id,)
        cur.execute(sql, values)

        # commit the changes to the database, then create commit log
        try:
            conn.commit()
        finally:
            # Define the data dictionary
            data = {
                "type": "DELETE",
                "target": user_id
            }

            # Convert the dictionary to a JSON string
            json_data = json.dumps(data)

            # Insert the JSON string into the database
            sql = "INSERT INTO commit_log (commit_id, action) VALUES (%s, %s)"
            values = (userID, json_data)
            cur.execute(sql, values)
            conn.commit()

        # delete user's images directory
        masked_train_path = os.path.join("static", "faceImgs", "masked", "train", user_id)
        unmasked_train_path = os.path.join("static", "faceImgs", "unmasked", "train", user_id)
        masked_test_path = os.path.join("static", "faceImgs", "masked", "test", user_id)
        unmasked_test_path = os.path.join("static", "faceImgs", "unmasked", "test", user_id)

        if os.path.exists(masked_train_path):
            shutil.rmtree(masked_train_path)
        if os.path.exists(unmasked_train_path):
            shutil.rmtree(unmasked_train_path)
        if os.path.exists(masked_test_path):
            shutil.rmtree(masked_test_path)
        if os.path.exists(unmasked_test_path):
            shutil.rmtree(unmasked_test_path)

    return redirect("/userList")

# timeline 
@app.route("/timeline")
def timeline():
    pingDb()
    # create curser in database then perform query function
    cur = conn.cursor()
    cur.execute("SELECT * FROM weekly_timestamp")
    result = cur.fetchall()
    # sort the date-time (ascending order)
    result = sorted(result, key=lambda x: x[0])
    resultArray = []
    # transform a datetime to a prefered date time form
    for row in result:
        rowList = list(row)
        rowList[1] = rowList[1].strftime("%d/%m/%Y %X")
        # extract user data from json string > json > separate ID and name
        rowList[2] = json.loads(rowList[2])
        resultArray.append(rowList)
    return render_template('timeline.html', timelineList = resultArray)

train_status = False
training_thread = None
# code from Pavat (model training and face recognition)
# train the model
@app.route("/trainModel", methods=["GET", "POST"])
def trainModel():
    global train_status
    global training_thread
    if request.method == "POST":
        # Check if train is running
        if train_status == True:
            return jsonify({"message": "Model is training"})
        else:
            pingDb()
            cur = conn.cursor()
            userID = request.json.get('commit_id')
            # Define the data dictionary
            data = {
                "type": "TRAIN",
            }
            # Convert the dictionary to a JSON string
            json_data = json.dumps(data)

            # Insert the JSON string into the database
            sql = "INSERT INTO commit_log (commit_id, action) VALUES (%s, %s)"
            values = (userID, json_data)
            cur.execute(sql, values)
            conn.commit()
            # Start training in a separate thread, so the application can run normally while the model is being trained
            training_thread = threading.Thread(target=trainInBg)
            training_thread.start()
            return jsonify({"message": "Model training is started."})

# Train function with status update (train 3 models in another threat), not sure if I can run three of them at once in 3 separated threats
def trainInBg():
    global train_status
    global training_thread
    train_status = True
    train("VGG16")
    train("VGGFace")
    train("IncepResNet")
    train_status = False
    print("Training done!")
    
    # Join the trainThread to close it
    if training_thread is not None and training_thread != threading.current_thread():
        training_thread.join()
        training_thread = None


@app.route("/getLog", methods=["GET"])
def getCommitLog():
    cur = conn.cursor()
    pingDb()

    # query log data from database
    sql = "SELECT * FROM commit_log ORDER BY id DESC"
    cur.execute(sql)
    result = cur.fetchall()

    # query user data from database
    sql = "SELECT id, first_name, last_name FROM user_info ORDER BY id ASC"
    cur.execute(sql)
    userData = cur.fetchall()

    # create a dictionary to map user IDs to names
    userMap = {user[0]: f"{user[1]} {user[2]} ({user[0]})" for user in userData}

    # create a new list with the modified items and replace the tuple in the result list
    newResult = []
    for item in result:
        # replace committer ID with name
        committerID = item[1]
        committerName = userMap.get(int(committerID), committerID)

        # replace target ID with name
        data = json.loads(item[3])
        targetID = data.get("target")
        if targetID:
            targetName = userMap.get(int(targetID), f"Deleted User ({targetID})")
            data["target"] = targetName

        newItem = list(item)
        newItem[1] = committerName
        newItem[3] = json.dumps(data)
        newResult.append(newItem)

    # return new result as JSON
    return jsonify(newResult)

# dataManagement 
@app.route("/dataManage")
def dataManage():
    pingDb()
    # create curser in database then perform query function
    cur = conn.cursor()
    cur.execute("SELECT * FROM positions")
    positions = cur.fetchall()

    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()

    cur.execute("SELECT * FROM question")
    questions = cur.fetchall()

    return render_template('option.html', posList = positions, depList = departments, qnaList = questions)

# add new pos
@app.route("/addPos", methods=["GET", "POST"])
def addPos():
    if request.method == "POST":
        userID = request.args.get('commit_id')
        pingDb()
        # create curser in database then perform query function
        cur = conn.cursor()

        sql = "INSERT INTO positions (pos_name) VALUES (%s)"
        value = (request.form["newPosName"],)
        cur.execute(sql, value)

        # Define the data dictionary
        data = {
            "type": "ADD_POS",
        }
        # Convert the dictionary to a JSON string
        json_data = json.dumps(data)

        # Insert the JSON string into the database
        sql = "INSERT INTO commit_log (commit_id, action) VALUES (%s, %s)"
        values = (userID, json_data)
        cur.execute(sql, values)
        conn.commit()
    return redirect("/dataManage")

# edit pos
@app.route("/editPos", methods=["POST"])
def editPos():
    if request.method == "POST":
        userID = request.args.get('commit_id')
        pingDb()
        # create curser in database then perform query function
        cur = conn.cursor()

        sql = "UPDATE positions SET pos_name = %s WHERE pos_id = %s"
        value = (request.form["editPosName"], request.form["position"])
        cur.execute(sql, value)

        # Define the data dictionary
        data = {
            "type": "EDIT_POS",
        }
        # Convert the dictionary to a JSON string
        json_data = json.dumps(data)

        # Insert the JSON string into the database
        sql = "INSERT INTO commit_log (commit_id, action) VALUES (%s, %s)"
        values = (userID, json_data)
        cur.execute(sql, values)
        conn.commit()
    return redirect("/dataManage")

# delete pos
@app.route("/delPos", methods=["POST"])
def delPos():
    if request.method == "POST":
        userID = request.args.get('commit_id')
        pingDb()
        # create curser in database then perform query function
        cur = conn.cursor()

        sql = "DELETE FROM positions WHERE pos_id = %s"
        value = (request.form["position"],)
        cur.execute(sql, value)

        # Define the data dictionary
        data = {
            "type": "DEL_POS",
        }
        # Convert the dictionary to a JSON string
        json_data = json.dumps(data)

        # Insert the JSON string into the database
        sql = "INSERT INTO commit_log (commit_id, action) VALUES (%s, %s)"
        values = (userID, json_data)
        cur.execute(sql, values)
        conn.commit()
    return redirect("/dataManage")

# add new dep
@app.route("/addDep", methods=["POST"])
def addDep():
    if request.method == "POST":
        userID = request.args.get('commit_id')
        pingDb()
        # create curser in database then perform query function
        cur = conn.cursor()

        sql = "INSERT INTO departments (dep_name) VALUES (%s)"
        value = (request.form["newDepName"],)
        cur.execute(sql, value)

        # Define the data dictionary
        data = {
            "type": "ADD_DEP",
        }
        # Convert the dictionary to a JSON string
        json_data = json.dumps(data)

        # Insert the JSON string into the database
        sql = "INSERT INTO commit_log (commit_id, action) VALUES (%s, %s)"
        values = (userID, json_data)
        cur.execute(sql, values)
        conn.commit()
    return redirect("/dataManage")

# edit dep
@app.route("/editDep", methods=["POST"])
def editDep():
    if request.method == "POST":
        userID = request.args.get('commit_id')
        pingDb()
        # create curser in database then perform query function
        cur = conn.cursor()

        sql = "UPDATE departments SET dep_name = %s WHERE dep_id = %s"
        value = (request.form["editDepName"], request.form["department"])
        cur.execute(sql, value)

        # Define the data dictionary
        data = {
            "type": "EDIT_DEP",
        }
        # Convert the dictionary to a JSON string
        json_data = json.dumps(data)

        # Insert the JSON string into the database
        sql = "INSERT INTO commit_log (commit_id, action) VALUES (%s, %s)"
        values = (userID, json_data)
        cur.execute(sql, values)
        conn.commit()
    return redirect("/dataManage")

# delete pos
@app.route("/delDep", methods=["POST"])
def delDep():
    if request.method == "POST":
        userID = request.args.get('commit_id')
        pingDb()
        # create curser in database then perform query function
        cur = conn.cursor()

        # UPDATE user_images SET last_update=%s WHERE id=%s
        sql = "DELETE FROM departments WHERE dep_id = %s"
        value = (request.form["department"],)
        cur.execute(sql, value)

        # Define the data dictionary
        data = {
            "type": "DEL_DEP",
        }
        # Convert the dictionary to a JSON string
        json_data = json.dumps(data)

        # Insert the JSON string into the database
        sql = "INSERT INTO commit_log (commit_id, action) VALUES (%s, %s)"
        values = (userID, json_data)
        cur.execute(sql, values)
        conn.commit()
    return redirect("/dataManage")

# add new qna
@app.route("/addQuestion", methods=["POST"])
def addQuestion():
    if request.method == "POST":
        userID = request.args.get('commit_id')
        pingDb()
        # create curser in database then perform query function
        cur = conn.cursor()

        sql = "INSERT INTO question (question, answer) VALUES (%s, %s)"
        value = (request.form["newQuestion"], request.form["newAnswer"])
        cur.execute(sql, value)

        # Define the data dictionary
        data = {
            "type": "ADD_QNA",
        }
        # Convert the dictionary to a JSON string
        json_data = json.dumps(data)

        # Insert the JSON string into the database
        sql = "INSERT INTO commit_log (commit_id, action) VALUES (%s, %s)"
        values = (userID, json_data)
        cur.execute(sql, values)
        conn.commit()
    return redirect("/dataManage")

# delete qna
@app.route("/delQuestion", methods=["POST"])
def delQuestion():
    if request.method == "POST":
        userID = request.args.get('commit_id')
        pingDb()
        # create curser in database then perform query function
        cur = conn.cursor()

        sql = "DELETE FROM question WHERE id = %s"
        value = (request.form["question"],)
        cur.execute(sql, value)

        # Define the data dictionary
        data = {
            "type": "DEL_QNA",
        }
        # Convert the dictionary to a JSON string
        json_data = json.dumps(data)

        # Insert the JSON string into the database
        sql = "INSERT INTO commit_log (commit_id, action) VALUES (%s, %s)"
        values = (userID, json_data)
        cur.execute(sql, values)
        conn.commit()
    return redirect("/dataManage")

# database catching issue fixer (disconnect and reconnect)
def pingDb():
    conn.close()
    conn.ping(reconnect=True)

# run the webapp
if __name__ == "__main__":
    app.run(debug = True)
    socketio.run(app)