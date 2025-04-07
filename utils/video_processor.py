import os
import subprocess
import tempfile
import logging

def extract_audio_from_video(video_path, audio_output_path):
    """
    Extract audio from a video file using FFmpeg
    
    Args:
        video_path (str): Path to input video file
        audio_output_path (str): Path to save extracted audio
        
    Returns:
        bool: True if extraction was successful, False otherwise
    """
    try:
        command = [
            'ffmpeg',
            '-y',  # Overwrite output file if it exists
            '-i', video_path,  # Input file
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # Audio codec
            '-ar', '44100',  # Audio sample rate
            '-ac', '2',  # Audio channels
            audio_output_path  # Output file
        ]
        
        # Run FFmpeg command
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode != 0:
            logging.error(f"Error extracting audio: {process.stderr}")
            return False
        
        return True
    except Exception as e:
        logging.error(f"Exception during audio extraction: {str(e)}")
        return False

def create_subtitled_video(video_path, subtitle_path, audio_path, output_path):
    """
    Create a video with subtitles and replaced audio using FFmpeg
    
    Args:
        video_path (str): Path to input video file
        subtitle_path (str): Path to SRT subtitle file
        audio_path (str): Path to new audio file
        output_path (str): Path to save the output video
        
    Returns:
        bool: True if creation was successful, False otherwise
    """
    try:
        # Create temporary file for subtitles with adjusted encoding
        with tempfile.NamedTemporaryFile(suffix='.srt', delete=False) as temp_file:
            temp_subtitle_path = temp_file.name
            
        # Copy SRT file with UTF-8 encoding to ensure compatibility
        with open(subtitle_path, 'r', encoding='utf-8') as f_in:
            with open(temp_subtitle_path, 'w', encoding='utf-8') as f_out:
                f_out.write(f_in.read())
        
        # Command to create video with subtitles and new audio
        command = [
            'ffmpeg',
            '-y',  # Overwrite output file if it exists
            '-i', video_path,  # Input video
            '-i', audio_path,  # Input audio
            '-map', '0:v',  # Use video from first input
            '-map', '1:a',  # Use audio from second input
            '-vf', f'subtitles={temp_subtitle_path}:force_style=\'FontSize=24,Alignment=2\'',  # Add subtitles
            '-c:v', 'libx264',  # Video codec
            '-crf', '18',  # Video quality
            '-c:a', 'aac',  # Audio codec
            '-b:a', '192k',  # Audio bitrate
            output_path  # Output file
        ]
        
        # Run FFmpeg command
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Clean up temporary subtitle file
        os.unlink(temp_subtitle_path)
        
        if process.returncode != 0:
            logging.error(f"Error creating subtitled video: {process.stderr}")
            return False
        
        return True
    except Exception as e:
        logging.error(f"Exception during video creation: {str(e)}")
        return False

def extract_video_duration(video_path):
    """
    Get the duration of a video file in seconds using FFmpeg
    
    Args:
        video_path (str): Path to video file
        
    Returns:
        float: Duration in seconds or None if an error occurred
    """
    try:
        command = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        
        # Run FFprobe command
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode != 0:
            logging.error(f"Error getting video duration: {process.stderr}")
            return None
        
        # Parse duration
        duration = float(process.stdout.strip())
        return duration
    except Exception as e:
        logging.error(f"Exception getting video duration: {str(e)}")
        return None

def extract_video_frame(video_path, output_path, time_position=0):
    """
    Extract a single frame from a video at a specific time position
    
    Args:
        video_path (str): Path to input video file
        output_path (str): Path to save extracted frame
        time_position (float): Time position in seconds
        
    Returns:
        bool: True if extraction was successful, False otherwise
    """
    try:
        command = [
            'ffmpeg',
            '-y',  # Overwrite output file if it exists
            '-ss', str(time_position),  # Seek position
            '-i', video_path,  # Input file
            '-vframes', '1',  # Extract only one frame
            '-q:v', '2',  # Quality level
            output_path  # Output file
        ]
        
        # Run FFmpeg command
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode != 0:
            logging.error(f"Error extracting video frame: {process.stderr}")
            return False
        
        return True
    except Exception as e:
        logging.error(f"Exception during frame extraction: {str(e)}")
        return False

def get_video_metadata(video_path):
    """
    Get video metadata including resolution, FPS, codec, etc.
    
    Args:
        video_path (str): Path to video file
        
    Returns:
        dict: Dictionary with video metadata
    """
    try:
        command = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,codec_name,r_frame_rate',
            '-of', 'json',
            video_path
        ]
        
        # Run FFprobe command
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode != 0:
            logging.error(f"Error getting video metadata: {process.stderr}")
            return {}
        
        import json
        data = json.loads(process.stdout)
        
        # Extract stream info
        if 'streams' in data and len(data['streams']) > 0:
            stream = data['streams'][0]
            
            # Parse frame rate fraction
            fps_parts = stream.get('r_frame_rate', '').split('/')
            fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else None
            
            return {
                'width': stream.get('width'),
                'height': stream.get('height'),
                'codec': stream.get('codec_name'),
                'fps': fps
            }
        
        return {}
    except Exception as e:
        logging.error(f"Exception getting video metadata: {str(e)}")
        return {}