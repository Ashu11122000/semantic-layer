# 07 — Dashboard Validation

## 1. Purpose

This document defines the validation plan for the Business Intelligence (BI) dashboard connected to the E-Commerce Semantic Layer project.

The objective is to ensure that dashboard metrics match the governed definitions, filters behave consistently, visualizations use the correct data grain, and users cannot access unauthorized information.

This validation plan applies to Power BI or Tableau.

**Status:** Validation plan documented. Dashboard-specific execution results must be recorded after the dashboard is implemented and tested.

## 2. Dashboard Data Source

The dashboard should use the approved PostgreSQL semantic views rather than independently recreating business calculations in individual charts.

| Semantic view                     | Intended dashboard use                          |
| --------------------------------- | ----------------------------------------------- |
| `semantic.vw_order_line_metrics`  | Revenue and profit analysis at order-line level |
| `semantic.vw_sales_metrics`       | Aggregated sales analysis                       |
| `semantic.vw_customer_summary`    | Customer-level performance                      |
| `semantic.vw_product_performance` | Product and category performance                |
| `semantic.vw_return_analysis`     | Return analysis                                 |

Use the appropriate view for each visual. Avoid joining multiple views at different grains in a way that duplicates revenue or profit.

## 3. Governed Metrics and Expected Results

The following values were validated against the current database and should be used as baseline values when testing the dashboard without additional filters.

| Metric                         | Governed definition                                                                      | Expected baseline |
| ------------------------------ | ---------------------------------------------------------------------------------------- | ----------------: |
| Gross sales                    | Sum of eligible order-line quantities multiplied by historical sale prices               |     48,236,547.60 |
| Total discounts                | Sum of recorded discount amounts for eligible order lines                                |      3,863,139.42 |
| Net item revenue               | Gross sales minus total discounts                                                        |     44,373,408.18 |
| Estimated product cost         | Sum of eligible quantities multiplied by historical unit costs                           |     30,185,799.68 |
| Estimated gross profit         | Net item revenue minus estimated product cost                                            |     14,187,608.50 |
| Estimated gross margin         | Estimated gross profit divided by net item revenue, multiplied by 100                    |            31.97% |
| Average order value            | Eligible net item revenue divided by distinct eligible orders                            |         39,338.13 |
| Customers with eligible orders | Number of customers with at least one eligible order                                     |               338 |
| Total customers                | Number of customers in the customer source/summary                                       |               350 |
| Eligible orders                | Number of distinct orders eligible for sales metrics                                     |             1,128 |
| Distinct returned orders       | Number of distinct eligible orders with a return record                                  |                42 |
| Order return rate              | Distinct returned eligible orders divided by eligible distinct orders, multiplied by 100 |             3.72% |

These values are dataset-specific baselines, not universal targets. If the source data or documented business rules change, revalidate and update the expected values.

## 4. Business Rules to Validate

### 4.1 Revenue

- Gross sales use historical transaction prices, not current product catalogue prices.
- Discounts are summed from `discount_amount`; they are not multiplied by quantity again.
- Net item revenue equals gross sales minus discounts.
- Shipping fees are tracked separately and must not be silently included in item revenue.

### 4.2 Profit

- Estimated product cost uses historical transaction cost multiplied by quantity.
- Estimated gross profit equals net item revenue minus estimated product cost.
- Estimated gross margin is calculated from aggregate profit divided by aggregate net item revenue.
- Profit and margin must not be recalculated using current product costs.

### 4.3 Order eligibility

- Cancelled orders are excluded from eligible sales metrics.
- Returned orders remain eligible unless the documented business rule changes.
- A return record does not independently establish a refund amount or returned quantity.

### 4.4 Customer and product coverage

- The customer summary should retain all 350 source customers, including customers with no eligible orders.
- The product-performance view should retain all 26 source products.
- Zero-activity entities must not disappear from a visualization unless an explicit filter excludes them.

## 5. Dashboard Components

The dashboard should contain the following recommended components.

| Component            | Recommended visualization   | Main validation                          |
| -------------------- | --------------------------- | ---------------------------------------- |
| Revenue overview     | KPI cards                   | Gross sales, discounts, net item revenue |
| Profitability        | KPI cards and bar chart     | Estimated profit, cost, margin           |
| Sales trends         | Line chart                  | Date aggregation and date filters        |
| Product performance  | Bar chart or table          | Revenue and profit by product/category   |
| Customer performance | Bar chart or table          | Customer counts, order counts, revenue   |
| Returns              | KPI card and category chart | Distinct returned orders and return rate |

Every visual should have a descriptive title, readable labels, appropriate number formatting, and a clearly stated metric definition where needed.

## 6. Filter Validation

Test the dashboard with no filters first, then apply each filter individually.

