"""
F2: Advanced Source Separation Module
Uses audio-separator to run models like BS-RoFormer (vocals) 
or MDX23C/Demucs (instruments).
"""

import os
import logging
from audio_separator.separator import Separator
from src.utils.memory_manager import cleanup_vram

def separate_source(audio_path, model_name, output_dir):
    """
    Separates the audio using the specified model via audio-separator.
    Returns:
        list: Paths to the separated audio files.
    """
    print(f"[F2] Loading Source Separation Model: {model_name} ...")
    
    # Initialize separator
    separator = Separator(output_dir=output_dir, log_level=logging.WARNING)
    
    # Load model (e.g. BS-RoFormer, htdemucs_ft)
    # The extension or exact string depends on what audio-separator expects, 
    # but usually passing the standard model name fetches the right model.
    separator.load_model(model_filename=model_name)
    
    print(f"[F2] Separating audio: {os.path.basename(audio_path)} ...")
    output_files = separator.separate(audio_path)
    
    # Force unload model to free up VRAM for the next steps
    del separator
    cleanup_vram()
    print(f"[F2] Model {model_name} unloaded. VRAM cleaned.")
    
    # Return absolute paths
    return [os.path.join(output_dir, f) for f in output_files]

