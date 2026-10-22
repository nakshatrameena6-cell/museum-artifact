# Final Project Report — Museum Artifact Explorer

**Repository:** Flask + PostgreSQL on Supabase "Museum Artifact Explorer"  
**Audience:** College DBMS Evaluator & Senior Python/Database Review Board  
**Status:** All Migration and Hardening Phases Completed Successfully  

---

## 1. Executive Summary

The **Museum Artifact Explorer** application was successfully migrated from local SQLite to a cloud-hosted **PostgreSQL database on Supabase** using plain SQL via `psycopg2-binary` (without Supabase SDK dependencies). The platform features enterprise relational DBMS capabilities: primary keys defined with `GENERATED ALWAYS AS IDENTITY`, temporal tracking with `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` and `DATE` data types, Many-to-Many associations (`curators`, `exhibitions`, `exhibition_artifacts`), a procedural PL/pgSQL trigger function (`log_deleted_artifact()`) attached to an `AFTER DELETE` trigger for audit logging, performance indexes, and a denormalized SQL view (`artifact_details`).

To protect cloud data from unauthorized access via Supabase's public PostgREST API, **Row Level Security (RLS)** was enabled across every table. The application layer handles PostgreSQL-specific errors (`UniqueViolation`, `CheckViolation`) with immediate transaction rollbacks. Test isolation is guaranteed by generating dynamic test schemas per test run, ensuring tests never touch production data.

---

## 2. Deliverables & Change Matrix

| # | Task / Change Description | Target File(s) | Status | Details / Rationale |
|---|---|---|---|---|
| 1 | Database Connection via `psycopg2` & `.env` | `database.py`, `.env` | **Done** | Implemented `get_db(schema)` connecting with `DATABASE_URL` and `sslmode=require`. Wrapped with parameter translation (`?` -> `%s`) and `psycopg2.extras.DictCursor`. |
| 2 | PostgreSQL Schema Conversion | `database.py` | **Done** | Converted schema to `GENERATED ALWAYS AS IDENTITY`, `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`, `DATE` for exhibitions, `CREATE OR REPLACE VIEW`, and idempotent `ON CONFLICT DO NOTHING` seeds. Removed `executescript` and `PRAGMA`. |
| 3 | PL/pgSQL Audit Trigger | `database.py` | **Done** | Created procedural language function `log_deleted_artifact()` returning `TRIGGER` and attached `trg_artifact_deleted` to log deleted artifacts to `deleted_artifacts_log`. |
| 4 | Row Level Security (RLS) Hardening | `database.py` | **Done** | Executed `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` on all 8 tables to block unauthorized exposure through Supabase's PostgREST API while allowing connection as `postgres`. |
| 5 | Application Route Updates (`ILIKE` & Error Handling) | `app.py` | **Done** | Replaced search with PostgreSQL `ILIKE`; caught psycopg2 `UniqueViolation` and `CheckViolation` with `db.rollback()` and user flash messages. |
| 6 | Dynamic Schema Test Suite Isolation | `test_app.py` | **Done** | Updated 16 unit tests to create a temporary schema (`test_museum_<uuid>`), set PostgreSQL `search_path`, run all tests in isolation, and clean up with `DROP SCHEMA CASCADE`. |
| 7 | PostgreSQL Queries Migration | `queries.sql` | **Done** | Converted queries to PostgreSQL standard, replacing SQLite `GROUP_CONCAT` with `STRING_AGG(DISTINCT a.material, ', ')` and adding dynamic FK subqueries. |
| 8 | Environment Template & Requirements | `.env.example`, `requirements.txt` | **Done** | Created `.env.example` with placeholder credentials; added `psycopg2-binary` and `python-dotenv` to `requirements.txt`. |
| 9 | Documentation & PDF Report Regeneration | `README.md`, `REPORT.md`, `export_report_pdf.py`, `REPORT.pdf` | **Done** | Updated documentation with Supabase project setup, connection string instructions, RLS security notes, and recompiled the two-page summary PDF. |

---

## 3. Final PostgreSQL Database Schema Overview

### Tables & Key Constraints

1. **`civilizations`**:
   - `id`: `INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY`
   - `name`: `TEXT NOT NULL UNIQUE`
   - `region`: `TEXT`
   - `period`: `TEXT`
   - `description`: `TEXT`

2. **`categories`**:
   - `id`: `INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY`
   - `name`: `TEXT NOT NULL UNIQUE`
   - `description`: `TEXT`

3. **`artifacts`**:
   - `id`: `INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY`
   - `name`: `TEXT NOT NULL`
   - `description`: `TEXT NOT NULL`
   - `period`: `TEXT`
   - `discovery_location`: `TEXT`
   - `discovery_year`: `INT`
   - `material`: `TEXT`
   - `image_url`: `TEXT`
   - `civilization_id`: `INT NOT NULL REFERENCES civilizations(id)`
   - `category_id`: `INT NOT NULL REFERENCES categories(id)`
   - `created_at`: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
   - Constraints:
     - `CHECK (discovery_year IS NULL OR discovery_year <= 2026)`
     - `CHECK (length(trim(name)) > 0)`
     - `UNIQUE (name, civilization_id)`

4. **`favorites`**:
   - `id`: `INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY`
   - `artifact_id`: `INT NOT NULL UNIQUE REFERENCES artifacts(id) ON DELETE CASCADE`
   - `created_at`: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

