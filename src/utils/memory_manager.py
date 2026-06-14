"""
VRAM Management Helper
Centralizes PyTorch memory cleanup (del, torch.cuda.empty_cache, gc.collect).
"""
import gc
import torch

def cleanup_vram():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()
