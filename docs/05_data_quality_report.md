# Data Quality and Semantic Validation Report

## 1. Objective

This report documents the validation of the raw e-commerce data, semantic views, and governed revenue and profit metrics in the PostgreSQL semantic-layer project.

## 2. Raw Data Validation

The seven raw tables contain 6,376 records in total.

| Source table | Expected and validated rows |
| ------------ | --------------------------: |
| Customers    |                         350 |
| Products     |                          26 |
| Orders       |                       1,200 |
| Order items  |                       2,908 |
| Payments     |                       1,200 |
| Returns      |                          42 |
| Reviews      |                         650 |
| **Total**    |                   **6,376** |

The implemented checks reported zero duplicate primary-key groups, zero missing required identifiers, zero invalid review scores, zero invalid quantities or negative monetary values, and zero broken relationships among the checked tables.

## 3. Revenue Metric Validation

| Metric           | Validated value |
| ---------------- | --------------: |
| Gross sales      |   48,236,547.60 |
| Total discounts  |    3,863,139.42 |
| Net item revenue |   44,373,408.18 |

The order-line totals matched the governed sales metrics. All three reconciliation differences were 0.00.

The independent revenue formula check also returned a difference of 0.00.

**Business rule:** Net item revenue equals gross sales minus discounts. Shipping fees are excluded.

## 4. Profit Metric Validation

| Metric                 | Validated value |
| ---------------------- | --------------: |
| Estimated product cost |   30,185,799.68 |
| Estimated gross profit |   14,187,608.50 |
| Estimated gross margin |          31.97% |

The estimated cost and profit totals reconciled between the order-line and product-performance views. Both differences were 0.00.

The independent profit formula check returned a difference of 0.00.

**Business rule:** Estimated gross profit equals net item revenue minus estimated product cost. These are estimates based on historical transaction costs, not audited accounting profit.

## 5. Semantic View Validation

| Semantic view                     | Validated rows |
| --------------------------------- | -------------: |
| `semantic.vw_order_line_metrics`  |          2,908 |
| `semantic.vw_sales_metrics`       |            749 |
| `semantic.vw_customer_summary`    |            350 |
| `semantic.vw_product_performance` |             26 |
| `semantic.vw_return_analysis`     |             42 |

No duplicate customer IDs or product IDs were detected in their respective summary views. Revenue and estimated profit reconciled across the sales, customer, and product views, with all four differences equal to 0.00.

## 6. Cancelled Order Handling

The validation identified 167 order lines belonging to cancelled orders. All 167 were excluded from eligible sales metrics, and zero cancelled lines were marked eligible.

This follows the documented policy of excluding orders whose normalized status is `cancelled`.

## 7. Security Validation Evidence

The secured customer metrics table contains 350 customer rows when inspected by the administrator. A dedicated regional test login was assigned to the North region and returned 71 customers from that region through `semantic.vw_customer_metrics_secure`.

The regional view test confirmed that the login could see one region only: North.

The access-denial test for the unrestricted customer summary view should be recorded separately after it has been verified using the regional test login.

## 8. Conclusion

The implemented raw-data, revenue, profit, and semantic-view validation checks passed. The results demonstrate consistency across the checked semantic metrics and adherence to the documented cancelled-order policy.

These results apply to the checks performed; they do not prove that every possible data quality issue has been eliminated. Dashboard-level validation and the remaining security access tests should be documented separately.
