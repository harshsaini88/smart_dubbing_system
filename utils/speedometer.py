"""
Handles audio timing adjustment to match subtitle timing.

This module adjusts the duration of an audio file to match the
timing specified in an SRT subtitle file using FFmpeg.
"""
import pysrt
import subprocess
import os
from datetime import datetime

def adjust_audio_length_ffmpeg(audio_path, srt_path, output_path):
    """
    Adjust audio length to match the timing in an SRT file using FFmpeg.
    
    Args:
        audio_path (str): Path to input audio file
        srt_path (str): Path to SRT file with timing information
        output_path (str): Path to save adjusted audio file
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"Adjusting audio timing to match subtitles...")
    
    # Verify the existence of input files
    if not os.path.exists(audio_path):
        print(f"Error: Audio file '{audio_path}' not found.")
        return False
    if not os.path.exists(srt_path):
        print(f"Error: SRT file '{srt_path}' not found.")
        return False

    try:
        # Load and parse the SRT file to get the total subtitle duration
        subs = pysrt.open(srt_path)
        start_time = subs[0].start.to_time()
        end_time = subs[-1].end.to_time()
        
        # Calculate the target duration from the SRT timeline in seconds
        target_duration = (end_time.hour * 3600 + end_time.minute * 60 + end_time.second + end_time.microsecond/1000000) - \
                          (start_time.hour * 3600 + start_time.minute * 60 + start_time.second + start_time.microsecond/1000000)
        
        # Get the current duration of the audio in seconds using ffprobe
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True
        )
        current_duration = float(result.stdout.strip())
        
        # Calculate the stretch factor needed to match the target duration
        stretch_factor = current_duration / target_duration
        print(f"Current audio duration: {current_duration:.2f}s, Target SRT duration: {target_duration:.2f}s")
        print(f"Calculated stretch factor: {stretch_factor:.4f}")

        # Define the range for humanistic adjustment factors
        fine_threshold = 0.08  # 8% adjustment threshold for minimal change
        max_stretch_factor = 1.1  # Max stretch for more natural pacing
        min_stretch_factor = 0.9  # Min stretch for humanistic timing

        # Clip the stretch factor within natural bounds
        if stretch_factor > max_stretch_factor:
            print(f"Limiting stretch factor from {stretch_factor:.4f} to {max_stretch_factor}")
            stretch_factor = max_stretch_factor
        elif stretch_factor < min_stretch_factor:
            print(f"Limiting stretch factor from {stretch_factor:.4f} to {min_stretch_factor}")
            stretch_factor = min_stretch_factor

        # Only apply FFmpeg adjustment if beyond the fine threshold
        if abs(stretch_factor - 1) > fine_threshold:
            # Calculate the `atempo` factor based on the stretch factor
            atempo_factors = []
            temp_stretch = stretch_factor
            
            while temp_stretch > 2.0 or temp_stretch < 0.5:
                factor = 2.0 if temp_stretch > 2.0 else 0.5
                atempo_factors.append(factor)
                temp_stretch /= factor
            
            atempo_factors.append(temp_stretch)

            # Construct the `atempo` filter chain string
            atempo_filter = ",".join([f"atempo={factor}" for factor in atempo_factors])

            # Create a unique output path to avoid overwriting existing files
            unique_output_path = add_timestamp_to_filename(output_path)

            # Use FFmpeg to adjust audio duration with atempo filter
            print(f"Applying FFmpeg filter: {atempo_filter}")
            subprocess.run(
                ["ffmpeg", "-i", audio_path, "-filter:a", atempo_filter, "-y", unique_output_path]
            )
            print(f"Audio has been adjusted with FFmpeg and saved to {unique_output_path}")
            return True
        else:
            # If minimal adjustment is needed, copy the original audio to output
            print("Adjustment is minimal; original audio retained to preserve quality.")
            subprocess.run(["ffmpeg", "-i", audio_path, "-c", "copy", output_path])
            return True
    except Exception as e:
        print(f"An error occurred during audio adjustment: {e}")
        return False

def add_timestamp_to_filename(filepath):
    """
    Add a timestamp to a filename to avoid overwriting existing files.
    
    Args:
        filepath (str): Original file path
        
    Returns:
        str: File path with timestamp inserted before extension
    """
    base, ext = os.path.splitext(filepath)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base}_{timestamp}{ext}"