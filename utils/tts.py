"""
Handles text-to-speech generation with voice cloning capabilities.

This module provides functions to clone a voice from an input audio file
and generate new speech in the same voice using the Eleven Labs API.
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

def create_voice_clone(audio_file_path, voice_name="Cloned Voice"):
    """
    Create a voice clone from an audio sample using Eleven Labs API.
    
    Args:
        audio_file_path (str): Path to the audio file for voice cloning
        voice_name (str): Name to assign to the cloned voice
        
    Returns:
        str: Voice ID if successful, None otherwise
    """
    if not ELEVEN_LABS_API_KEY:
        print("Error: Eleven Labs API key not found in environment variables.")
        return None
    
    print(f"Creating voice clone from {audio_file_path}...")
    
    # Prepare request headers
    headers = {
        "xi-api-key": ELEVEN_LABS_API_KEY
    }
    
    # Create multipart form data with audio file
    with open(audio_file_path, "rb") as audio_file:
        files = {
            "files": (os.path.basename(audio_file_path), audio_file, "audio/mpeg"),
        }
        
        data = {
            "name": voice_name,
            "description": "Voice clone created by Smart Dubbing System"
        }
        
        try:
            # Make API request to add a voice
            response = requests.post(
                f"{ELEVEN_LABS_API_URL}/voices/add",
                headers=headers,
                data=data,
                files=files
            )
            
            # Check if request was successful
            if response.status_code == 200:
                response_data = response.json()
                voice_id = response_data.get("voice_id")
                print(f"Successfully created voice clone with ID: {voice_id}")
                return voice_id
            else:
                print(f"Error from Eleven Labs API: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Exception during voice cloning: {e}")
            return None

def delete_cloned_voice(voice_id):
    """
    Delete a cloned voice to clean up after processing.
    
    Args:
        voice_id (str): ID of the voice to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not voice_id or not ELEVEN_LABS_API_KEY:
        return False
    
    print(f"Deleting cloned voice with ID: {voice_id}...")
    
    headers = {
        "xi-api-key": ELEVEN_LABS_API_KEY
    }
    
    try:
        response = requests.delete(
            f"{ELEVEN_LABS_API_URL}/voices/{voice_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"Successfully deleted cloned voice.")
            return True
        else:
            print(f"Error deleting voice: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Exception during voice deletion: {e}")
        return False

def generate_audio_with_cloned_voice(text, output_path, voice_id):
    """
    Generate audio using a cloned voice via the Eleven Labs API.
    
    Args:
        text (str): Text to convert to speech
        output_path (str): Path to save the generated audio
        voice_id (str): ID of the cloned voice to use
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not ELEVEN_LABS_API_KEY:
        print("Error: Eleven Labs API key not found in environment variables.")
        return False
    
    print(f"Generating speech using cloned voice (ID: {voice_id})...")
    
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
            "stability": 0.5,
            "similarity_boost": 0.75  # Higher similarity to better match the original voice
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
            print(f"Successfully generated audio with cloned voice and saved to {output_path}")
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

def extract_sample_audio(input_audio_path, sample_audio_path, duration=30):
    """
    Extract a sample from the input audio for voice cloning.
    Eleven Labs works best with 30-60 second samples.
    
    Args:
        input_audio_path (str): Path to the original audio
        sample_audio_path (str): Path to save the sample
        duration (int): Maximum duration of the sample in seconds
        
    Returns:
        str: Path to the sample audio file
    """
    try:
        from pydub import AudioSegment
        
        # Load the audio
        audio = AudioSegment.from_file(input_audio_path)
        
        # Take a sample (either the full audio if it's short, or the first N seconds)
        sample_duration_ms = min(duration * 1000, len(audio))
        sample = audio[:sample_duration_ms]
        
        # Export the sample
        sample.export(sample_audio_path, format="mp3")
        
        print(f"Created {sample_duration_ms/1000:.1f} second audio sample for voice cloning")
        return sample_audio_path
        
    except Exception as e:
        print(f"Error creating audio sample: {e}")
        # If extraction fails, return the original file
        return input_audio_path