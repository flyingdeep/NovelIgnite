# E2E 端到端测试

## 运行方式

```bash
# 安装依赖
pip install -e ".[e2e]"
playwright install chromium

# 启动后端（另一终端）
py -m uvicorn app.main:app --reload

# 运行完整测试
pytest tests/e2e -v

# 调试模式（显示浏览器）
pytest tests/e2e -v --headed --slowmo 300

# 只跑冒烟测试
pytest tests/e2e/test_smoke.py -v
```

## 测试套件

| 文件 | 内容 |
|------|------|
| `test_smoke.py` | CI 快速冒烟：后端健康、页面可访问 |
| `test_full_flow.py` | 完整流程：创意→概念→蓝图→章节→工作台 |

## 前置条件

- 后端运行在 `http://127.0.0.1:8000`
- 使用 fake adapter（无需真实 API key）
