import pytest
from unittest.mock import AsyncMock, patch
from repository import (
    LinkRepository,
    delete_expired_links,
    normalize_url,
)
from database import LinkOrm
from schemas import SLinkAdd, SLinkResponse
from fastapi import HTTPException
from datetime import datetime, timedelta
import asyncio


@pytest.mark.asyncio
async def test_generate_short_code():
    code = LinkRepository.generate_short_code()
    assert len(code) == 8
    assert code.isalnum()


@pytest.mark.asyncio
async def test_normalize_url():
    assert normalize_url("HTTPS://Example.COM/Path%20") == "https://example.com/path "


@pytest.mark.asyncio
async def test_add_one_with_custom_alias():
    mock_session = AsyncMock()
    mock_session.execute.return_value.scalars.return_value.first.return_value = None

    with patch("repository.new_session", return_value=mock_session):
        data = SLinkAdd(original_url="https://example.com", custom_alias="test123")
        result = await LinkRepository.add_one(data)

        assert result.short_code == "test123"
        mock_session.add.assert_called_once()


@pytest.mark.asyncio
async def test_add_one_with_existing_alias():
    mock_session = AsyncMock()
    mock_session.execute.return_value.scalars.return_value.first.return_value = LinkOrm()

    with patch("repository.new_session", return_value=mock_session):
        data = SLinkAdd(original_url="https://example.com", custom_alias="taken")
        with pytest.raises(HTTPException) as exc:
            await LinkRepository.add_one(data)
        assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_find_by_short_code():
    mock_link = LinkOrm(short_code="abc123")
    mock_session = AsyncMock()
    mock_session.execute.return_value.scalars.return_value.first.return_value = mock_link

    with patch("repository.new_session", return_value=mock_session):
        result = await LinkRepository.find_by_short_code("abc123")
        assert result.short_code == "abc123"


@pytest.mark.asyncio
async def test_increment_click_count():
    mock_session = AsyncMock()
    with patch("repository.new_session", return_value=mock_session):
        await LinkRepository.increment_click_count(1)
        mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_delete_expired_links():
    mock_session = AsyncMock()
    with patch("repository.new_session", return_value=mock_session):
        await delete_expired_links()
        mock_session.execute.assert_called_once()
