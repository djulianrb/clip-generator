import os
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip
import moviepy.video.fx.all as vfx

def add_part_text(frame, part_num):
    # Copy the frame so we don't overwrite MoviePy's buffers
    img = frame.copy()
    text = f"Parte {part_num}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.5
    thickness = 3
    color = (255, 255, 255) # white in RGB
    bg_color = (0, 0, 0) # black in RGB
    
    # Calculate text size and background rectangle size
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    margin = 20
    x, y = 40, 40 # Offset from top-left
    
    rect_w = text_w + margin * 2
    rect_h = text_h + margin * 2
    
    # Draw black rectangle background
    cv2.rectangle(img, (x, y), (x + rect_w, y + rect_h), bg_color, -1)
    
    # Draw white text
    cv2.putText(img, text, (x + margin, y + margin + text_h), font, font_scale, color, thickness, cv2.LINE_AA)
    
    return img

class VideoClipper:
    def __init__(self, clip_duration=60, max_clips=None):
        self.clip_duration = clip_duration
        self.max_clips = max_clips
        self.target_w = 1080
        self.target_h = 1920

    def generate_clips(self, input_video, output_dir, base_name="short_clip"):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        video = VideoFileClip(input_video)
        total_duration = video.duration
        
        clips_generated = []
        start = 0
        idx = 1
        
        print(f"Total video duration: {total_duration}s. Generating clips of {self.clip_duration}s...")
        
        while start < total_duration:
            end = min(start + self.clip_duration, total_duration)
            if end - start < 1.0:  # Skip tiny leftovers less than 1 second
                break
            
            subclip = video.subclip(start, end)
            
            # Format to 9:16 vertical
            try:
                # 1. Resize main video to fit the 1080 width exactly
                main_centered = subclip.resize(width=self.target_w)
            except Exception as e:
                print(f"Error resizing main_centered: {e}")
                # Fallback to original subclip if resize fails
                main_centered = subclip

            try:
                # 2. Create the "Blurry/Dark" background using the same frame
                bg = subclip.resize(height=self.target_h)
                bg = vfx.crop(bg, x_center=int(bg.w/2), y_center=int(bg.h/2), width=self.target_w, height=self.target_h)
                bg = vfx.colorx(bg, 0.3)
                # Ensure the background is at least target width. If resize/crop missed, we can fallback.
                
                final_clip = CompositeVideoClip([bg, main_centered.set_pos("center")])
            except Exception as e:
                print(f"Fallback to black background: {e}")
                # Fallback to dark solid background if background generation fails
                black_bg = ColorClip(size=(self.target_w, self.target_h), color=(15,23,42)).set_duration(self.clip_duration)
                final_clip = CompositeVideoClip([black_bg, main_centered.set_pos("center")])
            
            # Apply OpenCV-based Text Overlay for "Parte X"
            final_clip = final_clip.fl_image(lambda frame, num=idx: add_part_text(frame, num))
            
            output_filename = f"{base_name}_{idx}.mp4"
            output_path = os.path.join(output_dir, output_filename)
            
            print(f"Writing {output_filename}...")
            # Write file
            final_clip.write_videofile(
                output_path, 
                codec="libx264", 
                audio_codec="aac", 
                logger=None, 
                threads=4, 
                preset="ultrafast"
            )
            clips_generated.append(output_filename)
            
            start += self.clip_duration
            idx += 1
            if self.max_clips is not None and idx > self.max_clips: 
                break
                
        video.close()
        return clips_generated
