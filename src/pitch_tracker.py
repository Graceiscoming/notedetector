"""
F4: Dual-Engine Pitch Tracking Module
Mode A (Mono): torchcrepe
Mode B (Poly): piano_transcription_inference
"""

import torch
import numpy as np

def track_pitch_mono(audio_path, config):
    import torchcrepe
    import scipy.signal
    import librosa
    from src.audio_ingest import load_and_resample
    
    # torchcrepe requires 16000 Hz
    audio, sr = load_and_resample(audio_path, target_sr=16000)
    device = audio.device
    
    batch_size = config.get("pitch_tracking", {}).get("monophonic", {}).get("batch_size", 512)
    model = config.get("pitch_tracking", {}).get("monophonic", {}).get("crepe_model", "full")
    
    if audio.dim() == 1:
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
    
    # 2. Smooth Vibrato using Median Filter
    # 11 frames = 110ms smoothing window
    midi_smoothed = scipy.signal.medfilt(midi_floats, kernel_size=11)
    
    # 3. Apply periodicity threshold to drop unvoiced frames
    confidence_thresh = 0.4
    voiced_mask = periodicity_np > confidence_thresh
    midi_smoothed[~voiced_mask] = np.nan
    
    # 4. Group into Note Events
    notes = []
    current_note = None
    frame_duration = 10 / 1000.0 # 10ms
    
    for i, midi_val in enumerate(midi_smoothed):
        if np.isnan(midi_val):
            if current_note is not None:
                current_note["end"] = i * frame_duration
                notes.append(current_note)
                current_note = None
        else:
            rounded_pitch = int(round(midi_val))
            if current_note is None:
                current_note = {
                    "start": i * frame_duration,
                    "pitch": rounded_pitch,
                    "velocity": 80
                }
            elif current_note["pitch"] != rounded_pitch:
                current_note["end"] = i * frame_duration
                notes.append(current_note)
                current_note = {
                    "start": i * frame_duration,
                    "pitch": rounded_pitch,
                    "velocity": 80
                }
                
    if current_note is not None:
        current_note["end"] = len(midi_smoothed) * frame_duration
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

def track_pitch(audio_path, config, mode="mono"):
    if mode == "mono":
        return track_pitch_mono(audio_path, config)
    else:
        return track_pitch_poly(audio_path, config)

