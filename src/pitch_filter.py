import librosa
import numpy as np

# Maps pitch class index to the standard major/minor scales (intervals from root)
SCALES = {
    "Major": [0, 2, 4, 5, 7, 9, 11],
    "Minor": [0, 2, 3, 5, 7, 8, 10]
}

PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def get_scale_notes(key_string):
    """
    Parses a key string like 'A#_Major' and returns a set of valid pitch classes (0-11).
    """
    if "_" not in key_string:
        return set(range(12)) # Fallback: all notes
        
    root_str, mode = key_string.split("_")
    
    if root_str not in PITCH_CLASSES or mode not in SCALES:
        return set(range(12)) # Fallback
        
    root_idx = PITCH_CLASSES.index(root_str)
    intervals = SCALES[mode]
    
    valid_pitch_classes = set((root_idx + interval) % 12 for interval in intervals)
    return valid_pitch_classes

def snap_pitch_to_scale(pitch, valid_pitch_classes):
    """
    Snaps a MIDI pitch to the closest pitch class in the scale.
    """
    pitch = int(round(pitch))
    pitch_class = pitch % 12
    if pitch_class in valid_pitch_classes:
        return pitch
        
    # Find closest valid pitch
    best_pitch = pitch
    for offset in range(1, 7):
        if (pitch + offset) % 12 in valid_pitch_classes:
            best_pitch = pitch + offset
            break
        if (pitch - offset) % 12 in valid_pitch_classes:
            best_pitch = pitch - offset
            break
            
    return best_pitch

def filter_and_snap_notes(notes_data, key_string, config):
    """
    Snaps notes to the given key and filters out overly short notes.
    """
    min_duration = config.get("pitch_tracking", {}).get("min_note_duration", 0.05)
    
    valid_pitch_classes = get_scale_notes(key_string)
    print(f"[F5] Snapping notes to scale: {key_string}")
    
    filtered_notes = []
    snapped_count = 0
    filtered_count = 0
    
    for note in notes_data:
        duration = note['end'] - note['start']
        if duration < min_duration:
            filtered_count += 1
            continue
            
        original_pitch = note['pitch']
        snapped_pitch = snap_pitch_to_scale(original_pitch, valid_pitch_classes)
        
        if snapped_pitch != original_pitch:
            snapped_count += 1
            
        new_note = {
            "start": note['start'],
            "end": note['end'],
            "pitch": snapped_pitch,
            "velocity": note['velocity']
        }
        filtered_notes.append(new_note)
        
    print(f"[F5] Filtering complete: Snapped {snapped_count} notes, removed {filtered_count} short notes.")
    return filtered_notes
