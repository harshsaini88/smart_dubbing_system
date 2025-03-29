"""
Smart Dubbing System - Streamlit Web Application

This application translates subtitles, enhances them with natural language features,
merges them for better flow, generates speech with text-to-speech technology, and
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

# Set page configuration
st.set_page_config(
    page_title="Smart Dubbing System",
    page_icon="🎙️",
    layout="wide"
)

# App title and description
st.title("Smart Dubbing System")
st.markdown("""
This application helps you translate subtitles, enhance them with natural language features,
merge them for better flow, generate speech with text-to-speech technology, and adjust
audio timing to match the subtitles.
""")

# Create sidebar for inputs
st.sidebar.header("Input Settings")

# Create necessary directories
create_directories()

# File uploader for SRT file
uploaded_file = st.sidebar.file_uploader("Upload SRT file", type=["srt"])

# Language selection
source_lang = st.sidebar.text_input("Source Language (e.g., English)", "English")
target_lang = st.sidebar.text_input("Target Language (e.g., Spanish)", "Spanish")

# Set file paths
input_path = "srt_files/input.srt" if uploaded_file else None
translated_path = 'srt_files/translated.srt'
translated_filled_path = 'srt_files/translated_filled.srt'
output_path = 'translated_output/merged_output.srt'
audio_path = "tts_output/final_merged_output.wav"
adjusted_audio_path = "tts_output/final_merged_output.wav"

# Process button
if uploaded_file is not None:
    # Save the uploaded file temporarily
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.sidebar.success(f"File uploaded successfully!")
    
    if st.sidebar.button("Start Dubbing Process"):
        # Main processing steps with progress bars
        st.header("Processing")
        
        # Step 1: Translate subtitles
        with st.spinner("Translating subtitles..."):
            progress_bar1 = st.progress(0)
            translate_srt_file(input_path, translated_path, source_lang, target_lang)
            progress_bar1.progress(100)
            st.success("Translation complete!")
        
        # Step 2: Add filler words to make speech more natural
        with st.spinner("Enhancing speech with natural filler words..."):
            progress_bar2 = st.progress(0)
            add_filler_words(translated_path, translated_filled_path, target_lang)
            progress_bar2.progress(100)
            st.success("Speech enhancement complete!")
        
        # Step 3: Merge subtitles that are close together
        with st.spinner("Merging subtitles for better flow..."):
            progress_bar3 = st.progress(0)
            subtitles = load_srt(translated_filled_path)
            merged_subtitles = merge_subtitles(subtitles)
            save_srt(merged_subtitles, output_path)
            progress_bar3.progress(100)
            st.success("Subtitle merging complete!")
        
        # Step 4: Generate audio using Eleven Labs API
        with st.spinner("Generating speech audio from translated text..."):
            progress_bar4 = st.progress(0)
            text_content = extract_text_from_srt(output_path)
            generate_audio_with_elevenlabs(text_content, audio_path)
            progress_bar4.progress(100)
            st.success("Audio generation complete!")
        
        # Step 5: Adjust audio length to match SRT timeline
        with st.spinner("Adjusting audio timing to match subtitles..."):
            progress_bar5 = st.progress(0)
            adjust_audio_length_ffmpeg(audio_path, output_path, adjusted_audio_path)
            progress_bar5.progress(100)
            st.success("Audio timing adjustment complete!")
        
        # Display results
        st.header("Results")
        
        # Display the translated SRT content
        with open(output_path, "r", encoding="utf-8") as f:
            srt_content = f.read()
            
        col1, col2 = st.columns(2)
        
        with col1:
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
        
        with col2:
            st.subheader("Generated Audio")
            
            # Display original audio
            st.audio(audio_path)
            st.caption("Original Generated Audio")
            
            # Download button for original audio
            with open(audio_path, "rb") as f:
                st.download_button(
                    label="Download Original Audio",
                    data=f,
                    file_name="generated_audio.wav",
                    mime="audio/wav"
                )
            
            # Display timing-adjusted audio
            st.audio(adjusted_audio_path)
            st.caption("Timing-Adjusted Audio")
            
            # Download button for adjusted audio
            with open(adjusted_audio_path, "rb") as f:
                st.download_button(
                    label="Download Adjusted Audio",
                    data=f,
                    file_name="adjusted_audio.wav",
                    mime="audio/wav"
                )
else:
    st.info("Please upload an SRT file to begin the dubbing process.")

# Advanced settings (collapsible)
with st.sidebar.expander("Advanced Settings"):
    st.markdown("These settings will be implemented in future versions")
    st.slider("Voice Pitch", -10, 10, 0)
    st.slider("Speaking Rate", 0.5, 2.0, 1.0)
    st.checkbox("Generate Video with Subtitles")

# Footer
st.markdown("""
---
Smart Dubbing System | Created with Streamlit
""")