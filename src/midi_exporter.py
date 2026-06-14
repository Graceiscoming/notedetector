"""
F6: MIDI Generation Module
Generates a .mid file using pretty_midi based on pitch, onset, offset, and velocity.
"""

import pretty_midi
import numpy as np

def export_to_midi(notes_data, output_path, tempo=120):
    """
    notes_data: list of dicts with 'start', 'end', 'pitch', 'velocity'
    """
    print(f"[F6] Exporting MIDI to {output_path}...")
    midi_data = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    
    # Create an Instrument instance for a Piano instrument
    instrument = pretty_midi.Instrument(program=0)
    
    for note_info in notes_data:
        # Skip invalid or empty notes
        if note_info['pitch'] <= 0 or np.isnan(note_info['pitch']):
            continue
            
        note = pretty_midi.Note(
            velocity=int(note_info.get('velocity', 100)),
            pitch=int(round(note_info['pitch'])),
            start=float(note_info['start']),
            end=float(note_info['end'])
        )
        instrument.notes.append(note)
        
    midi_data.instruments.append(instrument)
    midi_data.write(output_path)
    print(f"[F6] MIDI successfully saved with {len(instrument.notes)} notes.")

def export_to_text(notes_data, output_path):
    """
    Exports the notes to a human-readable text file (e.g., C4, D#4).
    """
    print(f"[F6] Exporting Text Notes to {output_path}...")
    PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("Start(s)\tEnd(s)\tNote\n")
        f.write("-" * 30 + "\n")
        
        for note_info in notes_data:
            if note_info['pitch'] <= 0 or np.isnan(note_info['pitch']):
                continue
                
            pitch = int(round(note_info['pitch']))
            pitch_class = PITCH_CLASSES[pitch % 12]
            octave = (pitch // 12) - 1
            note_name = f"{pitch_class}{octave}"
            
            start = round(note_info['start'], 2)
            end = round(note_info['end'], 2)
            
            f.write(f"{start:.2f}\t\t{end:.2f}\t\t{note_name}\n")
            
    print(f"[F6] Text Notes successfully saved to {output_path}")

