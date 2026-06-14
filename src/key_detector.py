"""
F3: Key Detection & Override Module
Implements Voting Ensemble (Krumhansl-Schmuckler, Temperley, Chroma Energy)
or handles manual key override.
"""

import numpy as np
import librosa
import scipy.stats

PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# KS Profiles
KS_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KS_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

# Temperley Profiles
TEMP_MAJOR = np.array([5.0, 2.0, 3.5, 2.0, 4.5, 4.0, 2.0, 4.5, 2.0, 3.5, 1.5, 4.0])
TEMP_MINOR = np.array([5.0, 2.0, 3.5, 4.5, 2.0, 4.0, 2.0, 4.5, 3.5, 2.0, 1.5, 4.0])

# Binary (Chroma Energy) Profiles
BIN_MAJOR = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])
BIN_MINOR = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0])

def compute_correlations(chroma_vector, major_profile, minor_profile):
    major_corrs = []
    minor_corrs = []
    for i in range(12):
        shifted_major = np.roll(major_profile, i)
        shifted_minor = np.roll(minor_profile, i)
        major_corrs.append(scipy.stats.pearsonr(chroma_vector, shifted_major)[0])
        minor_corrs.append(scipy.stats.pearsonr(chroma_vector, shifted_minor)[0])
    return major_corrs, minor_corrs

def estimate_key(chroma_vector, major_profile, minor_profile):
    major_corrs, minor_corrs = compute_correlations(chroma_vector, major_profile, minor_profile)
    max_major_idx = np.argmax(major_corrs)
    max_minor_idx = np.argmax(minor_corrs)
    
    if major_corrs[max_major_idx] > minor_corrs[max_minor_idx]:
        return f"{PITCH_CLASSES[max_major_idx]}_Major"
    else:
        return f"{PITCH_CLASSES[max_minor_idx]}_Minor"

def detect_keys_over_time(audio_path, config):
    """
    Detects the key of the given audio using a sliding window to catch modulations.
    """
    target_key = config.get("key_detection", {}).get("target_key", "AUTO")
    if target_key != "AUTO":
        print(f"[F3] Manual Key Override activated: {target_key}")
        return [{"start": 0.0, "end": float('inf'), "key": target_key}]
        
    print(f"[F3] Auto-detecting key modulations for {audio_path}...")
    y, sr = librosa.load(audio_path, sr=22050)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    
    # chromagram shape is (12, frames)
    # Frame duration is approx hop_length/sr = 512/22050 = 0.02322 seconds
    frame_duration = 512.0 / sr

    window_seconds = config.get("key_detection", {}).get("window_seconds", 10.0)
    frames_per_window = int(window_seconds / frame_duration)

    keys_over_time = []
    total_frames = chroma.shape[1]
    
    from collections import Counter

    for start_frame in range(0, total_frames, frames_per_window):
        end_frame = min(start_frame + frames_per_window, total_frames)
        window_chroma = chroma[:, start_frame:end_frame]
        chroma_vector = np.sum(window_chroma, axis=1)

        key_ks = estimate_key(chroma_vector, KS_MAJOR, KS_MINOR)
        key_temp = estimate_key(chroma_vector, TEMP_MAJOR, TEMP_MINOR)
        key_bin = estimate_key(chroma_vector, BIN_MAJOR, BIN_MINOR)
        
        votes = [key_ks, key_temp, key_bin]
        vote_counts = Counter(votes)
        final_key = vote_counts.most_common(1)[0][0]

        start_time = start_frame * frame_duration
        end_time = end_frame * frame_duration
        keys_over_time.append({
            "start": float(start_time),
            "end": float(end_time),
            "key": final_key
        })

    return keys_over_time
