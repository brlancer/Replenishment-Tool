"""
Documents module - Central import point for document generation functions.
"""

from documents.packing_slips import packing_slips
from documents.barcode_labels import barcode_labels

__all__ = [
    'packing_slips',
    'barcode_labels',
]
