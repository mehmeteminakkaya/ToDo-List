from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import Request
from fastapi import APIRouter, Depends, HTTPException
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm , OAuth2PasswordBearer
from ..database import SessionLocal
from ..models import Users
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

script_dir = os.path.dirname(__file__)
template_dir = os.path.join(os.path.dirname(script_dir), "templates")
templates = Jinja2Templates(directory=template_dir)

SECRET_KEY = "f8dsf70sad07ef0708s7dsv87dsv0"
ALGORITHM = "HS256"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DbSession = Annotated[Session, Depends(get_db)]

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")

class CreateUserRequest(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str


class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(username : str , user_id : int , role : str , expires_delta : timedelta):
    encode = {'sub' : username , 'id' : user_id , 'role' : role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": int(expires.timestamp())})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str , db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role = payload.get("role")

        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username, "id": user_id , 'role': user_role}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/login-page")
def render_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register-page")
def render_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/" , status_code=status.HTTP_201_CREATED)
async def create_user(db: DbSession, create_user_request: CreateUserRequest):
    user = Users(
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        email=create_user_request.email,
        role=create_user_request.role,
        is_active=True,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        phone_number=create_user_request.phone_number
    )
    db.add(user)
    db.commit()


@router.post("/token" , response_model=Token)
async def login_for_access_token(form_data : Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: DbSession):
    user = authenticate_user(form_data.username, form_data.password , db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    token = create_access_token(user.username , user.id, user.role , timedelta(minutes = 60))
    return {"access_token": token, "token_type": "bearer"}

