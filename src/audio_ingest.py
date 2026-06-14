"""
F1: Audio Ingestion Module
Handles loading audio files (e.g., using soundfile) and resampling 
to a required sample rate (using torchaudio.transforms.Resample).
"""

import soundfile as sf
import torchaudio
import torch
import numpy as np

def load_and_resample(file_path, target_sr=44100, device=None):
    """
    Loads an audio file, converts it to mono, and resamples it to target_sr using GPU if available.
    Returns:
        audio_tensor (torch.Tensor): 1D tensor of audio samples on the specified device.
        sr (int): Target sample rate.
    """
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    # Load with soundfile (fast for large files)
    # returns audio_data shape (frames, channels) or (frames,)
    audio_data, orig_sr = sf.read(file_path, dtype='float32')
    
    # Convert to mono if it's stereo
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)
        
    # Convert numpy array to torch tensor
    # We add a channel dimension (1, time) for torchaudio resampler
    audio_tensor = torch.from_numpy(audio_data).unsqueeze(0)
    
    # Move to GPU for fast resampling
    audio_tensor = audio_tensor.to(device)
    
    # Resample if needed
    if orig_sr != target_sr:
        resampler = torchaudio.transforms.Resample(orig_freq=orig_sr, new_freq=target_sr).to(device)
        audio_tensor = resampler(audio_tensor)
        
    # Remove the channel dimension to return 1D tensor (time,)
    audio_tensor = audio_tensor.squeeze(0)
    
    return audio_tensor, target_sr

