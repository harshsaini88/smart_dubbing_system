# Smart Dubbing System with Voice Cloning

A comprehensive web-based system for transcribing, translating, enhancing, and creating dubbed audio from original content with voice cloning technology.

## Features

- Audio file input for automatic transcription
- Voice sample extraction for voice cloning
- Subtitle transcription using OpenAI Whisper models
- Subtitle translation between languages
- Natural language enhancement with filler words
- Smart subtitle merging for better flow
- Text-to-speech generation using Eleven Labs voice cloning API
- Audio timing adjustment to match subtitle timing

## Setup

1. Clone this repository
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and add your API keys:
   ```
   cp .env.example .env
   ```
4. Edit the `.env` file with your OpenAI and Eleven Labs API keys
5. Ensure FFmpeg is installed and available in your system PATH

## Usage

Run the Streamlit web application:
```
streamlit run app.py --server.fileWatcherType none
```

Follow the interface to:
1. Upload an audio file for transcription and voice cloning
2. Specify the source language
3. Specify the target language for translation
4. Configure voice cloning settings
5. Select the Whisper model for transcription
6. Start the dubbing process

The system will:
1. Transcribe your audio file to subtitles
2. Translate your subtitles
3. Add natural filler words
4. Merge subtitles for better flow
5. Extract a voice sample from your input audio
6. Clone the voice using Eleven Labs API
7. Generate audio using the cloned voice
8. Adjust audio timing to match the subtitles

## Output Files

- Transcribed SRT: `srt_files/transcribed.srt`
- Translated SRT: `srt_files/translated.srt`
- Enhanced SRT: `srt_files/translated_filled.srt`
- Final Merged SRT: `translated_output/merged_output.srt`
- Generated Audio: `tts_output/final_merged_output.wav`
- Adjusted Audio: `tts_output/adjusted_output.wav`

## Advanced Settings

The application provides advanced settings for:
- Word-level timestamps
- Compute type selection (float16, float32, int8)
- Optional video generation with subtitles

## Requirements

- Python 3.7+
- FFmpeg (must be installed and available in system PATH)
- OpenAI API key
- Eleven Labs API key
- Streamlit
