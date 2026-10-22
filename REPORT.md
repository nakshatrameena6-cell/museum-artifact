# Final Project Report — Museum Artifact Explorer

**Repository:** Flask + SQLite "Museum Artifact Explorer"  
**Audience:** College DBMS Evaluator & Senior Python/SQLite Review Board  
**Status:** All Phases (1 through 6) Completed Successfully  

---

## 1. Executive Summary

The **Museum Artifact Explorer** application was upgraded and hardened into a production-grade relational DBMS demonstration platform. Legacy technical debt was eliminated, database schema integrity was enforced with `CHECK`, `NOT NULL`, and `UNIQUE` constraints, and advanced DBMS features were added—including Many-to-Many associations (`curators`, `exhibitions`, `exhibition_artifacts`), an `AFTER DELETE` audit logging trigger (`deleted_artifacts_log`), multi-column indexes, and a denormalized SQL view (`artifact_details`). Open-redirect and secret key configuration security issues were resolved, the automated test suite was expanded from 8 to 16 passing unit tests, and comprehensive SQL scripts and documentation artifacts were delivered.

---

## 2. Deliverables & Change Matrix

| # | Task / Change Description | Target File(s) | Status | Details / Rationale |
|---|---|---|---|---|
| 1 | Add `museum.db` to `.gitignore` and `git rm --cached museum.db` | `.gitignore`, Git index | **Done** | Untracked database binary from version control to prevent state collisions. |
| 2 | Delete redundant files (`package-lock.json`, `templates/details.html`, `static/style.css`) | `package-lock.json`, `templates/details.html`, `static/style.css` | **Done** | Verified zero dangling references; confirmed `base.html` uses `css/style.css`. |
| 3 | Clean README personal Windows path & remove "Antigravity IDE" | `README.md` | **Done** | Replaced personal path with portable `cd museum-artifact` and modernized tooling notes. |
| 4 | Sanitize `next` redirect in `toggle_favorite` | `app.py` | **Done** | Strictly validates `next.startswith('/') and not next.startswith('//')` to block open-redirect attacks. |
| 5 | Read `FLASK_DEBUG` from env & warn on fallback `SECRET_KEY` | `app.py` | **Done** | Reads `FLASK_DEBUG` (default off); warns on console if development secret key fallback is used. |
| 6 | Remove legacy `DROP TABLE` migration block | `database.py` | **Done** | Eradicated destructive drop-table logic; schema initialization is clean and idempotent. |
| 7 | Schema integrity constraints & duplicate handling in routes | `database.py`, `app.py` | **Done** | Enforced `NOT NULL` on FKs, `CHECK(discovery_year <= 2026)`, `CHECK(length(trim(name)) > 0)`, `UNIQUE(name, civilization_id)`, and caught `sqlite3.IntegrityError` in add/edit routes. |
| 8 | Assign distinct Unsplash URLs for sharing artifacts | `database.py` | **Done** | Gave "Chola Gold Coin" a unique high-resolution historical coin image URL distinct from the Roman Denarius. |
| 9 | Add `curators`, `exhibitions`, and `exhibition_artifacts` (M:N) | `database.py` | **Done** | Added 3 tables with foreign keys and cascading deletes; seeded 3 curators, 3 exhibitions, and 10 links. |
| 10 | Add database indexes | `database.py` | **Done** | Added `idx_artifacts_name` on `name` and `idx_artifacts_civ_cat` on `(civilization_id, category_id)`. |
| 11 | Add `artifact_details` SQL View and integrate in `_artifact_query` | `database.py`, `app.py` | **Done** | Created view joining artifacts, civilizations, and categories; updated `_artifact_query` to query the view. |
| 12 | Add `deleted_artifacts_log` and `AFTER DELETE` trigger | `database.py` | **Done** | Created table and trigger `trg_artifact_deleted` to log deleted artifact IDs, titles, and timestamps. |
| 13 | Exhibitions UI (`/exhibitions` & `/exhibitions/<id>`) | `templates/exhibitions.html`, `templates/exhibition_detail.html`, `templates/base.html`, `app.py` | **Done** | Added exhibition list and detail templates, navbar link, curator info, and curated artifact cards. |
| 14 | Create `queries.sql` with 14+ documented DBMS queries | `queries.sql` | **Done** | Covered INNER/LEFT JOINs, GROUP BY + HAVING, AVG/MIN/MAX, subqueries, EXISTS, view queries, M:N joins, and trigger audit demo. Verified on seeded DB. |
| 15 | Update README with schema, Mermaid ER diagram & Normalization | `README.md` | **Done** | Documented all 7 tables, audit table, view, trigger, indexes, Mermaid diagram, and 1NF/2NF/3NF breakdown. |
| 16 | Generate `docs/er_diagram.png` | `generate_er.py`, `docs/er_diagram.png` | **Done** | Generated high-resolution relational schema diagram matching final schema. |
| 17 | Comprehensive automated test suite in `test_app.py` | `test_app.py` | **Done** | Implemented 8 new unit tests (16 total) validating empty name, missing civ, duplicate names, open-redirect blocking, CHECK constraints, trigger logging, exhibition 200, and M:N cascades. |

