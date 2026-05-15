from __future__ import annotations

import threading
from collections import defaultdict
from logging import Logger, getLogger
from typing import Callable

from app.orders.order_service import OrderService
from app.schemas.orders import OrderStatusParams, StreamOrderEvent


class OrderStreamManager:
    def __init__(self, order_service: OrderService):
        self._service = order_service
        self._callbacks: dict[str, list[Callable[[StreamOrderEvent], None]]] = defaultdict(list)
        self._threads: dict[str, threading.Thread] = {}
        self._stop_events: dict[str, threading.Event] = {}
        self._lock = threading.Lock()
        self.log: Logger = getLogger(self.__class__.__name__)

    def subscribe(self, account_id: str, callback: Callable[[StreamOrderEvent], None]) -> None:
        with self._lock:
            self._callbacks[account_id].append(callback)
            if account_id not in self._threads:
                stop = threading.Event()
                self._stop_events[account_id] = stop
                thread = threading.Thread(target=self._run_stream, args=(account_id, stop), daemon=True)
                self._threads[account_id] = thread
                thread.start()
                self.log.info("subscribe %s", account_id)

    def unsubscribe(self, account_id: str, callback: Callable[[StreamOrderEvent], None]) -> None:
        with self._lock:
            callbacks = self._callbacks.get(account_id, [])
            if callback in callbacks:
                callbacks.remove(callback)

            if not callbacks and account_id in self._stop_events:
                self.log.info("unsubscribe %s (last)", account_id)
                self._stop_events[account_id].set()

    def shutdown(self) -> None:
        with self._lock:
            account_ids = list(self._stop_events.keys())
        for account_id in account_ids:
            self._stop_events[account_id].set()

    def _run_stream(self, account_id: str, stop: threading.Event) -> None:
        params = OrderStatusParams(account_id=account_id)
        log = self.log.getChild(account_id)
        log.debug("stream open")
        try:
            for event in self._service.stream_orders(params):
                if stop.is_set():
                    break
                with self._lock:
                    callbacks = list(self._callbacks[account_id])
                for cb in callbacks:
                    cb(event)
        finally:
            log.debug("stream closed")
            with self._lock:
                self._threads.pop(account_id, None)
                self._stop_events.pop(account_id, None)
                self._callbacks.pop(account_id, None)
