# model training program
# created by Pavat Poonpinij
# modified by Nattawut Na Lumpoon (define a train() function to further use in the web application)
from tensorflow import keras
from keras.layers import Dense, Flatten
from keras.models import Model
from keras.applications.vgg16 import VGG16
from keras_vggface.vggface import VGGFace
from keras.applications.inception_resnet_v2 import InceptionResNetV2
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from glob import glob
# import matplotlib.pyplot as plt
import numpy as np
import timeit
import os

# Constants
RANDOM_SEED = 1
EPOCHS = 20
PATIENCE = 3
FOLDER_NAME = 'static/faceImgs/masked\\'

def train(modelName):
  # Paths
  cwd = os.getcwd()
  print("Current wd: {0}".format(cwd))

  # Change paths to where the datasets locate
  # Train set will be changed between unmasked/masked/mixed
  train_path = os.path.join(cwd, FOLDER_NAME, 'train')
  # Test set is always masked images
  test_path = os.path.join(cwd, FOLDER_NAME, 'test')

  # Check classes
  folders = glob(os.path.join(cwd, FOLDER_NAME, 'train', '*'))
  print("Current classes: " + str(len(folders)))
  names = [os.path.basename(folder) for folder in folders]
  print(names)

  # if change the model, comment 2 other unused models (use if statement to choose the model)

  # Create VGG16 model
  if modelName == "VGG16":
    vgg = VGG16(input_shape=(224,224,3), weights='imagenet', include_top=False)
    for layer in vgg.layers:
      layer.trainable = False  

    # Fine-tuning
    x = Flatten()(vgg.output)
    prediction = Dense(len(folders), activation='softmax')(x)
    model = Model(inputs=vgg.input, outputs=prediction)
    model.summary()

  # Create VGGFace model
  elif modelName == "VGGFace":
    vggface = VGGFace(model='vgg16')
    vgg_model = VGGFace(include_top=False, input_shape=(224, 224, 3), pooling='avg')
    for layer in vgg_model.layers:
        layer.trainable = False

    # Finetuning
    x = Flatten(name='flatten')(vgg_model.output)
    x = Dense(512, activation='relu', name='fc6')(x)
    x = Dense(512, activation='relu', name='fc7')(x)
    output = Dense(len(folders), activation='softmax', name='classifier')(x)
    model = Model(vgg_model.input,output)
    model.summary()

  # Create InceptionResNet model
  elif modelName == "IncepResNet":
    incep = InceptionResNetV2(input_shape=(224, 224, 3), include_top=False)
    for layer in incep.layers:
        layer.trainable = False

    # Finetuning
    x = Flatten()(incep.output)
    x = Dense(128, activation='relu')(x)
    prediction = Dense(len(folders), activation='softmax')(x)
    model = Model(incep.input, prediction)
    model.summary()

  # Reading images from train/test data
  train_datagen = ImageDataGenerator(rescale = 1./255, shear_range = 0.2, zoom_range = 0.2, 
                                    horizontal_flip = True, validation_split = 1/7)
  test_datagen = ImageDataGenerator(rescale = 1./255)

  # Train and validation set
  print("Preparing train/valid set")
  train_generator = train_datagen.flow_from_directory(train_path, target_size = (224, 224),
                                                  batch_size = 32, class_mode = 'categorical',
                                                  subset = 'training', seed = RANDOM_SEED)
  valid_generator = train_datagen.flow_from_directory(train_path, target_size = (224, 224),
                                              batch_size = 32, class_mode = 'categorical',
                                              shuffle = False, subset = 'validation', seed = RANDOM_SEED)
  # Test set
  print("Preparing test set")
  test_generator = test_datagen.flow_from_directory(test_path, target_size = (224, 224),
                                              batch_size = 32, class_mode = 'categorical',
                                              shuffle = False)

  # will change the model name to model type later
  checkpoint = ModelCheckpoint('static/models/face_recognition/' + modelName + '.h5', monitor='val_loss', mode='min', save_best_only=True, verbose=1)
  earlystop = EarlyStopping(monitor='val_loss', mode='min', patience=PATIENCE, restore_best_weights=True)

  # Keep track of elapsed time
  t_0 = timeit.default_timer()
  print("Start compiling and training the model")


  # if change the model, set here also

  # Compile the model
  # VGG16
  opt = keras.optimizers.Adam(learning_rate=0.0001)
  if modelName == "VGG16":
    model.compile(loss='categorical_crossentropy', optimizer=opt, metrics=['accuracy'])

  # VGGFace OR InceptionResNetV2
  elif modelName == "VGGFace" or modelName == "IncepResNet":
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

  r = model.fit(train_generator, validation_data=valid_generator, 
                epochs=EPOCHS, callbacks=[earlystop, checkpoint])

  # Total training time
  t_1 = timeit.default_timer()
  elpased_time = round((t_1 - t_0) / 60, 3)
  print(f"Elapsed time: {elpased_time} minutes")

  # Graphs
  # plt.plot(r.history['loss'], label='Train loss')
  # plt.plot(r.history['val_loss'], label='Valid loss')
  # plt.legend()
  # plt.savefig('small_loss.png')
  # plt.show()

  # plt.plot(r.history['accuracy'], label='Train acc')
  # plt.plot(r.history['val_accuracy'], label='Valid acc')
  # plt.legend()
  # plt.savefig('small_acc.png')
  # plt.show()

  # Performance evaluation using test set
  pred = model.predict(test_generator)
  pred = np.argmax(pred, axis=1)

  # Metrics
  accuracy = accuracy_score(test_generator.classes, pred)
  precision = precision_score(test_generator.classes, pred, average='weighted')
  recall = recall_score(test_generator.classes, pred, average='weighted')
  f1 = f1_score(test_generator.classes, pred, average='weighted')

  print('Accuracy: %f' % accuracy)
  print('Precision: %f' % precision)
  print('Recall: %f' % recall)
  print('F1 score: %f' % f1)