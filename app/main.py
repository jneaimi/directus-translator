# main.py

from fastapi import FastAPI, HTTPException, Request
import openai
import os
import json  # Import json for safe parsing
from openai import OpenAI

app = FastAPI()

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


@app.post("/translate")
async def translate_endpoint(request: Request):
    try:
        body = await request.json()
        print("Received body:", body)  # Debug print
        
        # Initialize translations data
        translations_data = {}
        
        # Check if we have the translations key with create array
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="Request body must be a JSON object")
            
        translations = body.get("translations")
        if not translations or not isinstance(translations, dict):
            raise HTTPException(status_code=400, detail="Missing or invalid 'translations' object")
            
        create_items = translations.get("create")
        if not create_items or not isinstance(create_items, list):
            raise HTTPException(status_code=400, detail="Missing or invalid 'create' array in translations")
            
        if not create_items:
            raise HTTPException(status_code=400, detail="'create' array is empty")
            
        # Get the first item
        item = create_items[0]
        
        # Extract translatable fields
        if "headline" in item:
            translations_data["headline"] = item["headline"]
        if "content" in item:
            translations_data["content"] = item["content"]
            
        if not translations_data:
            raise HTTPException(
                status_code=400,
                detail="No translatable content found (headline or content)"
            )
            
        print("Extracted translations_data:", translations_data)  # Debug print
        
        # Perform translation
        translated_content = recursive_translate(translations_data)
        
        response = {
            "status": "success",
            "translated_data": translated_content
        }
        
        print("Response:", response)  # Debug print
        return response
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except HTTPException as he:
        raise he
    except Exception as e:
        print("Error:", str(e))  # Debug print
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")