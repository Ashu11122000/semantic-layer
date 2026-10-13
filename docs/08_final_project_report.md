# 08 — Final Project Report: E-Commerce Semantic Layer

## 1. Executive Summary

The E-Commerce Semantic Layer project establishes a consistent, governed business-metrics layer on top of raw e-commerce data stored in PostgreSQL.

The project organizes source data into a raw schema, creates reusable semantic views, defines governed business metrics, validates revenue and estimated-profit calculations, and implements database access controls.

Automated Python and pytest validation scripts support repeatable data-quality and metric checks.

The semantic layer is designed to provide consistent business definitions for downstream reporting tools such as Power BI or Tableau.

**Current status:** Core database implementation, metric reconciliation, and automated tests have been executed successfully. BI dashboard implementation and some security acceptance tests remain subject to final verification.

## 2. Project Objectives

The project aims to:

1. Document business terminology and metric definitions.
2. Map source fields to business concepts.
3. Create reusable SQL semantic views.
4. Establish consistent revenue, profitability, customer, and return metrics.
5. Define metric governance rules.
6. Validate data quality and semantic calculations.
7. Implement role-based, row-level, and field-level access restrictions.
8. Prepare the semantic layer for BI integration.
9. Record validation outcomes and known limitations.

## 3. Technology Stack

| Component                                    | Technology             |
| -------------------------------------------- | ---------------------- |
| Database                                     | PostgreSQL 18.1        |
| Query language                               | SQL                    |
| Python environment and dependency management | Python with `uv`       |
| Database access from Python                  | SQLAlchemy and psycopg |
| Environment configuration                    | `python-dotenv`        |
| Automated testing                            | pytest                 |
| Validation outputs                           | CSV reports            |
| Documentation                                | Markdown               |
| Intended BI integration                      | Power BI or Tableau    |

The implemented semantic layer uses PostgreSQL views and SQL-based metric definitions. dbt is not required for the current implementation.

## 4. Data Sources

Seven source tables were imported into the `raw` schema.

| Source table      |      Rows |
| ----------------- | --------: |
| `raw.customers`   |       350 |
| `raw.products`    |        26 |
| `raw.orders`      |     1,200 |
| `raw.order_items` |     2,908 |
| `raw.payments`    |     1,200 |
| `raw.returns`     |        42 |
| `raw.reviews`     |       650 |
| **Total**         | **6,376** |

The imported data represents customer, product, order, transaction-line, payment, return, and review information.

The raw layer preserves source data for validation and downstream semantic calculations.

## 5. Architecture

The project follows this logical architecture:

```text
E-Commerce CSV Files
        |
        v
PostgreSQL Raw Schema
        |
        v
Data Quality Validation
        |
        v
PostgreSQL Semantic Views
        |
        v
Governed Metric Definitions
        |
        +-----------------------+
        |                       |
        v                       v
Automated Testing         Access Controls
        |                       |
        +-----------+-----------+
                    |
                    v
           BI Integration Layer
                    |
                    v
        Power BI or Tableau Dashboard
```

The database and validation components have been implemented. The final dashboard and its interactive filter behavior must be validated separately.

## 6. Semantic Views

Five semantic views were created and validated.

| Semantic view                     |  Rows | Purpose                                                             |
| --------------------------------- | ----: | ------------------------------------------------------------------- |
| `semantic.vw_order_line_metrics`  | 2,908 | Order-line revenue, discounts, cost, profit, and eligibility        |
| `semantic.vw_sales_metrics`       |   749 | Aggregated sales metrics                                            |
| `semantic.vw_customer_summary`    |   350 | Customer-level metrics, including customers without eligible orders |
| `semantic.vw_product_performance` |    26 | Product-level revenue and profitability                             |
| `semantic.vw_return_analysis`     |    42 | Return records and associated analysis                              |

The views use historical transaction prices and costs rather than current product catalogue prices for transaction-level calculations.

Reconciliation checks confirmed that eligible revenue and estimated gross profit agree across the order-line, customer, and product semantic views.

## 7. Governed Business Metrics

The following metrics were validated against the current dataset.

