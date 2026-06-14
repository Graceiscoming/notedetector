import yaml
import os
from src.pitch_tracker import track_pitch
from src.key_detector import detect_key
from src.pitch_filter import filter_and_snap_notes
from src.midi_exporter import export_to_midi, export_to_text

def test_filtering():
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    audio_path = "temp_separated/testhbd_(Other)_htdemucs_ft.wav"
    if not os.path.exists(audio_path):
        print("Audio not found")
        return
        
    # 1. Detect Key
    key = detect_key(audio_path, config)
    
    # 2. Pitch Tracking
    result = track_pitch(audio_path, config, mode="poly")
    notes = result["notes"]
    print(f"Before filtering: {len(notes)} notes")
    
    # 3. Filter and Snap
    filtered_notes = filter_and_snap_notes(notes, key, config)
    print(f"After filtering: {len(filtered_notes)} notes")
    
    # 4. Export
    os.makedirs("output_midi", exist_ok=True)
    output_path = "output_midi/test_polyphonic_snapped.mid"
    export_to_midi(filtered_notes, output_path)
    
    text_output_path = "output_midi/test_notes_snapped.txt"
    export_to_text(filtered_notes, text_output_path)

if __name__ == "__main__":
    test_filtering()
