import os
import shutil
import winreg
from pathlib import Path

def refresh_path_from_registry():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment', 0, winreg.KEY_READ) as key:
            user_path, _ = winreg.QueryValueEx(key, 'Path')
    except FileNotFoundError:
        user_path = ""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 0, winreg.KEY_READ) as key:
            machine_path, _ = winreg.QueryValueEx(key, 'Path')
    except FileNotFoundError:
        machine_path = ""
    os.environ['PATH'] = f"{machine_path};{user_path};{os.environ.get('PATH', '')}"

# Refresh PATH before loading modules so ffmpeg is found
refresh_path_from_registry()

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import yaml

# Import pipeline modules
from src.source_separator import separate_source
from src.key_detector import detect_keys_over_time
from src.pitch_tracker import track_pitch
from src.pitch_filter import filter_and_snap_notes
from src.midi_exporter import export_to_midi, export_to_text
from src.utils.memory_manager import setup_vram_limit, cleanup_vram

app = FastAPI(title="Note Detector API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
os.makedirs("projects", exist_ok=True)
os.makedirs("frontend", exist_ok=True)

# Mount static frontend
app.mount("/static", StaticFiles(directory="frontend"), name="frontend")
# Mount output to allow downloading
app.mount("/download", StaticFiles(directory="projects"), name="download")

@app.get("/")
def read_index():
    return FileResponse("frontend/index.html")

def run_pipeline(input_audio: str, stem_choice: str, song_dir: str):
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    setup_vram_limit()
    
    basename = Path(input_audio).stem
    
    print(f"--- API PIPELINE START: {basename} ({stem_choice}) ---")
    
    # 2. Source Separation
    model_name = config.get("source_separation", {}).get("model", "htdemucs_ft.yaml")
    if stem_choice == "Vocals":
        print("[F2] Vocals selected! Switching to advanced BS-RoFormer model.")
        model_name = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"
        
    temp_dir = os.path.join(song_dir, "temp_separated")
    os.makedirs(temp_dir, exist_ok=True)
    separated_paths = separate_source(input_audio, model_name, temp_dir)
    
    target_stem_path = None
    for path in separated_paths:
        if f"({stem_choice})" in path:
            target_stem_path = path
            break
            
    if not target_stem_path:
        raise Exception(f"Could not find separated stem for '{stem_choice}'")

    # 3. Key Detection
    detected_keys = detect_keys_over_time(input_audio, config)

    # 4. Extract Lyrics (For Vocals)
    words = None
    if stem_choice == "Vocals":
        from src.lyrics_aligner import extract_lyrics
        words = extract_lyrics(target_stem_path, config)
        
    # 5. Pitch Tracking
    tracking_mode = "mono" if stem_choice in ["Vocals", "Bass"] else "poly"
    tracking_result = track_pitch(target_stem_path, config, mode=tracking_mode, words=words)
    raw_notes = tracking_result["notes"]

    # 5. Filtering
    filtered_notes = filter_and_snap_notes(raw_notes, detected_keys, config)

    # 7. Rhythm Quantization
    from src.rhythm_quantizer import quantize_notes
    final_notes = quantize_notes(filtered_notes, input_audio, config)

    # 6. Export
    out_dir = os.path.join(song_dir, "output")
    os.makedirs(out_dir, exist_ok=True)
    
    midi_filename = f"{basename}_{stem_choice}_snapped.mid"
    text_filename = f"{basename}_{stem_choice}_notes.txt"
    midi_output = os.path.join(out_dir, midi_filename)
    text_output = os.path.join(out_dir, text_filename)
    
    export_to_midi(final_notes, midi_output)
    export_to_text(final_notes, text_output)
    
    cleanup_vram()
    print("--- API PIPELINE END ---")
    
    return midi_filename, text_filename

@app.post("/api/process")
async def process_audio(file: UploadFile = File(...), stem: str = Form(...), song_name: str = Form(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
        
    # Create project directory
    safe_song_name = "".join([c for c in song_name if c.isalpha() or c.isdigit() or c==' ']).rstrip().replace(" ", "_")
    if not safe_song_name:
        safe_song_name = "untitled_project"
        
    song_dir = f"projects/{safe_song_name}"
    os.makedirs(song_dir, exist_ok=True)
        
    file_path = f"{song_dir}/{file.filename}"
    
    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        midi_file, text_file = run_pipeline(file_path, stem, song_dir)
        return {
            "status": "success",
            "midi_url": f"/download/{safe_song_name}/output/{midi_file}",
            "text_url": f"/download/{safe_song_name}/output/{text_file}"
        }
    except Exception as e:
        cleanup_vram() # Ensure cleanup on error
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process_youtube")
async def process_youtube_audio(youtube_url: str = Form(...), stem: str = Form(...), song_name: str = Form(...)):
    if not youtube_url:
        raise HTTPException(status_code=400, detail="No YouTube URL provided")
        
    # Create project directory
    safe_song_name = "".join([c for c in song_name if c.isalpha() or c.isdigit() or c==' ']).rstrip().replace(" ", "_")
    if not safe_song_name:
        safe_song_name = "youtube_project"
        
    song_dir = f"projects/{safe_song_name}"
    os.makedirs(song_dir, exist_ok=True)
    
    try:
        # Download YouTube audio
        from src.youtube_downloader import download_youtube_audio
        file_path = download_youtube_audio(youtube_url, song_dir, file_name="downloaded_audio")
        
        # Run pipeline
        midi_file, text_file = run_pipeline(file_path, stem, song_dir)
        return {
            "status": "success",
            "midi_url": f"/download/{safe_song_name}/output/{midi_file}",
            "text_url": f"/download/{safe_song_name}/output/{text_file}"
        }
    except Exception as e:
        cleanup_vram() # Ensure cleanup on error
        raise HTTPException(status_code=500, detail=str(e))
