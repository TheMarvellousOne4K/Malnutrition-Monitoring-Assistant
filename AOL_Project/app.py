from flask import Flask, render_template, request, jsonify, after_this_request
from werkzeug.utils import secure_filename
from ultralytics import YOLO
import cv2
import os

app = Flask(__name__)
model = YOLO("yolov8n.pt")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    input_dir = 'static/input'
    input_path = os.path.join(input_dir, filename)
    os.makedirs(input_dir, exist_ok=True)
    file.save(input_path)

    results = model(input_path)
    output_dir = 'static/output'
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, filename)
    annotated_frame = results[0].plot()
    cv2.imwrite(output_path, annotated_frame)

    detected_items = {}
    for box in results[0].boxes.data.tolist():
        class_id = int(box[5])
        class_name = model.names[class_id]
        detected_items[class_name] = detected_items.get(class_name, 0) + 1


    # Dataset
    nutrition_data = {
        "apple": {"Calories": "62kcal", "Sugar": "12.2g", "Protein": "0.19g", "Carbohydrates": "14.3g", "Fiber": "2g", "Fat": "0.21g", "Potassium": "95mg", "Calcium": "5mg", "Magnesium": "4.7mg", "Vitamin B-6": "0.021mg"},
        "banana": {"Calories": "98kcal", "Sugar": "15.8g", "Protein": "0.74g", "Carbohydrates": "21.2g", "Fiber": "1.7g", "Fat": "0.29g", "Potassium": "326mg", "Calcium": "5mg", "Magnesium": "28mg", "Vitamin A": "1µg", "Vitamin B-6": "0.209mg", "Vitamin K": "0.1µg"},
        "orange": {"Calories": "47kcal", "Sugar": "9.35g", "Protein": "0.94g", "Carbohydrates": "11.8g", "Fiber": "2.4g", "Fat": "0.12g", "Potassium": "181mg", "Calcium": "40mg", "Magnesium": "10mg", "Vitamin A": "11µg", "Vitamin B-6": "0.06mg", "Vitamin C": "53.2mg", "Vitamin E": "0.18mg"},
    }

    
    detailed_results = []
    for food, count in detected_items.items():
        if food in nutrition_data:
            detailed_results.append({
                "name": food,
                "count": count,
                "nutrition": nutrition_data[food]
            })

    os.remove(input_path)
    
    return jsonify({
        "result_image": output_path.replace("\\", "/"),
        "items": detailed_results
    })


if __name__ == '__main__':
    app.run(debug=True)