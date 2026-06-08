from __future__ import annotations

import asyncio
from typing import Any

import anyio.to_thread
import fastapi.routing
import httpx
import starlette.concurrency
from fastapi import FastAPI


class SyncAsgiClient:
    """Minimal sync wrapper around httpx.AsyncClient for ASGI app tests."""

    def __init__(self, app: FastAPI, *, base_url: str = "http://testserver") -> None:
        self._app = app
        self._base_url = base_url

    def __enter__(self) -> SyncAsgiClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        del exc_type, exc, tb

    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        async def _inline_run_in_threadpool(func, *call_args, **call_kwargs):
            return func(*call_args, **call_kwargs)

        async def _inline_run_sync(func, *call_args, **call_kwargs):
            call_kwargs.pop("abandon_on_cancel", None)
            call_kwargs.pop("cancellable", None)
            call_kwargs.pop("limiter", None)
            return func(*call_args, **call_kwargs)

        original_fastapi = fastapi.routing.run_in_threadpool
        original_starlette = starlette.concurrency.run_in_threadpool
        original_anyio = anyio.to_thread.run_sync
        fastapi.routing.run_in_threadpool = _inline_run_in_threadpool
        starlette.concurrency.run_in_threadpool = _inline_run_in_threadpool
        anyio.to_thread.run_sync = _inline_run_sync
        try:
            async with self._app.router.lifespan_context(self._app):
                transport = httpx.ASGITransport(app=self._app)
                async with httpx.AsyncClient(
                    transport=transport,
                    base_url=self._base_url,
                    follow_redirects=True,
                ) as client:
                    return await client.request(method, url, **kwargs)
        finally:
            fastapi.routing.run_in_threadpool = original_fastapi
            starlette.concurrency.run_in_threadpool = original_starlette
            anyio.to_thread.run_sync = original_anyio

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        return asyncio.run(self._request(method, url, **kwargs))

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("DELETE", url, **kwargs)
