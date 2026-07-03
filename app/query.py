from fastapi import Query, Response
from sqlalchemy import or_
from sqlalchemy.orm import Query as SqlAlchemyQuery


def pagination_params(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> tuple[int, int]:
    return limit, offset


def apply_pagination(query: SqlAlchemyQuery, response: Response, limit: int, offset: int):
    total = query.count()
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Limit"] = str(limit)
    response.headers["X-Offset"] = str(offset)
    return query.offset(offset).limit(limit)


def listing_search_filter(query: SqlAlchemyQuery, model, search: str | None):
    if not search:
        return query
    term = f"%{search.strip()}%"
    return query.filter(
        or_(
            model.title.ilike(term),
            model.description.ilike(term),
            model.category.ilike(term),
            model.location.ilike(term),
        )
    )


def apply_sort(query: SqlAlchemyQuery, model, sort: str, allowed: dict[str, str]):
    descending = sort.startswith("-")
    key = sort[1:] if descending else sort
    column_name = allowed.get(key, allowed["default"])
    column = getattr(model, column_name)
    if descending:
        column = column.desc()
    return query.order_by(column)
