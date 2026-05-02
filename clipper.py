import os
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip
import moviepy.video.fx.all as vfx

def add_overlay_text(frame, title, part_num):
    # Copy the frame so we don't overwrite MoviePy's buffers
    img = frame.copy()
    h, w, _ = img.shape
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (255, 255, 255) # white in RGB
    thickness = 3
    
    # 1. Title Text - Handle multi-line if too long
    display_title = str(title).upper()
    words = display_title.split()
    lines = []
    current_line = ""
    
    # Simple word wrapping
    max_line_len = 25 # Max characters per line
    for word in words:
        if len(current_line) + len(word) + 1 <= max_line_len:
            current_line += (word + " ")
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        lines.append(current_line.strip())

    title_scale = 1.2
    line_height = 0
    max_tw = 0
    title_line_sizes = []
    
    for line in lines:
        (tw, th), tb = cv2.getTextSize(line, font, title_scale, thickness)
        title_line_sizes.append((tw, th))
        max_tw = max(max_tw, tw)
        line_height = max(line_height, th)

    # 2. Part Text
    part_text = f"PARTE {part_num}"
    part_scale = 1.5
    (pw, ph), pb = cv2.getTextSize(part_text, font, part_scale, thickness + 1)
    
    # Calculate positions (Centered horizontally, top area)
    margin_top = 250
    line_spacing = 60 # Increased from 20 to prevent overlap
    gap_to_part = 80  # Increased from 60
    
    # Draw Background and Text for each title line
    current_y = margin_top
    bg_margin = 20
    
    for i, line in enumerate(lines):
        tw, th = title_line_sizes[i]
        tx = (w - tw) // 2
        ty = current_y + th
        
        # BG for this line
        cv2.rectangle(img, (tx - bg_margin, ty - th - bg_margin), 
                      (tx + tw + bg_margin, ty + bg_margin), (0,0,0), -1)
        # Text for this line
        cv2.putText(img, line, (tx, ty), font, title_scale, color, thickness, cv2.LINE_AA)
        
        current_y = ty + line_spacing

    # Draw Part Text below all title lines
    part_x = (w - pw) // 2
    part_y = current_y + gap_to_part + ph
    
    # Part BG
    cv2.rectangle(img, (part_x - bg_margin, part_y - ph - bg_margin), 
                  (part_x + pw + bg_margin, part_y + bg_margin), (0,0,0), -1)
    # Part Text
    cv2.putText(img, part_text, (part_x, part_y), font, part_scale, color, thickness + 1, cv2.LINE_AA)
    
    return img

class VideoClipper:
    def __init__(self, clip_duration=60, max_clips=None):
        self.clip_duration = clip_duration
        self.max_clips = max_clips
        self.target_w = 1080
        self.target_h = 1920

    def generate_clips(self, input_video, output_dir, base_name="short_clip", title="VIDEO"):
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
                main_centered = subclip

            try:
                # 2. Create the "Blurry/Dark" background
                bg = subclip.resize(height=self.target_h)
                bg = vfx.crop(bg, x_center=int(bg.w/2), y_center=int(bg.h/2), width=self.target_w, height=self.target_h)
                bg = vfx.colorx(bg, 0.3)
                
                final_clip = CompositeVideoClip([bg, main_centered.set_pos("center")])
            except Exception as e:
                print(f"Fallback to black background: {e}")
                black_bg = ColorClip(size=(self.target_w, self.target_h), color=(15,23,42)).set_duration(subclip.duration)
                final_clip = CompositeVideoClip([black_bg, main_centered.set_pos("center")])
            
            # Apply OpenCV-based Overlay
            final_clip = final_clip.fl_image(lambda frame, n=idx: add_overlay_text(frame, title, n))
            
            output_filename = f"{base_name}_{idx}.mp4"
            output_path = os.path.join(output_dir, output_filename)
            
            print(f"Writing {output_filename}...")
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

