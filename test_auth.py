import pytest
from httpx import AsyncClient
from fastapi import FastAPI, HTTPException
from auth import AuthService, auth_router, generate_user_secret_key, active_users
from schemas import UserRegister, UserResponse
from unittest.mock import AsyncMock, patch
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(auth_router)

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_generate_user_secret_key():
    key = generate_user_secret_key("test_user")
    assert isinstance(key, str)
    assert len(key) == 64  # SHA-256 hash length

@pytest.mark.asyncio
async def test_register_user_success():
    mock_user = UserResponse(id=1, username="test_user")
    with patch("auth.new_session", new_callable=AsyncMock) as mock_session:
        mock_session.return_value.__aenter__.return_value.execute.return_value.scalar.return_value = None
        mock_session.return_value.__aenter__.return_value.add = AsyncMock()
        result = await AuthService.register_user(UserRegister(username="test_user", password="123456"))
        assert result.username == mock_user.username

@pytest.mark.asyncio
async def test_register_user_existing():
    with patch("auth.new_session", new_callable=AsyncMock) as mock_session:
        mock_session.return_value.__aenter__.return_value.execute.return_value.scalar.return_value = True
        with pytest.raises(HTTPException) as exc:
            await AuthService.register_user(UserRegister(username="existing_user", password="123456"))
        assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_authenticate_user_success():
    mock_user = AsyncMock()
    mock_user.password_hash = "$2b$12$fakehash"  # Пример хеша
    with patch("auth.new_session", new_callable=AsyncMock) as mock_session:
        mock_session.return_value.__aenter__.return_value.execute.return_value.scalar.return_value = mock_user
        with patch("auth.pwd_context.verify", return_value=True):
            user = await AuthService.authenticate_user("test_user", "123456")
            assert user.username == mock_user.username

@pytest.mark.asyncio
async def test_authenticate_user_fail():
    with patch("auth.new_session", new_callable=AsyncMock) as mock_session:
        mock_session.return_value.__aenter__.return_value.execute.return_value.scalar.return_value = None
        with pytest.raises(HTTPException) as exc:
            await AuthService.authenticate_user("invalid_user", "wrong_pass")
        assert exc.value.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    test_token = "test_token"
    active_users[test_token] = UserResponse(id=1, username="test_user")
    user = await AuthService.get_current_user(test_token)
    assert user.username == "test_user"

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    user = await AuthService.get_current_user("invalid_token")
    assert user is None

@pytest.mark.asyncio
async def test_login_for_token(client):
    with patch("auth.AuthService.authenticate_user", return_value=AsyncMock(id=1, username="test_user")):
        response = await client.post("/auth/token", data={"username": "test_user", "password": "123456"})
        assert response.status_code == 200
        assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_register_endpoint(client):
    with patch("auth.AuthService.register_user", return_value=UserResponse(id=1, username="test_user")):
        response = await client.post("/auth/register", data={"username": "test_user", "password": "123456"})
        assert response.status_code == 200
        assert response.json()["username"] == "test_user"
