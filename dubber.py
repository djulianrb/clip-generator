import os
import subprocess
import asyncio
import whisper
import edge_tts
import ssl

# Workaround for macOS SSL certificate errors when downloading Whisper models
ssl._create_default_https_context = ssl._create_unverified_context
from moviepy.editor import VideoFileClip, AudioFileClip
from deep_translator import GoogleTranslator
from pydub import AudioSegment

class VideoDubber:
    def __init__(self, source_lang='en', target_lang='es'):
        self.source_lang = source_lang
        self.target_lang = target_lang
        
        # Whisper expects 'en' or 'es' for language
        self.whisper_lang = source_lang
        
        # Voices for TTS
        self.tts_voices = {
            'en': 'en-US-GuyNeural',      # Popular natural English male voice
            'es': 'es-ES-AlvaroNeural'    # Popular natural Spanish male voice
        }
        
        print("Loading Whisper Speech-to-Text model (this may take a moment on first run)...")
        self.model = whisper.load_model("base")

    def extract_audio(self, video_path, output_audio_path):
        print(f"Extracting audio from {video_path}...")
        try:
            video = VideoFileClip(video_path)
            if video.audio is None:
                raise ValueError("The provided video has no audio track.")
            video.audio.write_audiofile(output_audio_path, logger=None)
            video.close()
            print("Audio extraction successful.")
        except Exception as e:
            print(f"Error extracting audio: {e}")
            raise

    def transcribe(self, audio_path):
        print("Transcribing audio...")
        result = self.model.transcribe(audio_path, language=self.whisper_lang, word_timestamps=False)
        return result['segments']

    def translate_text(self, text):
        translator = GoogleTranslator(source=self.source_lang, target=self.target_lang)
        translated = translator.translate(text)
        return translated

    async def generate_tts(self, text, output_path):
        voice = self.tts_voices.get(self.target_lang, 'en-US-GuyNeural')
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    def fit_audio_natural(self, input_path, output_path, max_duration):
        """
        Keeps audio at natural speed, automatically truncating internal silences.
        Only speeds up if it strictly exceeds max_duration (to prevent overlapping the next segment).
        """
        try:
            from pydub.silence import detect_nonsilent
            audio = AudioSegment.from_file(input_path)
            
            # 1. Remove internal silences to compress naturally without altering pitch/speed
            # Using silence threshold relative to the audio's volume.
            non_silent_ranges = detect_nonsilent(audio, min_silence_len=150, silence_thresh=audio.dBFS - 20)
            if non_silent_ranges:
                stripped = audio[:0] # Empty audio
                for start_, end_ in non_silent_ranges:
                    # add small crossfade or just append
                    stripped += audio[start_:end_]
                audio = stripped
            
            audio.export(input_path, format="mp3") # overwrite with stripped audio
            
            original_duration = len(audio) / 1000.0  # seconds
            
            # 2. If it fits perfectly within the allocated time before the next dialogue, keep it natural!
            if original_duration <= max_duration:
                audio.export(output_path, format="wav")
                return
                
            # 3. Time stretch ONLY when necessary (to avoid bleeding into the next line)
            ratio = original_duration / max_duration
            
            filters = []
            temp_ratio = ratio
            while temp_ratio > 100.0:
                filters.append("atempo=100.0")
                temp_ratio /= 100.0
            
            filters.append(f"atempo={temp_ratio:.4f}")
            filter_str = ",".join(filters)
            
            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-filter:a", filter_str,
                output_path
            ]
            
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            
        except Exception as e:
            print(f"Error adjusting audio: {e}. Padding with silence instead.")
            AudioSegment.silent(duration=int(max_duration * 1000)).export(output_path, format="wav")

    def process_video(self, input_video, output_video):
        temp_dir = "temp_dub"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 1. Extract audio
        original_audio = os.path.join(temp_dir, "original_audio.wav")
        self.extract_audio(input_video, original_audio)
        
        # 2. Transcribe
        segments = self.transcribe(original_audio)
        print(f"Found {len(segments)} spoken segments.")
        
        # Create a silent canvas matching the exact duration of the original audio
        orig_audio_seg = AudioSegment.from_file(original_audio)
        final_audio = AudioSegment.silent(duration=len(orig_audio_seg))
        
        # 3. Process each segment
        for i, segment in enumerate(segments):
            start_time = segment['start']
            end_time = segment['end']
            original_text = segment['text'].strip()
            
            # Calculate maximum allowed timeframe without stepping on the next segment
            if i + 1 < len(segments):
                next_start = segments[i+1]['start']
                max_allowed_duration = next_start - start_time
            else:
                max_allowed_duration = (len(orig_audio_seg) / 1000.0) - start_time
                
            # Fallback if Whisper reports overlapping segments
            if max_allowed_duration <= 0.1:
                max_allowed_duration = end_time - start_time
                if max_allowed_duration <= 0:
                    max_allowed_duration = 0.5
            
            if not original_text:
                continue
                
            # 3a. Translate
            translated_text = self.translate_text(original_text).strip()
            print(f"[{start_time:.2f} - {end_time:.2f} max:{max_allowed_duration:.2f}] {original_text} -> {translated_text}")
            
            # Avoid sending blank/unpronounceable text to edge-tts to prevent crash
            import re
            if not translated_text or not bool(re.search(r'\w', translated_text)):
                print(f"Skipping empty or unpronounceable text: '{translated_text}'")
                continue
            
            # 3b. Generate Speech
            tts_path = os.path.join(temp_dir, f"tts_{i}.mp3")
            asyncio.run(self.generate_tts(translated_text, tts_path))
            
            # 3c. Adjust timing naturallly
            adjusted_path = os.path.join(temp_dir, f"adjusted_{i}.wav")
            self.fit_audio_natural(tts_path, adjusted_path, max_allowed_duration)
            
            # 3d. Overlay onto the final audio track at the correct time
            try:
                adjusted_clip = AudioSegment.from_file(adjusted_path)
                start_ms = int(start_time * 1000)
                final_audio = final_audio.overlay(adjusted_clip, position=start_ms)
            except Exception as e:
                print(f"Skipping segment mapping due to error: {e}")
                
        # Export the fully dubbed track
        final_audio_path = os.path.join(temp_dir, "final_dubbed_audio.wav")
        print("Exporting complete stitched audio...")
        final_audio.export(final_audio_path, format="wav")
        
        # 4. Merge back with the video
        print("Merging dubbed audio with original video...")
        try:
            video = VideoFileClip(input_video)
            
            new_audio = AudioFileClip(final_audio_path)
            # Make sure we don't extend past the original video length
            if new_audio.duration > video.duration:
                new_audio = new_audio.subclip(0, video.duration)
            
            video = video.set_audio(new_audio)
            video.write_videofile(output_video, audio_codec="aac", logger=None)
            video.close()
            new_audio.close()
        except Exception as e:
            print(f"Error merging video: {e}")
        
        # 5. Cleanup
        print("Cleaning up temporary files...")
        for f in os.listdir(temp_dir):
            try:
                os.remove(os.path.join(temp_dir, f))
            except:
                pass
        try:
            os.rmdir(temp_dir)
        except:
            pass
            
        print(f"Dubbing complete! Saved video to {output_video}")
