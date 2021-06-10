"""security stuff
not for production grade currently has hard coded key
"""
from datetime import datetime, timedelta
from typing import Optional

# pylint: disable=E0611
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session


# from database import get_db, Models


class Login(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class Hash:
    def __init__(self, schemes=("bcrypt")) -> None:
        self.pwd_cxt = CryptContext(schemes=schemes, deprecated="auto")

    def bcrypt(self, password: str):
        return self.pwd_cxt.hash(password)

    def verify(self, plain_password, hashed_password):
        return self.pwd_cxt.verify(plain_password, hashed_password)


class Security:
    """Security Class for apifactory"""

    def __init__(
        self,
        usermodel,
        get_db,
        key,
        algorithm="HS256",
        access_token_expire_minutes=30,
        login_route="login",
    ) -> None:

        self.secret_key = key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.hash = Hash()
        self.login = self.login_router(usermodel=usermodel, get_db=get_db)
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl=login_route)
        self.get_current_user = self.current_user_factory()

    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, credentials_exception):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
            TokenData(email=email)
        except JWTError as error:
            raise credentials_exception from error

    def login_router(self, usermodel, get_db):
        """[summary]

        Parameters
        ----------
        usermodel : [type]
            [description]
        get_db : [type]
            [description]
        """

        # pylint: disable=no-member
        router = APIRouter(tags=["Authentication"])
        # pylint: disable=W0612
        @router.post("/login")
        def login(
            request: OAuth2PasswordRequestForm = Depends(),
            db: Session = Depends(get_db),
        ):
            """[summary]

            Parameters
            ----------
            request : OAuth2PasswordRequestForm, optional
                [description], by default Depends()
            db : Session, optional
                [description], by default Depends(get_db)

            Returns
            -------
            [type]
                [description]

            Raises
            ------
            HTTPException
                [description]
            HTTPException
                [description]
            """
            user = (
                db.query(usermodel).filter(usermodel.Email == request.username).first()
            )
            if not user or not self.hash.verify(request.password, user.Password):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
                )

            access_token = self.create_access_token(data={"sub": user.Email})
            return {"access_token": access_token, "token_type": "bearer"}

        return router
        # pylint: enable=W0612

    def current_user_factory(self):
        """[summary]"""

        def get_current_user(data: str = Depends(self.oauth2_scheme)):
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

            return self.verify_token(data, credentials_exception)

        return get_current_user
