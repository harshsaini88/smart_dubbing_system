import os
import time
import streamlit as st
from dotenv import load_dotenv
import json

# Import utility modules
from utils.translation import translate_srt_file
from utils.filler import add_filler_words
from utils.merge import load_srt, save_srt, merge_subtitles
from utils.speedometer import adjust_audio_length_ffmpeg
from utils.tts import generate_audio_with_voice, extract_text_from_srt, VOICE_OPTIONS, get_available_voices
from utils.transcription import generate_srt_from_audio
from utils.video_processor import extract_audio_from_video
from utils.lipsync import create_lip_sync_video
from google.cloud import storage
from google.oauth2 import service_account

# Load environment variables
load_dotenv()

# Add this function to your app setup
def setup_google_cloud_auth():
    """Set up Google Cloud authentication"""
    # Check for credentials file
    credentials_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if credentials_file and os.path.exists(credentials_file):
        # Use credentials file if available
        return storage.Client.from_service_account_json(credentials_file)
    elif os.getenv("GOOGLE_CREDENTIALS_JSON"):
        # Use JSON string if available (useful for Streamlit Cloud)
        credentials_info = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        return storage.Client(credentials=credentials)
    else:
        st.error("⚠️ Google Cloud credentials not found. Please set the GOOGLE_APPLICATION_CREDENTIALS environment variable or add your credentials JSON to your .env file.")
        st.info("See https://cloud.google.com/docs/authentication/getting-started for more information.")
        return None
    
