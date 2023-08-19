from typing import Annotated
from fastapi import FastAPI, Request, Form, Header, Depends, HTTPException, security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from sqlalchemy.orm import Session

from backend import crud, models, schemas
from backend.database import SessionLocal, engine

crud.create_database()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.post("/api/users/")
async def create_user(user: schemas.UserCreate, db: Session = Depends(crud.get_db)):
    db_user = await crud.get_user_by_email(db=db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already in use!")
    
    user = await crud.create_user(db=db, user=user)

    return await crud.create_token(user= user)


@app.post("/api/token")
async def generate_token(
    form_data: security.OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(crud.get_db)
):
    user = await crud.authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid Credentials!")
    
    return await crud.create_token(user)


@app.get("/api/users/me", response_model=schemas.User)
async def get_user(user: schemas.User = Depends(crud.get_current_user)):
    return user

@app.get("/login", response_class=HTMLResponse)
async def movielist(request: Request):
    return templates.TemplateResponse("login.html", context={'request': request, 'token':''})

@app.post("/auth", response_class=HTMLResponse)
async def movielist(
    request: Request, 
    username: Annotated[str, Form()], 
    password: Annotated[str, Form()],
    db: Session = Depends(crud.get_db)
):
    user = await crud.authenticate_user(username, password, db)
    
    if not user:
       token = {'access_token': 'Innvalid username'}
    else:
        token = await crud.create_token(user)
        
    context = {'request': request, 'token': token}
    
    return templates.TemplateResponse('/partials/token.html', context=context)


@app.get("/", response_class=HTMLResponse)
async def movielist(request: Request, hx_request: Optional[str] = Header(None)):
    films = [
        {'name': 'Blade Runner', 'director': 'Ridley Scott'},
        {'name': 'Pulp Fiction', 'director': 'Quentin Tarantino'},
        {'name': 'Mulholland Drive', 'director': 'David Lynch'},
    ]
    context = {"request": request, 'films': films}
    if hx_request:
        return templates.TemplateResponse("partials/table.html", context)
    return templates.TemplateResponse("index.html", context)

@app.post('/add-film/', response_class=HTMLResponse)
async def add_film(request: Request, title: Annotated[str, Form()], director: Annotated[str, Form()]): 
    data = [
        {'name': title, 'director': director},
    ]
    context = {'request': request, 'films': data}
    return templates.TemplateResponse('/partials/table.html', context=context)


