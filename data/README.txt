E-COMMERCE SEMANTIC LAYER PRACTICE DATASET
==========================================

This is a synthetic dataset created for learning and portfolio practice. It does not represent real people or a real business.

Files:
- customers.csv: customer and region details
- orders.csv: order headers, dates, status, shipping fee
- products.csv: product catalog and current list price/cost
- order_items.csv: item-level sales, quantities, historical price/cost snapshots, discounts
- payments.csv: payment method and payment status
- returns.csv: returned orders and reasons
- reviews.csv: customer review scores
- data_dictionary.csv: field descriptions and notes

Suggested relationships:
customers.customer_id 1 -> many orders.customer_id
orders.order_id 1 -> many order_items.order_id
products.product_id 1 -> many order_items.product_id
orders.order_id 1 -> one payment record in this practice dataset
orders.order_id 1 -> zero/one return record
orders.order_id 1 -> zero/one review record

Important metric conventions to decide and document:
- Gross sales = quantity * unit_price_at_sale
- Discounts = sum(discount_amount)
- Net item revenue = gross sales - discounts
- Estimated product cost = quantity * unit_cost_at_sale
- Estimated gross profit = net item revenue - estimated product cost
- Shipping fees are separate and should not silently be included in item revenue.
- For sales performance, define whether cancelled and returned orders are excluded, and apply the same rule consistently.
- This dataset is synthetic; values and relationships are generated for educational use.
