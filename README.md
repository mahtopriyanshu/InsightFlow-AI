# InsightFlow AI

InsightFlow AI is a beginner-friendly, end-to-end analytics project designed to show how raw data can eventually be transformed into useful insights and accessible through dashboards and an AI-assisted chat experience.

## Problem Statement

Organizations often store useful data in disconnected files and systems. Without a clear analytics workflow, it can be difficult for beginners and non-technical users to clean that data, explore it, and turn it into understandable business insights.

## Project Objective

The objective is to build a clear and approachable analytics workflow that will eventually:

- Collect and prepare raw data.
- Store clean, structured data.
- Analyze data with SQL and Python.
- Present insights in dashboards and reports.
- Allow users to explore insights through a chatbot interface.

The initial structure, dataset selection, and raw dataset inventory milestones are complete. Analytics features will be added in later stages.

## Planned Technology Stack

- Python for data processing and application logic
- pandas and NumPy for data preparation and analysis
- Jupyter Notebook for exploration and learning
- SQL and a relational database for structured data storage and querying
- Streamlit for the interactive application
- A dashboard tool for data visualization
- An AI model or API for the chatbot
- Docker and GitHub Actions for future deployment and automation

## Planned Project Modules

- **Data:** Raw input files and processed datasets
- **Notebooks:** Exploratory analysis and learning exercises
- **ETL:** Future extract, transform, and load workflows
- **Database:** Future database definitions and supporting files
- **SQL:** Queries used for analysis and reporting
- **Dashboard:** Assets and configuration for standalone business-intelligence dashboards, such as Power BI or Tableau dashboards
- **Streamlit app:** Python code for the future interactive Streamlit web application
- **Chatbot:** Future natural-language analytics assistant
- **Reports:** Generated analysis outputs
- **Tests:** Automated checks for future project code
- **Docs:** Project documentation
- **Config:** Non-secret project configuration
- **GitHub workflows:** Future automation and CI/CD definitions

## Current Project Status

**Stage: Milestone 2B complete — raw dataset acquired and inventoried**

The folder structure, starter documentation, dependency list, environment-variable template, and Git ignore rules are in place. Milestone 2 selected the **Olist Brazilian E-commerce Public Dataset** after comparison with AdventureWorks, Northwind, and Superstore. The decision and planned relational model are documented in [`docs/02_dataset_selection.md`](docs/02_dataset_selection.md).

### Selected dataset and business use case

InsightFlow AI will use Olist's anonymized Brazilian marketplace data to connect sales, customers, products, sellers, payments, deliveries, and reviews. The future platform will help marketplace stakeholders monitor performance, diagnose operational and customer-experience issues, and develop practical predictive use cases such as late-delivery and low-review risk.

The nine original Olist CSV files are stored unchanged under `data/raw/olist/`. Their schemas, row counts, candidate keys, foreign keys, relationship checks, and inspection-only quality observations are documented in [`docs/03_dataset_inventory.md`](docs/03_dataset_inventory.md). No cleaning, ETL, EDA, database, dashboard, chatbot, or predictive model has been implemented.

## Basic Setup

1. Clone or download this repository.
2. Open a terminal in the `InsightFlow-AI` folder.
3. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

4. Activate the virtual environment:

   On Windows PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   On macOS or Linux:

   ```bash
   source .venv/bin/activate
   ```

5. Install the starter dependencies when you are ready:

   ```bash
   pip install -r requirements.txt
   ```

6. Copy `.env.example` to `.env` and replace placeholders only when future modules require them. Never commit the `.env` file.

> Dependencies are not installed automatically as part of this initial setup.
