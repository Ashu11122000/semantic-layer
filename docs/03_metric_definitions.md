# Metric Definitions

## 1. Purpose

This document defines the business metrics used by the e-commerce semantic layer. Each metric has a consistent name, definition, calculation, source fields, and applicable business rules.

The metrics are calculated from the raw PostgreSQL tables populated from the supplied CSV files.

## 2. Source Tables

| Source table      | Purpose                                                     |
| ----------------- | ----------------------------------------------------------- |
| `raw.customers`   | Customer attributes and segmentation                        |
| `raw.orders`      | Order dates, statuses, and shipping fees                    |
| `raw.order_items` | Quantities, historical selling prices, costs, and discounts |
| `raw.products`    | Product names, categories, and current listed prices/costs  |
| `raw.payments`    | Payment methods and payment statuses                        |
| `raw.returns`     | Returned orders and return reasons                          |
| `raw.reviews`     | Customer review scores                                      |

Historical selling prices and costs from `raw.order_items` are used for sales calculations. Current product catalog prices and costs are not substituted for historical transaction values.

## 3. Metric Definitions

### Metric 1: Gross Sales

**Business definition:** The total value of items before discounts.

**Calculation:**

`Gross Sales = SUM(quantity × unit_price_at_sale)`

**Source fields:**

- `raw.order_items.quantity`
- `raw.order_items.unit_price_at_sale`

**Unit:** Currency.

**Business rules:**

- Calculate gross sales at the order-line level before aggregation.
- Do not subtract discounts in this metric.
- Exclude shipping fees from item gross sales.
- Apply the approved sales-order eligibility rule consistently.

### Metric 2: Total Discounts

**Business definition:** The total discount granted across eligible order lines.

**Calculation:**

`Total Discounts = SUM(discount_amount)`

**Source field:** `raw.order_items.discount_amount`

**Unit:** Currency.

**Business rules:**

- `discount_amount` represents the total discount for the order line.
- Do not multiply `discount_amount` by quantity.
- Use the same eligible orders as the corresponding sales metric.

### Metric 3: Net Item Revenue

**Business definition:** Item sales value after discounts and before shipping fees.

**Calculation:**

`Net Item Revenue = Gross Sales − Total Discounts`

Equivalent order-line calculation:

`SUM((quantity × unit_price_at_sale) − discount_amount)`

**Source fields:**

- `raw.order_items.quantity`
- `raw.order_items.unit_price_at_sale`
- `raw.order_items.discount_amount`

**Unit:** Currency.

**Business rules:**

- Shipping fees are excluded.
- Discounts are subtracted once per order line.
- Returned-order treatment must follow the approved reporting policy.
- This metric represents item revenue under the dataset's practice conventions; it is not a claim of audited accounting revenue.

### Metric 4: Estimated Product Cost

**Business definition:** Estimated cost of the products sold on eligible order lines.

**Calculation:**

`Estimated Product Cost = SUM(quantity × unit_cost_at_sale)`

**Source fields:**

- `raw.order_items.quantity`
- `raw.order_items.unit_cost_at_sale`

**Unit:** Currency.

**Business rules:**

- Use historical unit cost recorded at order time.
- Do not use the current product catalog cost for historical transactions.
- Exclude shipping costs because the dataset does not identify them as product costs.

### Metric 5: Estimated Gross Profit

**Business definition:** Estimated profit from item sales after discounts and estimated product costs.

**Calculation:**

`Estimated Gross Profit = Net Item Revenue − Estimated Product Cost`

Equivalent order-line calculation:

`SUM((quantity × unit_price_at_sale) − discount_amount − (quantity × unit_cost_at_sale))`

**Source fields:**

- `raw.order_items.quantity`
- `raw.order_items.unit_price_at_sale`
- `raw.order_items.unit_cost_at_sale`
- `raw.order_items.discount_amount`

**Unit:** Currency.

**Business rules:**

- This is an estimated product gross profit metric.
- It excludes shipping revenue, shipping costs, operating expenses, taxes, and other expenses not represented by the required formula.
- It must not be described as net profit.

### Metric 6: Shipping Fees

**Business definition:** Shipping fees recorded against eligible orders.

**Calculation:**

`Shipping Fees = SUM(shipping_fee)`

**Source field:** `raw.orders.shipping_fee`

**Unit:** Currency.

**Business rules:**

- Report shipping fees separately from item revenue.
- Do not silently add shipping fees to gross sales or net item revenue.
- Use the same order eligibility policy as the associated sales report.

