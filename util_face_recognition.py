import cv2 as cv
import numpy as np
import os
from glob import glob
from keras.models import load_model
from keras_vggface.utils import preprocess_input
from PIL import Image

# Model filename
modelName = 'VGGFace'
MODEL_NAME = 'static/models/face_recognition/' + modelName + '.h5'

# Constants
face_cascade = cv.CascadeClassifier('static/models/haar_cascade/haarcascade_frontalface_default.xml')

BW_THRESHOLD = 80
CONFIDENCE_THRESHOLD = 0.8
IMAGE_SIZE = (224, 224)

# Paths
cwd = os.getcwd()
print("Current wd: {0}".format(cwd))

# Detect face
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

# Recognize face
def face_recognition():
    cap = cv.VideoCapture(0)

    model = load_model(MODEL_NAME)

    classes = scan_folder()
    while True:
        ret, frame = cap.read()
        frame = cv.flip(frame,1)

        face = face_extractor(frame)
        if face is not None and type(face) is np.ndarray:
            face = cv.resize(face, IMAGE_SIZE)
            img = Image.fromarray(face, 'RGB')
            img_array = np.array(img)
            img_array = img_array.astype('float32')
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array, version=1)

            predict = model.predict(img_array)
            name = "unknown"

            print(predict[0])
            max_value = max(predict[0])
            if(max_value > CONFIDENCE_THRESHOLD):
                max_index = np.argmax(predict[0])
                name = str(classes[max_index])
                max_percent = "{:.1f}".format(max_value*100)
                if(name != "unknown"):
                    cv.putText(frame, str(max_percent), (50, 80), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 128, 0), 2, cv.LINE_AA)

            cv.putText(frame, name, (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 128, 0), 2, cv.LINE_AA)
        # No face detected
        else:
            cv.putText(frame, "unknown", (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 128, 0), 2, cv.LINE_AA)
        
        cv.imshow("Face Capture", frame)

        # Press Enter to exit
        if cv.waitKey(1) == 13:
            break

    cap.release()
    cv.destroyAllWindows()

# Scan folder to get class names
def scan_folder():
    folders = glob(os.path.join(cwd, 'static/faceImgs/unmasked/train', '*'))
    print("Current classes: " + str(len(folders)))
    names = [os.path.basename(folder) for folder in folders]
    return names

# Start face recognition process
face_recognition()