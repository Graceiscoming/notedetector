"""
VRAM Management Helper
Centralizes PyTorch memory cleanup (del, torch.cuda.empty_cache, gc.collect).
"""
import gc
import torch

def cleanup_vram():
    """
    Cleans up unused VRAM by collecting garbage and emptying the CUDA cache.
    Call this after unloading a model and before loading a new one.
    """
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def setup_vram_limit(fraction=0.85):
    """
    Sets the maximum fraction of GPU memory PyTorch can use to prevent OOM.
    Should be called once at the start of the program.
    """
    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(fraction)