5. **`curators`**:
   - `id`: `INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY`
   - `name`: `TEXT NOT NULL`
   - `email`: `TEXT NOT NULL UNIQUE`
   - `specialization`: `TEXT`

6. **`exhibitions`**:
   - `id`: `INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY`
   - `title`: `TEXT NOT NULL UNIQUE`
   - `start_date`: `DATE NOT NULL`
   - `end_date`: `DATE NOT NULL`
   - `curator_id`: `INT REFERENCES curators(id) ON DELETE SET NULL`
   - Constraints:
     - `CHECK (end_date >= start_date)`

7. **`exhibition_artifacts`** (Many-to-Many Association):
   - `exhibition_id`: `INT NOT NULL REFERENCES exhibitions(id) ON DELETE CASCADE`
   - `artifact_id`: `INT NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE`
   - `PRIMARY KEY (exhibition_id, artifact_id)`

8. **`deleted_artifacts_log`** (Audit Trail):
   - `id`: `INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY`
   - `artifact_id`: `INT NOT NULL`
   - `name`: `TEXT NOT NULL`
   - `deleted_at`: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

### View: `artifact_details`
```sql
CREATE OR REPLACE VIEW artifact_details AS
SELECT
    a.id, a.name, a.description, a.period, a.discovery_location,
    a.discovery_year, a.material, a.image_url, a.created_at,
    a.civilization_id, a.category_id,
    c.name AS civilization,
    c.region AS region,
    c.period AS civ_period,
    cat.name AS category
FROM artifacts a
JOIN civilizations c ON a.civilization_id = c.id
JOIN categories cat ON a.category_id = cat.id;
```

### Trigger Function & Trigger: `trg_artifact_deleted`
```sql
CREATE OR REPLACE FUNCTION log_deleted_artifact()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO deleted_artifacts_log (artifact_id, name, deleted_at)
    VALUES (OLD.id, OLD.name, CURRENT_TIMESTAMP);
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_artifact_deleted
AFTER DELETE ON artifacts
FOR EACH ROW
EXECUTE FUNCTION log_deleted_artifact();
```

### Row Level Security (RLS)
```sql
ALTER TABLE civilizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE curators ENABLE ROW LEVEL SECURITY;
ALTER TABLE exhibitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE exhibition_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE deleted_artifacts_log ENABLE ROW LEVEL SECURITY;
```

---

## 4. Test Results & Isolation Architecture

Execution command: `python -m unittest test_app.py`

### Test Suite Architecture:
- `setUpClass`: Connects to Supabase, generates a randomized schema `test_museum_<uuid>`, sets `database.SCHEMA` and `search_path`, and initializes tables/triggers in isolation.
- `tearDownClass`: Drops the temporary schema using `DROP SCHEMA IF EXISTS "<test_schema>" CASCADE`, ensuring zero residue.
- `test_01_schema_and_tables`: Validates all 8 tables in `information_schema.tables` under the test schema.
- `test_02_sample_data_and_idempotence`: Validates seed data and idempotent re-initialization.
- `test_03_homepage`: Validates HTTP 200 response and dynamic spotlight artifacts.
- `test_04_artifacts_listing_and_filtering`: Tests PostgreSQL `ILIKE` search and foreign key filters.
- `test_05_artifact_detail_and_404`: Validates single record retrieval and HTTP 404 response.
- `test_06_add_edit_delete_crud`: Validates complete artifact lifecycle.
- `test_07_favorites_and_cascade_delete`: Validates favorite toggles and foreign key cascading.
- `test_08_civilizations_and_categories_pages`: Validates aggregate count views.
- `test_09_empty_name_validation`: Validates whitespace rejection.
- `test_10_missing_civilization_validation`: Validates required foreign key dropdown checks.
- `test_11_duplicate_name_rejection`: Validates psycopg2 `UniqueViolation` handling.
- `test_12_open_redirect_blocked`: Validates strict redirect sanitization.
- `test_13_check_constraint_future_year`: Validates database `CHECK` constraints (`CheckViolation`).
- `test_14_trigger_logs_on_delete`: Validates PL/pgSQL `AFTER DELETE` trigger audit logging.
- `test_15_exhibition_pages`: Validates exhibition catalog and detail views.
- `test_16_many_to_many_cascade`: Validates cascading deletes on junction table `exhibition_artifacts`.

---

## 5. Security Architecture

1. **Row Level Security (RLS)**:
   - When using Supabase, public clients could potentially query tables via the PostgREST Data API (`https://<project-ref>.supabase.co/rest/v1/`).
   - Enabling RLS without permissive public policies ensures that public anonymous requests receive zero data.
   - The Flask app connects via the administrative `postgres` role, which naturally bypasses RLS and maintains full CRUD operations.
2. **Encrypted Wire Protocol (`sslmode=require`)**:
   - All client connections to Supabase enforce SSL transport encryption, preventing eavesdropping on queries or parameters.
3. **Transactional Integrity & Rollback**:
   - Any database constraint violation (`UniqueViolation`, `CheckViolation`) triggers an immediate `db.rollback()` to keep the connection in a clean state.
4. **Credential Isolation**:
   - The production connection string is stored strictly in `.env` (ignored by Git) and exposed as a template in `.env.example`.

---

## 6. How to Run the Project

```powershell
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Configure .env with Supabase connection string
Copy-Item .env.example .env
# Edit .env to add your DATABASE_URL

# 3. Initialize and seed PostgreSQL database on Supabase
python database.py

# 4. Run automated test suite in isolated schema
python -m unittest test_app.py

# 5. Start the Flask web application
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.
