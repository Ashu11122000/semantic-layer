# Raw CSV Data Import Guide

## 1. Purpose

This document explains how to load the e-commerce practice dataset from CSV files into the PostgreSQL `raw` schema.

The CSV files are the source data for the semantic layer. The raw tables preserve the source fields so that data can be validated before business metrics are calculated.

## 2. Prerequisites

Before importing the data, verify that:

- PostgreSQL is installed and running.
- The `semantic_layer_db` database exists.
- The `raw`, `semantic`, and `metrics` schemas have been created.
- The raw table definitions in `sql/01_raw/01_create_tables.sql` have been executed.
- The project `.env` file contains a valid `DATABASE_URL`.
- The CSV files are available in the project's `data` directory.
- The Python environment and required project dependencies are installed.

Do not commit `.env` or publish database credentials.

## 3. Source CSV Files

The following files are imported:

| CSV file          | PostgreSQL table  | Expected rows |
| ----------------- | ----------------- | ------------: |
| `customers.csv`   | `raw.customers`   |           350 |
| `products.csv`    | `raw.products`    |            26 |
| `orders.csv`      | `raw.orders`      |         1,200 |
| `order_items.csv` | `raw.order_items` |         2,908 |
| `payments.csv`    | `raw.payments`    |         1,200 |
| `returns.csv`     | `raw.returns`     |            42 |
| `reviews.csv`     | `raw.reviews`     |           650 |
| **Total**         | **7 tables**      |     **6,376** |

These are the expected row counts for the supplied practice dataset. If the source CSV files change, update the expected counts accordingly.

## 4. Import Method

The project uses the Python script:

`scripts/load_csv_data.py`

The script reads the database connection settings from `.env`, validates the CSV structure, and loads the data into PostgreSQL.

The import process uses a transaction so that a failed import does not leave a partially completed load.

The script also checks CSV headers and row field counts before loading the files.

## 5. Import Procedure

### Step 1: Open the project directory

In the VS Code PowerShell terminal, verify that the current directory is the project root:

```powershell
Get-Location
```

Expected directory:

`D:\semantic layer\semantic-layer-project`

### Step 2: Verify the source files

Run:

```powershell
Get-ChildItem ".\data\*.csv"
```

Confirm that all seven source CSV files are present.

### Step 3: Verify the raw table definitions

Execute:

```powershell
psql -h localhost -p 5432 -U postgres -d semantic_layer_db -v ON_ERROR_STOP=1 -f ".\sql\01_raw\01_create_tables.sql"
```

Replace `postgres` with the PostgreSQL username used by your environment if necessary.

This command creates the raw tables if they do not already exist.

### Step 4: Load the CSV data

For a fresh database with empty raw tables, run:

```powershell
uv run python ".\scripts\load_csv_data.py"
```

Enter your database password only if prompted.

If the script reports that tables already contain data, do not repeatedly rerun the import command. Inspect the existing row counts first.

### Step 5: Reload data when intentionally replacing existing rows

Only when you deliberately want to replace the existing raw data with the supplied CSV contents, run:

```powershell
uv run python ".\scripts\load_csv_data.py" --replace
```

**Warning:** Use `--replace` only when a replacement load is intended. It can remove existing rows before reloading the source data.

## 6. Validate Row Counts

After the import finishes, execute:

```powershell
psql -h localhost -p 5432 -U postgres -d semantic_layer_db -v ON_ERROR_STOP=1 -f ".\sql\01_raw\03_validate_row_counts.sql"
```

Compare the actual row counts with the expected values in Section 3.

The validation should also report the results of the existing identifier, quantity, review-score, and negative-value checks.

## 7. Validate Relationships

Execute:

```powershell
psql -h localhost -p 5432 -U postgres -d semantic_layer_db -v ON_ERROR_STOP=1 -f ".\sql\01_raw\04_validate_relationships.sql"
```

Confirm that the relationship checks report no unmatched or null relationship keys for:

- Orders to customers.
- Order items to orders.
- Order items to products.
- Payments to orders.
- Returns to orders.
- Reviews to orders.

These checks validate the relationships present in the imported data. They do not establish that every business rule or date condition is valid.

## 8. Import Acceptance Criteria

The import is accepted when:

1. All seven CSV files are present.
2. All seven raw tables contain the expected number of rows.
3. CSV headers and field counts are valid.
4. Required identifiers are present.
5. Quantity and review-score checks pass.
6. The existing negative-value checks pass.
7. The relationship checks report no unmatched or null relationship keys.
8. No import error remains unresolved.

## 9. Troubleshooting

### Database connection failure

Check that PostgreSQL is running, the database name is correct, and `.env` contains a valid connection URL.

### Missing CSV file

Confirm that the file exists under the project's `data` directory and that its name matches the expected source filename.

### Row-count mismatch

Inspect the source CSV row count and PostgreSQL table count. Check whether the previous load completed, whether the source file changed, or whether a replacement load is required.

### Import reports existing data

Run the row-count validation before deciding whether to reload. Use `--replace` only when the existing raw data should be replaced.

### Relationship validation fails

Inspect the unmatched identifiers in the relevant child and parent tables. Correct the source or loading issue before proceeding to the semantic layer.

## 10. Downstream Use

After the raw data import and validation are complete, the semantic layer can create business-facing SQL views using the approved metric definitions.

The raw schema should remain the source layer; business calculations belong in the semantic views and governed metric definitions.
