import cv2
from moviepy.editor import VideoFileClip
from clipper import get_primary_salient_center

def test_centers(video_path, frames_to_check=50):
    video = VideoFileClip(video_path)
    w, h = video.size
    print(f"Video size: {w}x{h}")
    
    centers = []
    for i in range(frames_to_check):
        t = i / video.fps
        frame = video.get_frame(t)
        cx = get_primary_salient_center(frame)
        centers.append(cx)
        
    print(f"Centers for first {frames_to_check} frames:")
    print(centers)
    print(f"Average center: {sum(centers)/len(centers):.2f}")
    print(f"Min center: {min(centers)}, Max center: {max(centers)}")
    
test_centers('The_Life_and_Legend_of_Son_Goku.mp4', 30)
