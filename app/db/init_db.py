from sqlalchemy.orm import Session
import os
from . import models, crud
from .database import engine

def init_db(db: Session):
    # Create tables
    models.Base.metadata.create_all(bind=engine)
    
    # Check if admin user exists
    admin_username = os.environ.get("ADMIN_USERNAME")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    
    if not admin_username or not admin_password:
        raise ValueError("ADMIN_USERNAME and ADMIN_PASSWORD must be set in environment variables")
    
    # Check if admin already exists
    existing_admin = crud.get_user(db, admin_username)
    if existing_admin:
        print(f"Admin user '{admin_username}' already exists")
        return
    
    # Create admin user
    admin_user = crud.create_user(
        db=db,
        username=admin_username,
        password=admin_password,
        email=admin_email,
        is_admin=True,
        is_approved=True
    )
    
    if admin_user:
        print(f"Created admin user: {admin_username}")
    else:
        print("Failed to create admin user")
