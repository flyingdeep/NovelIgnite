"""E2E 测试：完整创作流程（创意 → 概念 → 蓝图 → 章节）。

运行：
    pytest tests/e2e -v
    pytest tests/e2e -v --headed --slowmo 300  # 调试模式

前置条件：
    - 后端运行在 http://127.0.0.1:8000
    - pip install -e ".[e2e]" && playwright install chromium
"""

import pytest
from playwright.sync_api import expect
import httpx


@pytest.fixture(scope="session")
def api():
    """HTTP 客户端，用于创建/清理测试数据。"""
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=10) as cx:
        yield cx


@pytest.fixture
def story_id(api):
    """通过 API 创建测试作品，返回 ID。测试结束后软删除。"""
    resp = api.post("/api/v1/works", json={"title": "E2E 测试作品"})
    assert resp.status_code == 201, f"创建作品失败: {resp.text}"
    sid = resp.json()["id"]
    yield sid
    # 清理：软删除
    api.delete(f"/api/v1/works/{sid}")


# ---------------------------------------------------------------------------
# Test Suite
# ---------------------------------------------------------------------------

class TestCreateAndNavigate:
    """测试作品创建与页面导航。"""

    def test_see_work_card(self, page, story_id):
        """作品库显示刚创建的作品卡片。"""
        expect(page.locator("#book-grid")).to_be_visible(timeout=10000)
        cards = page.locator(".book-card")
        expect(cards).to_have_count(1)
        expect(cards).to_contain_text("E2E 测试作品")

    def test_navigate_to_idea(self, page):
        """点击作品进入创意页面。"""
        page.locator(".book-card").click()
        expect(page.locator("#idea-input")).to_be_visible(timeout=10000)

    def test_fill_idea_and_count(self, page):
        """填写创意并验证字符计数更新。"""
        idea = "一位能听见墙壁心跳的人，正在调查一桩失踪案。"
        page.locator("#idea-input").fill(idea)
        expect(page.locator("#idea-input")).to_have_value(idea)
        expect(page.locator("#idea-count")).to_contain_text(str(len(idea)))


class TestConceptGeneration:
    """测试概念生成流程。"""

    def test_generate_concept(self, page, story_id):
        """点击生成概念，等待候选内容填充。"""
        page.goto(f"http://127.0.0.1:8000/?v=20260813&story={story_id}&screen=idea")
        page.locator("#idea-input").fill("一位能听见墙壁心跳的人。")
        page.locator("#generate-concept").click()
        # 等待概念页面加载
        expect(page.locator("#concept-genre")).to_be_visible(timeout=60000)
        # 检查字段有内容（由 fake adapter 生成）
        genre = page.locator("#concept-genre").input_value()
        assert genre, "genre 字段为空"

    def test_re_generate_concept(self, page, story_id):
        """重新生成概念按钮可用。"""
        page.goto(f"http://127.0.0.1:8000/?v=20260813&story={story_id}&screen=concept")
        btn = page.locator("#re-generate-concept")
        expect(btn).to_be_visible()
        btn.click()
        # 重新生成后字段应更新
        page.wait_for_timeout(2000)
        genre = page.locator("#concept-genre").input_value()
        assert genre  # 不为空


class TestBlueprintFlow:
    """测试蓝图生成与确认。"""

    def test_generate_blueprint(self, page, story_id):
        """生成蓝图并验证内容分区。"""
        page.goto(f"http://127.0.0.1:8000/?v=20260813&story={story_id}&screen=blueprint")
        page.locator("#generate-blueprint").click()
        # 等待蓝图内容出现
        expect(page.locator("#blueprint-content")).to_contain_text("人物", timeout=60000)
        # 验证各个 tab 存在
        expect(page.locator('[data-blueprint="characters"]')).to_be_visible()
        expect(page.locator('[data-blueprint="world"]')).to_be_visible()
        expect(page.locator('[data-blueprint="timeline"]')).to_be_visible()
        expect(page.locator('[data-blueprint="arc"]')).to_be_visible()

    def test_confirm_blueprint(self, page, story_id):
        """确认蓝图后状态更新。"""
        page.goto(f"http://127.0.0.1:8000/?v=20260813&story={story_id}&screen=blueprint")
        page.locator("#generate-blueprint").click()
        expect(page.locator("#blueprint-content")).to_contain_text("人物", timeout=60000)
        page.locator("#confirm-blueprint").click()
        expect(page.locator("#blueprint-stage-note")).to_contain_text("已确认", timeout=30000)
        # 进入章节按钮应出现
        expect(page.locator("#to-chapters")).to_be_visible()


