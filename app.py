from flask import Flask, render_template, request, jsonify, after_this_request
from werkzeug.utils import secure_filename
from ultralytics import YOLO
import cv2
import os

app = Flask(__name__)
model = YOLO("best.pt")

def extract_number(value):
    return float(''.join(c for c in value if c.isdigit() or c == '.'))


DAILY_REQUIREMENTS = {
    "Calories": 2000,
    "Protein": 50
}

RECOMMENDED_VITAMINS = ["Vitamin A", "Vitamin C", "Vitamin B-6"]
RECOMMENDED_MINERALS = ["Calcium", "Potassium"]

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
        "orange": {
            "Calories": "47kcal",
            "Sugar": "9g",
            "Protein": "0.9g",
            "Carbohydrates": "12g",
            "Fiber": "2.4g",
            "Fat": "0.1g",
            "Vitamin C": "53.2mg",
            "Calcium": "40mg",
            "Allergens": []
        },
        "banana": {
            "Calories": "89kcal",
            "Sugar": "12g",
            "Protein": "1.1g",
            "Carbohydrates": "23g",
            "Fiber": "2.6g",
            "Fat": "0.3g",
            "Vitamin B-6": "0.4mg",
            "Vitamin C": "8.7mg",
            "Allergens": ["Latex"]
        },
        "apple": {
            "Calories": "52kcal",
            "Sugar": "10g",
            "Protein": "0.3g",
            "Carbohydrates": "14g",
            "Fiber": "2.4g",
            "Fat": "0.2g",
            "Vitamin C": "4.6mg",
            "Potassium": "107mg",
            "Allergens": []
        },
        "cucumber": {
            "Calories": "16kcal",
            "Sugar": "1.7g",
            "Protein": "0.7g",
            "Carbohydrates": "4g",
            "Fiber": "0.5g",
            "Fat": "0.1g",
            "Vitamin K": "16.4µg",
            "Water": "95%",
            "Allergens": []
        },
        "corn": {
            "Calories": "86kcal",
            "Sugar": "3.2g",
            "Protein": "3.2g",
            "Carbohydrates": "19g",
            "Fiber": "2.7g",
            "Fat": "1.2g",
            "Magnesium": "37mg",
            "Vitamin B1": "0.2mg",
            "Allergens": ["Corn"]
        },
        "broccoli": {
            "Calories": "34kcal",
            "Sugar": "1.7g",
            "Protein": "2.8g",
            "Carbohydrates": "7g",
            "Fiber": "2.6g",
            "Fat": "0.4g",
            "Vitamin C": "89.2mg",
            "Vitamin K": "101.6µg",
            "Allergens": []
        },
        "potato": {
            "Calories": "77kcal",
            "Sugar": "0.8g",
            "Protein": "2g",
            "Carbohydrates": "17g",
            "Fiber": "2.2g",
            "Fat": "0.1g",
            "Vitamin C": "19.7mg",
            "Potassium": "421mg",
            "Allergens": []
        },
        "egg": {
            "Calories": "155kcal",
            "Sugar": "1.1g",
            "Protein": "13g",
            "Carbohydrates": "1.1g",
            "Fiber": "0g",
            "Fat": "11g",
            "Vitamin D": "2.2µg",
            "Calcium": "50mg",
            "Allergens": ["Egg"]
        },
        "onion": {
            "Calories": "40kcal",
            "Sugar": "4.2g",
            "Protein": "1.1g",
            "Carbohydrates": "9g",
            "Fiber": "1.7g",
            "Fat": "0.1g",
            "Vitamin C": "7.4mg",
            "Vitamin B-6": "0.1mg",
            "Allergens": []
        },
        "carrot": {
            "Calories": "41kcal",
            "Sugar": "4.7g",
            "Protein": "0.9g",
            "Carbohydrates": "10g",
            "Fiber": "2.8g",
            "Fat": "0.2g",
            "Vitamin A": "835µg",
            "Vitamin K": "13.2µg",
            "Allergens": []
        }
    }

    
    detailed_results = []
    total_calories = 0
    total_protein = 0
    detected_allergens = set()
    vitamins_found = set()
    minerals_found = set()
    for food, count in detected_items.items():
        if food not in nutrition_data:
            continue

        food_data = nutrition_data[food]

        calories = extract_number(food_data["Calories"])
        protein = extract_number(food_data["Protein"])

        total_calories += calories * count
        total_protein += protein * count

        for nutrient in food_data:
            if nutrient in RECOMMENDED_VITAMINS:
                vitamins_found.add(nutrient)
            if nutrient in RECOMMENDED_MINERALS:
                minerals_found.add(nutrient)

        for allergen in food_data.get("Allergens", []):
            detected_allergens.add(allergen)

        detailed_results.append({
            "name": food,
            "count": count,
            "nutrition": {k: v for k, v in food_data.items() if k != "Allergens"},
            "allergens": food_data.get("Allergens", [])
        })

    calorie_percent = (total_calories / DAILY_REQUIREMENTS["Calories"]) * 100
    protein_percent = (total_protein / DAILY_REQUIREMENTS["Protein"]) * 100

    vitamin_score = (len(vitamins_found) / len(RECOMMENDED_VITAMINS)) * 100
    mineral_score = (len(minerals_found) / len(RECOMMENDED_MINERALS)) * 100

    nutrition_score = int(
        (calorie_percent * 0.3) +
        (protein_percent * 0.3) +
        (vitamin_score * 0.2) +
        (mineral_score * 0.2)
    )
    nutrition_score = min(nutrition_score, 100)

    if nutrition_score < 30:
        score_label = "Poor"
    elif nutrition_score < 60:
        score_label = "Moderate"
    elif nutrition_score < 80:
        score_label = "Good"
    else:
        score_label = "Excellent"

    risk_messages = []
    if calorie_percent < 30:
        risk_messages.append("Low calorie intake detected. Risk of undernutrition.")
    if protein_percent < 30:
        risk_messages.append("Low protein intake detected. Risk of protein deficiency.")
    if vitamin_score < 50:
        risk_messages.append("Possible micronutrient deficiency detected.")
    if not risk_messages:
        risk_messages.append("Meal provides balanced nutritional support.")

    recommendations = []
    if protein_percent < 30:
        recommendations.append("Add legumes, eggs, or dairy to increase protein intake.")
    if calorie_percent < 30:
        recommendations.append("Add rice, bread, or tubers for more energy.")
    if vitamin_score < 50:
        recommendations.append("Include fruits and vegetables rich in vitamins.")
    if not recommendations:
        recommendations.append("Maintain a varied and balanced diet.")

    allergy_warnings = []
    if detected_allergens:
        for allergen in detected_allergens:
            allergy_warnings.append(f"⚠️ Contains potential allergen: {allergen}")
    else:
        allergy_warnings.append("No common food allergens detected.")

    os.remove(input_path)

    return jsonify({
        "result_image": output_path.replace("\\", "/"),
        "items": detailed_results,
        "total_nutrition": {
            "Calories (kcal)": round(total_calories, 2),
            "Protein (g)": round(total_protein, 2)
        },
        "nutrition_coverage": {
            "Calories (%)": round(calorie_percent, 1),
            "Protein (%)": round(protein_percent, 1)
        },
        "micronutrient_coverage": {
            "Vitamins (%)": round(vitamin_score, 1),
            "Minerals (%)": round(mineral_score, 1),
            "Vitamins Found": list(vitamins_found),
            "Minerals Found": list(minerals_found)
        },
        "nutrition_score": {
            "score": nutrition_score,
            "label": score_label
        },
        "malnutrition_analysis": risk_messages,
        "recommendations": recommendations,
        "allergy_information": allergy_warnings
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
    # app.run(debug=True)
