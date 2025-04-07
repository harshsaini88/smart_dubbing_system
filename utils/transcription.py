"""
Utility for transcribing audio files to SRT format using OpenAI's Whisper model.
"""

import os
import whisper
import torch
import datetime
import srt
from typing import List, Tuple, Dict, Optional

def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format."""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    
    return f"{int(hours):02d}:{int(minutes):02d}:{seconds:02d},{milliseconds:03d}"

def seconds_to_timedelta(seconds: float) -> datetime.timedelta:
    """Convert seconds to datetime.timedelta"""
    return datetime.timedelta(seconds=seconds)

def generate_srt_from_audio(
    audio_path: str, 
    output_srt_path: str,
    model_name: str = "base",
    language: str = "English",
    word_level: bool = False,
    compute_type: str = "float16"
) -> None:
    """
    Generate SRT file from audio using Whisper ASR.
    
    Args:
        audio_path: Path to the audio file
        output_srt_path: Path where to save the SRT file
        model_name: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
        language: Source language of the audio
        word_level: Whether to use word-level timestamps
        compute_type: Computation type ('float16', 'float32', 'int8')
    """
    # Map compute type string to torch dtype
    dtype_map = {
        "float16": torch.float16,
        "float32": torch.float32,
        "int8": torch.int8
    }
    compute_dtype = dtype_map.get(compute_type, torch.float16)
    
    # Map language to Whisper language code
    language_map = {
        "English": "en",
        "Spanish": "es",
        "French": "fr",
        "German": "de",
        "Italian": "it",
        "Portuguese": "pt",
        "Dutch": "nl",
        "Russian": "ru",
        "Japanese": "ja",
        "Chinese": "zh",
        "Korean": "ko",
        "Arabic": "ar",
        "Hindi": "hi"
    }
    language_code = language_map.get(language, "en")
    
    # Load Whisper model
    model = whisper.load_model(model_name, device="cpu")
    
    # Set options for transcription
    options = {
        "language": language_code,
        "task": "transcribe",
        "word_timestamps": word_level
    }
    
    # Transcribe audio
    result = model.transcribe(audio_path, **options)
    
    # Convert to SRT format
    srt_entries = []
    for i, segment in enumerate(result["segments"]):
        start_time = seconds_to_timedelta(segment["start"])
        end_time = seconds_to_timedelta(segment["end"])
        text = segment["text"].strip()
        
        # Create SRT subtitle entry
        entry = srt.Subtitle(
            index=i+1,
            start=start_time,
            end=end_time,
            content=text
        )
        srt_entries.append(entry)
    
    # Write SRT file
    with open(output_srt_path, 'w', encoding='utf-8') as f:
        f.write(srt.compose(srt_entries))
    
    return output_srt_path