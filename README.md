# Museum Artifact Explorer

An interactive, responsive full-stack web application designed for exploring historical museum artifacts across ancient civilizations, periods, and classifications. Built with **Python Flask**, **SQLite**, and modern **Vanilla HTML5/CSS3/JavaScript**.

---

## 1. Project Overview & Objectives

**Museum Artifact Explorer** is developed for a College Database Management System (DBMS) project. The project demonstrates:
- Relational database modeling with **SQLite**.
- Integrity constraints: Primary Keys, Foreign Keys, Unique constraints, Cascading Deletes (`ON DELETE CASCADE`), and check constraints.
- Foreign key enforcement with `PRAGMA foreign_keys = ON`.
- Parameterized SQL queries to prevent SQL injection vulnerabilities.
- Multi-table `JOIN` operations across artifacts, civilizations, categories, and favorites.
- Full CRUD functionality (Create, Read, Update, Delete) on artifacts.
- Live searching, multi-criteria filtering, and user favoriting.
- An aesthetically refined museum theme (warm beige, cream, dark brown, and muted gold palette).

---

## 2. Technologies Used

- **Backend**: Python 3, Flask
- **Database**: SQLite3 (via Python standard library `sqlite3`)
- **Templating**: Flask Jinja2
- **Frontend**: Semantic HTML5, Vanilla CSS3 (custom CSS design system with Google Fonts *Playfair Display* & *Inter*), Modern Vanilla JavaScript (ES6+)
- **Development Tooling**: Windows PowerShell / Antigravity IDE

---

## 3. Project Structure

```text
museum-artifact/
├── app.py                     # Flask application entry point and route handlers
├── database.py                # Database initialization, schema creation, and seeding
├── museum.db                  # SQLite database file (created automatically)
├── requirements.txt           # Python package dependencies
├── README.md                  # Comprehensive documentation and project guide
├── .gitignore                 # Files excluded from version control
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Base layout with navbar, footer, flash alerts
│   ├── index.html             # Homepage: Hero, Artifact of Day, Highlights, Stats
│   ├── artifacts.html         # Artifact catalog with search, filter, and card grid
│   ├── artifact_detail.html   # Detailed artifact view with full provenance and actions
│   ├── add_artifact.html      # Create new artifact form with validation
│   ├── edit_artifact.html     # Edit artifact form with prefilled values
│   ├── civilizations.html     # List of civilizations with artifact counts
│   ├── categories.html        # List of categories with thematic icons & counts
│   ├── favorites.html         # User favorites collection
│   └── 404.html               # Custom museum-themed 404/500 error page
└── static/
    ├── css/
    │   └── style.css          # Museum palette, typography, responsive grid
    ├── js/
    │   └── script.js          # Mobile navbar, auto-dismiss alerts, image fallbacks
    ├── images/                # Local asset storage
    └── style.css              # Compatibility stylesheet redirect
```

---

## 4. Database Schema & Design

The database contains **four interrelated tables**:

### Table 1: `civilizations`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique civilization identifier |
| `name` | TEXT | NOT NULL, UNIQUE | Name of civilization (e.g. Roman, Chola) |
| `region` | TEXT | | Geographical origin region |
| `period` | TEXT | | Epoch or historical date span |
| `description` | TEXT | | Cultural and historical summary |

### Table 2: `categories`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique category identifier |
| `name` | TEXT | NOT NULL, UNIQUE | Category title (e.g. Pottery, Coins) |
| `description` | TEXT | | Functional/material description |

### Table 3: `artifacts`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique artifact identifier |
| `name` | TEXT | NOT NULL | Artifact title |
| `description` | TEXT | NOT NULL | Detailed background & provenance |
| `period` | TEXT | | Historical period or dynasty |
| `discovery_location`| TEXT | | Excavation / discovery site |
| `discovery_year` | INTEGER | | Excavation year (BCE supported via negative values) |
| `material` | TEXT | | Material composition (Bronze, Gold, etc.) |
| `image_url` | TEXT | | Public image link or local path |
| `civilization_id` | INTEGER | FOREIGN KEY -> `civilizations(id)` | Associated civilization |
| `category_id` | INTEGER | FOREIGN KEY -> `categories(id)` | Associated category |
| `created_at` | TEXT | DEFAULT `(datetime('now'))` | Timestamp of database addition |

### Table 4: `favorites`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique favorite identifier |
| `artifact_id` | INTEGER | NOT NULL, UNIQUE, FOREIGN KEY -> `artifacts(id)` ON DELETE CASCADE | Reference to favorited artifact |
| `created_at` | TEXT | DEFAULT `(datetime('now'))` | Timestamp when added to favorites |

---

## 5. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    CIVILIZATIONS ||--o{ ARTIFACTS : "produces / contains"
    CATEGORIES ||--o{ ARTIFACTS : "classifies"
    ARTIFACTS ||--o| FAVORITES : "saved as"

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
        TEXT name
        TEXT description
        TEXT period
        TEXT discovery_location
        INTEGER discovery_year
        TEXT material
        TEXT image_url
        INTEGER civilization_id FK
        INTEGER category_id FK
        TEXT created_at
    }

    FAVORITES {
        INTEGER id PK
        INTEGER artifact_id FK, UK
        TEXT created_at
    }
```

### Relational Constraints Enforced:
1. **One-to-Many (`civilizations` -> `artifacts`)**: One civilization can have many artifacts.
2. **One-to-Many (`categories` -> `artifacts`)**: One category can have many artifacts.
3. **One-to-One (`artifacts` -> `favorites`)**: Each artifact can appear in the favorites table at most once via the `UNIQUE` constraint on `favorites.artifact_id`.
4. **Cascading Deletions**: Deleting an artifact removes its entry from `favorites` automatically via `ON DELETE CASCADE`.

---

## 6. Installation & Execution Guide (Windows)

### Step 1: Open Terminal in Project Directory
Navigate to the repository folder:
```powershell
cd "c:\Users\AIML 27\OneDrive\文档\museum-artifact"
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> **Note on PowerShell Execution Policy**: If PowerShell blocks script execution with a permission error, either bypass it for the current terminal session:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\.venv\Scripts\Activate.ps1
> ```
> Or invoke Python directly without activation:
> ```powershell
> .\.venv\Scripts\python.exe -m pip install -r requirements.txt
> .\.venv\Scripts\python.exe database.py
> .\.venv\Scripts\python.exe app.py
> ```

### Step 3: Install Required Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 4: Initialize the Database
```powershell
python database.py
```
This automatically builds all four tables and idempotently inserts the 5 civilizations, 6 categories, and 12 sample artifacts without duplicate conflicts.

### Step 5: Start the Flask Application
```powershell
python app.py
```

### Step 6: Access the Application
Open any web browser and visit:
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
