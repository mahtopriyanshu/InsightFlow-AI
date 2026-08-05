# Milestone 3: Exploratory Data Analysis Report

## 1. Executive Summary

Milestone 3 inspected all nine raw Olist CSV tables without changing source data. The dataset contains 1,583,922 rows across 52 source columns. Eight documented candidate keys are valid, and six core transaction foreign keys have zero orphan rows. ETL is feasible, but geolocation duplication, optional missing values, incomplete lookup coverage, and raw type handling require explicit rules.

## 2. Table Inventory

| Table | Rows | Columns |
|---|---:|---:|
| Customers | 99,441 | 5 |
| Geolocation | 1,000,163 | 5 |
| Order items | 112,650 | 7 |
| Payments | 103,886 | 5 |
| Reviews | 99,224 | 7 |
| Orders | 99,441 | 8 |
| Products | 32,951 | 9 |
| Sellers | 3,095 | 4 |
| Category translation | 71 | 2 |

## 3. Missing Value Summary

| Table | Missing cells | Affected columns | Main finding |
|---|---:|---:|---|
| Orders | 4,908 | 3 | Approval, carrier handoff, and delivery timestamps are incomplete. |
| Products | 2,448 | 8 | 610 rows lack category/text/photo metadata; 2 rows lack physical measures. |
| Reviews | 145,903 | 2 | Titles and messages are optional and frequently absent. |
| All other tables | 0 | 0 | No missing cells detected. |

## 4. Duplicate Summary

- Geolocation contains **261,831 exact duplicate rows**.
- No exact duplicate rows were found in the other eight tables.
- No rows are removed during EDA.

## 5. Primary Key Validation

| Table | Candidate key | Result |
|---|---|---|
| Customers | `customer_id` | Valid |
| Orders | `order_id` | Valid |
| Order items | (`order_id`, `order_item_id`) | Valid |
| Payments | (`order_id`, `payment_sequential`) | Valid |
| Reviews | (`review_id`, `order_id`) | Valid |
| Products | `product_id` | Valid |
| Sellers | `seller_id` | Valid |
| Category translation | `product_category_name` | Valid |
| Geolocation | None | No natural raw key; ZIP prefix repeats heavily |

All eight candidate keys are unique and nonblank. Review modeling must preserve the composite key because neither `review_id` nor `order_id` is unique alone.

## 6. Foreign Key Validation

| Relationship | Orphan rows | Result |
|---|---:|---|
| Orders → Customers | 0 | Valid |
| Items → Orders | 0 | Valid |
| Items → Products | 0 | Valid |
| Items → Sellers | 0 | Valid |
| Payments → Orders | 0 | Valid |
| Reviews → Orders | 0 | Valid |
| Products → Category translation | 13 | Incomplete lookup |
| Customers → Geolocation ZIP prefix | 278 | Incomplete conceptual lookup |
| Sellers → Geolocation ZIP prefix | 7 | Incomplete conceptual lookup |

Geolocation ZIP prefix is not a unique parent key, so its relationship must remain conceptual until ETL creates a controlled geography dimension.

## 7. Data Quality Findings

Seventeen actionable structural observations were recorded:

1. Three order lifecycle timestamp columns contain 4,908 missing cells.
2. Review titles are missing in 87,656 rows.
3. Review messages are missing in 58,247 rows.
4. Four product metadata columns are missing together in 610 rows.
5. Four product physical-measure columns are missing in 2 rows each.
6. Geolocation contains 261,831 exact duplicate rows.
7. Geolocation has no suitable natural raw primary key.
8. ZIP prefix is non-unique and can multiply rows during joins.
9. Two nonblank categories covering 13 products lack English translations.
10. Customer ZIP prefixes lack geolocation matches in 278 rows.
11. Seller ZIP prefixes lack geolocation matches in 7 rows.
12. Reviews require the composite (`review_id`, `order_id`).
13. `customer_unique_id` repeats intentionally and is not the customer-row primary key.
14. Some orders have no item rows.
15. One order has no payment row.
16. Some orders have no review row.
17. Two product headers contain the source spelling `lenght`.

## 8. Recommended Cleaning Strategy

- Preserve all raw CSV files and hashes.
- Load source values into typed staging tables before applying business rules.
- Parse timestamps with explicit formats and log conversion failures.
- Keep lifecycle and optional-review nulls until their business meaning is classified.
- Deduplicate geolocation only after selecting a documented deterministic rule.
- Build a single-row ZIP-prefix dimension before geographic joins.
- Retain unmatched lookup records using controlled `Unknown` dimension members rather than dropping facts.
- Preserve verified composite keys and standardize misspelled headers only in processed layers.
- Reconcile row counts, key uniqueness, and FK coverage after every load.

## 9. ETL Readiness Checklist

- [x] Raw file inventory recorded
- [x] Row and column counts recorded
- [x] Missing values profiled
- [x] Exact duplicates profiled
- [x] Candidate primary keys validated
- [x] Foreign-key coverage validated
- [x] Timestamp columns identified
- [x] Data-quality risks documented
- [ ] Staging schemas approved
- [ ] Timestamp parsing rules approved
- [ ] Null-handling rules approved
- [ ] Geolocation deduplication rule approved
- [ ] Unknown category/geography handling approved
- [ ] PostgreSQL constraints and load order implemented
- [ ] Automated ETL reconciliation tests implemented
