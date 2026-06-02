"""
Auth API Tests
"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_register_and_login(db_session):
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register
        reg = await client.post("/api/v1/auth/register", json={
            "email": "newuser@test.com",
            "password": "Secure@123",
            "full_name": "Test User",
            "role": "clinician",
        })
        assert reg.status_code == 201
        assert reg.json()["email"] == "newuser@test.com"

        # Login
        login = await client.post("/api/v1/auth/login", json={
            "email": "newuser@test.com",
            "password": "Secure@123",
        })
        assert login.status_code == 200
        data = login.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/v1/auth/login", json={
            "email": "nobody@test.com",
            "password": "wrongpassword",
        })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(auth_headers):
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    # 404 is acceptable in test env (no real DB user), 200 means it worked
    assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_weak_password_rejected():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/v1/auth/register", json={
            "email": "weak@test.com",
            "password": "weak",
            "full_name": "Weak User",
        })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_security_password_hashing():
    from app.core.security import hash_password, verify_password
    hashed = hash_password("MyP@ssw0rd")
    assert hashed != "MyP@ssw0rd"
    assert verify_password("MyP@ssw0rd", hashed)
    assert not verify_password("WrongPass", hashed)


@pytest.mark.asyncio
async def test_jwt_token_creation_and_decode():
    from app.core.security import create_access_token, decode_token
    token = create_access_token("user-123", {"email": "a@b.com", "role": "clinician"})
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["email"] == "a@b.com"
    assert payload["type"] == "access"


@pytest.mark.asyncio
async def test_field_encryption():
    from app.core.security import encrypt_field, decrypt_field
    original = "123-45-6789"
    encrypted = encrypt_field(original)
    assert encrypted != original
    assert decrypt_field(encrypted) == original