### Metric 7: Order Count

**Business definition:** The number of distinct eligible orders.

**Calculation:**

`Order Count = COUNT(DISTINCT order_id)`

**Source field:** `raw.orders.order_id`

**Unit:** Orders.

**Business rules:**

- Count distinct orders, not order-item rows.
- An order with multiple products counts once.
- Cancelled-order treatment must be consistent with the sales reporting policy.

### Metric 8: Average Order Value (AOV)

**Business definition:** Average net item revenue per eligible order.

**Calculation:**

`AOV = Net Item Revenue ÷ Order Count`

**Unit:** Currency per order.

**Business rules:**

- Calculate revenue at order-line level and aggregate it to eligible orders.
- Count each eligible order once.
- Exclude shipping fees.
- Do not calculate AOV by dividing revenue by the number of order-item rows.
- Use the same order population in the numerator and denominator.

### Metric 9: Return Rate by Order

**Business definition:** The percentage of eligible orders associated with a recorded return.

**Calculation:**

`Return Rate = Returned Eligible Orders ÷ Eligible Orders × 100`

**Source fields:**

- `raw.orders.order_id`
- `raw.returns.order_id`

**Unit:** Percentage.

**Business rules:**

- Count distinct returned orders.
- The dataset records returns at the order level, not at the returned-product or returned-quantity level.
- This metric is an order-based return rate, not a unit return rate or a monetary refund rate.
- The denominator and reporting period must be documented and applied consistently.

### Metric 10: Average Review Score

**Business definition:** The average recorded customer review score for eligible review records.

**Calculation:**

`Average Review Score = AVG(review_score)`

**Source field:** `raw.reviews.review_score`

**Unit:** Score from 1 to 5.

**Business rules:**

- Use valid review scores from 1 to 5.
- Exclude missing scores from the average.
- Avoid duplicating review records when joining reviews to order-item data.

## 4. Order Eligibility and Reporting Policy

The dataset README requires a consistent decision about cancelled and returned orders. The following policy will be used for the initial sales-performance reporting layer:

1. Exclude orders whose `order_status` is `Cancelled`, using a case-insensitive comparison.
2. Include other non-cancelled order statuses in the initial order-based sales metrics, and report status separately where useful.
3. Treat a returned order as a recorded return, not as proof that all items were refunded or that all revenue must be reversed.
4. Do not automatically exclude returned orders from gross sales, net item revenue, or estimated gross profit. Report return metrics separately until refund amounts and returned quantities are available.
5. Do not filter sales based on `payment_status` in the initial sales metrics. Payment status will be analyzed separately because the dataset does not define a reconciliation rule between payment records and sales.
6. Apply the same order eligibility policy to gross sales, discounts, net item revenue, estimated product cost, estimated gross profit, shipping fees, order count, and AOV.

These are project reporting decisions, not rules explicitly mandated by the source dataset. They should be revisited if additional refund, cancellation, or accounting requirements are introduced.

## 5. Join and Aggregation Rules

- Join orders to customers using `customer_id`.
- Join order items to orders using `order_id`.
- Join order items to products using `product_id`.
- Join payments, returns, and reviews to orders using `order_id`.
- Aggregate order-item metrics before joining them to other one-to-many datasets where necessary.
- Avoid joins that multiply revenue, costs, discounts, or order counts.
- Use distinct order counts for order-level metrics.

## 6. Known Limitations

- Refund amounts are not supplied.
- Returned product IDs and returned quantities are not supplied.
- Shipping costs are not supplied.
- The dataset is synthetic and intended for learning and portfolio practice.
- Estimated gross profit is not net profit or audited accounting profit.
- Current product prices and costs may differ from historical transaction values.

## 7. Validation Requirements

Before the metrics are published, validate that:

1. Gross sales equal the sum of eligible line quantities multiplied by historical unit prices.
2. Total discounts equal the sum of eligible line-level discounts.
3. Net item revenue equals gross sales minus total discounts.
4. Estimated product cost equals eligible quantities multiplied by historical unit costs.
5. Estimated gross profit equals net item revenue minus estimated product cost.
6. Shipping fees remain separate from item revenue.
7. Order count uses distinct orders.
8. AOV uses eligible net item revenue divided by eligible distinct orders.
9. Return rate uses distinct returned eligible orders divided by eligible orders.
10. SQL views and the BI dashboard produce consistent results under identical filters.
