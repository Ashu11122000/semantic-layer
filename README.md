# Semantic Layer Project — E-Commerce Analytics

## 1. Project Overview

This project implements a SQL-based semantic layer for an e-commerce analytics system using PostgreSQL, Python, and Power BI.

The objective is to transform raw business data into consistent, reusable, governed business metrics that can be consumed by analysts and business users through interactive dashboards.

The project covers the complete analytics workflow: raw data ingestion, data-quality validation, semantic view creation, metric governance, reconciliation testing, database security, and business intelligence visualization.

### Key Objectives

- Organize raw e-commerce data in PostgreSQL.
- Define business-friendly metrics and terminology.
- Build reusable SQL semantic views.
- Establish consistent metric definitions and calculation rules.
- Validate data quality and reconcile results across semantic views.
- Implement database roles, row-level security, and column-level permissions.
- Build an interactive Power BI dashboard.
- Document the architecture, business rules, validation results, and security model.

## 2. Technology Stack

| Component                                 | Technology                              |
| ----------------------------------------- | --------------------------------------- |
| Database                                  | PostgreSQL 18.1                         |
| Query language                            | SQL                                     |
| Programming language                      | Python                                  |
| Python environment and package management | uv                                      |
| Database connectivity                     | SQLAlchemy and psycopg                  |
| Automated testing                         | pytest                                  |
| Business intelligence                     | Microsoft Power BI Desktop              |
| Data visualization                        | Power BI charts, KPI cards, and slicers |
| Configuration                             | Environment variables using `.env`      |

**Architecture:** PostgreSQL stores the data and defines the semantic layer through SQL views. Python scripts and pytest validate data quality and metric consistency. Power BI connects to the semantic views to provide business-facing analytics.

## 3. Project Architecture

The project follows a layered architecture:

```text
Raw E-Commerce Data
        |
        v
PostgreSQL Raw Schema
        |
        v
Data Quality Validation
        |
        v
SQL Semantic Views
        |
        v
Governed Business Metrics
        |
        +--------------------+
        |                    |
        v                    v
Security and Access      Python Validation
        |                    |
        +---------+----------+
                  |
                  v
          Power BI Dashboard
                  |
                  v
        Business Insights
```

The semantic layer separates business definitions and calculations from individual dashboard visuals. This helps maintain consistent metric definitions across reports and analytical queries.

## 4. Data Sources

The PostgreSQL database is named `semantic_layer_db`.

The raw schema contains seven e-commerce datasets.

| Raw table         | Description                             | Expected rows |
| ----------------- | --------------------------------------- | ------------: |
| `raw.customers`   | Customer information and segmentation   |           350 |
| `raw.products`    | Product catalog and categories          |            26 |
| `raw.orders`      | Order details, status, and dates        |         1,200 |
| `raw.order_items` | Individual products purchased in orders |         2,908 |
| `raw.payments`    | Payment methods and payment statuses    |         1,200 |
| `raw.returns`     | Recorded returns and their reasons      |            42 |
| `raw.reviews`     | Customer review scores and dates        |           650 |
| **Total**         | **Seven raw tables**                    |     **6,376** |

The source datasets support analysis of revenue, product performance, customer activity, orders, payments, returns, and reviews.

## 5. Semantic Layer Implementation

The semantic views are stored in the PostgreSQL `semantic` schema.

| Semantic view                     | Purpose                                                                     | Expected rows |
| --------------------------------- | --------------------------------------------------------------------------- | ------------: |
| `semantic.vw_order_line_metrics`  | Order-line-level sales, discounts, estimated costs, profit, and eligibility |         2,908 |
| `semantic.vw_sales_metrics`       | Daily sales metrics grouped by date and order status                        |           749 |
| `semantic.vw_customer_summary`    | Customer-level metrics and customer attributes                              |           350 |
| `semantic.vw_product_performance` | Product-level sales, costs, profit, and units sold                          |            26 |
| `semantic.vw_return_analysis`     | Return records enriched with order and customer information                 |            42 |

These views provide business-friendly analytical structures without requiring dashboard users to repeatedly join raw tables or independently implement core calculations.

### Semantic Layer Benefits

- Reusable business calculations.
- Consistent metric definitions.
- Easier Power BI integration.
- Separation of data preparation and visualization.
- Improved transparency and traceability of analytical results.
- Centralized implementation of important business rules.

## 6. Business Metrics and Governance

The project documents business terminology, source-field mappings, metric definitions, and calculation restrictions.

### 6.1 Core Metrics

**Gross Sales**

Total sales value before discounts.

`Gross Sales = Quantity × Unit Price at Sale`

**Total Discounts**

Sum of the recorded discount amounts.

**Net Item Revenue**

