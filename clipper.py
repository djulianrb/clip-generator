import os
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip
import moviepy.video.fx.all as vfx

class VideoClipper:
    def __init__(self, clip_duration=45, max_clips=4):
        self.clip_duration = clip_duration
        self.max_clips = max_clips
        self.target_w = 1080
        self.target_h = 1920

    def generate_clips(self, input_video, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        video = VideoFileClip(input_video)
        total_duration = video.duration
        
        clips_generated = []
        start = 0
        idx = 1
        
        print(f"Total video duration: {total_duration}s. Generating clips of {self.clip_duration}s...")
        
        while start + self.clip_duration <= total_duration:
            end = start + self.clip_duration
            
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
                final_clip = CompositeVideoClip([bg, main_centered.set_pos("center")])
            except Exception as e:
                print(f"Fallback to black background: {e}")
                # Fallback to dark solid background if background generation fails
                black_bg = ColorClip(size=(self.target_w, self.target_h), color=(15,23,42)).set_duration(self.clip_duration)
                final_clip = CompositeVideoClip([black_bg, main_centered.set_pos("center")])
            
            output_filename = f"short_clip_{idx}.mp4"
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
            if idx > self.max_clips: 
                break
                
        video.close()
        return clips_generated
