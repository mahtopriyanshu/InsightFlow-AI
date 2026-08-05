# Beginner Interview Handbook

## Git

### What is Git?

Git is a distributed version-control system. It records file changes, supports branching, and allows developers to restore or compare versions.

### What is the difference between `git add` and `git commit`?

`git add` puts selected changes into the staging area. `git commit` saves the staged snapshot in the repository's history.

### Why should you run `git status`?

It shows the current branch and which files are modified, staged, or untracked. It helps prevent accidental commits.

### What is a branch?

A branch is an independent line of development. It allows work on a feature or fix without immediately changing the main branch.

## GitHub

### What is GitHub?

GitHub is a hosted platform for Git repositories. It adds collaboration features such as pull requests, issues, code review, and automated workflows.

### How are Git and GitHub different?

Git is the version-control tool that can run locally. GitHub is an online service that stores Git repositories and supports collaboration.

### What is a pull request?

A pull request proposes merging changes from one branch into another. It provides a place to review code, discuss changes, and run checks before merging.

### What is a remote repository?

A remote repository is a repository stored elsewhere, commonly on GitHub. Local commits can be pushed to it, and remote changes can be fetched or pulled.

## Primary Key

### What is a primary key?

A primary key uniquely identifies each row in a table. It must be unique and should not contain null values.

### Give an Olist primary-key example.

`order_id` is the verified primary key of the orders table because all 99,441 values are nonblank and unique.

### Can a table have more than one primary key?

A table has one primary-key constraint, but that key may contain multiple columns. A table may also have other unique candidate keys.

## Foreign Key

### What is a foreign key?

A foreign key is a column or group of columns that refers to a key in another table. It represents a relationship between the tables.

### Give an Olist foreign-key example.

`order_items.order_id` refers to `orders.order_id`, connecting each item to its order.

### What is an orphan record?

An orphan is a child record whose foreign-key value has no matching parent record. For example, an order item with an unknown `order_id` would be an orphan.

## Composite Key

### What is a composite key?

A composite key uses multiple columns together to identify a row uniquely.

### Why does the order-items table need a composite key?

One order may contain many items. `order_id` repeats, and `order_item_id` can repeat across different orders. Together, (`order_id`, `order_item_id`) uniquely identifies an item row.

### What is another Olist composite-key example?

(`order_id`, `payment_sequential`) uniquely identifies a payment record because one order can have multiple sequential payments.

## Olist Dataset

### What is the Olist dataset?

It is an anonymized public dataset containing roughly 100,000 Brazilian e-commerce orders from 2016 to 2018. It covers customers, orders, items, products, sellers, payments, reviews, categories, and geography.

### Why is Olist useful for a portfolio project?

It combines realistic marketplace operations with a manageable relational model. It supports SQL, dashboards, business analysis, and predictive use cases such as delivery risk or low review scores.

### What is the central table in the planned model?

The orders table is central. It connects to customers, items, payments, and reviews. Items then connect orders to products and sellers.

### Why is `customer_unique_id` different from `customer_id`?

`customer_id` identifies the order-level customer record and is unique per order in this source. `customer_unique_id` can repeat and is used to recognize the same buyer across orders.

### What raw relationship issues were found?

The core transaction foreign keys have complete parent coverage. Some product categories lack translations, some customer and seller ZIP prefixes lack geolocation matches, and geolocation contains multiple rows per ZIP prefix.

## EDA

### What is EDA?

Exploratory Data Analysis is the process of inspecting data to understand its structure, completeness, distributions, relationships, and potential quality issues before formal modeling.

### Is EDA the same as data cleaning?

No. EDA discovers and describes issues. Cleaning changes data to address approved issues, for example by correcting types or handling missing values.

### What did the first Olist EDA examine?

It examined only the orders CSV: shape, first rows, columns, types, missing values, order-status counts, and a basic `describe()` summary.

### What did the first EDA find?

The table has 99,441 rows and 8 columns. Most orders are delivered. Some approval, carrier-handoff, and customer-delivery timestamps are missing, while identifiers, status, purchase time, and estimated delivery are complete.

## Pandas

### What is pandas?

pandas is a Python library for loading, inspecting, transforming, joining, and analyzing structured data.

### How do you load a CSV with pandas?

```python
import pandas as pd
df = pd.read_csv("file.csv")
```

### How do you count missing values?

```python
df.isna().sum()
```

### How do you count category values?

```python
df["category_column"].value_counts(dropna=False)
```

## DataFrame

### What is a DataFrame?

A DataFrame is pandas' labeled, two-dimensional tabular structure containing rows and columns.

### How is a DataFrame different from a Series?

A DataFrame contains multiple columns. A Series is one labeled one-dimensional sequence and commonly represents a single DataFrame column.

### What does `df.shape` return?

It returns a tuple containing the number of rows and columns: `(row_count, column_count)`.

### What does `df.describe()` do?

It returns a basic summary. For numeric data it includes statistics such as mean and quartiles; for text data with `include="all"`, it includes count, unique values, most common value, and frequency.
