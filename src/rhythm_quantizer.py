import librosa
import numpy as np
import torch
from src.audio_ingest import load_and_resample

def quantize_notes(notes, audio_path, config):
    """
    Snaps note start and end times to the nearest grid line based on detected BPM.
    By default snaps to 16th notes.
    """
    if not notes:
        return notes
        
    print(f"[F5] Detecting BPM and Quantizing Rhythm for {audio_path}...")
    
    # Load audio to detect BPM
    audio, sr = load_and_resample(audio_path, target_sr=22050)
    if audio.dim() > 1:
        audio = audio.mean(dim=0)
    audio_np = audio.cpu().numpy()
    
    # Detect tempo
    tempo, _ = librosa.beat.beat_track(y=audio_np, sr=sr)
    if isinstance(tempo, np.ndarray):
        bpm = float(tempo[0])
    else:
        bpm = float(tempo)
        
    print(f"[F5] Detected BPM: {bpm:.2f}")
    
    # Quantize to 16th notes by default
    grid_type = config.get("rhythm", {}).get("quantize_grid", 16) # 16th note
    
    # Duration of a quarter note (beat) in seconds
    beat_duration = 60.0 / bpm
    
    # Duration of a single grid step
    # 4 grid steps in a beat for 16th notes, 2 for 8th notes, etc.
    grid_step_duration = beat_duration / (grid_type / 4)
    
    quantized_notes = []
    for note in notes:
        q_start = round(note["start"] / grid_step_duration) * grid_step_duration
        q_end = round(note["end"] / grid_step_duration) * grid_step_duration
        
        # Ensure minimum duration of 1 grid step
        if q_end <= q_start:
            q_end = q_start + grid_step_duration
            
        new_note = note.copy()
        new_note["start"] = float(q_start)
        new_note["end"] = float(q_end)
        quantized_notes.append(new_note)
        
    return quantized_notes