class TestChapterPlanning:
    """测试章节规划流程。"""

    def test_generate_chapters(self, page, story_id):
        """生成章节计划并验证列表。"""
        page.goto(f"http://127.0.0.1:8000/?v=20260813&story={story_id}&screen=chapters")
        page.locator("#generate-chapter-plan").click()
        # 等待章节卡片出现
        expect(page.locator("#chapter-grid")).to_contain_text("第 1 章", timeout=60000)
        # 检查章节状态
        expect(page.locator(".chapter-card")).to_have_count(1)

    def test_navigate_to_workspace(self, page, story_id):
        """进入工作台。"""
        page.goto(f"http://127.0.0.1:8000/?v=20260813&story={story_id}&screen=workspace")
        expect(page.locator("#scene-content")).to_be_visible(timeout=10000)


class TestModalInteraction:
    """测试弹窗交互。"""

    def test_config_modal(self, page, story_id):
        """打开/关闭生成设置弹窗。"""
        page.goto(f"http://127.0.0.1:8000/?v=20260813&story={story_id}&screen=idea")
        page.locator('[data-config]').click()
        expect(page.locator("#config-modal")).to_be_visible()
        # 修改配置
        page.locator("#config-model").select_option("Agnes 2.5 Flash")
        expect(page.locator("#config-modal select")).to_have_value("Agnes 2.5 Flash")
        # 保存
        page.locator("#save-config").click()
        expect(page.locator("#config-modal")).not_to_be_visible()

    def test_tips_modal(self, page, story_id):
        """打开/关闭写法提示弹窗。"""
        page.goto(f"http://127.0.0.1:8000/?v=20260813&story={story_id}&screen=idea")
        page.locator("#show-write-tips").click()
        expect(page.locator("#tips-modal")).to_be_visible()
        expect(page.locator("#tips-title")).to_contain_text("如何完整描述一个创意")
        # 关闭
        page.locator("[data-close-tips]").click()
        expect(page.locator("#tips-modal")).not_to_be_visible()

    def test_help_toast(self, page, story_id):
        """帮助按钮触发 toast。"""
        page.goto(f"http://127.0.0.1:8000/?v=20260813&story={story_id}&screen=idea")
        page.locator('[aria-label="帮助"]').click()
        # toast 短暂显示
        expect(page.locator("[data-toast]")).to_be_visible(timeout=5000)


class TestNavigation:
    """测试顶部导航。"""

    def test_stepbar_navigation(self, page, story_id):
        """步骤条导航正常工作。"""
        page.goto(f"http://127.0.0.1:8000/?v=20260813&story={story_id}&screen=idea")
        # 点击「作品库」
        page.locator('[data-nav="works"]').click()
        expect(page.locator("#works")).to_be_visible()
        # 点击「创意」
        page.locator('[data-nav="idea"]').click()
        expect(page.locator("#idea")).to_be_visible()

    def test_breadcrumb_updates(self, page, story_id):
        """面包屑跟随当前页面更新。"""
        page.goto(f"http://127.0.0.1:8000/?v=20260813&story={story_id}&screen=idea")
        expect(page.locator("#crumb")).to_contain_text("创意")
        page.locator('[data-nav="concept"]').click()
        expect(page.locator("#crumb")).to_contain_text("概念")
