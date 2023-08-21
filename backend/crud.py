from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from jwt import encode, decode
from fastapi import security, Depends, HTTPException
import os
from dotenv import load_dotenv

from backend.database import SessionLocal, engine, Base
from backend import models, schemas

load_dotenv()

JWT_SECRET = os.getenv('JWT_SECRET')
ALGORITHM = os.getenv('ALGORITHM')

oauth2schema = security.OAuth2PasswordBearer(tokenUrl="/api/token")

def create_database():
    return Base.metadata.create_all(bind= engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_user(username: str, db: Session):
    return db.query(models.User).filter(models.User.username == username).first()


async def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        email= user.email,
        name = user.name,
        lastname = user.lastname,
        username = user.username, 
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


async def authenticate_user(username: str, password: str, db: Session):
    user = await get_user(db=db, username=username)

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
        payload = decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user = db.query(models.User).get(payload["id"])
    except:
        raise HTTPException(
            status_code=401, detail="Invalid Email or Password"
        )

    return schemas.User.model_validate(user)

async def get_movie_by_name_director(film_name: str, director: str, db: Session):
    movie =(
        db.query(models.Movie)
        .filter_by(film_name = film_name)
        .filter(models.Movie.director == director)
        .first()
    )
    
    return schemas.Movie.model_validate(movie)


async def add_movie(db: Session, movie: schemas.MovieCreate):
    movie = models.Movie(**movie.model_dump(), owner_id = 1)
    db.add(movie)
    db.commit()
    db.refresh(movie)
    
    movie_db = await get_movie_by_name_director(film_name= movie.film_name, director= movie.director, db=db)
    return schemas.Movie.model_validate(movie_db)


async def get_all_movies(db: Session):
    movies = db.query(models.Movie).all()
    
    return list(map(schemas.Movie.model_validate, movies))


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
    
    return schemas.Movie.model_validate(movie)


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
    
    return schemas.Movie.model_validate(movie_db)