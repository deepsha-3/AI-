import numpy as np
import cv2
from tensorflow.keras.models import load_model

# Load trained model
model = load_model("plant_disease_model.h5")

# Classes (same order as dataset folders)
classes = [
    "Potato_Early_blight",
    "Potato_Healthy",
    "Tomato_Bacterial_spot",
    "Tomato_Healthy"
]

# Load image
image_path = "leaf.jpg"

img = cv2.imread(image_path)
img = cv2.resize(img,(128,128))
img = img / 255.0
img = np.reshape(img,(1,128,128,3))

# Prediction
prediction = model.predict(img)
class_index = np.argmax(prediction)

print("Predicted Disease:", classes[class_index])