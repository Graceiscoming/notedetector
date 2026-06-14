import os
import yt_dlp

def download_youtube_audio(url, output_dir, file_name="youtube_audio"):
    """
    Downloads the highest quality audio from a YouTube URL and converts it to MP3.
    Returns the absolute path to the downloaded MP3 file.
    """
    print(f"[YT] Downloading audio from {url}...")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    output_template = os.path.join(output_dir, f"{file_name}.%(ext)s")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'extractor_args': {'youtube': {'player_client': ['android']}},
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        raise Exception(f"Failed to download YouTube audio: {str(e)}")
        
    final_path = os.path.join(output_dir, f"{file_name}.mp3")
    
    if not os.path.exists(final_path):
        raise Exception("YouTube download completed, but MP3 file not found.")
        
    print(f"[YT] Download successful: {final_path}")
    return final_path
