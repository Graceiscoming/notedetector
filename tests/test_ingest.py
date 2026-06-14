import time
from src.audio_ingest import load_and_resample
import torch

def test():
    file_path = "input_audio/testhbd.mp3"
    print(f"Testing audio ingestion for: {file_path}")
    
    start_time = time.time()
    try:
        audio_tensor, sr = load_and_resample(file_path, target_sr=44100)
        end_time = time.time()
        
        print(f"Success! Audio loaded in {end_time - start_time:.4f} seconds.")
        print(f"Shape: {audio_tensor.shape}")
        print(f"Device: {audio_tensor.device}")
        print(f"Target Sample Rate: {sr} Hz")
        print(f"Duration: {audio_tensor.shape[0] / sr:.2f} seconds")
    except Exception as e:
        print(f"Error during audio ingestion: {e}")

if __name__ == "__main__":
    test()
