"""Idle shutdown: Chromium must close after BROWSER_IDLE_TIMEOUT_S and relaunch on demand."""

from __future__ import annotations

import asyncio

import pytest

from sigaa_mcp.config import settings
from sigaa_mcp.session import SigaaSessionManager


@pytest.fixture
def short_idle(monkeypatch):
    monkeypatch.setattr(settings, "browser_idle_timeout_s", 0.5)


async def test_browser_closes_when_idle_and_reopens(short_idle):
    mgr = SigaaSessionManager()
    try:
        async with mgr.lock:
            page = await mgr.ensure_browser_page()
            await page.context.add_cookies(
                [{"name": "JSESSIONID", "value": "abc", "url": "https://sigaa.ufpa.br"}]
            )
        assert mgr.browser_running

        await asyncio.sleep(1.2)
        assert not mgr.browser_running
        assert mgr._ram_storage_state is not None

        async with mgr.lock:
            page = await mgr.ensure_browser_page()
            cookies = await page.context.cookies("https://sigaa.ufpa.br")
        assert any(c["name"] == "JSESSIONID" and c["value"] == "abc" for c in cookies)
        assert mgr._ram_storage_state is None
    finally:
        await mgr.close()


async def test_activity_postpones_shutdown(short_idle):
    mgr = SigaaSessionManager()
    try:
        async with mgr.lock:
            await mgr.ensure_browser_page()
        for _ in range(4):
            await asyncio.sleep(0.3)
            async with mgr.lock:
                pass
        assert mgr.browser_running
    finally:
        await mgr.close()


async def test_idle_disabled(monkeypatch):
    monkeypatch.setattr(settings, "browser_idle_timeout_s", 0)
    mgr = SigaaSessionManager()
    try:
        async with mgr.lock:
            await mgr.ensure_browser_page()
        await asyncio.sleep(0.5)
        assert mgr.browser_running
        assert mgr._idle_task is None
    finally:
        await mgr.close()
