import uuid
from secrets import token_hex
from typing import Tuple

import pytest
import pytest_asyncio
from faker import Faker
from fastapi import FastAPI, Depends, HTTPException
from httpx import AsyncClient, ASGITransport
from jwcrypto import jwk
from pydantic import BaseModel, ConfigDict, EmailStr

from fastapi_jwt_auth.jwtauth import KeypairGenerator, FastAPIJWTAuth, generate_jwt_token
from fastapi_jwt_auth.models import JWTHeader, JWTPresetClaims


class DecodedTokenModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    email: EmailStr
    iss: str
    aud: str
    exp: int
    sub: str
    iat: int
    jti: str


class LoginIn(BaseModel):
    username: str
    password: str


fake = Faker()


@pytest.fixture(autouse=True)
def jwt_auth(rsa_public_private_keypair: Tuple[str, str, str]) -> Tuple[FastAPIJWTAuth, JWTHeader, str, str]:
    private_key, public_key, public_key_id = rsa_public_private_keypair

    jwt_header = JWTHeader.factory(
        algorithm="RS256",
        public_key_id=public_key_id,
        base_url="http://testapi",
    )

    jwt_auth = FastAPIJWTAuth(
        header=jwt_header,
        issuer="http://testapi",
        secret_key=private_key,
        audience="http://testapi",
        public_key=public_key,
        expiry=3600,
        leeway=0,
        project_to=DecodedTokenModel,
    )
    return jwt_auth, jwt_header, private_key, public_key


@pytest.fixture(autouse=True)
def app(jwt_auth: Tuple[FastAPIJWTAuth, JWTHeader, str, str]) -> FastAPI:
    auth, jwt_header, private_key, public_key = jwt_auth

    app = FastAPI(title="FastAPIJWTAuth Test App")
    auth.init_app(app=app)

    @app.get("/test")
    async def test(auth: DecodedTokenModel = Depends(auth)):
        return {"message": "Hello, World!"}

    @app.post("/login")
    async def login(payload: LoginIn):
        if payload.username != "username" or payload.password != "password":
            raise HTTPException(status_code=401, detail="Invalid credentials")

        preset_claims = JWTPresetClaims.factory(
            issuer="http://testapi", audience="http://testapi", expiry=60 * 60, subject=str(uuid.uuid4())
        )
        claims = {"name": fake.name(), "email": fake.email()}
        token = generate_jwt_token(
            header=jwt_header, preset_claims=preset_claims, secret_key=private_key, claims=claims
        )
        return {"access_token": token}

    return app


@pytest_asyncio.fixture(autouse=True)
async def client(app: FastAPI) -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testapi") as ac:
        yield ac


@pytest.fixture(autouse=True)
def rsa_public_private_keypair() -> Tuple[str, str, str]:
    private_key, public_key = KeypairGenerator.generate_rsa_keypair()
    jwk_key = jwk.JWK.from_pem(public_key.encode("utf-8"))
    return private_key, public_key, jwk_key.get("kid")


@pytest.fixture(autouse=True)
def jwt_secret_key() -> str:
    return token_hex(247)


@pytest.fixture(autouse=True)
def ecdsa_public_private_keypair() -> Tuple[str, str]:
    return KeypairGenerator.generate_ecdsa_keypair()


@pytest.fixture(autouse=True)
def es256k_public_private_keypair() -> Tuple[str, str]:
    return KeypairGenerator.generate_es256k_keypair()


@pytest.fixture(autouse=True)
def eddsa_public_private_keypair() -> Tuple[str, str]:
    return KeypairGenerator.generate_eddsa_keypair()