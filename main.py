from datetime import datetime, timedelta
from typing import Annotated

from fastapi import FastAPI, Request, Form, Header, Depends, HTTPException, security, status, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from sqlalchemy.orm import Session

from fastapi.middleware.cors import CORSMiddleware

import os
from dotenv import load_dotenv

from backend import crud, models, schemas, auth
from backend.database import SessionLocal, engine

crud.create_database()

load_dotenv()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name='images')
app.mount("/user_image", StaticFiles(directory="user_image"), name='user_image')

templates = Jinja2Templates(directory="templates")


@app.post("/api/new-users/")
async def create_user(user: schemas.UserCreate, db: Session = Depends(crud.get_db)):
    db_user = await crud.get_user(db=db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already in use!")
    
    user = await crud.create_user(db=db, user=user)

    return user


@app.post("/api/token", response_model= schemas.Token)
async def generate_token(
    response: Response,
    form_data: Annotated[security.OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(crud.get_db)] 
):
    user = await crud.authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await crud.create_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    response.set_cookie(
        key='access_token', value= access_token, httponly=True
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/users/me", response_model=schemas.User)
async def get_user_me(user: Annotated[schemas.User, Depends(crud.get_current_user)]):
    return user


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", context={'request': request})


@app.post("/login", response_class=HTMLResponse, tags=['authenticate'])
async def login_request(
    request: Request,
    db: Annotated[Session, Depends(crud.get_db)]
):
    form = auth.LoginForm(request=request)
    await form.load_data()
        
    user = await crud.authenticate_user(username=form.username, password=form.password, db=db)
    
    if not user:
       access_token = {'access_token': 'Innvalid username'}
       context = {'request': request, 'token': access_token}
       return templates.TemplateResponse('/partials/token.html', context=context)
    
    image = {'path':'/user_image/'+user.username+'.jpg'}
    response = templates.TemplateResponse('index.html', context= {'request': request, 'user': user, 'image': image})
    response.headers['HX-Redirect'] = 'http://127.0.0.1:8000/'
    
    await generate_token(response=response, form_data=form, db=db)
       
    return response


@app.get("/", response_class=HTMLResponse)
async def movielist(
    request: Request,
    db: Annotated[Session, Depends(crud.get_db)],
    hx_request: Optional[str] = Header(None),
    ):
    
    token = request.cookies.get('access_token')
    
    # Authentication
    user = await crud.get_current_user(token=token, db=db)
    
    films = await crud.get_all_movies(db = db)
    films.reverse()
    
    image = {'path':'/user_image/'+user.username+'.jpg'}
    
    context = {"request": request, 'films': films, 'user': user, 'image': image}
    
    if hx_request:
        return templates.TemplateResponse("partials/table.html", context=context)
    
    return templates.TemplateResponse("index.html", context=context)



@app.post('/add-film/', response_class=HTMLResponse)
async def add_film(
    request: Request,
    db: Session = Depends(crud.get_db),
    ): 
    
    data = await request.form()
    
    token = request.cookies.get('access_token')
    user = await crud.get_current_user(token=token, db=db)
    
    movie = await crud.add_movie(
        owner_id= user.id,
        db=db,
        movie = schemas.MovieCreate(film_name=data['title'], director=data['director'])
    )
      
    context = {'request': request, 'films': [movie]}
    return templates.TemplateResponse('/partials/table.html', context=context)


@app.get('/movie/{movie_id}', response_class=HTMLResponse)
async def get_movie(
    request: Request,
    movie_id: int,
    db: Annotated[Session, Depends(crud.get_db)]
    ):
    movie =  await crud.get_movie(movie_id=movie_id, db=db)
    
    context = {'request': request, 'films': [movie]}
    return templates.TemplateResponse('/partials/table.html', context=context)


@app.put('/movie/{movie_id}', response_class=HTMLResponse)
async def update_movie(
    request: Request,
    title: Annotated[str, Form()], 
    director: Annotated[str, Form()],
    owner_id: Annotated[int, Form()],
    movie_id: int,
    db: Session = Depends(crud.get_db)
    ):
    
    movie = schemas.Movie(film_name=title, director=director, id=movie_id, owner_id=owner_id)
    movie_update =  await crud.update_movie(movie_id=movie_id, movie=movie ,db=db)
    
    context = {'request': request, 'films': [movie_update]}
    return templates.TemplateResponse('/partials/table.html', context=context)


@app.get('/movie/{movie_id}/edit', response_class=HTMLResponse)
async def get_movie(
    request: Request,
    movie_id: int,
    db: Session = Depends(crud.get_db)
    ):
    movie =  await crud.get_movie(movie_id=movie_id, db=db)  
    
    context = {'request': request, 'films': [movie]}
    return templates.TemplateResponse('/partials/table_edit.html', context=context)


@app.delete('/movie/{movie_id}/delete', response_class=HTMLResponse)
async def get_movie(
    request: Request,
    movie_id: int,
    db: Session = Depends(crud.get_db)
    ):
    
    await crud.delete_movie(movie_id=movie_id, db=db)
    
    context = {'request': request, 'films': []}
    return templates.TemplateResponse('/partials/table_edit.html', context=context)


