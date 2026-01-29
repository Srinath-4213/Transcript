import yt_dlp
import whisper
import os
import re
import time
import random

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def get_video_info(video_url):
    ydl_opts = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info.get('title', 'Unknown_Video')
    except Exception:
        return "Unknown_Video"

def download_audio(video_url, output_filename="temp_audio"):
    print(f"⬇️  Downloading audio...")
    
    final_filename = f"{output_filename}.mp3"
    
    # Clean up previous temp files to avoid false positives
    if os.path.exists(final_filename):
        os.remove(final_filename)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_filename,
        'quiet': True,
        'no_warnings': True,
        
        # ANTI-BOT & COOKIE SETTINGS
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'referer': 'https://www.google.com/',
        'nocheckcertificate': True,
        'ignoreerrors': True,  # Prevent crash on error
        'socket_timeout': 30,
        # Check if cookies.txt exists and use it
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # CRITICAL FIX: Verify file exists before returning success
        if os.path.exists(final_filename):
            return final_filename
        else:
            print("❌ Download failed (File not found). Likely 403 Forbidden.")
            return None
            
    except Exception as e:
        print(f"❌ Error downloading: {e}")
        return None

def clean_text(text):
    fillers = [r"\bum\b", r"\buh\b", r"\bah\b", r"\blike\b", r"\bso\b", r"\byou know\b"]
    clean_t = text
    for filler in fillers:
        clean_t = re.sub(filler, "", clean_t, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', clean_t).strip()

def format_timestamp(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

def transcribe_audio(audio_path, model):
    print(f"🎧 Transcribing...")
    
    # Double check file existence to prevent FFmpeg crash
    if not os.path.exists(audio_path):
        print("❌ Audio file missing, skipping transcription.")
        return []

    result = model.transcribe(audio_path)
    
    formatted_output = []
    for segment in result['segments']:
        start_time = format_timestamp(segment['start'])
        text = clean_text(segment['text'])
        if text:
            formatted_output.append(f"[{start_time}] {text}")
            
    return formatted_output

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    
    if not os.path.exists("urls.txt"):
        print("❌ Error: 'urls.txt' not found.")
        exit()

    # Check for cookies
    if os.path.exists("cookies.txt"):
        print("🍪 Cookies found! Using them for authentication.")
    else:
        print("⚠️ No cookies.txt found. If you get 403 errors, add your cookies.")

    print("⏳ Loading Whisper model...")
    model = whisper.load_model("base")

    with open("urls.txt", "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"🚀 Found {len(urls)} videos to process.\n")

    for index, url in enumerate(urls, 1):
        print(f"--- Processing {index}/{len(urls)} ---")
        
        # 1. Get Title
        raw_title = get_video_info(url)
        clean_title = sanitize_filename(raw_title)
        
        # If title fetch failed, use a generic name
        if clean_title == "Unknown_Video":
            clean_title = f"Video_{index}"
            
        output_file = f"{clean_title}.txt"
        
        # 2. Download
        audio_file = download_audio(url, "temp_audio_file")
        
        if audio_file:
            # 3. Transcribe
            transcript = transcribe_audio(audio_file, model)
            
            # 4. Save
            if transcript:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(transcript))
                print(f"✅ Saved: {output_file}")
            
            # 5. Cleanup
            if os.path.exists(audio_file):
                os.remove(audio_file)
        else:
            print(f"⚠️ Skipping {url} due to download failure.")
        
        print("\n")
        
        # Sleep to avoid Bot Detection (5 to 15 seconds)
        if index < len(urls):
            sleep_time = random.uniform(5, 15)
            print(f"💤 Sleeping for {int(sleep_time)}s to avoid detection...")
            time.sleep(sleep_time)

    print("🎉 Batch processing complete!")