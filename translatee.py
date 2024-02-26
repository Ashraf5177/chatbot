# Import necessary modules
from flask import Flask, render_template, request, jsonify
from spellchecker import SpellChecker
from langdetect import detect
from googletrans import Translator
import requests

# Initialize Flask app
app = Flask(__name__)

# Define keywords and responses data structure
data = {
    "keywords": {
        "greeting": ["hello", "hi", "hey"],
        "farewell": ["bye", "goodbye", "see you"], 
        "items": ["fruits", "vegetables", "dairy", "snacks", "beverages"],
        "charges": ["delivery charges", "delivery price", "charges", "price", "charge", "delivery", "fee", "fees"],
        "offers": ["discount", "offers", "offer", "off", "discounts"],
        "track": ["track my order", "track", "where is my order", "order"],
        "history": ["order history", "past purchases", "previous orders", "order tracking", "history"],
        "product":["products", "items", "item", "product"]
    },
    "responses": {
        "greeting": 'Hello! How can I assist you today?',
        "farewell": 'Thank you for shopping with us! Have a great day!',
        "not_understood": 'I am sorry, I did not understand that. Could you please ask again?',
        "track": 'Tracking your order is currently not available in your area.',
        "charges": 'We offer free delivery on orders above Rs 199 and below that delivery charge of Rs 49 is applied.',
        "offers": 'Available offer: get 20 percent discount on shopping above Rs 499.',
        "order_history_not_available": 'Sorry, your order history is not available at the moment. Please try again later.',
        "order_history_empty": 'Your order history is empty.',
        "product": 'We offer a variety of products. Here are some of our top selling products'
    }
}

# Initialize spell checker
spell_checker = SpellChecker()
# Load words into the spell checker from keywords data
spell_checker.word_frequency.load_words(set(word for words in data["keywords"].values() for word in words))

# Function to detect language of text
def detect_language(text):
    return detect(text)

# Function to translate text to target language
def translate_text(text, target_language):
    translator = Translator()
    translated = translator.translate(text, dest='en')
    return translated.text, translated.src

# Function to find appropriate response based on user input
def find_response(user_input, data):
    # Detect language of user input
    language = detect_language(user_input)
    
    # Translate non-English input to English
    if language != 'en':
        user_input, _ = translate_text(user_input, 'en')

    corrected_input = []

    # Check if user input contains any keywords related to tracking orders
    if any(word in user_input.lower() for word in data["keywords"]["track"]):
        return track_order()

    # Check if user input contains any keywords related to order history
    if any(word in user_input.lower() for word in data["keywords"]["history"]):
        return order_history()

    # Check if user input contains any keywords related to products
    if any(word in user_input.lower() for word in data["keywords"]["product"]):
        return product_inquiry()

    # Check spelling for each word in user input and correct if needed
    for word in user_input.split():
        corrected_word = spell_checker.correction(word)
        corrected_input.append(corrected_word)

    # Match user input with predefined keywords and get appropriate response
    for keyword, synonyms in data["keywords"].items():
        if any(word in corrected_input for word in synonyms):
            response = data["responses"].get(keyword, data["responses"]["not_understood"])
            if language != 'en':
                response, _ = translate_text(response, language)
            return response

    # Return default response if no match found
    response = data["responses"]["not_understood"]
    if language != 'en':
        response, _ = translate_text(response, language)
    return response



def track_order():
    # Backend API endpoint for tracking orders
    api_url = "https://edamam-food-and-grocery-database.p.rapidapi.com/api/food-database/v2/parser"

    querystring = {
        "nutrition-type": "cooking",
        "category[0]": "generic-foods",
        "health[0]": "alcohol-free",
        "label": "serving"
    }

    headers = {
        "X-RapidAPI-Key": "5a491cceeamsha927645b37d5992p1b2469jsn0071e75d4032",
        "X-RapidAPI-Host": "edamam-food-and-grocery-database.p.rapidapi.com"
    }

    try:
        response = requests.get(api_url, headers=headers, params=querystring)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes

        data = response.json()

    
        if 'hints' in data:
            titles = [item['food']['label'] for item in data['hints']]
            return titles
        else: 
            return {"error"}
    
    except requests.exceptions.RequestException as e:
        return f"Error making request: {e}"




# Function to retrieve order history
def order_history():
    # Backend API endpoint for retrieving order history
    api_url = "http://your-backend-api.com/order-history"

    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            order_history_data = response.json().get("order_history")
            if order_history_data:
                return "\n".join(order_history_data)
            else:
                return data["responses"]["order_history_empty"]
        else:
            return data["responses"]["order_history_not_available"]
    except Exception as e:
        return f"Sorry, an error occurred: {str(e)}"


def product_inquiry():
    pass



# Route for home page
@app.route('/')
def index():
    return render_template('index.html', data=data)


# Route for getting response from user input
@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.form['user_input']
    print(user_input)
    response = find_response(user_input, data)
    return jsonify({'response': response})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
