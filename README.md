# Museum Artifact Explorer

An interactive, responsive full-stack web application designed for exploring historical museum artifacts across ancient civilizations, periods, and classifications. Built with **Python Flask**, **PostgreSQL** hosted on **Supabase** (connected via **psycopg2** plain SQL), and modern **Vanilla HTML5/CSS3/JavaScript**.

---

## 1. Project Overview & Objectives

**Museum Artifact Explorer** is developed for a College Database Management System (DBMS) project. The project demonstrates:
- Relational database modeling with **PostgreSQL** hosted on **Supabase**.
- Primary keys with `GENERATED ALWAYS AS IDENTITY`, timestamps with `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`, and `DATE` types for events.
- Integrity constraints: Primary Keys, Foreign Keys, Unique constraints, Cascading Deletes (`ON DELETE CASCADE`), and Check constraints.
- PL/pgSQL procedural trigger function `log_deleted_artifact()` auditing artifact deletions into `deleted_artifacts_log`.
- Denormalized SQL View `artifact_details` providing pre-joined metadata.
- Row Level Security (RLS) enabled on every table to protect data from public exposure via Supabase Data APIs.
- Parameterized SQL queries (`%s` placeholders via psycopg2 wrapper) to prevent SQL injection.
- Case-insensitive search using PostgreSQL `ILIKE`.
- Multi-table `JOIN` operations across artifacts, civilizations, categories, exhibitions, and favorites.
- Full CRUD functionality (Create, Read, Update, Delete) on artifacts with psycopg2 `UniqueViolation` and `CheckViolation` error handling and transaction rollback.
- Automated testing with schema-level isolation (dynamic temporary test schema per test run, never modifying real data).
- An aesthetically refined museum theme (warm beige, cream, dark brown, and muted gold palette).

---

## 2. Technologies Used

- **Backend**: Python 3, Flask
- **Database**: PostgreSQL 15+ (Hosted on Supabase)
- **Database Driver**: `psycopg2-binary` (plain SQL, parameter conversion, DictCursor row support, no Supabase SDK)
- **Environment Management**: `python-dotenv`
- **Security**: Supabase Row Level Security (RLS) enabled on all tables; Open-redirect sanitization; Secret key configuration
- **Templating**: Flask Jinja2
- **Frontend**: Semantic HTML5, Vanilla CSS3 (custom CSS design system with Google Fonts *Playfair Display* & *Inter*), Modern Vanilla JavaScript (ES6+)
- **Testing**: Python `unittest` with dynamic PostgreSQL test schemas (`CREATE SCHEMA`, `search_path`, `DROP SCHEMA CASCADE`)

---

## 3. Project Structure

```text
museum-artifact/
├── app.py                     # Flask application entry point and route handlers
├── database.py                # Database initialization, schema creation, triggers, and seeding
├── test_app.py                # Comprehensive automated test suite
├── queries.sql                # 14+ documented SQL queries (JOINs, Aggregates, M:N, Triggers)
├── generate_er.py             # Script generating docs/er_diagram.png via matplotlib
├── requirements.txt           # Python package dependencies
├── README.md                  # Comprehensive documentation and project guide
├── REPORT.md                  # Detailed project deliverables report
├── .gitignore                 # Files excluded from version control (includes museum.db)
├── docs/
│   └── er_diagram.png         # High-resolution Entity-Relationship diagram
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Base layout with navbar, footer, flash alerts
│   ├── index.html             # Homepage: Hero, Artifact of Day, Highlights, Stats
│   ├── artifacts.html         # Artifact catalog with search, filter, and card grid
│   ├── artifact_detail.html   # Detailed artifact view with full provenance and actions
│   ├── add_artifact.html      # Create new artifact form with validation
│   ├── edit_artifact.html     # Edit artifact form with prefilled values
│   ├── civilizations.html     # List of civilizations with artifact counts
│   ├── categories.html        # List of categories with thematic icons & counts
│   ├── exhibitions.html       # Exhibitions list with dates, curators, and artifact counts
│   ├── exhibition_detail.html # Exhibition detail with curator and curated artifact cards
│   ├── favorites.html         # User favorites collection
│   └── 404.html               # Custom museum-themed 404/500 error page
└── static/
    ├── css/
    │   └── style.css          # Museum palette, typography, responsive grid
    ├── js/
    │   └── script.js          # Mobile navbar, auto-dismiss alerts, image fallbacks
    └── images/                # Local asset storage
```

