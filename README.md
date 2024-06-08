# FastAPI JWT Auth [![codecov](https://codecov.io/github/tistaharahap/fastapi-jwt-auth/graph/badge.svg?token=7UHRBSW1ZX)](https://codecov.io/github/tistaharahap/fastapi-jwt-auth)

FastAPI JWT Auth is a lightweight library designed to simplify the integration of JWT authentication into FastAPI applications. By strictly adhering to FastAPI conventions, it provides a seamless and straightforward authentication setup process. The library aims for 100% test coverage.

## Installing

```bash
pip install fastapi-jwt-auth3
```

**NOTE:** There are others who have written similar libraries with identical names. As an homage to the libraries that came before, I have decided to name this library `fastapi-jwt-auth3`.

## How To Use

This is an example single file implementation, let's name it `example.py`.

In order for this example to run, I took the liberty to use the `Faker` library to generate fake data. You can install it by running `pip install faker`.

```python
__all__ = ["app"]

import uuid

from fastapi import FastAPI, Depends, HTTPException

from faker import Faker
from jwcrypto import jwk
from pydantic import BaseModel, ConfigDict, EmailStr
from fastapi_jwt_auth3.jwtauth import FastAPIJWTAuth, KeypairGenerator, JWTPresetClaims, generate_jwt_token

# Initialize the Faker instance to generate fake data
fake = Faker()


# Define the token claims to be projected to when decoding JWT tokens
class TokenClaims(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    email: EmailStr
    iss: str
    aud: str
    exp: int
    sub: str
    iat: int
    jti: str


# Payload for our logins
class LoginIn(BaseModel):
    username: str
    password: str


app = FastAPI(title="FastAPI JWT Auth Example")

# For the purpose of this example, we will generate a new RSA keypair
private_key, public_key = KeypairGenerator.generate_rsa_keypair()

# Create a JWK key from the public key
jwk_key = jwk.JWK.from_pem(public_key.encode("utf-8"))
public_key_id = jwk_key.get("kid")

"""
    Initialize the FastAPIJWTAuth instance with an RSA algorithm. We need to provide a set of private and public key.
"""
jwt_auth = FastAPIJWTAuth(
    algorithm="RS256",
    base_url="http://localhost:8000",
    secret_key=private_key,
    public_key=public_key,
    public_key_id=public_key_id,
    issuer="https://localhost:8000",
    audience="https://localhost:8000",
    expiry=60 * 60 * 24 * 7,
    leeway=0,
    project_to=TokenClaims,
)


@app.get("/protected")
async def protected_route(claims: TokenClaims = Depends(jwt_auth)):
    return {"message": f"Hello, {claims.name}!"}


@app.post("/login")
async def login(payload: LoginIn):
    if payload.username != "username" or payload.password != "password":
        raise HTTPException(status_code=401, detail="Invalid credentials")

    preset_claims = JWTPresetClaims.factory(
        issuer=jwt_auth.issuer, audience=jwt_auth.audience, expiry=jwt_auth.expiry, subject=str(uuid.uuid4())
    )
    claims = {"name": fake.name(), "email": fake.email()}
    token = generate_jwt_token(
        header=jwt_auth.header, secret_key=jwt_auth.secret_key, preset_claims=preset_claims, claims=claims
    )
    return {"access_token": token}
```

We can run the example above with `uvicorn`.

```bash
uvicorn example:app --reload
```
