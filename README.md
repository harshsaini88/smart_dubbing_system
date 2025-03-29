# Smart Dubbing System

A comprehensive system for translating, enhancing, and creating dubbed audio from subtitle files.

## Features

- Subtitle translation between languages
- Natural language enhancement with filler words
- Smart subtitle merging for better flow
- Text-to-speech generation using Eleven Labs API
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

## Usage

Run the main script:
```
python main.py
```

Follow the prompts to:
1. Enter the path to your SRT subtitle file
2. Specify the source language
3. Specify the target language for translation

The system will:
1. Translate your subtitles
2. Add natural filler words
3. Merge subtitles for better flow
4. Generate audio using Eleven Labs TTS
5. Adjust audio timing to match the subtitles

## Output Files

- Translated SRT: `translated_output/merged_output.srt`
- Generated Audio: `tts_output/final_merged_output.wav`
- Adjusted Audio: `tts_output/output_adjusted_audio.wav`

## Requirements

- Python 3.7+
- FFmpeg (must be installed and available in system PATH)
- OpenAI API key
- Eleven Labs API key