import os
import sys
import subprocess
from clipper import VideoClipper

def download_video(url, output_filename="downloaded_video.mp4"):
    # ALWAYS delete the old file to avoid using a wrong version
    if os.path.exists(output_filename):
        os.remove(output_filename)
        
    print(f"Downloading {url} with Spanish audio (if available)...")
    
    # We use a very specific format selector that includes the ID 96-18 which we know works for MrBeast
    # and a generic one for other videos.
    cmd = [
        "./venv/bin/yt-dlp",
        "--js-runtimes", "node",
        "--remote-components", "ejs:github",
        "--audio-multistreams",
        "-f", "96-18/bestvideo+bestaudio[language^=es]/bestvideo+bestaudio[language*=es]/bestvideo+bestaudio",
        "--merge-output-format", "mp4",
        "-o", output_filename,
        url
    ]
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error downloading video: {e}")
        return False

def get_video_title(url):
    cmd = ["./venv/bin/yt-dlp", "--get-title", url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
        return "VIDEO"

def main():
    if len(sys.argv) < 2:
        print("Usage: python clip_youtube.py <YOUTUBE_URL>")
        return

    url = sys.argv[1]
    temp_video = "downloaded_video.mp4"
    output_dir = "output_clips"
    
    # 0. Get Title
    title = get_video_title(url)
    print(f"Processing: {title}")

    # 1. Download
    if download_video(url, temp_video):
        # 2. Clip
        print(f"Generating clips for {title}...")
        clipper = VideoClipper(clip_duration=60)
        
        # Clean title for filename
        safe_title = "".join([c for c in title if c.isalnum() or c==' ']).rstrip()
        base_name = safe_title.replace(" ", "_").lower()[:20]
        
        clipper.generate_clips(temp_video, output_dir, base_name=base_name, title=title)
        
        print(f"Done! Clips are in {output_dir}")
    else:
        print("Failed to process video.")

if __name__ == "__main__":
    main()
