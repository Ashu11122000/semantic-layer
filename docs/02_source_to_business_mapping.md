# Source-to-Business Mapping

## 1. Purpose

This document maps the raw e-commerce dataset fields to business concepts, reporting dimensions, and governed metrics.

The mapping provides traceability from the original CSV files to PostgreSQL raw tables and the business-facing semantic layer.

## 2. Data Flow

The project follows this data flow:

**CSV files → PostgreSQL raw schema → PostgreSQL semantic views → Governed metrics → BI dashboard**

- **CSV files:** Original source data.
- **Raw schema:** Source fields loaded into PostgreSQL with minimal transformation.
- **Semantic views:** Business-friendly names, joins, and calculations.
- **Governed metrics:** Approved definitions, calculation rules, and reporting restrictions.
- **BI dashboard:** Visual reporting using the approved semantic layer.

The implementation uses PostgreSQL SQL views. dbt is not required for this architecture.

## 3. Source-to-Table Mapping

| Source file       | PostgreSQL table  | Business purpose                                               |
| ----------------- | ----------------- | -------------------------------------------------------------- |
| `customers.csv`   | `raw.customers`   | Customer profiles and segmentation                             |
| `products.csv`    | `raw.products`    | Product catalog and current prices/costs                       |
| `orders.csv`      | `raw.orders`      | Order dates, statuses, and shipping fees                       |
| `order_items.csv` | `raw.order_items` | Transaction quantities, historical prices/costs, and discounts |
| `payments.csv`    | `raw.payments`    | Payment methods, statuses, and dates                           |
| `returns.csv`     | `raw.returns`     | Returned orders and return reasons                             |
| `reviews.csv`     | `raw.reviews`     | Customer review scores and dates                               |

## 4. Customer Mapping

**Source:** `customers.csv`

**Target:** `raw.customers`

| Source field    | Business concept           | Intended use                                |
| --------------- | -------------------------- | ------------------------------------------- |
| `customer_id`   | Customer identifier        | Customer joins and distinct customer counts |
| `customer_name` | Customer name              | Customer display; restrict where necessary  |
| `segment`       | Customer segment           | Segment-based reporting                     |
| `city`          | Customer city              | Geographic analysis                         |
| `region`        | Sales region               | Regional reporting                          |
| `signup_date`   | Customer registration date | Customer acquisition and cohort analysis    |

### Business use

Customer attributes support customer summaries, regional analysis, segmentation, and customer-level performance reporting.

Customer names should not be exposed in reports that do not require identifying customers.

## 5. Order Mapping

**Source:** `orders.csv`

**Target:** `raw.orders`

| Source field    | Business concept     | Intended use                          |
| --------------- | -------------------- | ------------------------------------- |
| `order_id`      | Order identifier     | Distinct order counts and joins       |
| `customer_id`   | Ordering customer    | Customer relationship                 |
| `order_date`    | Order date           | Sales trends and time filtering       |
| `order_status`  | Current order status | Order eligibility and status analysis |
| `shipping_fee`  | Shipping fee         | Separate shipping-fee reporting       |
| `ship_date`     | Shipment date        | Fulfilment analysis                   |
| `delivery_date` | Delivery date        | Delivery performance analysis         |

### Business use

Order attributes define the order population and support sales trends, fulfilment reporting, shipping-fee analysis, and customer-order relationships.

Cancelled orders are excluded from the initial sales-performance reporting policy. Other statuses are included unless a separately documented rule specifies otherwise.

## 6. Order-Item Mapping

**Source:** `order_items.csv`

**Target:** `raw.order_items`

| Source field         | Business concept                  | Intended use                          |
| -------------------- | --------------------------------- | ------------------------------------- |
| `order_item_id`      | Order-line identifier             | Order-line grain and uniqueness       |
| `order_id`           | Associated order                  | Join to order information             |
| `product_id`         | Sold product                      | Product analysis                      |
| `quantity`           | Units sold                        | Quantity and cost calculations        |
| `unit_price_at_sale` | Historical unit selling price     | Gross sales                           |
| `unit_cost_at_sale`  | Historical unit cost              | Estimated product cost                |
| `discount_amount`    | Total discount for the order line | Discount and net revenue calculations |

### Business use

This table is the primary source for transaction-level sales metrics.

The order-line grain is one row per `order_item_id`.

### Approved calculations

- Gross sales = `quantity × unit_price_at_sale`
- Total discounts = `discount_amount`
- Net item revenue = `(quantity × unit_price_at_sale) − discount_amount`
- Estimated product cost = `quantity × unit_cost_at_sale`
- Estimated gross profit = `net item revenue − estimated product cost`

The discount is already the total for the order line. It must not be multiplied by quantity again.

## 7. Product Mapping

**Source:** `products.csv`

**Target:** `raw.products`

| Source field   | Business concept          | Intended use                 |
| -------------- | ------------------------- | ---------------------------- |
| `product_id`   | Product identifier        | Product joins                |
| `product_name` | Product name              | Product display and analysis |
| `category`     | Product category          | Category-level performance   |
| `unit_price`   | Current listed unit price | Current catalog reporting    |
| `unit_cost`    | Current unit cost         | Current catalog analysis     |
| `active_flag`  | Product active status     | Product catalog filtering    |

