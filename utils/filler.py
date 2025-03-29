"""
Handles addition of filler words to make speech sound more natural.

This module adds appropriate filler words to single-word subtitles
to create a more natural-sounding speech pattern.
"""
import openai
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_filler_word(word, language="English"):
    """
    Generate a suitable filler word to place before the given word.
    
    Args:
        word (str): The word to precede with a filler
        language (str): The language of the word
        
    Returns:
        str or None: A suitable filler word or None if generation fails
    """
    prompt = f"Suggest a suitable natural filler word in {language} before '{word}'. Return only the filler word."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Filler word error: {e}")
        return None

def add_filler_words(input_path, output_path, language="English"):
    """
    Add filler words to single-word subtitles in an SRT file.
    
    Args:
        input_path (str): Path to input SRT file
        output_path (str): Path to save enhanced SRT file
        language (str): Language of the subtitles
    """
    print(f"Adding filler words to enhance natural speech in {language}...")
    
    with open(input_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    enhanced_content = []
    single_word_count = 0
    filler_added_count = 0
    
    for line in lines:
        # Keep subtitle numbers and timestamps unchanged
        if re.match(r'^\d+$', line.strip()) or re.match(r'^\d{2}:\d{2}:\d{2}.\d{3} --> \d{2}:\d{2}:\d{2}.\d{3}$', line.strip()):
            enhanced_content.append(line)
        # Add filler words to single-word subtitle text
        elif line.strip():
            words = line.strip().split()
            if len(words) == 1:
                single_word_count += 1
                filler = get_filler_word(words[0], language)
                if filler:
                    enhanced_content.append(f"{filler} {words[0]}\n")
                    filler_added_count += 1
                else:
                    enhanced_content.append(line)
            else:
                enhanced_content.append(line)
        # Keep empty lines unchanged
        else:
            enhanced_content.append(line)

    # Write enhanced content to output file
    with open(output_path, 'w', encoding='utf-8') as output_file:
        output_file.writelines(enhanced_content)
    
    print(f"Added {filler_added_count} filler words to {single_word_count} single-word subtitles")
    print(f"Enhanced subtitles saved to {output_path}")