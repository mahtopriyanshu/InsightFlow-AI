# Milestone 10 — Analytics Serving Layer

## Architecture

```text
Olist curated tables
  orders · customers · order_payments · order_items · products
  sellers · order_reviews · product_category_translation
                         ↓
Validated serving objects
  mv_order_revenue → vw_order_revenue
  orders           → vw_order_delivery_metrics
                         ↓
Streamlit services (view-first, CTE fallback)
                         ↓
Nine analytics pages, charts, searches, and reports
```

The application remains read-only. The schema migration is run separately
with the database credentials loaded from `.env`.

## Live inventory and discrepancy

The live `olist_analytics` schema contained all nine curated tables, primary
and foreign keys, and the expected base indexes. It contained no views or
materialized views. All five names formerly defined in
`sql/09_analytics_views.sql` were absent, including `vw_order_revenue`.

The root cause was deployment drift: the SQL file existed in the repository,
but the documented database migration sequence only covered `schema.sql`,
`constraints.sql`, and `indexes.sql`. No migration record or live object showed
that the analytics-view SQL had ever been applied.

## Serving objects

### `olist_analytics.mv_order_revenue`

- **Purpose:** avoid repeating payment and item aggregation on every dashboard
  rerun.
- **Grain:** exactly one row per order.
- **Sources:** `orders`, `order_payments`, `order_items`.
- **Metrics:** payment revenue, merchandise value, freight value, and combined
  item value.
- **Join key:** `order_id` with unique index
  `ux_mv_order_revenue_order_id`.
- **Refresh:** refresh after a successful curated ETL load. The current Olist
  dataset is static; no automatic refresh scheduler is required.

### `olist_analytics.vw_order_revenue`

- **Purpose:** stable normal-view interface for application queries.
- **Grain:** one row per order.
- **Source:** `mv_order_revenue`.
- **Filters supported:** joins to the filtered order set by `order_id`; date,
  state, and category semantics remain controlled by the service layer.

### `olist_analytics.vw_order_delivery_metrics`

- **Purpose:** centralize the validated delivery-duration calculation.
- **Grain:** one row per order.
- **Source:** `orders`.
- **Metrics:** actual delivery days, delivery delay days, and
  `on_time_or_early` / `late` / `not_delivered` classification.

Customer, seller, and category summary views were intentionally not created.
Full-history summary grains cannot correctly answer all combinations of the
application's date, state, and category filters without rejoining base facts.

## Validated business definitions

| Metric | Preserved definition |
|---|---|
| Total Revenue | Sum of per-order `order_payments.payment_value` |
| Total Orders | Count of filtered order rows |
| Unique Customers | Distinct `customer_unique_id` in filtered orders |
| Average Order Value | Average per-order payment revenue |
| Delivery Rate | Orders with status `delivered` / all filtered orders |
| Late Delivery Rate | Delivered orders after estimated date / orders with a customer delivery date |
| Average Delivery Days | Average elapsed days from purchase to customer delivery |
| Repeat Customer Rate | Customers with more than one filtered order / filtered unique customers |
| Average Review Score | Average review score joined to filtered orders |
| Negative Review Rate | Reviews scoring 1 or 2 / filtered reviews |
| Category Revenue | Sum of order-item price, not payment revenue |
| Seller Revenue | Sum of seller order-item price |

Revenue has two intentional meanings: executive revenue uses payments, while
seller/category merchandise revenue uses item price. This matches the existing
validated application and was not silently changed.

## Page and service dependencies

| Pages | Service areas | Serving object or fallback |
|---|---|---|
| Overview, Sales | `services.overview` | order revenue view; base CTE fallback |
| Customer Intelligence | `services.customers` | order revenue view; base CTE fallback |
| Product, Seller Intelligence | `services.commerce` | filtered base facts; shared order CTE |
| Delivery, Review Analytics | `services.operations` | delivery and revenue views; base CTE fallback |
| Reports | `services.reports` | view-first order report; original correlated fallback |
| AI Assistant | no analytics execution | no change |

`analytics_serving_available()` checks both serving views. If either is absent,
`filtered_orders_cte()` returns the original base-table implementation. The
fallback retains its original date predicate because it produces a safer
full-history plan under the 30-second timeout. The optimized path uses a
sargable half-open timestamp range and the existing timestamp index.

## Correctness validation

Fallback and optimized results were compared for full data, a 2018 date
range, SP, `health_beauty`, and the combined date/state/category context.
Executive KPIs, delivery metrics, and top-customer outputs passed all 15
comparisons. A deterministic customer-ID tie-breaker was added where equal
revenue previously allowed unstable ordering.

Baseline full-data values include:

- Total revenue: `16008872.12`
- Total orders: `99441`
- Unique customers: `96096`
- AOV: `160.9886477408714715`
- Delivery rate: `97.0203437214026408%`
- Late delivery rate: `8.1128985447157842%`
- Average review score: `4.0864206240425703`
- Repeat customer rate: `3.1187562437562438%`
- Top category: `health_beauty`
- Top state: `SP`
- Top seller: `4869f7a5dfa277a7dca6462dcf3b52b2`

## Controlled performance results

Measurements use `EXPLAIN (ANALYZE, BUFFERS)` and are environment-specific.

| Workload | Fallback | Optimized |
|---|---:|---:|
| Executive metrics | 1718.390 ms | 1089.710 ms |
| Delivery metrics | 1436.009 ms | 202.333 ms |
| Top customers | 2780.210 ms | 534.954 ms |
| Sales trend | 953.044 ms | 346.832 ms |
| Category ranking | 2983.299 ms | 1137.770 ms |
| Seller ranking | 1536.930 ms | 881.791 ms |
| Order drill-down (1,000) | 1491.839 ms | 28.087 ms |
| Order report (50,000) | 1856.666 ms | 243.205 ms |

## Operations

Apply the serving layer:

```powershell
py database/apply_milestone10.py
```

After a real curated-data reload, refresh the materialized fact using an
authorized migration/operations connection:

```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY olist_analytics.mv_order_revenue;
```

The Streamlit connection continues to execute
`SET default_transaction_read_only = on` and cannot refresh or modify these
objects.
