import os
import cv2
import numpy as np
from moviepy.editor import VideoFileClip
import shutil

class WatermarkRemover:
    def __init__(self, num_samples=30):
        self.num_samples = num_samples

    def get_watermark_bbox(self, video_path):
        try:
            clip = VideoFileClip(video_path)
            duration = clip.duration
        except Exception as e:
            print(f"Error opening video: {e}")
            return None
            
        edge_accumulator = None
        
        # Sample frames to discover static edges (watermark)
        try:
            for t in np.linspace(0.1, duration - 0.5, self.num_samples):
                frame = clip.get_frame(t)
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                # Canny edge detection
                edges = cv2.Canny(gray, 50, 150)
                if edge_accumulator is None:
                    edge_accumulator = edges.astype(np.float32)
                else:
                    edge_accumulator += edges.astype(np.float32)
        finally:
            clip.close()
                
        if edge_accumulator is None:
            return None
            
        # Average the edges across samples
        edge_accumulator /= self.num_samples
        
        # A persistent edge will have a high average value (close to 255)
        # We use a threshold to keep only edges that appear in most frames
        _, persistent_edges = cv2.threshold(edge_accumulator, 150, 255, cv2.THRESH_BINARY)
        persistent_edges = persistent_edges.astype(np.uint8)
        
        # Morphological operations to group the edges into a solid block
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
        grouped = cv2.dilate(persistent_edges, kernel, iterations=2)
        grouped = cv2.erode(grouped, kernel, iterations=1)
        
        # Find contours of the watermark
        contours, _ = cv2.findContours(grouped, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
            
        # Filter contours by size, assuming watermark is somewhat large but not the whole screen
        # We can just pick the largest static contour as the watermark
        valid_contours = []
        h_frame, w_frame = edge_accumulator.shape
        max_area = (h_frame * w_frame) * 0.25 # watermark shouldn't be larger than 25% of screen
        
        for c in contours:
            area = cv2.contourArea(c)
            if area < max_area and area > 100:
                valid_contours.append(c)
                
        if not valid_contours:
            return None
            
        largest_contour = max(valid_contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Add some padding to the bounding box
        padding = 10
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(w_frame - x, w + 2 * padding)
        h = min(h_frame - y, h + 2 * padding)
        
        return (x, y, w, h)

    def blur_watermark(self, frame, bbox):
        x, y, w, h = bbox
        roi = frame[y:y+h, x:x+w]
        
        # Apply strong Gaussian blur to obfuscate the watermark
        # The kernel size should be large and odd for a strong blur
        blurred_roi = cv2.GaussianBlur(roi, (75, 75), 0)
        
        new_frame = frame.copy()
        new_frame[y:y+h, x:x+w] = blurred_roi
        return new_frame

    def process_video(self, input_path, output_path):
        bbox = self.get_watermark_bbox(input_path)
        
        if not bbox:
            print("No watermark detected. Copying original file.")
            shutil.copy(input_path, output_path)
            return True
            
        print(f"Watermark detected at {bbox}. Blurring region...")
        try:
            clip = VideoFileClip(input_path)
            
            # Function to process each frame
            def fl(gf, t):
                frame = gf(t)
                return self.blur_watermark(frame, bbox)
                
            new_clip = clip.fl(fl)
            
            # Write the result to file
            new_clip.write_videofile(
                output_path, 
                codec="libx264", 
                audio_codec="aac"
            )
            return True
        except Exception as e:
            print(f"Error processing video: {e}")
            return False
        finally:
            if 'clip' in locals():
                clip.close()
            if 'new_clip' in locals():
                new_clip.close()