| Metric                         | Definition                                                            | Validated value |
| ------------------------------ | --------------------------------------------------------------------- | --------------: |
| Gross sales                    | Sum of eligible quantity multiplied by historical sale price          |   48,236,547.60 |
| Total discounts                | Sum of eligible recorded discount amounts                             |    3,863,139.42 |
| Net item revenue               | Gross sales minus discounts                                           |   44,373,408.18 |
| Estimated product cost         | Eligible quantity multiplied by historical unit cost                  |   30,185,799.68 |
| Estimated gross profit         | Net item revenue minus estimated product cost                         |   14,187,608.50 |
| Estimated gross margin         | Estimated gross profit divided by net item revenue, multiplied by 100 |          31.97% |
| Average order value            | Eligible net item revenue divided by distinct eligible orders         |       39,338.13 |
| Customers with eligible orders | Customers with at least one eligible order                            |             338 |
| Total customers                | Number of source customer records                                     |             350 |
| Eligible orders                | Distinct orders eligible for sales metrics                            |           1,128 |
| Distinct returned orders       | Distinct eligible orders with a return record                         |              42 |
| Order return rate              | Distinct returned eligible orders divided by eligible distinct orders |           3.72% |

Financial values are expressed in the dataset's monetary units. A specific currency should be identified in dashboard labels only after the source currency has been confirmed.

## 8. Business Rules and Assumptions

### 8.1 Revenue

- Gross sales are calculated using historical transaction prices.
- Discounts are summed from `discount_amount` and are not multiplied by quantity again.
- Net item revenue equals gross sales minus discounts.
- Shipping fees are separate from item revenue.

### 8.2 Profitability

- Estimated product cost uses historical transaction costs multiplied by quantity.
- Estimated gross profit equals net item revenue minus estimated product cost.
- Gross margin is calculated from aggregate estimated profit divided by aggregate net item revenue.
- These figures represent estimated gross profitability, not necessarily accounting profit or cash received.

### 8.3 Order eligibility

- Cancelled orders are excluded from eligible sales metrics.
- Returned orders remain eligible unless the documented business rules change.
- Return records do not establish refund amounts or returned quantities.
- Refunds must not be inferred from return records alone.

These definitions are documented so that SQL queries, automated tests, and future dashboard calculations follow the same rules.

## 9. Data Quality and Validation

The project includes SQL validation scripts and Python automation.

### 9.1 SQL validation

The following validation areas were executed:

- Source row counts
- Duplicate and missing identifiers
- Referential integrity
- Date checks
- Invalid business values
- Revenue and discount reconciliation
- Product-cost and estimated-profit reconciliation
- Semantic view row counts and entity coverage
- Cancelled-order exclusion

The executed SQL checks reported the expected results and zero differences in the tested revenue and profit reconciliations.

### 9.2 Automated Python validation

The following scripts were executed:

| Script                                 | Result                                               |
| -------------------------------------- | ---------------------------------------------------- |
| `scripts/export_validation_results.py` | 52 validation checks passed; 0 failed; 0 errors      |
| `scripts/profile_dataset.py`           | Dataset profiling reports generated                  |
| `scripts/validate_metrics.py`          | 20 governed metric checks passed; 0 failed; 0 errors |

The validation export created:

- `reports/validation_results.csv`
- `reports/validation_discrepancies.csv`

The dataset profiling process created:

- `reports/dataset_profile.csv`
- `reports/numeric_statistics.csv`
- `reports/categorical_distributions.csv`

The discrepancy export contained only its header because no discrepancies were recorded by that validation run.

### 9.3 Automated pytest results

The complete pytest suite was executed after adding the revenue, profit, and semantic-view tests.

| Test file                       | Passed |
| ------------------------------- | -----: |
| `tests/test_data_quality.py`    |     43 |
| `tests/test_profit_metrics.py`  |      9 |
| `tests/test_revenue_metrics.py` |     11 |
| `tests/test_semantic_views.py`  |     14 |
| **Total collected tests**       | **77** |
| **Failures in the final run**   |  **0** |

The final recorded full-suite result was **77 passed in 1.44 seconds**.