---

## 4. Database Schema & Design

The PostgreSQL relational database enforces data integrity through **7 core tables, 1 audit table, 1 view, 1 trigger function, 1 trigger, 2 performance indexes, and Row Level Security (RLS) on all tables**:

### Table 1: `civilizations`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INT | GENERATED ALWAYS AS IDENTITY PRIMARY KEY | Unique civilization identifier |
| `name` | TEXT | NOT NULL, UNIQUE | Civilization name (e.g., Indus Valley, Egyptian) |
| `region` | TEXT | | Geographical origin region |
| `period` | TEXT | | Epoch or historical date span |
| `description` | TEXT | | Cultural and historical summary |

### Table 2: `categories`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INT | GENERATED ALWAYS AS IDENTITY PRIMARY KEY | Unique category identifier |
| `name` | TEXT | NOT NULL, UNIQUE | Category title (e.g., Pottery, Sculpture, Coins) |
| `description` | TEXT | | Functional/material description |

### Table 3: `artifacts`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INT | GENERATED ALWAYS AS IDENTITY PRIMARY KEY | Unique artifact identifier |
| `name` | TEXT | NOT NULL, CHECK(length(trim(name)) > 0) | Artifact title |
| `description` | TEXT | NOT NULL | Detailed background & provenance |
| `period` | TEXT | | Historical period or dynasty |
| `discovery_location`| TEXT | | Excavation / discovery site |
| `discovery_year` | INT | CHECK(discovery_year IS NULL OR discovery_year <= 2026) | Excavation year (BCE supported via negative values) |
| `material` | TEXT | | Material composition (Bronze, Gold, etc.) |
| `image_url` | TEXT | | Public image link or local path |
| `civilization_id` | INT | NOT NULL, REFERENCES `civilizations(id)` | Associated civilization foreign key |
| `category_id` | INT | NOT NULL, REFERENCES `categories(id)` | Associated category foreign key |
| `created_at` | TIMESTAMP | DEFAULT `CURRENT_TIMESTAMP` | Timestamp of database addition |
| **Composite** | UNIQUE | `UNIQUE(name, civilization_id)` | Prevents duplicate artifact titles within a civilization |

### Table 4: `favorites`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INT | GENERATED ALWAYS AS IDENTITY PRIMARY KEY | Unique favorite identifier |
| `artifact_id` | INT | NOT NULL, UNIQUE, REFERENCES `artifacts(id)` ON DELETE CASCADE | Reference to favorited artifact |
| `created_at` | TIMESTAMP | DEFAULT `CURRENT_TIMESTAMP` | Timestamp when added to favorites |

### Table 5: `curators`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INT | GENERATED ALWAYS AS IDENTITY PRIMARY KEY | Unique curator identifier |
| `name` | TEXT | NOT NULL | Curator's full name |
| `email` | TEXT | NOT NULL, UNIQUE | Contact email address |
| `specialization` | TEXT | | Field of historical / archaeological expertise |

### Table 6: `exhibitions`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INT | GENERATED ALWAYS AS IDENTITY PRIMARY KEY | Unique exhibition identifier |
| `title` | TEXT | NOT NULL, UNIQUE | Exhibition title |
| `start_date` | DATE | NOT NULL | Opening date |
| `end_date` | DATE | NOT NULL, CHECK(end_date >= start_date) | Concluding date (must be >= start date) |
| `curator_id` | INT | REFERENCES `curators(id)` ON DELETE SET NULL | Curator in charge of the exhibition |

### Table 7: `exhibition_artifacts` (Many-to-Many M:N Association)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `exhibition_id` | INT | NOT NULL, REFERENCES `exhibitions(id)` ON DELETE CASCADE | Target exhibition |
| `artifact_id` | INT | NOT NULL, REFERENCES `artifacts(id)` ON DELETE CASCADE | Associated artifact |
| **Primary Key** | Composite | `PRIMARY KEY (exhibition_id, artifact_id)` | Unique exhibition-to-artifact mapping |

