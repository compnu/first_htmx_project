from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from typing import List
from jwt import encode, decode
from fastapi import security, Depends, HTTPException

from backend.database import SessionLocal, engine, Base
from backend import models, schemas

oauth2schema = security.OAuth2PasswordBearer(tokenUrl="/api/token")

JWT_SECRET = "myjwtsecret"

def create_database():
    return Base.metadata.create_all(bind= engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_user_by_email(email: str, db: Session):
    return db.query(models.User).filter(models.User.email == email).first()


async def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        email= user.email,
        name = user.name,
        lastname = user.lastname,
        username = user.name[0]+ user.lastname[0], 
        hashed_password = bcrypt.hash(user.hashed_password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


async def create_token(user: models.User):
    user_obj = schemas.User.model_validate(user)

    token = encode(user_obj.model_dump(), JWT_SECRET)

    return dict(access_token = token, token_type="bearer")


async def authenticate_user(email: str, password: str, db: Session):
    user = await get_user_by_email(db=db, email=email)

    if not user:
        return False
    
    if not user.verify_password(password):
        return False
    
    return user


async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2schema),
):
    try:
        payload = decode(token, JWT_SECRET, algorithms=["HS256"])
        user = db.query(models.User).get(payload["id"])
    except:
        raise HTTPException(
            status_code=401, detail="Invalid Email or Password"
        )

    return schemas.User.model_validate(user)


async def add_movie(db: Session, movie: schemas.MovieCreate):
    movie = models.Movie(**movie.model_dump(), owner_id = 1)
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return schemas.MovieCreate.model_validate(movie)


async def get_all_movies(db: Session):
    movies = db.query(models.Movie).all()
    
    return list(map(schemas.Movie.model_validate, movies))