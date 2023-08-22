from backend import crud, models, schemas

user = crud.get_user(username='bh', db=crud.get_db())

print(user)

schemas.User()