The test count includes overlapping checks across test files; it represents executed test cases, not 77 unique business rules.

## 10. Security Implementation

The project defines three database roles:

- `semantic_admin`
- `semantic_analyst`
- `semantic_regional_manager`

Security implementation includes:

- Restricted database roles without superuser or RLS-bypass privileges
- Explicit schema and object grants
- A protected customer-metrics table
- Row-level security policies
- A region-access mapping table
- A helper function for region authorization
- A secure customer-metrics view
- Column-level restrictions for approved customer-metric fields

A dedicated regional test login was mapped to North. Testing confirmed that the secure customer-metrics view returned 71 customer records from the North region.

**Remaining security verification:** Direct denial of access to the unrestricted customer summary has not yet been independently confirmed under the regional test login. The complete security acceptance process must include this test and checks for alternate access paths.

See `docs/06_security_matrix.md` for the role matrix and security validation details.

## 11. BI Integration and Dashboard Validation

The semantic views are intended to provide reusable data sources for Power BI or Tableau.

The dashboard validation plan is documented in `docs/07_dashboard_validation.md`.

The planned dashboard includes:

- Revenue overview
- Profitability metrics
- Sales trends
- Product performance
- Customer performance
- Return analysis

Validation will compare dashboard values with PostgreSQL results and test date, product, customer-segment, regional, and combined filters.

**Current status:** Dashboard-specific execution results have not yet been established in the project evidence recorded here. The dashboard should not be marked complete until it is implemented and its metrics, filters, and access restrictions have been tested.

## 12. Known Limitations

1. Product cost and gross profit are estimates based on recorded transaction costs.
2. Refund amounts and returned quantities cannot be established from the available return records alone.
3. Shipping fees are tracked separately from item revenue.
4. Current expected metric values are specific to the current dataset.
5. Database metric validation does not automatically prove that dashboard filters behave correctly.
6. Regional row-level security has a successful North-region test, but direct-access denial still requires independent verification.
7. Dashboard integration and user-facing security behavior require final testing.

These limitations should remain visible in project documentation and should be considered before using the outputs for production financial reporting.

## 13. Project Deliverables

The project contains the following categories of deliverables.

| Category                | Deliverables                                                               |
| ----------------------- | -------------------------------------------------------------------------- |
| Business documentation  | Glossary, source-to-business mapping, metric definitions, governance rules |
| Data ingestion          | Raw PostgreSQL tables and CSV import process                               |
| Semantic layer          | Five reusable semantic views                                               |
| Governed metrics        | SQL metric definitions for revenue, profit, customers, and returns         |
| Data validation         | SQL validation scripts and automated Python checks                         |
| Automated tests         | pytest test files and shared fixture configuration                         |
| Profiling and reporting | CSV validation, discrepancy, and profiling outputs                         |
| Security                | Role definitions, grants, RLS, and field-level restrictions                |
| Dashboard readiness     | Dashboard validation plan and reconciliation queries                       |
| Final report            | Project architecture, results, assumptions, limitations, and next steps    |

## 14. Recommended Next Steps

1. Complete direct-access denial testing using the actual regional test login.
2. Choose and configure Power BI or Tableau.
3. Connect the BI tool to the approved semantic views.
4. Build the planned dashboard components.
5. Validate unfiltered baseline metrics against PostgreSQL.
6. Test date, category, customer-segment, and combined filters.
7. Verify that dashboard users cannot bypass database security.
8. Record actual dashboard results in `docs/07_dashboard_validation.md`.
9. Re-run SQL validations, Python checks, and pytest after significant changes.
10. Review credentials, role memberships, and database permissions before deployment.

## 15. Conclusion

The E-Commerce Semantic Layer project establishes reusable PostgreSQL semantic views, governed business metrics, repeatable data-quality checks, and a documented security model.

The current database implementation has passed its recorded metric validations and all 77 tests in the final pytest run. Revenue and estimated-profit calculations reconcile across the tested semantic views.

The next major milestone is to complete the outstanding security denial checks and implement and validate the BI dashboard. Once those activities are complete, the project will have a stronger end-to-end demonstration of governed metrics, consistent reporting, and controlled data access.
