"""
Smart Dubbing System - Streamlit Web Application

This application supports audio file input for automatic transcription and subtitling.
It translates subtitles, enhances them with natural language features,
merges them for better flow, generates speech with voice cloning technology, and
adjusts audio timing to match the subtitles.

Usage:
    streamlit run app.py
"""

import os
import time
import streamlit as st
from tqdm import tqdm
from dotenv import load_dotenv

# Import utility modules
from utils.translation import translate_srt_file
from utils.filler import add_filler_words
from utils.merge import load_srt, save_srt, merge_subtitles
from utils.speedometer import adjust_audio_length_ffmpeg
from utils.tts import create_voice_clone, generate_audio_with_cloned_voice, extract_text_from_srt, extract_sample_audio, delete_cloned_voice
from utils.transcription import generate_srt_from_audio

# Load environment variables
load_dotenv()

def create_directories():
    """Create necessary directories for output files"""
    directories = [
        'audio_input',
        'audio_samples',
        'srt_files',
        'translated_output',
        'tts_output'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Set page configuration
st.set_page_config(
    page_title="Smart Dubbing System with Voice Cloning",
    page_icon="🎙️",
    layout="wide"
)

# App title and description
st.title("Smart Dubbing System with Voice Cloning")
st.markdown("""
This application helps you dub audio content from one language to another while preserving the original voice:
- Upload an audio file for automatic transcription and voice cloning
- Translate subtitles to your desired language
- Enhance them with natural language features
- Generate speech with the cloned voice
- Adjust audio timing to match the subtitles
""")

# Check for API key
if not os.getenv("ELEVEN_LABS_API_KEY"):
    st.error("⚠️ Eleven Labs API key not found. Please set the ELEVEN_LABS_API_KEY environment variable or add it to your .env file.")
    st.info("Get an API key from [Eleven Labs](https://elevenlabs.io)")
    st.stop()

# Create sidebar for inputs
st.sidebar.header("Input Settings")

# Create necessary directories
create_directories()

# File uploader for audio
uploaded_file = st.sidebar.file_uploader("Upload Audio file", type=["mp3", "wav", "m4a", "flac"])
input_audio_path = "audio_input/input_audio.wav" if uploaded_file else None
sample_audio_path = "audio_samples/voice_sample.mp3"

# Language selection
source_lang = st.sidebar.text_input("Source Language (e.g., English)", "English")
target_lang = st.sidebar.text_input("Target Language (e.g., Spanish)", "Spanish")

# Voice cloning settings
st.sidebar.header("Voice Cloning Settings")
voice_name = st.sidebar.text_input("Name for cloned voice", "Smart Dubbing Voice")
sample_duration = st.sidebar.slider("Voice sample duration (seconds)", 10, 120, 30, 
                               help="Length of audio sample to use for cloning. 30-60 seconds recommended.")
similarity_boost = st.sidebar.slider("Voice similarity", 0.0, 1.0, 0.75, 
                                help="Higher values make the generated voice sound more like the original")
stability = st.sidebar.slider("Voice stability", 0.0, 1.0, 0.5, 
                         help="Higher values make the voice more consistent but less expressive")

# Set file paths
transcribed_path = "srt_files/transcribed.srt"
translated_path = 'srt_files/translated.srt'
translated_filled_path = 'srt_files/translated_filled.srt'
output_path = 'translated_output/merged_output.srt'
audio_path = "tts_output/final_merged_output.wav"
adjusted_audio_path = "tts_output/adjusted_output.wav"

# Process button
if uploaded_file is not None:
    # Save the uploaded file temporarily
    with open(input_audio_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success(f"Audio file uploaded successfully!")
    
    # Display Whisper model selection
    whisper_model = st.sidebar.selectbox(
        "Select Whisper Model",
        ["tiny", "base", "small", "medium", "large"],
        index=1,
        help="Larger models are more accurate but slower and require more memory"
    )
    
    if st.sidebar.button("Start Dubbing Process"):
        # Main processing steps with progress bars
        st.header("Processing")
        
        # Step 1: Transcribe audio to SRT
        with st.spinner("Transcribing audio to SRT..."):
            progress_bar1 = st.progress(0)
            generate_srt_from_audio(input_audio_path, transcribed_path, whisper_model, source_lang)
            progress_bar1.progress(100)
            st.success("Transcription complete!")
        
        # Step 2: Translate subtitles
        with st.spinner("Translating subtitles..."):
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
        with st.spinner("Merging subtitles for better flow..."):
            progress_bar4 = st.progress(0)
            subtitles = load_srt(translated_filled_path)
            merged_subtitles = merge_subtitles(subtitles)
            save_srt(merged_subtitles, output_path)
            progress_bar4.progress(100)
            st.success("Subtitle merging complete!")
        
        # Step 5: Extract voice sample for cloning
        with st.spinner("Extracting voice sample for cloning..."):
            progress_bar5 = st.progress(0)
            sample_audio = extract_sample_audio(input_audio_path, sample_audio_path, sample_duration)
            progress_bar5.progress(100)
            st.success("Voice sample extracted!")
            
            # Let user hear the voice sample
            st.audio(sample_audio_path, format="audio/mp3")
            st.caption("Voice sample that will be used for cloning")
        
        # Step 6: Clone voice from the sample
        with st.spinner("Cloning voice from sample audio..."):
            progress_bar6 = st.progress(0)
            voice_id = create_voice_clone(sample_audio_path, voice_name)
            if not voice_id:
                st.error("Failed to clone voice. Please check your API key and try again.")
                st.stop()
            progress_bar6.progress(100)
            st.success(f"Voice successfully cloned! Voice ID: {voice_id}")
        
        # Step 7: Generate audio using cloned voice
        with st.spinner("Generating speech audio with cloned voice..."):
            progress_bar7 = st.progress(0)
            text_content = extract_text_from_srt(output_path)
            voice_settings = {
                "stability": stability,
                "similarity_boost": similarity_boost
            }
            generate_audio_with_cloned_voice(text_content, audio_path, voice_id)
            progress_bar7.progress(100)
            st.success("Audio generation with cloned voice complete!")
        
        # Step 8: Adjust audio length to match SRT timeline
        with st.spinner("Adjusting audio timing to match subtitles..."):
            progress_bar8 = st.progress(0)
            adjust_audio_length_ffmpeg(audio_path, output_path, adjusted_audio_path)
            progress_bar8.progress(100)
            st.success("Audio timing adjustment complete!")
        
        # Clean up the cloned voice (optional)
        cleanup = st.checkbox("Delete cloned voice from Eleven Labs after processing", value=True,
                        help="Recommended to avoid hitting voice limits on your Eleven Labs account")
        if cleanup:
            with st.spinner("Cleaning up resources..."):
                delete_cloned_voice(voice_id)
                st.success("Cloned voice deleted from Eleven Labs")
        
        # Display results
        st.header("Results")
        
        # Create tabs for different outputs
        tab1, tab2, tab3 = st.tabs(["Generated Subtitles", "Audio Output", "Original Input"])
        
        with tab1:
            # Display the translated SRT content
            with open(output_path, "r", encoding="utf-8") as f:
                srt_content = f.read()
            
            st.subheader("Translated Subtitles")
            st.text_area("SRT Content", srt_content, height=300)
            
            # Download button for SRT
            with open(output_path, "rb") as f:
                st.download_button(
                    label="Download SRT File",
                    data=f,
                    file_name="translated_subtitles.srt",
                    mime="text/plain"
                )
                
            # Show the original transcription
            with open(transcribed_path, "r", encoding="utf-8") as f:
                original_srt = f.read()
            
            st.subheader("Original Transcription")
            st.text_area("Original SRT", original_srt, height=300)
            
            # Download button for original transcription
            with open(transcribed_path, "rb") as f:
                st.download_button(
                    label="Download Original Transcription",
                    data=f,
                    file_name="original_transcription.srt",
                    mime="text/plain"
                )
        
        with tab2:
            st.subheader("Generated Audio with Cloned Voice")
            
            # Display original cloned voice audio
            st.audio(audio_path)
            st.caption("Original Generated Audio with Cloned Voice")
            
            # Download button for original audio
            with open(audio_path, "rb") as f:
                st.download_button(
                    label="Download Cloned Voice Audio",
                    data=f,
                    file_name="cloned_voice_audio.wav",
                    mime="audio/wav"
                )
            
            # Display timing-adjusted audio
            st.audio(adjusted_audio_path)
            st.caption("Timing-Adjusted Audio with Cloned Voice")
            
            # Download button for adjusted audio
            with open(adjusted_audio_path, "rb") as f:
                st.download_button(
                    label="Download Adjusted Cloned Voice Audio",
                    data=f,
                    file_name="adjusted_cloned_voice_audio.wav",
                    mime="audio/wav"
                )
        
        with tab3:
            st.subheader("Original Input")
            st.audio(input_audio_path)
            st.caption("Original Audio Input")
            
            # Voice sample used for cloning
            st.audio(sample_audio_path)
            st.caption("Voice Sample Used for Cloning")
else:
    st.info("Please upload an audio file to begin the voice cloning and dubbing process.")

# Advanced settings (collapsible)
with st.sidebar.expander("Advanced Settings"):
    st.markdown("Transcription Settings")
    word_level_timestamps = st.checkbox("Word-level timestamps", value=False, 
                                     help="Enable for more precise timing (may be slower)")
    compute_type = st.radio("Compute Type", ["float16", "float32", "int8"], 
                         index=0, help="Lower precision is faster but may be less accurate")
    
    st.markdown("Output Settings")
    generate_video = st.checkbox("Generate Video with Subtitles")

# Footer
st.markdown("""
---
Smart Dubbing System with Voice Cloning | Created with Streamlit
""")