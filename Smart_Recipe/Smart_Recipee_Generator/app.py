from flask import Flask, render_template, request, jsonify
import pickle
import numpy as np
import os

app = Flask(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'knn_model.pkl')
with open(MODEL_PATH, 'rb') as f:
    bundle = pickle.load(f)

model = bundle['model']
le = bundle['label_encoder']
feature_cols = bundle['feature_cols']
all_ingredients = bundle['all_ingredients']

RECIPE_INFO = {
    "Aloo Gobi": {"emoji": "🥔", "desc": "Spiced potato & cauliflower dry curry"},
    "Chole Bhature": {"emoji": "🫘", "desc": "Tangy chickpea curry with fluffy fried bread"},
    "Dal Tadka": {"emoji": "🍲", "desc": "Tempered lentil soup with aromatic spices"},
    "Jeera Rice": {"emoji": "🍚", "desc": "Fragrant cumin-infused basmati rice"},
    "Kadai Paneer": {"emoji": "🧀", "desc": "Paneer in bold kadai masala sauce"},
    "Lemon Rice": {"emoji": "🍋", "desc": "South Indian tangy lemon-tempered rice"},
    "Masala Dosa": {"emoji": "🥞", "desc": "Crispy crepe with spiced potato filling"},
    "Mixed Veg Curry": {"emoji": "🥕", "desc": "Hearty mixed vegetable curry"},
    "Mushroom Curry": {"emoji": "🍄", "desc": "Earthy mushroom in rich tomato gravy"},
    "Palak Paneer": {"emoji": "🌿", "desc": "Creamy spinach curry with paneer cubes"},
    "Paneer Butter Masala": {"emoji": "🧈", "desc": "Rich buttery tomato-cream paneer dish"},
    "Paneer Tikka": {"emoji": "🔥", "desc": "Grilled marinated paneer with peppers"},
    "Poha": {"emoji": "🌾", "desc": "Light flattened rice with onion & spices"},
    "Rajma Curry": {"emoji": "🫘", "desc": "Punjabi kidney bean curry in thick gravy"},
    "Sambar Rice": {"emoji": "🍛", "desc": "South Indian lentil-vegetable stew with rice"},
    "Tomato Rice": {"emoji": "🍅", "desc": "Tangy South Indian tomato-spiced rice"},
    "Upma": {"emoji": "🫙", "desc": "Savory semolina breakfast porridge"},
    "Veg Fried Rice": {"emoji": "🍳", "desc": "Indo-Chinese style vegetable fried rice"},
    "Veg Pulao": {"emoji": "🌸", "desc": "Aromatic one-pot rice with vegetables"},
    "Vegetable Biryani": {"emoji": "✨", "desc": "Royal layered spiced vegetable biryani"},
}

@app.route('/')
def index():
    return render_template('index.html', ingredients=all_ingredients)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    selected = data.get('ingredients', [])
    cooking_time = int(data.get('cooking_time', 30))

    if not selected:
        return jsonify({'error': 'Please select at least one ingredient.'}), 400

    # Build feature vector
    row = {}
    for col in feature_cols:
        if col == 'cooking_time_minutes':
            row[col] = cooking_time
        else:
            ing_name = col.replace('ing_', '').replace('_', ' ')
            row[col] = 1 if ing_name in selected else 0

    X_input = np.array([[row[c] for c in feature_cols]])
    pred_idx = model.predict(X_input)[0]
    proba = model.predict_proba(X_input)[0]

    recipe_name = le.inverse_transform([pred_idx])[0]
    confidence = round(float(proba[pred_idx]) * 100, 1)

    # Top 3 predictions
    top3_idx = np.argsort(proba)[::-1][:3]
    top3 = [
        {
            'name': le.inverse_transform([i])[0],
            'confidence': round(float(proba[i]) * 100, 1),
            'emoji': RECIPE_INFO.get(le.inverse_transform([i])[0], {}).get('emoji', '🍽️'),
            'desc': RECIPE_INFO.get(le.inverse_transform([i])[0], {}).get('desc', '')
        }
        for i in top3_idx if proba[i] > 0.01
    ]

    return jsonify({
        'recipe': recipe_name,
        'confidence': confidence,
        'emoji': RECIPE_INFO.get(recipe_name, {}).get('emoji', '🍽️'),
        'desc': RECIPE_INFO.get(recipe_name, {}).get('desc', ''),
        'top3': top3
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
