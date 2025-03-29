"""
Smart Dubbing System - Main Application

This application translates subtitles, enhances them with natural language features,
merges them for better flow, generates speech with text-to-speech technology, and
adjusts audio timing to match the subtitles.

Usage:
    python main.py

The application will guide you through the process with interactive prompts.
"""
import os
import time
from tqdm import tqdm
from dotenv import load_dotenv

# Import utility modules
from utils.translation import translate_srt_file
from utils.filler import add_filler_words
from utils.merge import load_srt, save_srt, merge_subtitles
from utils.speedometer import adjust_audio_length_ffmpeg
from utils.tts import generate_audio_with_elevenlabs, extract_text_from_srt

# Load environment variables
load_dotenv()

def create_directories():
    """Create necessary directories for output files"""
    directories = [
        'srt_files',
        'translated_output',
        'tts_output'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

def main():
    """
    Main function that orchestrates the subtitle translation and TTS pipeline
    """
    print("\n===== Smart Dubbing System =====\n")
    
    # Create necessary directories
    create_directories()
    
    # Get user inputs
    input_path = input("Enter the path of the input SRT file: ").strip()
    if not os.path.exists(input_path):
        print(f"Error: File '{input_path}' not found.")
        return
        
    source_lang = input("Enter the language of the original subtitles (e.g., English): ").strip()
    target_lang = input("Enter the language to translate the subtitles into (e.g., Spanish): ").strip()
    
    # Set file paths
    translated_path = 'srt_files/translated.srt'
    translated_filled_path = 'srt_files/translated_filled.srt'
    output_path = 'translated_output/merged_output.srt'
    audio_path = "tts_output/final_merged_output.wav"
    adjusted_audio_path = "tts_output/output_adjusted_audio.wav"

    # Step 1: Translate subtitles
    print("\nStarting subtitle translation process...")
    with tqdm(total=1, desc="Translation") as pbar:
        translate_srt_file(input_path, translated_path, source_lang, target_lang)
        pbar.update(1)

    # Step 2: Add filler words to make speech more natural
    print("\nEnhancing speech with natural filler words...")
    with tqdm(total=1, desc="Adding Fillers") as pbar:
        add_filler_words(translated_path, translated_filled_path, target_lang)
        pbar.update(1)

    # Step 3: Merge subtitles that are close together
    print("\nMerging subtitles for better flow...")
    subtitles = load_srt(translated_filled_path)
    merged_subtitles = merge_subtitles(subtitles)
    with tqdm(total=1, desc="Merging") as pbar:
        save_srt(merged_subtitles, output_path)
        pbar.update(1)

    # Step 4: Generate audio using Eleven Labs API
    print("\nGenerating speech audio from translated text...")
    with tqdm(total=1, desc="Audio Generation") as pbar:
        # Extract all text from the SRT file
        text_content = extract_text_from_srt(output_path)
        
        # Generate audio file
        generate_audio_with_elevenlabs(text_content, audio_path)
        pbar.update(1)

    # Step 5: Adjust audio length to match SRT timeline
    print("\nAdjusting audio timing to match subtitles...")
    with tqdm(total=1, desc="Adjusting Audio") as pbar:
        adjust_audio_length_ffmpeg(audio_path, output_path, adjusted_audio_path)
        pbar.update(1)
        
    print("\n===== Process Complete =====")
    print(f"Translated subtitles: {output_path}")
    print(f"Generated audio: {audio_path}")
    print(f"Timing-adjusted audio: {adjusted_audio_path}")
    print("\nThank you for using Smart Dubbing System!")

if __name__ == '__main__':
    main()