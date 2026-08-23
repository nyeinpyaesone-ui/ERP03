"""
SKU Generator - Stock Keeping Unit Algorithm
Format: CATEGORY-BRAND-SIZE-COLOR-VARIANT
"""
import uuid
from typing import Optional

class SKUGenerator:
    """Generates unique SKU codes for products"""
    
    @staticmethod
    def generate(category: str, brand: str, size: Optional[str] = None, 
                 color: Optional[str] = None, variant: Optional[str] = None) -> str:
        """
        Generate deterministic SKU from product attributes.
        Falls back to UUID suffix if collision detected.
        """
        parts = [
            category[:3].upper(),
            brand[:4].upper()
        ]
        
        if size:
            parts.append(size[:3].upper())
        if color:
            parts.append(color[:3].upper())
        if variant:
            parts.append(variant[:2].upper())
            
        base_sku = "-".join(parts)
        unique_suffix = str(uuid.uuid4())[:4].upper()
        
        return f"{base_sku}-{unique_suffix}"
    
    @staticmethod
    def parse(sku: str) -> dict:
        """Parse SKU back into components"""
        parts = sku.split('-')
        if len(parts) < 2:
            raise ValueError("Invalid SKU format")
            
        return {
            'category': parts[0] if len(parts) > 0 else '',
            'brand': parts[1] if len(parts) > 1 else '',
            'size': parts[2] if len(parts) > 2 else None,
            'color': parts[3] if len(parts) > 3 else None,
            'variant': parts[4] if len(parts) > 4 else None,
            'unique_id': parts[-1] if len(parts) > 4 else parts[-1]
        }
