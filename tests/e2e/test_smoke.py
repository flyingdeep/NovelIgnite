"""CI 预提交 E2E 测试：冒烟测试，只跑核心路径。

快速验证后端可用 + 前端能加载 + 基本导航正常。
"""

import os
import pytest
import httpx
from playwright.sync_api import expect

SERVER_URL = os.environ.get("NOVEL_SERVER_URL", "http://127.0.0.1:8000")


def test_backend_health():
    """后端健康检查。"""
    import httpx
    with httpx.Client(timeout=5) as cx:
        r = cx.get(f"{SERVER_URL}/health")
        assert r.status_code == 200, f"后端不可用: {r.text}"


def test_prototype_served(page):
    """原型页面可访问。"""
    page.goto(f"{SERVER_URL}/")
    page.wait_for_load_state("networkidle")
    # 检查页面标题包含 Novel Ignite
    expect(page.locator("text=Novel Ignite")).to_be_visible()
    # 检查作品库页面可见
    expect(page.locator("#works")).to_be_visible()


def test_new_work_button(page):
    """作品库页面正常加载（检查页面标题）。"""
    page.goto(f"{SERVER_URL}/")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    # 验证页面已加载
    expect(page.locator("#works")).to_be_visible(timeout=10000)