Revenue after deducting discounts.

`Net Item Revenue = Gross Sales − Total Discounts`

**Estimated Product Cost**

Estimated cost of the products sold, using the historical unit cost recorded at the time of sale.

`Estimated Product Cost = Quantity × Unit Cost at Sale`

**Estimated Gross Profit**

Estimated profit after product costs and discounts.

`Estimated Gross Profit = Net Item Revenue − Estimated Product Cost`

**Gross Margin Percentage**

Gross profit as a percentage of net item revenue.

`Gross Margin % = Estimated Gross Profit / Net Item Revenue × 100`

**Average Order Value**

Average net item revenue per eligible order.

**Order Return Rate**

Percentage of eligible distinct orders with a recorded return.

`Order Return Rate = Distinct Returned Eligible Orders / Eligible Distinct Orders × 100`

### 6.2 Metric Governance Rules

- Cancelled orders are excluded from eligible sales metrics.
- Returned orders remain eligible for sales calculations.
- Shipping fees are kept separate from net item revenue.
- Historical transaction prices and costs are used for sales and profit calculations.
- Return records are not treated as proof of a refund or returned quantity.
- Refund amounts are not calculated because the source data does not provide verified refund amounts.
- Metric definitions and restrictions are documented to prevent inconsistent interpretations.

### 6.3 Baseline Validation Results

The following baseline values were obtained from PostgreSQL validation queries over eligible sales data.

| Metric                         | Validated baseline |
| ------------------------------ | -----------------: |
| Gross Sales                    |      48,236,547.60 |
| Total Discounts                |       3,863,139.42 |
| Net Item Revenue               |      44,373,408.18 |
| Estimated Product Cost         |      30,185,799.68 |
| Estimated Gross Profit         |      14,187,608.50 |
| Gross Margin                   |             31.97% |
| Average Order Value            |          39,338.13 |
| Eligible orders                |              1,128 |
| Customers with eligible orders |                338 |
| Distinct returned orders       |                 42 |
| Order Return Rate              |              3.72% |

The currency unit is not specified because it has not been confirmed from the source data.

These figures represent the unfiltered PostgreSQL baseline under the documented business rules. Power BI totals should be compared against the same metric definition and filter context.

## 7. Data Quality and Validation

The project includes SQL validation scripts, Python validation utilities, exported reports, and automated tests.

### 7.1 SQL Validation

Validation covers:

- Expected raw table row counts.
- Duplicate identifiers.
- Missing identifiers.
- Invalid business values.
- Referential integrity between related datasets.
- Date validity.
- Revenue and discount reconciliation.
- Product cost and gross profit reconciliation.
- Consistency across semantic views.
- Exclusion of cancelled order lines from eligible sales.

### 7.2 Python Validation Scripts

The `scripts` directory includes:

- `load_csv_data.py` — loads CSV datasets into PostgreSQL.
- `profile_dataset.py` — profiles tables, columns, numeric statistics, categorical distributions, and null values.
- `export_validation_results.py` — exports validation checks and discrepancy results.
- `validate_metrics.py` — validates governed business metrics.

The scripts were executed successfully during project validation.

### 7.3 Automated Testing

The test suite uses pytest and a shared database fixture.

| Test file                       | Coverage                                                        |
| ------------------------------- | --------------------------------------------------------------- |
| `tests/test_data_quality.py`    | Data quality and integrity                                      |
| `tests/test_revenue_metrics.py` | Revenue and discount calculations                               |
| `tests/test_profit_metrics.py`  | Cost, profit, and margin calculations                           |
| `tests/test_semantic_views.py`  | View row counts, uniqueness, reconciliation, and business rules |
| `tests/conftest.py`             | Shared database connection fixture                              |

**Recorded test result: 77 passed in 1.44 seconds.**

The 77 passing test cases include overlapping checks across the test files; they should not be interpreted as 77 entirely distinct business rules.

### 7.4 Generated Validation Reports

The `reports` directory contains:

- `validation_results.csv`
- `validation_discrepancies.csv`
- `dataset_profile.csv`
- `numeric_statistics.csv`
- `categorical_distributions.csv`

The recorded validation export reported 52 checks passed, zero failed, and zero errors. The discrepancy CSV contained its header but no discrepancy records.

## 8. Database Security

Database security is implemented through the PostgreSQL `security` schema, database roles, row-level security, and column-level permissions.

### 8.1 Defined Roles

| Role                        | Intended access                                                          |
| --------------------------- | ------------------------------------------------------------------------ |
| `semantic_admin`            | Administrative access to approved semantic objects and security mappings |
| `semantic_analyst`          | Analytical access to approved semantic views and customer metric fields  |
| `semantic_regional_manager` | Restricted customer metrics for authorized regions                       |

