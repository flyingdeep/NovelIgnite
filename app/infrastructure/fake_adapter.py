"""Deterministic offline adapter used by tests and local development."""
from app.infrastructure.model_adapter import ModelAdapter


class FakeModelAdapter:
    def __init__(self, response: str = '{"ok": true}'):
        self.response = response
        self.calls: list[dict] = []

    def complete(self, messages, *, temperature=0.7, reasoning_strength="medium", json_mode=False, max_tokens=4096):
        self.calls.append({"messages": messages, "temperature": temperature, "reasoning_strength": reasoning_strength, "json_mode": json_mode, "max_tokens": max_tokens})
        return self.response
