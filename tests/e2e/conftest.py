"""E2E 测试会话级 fixtures。

- api: HTTP 客户端，用于创建/清理测试数据（不经过浏览器）
- story_id: 每个测试独立的测试作品 ID
"""

import pytest
import httpx


@pytest.fixture(scope="session")
def api():
    """HTTP 客户端，用于创建/清理测试数据。"""
    import os
    server_url = os.environ.get("NOVEL_SERVER_URL", "http://127.0.0.1:8000")
    with httpx.Client(base_url=server_url, timeout=10) as cx:
        yield cx


@pytest.fixture
def story_id(api: httpx.Client):
    """通过 API 创建测试作品，返回 ID。测试结束后软删除。"""
    resp = api.post("/api/v1/works", json={"title": "E2E 测试作品"})
    assert resp.status_code == 201, f"创建作品失败: {resp.text}"
    sid = resp.json()["id"]
    yield sid
    # 清理：软删除
    api.delete(f"/api/v1/works/{sid}")
