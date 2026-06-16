from auth import hash_password, verify_password, create_access_token
from models import User, SignUpRequest, LogInRequest
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
 
@router.post("/signup")
def signup_user(data: SignUpRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    # hashed_password = hash_password(data.password)
    new_user = User(email=data.email, hashed_password=data.password)
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}

@router.post("/login")
def login_user(data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # verified = verify_password(data.password, user.hashed_password)
    verified = data.password == user.hashed_password
    if not verified:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}