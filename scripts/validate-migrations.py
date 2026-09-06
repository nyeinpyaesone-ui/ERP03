#!/usr/bin/env python3
"""
ERP03 — Validate Alembic Migration Chain Integrity

Usage: python scripts/validate-migrations.py

Checks:
- Migration chain is linear (no branching)
- All migrations have proper dependencies
- Can reach head from base
- No circular dependencies
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'ERP-BACKEND'
sys.path.insert(0, str(backend_path))

from alembic.config import Config
from alembic.script import ScriptDirectory


def validate_migration_chain():
    """Check migration chain for gaps and conflicts."""
    alembic_cfg = Config(str(backend_path / 'alembic.ini'))
    
    # Change to backend directory so alembic can find the alembic/ folder
    import os
    original_dir = os.getcwd()
    os.chdir(backend_path)
    
    try:
        script = ScriptDirectory.from_config(alembic_cfg)
    except Exception as e:
        print(f"✗ Failed to load Alembic configuration: {e}")
        return False
    finally:
        # Restore original directory but keep script object usable
        os.chdir(original_dir)
        # Re-change to backend for walk_revisions if needed
        os.chdir(backend_path)
    
    # Get all revisions
    revisions = list(script.walk_revisions())
    
    if not revisions:
        print("⚠️  WARNING: No migrations found")
        return True
    
    print(f"Found {len(revisions)} migration(s)")
    print("")
    
    # Check for multiple heads (indicates branching)
    heads = script.get_heads()
    if len(heads) > 1:
        print(f"✗ CRITICAL: Multiple heads detected: {heads}")
        print("   This indicates a branched migration history.")
        print("   Resolution: Create a merge migration.")
        return False
    
    print(f"✓ Single head revision: {heads[0]}")
    
    # Verify each migration has proper down_revision
    print("")
    print("Migration chain:")
    for rev in reversed(revisions):
        down_rev = rev.down_revision
        if down_rev is None:
            down_id = '(base)'
        elif isinstance(down_rev, str):
            down_id = down_rev[:12]
        else:
            down_id = down_rev.revision[:12]
        print(f"  {rev.revision[:12]} <- {down_id}")
    
    # Check for base revision
    base = script.get_base()
    if base:
        base_id = base if isinstance(base, str) else base.revision
        print(f"✓ Base revision: {base_id}")
    else:
        print("✗ No base revision found")
        return False
    
    # Verify we can traverse from head to base
    print("")
    print("Verifying chain integrity...")
    current_heads = heads
    visited = set()
    
    while current_heads:
        current_rev = current_heads.pop(0)
        if current_rev in visited:
            print(f"✗ CRITICAL: Circular dependency detected at {current_rev}")
            return False
        
        visited.add(current_rev)
        rev_obj = script.get_revision(current_rev)
        
        if rev_obj.down_revision:
            down_id = rev_obj.down_revision if isinstance(rev_obj.down_revision, str) else rev_obj.down_revision.revision
            current_heads.append(down_id)
    
    print("✓ Migration chain is valid and linear")
    print("")
    print("Summary:")
    print(f"  - Total migrations: {len(revisions)}")
    head_id = heads[0] if heads else 'None'
    print(f"  - Head revision: {head_id[:12] if head_id != 'None' else 'None'}")
    base_id = base if isinstance(base, str) else (base.revision if base else None)
    print(f"  - Base revision: {base_id[:12] if base_id else 'None'}")
    print(f"  - Chain integrity: VALID")
    
    return True


def main():
    print("=" * 60)
    print("ERP03 Migration Chain Validation")
    print("=" * 60)
    print("")
    
    success = validate_migration_chain()
    
    print("")
    if success:
        print("✓ Validation PASSED")
        return 0
    else:
        print("✗ Validation FAILED")
        print("")
        print("To fix migration issues:")
        print("1. Ensure all migrations have correct down_revision")
        print("2. If multiple heads exist, create a merge migration:")
        print("   cd ERP-BACKEND && alembic merge -m 'merge_heads'")
        print("3. Test with: alembic upgrade head")
        return 1


if __name__ == "__main__":
    sys.exit(main())
