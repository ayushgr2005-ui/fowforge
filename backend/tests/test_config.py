from app.core.config import Settings


def test_settings_validation():
    s = Settings(database_url="postgresql+asyncpg://x", redis_url="redis://x")
    assert s.top_k == 6
    assert s.max_upload_mb == 10
