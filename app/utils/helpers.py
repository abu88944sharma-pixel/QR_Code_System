from math import ceil
from typing import Any, Iterable, Mapping

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success_response(message: str, data: Any = None, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            {
                "status": True,
                "message": message,
                "data": data if data is not None else {},
            }
        ),
    )


def error_response(message: str, status_code: int = 400, data: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            {
                "status": False,
                "message": message,
                "data": data if data is not None else {},
            }
        ),
    )


def paginate_items(items: Iterable[Any], page: int = 1, limit: int = 10) -> dict:
    normalized_page = max(page or 1, 1)
    normalized_limit = max(limit or 10, 1)
    items_list = list(items)
    total_items = len(items_list)
    start_index = (normalized_page - 1) * normalized_limit
    end_index = start_index + normalized_limit

    return {
        "items": items_list[start_index:end_index],
        "pagination": {
            "page": normalized_page,
            "limit": normalized_limit,
            "total": total_items,
            "pages": ceil(total_items / normalized_limit) if total_items else 0,
        },
    }


def search_items(items: Iterable[Any], search_term: str | None, fields: list[str]) -> list[Any]:
    items_list = list(items)
    if not search_term:
        return items_list

    normalized_search = search_term.strip().lower()
    if not normalized_search:
        return items_list

    return [
        item
        for item in items_list
        if any(
            normalized_search in str(_get_item_value(item, field) or "").lower()
            for field in fields
        )
    ]


def filter_items(items: Iterable[Any], filters: dict[str, Any] | None) -> list[Any]:
    items_list = list(items)
    if not filters:
        return items_list

    active_filters = {
        key: value
        for key, value in filters.items()
        if value not in (None, "")
    }

    if not active_filters:
        return items_list

    return [
        item
        for item in items_list
        if all(_get_item_value(item, key) == value for key, value in active_filters.items())
    ]


def _get_item_value(item: Any, field: str) -> Any:
    if isinstance(item, Mapping):
        return item.get(field)

    return getattr(item, field, None)
