"""E2E 测试：完整创作流程（创意 → 概念 → 蓝图 → 章节 → 工作台正文 → 阅读）。

适配当前 SPA：步骤条导航 + localStorage，不使用 URL 参数。
建议在「无 API Key」的服务器上运行（生成走确定性回退，快速稳定）：

    $env:DATABASE_URL="sqlite:///./e2e_test.db"
    $env:AGNES_API_KEY=""; $env:DEEPSEEK_API_KEY=""; $env:GROK_API_KEY=""
    py -3.13 -m uvicorn app.main:app --host 127.0.0.1 --port 8010

    $env:NOVEL_SERVER_URL="http://127.0.0.1:8010"; pytest tests/e2e -v

前置条件：
    - 后端运行（默认 http://127.0.0.1:8000，可用 NOVEL_SERVER_URL 覆盖）
    - pip install -e ".[e2e]" && playwright install chromium
"""

import os
import pytest
import httpx
from playwright.sync_api import expect

SERVER_URL = os.environ.get("NOVEL_SERVER_URL", "http://127.0.0.1:8000")


# ---------------------------------------------------------------------------
# Session fixtures: one API client + one fully-prepared story
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def api():
    with httpx.Client(base_url=SERVER_URL, timeout=120) as cx:
        yield cx


def advance_story(api: httpx.Client, sid: str) -> dict:
    """通过 API 把故事推进到「工作台就绪」：概念→蓝图→章节→场景→节拍→场景1正文。

    返回 {chapter_id, scenes}。所有生成在无 Key 服务器上走确定性回退。
    """
    work = api.get(f"/api/v1/works/{sid}").json()
    api.put(f"/api/v1/stories/{sid}/idea", json={"idea_text": "一只流浪猫和一只流浪狗在暴雨中相遇并结伴求生。", "expected_version": work["version"]})
    concept = api.post(f"/api/v1/stories/{sid}/generations", json={"action": "generate_concept"}).json()["artifact"]
    api.post(f"/api/v1/stories/{sid}/concept/confirm", json={"expected_version": concept["version"]})
    blueprints = api.post(f"/api/v1/stories/{sid}/blueprint/generations", json={"action": "generate_blueprint"}).json()["artifacts"]
    api.post(f"/api/v1/stories/{sid}/blueprint/confirm", json={"expected_versions": {a["kind"]: a["version"] for a in blueprints}})
    chapters = api.post(f"/api/v1/stories/{sid}/chapter-plan", json={"action": "generate_chapter_plan"}).json()["chapters"]
    chapter = next(c for c in chapters if c["access_status"] == "active")
    scenes = api.post(f"/api/v1/stories/{sid}/chapters/{chapter['id']}/generations", json={"action": "generate_scene_plan"}).json()["scenes"]
    for scene in scenes:
        api.post(f"/api/v1/stories/{sid}/chapters/{chapter['id']}/scenes/{scene['id']}/generations", json={"action": "generate_beat_plan"})
    # 场景 1 生成正文（触发 Scene Summary），供 UI 验证摘要与正文编辑。
    api.post(f"/api/v1/stories/{sid}/chapters/{chapter['id']}/scenes/{scenes[0]['id']}/generations", json={"action": "generate_scene"})
    return {"chapter_id": chapter["id"], "scenes": scenes}


@pytest.fixture(scope="session")
def story(api):
    """会话级：创建一个并推进到工作台就绪的故事，测试结束后软删除。"""
    resp = api.post("/api/v1/works", json={"title": "E2E 测试作品"})
    assert resp.status_code == 201, f"创建作品失败: {resp.text}"
    sid = resp.json()["id"]
    state = advance_story(api, sid)
    yield {"id": sid, **state}
    api.delete(f"/api/v1/works/{sid}")


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def open_story(page, sid: str):
    """从作品库打开指定作品（进入创意页）。"""
    page.goto(f"{SERVER_URL}/")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#book-grid")).to_be_visible(timeout=15000)
    page.evaluate(
        "(sel) => document.querySelector(sel).dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true}))",
        f'.book-cover[data-open="{sid}"]',
    )
    expect(page.locator("#idea")).to_be_visible(timeout=15000)


def js_click(page, selector: str):
    page.evaluate(
        "(sel) => document.querySelector(sel).dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true}))",
        selector,
    )


def goto_screen(page, sid: str, screen: str):
    """打开故事并导航到指定步骤（步骤条）。"""
    open_story(page, sid)
    js_click(page, f'[data-nav="{screen}"]')
    page.wait_for_load_state("networkidle")


# ---------------------------------------------------------------------------
# 作品库 / 创意
# ---------------------------------------------------------------------------

def test_library_shows_created_work(page, story):
    """作品库显示预置的测试作品卡片。"""
    page.goto(f"{SERVER_URL}/")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#book-grid")).to_be_visible(timeout=15000)
    expect(page.locator(f'.book-card[data-id="{story["id"]}"]')).to_contain_text("E2E 测试作品")


