import pytest
from httpx import AsyncClient
from main import app
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_app_lifespan(client):
    response = await client.get("/docs")
    assert response.status_code == 200
    logger.info("Приложение запущено, документация доступна")

@pytest.mark.asyncio
async def test_auth_router(client):
    response = await client.post("/auth/token", data={"username": "test", "password": "test"})
    assert response.status_code in [200, 401]
    logger.info("Тест аутентификации пройден")

@pytest.mark.asyncio
async def test_links_router(client):
    response = await client.post("/links/", json={"original_url": "https://example.com"})
    assert response.status_code in [200, 403]
    logger.info("Тест роутера ссылок пройден")