These are PostgreSQL database roles, not a complete application login or identity-management system.

### 8.2 Security Components

The security implementation includes:

- `security.user_region_access` — maps database users to authorized regions.
- `security.is_region_authorized(TEXT)` — checks region authorization.
- `semantic.secured_customer_metrics` — stores customer metrics protected by row-level security.
- `semantic.vw_customer_metrics_secure` — exposes approved customer metric fields.

Row-level security is enabled and forced on the protected customer metrics table. Column-level grants restrict the customer metric fields available to analysts and regional managers.

### 8.3 Security Validation

A regional test login mapped to the North region returned 71 customers and only one region, North, through the secured customer metrics view.

Direct denial of access to the unrestricted customer summary view was documented as pending independent verification in the recorded project notes. It should be reported as verified only after that test has been completed successfully.

## 9. Power BI Dashboard

The dashboard was built in Microsoft Power BI Desktop using the PostgreSQL semantic views.

### 9.1 KPI Cards

- Net Item Revenue
- Estimated Gross Profit
- Gross Margin %

### 9.2 Analytical Visuals

- Net Item Revenue by Order Date — revenue trend.
- Net Item Revenue by Product — product performance.
- Net Item Revenue by Region — regional comparison.
- Net Item Revenue by Customer Segment — segment comparison.
- Returns by Reason — count of recorded return records by reason.

### 9.3 Interactive Slicers

- Date range.
- Region.
- Product category.

The dashboard uses semantic views instead of building its core business logic directly from raw tables.

### 9.4 Dashboard Validation

The dashboard validation process compares unfiltered KPI values with PostgreSQL baselines, tests slicer behavior, and checks filtered results against equivalent SQL queries.

Slicer interactions must be validated for each visual because the semantic views represent different levels of detail. The existence of a slicer does not guarantee that every visual will respond to it.

The Power BI report is a separate deliverable and should be saved as a `.pbix` file in the project’s dashboard directory.

## 10. Project Documentation

The `docs` directory contains the following documentation:

| File                               | Purpose                                                |
| ---------------------------------- | ------------------------------------------------------ |
| `01_business_glossary.md`          | Business terminology and definitions                   |
| `02_source_to_business_mapping.md` | Mapping between source fields and business concepts    |
| `03_metric_definitions.md`         | Metric formulas and calculation logic                  |
| `04_metric_governance.md`          | Metric restrictions, assumptions, and governance rules |
| `05_data_quality_report.md`        | Data-quality checks and findings                       |
| `06_security_matrix.md`            | Database roles, access matrix, and security design     |
| `07_dashboard_validation.md`       | Power BI validation plan and test results              |
| `08_final_project_report.md`       | Consolidated project summary and outcomes              |

Documentation should reflect the actual test status, including any outstanding verification tasks.

## 11. Repository Structure

The main project structure is organized as follows:

