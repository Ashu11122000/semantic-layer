# 06 — Security Matrix

## 1. Purpose

This document defines the access-control model for the E-Commerce Semantic Layer project. It documents database roles, permitted operations, row-level security (RLS), field-level restrictions, and validation procedures.

The objective is to ensure that users can access only the semantic data required for their responsibilities.

## 2. Security Architecture

The project uses PostgreSQL roles, schema permissions, column-level privileges, and row-level security to control access to semantic data.

The security implementation includes:

- `semantic_admin`: administrative access to semantic objects and authorized security configuration.
- `semantic_analyst`: analytical access to approved semantic views and selected customer metrics.
- `semantic_regional_manager`: restricted customer-metric access based on authorized regions.
- `security.user_region_access`: maps database users to permitted regions.
- `security.is_region_authorized(TEXT)`: helper function used by the regional access policy.
- `semantic.secured_customer_metrics`: protected customer-metrics table.
- `semantic.vw_customer_metrics_secure`: restricted customer-metrics view.

## 3. Role Access Matrix

| Capability                                | Semantic Admin                       | Semantic Analyst                           | Regional Manager                           |
| ----------------------------------------- | ------------------------------------ | ------------------------------------------ | ------------------------------------------ |
| Read order-line metrics                   | Yes                                  | Yes                                        | No                                         |
| Read sales metrics                        | Yes                                  | Yes                                        | No                                         |
| Read customer summary                     | Yes                                  | No                                         | No                                         |
| Read product performance                  | Yes                                  | Yes                                        | No                                         |
| Read return analysis                      | Yes                                  | Yes                                        | No                                         |
| Read approved customer metrics            | Yes                                  | Yes                                        | Yes                                        |
| Read all customer regions                 | Yes, subject to database privileges  | Yes, subject to database privileges        | No                                         |
| Read authorized regional customer metrics | Yes                                  | Yes                                        | Yes                                        |
| Modify region-access mappings             | Yes                                  | No                                         | No                                         |
| Modify semantic views                     | Administrative privileges permitting | No                                         | No                                         |
| Access restricted customer fields         | According to granted privileges      | No access through the approved secure view | No access through the approved secure view |

**Important:** This matrix describes the intended and configured permissions for the project. It does not imply that the roles can modify every database object; actual capabilities depend on PostgreSQL ownership, grants, and applicable policies.

## 4. Database Roles

### 4.1 Semantic Admin

**Role:** `semantic_admin`

Purpose:

- Administer approved semantic-layer access.
- Read all approved semantic views.
- Read and manage the regional-access mapping table.
- Perform authorized administrative tasks.

The role was configured as `NOLOGIN`, `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE`, and `NOBYPASSRLS`.

A `NOLOGIN` role acts as a permission group. A database login must be explicitly granted membership or otherwise receive the required privileges to use its permissions.

### 4.2 Semantic Analyst

**Role:** `semantic_analyst`

Purpose:

- Analyze sales and revenue.
- Evaluate estimated product cost and gross profit.
- Review product performance and returns.
- Access approved customer metrics.

The analyst role has read access to the approved analytical views and selected customer-metric fields. It does not have direct access to the full customer summary through the configured grants.

### 4.3 Regional Manager

**Role:** `semantic_regional_manager`

Purpose:

- Analyze customer metrics for an authorized region.
- Review permitted revenue and estimated-profit measures.
- Access only the approved fields in the secure customer-metrics view.

Regional access is controlled by the region mapping table and row-level security policy.

The role is not granted access to the general order-line, sales, product-performance, or return-analysis views in the configured permissions.

## 5. Row-Level Security

### 5.1 Protected table

`semantic.secured_customer_metrics`

This table contains customer-level metrics and region information used to enforce regional restrictions.

### 5.2 Region mapping

`security.user_region_access` records the relationship between a database username and an authorized region.

| Column     | Purpose                                       |
| ---------- | --------------------------------------------- |
| `username` | Database login associated with the permission |
| `region`   | Region that the login is permitted to access  |

The mapping table is managed by the authorized administrator.

### 5.3 Authorization function

`security.is_region_authorized(TEXT)` checks whether the current database user is authorized for a given region.

The function supports the regional row-level security policy. Its execution permissions were restricted rather than left publicly executable.

### 5.4 RLS policies

Row-level security is enabled and forced on `semantic.secured_customer_metrics`.

| Policy                  | Intended behavior                                                    |
| ----------------------- | -------------------------------------------------------------------- |
| Administrator policy    | Allows authorized administrative access                              |
| Analyst policy          | Allows access to the customer metrics permitted by the analyst grant |
| Regional-manager policy | Restricts rows to the manager's authorized region                    |

