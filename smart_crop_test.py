import cv2
import numpy as np
from moviepy.editor import VideoFileClip

def get_salient_centers(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (21, 21), 0)
    edges = cv2.Canny(blurred, 30, 150)
    dilated = cv2.dilate(edges, None, iterations=3)
    
    contours, _ = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    centers = []
    height, width = frame.shape[:2]
    min_area = (width * height) * 0.05
    
    for c in contours:
        if cv2.contourArea(c) > min_area:
            m = cv2.moments(c)
            if m["m00"] != 0:
                cx = int(m["m10"] / m["m00"])
                centers.append(cx)
                
    centers.sort()
    
    if not centers:
        return [width // 2]
        
    return centers

def process_video(input_path, output_path, duration=10):
    video = VideoFileClip(input_path).subclip(0, duration)
    fps = video.fps
    chunk_duration = 2.0
    w, h = video.size
    crop_w = int(h * 9 / 16)
    current_x = w / 2

    def process_frame(get_frame, t):
        nonlocal current_x
        frame = get_frame(t)
        centers = get_salient_centers(frame)
        
        # Determine focus
        chunk_idx = int(t / chunk_duration)
        time_in_chunk = t % chunk_duration
        num_centers = len(centers)
        center_idx = int((time_in_chunk / chunk_duration) * num_centers)
        
        # Clamp index
        center_idx = min(center_idx, num_centers - 1)
        target_center = centers[center_idx]
        
        # Smooth
        current_x += (target_center - current_x) * 0.1
        
        x1 = int(current_x - crop_w / 2)
        x2 = int(x1 + crop_w)
        
        if x2 > w:
            x2 = w
            x1 = w - crop_w
        if x1 < 0:
            x1 = 0
            x2 = crop_w
            
        cropped = frame[:, x1:x2]
        
        try:
            resized = cv2.resize(cropped, (1080, 1920))
            return resized
        except Exception as e:
            print("Resize error:", e)
            return cropped

    modified_clip = video.fl(process_frame)
    modified_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", preset="ultrafast", threads=4)

if __name__ == "__main__":
    process_video("The_Life_and_Legend_of_Son_Goku.mp4", "test_output.mp4", duration=10)