### Table 8: `deleted_artifacts_log` (Audit Trail)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INT | GENERATED ALWAYS AS IDENTITY PRIMARY KEY | Unique audit log ID |
| `artifact_id` | INT | NOT NULL | ID of deleted artifact |
| `name` | TEXT | NOT NULL | Title of deleted artifact |
| `deleted_at` | TIMESTAMP | DEFAULT `CURRENT_TIMESTAMP` | Deletion timestamp |

### View: `artifact_details`
Denormalized SQL View (`CREATE OR REPLACE VIEW artifact_details`) joining `artifacts`, `civilizations`, and `categories` to provide pre-joined metadata (`civilization`, `region`, `civ_period`, `category`) without redundant join syntax in queries.

### Trigger Function & Trigger: `trg_artifact_deleted`
PL/pgSQL trigger function `log_deleted_artifact()` returning `TRIGGER`. Fired by `CREATE TRIGGER trg_artifact_deleted AFTER DELETE ON artifacts FOR EACH ROW EXECUTE FUNCTION log_deleted_artifact()`. Automatically logs the deleted artifact's ID, title, and timestamp into `deleted_artifacts_log`.

### Security: Row Level Security (RLS)
Every table has Row Level Security enabled (`ALTER TABLE <table> ENABLE ROW LEVEL SECURITY`). This prevents public exposure of data via Supabase's auto-generated PostgREST APIs, while allowing our Flask application to read and write freely by connecting with the administrative `postgres` role.

### Indexes:
- `idx_artifacts_name`: Index on `artifacts(name)` for optimized search operations.
- `idx_artifacts_civ_cat`: Composite index on `artifacts(civilization_id, category_id)` for dual-filter queries.

---

