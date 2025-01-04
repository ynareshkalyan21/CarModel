# Created by yarramsettinaresh GORAKA DIGITAL PRIVATE LIMITED at 31/12/24
import numpy as np
import cv2
from tensorflow.keras.models import load_model

from config import MAJOR_PARTS_NO_DIRECTION
from positional_pattern_model import calculate_centroid, pad_sequence, pad_labels, pad_positions
from prepare_dataframe import process_via_dataset
from tensorflow.keras.utils import to_categorical
from keras.utils import custom_object_scope
import tensorflow as tf
from ultralytics import YOLO
image_shape = (640, 640)
# Load the YOLO model
yolo_model = YOLO("/Users/yarramsettinaresh/PycharmProjects/CarModel/yolo_model/carparts_poly3/weights/best.pt", )

# Load the classification model
# custom_objects = {"Cast":  tf.cast}

model = load_model("/Users/yarramsettinaresh/PycharmProjects/CarModel/model/car_parts_model.keras")
print(model.summary())

# Example input image for YOLO detection
image = cv2.imread("/Users/yarramsettinaresh/PycharmProjects/CarModel/_car_parts_poly_region_dataset/images/train/0EETD2gUOZ_1648015344105.jpg")
input_size = 640  # Typically 640x640
resized_image = cv2.resize(image, (input_size, input_size))
# Run YOLO prediction
yolo_results = yolo_model.predict(resized_image)

# Convert Masks object to NumPy arrays
masks_data = yolo_results[0].masks.data.cpu().numpy()  # Access and convert to NumPy array

def mask_to_polygons(mask):
    # Ensure the mask is binary
    binary_mask = (mask > 0.5).astype(np.uint8) * 255  # Convert to binary and scale to 8-bit
    _, binary_mask = cv2.threshold(binary_mask, 127, 255, cv2.THRESH_BINARY)

    # Find contours in the binary mask
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    polygons = []
    for contour in contours:
        # Approximate the contour to reduce the number of points
        epsilon = 0.01 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        # Convert the contour to a list of (x, y) coordinates
        polygon = approx.reshape(-1, 2)
        polygons.append(polygon)
    return polygons


# Calculate centroids for each mask
positions = []
for mask in masks_data:  # Iterate through NumPy masks
    polygons = mask_to_polygons(mask)
    for polygon in polygons:
        positions.append(calculate_centroid(polygon))

max_parts = 20
num_part_types = len(MAJOR_PARTS_NO_DIRECTION)
# Process the YOLO results (you may need to pad or resize masks, positions, and labels)
# input_masks = np.array([pad_sequence(masks_data, max_parts=20, height=640, width=640)])
# input_positions = np.array([pad_positions(positions, max_parts=20)])
# input_labels = np.array([pad_labels(yolo_results[0].boxes.numpy().cls.astype(int), max_parts=20, num_part_types=5)])
#
masks = pad_sequence([masks_data], 20, image_shape[0], image_shape[1])

# positions = [calculate_centroid(polygon) for polygon in polygons]
positions = pad_positions([np.array(positions)], max_parts)

one_hot_labels = [np.eye(num_part_types)[label] for label in yolo_results[0].boxes.numpy().cls.astype(int)]
one_hot_labels = pad_labels(one_hot_labels, max_parts, num_part_types)
# Predict the category using the position-based classification model
predictions = model.predict([masks, positions, one_hot_labels])

# Output the predicted category
predicted_category = np.argmax(predictions, axis=-1)
print(f'Predicted category index: {predicted_category}')