---

## 3. Final Database Schema Overview

### Tables & Key Constraints

1. **`civilizations`**:
   - `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
   - `name`: `TEXT NOT NULL UNIQUE`
   - `region`: `TEXT`
   - `period`: `TEXT`
   - `description`: `TEXT`

2. **`categories`**:
   - `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
   - `name`: `TEXT NOT NULL UNIQUE`
   - `description`: `TEXT`

3. **`artifacts`**:
   - `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
   - `name`: `TEXT NOT NULL`
   - `description`: `TEXT NOT NULL`
   - `period`: `TEXT`
   - `discovery_location`: `TEXT`
   - `discovery_year`: `INTEGER`
   - `material`: `TEXT`
   - `image_url`: `TEXT`
   - `civilization_id`: `INTEGER NOT NULL`, `FOREIGN KEY -> civilizations(id)`
   - `category_id`: `INTEGER NOT NULL`, `FOREIGN KEY -> categories(id)`
   - `created_at`: `TEXT DEFAULT (datetime('now'))`
   - Constraints:
     - `CHECK (discovery_year IS NULL OR discovery_year <= 2026)`
     - `CHECK (length(trim(name)) > 0)`
     - `UNIQUE (name, civilization_id)`

4. **`favorites`**:
   - `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
   - `artifact_id`: `INTEGER NOT NULL UNIQUE`, `FOREIGN KEY -> artifacts(id) ON DELETE CASCADE`
   - `created_at`: `TEXT DEFAULT (datetime('now'))`

5. **`curators`**:
   - `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
   - `name`: `TEXT NOT NULL`
   - `email`: `TEXT NOT NULL UNIQUE`
   - `specialization`: `TEXT`

6. **`exhibitions`**:
   - `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
   - `title`: `TEXT NOT NULL UNIQUE`
   - `start_date`: `TEXT NOT NULL`
   - `end_date`: `TEXT NOT NULL`
   - `curator_id`: `INTEGER`, `FOREIGN KEY -> curators(id) ON DELETE SET NULL`
   - Constraints:
     - `CHECK (end_date >= start_date)`

7. **`exhibition_artifacts`** (Many-to-Many Association):
   - `exhibition_id`: `INTEGER NOT NULL`, `FOREIGN KEY -> exhibitions(id) ON DELETE CASCADE`
   - `artifact_id`: `INTEGER NOT NULL`, `FOREIGN KEY -> artifacts(id) ON DELETE CASCADE`
   - `PRIMARY KEY (exhibition_id, artifact_id)`

