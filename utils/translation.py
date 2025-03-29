"""
Handles translation of SRT subtitles between languages.

This module uses the OpenAI API to translate text between languages
and applies that translation to SRT subtitle files.
"""
import openai
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_translated_text(text, source_language, target_language):
    """
    Translate text from source language to target language using OpenAI API.
    
    Args:
        text (str): Text to translate
        source_language (str): Source language name (e.g., "English")
        target_language (str): Target language name (e.g., "Spanish")
        
    Returns:
        str: Translated text or original text if translation fails
    """
    prompt = f"Translate the following text from {source_language} to {target_language}:\n'{text}'"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text if translation fails

def translate_srt_file(input_path, output_path, source_lang, target_lang):
    """
    Translate an entire SRT subtitle file.
    
    Args:
        input_path (str): Path to source SRT file
        output_path (str): Path to save translated SRT file
        source_lang (str): Source language name
        target_lang (str): Target language name
    """
    print(f"Translating subtitles from {source_lang} to {target_lang}...")
    
    with open(input_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    translated_content = []
    for line in lines:
        # Keep subtitle numbers and timestamps unchanged
        if re.match(r'^\d+$', line.strip()) or re.match(r'^\d{2}:\d{2}:\d{2}.\d{3} --> \d{2}:\d{2}:\d{2}.\d{3}$', line.strip()):
            translated_content.append(line)
        # Translate subtitle text
        elif line.strip():
            translated_text = get_translated_text(line.strip(), source_lang, target_lang)
            translated_content.append(translated_text + '\n')
        # Keep empty lines unchanged
        else:
            translated_content.append(line)

    # Write translated content to output file
    with open(output_path, 'w', encoding='utf-8') as output_file:
        output_file.writelines(translated_content)
        
    print(f"Translation complete. Saved to {output_path}")