def create_directories():
    """Create necessary directories for output files"""
    directories = [
        'audio_input',
        'srt_files',
        'translated_output',
        'tts_output',
        'video_input',
        'video_output'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Function to crop video after lip sync
def crop_video(input_video, output_video, crop_top=20):
    """Crop specified pixels from the top of the video"""
    import subprocess
    
    # Get video dimensions with ffprobe
    cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 {input_video}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    width, height = map(int, result.stdout.strip().split(','))
    
    # Calculate new dimensions
    new_height = height - crop_top
    
    # Crop video with ffmpeg
    cmd = f'ffmpeg -i {input_video} -vf "crop={width}:{new_height}:0:{crop_top}" -c:a copy {output_video} -y'
    subprocess.run(cmd, shell=True)
    
    return output_video

# Set page configuration
st.set_page_config(
    page_title="Video Translation with TTS and Lip Sync",
    page_icon="🎙️",
    layout="wide"
)

# App title and description
st.title("Video Translation with TTS and Lip Sync")
st.markdown("""
This application helps you dub video content from one language to another using Eleven Labs voices:
- Upload a video file for automatic transcription
- Choose from our selection of premium voices
- Your video will be translated to your desired language
""")

# Check for API keys
if not os.getenv("ELEVEN_LABS_API_KEY"):
    st.error("⚠️ Eleven Labs API key not found. Please set the ELEVEN_LABS_API_KEY environment variable or add it to your .env file.")
    st.info("Get an API key from [Eleven Labs](https://elevenlabs.io)")
    st.stop()

if not os.getenv("SYNC_LABS_API_KEY"):
    st.error("⚠️ Sync Labs API key not found. Please set the SYNC_LABS_API_KEY environment variable or add it to your .env file for lip sync features.")
    st.info("Get an API key from [Sync Labs](https://synclabs.ai)")
    st.stop()

# Create sidebar for inputs
st.sidebar.header("Input Settings")

# Create necessary directories
create_directories()

# File uploader for video
uploaded_file = st.sidebar.file_uploader("Upload Video file", type=["mp4", "mov", "avi", "mkv"])
input_video_path = None
if uploaded_file:
    # Save the uploaded file
    input_video_path = f"video_input/{uploaded_file.name}"
    with open(input_video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success(f"Video file uploaded successfully!")

input_audio_path = "audio_input/extracted_audio.wav" if uploaded_file else None

# Language selection
source_lang = st.sidebar.text_input("Source Language (e.g., English)", "English")
target_lang = st.sidebar.text_input("Target Language (e.g., Spanish)", "Spanish")

# Voice selection settings
st.sidebar.header("Voice Settings")

# Voice selection dropdown
voice_options = {
    "Vikas": VOICE_OPTIONS["male_american"],
    "Harshita": VOICE_OPTIONS["female_british"],
    "Keshav": VOICE_OPTIONS["male_british"]
}
selected_voice_name = st.sidebar.selectbox("Select Voice", list(voice_options.keys()))
selected_voice_id = voice_options[selected_voice_name]

# Voice settings sliders
similarity_boost = st.sidebar.slider("Voice expressiveness", 0.0, 1.0, 0.75, 
                                help="Higher values make the voice more expressive but may sound less natural")
stability = st.sidebar.slider("Voice stability", 0.0, 1.0, 0.5, 
                         help="Higher values make the voice more consistent but less expressive")

# Set file paths
transcribed_path = "srt_files/transcribed.srt"
translated_path = 'srt_files/translated.srt'
translated_filled_path = 'srt_files/translated_filled.srt'
output_path = 'translated_output/merged_output.srt'
audio_path = "tts_output/final_merged_output.wav"
adjusted_audio_path = "tts_output/adjusted_output.wav"
lip_synced_video_path = "video_output/lip_synced_video.mp4"
cropped_video_path = "video_output/cropped_video.mp4"

storage_client = setup_google_cloud_auth()
if not storage_client:
    st.sidebar.warning("Google Cloud authentication not set up properly. Lip sync feature may not work.")

# Process button
if uploaded_file is not None and st.sidebar.button("Real Time Translation"):
    # Main processing steps with progress bars
    st.header("Processing")
    
    # Step 0: Extract audio from video
    with st.spinner("Extracting audio from video..."):
        progress_bar0 = st.progress(0)
        extract_audio_from_video(input_video_path, input_audio_path)
        progress_bar0.progress(100)
        st.success("Audio extraction complete!")
    
    # Step 1: Transcribe audio to SRT
    with st.spinner("Transcribing audio to SRT..."):
        progress_bar1 = st.progress(0)
        # Fixed whisper model to base
        whisper_model = "base"
        generate_srt_from_audio(input_audio_path, transcribed_path, whisper_model, source_lang)
        progress_bar1.progress(100)
        st.success("Transcription complete!")
    
    # Step 2: Translate subtitles
    with st.spinner("Translating speech..."):
        progress_bar2 = st.progress(0)
        translate_srt_file(transcribed_path, translated_path, source_lang, target_lang)
        progress_bar2.progress(100)
        st.success("Translation complete!")
    
    # Step 3: Add filler words to make speech more natural
    with st.spinner("Enhancing speech with natural filler words..."):
        progress_bar3 = st.progress(0)
        add_filler_words(translated_path, translated_filled_path, target_lang)
        progress_bar3.progress(100)
        st.success("Speech enhancement complete!")
    
    # Step 4: Merge subtitles that are close together
    with st.spinner("Merging speech segments for better flow..."):
        progress_bar4 = st.progress(0)
        subtitles = load_srt(translated_filled_path)
        merged_subtitles = merge_subtitles(subtitles)
        save_srt(merged_subtitles, output_path)
        progress_bar4.progress(100)
        st.success("Speech segment merging complete!")
    
    # Step 5: Generate audio using selected voice
    with st.spinner(f"Generating speech audio with {selected_voice_name}..."):
        progress_bar5 = st.progress(0)
        text_content = extract_text_from_srt(output_path)
        generate_audio_with_voice(
            text_content, 
            audio_path, 
            selected_voice_id,
            stability=stability,
            similarity_boost=similarity_boost
        )
        progress_bar5.progress(100)
        st.success("Audio generation complete!")
        
        # Let user hear the generated voice
        st.audio(audio_path, format="audio/mp3")
        st.caption(f"Generated audio using {selected_voice_name}")
    
    # Step 6: Adjust audio length to match SRT timeline
    with st.spinner("Adjusting audio timing to match speech segments..."):
        progress_bar6 = st.progress(0)
        adjust_audio_length_ffmpeg(audio_path, output_path, adjusted_audio_path)
        progress_bar6.progress(100)
        st.success("Audio timing adjustment complete!")
        
    # Step 7: Create lip-synced video
    with st.spinner("Creating lip-synced video (this may take several minutes)..."):
        progress_bar7 = st.progress(0)
        try:
            # Show intermediate status updates
            status_placeholder = st.empty()
            progress_bar7.progress(20)
            
            # Get the URL from the function
            video_url = create_lip_sync_video(
                input_video_path, 
                adjusted_audio_path, 
                lip_synced_video_path, 
            )
            
            status_placeholder.text("Video processing completed!")
            progress_bar7.progress(100)
            st.success("Lip-synced video created!")
            processing_successful = True
        except Exception as e:
            st.error(f"Error creating lip-synced video")
            processing_successful = False
    
    # Step 8: Crop video (new step)
    if processing_successful:
        with st.spinner("Playing Video"):
            progress_bar8 = st.progress(0)
            try:
                # If video_url is a URL, download it first
                if video_url.startswith('http'):
                    import requests
                    r = requests.get(video_url)
                    with open(lip_synced_video_path, 'wb') as f:
                        f.write(r.content)
                
                # Process the cropping
                crop_video(lip_synced_video_path, cropped_video_path, crop_top=60)
                progress_bar8.progress(100)
                # st.success("Video cropping complete!")
                
                # If we're working with URLs, we need to adjust the video_url
                if video_url.startswith('http'):
                    # Create a relative URL for the cropped video
                    video_url = cropped_video_path
            except Exception as e:
                st.error(f"Error cropping video: {e}")
                # Fallback to uncropped video
                cropped_video_path = lip_synced_video_path

    # Display results only if processing was successful
    if processing_successful:
        st.header("Results")
        
        # Create tabs for different outputs
        tab1, tab2, tab3 = st.tabs(["Lip-Synced Video", "Audio Output", "Original Input"])
        
        with tab1:
            st.subheader("Lip-Synced Video")
            
            # Display the cropped video
            if os.path.exists(cropped_video_path):
                st.video(cropped_video_path)
                st.caption(f"Lip-Synced Video with {selected_voice_name} voice ({source_lang} → {target_lang})")
                
                # If it's a local file (not a URL), provide download option
                if not video_url.startswith('http'):
                    with open(cropped_video_path, "rb") as file:
                        st.download_button(
                            label="Download video",
                            data=file,
                            file_name=os.path.basename(cropped_video_path),
                            mime="video/mp4"
                        )
                else:
                    # For URLs
                    st.markdown(f"[Click here to open the video in a new tab]({video_url})")
            else:
                st.error("video not found")
        
        with tab2:
            st.subheader(f"Generated Audio with {selected_voice_name}")
            
            # Display original generated audio
            st.audio(audio_path)
            st.caption("Original Generated Audio")
            
            # Display timing-adjusted audio
            st.audio(adjusted_audio_path)
            st.caption("Timing-Adjusted Audio")
        
        with tab3:
            st.subheader("Original Input")
            
            st.video(input_video_path)
            st.caption(f"Original {source_lang} Video Input")
            
            st.audio(input_audio_path)
            st.caption("Extracted Audio from Video")
    else:
        st.header("Processing Failed")
        st.error("The lip sync process failed due to GPU memory limitations.")
        st.markdown("""
        ### Recommended Solutions:
        1. Try a shorter video clip
        2. Reduce the video resolution before uploading
        """)
else:
    st.info("Please upload a video file and click 'Real Time Translation' to begin.")
# Footer
st.markdown("""
---
Smart Dubbing System with TTS & Lip Sync | Demo Version
""")