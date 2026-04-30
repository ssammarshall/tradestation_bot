from __future__ import annotations

import threading
from collections import defaultdict
from typing import Callable

from app.market_data.stream_service import StreamService
from app.schemas.bars import BarHistoryParams, StreamBarEvent

_StreamKey = tuple  # (symbol, unit, interval, session_template)


class StreamManager:
    def __init__(self, stream_service: StreamService):
        self._service = stream_service
        self._callbacks: dict[_StreamKey, list[Callable[[StreamBarEvent], None]]] = defaultdict(list)
        self._threads: dict[_StreamKey, threading.Thread] = {}
        self._stop_events: dict[_StreamKey, threading.Event] = {}
        self._params: dict[_StreamKey, BarHistoryParams] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _key(params: BarHistoryParams) -> _StreamKey:
        return (params.symbol, params.unit, params.interval, params.session_template)

    def subscribe(self, params: BarHistoryParams, callback: Callable[[StreamBarEvent], None]) -> None:
        key = self._key(params)
        with self._lock:
            self._callbacks[key].append(callback)
            if key not in self._threads:
                self._params[key] = params
                stop = threading.Event()
                self._stop_events[key] = stop
                thread = threading.Thread(target=self._run_stream, args=(key, stop), daemon=True)
                self._threads[key] = thread
                thread.start()

    def unsubscribe(self, params: BarHistoryParams, callback: Callable[[StreamBarEvent], None]) -> None:
        key = self._key(params)
        with self._lock:
            callbacks = self._callbacks.get(key, [])
            if callback in callbacks:
                callbacks.remove(callback)
            
            if not callbacks:
                if key in self._stop_events:
                    self._stop_events[key].set()

    def shutdown(self) -> None:
        with self._lock:
            keys = list(self._stop_events.keys())
        for key in keys:
            self._stop_events[key].set()

    def _run_stream(self, key: _StreamKey, stop: threading.Event) -> None:
        params = self._params[key]
        try:
            for event in self._service.stream_bars(params):
                if stop.is_set():
                    break
                with self._lock:
                    callbacks = list(self._callbacks[key])
                for cb in callbacks:
                    cb(event)
        finally:
            with self._lock:
                self._threads.pop(key, None)
                self._stop_events.pop(key, None)
