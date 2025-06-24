from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm # For a more standard login form if preferred
from starlette.responses import JSONResponse

from app.schemas.user import UserCreate, UserOut
from app.schemas.auth import Token, UserLogin
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token, get_current_active_user
# from app.services.user_service import UserService # We'll create this simple service
from beanie.exceptions import RevisionIdWasChanged

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Simple user service for DB operations (can be expanded)
class UserService:
    @staticmethod
    async def get_user_by_email(email: str) -> User | None:
        return await User.find_one(User.email == email)

    @staticmethod
    async def create_user(user_create: UserCreate) -> User:
        existing_user = await UserService.get_user_by_email(user_create.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        hashed_password = get_password_hash(user_create.password)
        user = User(
            email=user_create.email,
            hashed_password=hashed_password,
            full_name=user_create.full_name
        )
        await user.insert()
        return user

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate):
    try:
        user = await UserService.create_user(user_in)
        # Manually construct UserOut from User model, converting id
        return UserOut(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at
        )
    except HTTPException as e:
        raise e # Re-raise HTTPException to be handled by global handler
    except Exception as e: # Catch other potential errors during user creation
        # Log the error using Loguru (assuming logger is configured in main and accessible)
        # from loguru import logger # Or pass logger around
        # logger.error(f"Error during user registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during user registration.",
        )


@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: UserLogin):
    user = await UserService.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.options("/login")
async def preflight_login():
    return JSONResponse(
        status_code=200,
        content={"detail": "CORS preflight OK"},
        headers={
            "Access-Control-Allow-Origin": "https://ria-virid.vercel.app",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )


# Alternative login using OAuth2PasswordRequestForm for form data (Content-Type: application/x-www-form-urlencoded)
# @router.post("/token", response_model=Token)
# async def login_for_access_token_form(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = await UserService.get_user_by_email(form_data.username)
#     if not user or not verify_password(form_data.password, user.hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     if not user.is_active:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
#     access_token = create_access_token(data={"sub": user.email})
#     return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    # The User object from get_current_active_user might not be directly convertible
    # to UserOut if id is not str. Ensure conversion.
    return UserOut(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )
