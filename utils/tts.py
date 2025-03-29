"""
Handles text-to-speech generation using external APIs.

This module provides functions to generate speech audio from text
using the Eleven Labs API.
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment variables
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
ELEVEN_LABS_VOICE_ID = os.getenv("ELEVEN_LABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default voice ID
ELEVEN_LABS_API_URL = os.getenv("ELEVEN_LABS_API_URL", "https://api.elevenlabs.io/v1/text-to-speech")

def generate_audio_with_elevenlabs(text, output_path, voice_id=None):
    """
    Generate audio using the Eleven Labs API.
    
    Args:
        text (str): Text to convert to speech
        output_path (str): Path to save the generated audio
        voice_id (str, optional): ID of the voice to use. Defaults to env setting.
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not ELEVEN_LABS_API_KEY:
        print("Error: Eleven Labs API key not found in environment variables.")
        return False
    
    # Use default voice ID if not specified
    if voice_id is None:
        voice_id = ELEVEN_LABS_VOICE_ID
    
    print(f"Generating speech using Eleven Labs API (voice ID: {voice_id})...")
    
    # Prepare request headers
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_LABS_API_KEY
    }
    
    # Prepare request data
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        # Make API request
        response = requests.post(
            f"{ELEVEN_LABS_API_URL}/{voice_id}",
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