| Filter                           | Expected behavior                                                        | Result  |
| -------------------------------- | ------------------------------------------------------------------------ | ------- |
| Order date                       | Filters eligible sales and date-based trends consistently                | Pending |
| Product category                 | Restricts product metrics to the selected category                       | Pending |
| Product                          | Restricts metrics to the selected product                                | Pending |
| Customer segment                 | Restricts customer analysis to the selected segment                      | Pending |
| Region                           | Restricts results according to the intended analytical or security rules | Pending |
| Order status                     | Cancelled orders must not enter governed sales metrics                   | Pending |
| Return status or return presence | Must use the documented return definition                                | Pending |
| Multiple filters                 | Combined selections must produce consistent results                      | Pending |
| Clear/reset filters              | Restores the unfiltered baseline                                         | Pending |

A filter should affect only visuals whose data and business meaning support that filter. Document any intentionally disconnected filters.

## 7. Metric Reconciliation Procedure

For each KPI or aggregate shown in the dashboard:

1. Record the dashboard value with all filters cleared.
2. Query the corresponding semantic view in PostgreSQL.
3. Apply equivalent filters in SQL and in the BI dashboard.
4. Compare the dashboard result with the SQL result.
5. Repeat with at least one filtered scenario.
6. Record the difference and investigate discrepancies.

For financial measures, use a tolerance of 0.01 in the underlying currency units unless the reporting specification defines a different tolerance. Percentage comparisons should use the documented rounding precision.

### Example: Validate net item revenue

```sql
SELECT ROUND(SUM(net_item_revenue)::numeric, 2) AS net_item_revenue
FROM semantic.vw_order_line_metrics
WHERE is_sales_eligible;
```

Expected baseline: `44373408.18`.

### Example: Validate estimated gross profit

```sql
SELECT ROUND(SUM(estimated_gross_profit)::numeric, 2)
       AS estimated_gross_profit
FROM semantic.vw_order_line_metrics
WHERE is_sales_eligible;
```

Expected baseline: `14187608.50`.

### Example: Validate estimated gross margin

```sql
SELECT ROUND(
    100.0 * SUM(estimated_gross_profit)
    / NULLIF(SUM(net_item_revenue), 0),
    2
) AS estimated_gross_margin_pct
FROM semantic.vw_order_line_metrics
WHERE is_sales_eligible;
```

Expected baseline: `31.97`.

These queries provide baseline checks. Add matching date, product, customer, and regional predicates when validating filtered dashboard results.

## 8. Security Validation

Dashboard filters are not a replacement for database access controls.

Validate that:

- The dashboard uses an appropriately restricted database account.
- Regional users cannot access unauthorized regions through direct database access.
- Restricted customer fields are not exposed through another view or data source.
- Dashboard filters cannot bypass PostgreSQL row-level security.
- Analyst and regional-manager permissions match `docs/06_security_matrix.md`.
- Access tests are performed with the actual role-specific database login, not only with an administrator connection.

Record successful and failed access attempts in the security validation results.

## 9. Dashboard Test Log

Use this table to record actual results after implementation.

| Test ID | Test                              | Expected result                       | Actual result | Status  |
| ------- | --------------------------------- | ------------------------------------- | ------------- | ------- |
| DB-01   | Unfiltered net item revenue       | 44,373,408.18                         | Not run       | Pending |
| DB-02   | Unfiltered estimated gross profit | 14,187,608.50                         | Not run       | Pending |
| DB-03   | Unfiltered estimated gross margin | 31.97%                                | Not run       | Pending |
| DB-04   | Cancelled-order exclusion         | No cancelled lines in eligible sales  | Not run       | Pending |
| DB-05   | Product-category filter           | SQL and dashboard agree               | Not run       | Pending |
| DB-06   | Date filter                       | SQL and dashboard agree               | Not run       | Pending |
| DB-07   | Customer-segment filter           | SQL and dashboard agree               | Not run       | Pending |
| DB-08   | Multiple filters combined         | SQL and dashboard agree               | Not run       | Pending |
| DB-09   | Clear filters                     | Baseline values restored              | Not run       | Pending |
| DB-10   | Regional access restriction       | Only authorized region is accessible  | Not run       | Pending |
| DB-11   | Restricted field access           | Restricted fields remain inaccessible | Not run       | Pending |

Do not mark a test as passed until its actual result has been observed.

## 10. Discrepancy Log

For every failed comparison, record:

- Test ID and execution date
- Dashboard visual and metric
- Filters and selections applied
- Dashboard value
- SQL validation value
- Difference
- Root cause
- Corrective action
- Retest result

Investigate common causes such as:

- Duplicate rows from joins
- Incorrect aggregation grain
- Missing cancelled-order exclusions
- Discount or cost
