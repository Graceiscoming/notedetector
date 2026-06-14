import os
import shutil
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import yaml

# Import pipeline modules
from src.source_separator import separate_source
from src.key_detector import detect_key
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
os.makedirs("input_audio", exist_ok=True)
os.makedirs("temp_separated", exist_ok=True)
os.makedirs("output_midi", exist_ok=True)
os.makedirs("frontend", exist_ok=True)

# Mount static frontend
app.mount("/static", StaticFiles(directory="frontend"), name="frontend")
# Mount output to allow downloading
app.mount("/download", StaticFiles(directory="output_midi"), name="download")

@app.get("/")
def read_index():
    return FileResponse("frontend/index.html")

def run_pipeline(input_audio: str, stem_choice: str):
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    setup_vram_limit()
    
    basename = Path(input_audio).stem
    
    print(f"--- API PIPELINE START: {basename} ({stem_choice}) ---")
    
    # 2. Source Separation
    model_name = config.get("source_separation", {}).get("model", "htdemucs_ft.yaml")
    separated_paths = separate_source(input_audio, model_name, "temp_separated")
    
    target_stem_path = None
    for path in separated_paths:
        if f"({stem_choice})" in path:
            target_stem_path = path
            break
            
    if not target_stem_path:
        raise Exception(f"Could not find separated stem for '{stem_choice}'")

    # 3. Key Detection
    detected_key = detect_key(input_audio, config)

    # 4. Pitch Tracking
    tracking_result = track_pitch(target_stem_path, config, mode="poly")
    raw_notes = tracking_result["notes"]

    # 5. Filtering
    filtered_notes = filter_and_snap_notes(raw_notes, detected_key, config)

    # 6. Export
    midi_filename = f"{basename}_{stem_choice}_snapped.mid"
    text_filename = f"{basename}_{stem_choice}_notes.txt"
    midi_output = f"output_midi/{midi_filename}"
    text_output = f"output_midi/{text_filename}"
    
    export_to_midi(filtered_notes, midi_output)
    export_to_text(filtered_notes, text_output)
    
    cleanup_vram()
    print("--- API PIPELINE END ---")
    
    return midi_filename, text_filename

@app.post("/api/process")
async def process_audio(file: UploadFile = File(...), stem: str = Form(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
        
    file_path = f"input_audio/{file.filename}"
    
    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        midi_file, text_file = run_pipeline(file_path, stem)
        return {
            "status": "success",
            "midi_url": f"/download/{midi_file}",
            "text_url": f"/download/{text_file}"
        }
    except Exception as e:
        cleanup_vram() # Ensure cleanup on error
        raise HTTPException(status_code=500, detail=str(e))
