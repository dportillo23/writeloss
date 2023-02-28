from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, status
from routers.mock_users import users_db
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from routers.schemas.users_schemas import User, UserDB
from routers.schemas.auth_schemas import Token, TokenData
from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv
import os

# -----------------------------------------------
# CONSTANTS
# -----------------------------------------------

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv('ACCESS_TOKEN_EXPIRE_DAYS'))

credential_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"}
)

# -----------------------------------------------
# INITIALIZERS
# -----------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2 = OAuth2PasswordBearer(tokenUrl='/auth/login')

router = APIRouter(prefix='/auth')

# -----------------------------------------------
# UTILITY FUNCTIONS
# -----------------------------------------------

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_db_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_db_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_db_user(users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# -----------------------------------------------
# API
# -----------------------------------------------

@router.post('/login', response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(users_db, form.username, form.password)
    if not user:
        raise credential_exception

    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={'sub': user.username},
        expires_delta=access_token_expires
        )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get('/users/me')
async def me(user: User = Depends(get_current_active_user)):
    return user
