import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx

from src.config import get_settings
from src.logging_config import log_info

logger = logging.getLogger("veritix.etl.extract")

REQUEST_TIMEOUT_SECONDS = 30.0
MAX_RETRIES = 3


@dataclass(frozen=True)
class EventRecord:
    event_id: str
    event_name: str
    raw: Dict[str, Any]


@dataclass(frozen=True)
class TicketSaleRecord:
    event_id: str
    quantity: int
    price: float
    total_amount: float
    sale_date: Optional[str]
    raw: Dict[str, Any]


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _auth_headers() -> Dict[str, str]:
    token = get_settings().NEST_API_TOKEN
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _normalize_items(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    for key in ("data", "results", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _next_page(payload: Any, current_page: int) -> Optional[int]:
    if not isinstance(payload, dict):
        return None

    pagination = payload.get("pagination")
    if isinstance(pagination, dict):
        if pagination.get("next_page") is not None:
            return _to_int(pagination.get("next_page"), current_page + 1)
        if pagination.get("nextPage") is not None:
            return _to_int(pagination.get("nextPage"), current_page + 1)
        page = _to_int(pagination.get("page"), current_page)
        total_pages = _to_int(pagination.get("total_pages") or pagination.get("totalPages"), 0)
        if total_pages and page < total_pages:
            return page + 1
        if pagination.get("has_more") is True or pagination.get("hasMore") is True:
            return current_page + 1

    if payload.get("next_page") is not None:
        return _to_int(payload.get("next_page"), current_page + 1)
    if payload.get("nextPage") is not None:
        return _to_int(payload.get("nextPage"), current_page + 1)
    if payload.get("has_more") is True or payload.get("hasMore") is True:
        return current_page + 1

    return None


def _request_with_retry(
    client: httpx.Client,
    url: str,
    headers: Dict[str, str],
    dataset: str,
    params: Optional[Dict[str, Any]] = None,
) -> httpx.Response:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.get(url, headers=headers, params=params)
            try:
                payload = response.json() if response.content else []
            except ValueError:
                payload = []
            record_count = len(_normalize_items(payload))
            log_info(
                "ETL extract attempt",
                {
                    "dataset": dataset,
                    "attempt": attempt,
                    "status_code": response.status_code,
                    "record_count": record_count,
                },
            )

            if 500 <= response.status_code < 600 and attempt < MAX_RETRIES:
                time.sleep(2 ** (attempt - 1))
                continue

            response.raise_for_status()
            return response
        except httpx.RequestError as exc:
            log_info(
                "ETL extract attempt",
                {
                    "dataset": dataset,
                    "attempt": attempt,
                    "status_code": None,
                    "record_count": 0,
                    "error": str(exc),
                },
            )
            if attempt >= MAX_RETRIES:
                raise
            time.sleep(2 ** (attempt - 1))

    raise RuntimeError("unreachable")


def _to_event_record(item: Dict[str, Any]) -> EventRecord:
    event_id = str(item.get("id") or item.get("event_id") or "")
    event_name = str(item.get("name") or item.get("title") or "")
    return EventRecord(event_id=event_id, event_name=event_name, raw=item)


def _to_ticket_sale_record(item: Dict[str, Any]) -> TicketSaleRecord:
    quantity = _to_int(item.get("quantity") or item.get("qty") or 1, 1)
    price = _to_float(item.get("price") or item.get("unit_price") or item.get("amount") or 0)
    total_amount = _to_float(item.get("total_amount"), quantity * price)
    sale_date = item.get("sale_date") or item.get("created_at") or item.get("timestamp")
    event_id = str(item.get("event_id") or item.get("eventId") or item.get("event") or "")
    return TicketSaleRecord(
        event_id=event_id,
        quantity=quantity,
        price=price,
        total_amount=total_amount,
        sale_date=(str(sale_date) if sale_date is not None else None),
        raw=item,
    )


def extract_events_and_sales() -> Tuple[List[EventRecord], List[TicketSaleRecord]]:
    settings = get_settings()
    base_url = settings.NEST_API_BASE_URL.rstrip("/")
    headers = _auth_headers()
    events: List[EventRecord] = []

    with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        page = 1
        while True:
            response = _request_with_retry(
                client=client,
                url=f"{base_url}/events",
                headers=headers,
                dataset="events",
                params={"page": page},
            )
            payload = response.json()
            items = _normalize_items(payload)
            events.extend(_to_event_record(item) for item in items)
            next_page = _next_page(payload, page)
            if not next_page:
                break
            page = next_page

        sales_response = _request_with_retry(
            client=client,
            url=f"{base_url}/ticket-sales",
            headers=headers,
            dataset="ticket-sales",
        )
        sales_payload = sales_response.json()
        sales_items = _normalize_items(sales_payload)
        sales = [_to_ticket_sale_record(item) for item in sales_items]

    log_info(
        "ETL extract completed",
        {
            "events_count": len(events),
            "sales_count": len(sales),
        },
    )
    return events, sales
