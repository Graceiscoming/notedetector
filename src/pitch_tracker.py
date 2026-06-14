"""
F4: Dual-Engine Pitch Tracking Module
Mode A (Mono): torchcrepe
Mode B (Poly): piano_transcription_inference
"""

import torch
import numpy as np

def track_pitch_mono(audio_path, config):
    import torchcrepe
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
    times = np.arange(pitch_np.shape[0]) * (10 / 1000.0)
    
    return {"times": times, "pitches": pitch_np, "confidence": periodicity_np, "type": "mono"}

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

