# main.py

from fastapi import FastAPI, HTTPException, Request
import openai
import os
import json  # Import json for safe parsing
from openai import OpenAI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["lan.estatfinder.com", "localhost", "127.0.0.1"]
)

# Set OpenAI API Key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()


def translate_text_with_prompt(text: str, target_language: str = "Arabic") -> str:
    """
    Translate a given text using OpenAI's chat models with a custom advanced prompt.
    
    Args:
        text (str): The English text to be translated.
        target_language (str): The target language for translation. Default is "Arabic".
        
    Returns:
        str: The translation result in JSON format.
    """
    # System prompt with detailed translation instructions
    system_prompt = f"""
    You are an expert translator specializing in English to {target_language} translations. 
    Your task is to provide an accurate and natural-sounding translation while preserving 
    the original meaning and tone of the text.
    
    Please follow these instructions carefully:
    
    1. Translate the content into Modern Standard Arabic (فصحى), ensuring grammatical 
       correctness and appropriate vocabulary usage.
    2. Maintain the original formatting, including paragraphs, line breaks, and any 
       special characters or punctuation marks.
    3. Keep proper nouns, brand names, and technical terms in their original form.
    4. For idiomatic expressions or culturally specific references, find an Arabic 
       equivalent that conveys the same meaning. If no suitable equivalent exists, 
       translate the meaning rather than providing a literal translation.
    5. After completing the translation, review it to ensure accuracy, fluency, 
       and naturalness in Arabic.
    
    Your final output must be in the specified JSON format:
    
    {{
        "arabic_translation": "Your Arabic translation here",
        "translation_notes": "Any relevant notes or explanations about the translation, if necessary"
    }}
    
    Remember to provide a high-quality translation that accurately conveys the meaning and tone of the original English content in fluent, natural-sounding Arabic.
    """

    # User prompt containing the text to be translated
    user_prompt = f"Here is the English content to be translated:\n\n{text}"
    
    try:
        # Call OpenAI's ChatCompletion API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Replace with "gpt-4" if you have access
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0  # Set to 0 for more consistent translations
        )
        
        # Extract and return the translation result
        return response.choices[0].message.content.strip()
    
    except openai.APIError as e:
        # Handle OpenAI API errors
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        # Handle general errors
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def recursive_translate(data, target_language: str = "Arabic"):
    """
    Recursively translate all text within the translations section using the custom translation prompt.
    
    Args:
        data (dict or list): The JSON data containing text to be translated.
        target_language (str): The target language for translation. Default is "Arabic".
        
    Returns:
        dict or list: The translated JSON data.
    """
    if isinstance(data, dict):
        translated_data = {}
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                # Recursively translate nested structures
                translated_data[key] = recursive_translate(value, target_language)
            elif isinstance(value, str):
                # Translate string values
                translated_translation = translate_text_with_prompt(value, target_language)
                # Parse the JSON response from the translation safely
                try:
                    translated_json = json.loads(translated_translation)
                    translated_data[key] = translated_json.get("arabic_translation", value)
                except json.JSONDecodeError:
                    # If parsing fails, use the raw translated text
                    translated_data[key] = translated_translation
            else:
                # Keep non-string values as is
                translated_data[key] = value
        return translated_data
    elif isinstance(data, list):
        # Translate each element in the list
        return [recursive_translate(item, target_language) for item in data]
    else:
        # Return non-translatable data as is
        return data


@app.get("/version")
async def version():
    return {"version": "2.0", "environment": "production"}

@app.post("/translate")
async def translate_endpoint(request: Request):
    try:
        print(f"Request headers: {request.headers}")  # Debug headers
        body = await request.json()
        print(f"Request body: {body}")  # Debug body
        
        # Check for required fields in the new structure
        if "payload" not in body:
            print("Invalid request structure")
            return {
                "status": "error",
                "detail": "Invalid request structure",
                "received": body
            }
        
        # Extract fields to translate from payload
        to_translate = {
            "title": body["payload"].get("title", ""),
            "Headline": body["payload"].get("Headline", ""),
            "content": body["payload"].get("content", "")
        }
        
        # Translate the content
        translated = recursive_translate(to_translate)
        
        # Return both original and translated content
        return {
            "status": "success",
            "event": body.get("event"),
            "collection": body.get("collection"),
            "key": body.get("key"),
            "payload": {
                **body["payload"],  # Original payload
                "translations": {
                    "ar": translated  # Arabic translations
                }
            }
        }
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0"}