8. **`deleted_artifacts_log`** (Audit Trail):
   - `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
   - `artifact_id`: `INTEGER NOT NULL`
   - `name`: `TEXT NOT NULL`
   - `deleted_at`: `TEXT DEFAULT (datetime('now'))`

### View
- **`artifact_details`**:
  ```sql
  CREATE VIEW IF NOT EXISTS artifact_details AS
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

### Indexes
- `idx_artifacts_name`: `ON artifacts(name)`
- `idx_artifacts_civ_cat`: `ON artifacts(civilization_id, category_id)`

### Trigger
- **`trg_artifact_deleted`**:
  ```sql
  CREATE TRIGGER IF NOT EXISTS trg_artifact_deleted
  AFTER DELETE ON artifacts
  FOR EACH ROW
  BEGIN
      INSERT INTO deleted_artifacts_log (artifact_id, name, deleted_at)
      VALUES (OLD.id, OLD.name, datetime('now'));
  END;
  ```

---

## 4. Test Results

Execution command: `python -m unittest test_app`

```text
................
----------------------------------------------------------------------
Ran 16 tests in 0.619s

OK
[WARNING] SECRET_KEY not found in environment; using insecure development fallback!
[DB] Database ready: tmpebw_v1w6.db
[DB] Database ready: tmp3k9bncms.db
[DB] Database ready: tmp3k9bncms.db
[DB] Database ready: tmplf18dgth.db
[DB] Database ready: tmpz5j3b4yz.db
[DB] Database ready: tmp6anv4oyp.db
[DB] Database ready: tmpr31b4c5x.db
[DB] Database ready: tmpdpf_0ust.db
[DB] Database ready: tmpwj0nwqvl.db
[DB] Database ready: tmpkuk98ndn.db
[DB] Database ready: tmpmanlsweb.db
[DB] Database ready: tmp1ekcy4ck.db
[DB] Database ready: tmpgyz4rr1i.db
[DB] Database ready: tmp5vtg0v1o.db
[DB] Database ready: tmpdpwd164r.db
[DB] Database ready: tmp2wbtgpkj.db
[DB] Database ready: tmpdzpxqngp.db
```

### Breakdown of Test Suite:
- `test_01_schema_and_tables`: Validates core schema tables exist.
- `test_02_sample_data_and_idempotence`: Validates seed data and idempotent re-execution.
- `test_03_homepage`: Validates HTTP 200 and spotlight elements.
- `test_04_artifacts_listing_and_filtering`: Tests catalog search, query params, and civilization filters.
- `test_05_artifact_detail_and_404`: Validates detail page rendering and 404 handler.
- `test_06_add_edit_delete_crud`: Validates complete artifact lifecycle.
- `test_07_favorites_and_cascade_delete`: Validates favorite toggles and cascade deletion.
- `test_08_civilizations_and_categories_pages`: Validates overview routes.
- `test_09_empty_name_validation`: Validates whitespace-only and empty name rejection.
- `test_10_missing_civilization_validation`: Validates missing civilization selection rejection.
- `test_11_duplicate_name_rejection`: Validates duplicate `(name, civilization_id)` flash handling.
- `test_12_open_redirect_blocked`: Validates external and protocol-relative redirect sanitization.
- `test_13_check_constraint_future_year`: Validates database-level `CHECK` constraints.
- `test_14_trigger_logs_on_delete`: Validates `AFTER DELETE` trigger inserting into `deleted_artifacts_log`.
- `test_15_exhibition_pages`: Validates `/exhibitions` and `/exhibitions/<id>` HTTP 200 responses.
- `test_16_many_to_many_cascade`: Validates cascading deletes on junction table `exhibition_artifacts`.

---

## 5. Security Fixes & Remaining Risks

### Security Hardening Measures Implemented:
1. **Open-Redirect Mitigation**:
   - In `app.py:toggle_favorite`, incoming `next` parameters were previously passed unfiltered to `redirect()`. Attackers could exploit this to redirect authenticated users to phishing domains (e.g. `next=https://malicious.com` or `next=//malicious.com`).
   - Fix: Added strict URL validation requiring `next.startswith("/") and not next.startswith("//")`, safely defaulting to the artifact's own detail route if validation fails.
