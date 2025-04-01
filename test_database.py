import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import (
    engine,
    new_session,
    UserOrm,
    LinkOrm,
    create_tables,
    delete_tables,
    Model,
)
from datetime import datetime, timedelta
import asyncio

@pytest.fixture(scope="module")
async def setup_db():
    await create_tables()
    yield
    await delete_tables()

@pytest.mark.asyncio
async def test_create_and_drop_tables():
    await create_tables()
    async with engine.begin() as conn:
        tables = await conn.run_sync(lambda sync_conn: sync_conn.execute("SELECT name FROM sqlite_master WHERE type='table'"))
        table_names = [row[0] for row in tables]
        assert "users" in table_names
        assert "links" in table_names

    await delete_tables()
    async with engine.begin() as conn:
        tables = await conn.run_sync(lambda sync_conn: sync_conn.execute("SELECT name FROM sqlite_master WHERE type='table'"))
        table_names = [row[0] for row in tables]
        assert "users" not in table_names
        assert "links" not in table_names

@pytest.mark.asyncio
async def test_user_model(setup_db):
    async with new_session() as session:
        user = UserOrm(username="test_user", password_hash="hashed_password")
        session.add(user)
        await session.commit()

        result = await session.execute(select(UserOrm).where(UserOrm.username == "test_user"))
        saved_user = result.scalar_one()
        assert saved_user.username == "test_user"
        assert saved_user.password_hash == "hashed_password"

@pytest.mark.asyncio
async def test_link_model(setup_db):
    async with new_session() as session:
        link = LinkOrm(
            original_url="https://example.com",
            short_code="abc123",
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        session.add(link)
        await session.commit()

        result = await session.execute(select(LinkOrm).where(LinkOrm.short_code == "abc123"))
        saved_link = result.scalar_one()
        assert saved_link.original_url == "https://example.com"
        assert saved_link.click_count == 0
        assert saved_link.user_id is None
