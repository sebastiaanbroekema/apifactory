"""Module pertaining to security, contains pydantic models required for handeling tokens and login.
Contains a class for hashing and a class handeling login and JWT handeling.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from collections.abc import Callable


# pylint: disable=E0611
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import Table


# from database import get_db, Models


class Login(BaseModel):
    """Pydantic schema for handeling login with username and password."""

    username: str
    password: str


class Token(BaseModel):
    """Pydantic schema defining"""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Pydantic schema defining the data of JWT tokens."""

    email: Optional[str] = None


class Hash:
    # pylint: disable=C0301
    """class for hashing of paswords contains option for having a salt as a seperate secret.



    :param schemes: Define which password hashing algorithm to use, defaults to ("bcrypt"), defaults to ("bcrypt")
    :type schemes: tuple, optional
    :param salt: Inaptly named version of a pepper. String that defines the pepper key to use in encription, defaults to None
    :type salt: [type], optional


    Basic use is instanciating the Hash class. Afterwards input can be hashed and verified.


    >>> hasher = Hash()
    >>> hash = hasher.hash('somepassword')
    >>> hasher.verify('somepassword', hash)
    True
    """
    # pylint: enable=C0301

    def __init__(self, schemes=("bcrypt"), salt=None) -> None:
        if not salt:
            salt = ""
        self.salt = salt
        self.pwd_cxt = CryptContext(schemes=schemes, deprecated="auto")

    def hash(self, password: str) -> str:
        """function to encrypt a password

        :param password: It's the password to encrypt.
        :type password: str
        :return: Hashed password.
        :rtype: str
        """

        return self.pwd_cxt.hash(f"{self.salt}{password}")

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verifies if the provided password is hashed to the hashed_password

        :param plain_password: It's the password to verify.
        :type plain_password: str
        :param hashed_password: Hash to test password against.
        :type hashed_password: str
        :return: Whether or not the plain_password can be hashed to the same hashed_password.
        :rtype: bool
        """
        return self.pwd_cxt.verify(f"{self.salt}{plain_password}", hashed_password)


class Security:
    # pylint: disable=C0301
    """Class responsible for login and jwt handeling.


    :param usermodel: SQLalchemy table defining the table containing information about the users of the api.
    :type usermodel: Table
    :param get_db: Function to acquire a database session
    :type get_db: Callable
    :param jwt_key: Key for encrypting JWT
    :type jwt_key: str
    :param algorithm: Algorithm to use for JWT encryption, defaults to "HS256"
    :type algorithm: str, optional
    :param hash_class: Hashing class to use for hashing and verifying passwords.
    :type hash_class: Hash, optional
    :param access_token_expire_minutes: Defines howlong a token is valid after issuing, defaults to 30
    :type access_token_expire_minutes: int, optional
    :param login_route: route you desire the login endpoint to be, defaults to "login"
    :type login_route: str, optional
    :param password_salt: If a password salt (actually a pepper) is to be provided, defaults to None
    :type password_salt: Optional[str], optional
    :param hash_scheme: Scheme to use for pasword hashing.
    :type hash_scheme: Tuple[str], optional

    Basic use requires a Table containing the username/hashed passwords, method to aquire database session and a key to hash the json web token.


    >>> sec = Security(Table, get_db, jwt_key)

    More advanced use can include altering which hashing class is passed to the security class.
    This can be done to have a hashing class with different behavior.

    >>> class NewHashing(Hash):
    ...     "somehow different"
    >>> sec = Security(Table, get_db, jwt_key, NewHashing)


    """
    # pylint: enable=C0301
    def __init__(
        self,
        usermodel: Table,
        get_db: Callable,
        jwt_key: str,
        algorithm="HS256",
        hash_class: Hash = Hash,
        access_token_expire_minutes: int = 30,
        login_route: str = "login",
        password_salt: Optional[str] = None,
        hash_scheme: Tuple[str] = ("bcrypt"),
    ) -> None:

        self.secret_key = jwt_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.hash = hash_class(hash_scheme, salt=password_salt)
        self.login = self.login_router(usermodel=usermodel, get_db=get_db)
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl=login_route)
        self.get_current_user = self.current_user_factory()

    def create_access_token(self, data: dict) -> str:
        """function for creating the encoded access token.
        Adds the required data to the token then uses the secret key to
        encode the data into a jwt.

        :param data: Dictionary containing the data for the jwt.
        :type data: dict
        :return: encrypted jwt.
        :rtype: str
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, credentials_exception: Exception):
        # pylint: disable=C0301
        """Function for checking the validity of jwt tokens.
        Checks if the required fields are present and if the JWT can be recreated.

        :param token: JWT token provided by the endpoint user.
        :type token: str
        :param credentials_exception: Exception to raise when faced with invalid credentials.
        :type credentials_exception: Exception
        :raises credentials_exception: The provided token is invalid and the user is not granted acces to the endpoint.
        """
        # pylint: enable=C0301
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
            TokenData(email=email)
        except JWTError as error:
            raise credentials_exception from error

    def login_router(self, usermodel: Table, get_db: Callable) -> APIRouter:
        # pylint: disable=C0301
        """Creates the login_router and route.


        :param usermodel: SQLalchemy table defining the table containing information about the users of the api.
        :type usermodel: Table
        :param get_db: Function to acquire a database session
        :type get_db: Callable
        :raises HTTPException: raises HTTP 404 error if either user or password are invalid
        :return: APIRouter for login will be added to the app with ApiFactory.
        :rtype: APIRouter
        """
        # pylint: enable=C0301

        # pylint: disable=no-member
        router = APIRouter(tags=["Authentication"])
        # pylint: disable=W0612
        @router.post("/login")
        def login(
            request: OAuth2PasswordRequestForm = Depends(),
            db: Session = Depends(get_db),
        ):
            """[summary]

            [extended_summary]

            :param request: Login request form, defaults to Depends()
            :type request: OAuth2PasswordRequestForm, optional
            :param db: Database session, defaults to Depends(get_db)
            :type db: Session, optional
            :raises HTTPException: [description]
            :return: [description]
            :rtype: [type]
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

    def current_user_factory(self) -> Callable:
        """Function to create a get_current_user function.
        Raises http 401 error if the user cannot be authenticated.

        :return: Function that tests if the provided token is valid
        :rtype: Callable
        """

        def get_current_user(data: str = Depends(self.oauth2_scheme)):
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

            return self.verify_token(data, credentials_exception)

        return get_current_user