2. **Environment-Driven Secrets & Warning**:
   - `app.secret_key` now checks for `SECRET_KEY` in `os.environ` and emits an explicit runtime warning on console when the hardcoded development fallback is used.
3. **Safe Debug Toggle**:
   - Debug mode is now parsed from `FLASK_DEBUG` (defaulting to off/False) preventing accidental remote code execution (RCE) vulnerabilities in production deployments.
4. **Parameter Injection Prevention**:
   - All SQL statements use SQLite parameter bindings (`?`) rather than string concatenation or formatting, guarding against SQL injection.
5. **Database Constraint Defenses**:
   - Hardened schema against corrupt data insertion (e.g., negative/excessive dates, empty strings, missing foreign key relations).

### Remaining Risks & Recommended Enhancements:
- **Authentication & Authorization**: Currently, artifact editing, deletion, and favoriting are open to all visitors. For production, add role-based access control (RBAC) with hashed password authentication (e.g., `Flask-Login` + `bcrypt`).
- **CSRF Protection**: Forms currently rely on standard POST handlers. In production, integrate `Flask-WTF` with CSRF tokens on all state-altering forms.
- **Image URL SSRF/Validation**: Image URLs are user-provided. If an internal image proxy or fetcher is added in the future, enforce an allowed host whitelist to prevent Server-Side Request Forgery (SSRF).

---

## 6. How to Run the Project

Execute the following commands in PowerShell from the repository root:

```powershell
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Initialize and seed SQLite database
python database.py

# 3. Run automated test suite
python -m unittest test_app

# 4. Start the Flask web application
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## 7. Suggested 5-Minute Evaluator Demo Script

- **Minute 1: Homepage & Modern Theme (`/`)**
  - Point out the warm museum theme, dynamic statistics counters (artifacts, civilizations, categories), and the randomized "Artifact of the Day".
- **Minute 2: Search, Filters & View Optimization (`/artifacts`)**
  - Search for "Denarius" or "Amphora" to demonstrate index-accelerated LIKE queries.
  - Filter by Civilization (Egyptian) and Category (Pottery), pointing out how `artifact_details` view provides seamless joined metadata.
- **Minute 3: Relational Constraints & Duplicate Handling (`/artifact/add`)**
  - Attempt to add an artifact with an empty name or year 2099 to demonstrate client/server and `CHECK` constraint enforcement.
  - Attempt to add "Mohenjo-daro Dancing Girl" under "Indus Valley" to show the friendly flash warning triggered by `UNIQUE(name, civilization_id)`.
- **Minute 4: Curated Exhibitions & Many-to-Many M:N Association (`/exhibitions`)**
  - Click the **Exhibitions** nav link to showcase the new M:N feature.
  - Open "Echoes of the Indus" or "Treasures of the Nile" to show curator credentials and all linked artifacts displayed via `exhibition_artifacts`.
- **Minute 5: Trigger & Cascading Delete Verification**
  - Delete a test artifact or unfavorite an item.
  - Run `python -c "import database; print(database.get_db().execute('SELECT * FROM deleted_artifacts_log').fetchall())"` in terminal to show the `AFTER DELETE` trigger audit entry.
  - Run `python -m unittest test_app` to show all 16 tests passing cleanly.

---

## 8. Known Limitations & Future Work

- **Pagination**: The collection currently renders all filtered results on a single page. Implementing cursor-based or offset pagination will support collections scaling past 10,000 artifacts.
- **Direct File Uploads**: Images currently use remote web URLs. Implementing local multipart file uploads using `werkzeug.utils.secure_filename` with cloud/local object storage would allow offline asset management.
- **Curator Admin Interface**: Add an administrative dashboard for curators to create new exhibitions, adjust exhibition date schedules, and drag-and-drop artifacts into exhibitions.