```text
semantic-layer-project/
│
├── data/
│
├── sql/
│   ├── 01_raw/
│   │   ├── 01_create_tables.sql
│   │   ├── 02_import_data.md
│   │   ├── 03_validate_row_counts.sql
│   │   ├── 04_validate_relationships.sql
│   │   └── 05_validate_dates.sql
│   │
│   ├── 02_semantic/
│   │   ├── 01_vw_order_line_metrics.sql
│   │   ├── 02_vw_sales_metrics.sql
│   │   ├── 03_vw_customer_summary.sql
│   │   ├── 04_vw_product_performance.sql
│   │   └── 05_vw_return_analysis.sql
│   │
│   ├── 03_metrics/
│   │   ├── 01_revenue_metrics.sql
│   │   ├── 02_profit_metrics.sql
│   │   ├── 03_customer_metrics.sql
│   │   └── 04_return_metrics.sql
│   │
│   ├── 04_security/
│   │   ├── 01_create_roles.sql
│   │   ├── 02_row_level_security.sql
│   │   ├── 03_field_level_security.sql
│   │   └── 04_grants_and_permissions.sql
│   │
│   └── 05_validation/
│       ├── 01_data_quality.sql
│       ├── 02_revenue_validation.sql
│       ├── 03_profit_validation.sql
│       └── 04_semantic_view_validation.sql
│
├── scripts/
│   ├── load_csv_data.py
│   ├── profile_dataset.py
│   ├── export_validation_results.py
│   └── validate_metrics.py
│
├── tests/
│   ├── conftest.py
│   ├── test_data_quality.py
│   ├── test_revenue_metrics.py
│   ├── test_profit_metrics.py
│   └── test_semantic_views.py
│
├── docs/
│   ├── 01_business_glossary.md
│   ├── 02_source_to_business_mapping.md
│   ├── 03_metric_definitions.md
│   ├── 04_metric_governance.md
│   ├── 05_data_quality_report.md
│   ├── 06_security_matrix.md
│   ├── 07_dashboard_validation.md
│   └── 08_final_project_report.md
│
├── reports/
│   ├── validation_results.csv
│   ├── validation_discrepancies.csv
│   ├── dataset_profile.csv
│   ├── numeric_statistics.csv
│   └── categorical_distributions.csv
│
├── dashboard/
│   └── semantic_layer_dashboard.pbix
│
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

This is the documented target structure. Keep only files and folders that exist in the final repository, and update any names if your local structure differs.

## 12. Setup and Execution

### Prerequisites

- PostgreSQL 18.1 or a compatible PostgreSQL installation.
- Python compatible with the project dependencies.
- `uv` package manager.
- Access to the project CSV datasets.
- Microsoft Power BI Desktop for the dashboard.

### Step 1: Configure Environment Variables

Create a local `.env` file based on `.env.example`.

Example:

```dotenv
DATABASE_URL=postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@localhost:5432/semantic_layer_db
```

Replace the placeholders with your local PostgreSQL credentials. Do not commit `.env` or expose database passwords.

### Step 2: Install Python Dependencies

From the project root:

```bash
uv sync
```

### Step 3: Create the Database

Create a PostgreSQL database named:

```text
semantic_layer_db
```

Configure the connection details in `.env`.

### Step 4: Create Raw Tables and Load Data

Execute the SQL script:

```text
sql/01_raw/01_create_tables.sql
```

Follow the instructions in:

```text
sql/01_raw/02_import_data.md
```

Run the CSV-loading script if required by your existing setup:

```bash
uv run python scripts/load_csv_data.py
```

### Step 5: Validate the Raw Data

Execute the raw-data validation scripts in order:

```text
sql/01_raw/03_validate_row_counts.sql
sql/01_raw/04_validate_relationships.sql
sql/01_raw/05_validate_dates.sql
```

These scripts validate expected row counts, relationships, and date quality.

### Step 6: Create Semantic Views

Execute the five SQL files in `sql/02_semantic/` in numerical order.

Confirm that all five views are created successfully.

### Step 7: Execute Metric SQL

Execute the SQL files in `sql/03_metrics/` in numerical order.

### Step 8: Configure Security

Execute the security SQL files in `sql/04_security/` in the documented order, using a database administrator account.

Use a non-production environment for security testing. Verify the role grants and row-level security behavior using the appropriate test logins.

### Step 9: Run SQL Validation

Execute the SQL scripts in `sql/05_validation/` in numerical order.

### Step 10: Generate Validation Reports

Run the project validation utilities:

```bash
uv run python scripts/profile_dataset.py
uv run python scripts/export_validation_results.py
uv run python scripts/validate_metrics.py
```

### Step 11: Run Automated Tests

```bash
uv run pytest -v
```

The recorded full test run completed with 77 passing tests. Test results can vary if the database contents, schema, or code change.

### Step 12: Open the Power BI Dashboard

Open the saved `.pbix` file in Microsoft Power BI Desktop.

If prompted, configure the PostgreSQL connection to the correct server and database. Refresh the data and validate the dashboard against the documented SQL metric baselines.

## 13. Limitations and Assumptions

- The project uses SQL views rather than dbt-managed models.
- The dataset's currency unit has not been confirmed.
- Gross profit is an estimate based on recorded unit costs and excludes other expenses not represented in the model.
- Shipping fees are not included in net item revenue.
- Return records do not establish refund amounts or returned quantities.
- PostgreSQL database roles provide database-level access control; they do not replace application-level authentication.
- Dashboard filter behavior depends on the semantic views, relationships, and Power BI visual interactions.
- Security and dashboard validation documentation must distinguish completed tests from any tests still pending.

## 14. Key Outcomes

The project demonstrates how a SQL-based semantic layer can improve consistency, governance, and accessibility in e-commerce analytics.

The completed implementation includes:

- Seven raw PostgreSQL tables.
- Five reusable semantic views.
- Documented business metrics and calculation rules.
- SQL-based data-quality and reconciliation checks.
- Python validation scripts and exported reports.
- Automated pytest coverage with 77 recorded passing tests.
- PostgreSQL roles, row-level security, and column-level permissions.
- A Power BI dashboard with KPI cards, analytical charts, and interactive slicers.
- Technical and business documentation for the overall workflow.

## 15. Conclusion

This project demonstrates an end-to-end approach to building a governed analytics layer on top of relational data.

By defining business metrics centrally in PostgreSQL, validating them with SQL and Python, implementing database access controls, and exposing the results through Power BI, the project provides a structured foundation for consistent business reporting and analytical decision-making.
