"""
Handles merging and splitting of subtitles for better flow and readability.

This module provides functions to:
1. Load SRT files into a manipulable format
2. Merge subtitles that are close together or incomplete sentences
3. Split long subtitles for better readability
4. Save the modified subtitles back to SRT format
"""
import re
from datetime import datetime, timedelta

def parse_time(timestamp):
    """
    Parse a timestamp string into a datetime object.
    
    Args:
        timestamp (str): Timestamp in format HH:MM:SS.mmm
        
    Returns:
        datetime: Datetime object representing the timestamp
    """
    return datetime.strptime(timestamp, '%H:%M:%S.%f')

def format_time(dt_obj):
    """
    Format a datetime object back to SRT timestamp format.
    
    Args:
        dt_obj (datetime): Datetime object
        
    Returns:
        str: Formatted timestamp string in format HH:MM:SS.mmm
    """
    return dt_obj.strftime('%H:%M:%S.%f')[:-3]

def is_complete_sentence(text):
    """
    Check if text ends with a sentence-ending punctuation mark.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text ends with a period, question mark, or exclamation mark
    """
    return text.strip()[-1] in {'.', '?', '!'}

def split_subtitle_text(text, max_words):
    """
    Split subtitle text into multiple lines with word limit.
    
    Args:
        text (str): Text to split
        max_words (int): Maximum words per line
        
    Returns:
        list: List of text strings, each with no more than max_words
    """
    words = text.split()
    splits = [words[i:i + max_words] for i in range(0, len(words), max_words)]
    return [' '.join(split) for split in splits]

def distribute_time(start_time, end_time, num_splits):
    """
    Distribute time evenly between start_time and end_time across num_splits.
    
    Args:
        start_time (str): Start timestamp
        end_time (str): End timestamp
        num_splits (int): Number of splits to create
        
    Returns:
        list: List of (start, end) timestamp tuples
    """
    start = parse_time(start_time)
    end = parse_time(end_time)
    total_duration = (end - start) / num_splits
    time_intervals = [(start + i * total_duration, start + (i + 1) * total_duration) for i in range(num_splits)]
    return [(format_time(interval[0]), format_time(interval[1])) for interval in time_intervals]

def merge_subtitles(subtitles, min_words=4, max_words=15):
    """
    Merge subtitles intelligently based on word count and sentence completeness.
    
    Args:
        subtitles (list): List of subtitle dictionaries
        min_words (int): Minimum words per subtitle
        max_words (int): Maximum words per subtitle
        
    Returns:
        list: Merged subtitle dictionaries
    """
    print(f"Merging subtitles with parameters: min_words={min_words}, max_words={max_words}")
    
    merged = []
    current = None

    for subtitle in subtitles:
        if not current:
            current = subtitle
        else:
            curr_words = len(current['text'].split())
            next_words = len(subtitle['text'].split())

            # Determine whether to merge based on word count and sentence completeness
            if (curr_words + next_words) <= max_words or not is_complete_sentence(current['text']):
                current['text'] += ' ' + subtitle['text']
                current['end_time'] = subtitle['end_time']
            else:
                if curr_words >= min_words:
                    merged.append(current)
                    current = subtitle
                else:
                    current['text'] += ' ' + subtitle['text']
                    current['end_time'] = subtitle['end_time']

            # Split if current subtitle exceeds max_words
            if len(current['text'].split()) > max_words:
                split_texts = split_subtitle_text(current['text'], max_words)
                time_intervals = distribute_time(current['start_time'], current['end_time'], len(split_texts))
                
                for i, (text, (start, end)) in enumerate(zip(split_texts, time_intervals)):
                    if i == 0:
                        current['text'] = text
                        current['start_time'], current['end_time'] = start, end
                    else:
                        # Create new subtitle entry for split text with distributed time
                        merged.append(current)
                        current = {
                            'index': current['index'] + 1,
                            'start_time': start,
                            'end_time': end,
                            'text': text
                        }

    # Append the last entry if it exists
    if current:
        merged.append(current)

    print(f"Merged {len(subtitles)} subtitles into {len(merged)} subtitles")
    return merged

def load_srt(file_path):
    """
    Load SRT file and parse into a list of subtitle dictionaries.
    
    Args:
        file_path (str): Path to SRT file
        
    Returns:
        list: List of subtitle dictionaries with keys: index, start_time, end_time, text
    """
    print(f"Loading SRT file: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    entries = re.split(r'\n\n', content.strip())
    subtitles = []
    
    for entry in entries:
        lines = entry.split('\n')
        if len(lines) >= 2:  # Ensure valid entry with at least index and timestamp
            try:
                subtitles.append({
                    'index': int(lines[0]),
                    'start_time': lines[1].split(' --> ')[0],
                    'end_time': lines[1].split(' --> ')[1],
                    'text': ' '.join(lines[2:])
                })
            except (ValueError, IndexError) as e:
                print(f"Error parsing entry: {entry}\nError: {e}")
                continue
    
    print(f"Loaded {len(subtitles)} subtitles")
    return subtitles

def save_srt(subtitles, output_path):
    """
    Save subtitle dictionaries back to SRT format.
    
    Args:
        subtitles (list): List of subtitle dictionaries
        output_path (str): Path to save SRT file
    """
    print(f"Saving {len(subtitles)} subtitles to {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as file:
        for i, subtitle in enumerate(subtitles, start=1):
            file.write(f"{i}\n{subtitle['start_time']} --> {subtitle['end_time']}\n{subtitle['text']}\n\n")
    
    print(f"Saved SRT file to {output_path}")