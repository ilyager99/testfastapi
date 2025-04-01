import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from router import router
from unittest.mock import AsyncMock, patch
from schemas import SLinkResponse, SLinkStatsResponse, UserResponse
from datetime import datetime, timedelta
import logging

app = FastAPI()
app.include_router(router)
client = TestClient(app)

logger = logging.getLogger(__name__)

@pytest.fixture
def mock_user():
    return UserResponse(id=1, username="testuser")

@pytest.fixture
def mock_link():
    return SLinkResponse(
        id=1,
        original_url="https://example.com",
        short_code="abc123",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),
        user_id=1,
        click_count=0,
        short_url="http://test/links/abc123"
    )

@pytest.fixture
def mock_link_stats():
    return SLinkStatsResponse(
        original_url="https://example.com",
        created_at=datetime.utcnow(),
        click_count=5,
        last_used_at=datetime.utcnow()
    )

@pytest.mark.asyncio
async def test_search_link_by_original_url(mock_link):
    with patch("router.LinkRepository.find_by_original_url", return_value=mock_link):
        response = client.get("/links/search?original_url=https://example.com")
        assert response.status_code == 200
        data = response.json()
        assert data["original_url"] == "https://example.com"
        assert "short_url" in data

@pytest.mark.asyncio
async def test_shorten_link_authenticated(mock_user, mock_link):
    with patch("router.get_current_user", return_value=mock_user), \
         patch("router.LinkRepository.add_one", return_value=mock_link):
        response = client.post(
            "/links/shorten",
            data={"original_url": "https://example.com"},
            headers={"Authorization": "Bearer testtoken"}
        )
        assert response.status_code == 200
        assert response.json()["user_id"] == 1

@pytest.mark.asyncio
async def test_shorten_link_unauthenticated(mock_link):
    with patch("router.get_current_user", return_value=None), \
         patch("router.LinkRepository.add_one", return_value=mock_link):
        response = client.post(
            "/links/shorten",
            data={"original_url": "https://example.com"}
        )
        assert response.status_code == 200
        assert response.json()["user_id"] is None

@pytest.mark.asyncio
async def test_redirect_link(mock_link):
    with patch("router.LinkRepository.find_by_short_code", return_value=mock_link), \
         patch("router.LinkRepository.increment_click_count", new_callable=AsyncMock):
        response = client.get("/links/abc123", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "https://example.com"

@pytest.mark.asyncio
async def test_delete_link_authenticated(mock_user):
    with patch("router.get_current_user", return_value=mock_user), \
         patch("router.LinkRepository.find_by_short_code", return_value=AsyncMock(user_id=1)), \
         patch("router.LinkRepository.delete_by_short_code", new_callable=AsyncMock):
        response = client.delete(
            "/links/abc123",
            headers={"Authorization": "Bearer testtoken"}
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}

@pytest.mark.asyncio
async def test_update_link(mock_user, mock_link):
    with patch("router.get_current_user", return_value=mock_user), \
         patch("router.LinkRepository.find_by_short_code", return_value=AsyncMock(user_id=1)), \
         patch("router.LinkRepository.update_original_url", return_value=mock_link):
        response = client.put(
            "/links/abc123",
            data={"new_url": "https://newexample.com"},
            headers={"Authorization": "Bearer testtoken"}
        )
        assert response.status_code == 200
        assert response.json()["original_url"] == "https://example.com"

@pytest.mark.asyncio
async def test_link_stats(mock_link_stats):
    with patch("router.LinkRepository.find_by_short_code", return_value=mock_link_stats):
        response = client.get("/links/abc123/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["click_count"] == 5
        assert "last_used_at" in data
