"""Global filter state and safe SQL predicate construction."""
from dataclasses import dataclass
from datetime import date
from datetime import timedelta


@dataclass(frozen=True)
class FilterState:
    """Hashable global analytics filters."""

    start_date: date
    end_date: date
    states: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()


def order_filter_sql(
    filters: FilterState,
    order_alias: str = "o",
    customer_alias: str = "c",
    *,
    sargable_dates: bool = True,
) -> tuple[str, tuple[object, ...]]:
    """Build parameterized predicates without multiplying order rows."""
    if sargable_dates:
        clauses = [
            f"{order_alias}.order_purchase_timestamp >= %s AND "
            f"{order_alias}.order_purchase_timestamp < %s"
        ]
        params: list[object] = [
            filters.start_date, filters.end_date + timedelta(days=1)
        ]
    else:
        clauses = [
            f"{order_alias}.order_purchase_timestamp::date BETWEEN %s AND %s"
        ]
        params = [filters.start_date, filters.end_date]
    if filters.states:
        placeholders = ", ".join(["%s"] * len(filters.states))
        clauses.append(f"{customer_alias}.customer_state IN ({placeholders})")
        params.extend(filters.states)
    if filters.categories:
        placeholders = ", ".join(["%s"] * len(filters.categories))
        clauses.append(
            "EXISTS (SELECT 1 FROM olist_analytics.order_items AS fi "
            "JOIN olist_analytics.products AS fp ON fp.product_id = fi.product_id "
            "LEFT JOIN olist_analytics.product_category_translation AS fc "
            "ON fc.product_category_name = fp.product_category_name "
            f"WHERE fi.order_id = {order_alias}.order_id "
            "AND COALESCE(fc.product_category_name_english, "
            f"fp.product_category_name) IN ({placeholders}))"
        )
        params.extend(filters.categories)
    return " AND ".join(clauses), tuple(params)
