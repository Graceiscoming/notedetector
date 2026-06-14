import os
import argparse
import yaml
from pathlib import Path

# Import pipeline modules
from src.source_separator import separate_source
from src.key_detector import detect_key
from src.pitch_tracker import track_pitch
from src.pitch_filter import filter_and_snap_notes
from src.midi_exporter import export_to_midi, export_to_text
from src.utils.memory_manager import setup_vram_limit, cleanup_vram

def ensure_pti_model():
    import urllib.request
    checkpoint_path = '{}/piano_transcription_inference_data/note_F1=0.9677_pedal_F1=0.9186.pth'.format(str(Path.home()))
    if not os.path.exists(checkpoint_path) or os.path.getsize(checkpoint_path) < 1.6e8:
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        print("[INIT] Downloading PTI model (~165MB) to avoid 'wget' error on Windows...")
        url = "https://zenodo.org/record/4034264/files/CRNN_note_F1%3D0.9677_pedal_F1%3D0.9186.pth?download=1"
        urllib.request.urlretrieve(url, checkpoint_path)
        print("[INIT] Model downloaded successfully!")

def main():
    parser = argparse.ArgumentParser(description="Note Detector Pipeline")
    parser.add_argument("--input", type=str, default="input_audio/testhbd.mp3", help="Path to input audio file")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--stem", type=str, default="Other", choices=["Vocals", "Bass", "Drums", "Other"], help="Which separated stem to transcribe")
    args = parser.parse_args()

    # Setup
    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    setup_vram_limit()
    ensure_pti_model()
    
    input_audio = args.input
    stem_choice = args.stem
    basename = Path(input_audio).stem

    print("\n" + "="*50)
    print(f"*** STARTING NOTE DETECTOR PIPELINE ***")
    print(f"Input File: {input_audio}")
    print(f"Target Stem: {stem_choice}")
    print("="*50)

    # --- Phase 2: Source Separation ---
    print("\n>>> PHASE 2: Source Separation")
    # Returns paths to the separated files
    os.makedirs("temp_separated", exist_ok=True)
    model_name = config.get("source_separation", {}).get("model", "htdemucs_ft.yaml")
    
    if stem_choice == "Vocals":
        print("[F2] Vocals selected! Switching to advanced BS-RoFormer model.")
        model_name = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"
        
    separated_paths = separate_source(input_audio, model_name, "temp_separated")
    
    # Find the requested stem
    target_stem_path = None
    for path in separated_paths:
        if f"({stem_choice})" in path:
            target_stem_path = path
            break
            
    if not target_stem_path:
        print(f"Error: Could not find separated stem for '{stem_choice}'")
        return

    # --- Phase 3: Key Detection ---
    print("\n>>> PHASE 3: Key Detection")
    from src.key_detector import detect_keys_over_time
    detected_keys = detect_keys_over_time(input_audio, config)
    print(f"Detected key modulations: {[k['key'] for k in detected_keys]}")

    # --- Phase 4: Extract Lyrics (For Vocals) ---
    print("\n>>> PHASE 4: Extract Lyrics")
    words = None
    if stem_choice == "Vocals":
        from src.lyrics_aligner import extract_lyrics
        words = extract_lyrics(target_stem_path, config)
        
    # --- Phase 5: Pitch Tracking ---
    print("\n>>> PHASE 5: Pitch Tracking")
    tracking_mode = "mono" if stem_choice in ["Vocals", "Bass"] else "poly"
    tracking_result = track_pitch(target_stem_path, config, mode=tracking_mode, words=words)
    raw_notes = tracking_result["notes"]
    print(f"Detected {len(raw_notes)} raw notes.")

    # --- Phase 5: Pitch Filtering & Snapping ---
    print("\n>>> PHASE 5: Pitch Filtering & Snapping")
    filtered_notes = filter_and_snap_notes(raw_notes, detected_keys, config)
    print(f"After filtering: {len(filtered_notes)} notes.")
    
    # --- Phase 7: Rhythm Quantization ---
    print("\n>>> PHASE 7: Rhythm Quantization")
    from src.rhythm_quantizer import quantize_notes
    final_notes = quantize_notes(filtered_notes, input_audio, config)

    # --- Phase 6: MIDI Export ---
    print("\n>>> PHASE 6: MIDI Export")
    os.makedirs("output_midi", exist_ok=True)
    
    midi_output_path = f"output_midi/{basename}_{stem_choice}_snapped.mid"
    export_to_midi(final_notes, midi_output_path)
    
    text_output_path = f"output_midi/{basename}_{stem_choice}_notes.txt"
    export_to_text(final_notes, text_output_path)
    
    # Cleanup
    cleanup_vram()
    print("\n" + "="*50)
    print("*** PIPELINE COMPLETE! ***")
    print(f"Outputs saved to:\n - {midi_output}\n - {text_output}")
    print("="*50)

if __name__ == "__main__":
    main()
