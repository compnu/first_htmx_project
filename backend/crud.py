from datetime import datetime, timedelta
from typing import Annotated

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

import os
from dotenv import load_dotenv

from backend.database import SessionLocal, engine, Base
from backend import models, schemas

load_dotenv()

JWT_SECRET = os.getenv('JWT_SECRET')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

oauth2schema = OAuth2PasswordBearer(tokenUrl="/api/token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_database():
    return Base.metadata.create_all(bind= engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_user_schema(username: str, db: Session):
    user_db = db.query(models.User).filter(models.User.username == username).first()
    user = schemas.User(
        email= user_db.email,
        username=user_db.username,
        name=user_db.name,
        lastname=user_db.lastname,
        hashed_password = user_db.hashed_password,
        id= user_db.id
    )
    return user


async def get_user(username: str, db: Session):
    return db.query(models.User).filter(models.User.username == username).first()


async def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        email= user.email,
        username = user.username, 
        name = user.name,
        lastname = user.lastname,
        hashed_password = pwd_context.hash(user.hashed_password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


async def create_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    
    return encoded_jwt


async def authenticate_user(username: str, password: str, db: Session):
    user = await get_user(db=db, username=username)

    if not user:
        return False
    
    if not user.verify_password(password):
        return False
    
    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2schema)],
    db:  Annotated[Session, Depends(get_db)]
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_302_FOUND,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer", "Location": "/login"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
        
        token_data = schemas.TokenData(username=username)
    
    except JWTError:
        raise credentials_exception
    
    user = await get_user(username=token_data.username, db=db)
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_movie_by_name_director(film_name: str, director: str, db: Session):
    movie =(
        db.query(models.Movie)
        .filter_by(film_name = film_name)
        .filter(models.Movie.director == director)
        .first()
    )
    
    return movie


async def add_movie(owner_id: int, db: Session, movie: schemas.MovieCreate):
    movie = models.Movie(**movie.model_dump(), owner_id = owner_id)
    db.add(movie)
    db.commit()
    db.refresh(movie)
    
    movie_db = await get_movie_by_name_director(film_name= movie.film_name, director= movie.director, db=db)
    return movie_db


async def get_all_movies(db: Session):
    movies = db.query(models.Movie).all()
    
    return movies
    # return list(map(schemas.Movie.model_validate, movies))


async def movie_selector(movie_id: int, db: Session):
    movie = (
        db.query(models.Movie)
        .filter(models.Movie.id == movie_id)
        .first()
    )
    if movie is None:
        raise HTTPException(status_code=404, detail='Movie does not exist')
    
    return movie


async def get_movie(movie_id: int, db: Session):
    movie = await movie_selector(movie_id=movie_id, db=db)
    return movie
    # return schemas.Movie.model_validate(movie)


async def delete_movie(movie_id: int, db: Session):
    movie = await movie_selector(movie_id=movie_id, db=db)
    
    db.delete(movie)
    db.commit()


async def update_movie(movie_id: int, movie: schemas.MovieCreate, db: Session):
    movie_db = await movie_selector(movie_id=movie_id, db=db)
    
    movie_db.film_name = movie.film_name
    movie_db.director = movie.director
    
    db.commit()
    db.refresh(movie_db)
    
    return movie_db
    # return schemas.Movie.model_validate(movie_db)