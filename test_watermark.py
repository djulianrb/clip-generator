from watermark import WatermarkRemover

def test():
    video_path = "/Users/duber.rodriguez/Desktop/clip-generator/The_Life_and_Legend_of_Son_Goku.mp4"
    output_path = "/Users/duber.rodriguez/Desktop/clip-generator/test_clean_Goku.mp4"
    
    print(f"Testing watermark removal on {video_path}")
    remover = WatermarkRemover(num_samples=20)
    
    bbox = remover.get_watermark_bbox(video_path)
    if bbox:
        print(f"Detected watermark bound: {bbox}")
        remover.process_video(video_path, output_path)
        print(f"Result saved to {output_path}")
    else:
        print("No watermark detected!")

if __name__ == "__main__":
    test()