### Business use

Product attributes provide category and descriptive context for transaction metrics.

Historical sales and profit calculations must use `unit_price_at_sale` and `unit_cost_at_sale` from `raw.order_items`, rather than substituting current catalog prices or costs.

## 8. Payment Mapping

**Source:** `payments.csv`

**Target:** `raw.payments`

| Source field     | Business concept          | Intended use                  |
| ---------------- | ------------------------- | ----------------------------- |
| `payment_id`     | Payment record identifier | Payment-record identification |
| `order_id`       | Associated order          | Join to orders                |
| `payment_method` | Payment method            | Payment-method analysis       |
| `payment_status` | Payment state             | Payment-status analysis       |
| `payment_date`   | Payment recording date    | Payment timing analysis       |

### Business use

Payment fields support payment-method and payment-status reporting.

Payment status must not silently filter sales metrics. The initial sales policy does not filter by payment status because a reconciliation rule has not been established.

## 9. Return Mapping

**Source:** `returns.csv`

**Target:** `raw.returns`

| Source field    | Business concept         | Intended use                            |
| --------------- | ------------------------ | --------------------------------------- |
| `return_id`     | Return record identifier | Return-record identification            |
| `order_id`      | Returned order           | Identify orders associated with returns |
| `return_date`   | Return date              | Return trends                           |
| `return_reason` | Return reason            | Return-reason analysis                  |

### Business use

The dataset supports an order-based return rate and return-reason analysis.

It does not supply returned product IDs, returned quantities, or refund amounts. Therefore, it cannot independently support a returned-unit rate or monetary refund rate.

## 10. Review Mapping

**Source:** `reviews.csv`

**Target:** `raw.reviews`

| Source field   | Business concept       | Intended use                 |
| -------------- | ---------------------- | ---------------------------- |
| `review_id`    | Review identifier      | Review-record identification |
| `order_id`     | Reviewed order         | Join to order information    |
| `review_score` | Review score           | Average review score         |
| `review_date`  | Review submission date | Review trends                |

### Business use

Review data supports average review score and review-trend analysis.

Valid scores are from 1 to 5. Review records must not be duplicated when combined with order-item records.

## 11. Semantic View Mapping

The following views are planned or intended for the semantic layer.

| Semantic view                     | Main sources                     | Business purpose                                                      |
| --------------------------------- | -------------------------------- | --------------------------------------------------------------------- |
| `semantic.vw_order_line_metrics`  | Orders, order items, products    | Calculate line-level sales, discounts, costs, profit, and eligibility |
| `semantic.vw_sales_metrics`       | Orders and order-item metrics    | Aggregate sales metrics consistently                                  |
| `semantic.vw_customer_summary`    | Customers, orders, order metrics | Summarize customer-level performance                                  |
| `semantic.vw_product_performance` | Products, order items, orders    | Analyze product and category performance                              |
| `semantic.vw_return_analysis`     | Orders, returns                  | Analyze return rates and return reasons                               |

These are intended semantic objects. Their actual implementation and successful execution must be verified separately.

## 12. Business Metric Traceability

| Business metric        | Required source fields                     | Calculation                                                   |
| ---------------------- | ------------------------------------------ | ------------------------------------------------------------- |
| Gross sales            | `quantity`, `unit_price_at_sale`           | Sum quantity multiplied by historical unit price              |
| Total discounts        | `discount_amount`                          | Sum line-level discounts                                      |
| Net item revenue       | Quantity, historical unit price, discount  | Gross sales minus discounts                                   |
| Estimated product cost | `quantity`, `unit_cost_at_sale`            | Sum quantity multiplied by historical unit cost               |
| Estimated gross profit | Revenue and historical product cost fields | Net item revenue minus estimated product cost                 |
| Shipping fees          | `shipping_fee`                             | Sum shipping fees for eligible orders                         |
| Order count            | `order_id`, `order_status`                 | Count distinct eligible orders                                |
| Average order value    | Order IDs and line-level revenue fields    | Eligible net item revenue divided by eligible distinct orders |
| Return rate by order   | Order IDs and return order IDs             | Distinct returned eligible orders divided by eligible orders  |
| Average review score   | `review_score`                             | Average valid review score                                    |

## 13. Join and Aggregation Controls

- Customers join to orders using `customer_id`.
- Orders join to order items using `order_id`.
- Products join to order items using `product_id`.
- Payments, returns, and reviews join to orders using `order_id`.
- Order-level and order-line metrics must be aggregated at the appropriate grain.
- One-to-many joins must not inflate revenue, cost, discounts, or order counts.
- Order counts must use distinct order identifiers.
- Returned orders remain in initial sales metrics unless a later approved policy changes this treatment.

## 14. Known Limitations

- Refund amounts are not provided.
- Returned product IDs and returned quantities are not provided.
- Shipping costs are not provided.
- Payment reconciliation rules are not provided.
- Current product prices and costs may differ from historical transaction values.
- The dataset is synthetic and intended for learning and portfolio practice.

These limitations must be documented wherever they affect dashboard interpretation.
