from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from . import models
from passlib.context import CryptContext
import uuid
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_id(db: Session, user_id: uuid.UUID):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_pending_users(db: Session):
    return db.query(models.User).filter(models.User.is_approved == False).all()

def create_user(db: Session, username: str, password: str, email: str, is_admin: bool = False, is_approved: bool = False):
    hashed_password = get_password_hash(password)
    db_user = models.User(
        username=username,
        hashed_password=hashed_password,
        email=email,
        is_admin=is_admin,
        is_approved=is_approved
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        return None

def approve_user(db: Session, user_id: uuid.UUID):
    try:
        # Convert to UUID if it's a string
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
            
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            user.is_approved = True
            db.commit()
            db.refresh(user)  # Refresh to ensure we get the latest state
            return user
        return None
    except Exception as e:
        db.rollback()
        raise e

def suspend_user(db: Session, user_id: uuid.UUID):
    user = get_user_by_id(db, user_id)
    if user:
        user.is_active = False
        db.commit()
        return user
    return None

def activate_user(db: Session, user_id: uuid.UUID):
    user = get_user_by_id(db, user_id)
    if user:
        user.is_active = True
        db.commit()
        return user
    return None

def promote_to_admin(db: Session, user_id: uuid.UUID):
    user = get_user_by_id(db, user_id)
    if user:
        user.is_admin = True
        db.commit()
        return user
    return None

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    # Remove the active check here, let the login handler manage this
    # This allows the proper error message to be displayed
    return user
