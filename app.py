import nltk
from nltk.stem import WordNetLemmatizer
import random
import torch
from sentence_transformers import SentenceTransformer, util
import pandas as pd
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import psycopg2
import langdetect
from googletrans import Translator
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_PORT=os.getenv('DB_PORT')

# Initialize NLTK resources
nltk.download('wordnet')

# Initialize SentenceTransformer model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Establish a connection to the PostgreSQL database
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)

# Create a cursor object
cur = conn.cursor()

# Execute a query to fetch data from the table
cur.execute("SELECT questions, answers, asset_links FROM chatbot")

# Fetch all rows from the result set
rows = cur.fetchall()

# Extract questions, answers, and asset links from the rows
questions = [row[0] for row in rows]
answers = [row[1] for row in rows]
asset_links = [row[2] for row in rows]

# Close the cursor and the connection
cur.close()
conn.close()

# Flask app code
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.static_folder = 'static'

@app.route("/chatbot/translate_welcome_message")
def translate_welcome_message():
    selected_language = request.args.get('lang')
    translated_message = translate_text("Hello! I'm NULP Connect's Virtual Support. I'm here to help you.", "en", selected_language)
    return translated_message

# Function to detect language and translate if necessary
def detect_and_translate(msg, user_lang):
    detected_language = langdetect.detect(msg)
    # List of Indian languages along with their ISO language codes
    supported_languages = ['as', 'bn', 'brx', 'doi', 'gu', 'hi', 'kn', 'ks', 'kok', 'mai', 'ml', 'mni', 'mr', 'ne', 'or', 'pa', 'sa', 'sat', 'sd', 'ta', 'te', 'ur']
    if detected_language in supported_languages:
        try:
            translator = Translator()
            msg = translator.translate(msg, src=detected_language, dest='en').text
        except Exception as e:
            print(f"Translation error: {e}")
            # Handle the exception here (e.g., return original message)
    return msg

# Function to translate text
def translate_text(text, src_lang, dest_lang):
    translator = Translator()
    translated_text = translator.translate(text, src=src_lang, dest=dest_lang).text
    return translated_text

# Function to translate HTML preserving structure
def translate_html(html, src_lang, dest_lang):
    soup = BeautifulSoup(html, 'html.parser')
    
    # Iterate through all text elements in the HTML
    for element in soup.find_all(text=True):
        # Translate only if the text is not empty and not a script or style tag
        if element.strip() and element.parent.name not in ['script', 'style']:
            translated_text = translate_text(element, src_lang, dest_lang)
            element.replace_with(translated_text)
    
    # Return the translated HTML with preserved structure
    return str(soup)

# Function to get bot response
def chatbot_response(msg, user_lang):
    # Detect language and translate if necessary
    msg_translated = detect_and_translate(msg, user_lang)
    
    # Encode sentences
    embeddings = model.encode(questions)
    
    # Encode user input
    query_embedding = model.encode([msg_translated])[0]
    
    # Calculate cosine similarity scores
    cos_scores = util.cos_sim(query_embedding, embeddings)
    
    # Find closest matching question
    max_score = torch.max(cos_scores)
    closest_idx = torch.argmax(cos_scores)
    closest_sentence = answers[closest_idx]
    
    # Get corresponding asset link
    asset = asset_links[closest_idx]
    
    try:
        join_text = ""
        if 'youtube' in asset:
            join_text = f"""<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:20px;"><iframe style="position:absolute;top:0;left:0;width:100%;height:100%;border-radius:20px;" width="600" height="400" src="{asset}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe></div>"""

        elif '.png' in asset:
            join_text = f"""<img src="{asset}" style="border-radius: 20px; width: 100%; height: 100%" />"""

        else:
            join_text = f"""<br><button style="background-color: #8F00FF; border-radius: 4px; border:none; padding: 4px; color: white;margin-top: 9px;" onclick="window.open('{asset}', '_blank')">Click Here</button>"""            

    except Exception as e:
        print(f"Error processing asset: {e}")
        join_text = ""
    
    # If accuracy score is not up to the mark.
    if max_score > 0.5:
        response_text = closest_sentence + join_text
        
        # If the input message was translated, translate the response back to the original language
        if msg != msg_translated:
            response_text = translate_html(response_text, 'en', user_lang)
        
        return response_text 
    else:
        # Responses for insufficient data.
        responses = [
            "Apologies, but I am unable to offer the requested information. Please feel free to contact us via email at nulp@niua.org."
        ]
        
        # Translate the response if necessary
        if msg != msg_translated:
            response_text = translate_text(random.choice(responses), 'en', user_lang)
            return response_text
        else:
            return random.choice(responses)

@app.route("/chatbot/get")
def get_bot_response():
    userText = request.args.get('msg')
    user_lang = langdetect.detect(userText)
    response_text = chatbot_response(userText, user_lang)
    print("--------------", response_text)
    return Response(response=response_text)

@app.route('/')
def welcome():
    return render_template('index.html', welcome_message="Hello! I'm NULP Connect's Virtual Support. I'm here to help you.")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
