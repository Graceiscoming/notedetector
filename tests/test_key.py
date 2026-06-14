from src.key_detector import detect_key
import yaml

def test_key_detection():
    # Load config
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    # Test with original audio
    audio_path = "input_audio/testhbd.mp3"
    print("--- Test 1: Auto Detection ---")
    detected_key = detect_key(audio_path, config)
    
    # Test with override
    print("\n--- Test 2: Manual Override ---")
    config["key_detection"]["target_key"] = "C_Major"
    override_key = detect_key(audio_path, config)

if __name__ == "__main__":
    test_key_detection()
