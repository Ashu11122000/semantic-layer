# Metric Governance

## 1. Purpose

This document establishes governance rules for the e-commerce semantic layer. It identifies metric ownership, approved calculations, source tables, reporting restrictions, and validation responsibilities.

The purpose is to ensure that PostgreSQL semantic views, SQL metric calculations, and BI dashboards use consistent business definitions.

## 2. Governance Principles

1. Every published metric must have one documented business definition.
2. Metric calculations must use the approved source fields and formulas.
3. Filters must be consistent across reports unless a different scope is explicitly documented.
4. Historical transaction prices and costs must be used for historical sales calculations.
5. Shipping fees must remain separate from item revenue.
6. Returned orders must not automatically be treated as fully refunded because refund amounts and returned quantities are unavailable.
7. Metric changes must be documented and validated before they are published.
8. Sensitive customer information must not be exposed to unauthorized dashboard users.

## 3. Metric Ownership and Governance Register

For this portfolio project, the roles below are proposed responsibilities. They do not represent actual organizational appointments.

| Metric                 | Business owner role         | Technical steward role | Approved source                 | Main restriction                                     |
| ---------------------- | --------------------------- | ---------------------- | ------------------------------- | ---------------------------------------------------- |
| Gross Sales            | Sales Manager               | Data Engineer          | `raw.order_items`, `raw.orders` | Exclude cancelled orders; exclude shipping           |
| Total Discounts        | Sales Manager               | Data Engineer          | `raw.order_items`, `raw.orders` | Sum line-level discounts once                        |
| Net Item Revenue       | Finance Manager             | Analytics Engineer     | `raw.order_items`, `raw.orders` | Gross sales minus discounts                          |
| Estimated Product Cost | Finance Manager             | Data Engineer          | `raw.order_items`, `raw.orders` | Use historical unit costs                            |
| Estimated Gross Profit | Finance Manager             | Analytics Engineer     | `raw.order_items`, `raw.orders` | Not net profit; exclude unsupported expenses         |
| Shipping Fees          | Operations Manager          | Data Engineer          | `raw.orders`                    | Report separately from item revenue                  |
| Order Count            | Sales Manager               | Analytics Engineer     | `raw.orders`                    | Count distinct eligible orders                       |
| Average Order Value    | Sales Manager               | Analytics Engineer     | `raw.orders`, `raw.order_items` | Eligible net item revenue divided by eligible orders |
| Return Rate by Order   | Customer Operations Manager | Analytics Engineer     | `raw.orders`, `raw.returns`     | Count distinct returned orders                       |
| Average Review Score   | Customer Experience Manager | Analytics Engineer     | `raw.reviews`                   | Average valid review scores from 1 to 5              |

## 4. Approved Sales Reporting Policy

The following rules govern the initial sales reporting layer:

- Exclude orders whose status equals `Cancelled`, ignoring differences in letter case.
- Include other non-cancelled statuses in the initial sales calculations.
- Keep returned orders in sales calculations unless a future approved policy explicitly requires revenue reversals.
- Report returns separately because the source data does not provide refund amounts or returned quantities.
- Do not filter sales metrics by payment status until a documented reconciliation rule is established.
- Calculate order-item metrics before combining them with other one-to-many tables to avoid double counting.
- Apply identical eligibility rules to gross sales, discounts, net item revenue, estimated product cost, estimated gross profit, shipping fees, order count, and AOV.

These rules are project-level reporting decisions based on the available dataset. They are not universal accounting rules.

## 5. Metric Calculation Controls

### Gross Sales

- Formula: `SUM(quantity * unit_price_at_sale)`.
- Use historical unit prices from order items.
- Exclude discounts and shipping fees.
- Exclude cancelled orders.

### Total Discounts

- Formula: `SUM(discount_amount)`.
- Treat each value as the total discount for its order line.
- Do not multiply the discount by quantity.

### Net Item Revenue

- Formula: `Gross Sales - Total Discounts`.
- Exclude shipping fees.
- Use the approved order eligibility policy.

### Estimated Product Cost

- Formula: `SUM(quantity * unit_cost_at_sale)`.
- Use historical costs from order items.
- Do not substitute current product catalog costs.

### Estimated Gross Profit

- Formula: `Net Item Revenue - Estimated Product Cost`.
- Do not label this as net profit.
- Shipping costs and other operating expenses are unavailable in the source dataset.

### Shipping Fees

- Formula: `SUM(shipping_fee)`.
- Use eligible orders.
- Do not silently add shipping fees to item revenue.

### Order Count

- Formula: `COUNT(DISTINCT order_id)`.
- Count orders, not order-item rows.

### Average Order Value

- Formula: `Eligible Net Item Revenue / Eligible Distinct Orders`.
- Protect against division by zero.
- Keep the numerator and denominator on the same order population.

### Return Rate by Order

- Formula: `Distinct Returned Eligible Orders / Eligible Orders * 100`.
- Use distinct order identifiers.
- Do not interpret this as a monetary refund rate or returned-unit rate.

### Average Review Score

- Formula: `AVG(review_score)`.
- Accept valid scores from 1 to 5.
- Prevent duplicated review records when joining review data to order items.

## 6. Change Management

A proposed metric change must include:

1. The reason for the change.
2. The existing and proposed definitions.
3. The source fields and calculation changes.
4. The expected impact on existing dashboards.
5. The SQL validation results.
6. The date and version of the approved change.

After a change, rerun the relevant validation queries and compare the SQL results with the BI dashboard.

## 7. Validation and Reconciliation

Before a metric is published:

- Verify source-table row counts and relationship integrity.
- Validate the metric against an independent SQL calculation.
- Check for double counting caused by joins.
- Test the metric with the approved order filters.
- Compare results between semantic views and dashboard visuals.
- Record discrepancies, investigation steps, and resolution status.

A metric must not be marked as validated merely because its SQL query executes successfully.

## 8. Limitations and Future Improvements

The dataset does not include refund amounts, returned quantities, shipping costs, or a documented payment-reconciliation policy. Therefore:

- Monetary refund rates cannot be calculated reliably.
- Returned-unit rates cannot be calculated reliably.
- Net profit cannot be calculated from the available product-cost fields alone.
- Payment status should be analyzed separately until reconciliation rules are defined.

These limitations must be communicated to dashboard users.
