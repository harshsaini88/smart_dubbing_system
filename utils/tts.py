"""
Handles text-to-speech generation using predefined Eleven Labs voices.

This module provides functions to generate speech using existing Eleven Labs voices
instead of voice cloning capabilities.
"""
import os
import requests
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment variables
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
ELEVEN_LABS_API_URL = os.getenv("ELEVEN_LABS_API_URL", "https://api.elevenlabs.io/v1")

# Predefined voice IDs to use instead of voice cloning
VOICE_OPTIONS = {
    "male_american": "zT03pEAEi0VHKciJODfn",  # Josh - deep male American voice
    "female_british": "1qEiC6qsybMkmnNdVMbK",  # Rachel - female British voice
    "male_british": "m5qndnI7u4OAdXhH0Mr5"    # Adam - male British voice
}

def get_available_voices():
    """
    Get a list of available voices from Eleven Labs API.
    
    Returns:
        list: List of available voice objects
    """
    if not ELEVEN_LABS_API_KEY:
        print("Error: Eleven Labs API key not found in environment variables.")
        return []
    
    headers = {
        "xi-api-key": ELEVEN_LABS_API_KEY
    }
    
    try:
        response = requests.get(
            f"{ELEVEN_LABS_API_URL}/voices",
            headers=headers
        )
        
        if response.status_code == 200:
            voices = response.json().get("voices", [])
            return voices
        else:
            print(f"Error fetching voices: {response.status_code} - {response.text}")
            return []
    
    except Exception as e:
        print(f"Exception fetching voices: {e}")
        return []

def generate_audio_with_voice(text, output_path, voice_id, stability=0.5, similarity_boost=0.75):
    """
    Generate audio using a predefined voice via the Eleven Labs API.
    
    Args:
        text (str): Text to convert to speech
        output_path (str): Path to save the generated audio
        voice_id (str): ID of the voice to use
        stability (float): Voice stability setting (0.0-1.0)
        similarity_boost (float): Voice similarity boost setting (0.0-1.0)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not ELEVEN_LABS_API_KEY:
        print("Error: Eleven Labs API key not found in environment variables.")
        return False
    
    print(f"Generating speech using voice ID: {voice_id}...")
    
    # Prepare request headers
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_LABS_API_KEY
    }
    
    # Prepare request data
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",  # Using multilingual model for better translation support
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost
        }
    }
    
    try:
        # Make API request
        response = requests.post(
            f"{ELEVEN_LABS_API_URL}/text-to-speech/{voice_id}",
            json=data,
            headers=headers
        )
        
        # Check if request was successful
        if response.status_code == 200:
            # Save the audio file
            with open(output_path, "wb") as audio_file:
                audio_file.write(response.content)
            print(f"Successfully generated audio and saved to {output_path}")
            return True
        else:
            print(f"Error from Eleven Labs API: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        print(f"Exception during TTS generation: {e}")
        return False

def extract_text_from_srt(srt_file):
    """
    Extract all text from an SRT file to create a single text string for TTS.
    
    Args:
        srt_file (str): Path to the SRT file
        
    Returns:
        str: Concatenated text from the SRT file
    """
    from utils.merge import load_srt
    
    print(f"Extracting text from SRT file: {srt_file}")
    subtitles = load_srt(srt_file)
    text_content = " ".join([subtitle['text'] for subtitle in subtitles])
    print(f"Extracted {len(text_content)} characters of text")
    return text_content