import cv2
from moviepy.editor import VideoFileClip
import numpy as np

def test():
    video = VideoFileClip('The_Life_and_Legend_of_Son_Goku.mp4')
    frame = video.get_frame(0)
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (21, 21), 0)
    edges = cv2.Canny(blurred, 30, 150)
    
    # Calculate moments of the edge image directly
    M = cv2.moments(edges)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        print(f"Center of Mass of ALL edges: cx={cx}, cy={cy}")

    width = frame.shape[1]
    print(f"Video center: cx={width//2}")

test()
