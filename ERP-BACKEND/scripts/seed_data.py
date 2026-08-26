#!/usr/bin/env python3
"""
Seed Data Loading Script for ERP03

This script loads initial seed data into the database after migrations.
It supports atomic transactions and rollback on failure.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import engine, get_db
from app.models import User, Role, Permission
from app.config import settings
import hashlib

def hash_password(password: str) -> str:
    """Hash a password using SHA-256 (replace with bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

def seed_users(db: Session):
    """Create default admin user"""
    print("Seeding users...")
    
    # Check if admin already exists
    admin = db.query(User).filter(User.email == "admin@erp03.local").first()
    if not admin:
        admin = User(
            email="admin@erp03.local",
            hashed_password=hash_password("admin123"),  # Change in production!
            full_name="System Administrator",
            is_active=True,
            is_superuser=True
        )
        db.add(admin)
        print("  ✓ Created admin user")
    else:
        print("  ℹ Admin user already exists")
    
    # Create demo user
    demo = db.query(User).filter(User.email == "demo@erp03.local").first()
    if not demo:
        demo = User(
            email="demo@erp03.local",
            hashed_password=hash_password("demo123"),
            full_name="Demo User",
            is_active=True,
            is_superuser=False
        )
        db.add(demo)
        print("  ✓ Created demo user")
    else:
        print("  ℹ Demo user already exists")

def seed_roles(db: Session):
    """Create default roles"""
    print("Seeding roles...")
    
    default_roles = [
        {"name": "admin", "display_name": "Administrator", "description": "Full system access", "is_system": True},
        {"name": "manager", "display_name": "Manager", "description": "Department management", "is_system": True},
        {"name": "user", "display_name": "User", "description": "Standard user access", "is_system": True},
        {"name": "viewer", "display_name": "Viewer", "description": "Read-only access", "is_system": True},
    ]
    
    for role_data in default_roles:
        role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not role:
            role = Role(**role_data)
            db.add(role)
            print(f"  ✓ Created role: {role_data['name']}")
        else:
            print(f"  ℹ Role {role_data['name']} already exists")

def seed_permissions(db: Session):
    """Create default permissions"""
    print("Seeding permissions...")
    
    default_permissions = [
        # Users
        {"code": "users.read", "description": "View users"},
        {"code": "users.create", "description": "Create users"},
        {"code": "users.update", "description": "Update users"},
        {"code": "users.delete", "description": "Delete users"},
        # Roles
        {"code": "roles.read", "description": "View roles"},
        {"code": "roles.create", "description": "Create roles"},
        {"code": "roles.update", "description": "Update roles"},
        {"code": "roles.delete", "description": "Delete roles"},
        # Finance
        {"code": "finance.read", "description": "View financial data"},
        {"code": "finance.create", "description": "Create financial records"},
        {"code": "finance.update", "description": "Update financial records"},
        # Inventory
        {"code": "inventory.read", "description": "View inventory"},
        {"code": "inventory.create", "description": "Manage inventory"},
        # Reports
        {"code": "reports.read", "description": "View reports"},
        {"code": "reports.export", "description": "Export reports"},
    ]
    
    for perm_data in default_permissions:
        perm = db.query(Permission).filter(Permission.code == perm_data["code"]).first()
        if not perm:
            perm = Permission(**perm_data)
            db.add(perm)
            print(f"  ✓ Created permission: {perm_data['code']}")
        else:
            print(f"  ℹ Permission {perm_data['code']} already exists")

def run_seeds():
    """Run all seed functions with atomic transaction"""
    print("=" * 60)
    print("ERP03 Seed Data Loading")
    print("=" * 60)
    print(f"Database: {settings.DATABASE_URL[:30]}...")
    print()
    
    try:
        with Session(engine) as db:
            try:
                seed_users(db)
                seed_roles(db)
                seed_permissions(db)
                
                db.commit()
                print()
                print("=" * 60)
                print("✓ Seed data loaded successfully!")
                print("=" * 60)
                
            except Exception as e:
                db.rollback()
                print()
                print("=" * 60)
                print(f"✗ Error seeding data: {e}")
                print("Rolling back changes...")
                print("=" * 60)
                raise
                
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_seeds()