## 5. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    CIVILIZATIONS ||--o{ ARTIFACTS : "originates (1:N)"
    CATEGORIES ||--o{ ARTIFACTS : "classifies (1:N)"
    ARTIFACTS ||--o| FAVORITES : "bookmarked as (1:1)"
    CURATORS ||--o{ EXHIBITIONS : "curates (1:N)"
    EXHIBITIONS ||--o{ EXHIBITION_ARTIFACTS : "contains (1:N)"
    ARTIFACTS ||--o{ EXHIBITION_ARTIFACTS : "displayed in (1:N)"
    ARTIFACTS ||--o{ DELETED_ARTIFACTS_LOG : "audited by trigger"

    CIVILIZATIONS {
        INTEGER id PK
        TEXT name UK
        TEXT region
        TEXT period
        TEXT description
    }

    CATEGORIES {
        INTEGER id PK
        TEXT name UK
        TEXT description
    }

    ARTIFACTS {
        INTEGER id PK
        TEXT name "REQ, CHECK"
        TEXT description "REQ"
        TEXT period
        TEXT discovery_location
        INTEGER discovery_year "CHECK <= 2026"
        TEXT material
        TEXT image_url
        INTEGER civilization_id FK "NOT NULL"
        INTEGER category_id FK "NOT NULL"
        TEXT created_at
    }

    FAVORITES {
        INTEGER id PK
        INTEGER artifact_id FK, UK "ON DELETE CASCADE"
        TEXT created_at
    }

    CURATORS {
        INTEGER id PK
        TEXT name "REQ"
        TEXT email UK "REQ"
        TEXT specialization
    }

    EXHIBITIONS {
        INTEGER id PK
        TEXT title UK "REQ"
        TEXT start_date "REQ"
        TEXT end_date "REQ, CHECK >= start_date"
        INTEGER curator_id FK "ON DELETE SET NULL"
    }

    EXHIBITION_ARTIFACTS {
        INTEGER exhibition_id PK, FK "ON DELETE CASCADE"
        INTEGER artifact_id PK, FK "ON DELETE CASCADE"
    }

    DELETED_ARTIFACTS_LOG {
        INTEGER id PK
        INTEGER artifact_id
        TEXT name
        TEXT deleted_at
    }
```

A standalone high-resolution diagram is available at [`docs/er_diagram.png`](file:///c:/Users/AIML%2027/OneDrive/文档/museum-artifact/docs/er_diagram.png).

---

## 6. Database Normalization (1NF / 2NF / 3NF)

The database schema is rigorously structured according to relational normalization principles:

1. **First Normal Form (1NF)**:
   - Every column contains atomic (indivisible) values.
   - Repeating groups and array lists within single fields (e.g., storing comma-separated artifact lists in exhibitions) are strictly prohibited.
   - Every table possesses an unambiguous Primary Key (`id` or composite `(exhibition_id, artifact_id)`).

2. **Second Normal Form (2NF)**:
   - The schema satisfies 1NF.
   - All non-key attributes are fully functionally dependent on the entire primary key.
   - In `exhibition_artifacts`, the junction table only stores the composite foreign keys `(exhibition_id, artifact_id)`. Specific exhibition metadata (e.g., dates) resides exclusively in `exhibitions`, eliminating partial key dependencies.

3. **Third Normal Form (3NF)**:
   - The schema satisfies 2NF.
   - Non-key attributes are non-transitively dependent on primary keys (no attribute depends on another non-key attribute).
   - Civilization regions and periods are stored in `civilizations`, not duplicated across each artifact record in `artifacts`.
   - Curator contact information and specializations are stored in `curators`, referenced by foreign key in `exhibitions`.

| Table | Normal Form | Key Design Rationale |
|---|---|---|
| `civilizations` | 3NF | Eliminates transitive dependencies between civilization name, region, and epoch. |
| `categories` | 3NF | Isolates artifact classification taxonomy from physical artifacts. |
| `artifacts` | 3NF | Core entity with atomic attributes; references civilizations and categories via non-null FKs. |
| `favorites` | 3NF | 1:1 user bookmark mapping with cascading deletion integrity. |
| `curators` | 3NF | Isolates staff profiles from exhibition dates and venues. |
| `exhibitions` | 3NF | Encapsulates temporal exhibition events; links to curator via foreign key. |
| `exhibition_artifacts` | 3NF | Pure junction entity modeling the M:N relationship between exhibitions and artifacts. |
| `deleted_artifacts_log` | 1NF/Audit | Append-only historical log populated by database trigger upon artifact deletion. |

---

## 6. Installation & Execution Guide (Windows / Linux / macOS)

### Step 1: Open Terminal in Project Directory
Navigate to the repository folder:
```powershell
cd museum-artifact
```

### Step 2: Supabase Project Setup & Connection String
1. Sign in to [Supabase](https://supabase.com/) and create a new project (e.g., `museum-artifact`).
2. Note your database password chosen during project creation.
3. In your Supabase Project Dashboard, navigate to:
   **Project Settings** (gear icon) > **Database** > **Connection string**.
4. Select the **URI** tab (or **Connection pooler** / **Session** mode on port `5432` or `6543`).
5. Copy the connection URI:
   ```text
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```
   > **Note**: Ensure `sslmode=require` is enabled and any special characters in `[YOUR-PASSWORD]` are URL-encoded (e.g., `@` as `%40`).

### Step 3: Configure Environment Variables (.env)
Create your local `.env` file from the provided `.env.example`:
```powershell
Copy-Item .env.example .env
```
Open `.env` and fill in your connection string and security key:
```env
DATABASE_URL=postgresql://postgres.YOUR_PROJECT_REF:YOUR_PASSWORD@aws-0-YOUR_REGION.pooler.supabase.com:5432/postgres
SECRET_KEY=replace-me
FLASK_DEBUG=0
```
> **Security Reminder**: The `.env` file contains sensitive credentials and is strictly excluded via `.gitignore`. Never commit `.env` to GitHub.

### Step 4: Verify Environment & Connectivity (check_env.py)
Run the diagnostic check to verify that `.env` is properly positioned and that Supabase is reachable (secrets are masked):
```powershell
python check_env.py
```

### Step 5: Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> **Note on PowerShell Execution Policy**: If PowerShell restricts script activation, run:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\.venv\Scripts\Activate.ps1
> ```

### Step 6: Install Required Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 7: Initialize Database & Seed Data
Run the database initialization script:
```powershell
python database.py
```
This connects to Supabase, creates all 8 tables with `GENERATED ALWAYS AS IDENTITY` primary keys, the `artifact_details` view, the `log_deleted_artifact()` trigger function and trigger, enables Row Level Security (RLS) on all tables, and idempotently seeds civilizations, categories, artifacts, curators, exhibitions, and junction links using `ON CONFLICT DO NOTHING`.

### Step 8: Run Automated Tests
Execute the comprehensive test suite:
```powershell
python -m unittest test_app.py
```
> **Test Isolation**: The test suite dynamically generates an isolated temporary schema (e.g., `test_museum_<uuid>`), sets the PostgreSQL `search_path`, validates all 16 test cases without touching production data, and cleans up with `DROP SCHEMA CASCADE` upon completion.

### Step 9: Start the Flask Application
```powershell
python app.py
```

### Step 10: Access the Application
Open your web browser and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 7. Example SQL Queries (DBMS College Requirements)

Here are the primary SQL statements executed within the application:

### 1. Multi-Table JOIN with LEFT JOIN for Favorites
```sql
SELECT
    a.id, a.name, a.description, a.period, a.material, a.image_url,
    c.name AS civilization,
    c.region AS region,
    cat.name AS category,
    CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END AS is_favorite
FROM artifacts a
JOIN civilizations c ON a.civilization_id = c.id
JOIN categories cat ON a.category_id = cat.id
LEFT JOIN favorites f ON f.artifact_id = a.id
ORDER BY a.name ASC;
```

### 2. Multi-Criteria Filtering with WHERE and Parameterized Search
```sql
SELECT a.*, c.name AS civilization, cat.name AS category
FROM artifacts a
JOIN civilizations c ON a.civilization_id = c.id
JOIN categories cat ON a.category_id = cat.id
WHERE (a.name LIKE ? OR a.description LIKE ? OR a.material LIKE ?)
  AND a.civilization_id = ?
  AND a.category_id = ?;
```

### 3. Aggregate COUNT with GROUP BY and LEFT JOIN
```sql
SELECT c.id, c.name, c.region, c.period,
       COUNT(a.id) AS artifact_count
FROM civilizations c
LEFT JOIN artifacts a ON a.civilization_id = c.id
GROUP BY c.id
ORDER BY c.name;
```

### 4. INSERT (Add New Artifact)
```sql
INSERT INTO artifacts (
    name, description, period, discovery_location,
    discovery_year, material, image_url, civilization_id, category_id
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
```

### 5. UPDATE (Edit Existing Artifact)
```sql
UPDATE artifacts
SET name = ?, description = ?, period = ?, discovery_location = ?,
    discovery_year = ?, material = ?, image_url = ?,
    civilization_id = ?, category_id = ?
WHERE id = ?;
```

### 6. DELETE with Cascading Foreign Keys
```sql
DELETE FROM artifacts WHERE id = ?;
```

---

## 8. Application Features

1. **Homepage**:
   - Welcome banner with live database counts (Artifacts, Civilizations, Categories).
   - Dynamic *Artifact of the Day* randomly spotlighted.
   - Curated highlights carousel with civilization badges.
2. **Artifact Catalog (`/artifacts`)**:
   - Live search across artifact names, descriptions, materials, and locations.
   - Dual filtering by Civilization dropdown and Category dropdown.
   - Period-specific filtering.
3. **Artifact Details (`/artifact/<id>`)**:
   - High-resolution museum image with fallback to historical glyph icons if offline.
   - Comprehensive provenance metadata: civilization, region, material, discovery year, location.
   - Quick one-click favorite toggle button.
   - Direct edit and secure modal-confirmed delete triggers.
4. **CRUD Management**:
   - `/artifact/add`: Client and server-side validated input forms.
   - `/artifact/<id>/edit`: Safe pre-populated form with update notifications.
   - `/artifact/<id>/delete`: Protected `POST` handler with JavaScript confirmation modal.
5. **Favorites System (`/favorites`)**:
   - Dedicated collection page displaying saved artifacts.
   - Instant removal toggle and duplicate prevention using SQL UNIQUE constraints.
6. **Civilizations & Categories Explorers**:
   - Dedicated index pages calculating live artifact counts per culture and medium.
   - One-click filtering from any civilization or category card.

---

## 9. Known Limitations & Future Improvements

- **User Authentication**: Currently designed for educational DBMS demonstration where favorites are accessible globally. Future versions can add user login with session-specific favorites.
- **Image Uploads**: Artifacts currently accept web URLs. Future updates could implement local file upload handling using `werkzeug.utils.secure_filename`.
- **Advanced Pagination**: The catalog currently displays query results dynamically. Client-side or cursor-based pagination can be added as the collection grows beyond 1,000 items.