The regional-manager policy checks region authorization through the security mapping and helper function.

**Security requirement:** Regional restrictions must be enforced in PostgreSQL, not merely by a dashboard filter. A user who connects directly to the database must not be able to retrieve unauthorized regions.

## 6. Field-Level Security

The approved secure customer-metrics view is:

`semantic.vw_customer_metrics_secure`

The view exposes only these fields:

| Field                    | Purpose                      |
| ------------------------ | ---------------------------- |
| `customer_id`            | Customer identifier          |
| `segment`                | Customer segment             |
| `region`                 | Customer region              |
| `order_count`            | Number of eligible orders    |
| `net_item_revenue`       | Revenue after item discounts |
| `estimated_gross_profit` | Estimated gross profit       |

The analyst and regional-manager roles receive access to the approved fields through the secure view.

The implementation also uses column-level grants on `semantic.secured_customer_metrics` to limit which columns these roles can select directly.

Restricted fields that are not included in the secure view should not be exposed through alternate views or grants.

## 7. Least-Privilege Principles

The security design follows these principles:

1. **Least privilege:** Give each role only the access needed for its responsibilities.
2. **Separation of duties:** Separate administrative permissions from ordinary analytical access.
3. **Database enforcement:** Enforce regional restrictions at the database level.
4. **Restricted field exposure:** Publish approved columns rather than exposing every field.
5. **Explicit grants:** Avoid unnecessary public privileges.
6. **Traceable access rules:** Keep role definitions, grants, mappings, and RLS policies in version-controlled SQL files.

## 8. Security Validation

The following security implementation and checks have been completed.

| Validation                                                     | Result                                                       |
| -------------------------------------------------------------- | ------------------------------------------------------------ |
| Security roles created                                         | Completed                                                    |
| Roles configured without superuser or RLS-bypass privileges    | Verified                                                     |
| Protected customer-metrics table created                       | Completed                                                    |
| RLS enabled and forced                                         | Completed                                                    |
| Regional authorization mapping created                         | Completed                                                    |
| Field-level grants configured                                  | Completed                                                    |
| Secure customer-metrics view created                           | Completed                                                    |
| Regional test login created                                    | Completed                                                    |
| Regional test login mapped to North                            | Completed                                                    |
| Regional test login returned only North-region customers       | Passed; 71 customer records returned                         |
| Direct-access denial to the unrestricted customer-summary view | Not yet independently verified under the regional test login |

The regional test was performed using the dedicated database login. Both `session_user` and `current_user` were confirmed as the test login, and the secure customer-metrics view returned 71 records from the North region.

The direct-access denial check remains a pending verification. A query executed under the administrator connection does not prove that the regional manager is denied access.

## 9. Recommended Final Security Tests

Perform the following tests using the actual regional test login.

### Test A — Authorized regional access

```sql
SELECT
    COUNT(*) AS customer_count,
    COUNT(DISTINCT region) AS region_count,
    MIN(region) AS region_name,
    MAX(region) AS region_name_max
FROM semantic.vw_customer_metrics_secure;
```

Expected for the current North-region test mapping:

- Customer count: `71`
- Distinct region count: `1`
- Both region-name results: `North`

### Test B — Attempted access to the unrestricted customer summary

```sql
SELECT COUNT(*)
FROM semantic.vw_customer_summary;
```

Expected under the regional test login: PostgreSQL should deny access because the role has not been granted permission to read this view.

### Test C — Direct access to the protected table

```sql
SELECT COUNT(*)
FROM semantic.secured_customer_metrics;
```

The role should be limited by its column-level grants and row-level policy. The exact result depends on the granted columns and active policies; test the query using the actual regional login.

### Test D — Unauthorized region

Verify that the regional login cannot retrieve customer rows from a region other than its assigned region through the secure access path.

Do not treat a dashboard filter as proof of database security.

## 10. Operational Notes

- Do not store database passwords in this document or commit them to version control.
- Keep connection credentials in environment variables and protect the `.env` file.
- Review role memberships and regional mappings when responsibilities change.
- Re-run the security tests after changing grants, views, policies, or mappings.
- Reconcile security behavior against the actual PostgreSQL grants and role memberships before deployment.
- Use separate, appropriately restricted database logins for administrators, analysts, and regional managers.

## 11. Conclusion

The project implements role-based database access, field-level restrictions, and row-level regional controls in PostgreSQL. The regional test login successfully returned only North-region customer metrics.

The remaining direct-access denial check must be completed before claiming that every unauthorized access path has been verified.
