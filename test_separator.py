import os
import yaml
from src.source_separator import separate_source

def test_separation():
    audio_path = "input_audio/testhbd.mp3"
    output_dir = "temp_separated"
    
    # Let's use the vocal model from config, or a default one that is fast to download
    # Actually MDX23C or Demucs are usually smaller and faster for general testing
    # We will test Demucs for vocals/instruments
    model_name = "htdemucs_ft.yaml"  # The standard name audio-separator uses for Demucs v4
    
    print(f"Testing Source Separation with {model_name}...")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    try:
        output_files = separate_source(audio_path, model_name, output_dir)
        print("Success! Separated files:")
        for f in output_files:
            print(f" - {f}")
    except Exception as e:
        print(f"Error during separation: {e}")

if __name__ == "__main__":
    test_separation()
