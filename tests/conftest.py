"""Pytest session fixtures.

Redirects observability logs to a temp dir so tests never pollute logs/app.jsonl.
Must run before app modules import observability.
"""
import os
import tempfile

os.environ.setdefault("NOVEL_LOG_DIR", os.path.join(tempfile.gettempdir(), "novel_ignite_test_logs"))
