# Learning Notes

## Day 1: Foundations

### Git

Git is a version-control system that records changes to files over time. It lets a developer see what changed, restore earlier versions, and work safely in branches.

Useful commands:

```bash
git status
git add <file>
git commit -m "Clear commit message"
git log --oneline
git branch --show-current
```

Key idea: a working file is first **modified**, then **staged**, and finally saved in repository history through a **commit**. `git status` should be checked before staging or committing.

### Project setup

A good analytics project starts with an understandable folder structure and clear documentation. InsightFlow AI separates raw data, processed data, notebooks, ETL code, SQL, dashboards, applications, reports, tests, configuration, and documentation.

Important setup practices:

- Keep raw source files separate from processed data.
- Store secrets in a local `.env` file and never commit them.
- List Python dependencies in `requirements.txt`.
- Use `.gitignore` to exclude generated files, secrets, and local environments.
- Explain the purpose and setup process in `README.md`.
- Build the project in milestones so every change has a clear purpose.

### Dataset understanding

Dataset understanding comes before cleaning or analysis. First identify:

- What business process produced the data?
- What does one row represent in each table?
- Which columns identify records?
- How are tables connected?
- Which fields may be missing?
- Is the source real, synthetic, or transformed?
- What decisions could the data support?

The Olist dataset represents a Brazilian e-commerce marketplace. Its nine raw tables describe customers, orders, order items, payments, reviews, products, sellers, geolocation, and product-category translations.

### Primary Key

A **Primary Key (PK)** is a column, or set of columns, that uniquely identifies each row in a table. A valid primary key should be unique and not null.

Example: `order_id` uniquely identifies a row in the Olist orders table.

Why it matters:

- Prevents duplicate identities.
- Makes a row easy to find.
- Provides a reliable target for relationships from other tables.

### Foreign Key

A **Foreign Key (FK)** is a column in one table that refers to a primary or candidate key in another table.

Example: `order_items.order_id` refers to `orders.order_id`.

Why it matters:

- Connects related business entities.
- Supports SQL joins.
- Helps enforce referential integrity.
- Prevents child records from pointing to nonexistent parents when constraints are enforced.

### Composite Key

A **Composite Key** uses two or more columns together to identify a row uniquely. Each individual column may repeat, but their combination must be unique.

Example: (`order_id`, `order_item_id`) identifies one item position inside an Olist order. An order can have many items, and the same item number can appear in different orders, but the pair is unique.

Other verified Olist examples include (`order_id`, `payment_sequential`) for payments and (`review_id`, `order_id`) for raw review records.

### Pandas

pandas is a Python library for working with tabular data. It can read files, inspect schemas, handle missing values, filter rows, aggregate measures, join tables, and prepare data for analysis.

Basic example:

```python
import pandas as pd

orders_df = pd.read_csv("orders.csv")
orders_df.shape
orders_df.head()
orders_df.isna().sum()
```

Inspection does not automatically change the source CSV. The file changes only if transformed data is explicitly written back.

### DataFrame

A **DataFrame** is pandas' two-dimensional table structure. It has labeled rows and columns and is similar to a spreadsheet or SQL result table.

Common DataFrame properties and methods:

- `df.shape` — returns row and column counts.
- `df.head()` — displays the first rows.
- `df.columns` — lists column names.
- `df.dtypes` — shows how pandas interpreted each column.
- `df.isna().sum()` — counts missing values by column.
- `df.describe()` — provides a basic statistical or structural summary.

### EDA basics

**Exploratory Data Analysis (EDA)** is the first structured examination of a dataset. Its purpose is to understand shape, fields, types, completeness, distributions, relationships, and possible quality issues before modeling or reporting.

A beginner EDA sequence is:

1. Confirm the correct source file.
2. Load it without modifying the raw file.
3. Check shape and preview rows.
4. Review columns and data types.
5. Count missing values.
6. Inspect important categorical values.
7. Generate a basic summary.
8. Record business interpretations and questions.

EDA is not the same as cleaning. Finding a missing value is EDA; filling or deleting it is cleaning. InsightFlow AI's first EDA notebook inspects only the orders table and intentionally performs no cleaning, visualization, or feature engineering.
