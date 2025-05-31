from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.core.config import settings
from app.schemas.auth import TokenData # Make sure this path is correct
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.models.user import User # Assuming User model is in app.models.user
# from app.services.user_service import UserService # If you created a separate user_service.py

# If UserService is not separate, we'll need a way to get user by email here
# For simplicity, let's assume a direct User.find_one call for now.
# If UserService was in app/api/auth_routes.py, that's not ideal for direct import here.
# A better structure would be app/services/user_service.py

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login") # tokenUrl points to login route

async def get_user_by_email_for_auth(email: str) -> User | None:
    # This helper is because UserService might not be easily accessible
    # or to avoid circular dependencies if UserService itself uses Depends.
    return await User.find_one(User.email == email)

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# JWT Handling
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: Optional[str] = payload.get("sub") # Assuming we store email in "sub"
        if email is None:
            return None # Or raise an exception
        return TokenData(email=email)
    except JWTError:
        return None # Or raise an appropriate exception

async def get_current_active_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = decode_access_token(token)
    if token_data is None or token_data.email is None:
        raise credentials_exception

    # user = await UserService.get_user_by_email(token_data.email) # If using UserService
    user = await get_user_by_email_for_auth(token_data.email) # Using direct model access

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user
