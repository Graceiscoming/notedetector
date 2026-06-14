import whisper
import torch
import warnings
import numpy as np

# Monkey-patch Whisper's load_audio to avoid ffmpeg dependency
def custom_load_audio(file_path, sr=16000):
    from src.audio_ingest import load_and_resample
    audio_tensor, _ = load_and_resample(file_path, target_sr=sr)
    return audio_tensor.cpu().numpy().astype(np.float32)

whisper.audio.load_audio = custom_load_audio

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

def extract_lyrics(audio_path, config):
    """
    Transcribes audio to get word-level timestamps.
    Returns a list of dicts: [{"word": str, "start": float, "end": float}]
    """
    print(f"[F6] Running Whisper (Word-Level) on {audio_path}...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Load Whisper model ('small' is a good balance for Thai)
    model_size = config.get("lyrics", {}).get("whisper_model", "small")
    model = whisper.load_model(model_size, device=device)
    
    # Transcribe with word timestamps (Forcing Thai language)
    print(f"[F6] Transcribing and extracting timestamps...")
    result = model.transcribe(audio_path, word_timestamps=True, language="th")
    
    import json
    with open("whisper_debug.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    words = []
    for segment in result.get("segments", []):
        segment_words = segment.get("words", [])
        if segment_words:
            for word in segment_words:
                clean_word = word["word"].strip()
                if clean_word:
                    words.append({
                        "word": clean_word,
                        "start": word["start"],
                        "end": word["end"]
                    })
        else:
            clean_text = segment.get("text", "").strip()
            if clean_text:
                words.append({
                    "word": clean_text,
                    "start": segment["start"],
                    "end": segment["end"]
                })
            
    print(f"[F6] Extracted {len(words)} words.")
    return words
