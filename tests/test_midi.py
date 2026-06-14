import yaml
import os
import urllib.request
from pathlib import Path
from src.pitch_tracker import track_pitch
from src.midi_exporter import export_to_midi

def ensure_pti_model():
    checkpoint_path = '{}/piano_transcription_inference_data/note_F1=0.9677_pedal_F1=0.9186.pth'.format(str(Path.home()))
    if not os.path.exists(checkpoint_path) or os.path.getsize(checkpoint_path) < 1.6e8:
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        print("Downloading PTI model (~165MB) to avoid 'wget' error on Windows...")
        url = "https://zenodo.org/record/4034264/files/CRNN_note_F1%3D0.9677_pedal_F1%3D0.9186.pth?download=1"
        urllib.request.urlretrieve(url, checkpoint_path)
        print("Model downloaded successfully!")

def test_pitch_tracking_and_midi():
    ensure_pti_model()
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    audio_path = "temp_separated/testhbd_(Other)_htdemucs_ft.wav"
    output_path = "output_midi/test_polyphonic.mid"
    
    if not os.path.exists(audio_path):
        print(f"Error: {audio_path} not found. Did Phase 2 run successfully?")
        return
    
    print("--- Test: Polyphonic Pitch Tracking & MIDI Export ---")
    result = track_pitch(audio_path, config, mode="poly")
    
    if result["type"] == "poly":
        notes_data = result["notes"]
        print(f"Extracted {len(notes_data)} notes.")
        export_to_midi(notes_data, output_path)
    
if __name__ == "__main__":
    test_pitch_tracking_and_midi()