def test_open_story_shows_idea(page, story):
    """点击作品进入创意页，原始创意只读展示。"""
    open_story(page, story["id"])
    expect(page.locator("#idea-input")).to_have_value("一只流浪猫和一只流浪狗在暴雨中相遇并结伴求生。")


# ---------------------------------------------------------------------------
# 概念 / 蓝图 / 章节（由 API 预置，UI 渲染校验）
# ---------------------------------------------------------------------------

def test_concept_screen_renders(page, story):
    """概念页展示已确认的候选内容。"""
    goto_screen(page, story["id"], "concept")
    expect(page.locator("#concept-genre")).to_be_visible(timeout=15000)
    genre = page.locator("#concept-genre").input_value()
    assert genre, "concept-genre 应为空后已有生成内容"


def test_blueprint_screen_renders(page, story):
    """蓝图页展示已生成的分类设定。"""
    goto_screen(page, story["id"], "blueprint")
    expect(page.locator("#blueprint-content")).to_be_visible(timeout=15000)
    expect(page.locator("#blueprint-content")).to_contain_text("人物", timeout=15000)


def test_chapters_screen_renders(page, story):
    """章节页展示章节卡片。"""
    goto_screen(page, story["id"], "chapters")
    expect(page.locator("#chapter-grid")).to_contain_text("CHAPTER 01", timeout=15000)


# ---------------------------------------------------------------------------
# 工作台正文流程（核心新覆盖）
# ---------------------------------------------------------------------------

def test_workspace_shows_scene_with_summary(page, story):
    """工作台展示场景列表；场景1 已完成并带有 Scene Summary。"""
    goto_screen(page, story["id"], "workspace")
    expect(page.locator("#scene-content")).to_be_visible(timeout=20000)
    expect(page.locator("#scene-content")).to_contain_text("Scene 1", timeout=20000)
    # 场景1 已由 API 生成正文并触发摘要，UI 应展示「场景摘要」。
    expect(page.locator("#scene-content")).to_contain_text("场景摘要", timeout=15000)


def test_workspace_author_edit_prose(page, story):
    """作者在工作台直接编辑正文并应用：创建新版本，原文保留。"""
    goto_screen(page, story["id"], "workspace")
    expect(page.locator("#scene-content")).to_be_visible(timeout=20000)
    # 场景1 第一个已应用 Beat 的卡片上有「编辑正文」按钮。
    edit_btn = page.locator(".beat-card .edit-beat").first
    expect(edit_btn).to_be_visible(timeout=20000)
    edit_btn.click()
    textarea = page.locator(".beat-card textarea.prose-editor").first
    expect(textarea).to_be_visible(timeout=10000)
    # 读取当前正文并追加作者修订标记。
    current = textarea.input_value()
    marker = "\n\n（作者修订：E2E 验证作者直接修改正文。）"
    textarea.fill(current + marker)
    page.locator(".beat-card .save-beat-prose").first.click()
    # 保存后重新渲染：正文包含作者修订文本。
    expect(page.locator("#scene-content")).to_contain_text("作者修订", timeout=30000)
    # 版本徽章应已递增（原 v1 保留，新 v2 应用）。
    expect(page.locator("#scene-content")).to_contain_text("v2", timeout=30000)


def test_workspace_generate_scene_prose(page, story):
    """工作台为未写作的场景一键生成正文：Beat 全部应用并生成摘要。"""
    goto_screen(page, story["id"], "workspace")
    expect(page.locator("#scene-content")).to_be_visible(timeout=20000)
    # 场景 2（未写作）在左侧栏；点击后生成整个 Scene 正文。
    scene2 = page.locator(f'.scene-item[data-scene="{story["scenes"][1]["id"]}"]')
    expect(scene2).to_be_visible(timeout=20000)
    scene2.click()
    expect(page.locator("#scene-content")).to_contain_text("Scene 2", timeout=15000)
    page.locator(".scene-generate").first.click()
    # 生成完成后：该场景出现摘要。
    expect(page.locator("#scene-content")).to_contain_text("场景摘要", timeout=60000)
    applied = page.locator("#scene-content .beat-card .tag.green")
    expect(applied.first).to_be_visible(timeout=60000)


# ---------------------------------------------------------------------------
# 阅读模式
# ---------------------------------------------------------------------------

def test_reader_shows_continuous_prose(page, story):
    """阅读模式展示已写章节的连续正文与场景摘要。"""
    goto_screen(page, story["id"], "read")
    expect(page.locator("#reader-content")).to_be_visible(timeout=20000)
    expect(page.locator("#reader-toc-list")).to_contain_text("第 1 章", timeout=15000)
    # 已写作场景正文可见（场景摘要或正文至少其一）。
    expect(page.locator("#reader-content")).to_contain_text("场景摘要", timeout=15000)
