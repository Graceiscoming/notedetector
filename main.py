import yaml

def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    print("Starting NoteDetector Pipeline...")
    config = load_config()
    print("Configuration loaded successfully.")

    # TODO: Implement Pipeline Steps
    # 1. Audio Ingestion (F1)
    # 2. Source Separation (F2)
    # 3. Key Detection (F3)
    # 4. Pitch Tracking (F4)
    # 5. Pitch Filtering & Snapping (F5)
    # 6. MIDI Export (F6)

if __name__ == "__main__":
    main()
