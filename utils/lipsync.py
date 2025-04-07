import os
import requests
import time
import urllib.request
from google.cloud import storage

def create_lip_sync_video(input_video_path, input_audio_path, output_video_path, retain_original_audio=True):
    """
    Create a lip-synced video using Sync Labs API
    
    Args:
        input_video_path (str): Path to the input video file
        input_audio_path (str): Path to the audio file with speech
        output_video_path (str): Path where the lip-synced video will be saved
        retain_original_audio (bool): Whether to retain original background sounds
    
    Returns:
        str: Path to the output video file or download URL
    """
    # Get API key from environment variable
    api_key = os.getenv("SYNC_LABS_API_KEY")
    if not api_key:
        raise ValueError("SYNC_LABS_API_KEY environment variable not set")
    
    # Set up the bucket name
    google_cloud_bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET", "your_default_bucket_name")
    
    # Initialize Google Cloud Storage client
    client = storage.Client()
    
    try:
        # Upload files to Google Cloud Storage
        video_url = upload_to_gcs(client, input_video_path, google_cloud_bucket_name)
        audio_url = upload_to_gcs(client, input_audio_path, google_cloud_bucket_name)
        
        # Submit lip sync job
        print("Starting lip sync generation job...")
        job_id = submit_generation(api_key, video_url, audio_url)
        
        # Poll for job completion and download result
        output_video_url = poll_job(api_key, job_id)
        
        # # Download the file
        # print(f"Downloading to {output_video_path}...")
        # urllib.request.urlretrieve(download_url, output_video_path)
        # print(f"Downloaded successfully to {output_video_path}")
        
        return output_video_url
        
    except Exception as e:
        print(f"Error in create_lip_sync_video: {str(e)}")
        raise

def upload_to_gcs(client, local_file_path, bucket_name):
    """Upload a file to Google Cloud Storage and return signed URL"""
    file_name = os.path.basename(local_file_path)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    
    print(f"Uploading {file_name} to Google Cloud Storage...")
    blob.upload_from_filename(local_file_path)
    
    # Generate a signed URL (valid for 2 hours)
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=7200,  # 2 hours
        method="GET"
    )
    
    print(f"File uploaded successfully. Signed URL: {signed_url}")
    return signed_url

def submit_generation(api_key, video_url, audio_url):
    """Submit a lip sync generation job to Sync Labs API"""
    api_url = "https://api.sync.so/v2/generate"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "lipsync-1.9.0-beta",
        "options": {
            "output_format": "mp4"
        },
        "input": [
            {"type": "video", "url": video_url},
            {"type": "audio", "url": audio_url}
        ]
    }

    response = requests.post(api_url, json=payload, headers=headers, timeout=30)
    if response.status_code == 201:
        print("Generation submitted successfully, job id:", response.json()["id"])
        return response.json()["id"]
    else:
        print(response.text)
        raise Exception(f"Failed to submit generation: {response.status_code}")

def poll_job(api_key, job_id):
    """Poll for job completion and return download URL"""
    api_url = "https://api.sync.so/v2/generate"
    poll_url = f"{api_url}/{job_id}"
    headers = {"x-api-key": api_key}
    
    while True:
        response = requests.get(poll_url, headers=headers, timeout=10)
        try:
            result = response.json()
            status = result["status"]
        except:
            print(response.text)
            raise Exception(f"Failed to poll job: {response.status_code}")
    
        terminal_statuses = ['COMPLETED', 'FAILED', 'REJECTED', 'CANCELLED']
        if status in terminal_statuses:
            if status == 'COMPLETED':
                generated_video_url = result["outputUrl"]
                print(f"Job {job_id} completed!")
                print(f"Generated video URL: {generated_video_url}")
                return generated_video_url
            else:
                print(f"Job {job_id} failed with status: {status}")
                print(response.text)
                raise Exception(f"Lip sync job failed with status: {status}")
        else:
            print(f"Job status: {status}. Waiting...")
            time.sleep(10)