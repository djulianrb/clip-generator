import argparse
import sys
from dubber import VideoDubber

def main():
    parser = argparse.ArgumentParser(description="AI Video Dubber (English to Spanish, Spanish to English)")
    parser.add_argument("-i", "--input", required=True, help="Path to input MP4 video")
    parser.add_argument("-o", "--output", required=True, help="Path to output MP4 video")
    parser.add_argument("--source", choices=["en", "es"], default="en", help="Source language (en or es)")
    parser.add_argument("--target", choices=["en", "es"], default="es", help="Target language (en or es)")

    args = parser.parse_args()

    if args.source == args.target:
        print("Source and target language must be different.")
        sys.exit(1)

    print(f"Initializing video dubber from {args.source} to {args.target}...")
    dubber = VideoDubber(source_lang=args.source, target_lang=args.target)
    dubber.process_video(args.input, args.output)

if __name__ == "__main__":
    main()
