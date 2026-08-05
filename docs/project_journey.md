# Project Journey

InsightFlow AI is being developed in small, reviewable milestones. This journal records what each completed milestone aimed to achieve, what was done, the main challenges, how they were handled, and the resulting project state.

## Milestone 1: Project foundation

### Goal

Create a clean, beginner-friendly repository structure for an end-to-end analytics platform before implementing analytics features.

### Work completed

- Created folders for raw and processed data, notebooks, ETL, database, SQL, dashboards, Streamlit, chatbot, reports, tests, documentation, configuration, and GitHub workflows.
- Added `README.md`, `requirements.txt`, `.gitignore`, and `.env.example`.
- Initialized a local Git repository.
- Documented the project objective, planned stack, module responsibilities, and basic setup.

### Challenges

- The project moved from its temporary workspace to `C:\Projects\InsightFlow-AI`.
- Repository-local Git configuration could not be written because `.git/config` returned a permission-denied error.

### Solution

- Verified the permanent project path, required starter files, complete directory tree, and local Git repository before making changes.
- Preserved the exact Git error and did not force or work around repository metadata permissions unsafely.

### Outcome

The repository has an organized foundation and clear scope. The requested initial Git commit was not created because of the permission restriction.

## Milestone 2A: Dataset selection

### Goal

Choose one realistic dataset capable of supporting a fresher portfolio across data analytics, business analysis, SQL, dashboards, and data science.

### Work completed

- Compared Olist, AdventureWorks, Northwind, and Superstore.
- Evaluated realism, relational depth, SQL practice, dashboard potential, business analysis, machine learning, and fresher-portfolio suitability.
- Selected the Olist Brazilian E-commerce Public Dataset.
- Documented the business scenario, expected tables, relationships, primary and foreign keys, ER diagram, and 25 business questions.
- Updated the README with the selection and intended use case.

### Challenges

- AdventureWorks offered greater enterprise-schema breadth, while Superstore offered very easy dashboard creation. The selection needed to be evidence-based rather than assumed.
- The selected dataset needed to be complex enough to be credible without becoming unmanageable for a beginner.

### Solution

- Used a consistent comparison matrix across all four candidates.
- Chose Olist because its real, anonymized marketplace transactions balance manageable relational complexity with commercial, operational, customer-experience, and predictive use cases.

### Outcome

Olist was approved as the project dataset. The decision and planned model are recorded in `docs/02_dataset_selection.md`.

## Milestone 2B: Dataset acquisition and inventory

### Goal

Store the untouched Olist source files, understand every table, and verify the raw relational model before cleaning or analysis.

### Work completed

- Stored nine original CSV files under `data/raw/olist/`.
- Recorded file size, row count, column count, every column name, and a simple business explanation for each table.
- Tested candidate primary keys for uniqueness and blank values.
- Checked foreign-key coverage across the core transaction tables and optional lookup relationships.
- Documented a verified ER model and inspection-only data-quality observations.
- Updated the README with acquisition and inventory status.

### Challenges

- Automated download attempts were interrupted by network and sandbox errors, so the dataset was downloaded manually from the approved source.
- Raw review identifiers and geolocation did not follow simple one-column-key assumptions.
- Some optional lookup values did not have matching parent records.

### Solution

- Inspected the manually downloaded files in place without rewriting them.
- Verified that reviews require the composite (`review_id`, `order_id`) at raw-row grain.
- Documented that raw geolocation has no suitable natural primary key and should later become a controlled ZIP-prefix dimension.
- Reported missing category translations and ZIP-prefix lookup matches without correcting them.

### Outcome

The project now has a verified nine-table raw data model containing 1,583,922 rows and 126,186,995 bytes. The six core transactional foreign-key relationships have zero orphan records. Full details are in `docs/03_dataset_inventory.md`.

## Milestone 3: Orders EDA

### Goal

Perform a tightly scoped, beginner-friendly EDA of only the raw orders table without cleaning, visualization, feature engineering, or analysis of other tables.

### Work completed

- Created `notebooks/01_EDA_Orders.ipynb` using pandas only.
- Loaded only `olist_orders_dataset.csv`.
- Inspected shape, first five rows, columns, data types, missing values, order-status counts, and `describe()` output.
- Added Markdown before every code cell and business interpretation after every output.
- Recorded final business observations without changing the data.

### Challenges

- The notebook had to remain informative while obeying strict scope boundaries.
- All timestamp fields loaded as text, and missing lifecycle dates needed careful interpretation without prematurely cleaning or assuming causes.
- The available runtime lacked notebook-execution packages.

### Solution

- Restricted all notebook code to pandas and one source path.
- Treated timestamp types and missing values as observations, leaving conversion and missing-value handling for later approval.
- Created a valid standard notebook with captured pandas outputs and validated its cell order and source-file restriction.

### Outcome

The first EDA notebook provides a reproducible introduction to the 99,441-row orders table. It shows that delivered orders dominate and that some later lifecycle timestamps are missing, establishing the next question: how missing timestamps relate to `order_status`.
