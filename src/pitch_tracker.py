"""
F4: Dual-Engine Pitch Tracking Module
Mode A (Mono): torchcrepe
Mode B (Poly): piano_transcription_inference
"""

import torch
import numpy as np

def track_pitch_mono(audio_path, config, words=None):
    import torchcrepe
    import scipy.signal
    import librosa
    from src.audio_ingest import load_and_resample
    
    # torchcrepe requires 16000 Hz
    audio, sr = load_and_resample(audio_path, target_sr=16000)
    device = audio.device
    
    batch_size = config.get("pitch_tracking", {}).get("monophonic", {}).get("batch_size", 512)
    model = config.get("pitch_tracking", {}).get("monophonic", {}).get("crepe_model", "full")
    
    if audio.dim() > 1:
        audio = audio.mean(dim=0, keepdim=True)
    elif audio.dim() == 1:
        audio = audio.unsqueeze(0)
        
    print(f"[F4] Running Torchcrepe ({model}) on {device} (Mono Mode)...")
    pitch, periodicity = torchcrepe.predict(
        audio,
        sample_rate=sr,
        hop_length=int(sr / 100), # 10ms hop
        fmin=50,
        fmax=2000,
        model=model,
        batch_size=batch_size,
        device=device,
        return_periodicity=True
    )
    
    pitch_np = pitch.squeeze(0).cpu().numpy()
    periodicity_np = periodicity.squeeze(0).cpu().numpy()
    
    # 1. Convert Hz to MIDI floats
    midi_floats = librosa.hz_to_midi(pitch_np)
    
    # 2. Apply periodicity threshold to drop unvoiced frames
    # High confidence threshold to prevent false positives (D#2 from 50Hz fmin)
    confidence_thresh = 0.8
    voiced_mask = periodicity_np > confidence_thresh
    midi_floats[~voiced_mask] = np.nan
    
    # 3. Group into Note Events
    notes = []
    frame_duration = 10 / 1000.0 # 10ms
    
    if words is not None and len(words) > 0:
        print(f"[F4] Lyrics-Driven Tracking enabled for {len(words)} words.")
        used_frames = np.zeros(len(midi_floats), dtype=bool)
        
        for w in words:
            start_frame = int(w["start"] / frame_duration)
            end_frame = int(w["end"] / frame_duration)
            start_frame = max(0, start_frame)
            end_frame = min(len(midi_floats) - 1, end_frame)
            
            if start_frame > end_frame:
                continue
                
            word_pitches = midi_floats[start_frame:end_frame+1]
            valid_pitches = word_pitches[~np.isnan(word_pitches)]
            
            if len(valid_pitches) > 0:
                median_pitch = int(round(np.median(valid_pitches)))
                
                # Check if we can merge with the previous note
                if len(notes) > 0 and notes[-1]["pitch"] == median_pitch and (w["start"] - notes[-1]["end"] < 0.2):
                    # Merge notes and concat words
                    notes[-1]["end"] = w["end"]
                    notes[-1]["word"] += w["word"]
                else:
                    notes.append({
                        "start": w["start"],
                        "end": w["end"],
                        "pitch": median_pitch,
                        "velocity": 80,
                        "word": w["word"]
                    })
                used_frames[start_frame:end_frame+1] = True
                
        current_hum = None
        for i, midi_val in enumerate(midi_floats):
            if used_frames[i] or np.isnan(midi_val):
                if current_hum is not None:
                    current_hum["end"] = i * frame_duration
                    if current_hum["end"] - current_hum["start"] >= 0.1:
                        notes.append(current_hum)
                    current_hum = None
            else:
                rounded_pitch = int(round(midi_val))
                if current_hum is None:
                    current_hum = {"start": i * frame_duration, "pitch": rounded_pitch, "velocity": 80, "word": "-"}
                elif current_hum["pitch"] != rounded_pitch:
                    current_hum["end"] = i * frame_duration
                    if current_hum["end"] - current_hum["start"] >= 0.1:
                        notes.append(current_hum)
                    current_hum = {"start": i * frame_duration, "pitch": rounded_pitch, "velocity": 80, "word": "-"}
        if current_hum is not None:
            current_hum["end"] = len(midi_floats) * frame_duration
            if current_hum["end"] - current_hum["start"] >= 0.1:
                notes.append(current_hum)
                
        notes.sort(key=lambda x: x["start"])
        
    else:
        current_note = None
        for i, midi_val in enumerate(midi_floats):
            if np.isnan(midi_val):
                if current_note is not None:
                    current_note["end"] = i * frame_duration
                    notes.append(current_note)
                    current_note = None
            else:
                rounded_pitch = int(round(midi_val))
                if current_note is None:
                    current_note = {"start": i * frame_duration, "pitch": rounded_pitch, "velocity": 80, "word": "-"}
                elif current_note["pitch"] != rounded_pitch:
                    current_note["end"] = i * frame_duration
                    notes.append(current_note)
                    current_note = {"start": i * frame_duration, "pitch": rounded_pitch, "velocity": 80, "word": "-"}
        if current_note is not None:
            current_note["end"] = len(midi_floats) * frame_duration
            notes.append(current_note)
            
    return {"notes": notes, "type": "mono"}

def track_pitch_poly(audio_path, config):
    from piano_transcription_inference import PianoTranscription, sample_rate
    from src.audio_ingest import load_and_resample
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print(f"[F4] Running Piano Transcription Inference on {device} (Poly Mode)...")
    
    # Use our robust audio_ingest to avoid audioread NoBackendError
    audio_tensor, _ = load_and_resample(audio_path, target_sr=sample_rate)
    audio = audio_tensor.cpu().numpy()
    
    transcriptor = PianoTranscription(device=device)
    transcribed_dict = transcriptor.transcribe(audio, midi_path=None)
    
    notes = []
    for note_event in transcribed_dict['est_note_events']:
        notes.append({
            "start": note_event['onset_time'],
            "end": note_event['offset_time'],
            "pitch": note_event['midi_note'],
            "velocity": note_event['velocity']
        })
        
    return {"notes": notes, "type": "poly"}

def track_pitch(audio_path, config, mode="mono", words=None):
    if mode == "mono":
        return track_pitch_mono(audio_path, config, words)
    else:
        return track_pitch_poly(audio_path, config)
