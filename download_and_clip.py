import os
from clipper import VideoClipper

def main():
    input_video = "mr_beast_spanish.mp4"
    output_dir = "output_clips"
    base_name = "mrbeast_es"
    video_title = "Last To Leave Grocery Store, Wins $250,000" # Correct title
    
    if not os.path.exists(input_video):
        print(f"Error: {input_video} not found. Please wait for the download to finish.")
        return

    print(f"Starting clipping process for {input_video} with NEW LAYOUT...")
    clipper = VideoClipper(clip_duration=60)
    clips = clipper.generate_clips(input_video, output_dir, base_name=base_name, title=video_title)
    
    print(f"Successfully generated {len(clips)} clips in {output_dir}:")
    for clip in clips:
        print(f" - {clip}")

if __name__ == "__main__":
    main()
