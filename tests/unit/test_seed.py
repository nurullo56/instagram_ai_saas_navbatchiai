import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.database.seed import seed_database


@pytest.mark.asyncio
async def test_seed_database_execution():
    mock_session = AsyncMock()
    # Mocking first query returning None so plans and user get created
    mock_session.execute.return_value = MagicMock(scalars=lambda: MagicMock(first=lambda: None))

    with patch("app.database.seed.async_session_factory") as mock_factory:
        mock_factory.return_value.__aenter__.return_value = mock_session
        await seed_database()

        assert mock_session.add.called
        assert mock_session.commit.called
