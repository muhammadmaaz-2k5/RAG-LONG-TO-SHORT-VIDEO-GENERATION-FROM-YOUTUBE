import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.core.database import engine
from app.main import app

@pytest_asyncio.fixture(scope="function")
async def client():
    # Dispose connection pool so each test gets fresh connection on current event loop
    await engine.dispose()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    await engine.dispose()
