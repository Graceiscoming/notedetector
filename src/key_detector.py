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

def detect_key(audio_path, config):
    """
    Detects the key of the given audio using a voting ensemble, or returns the override key.
    """
    target_key = config.get("key_detection", {}).get("target_key", "AUTO")
    if target_key != "AUTO":
        print(f"[F3] Manual Key Override activated: {target_key}")
        return target_key
        
    print(f"[F3] Auto-detecting key for {audio_path}...")
    y, sr = librosa.load(audio_path, sr=22050)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_vector = np.sum(chroma, axis=1) # Sum energy over time
    
    # Voting methods
    key_ks = estimate_key(chroma_vector, KS_MAJOR, KS_MINOR)
    key_temp = estimate_key(chroma_vector, TEMP_MAJOR, TEMP_MINOR)
    key_bin = estimate_key(chroma_vector, BIN_MAJOR, BIN_MINOR)
    
    votes = [key_ks, key_temp, key_bin]
    print(f"[F3] Key Votes -> KS: {key_ks}, Temperley: {key_temp}, Energy: {key_bin}")
    
    from collections import Counter
    vote_counts = Counter(votes)
    final_key = vote_counts.most_common(1)[0][0]
    
    print(f"[F3] Final Detected Key: {final_key}")
    return final_key
