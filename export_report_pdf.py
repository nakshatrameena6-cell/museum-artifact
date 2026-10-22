"""
export_report_pdf.py — Converts the essential sections of REPORT.md into a cleanly formatted PDF document.
"""
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def generate_pdf(output_pdf="REPORT.pdf"):
    with PdfPages(output_pdf) as pdf:
        # Page 1: Cover & Summary & Deliverables
        fig, ax = plt.subplots(figsize=(8.5, 11), dpi=200)
        ax.axis("off")
        fig.patch.set_facecolor("#FAF8F5")

        ax.text(0.5, 0.94, "MUSEUM ARTIFACT EXPLORER — FINAL REPORT",
                ha="center", fontsize=15, fontweight="bold", color="#2C241E")
        ax.text(0.5, 0.91, "Flask + SQLite Relational DBMS Hardening & Feature Expansion",
                ha="center", fontsize=10, color="#796B5F")
        ax.plot([0.08, 0.92], [0.89, 0.89], color="#A45A2A", lw=1.5)

        p1_text = """
1. EXECUTIVE SUMMARY
The Museum Artifact Explorer was enhanced into a robust relational DBMS platform.
Technical debt and unneeded files were removed, database schema integrity was enforced
using CHECK, NOT NULL, and UNIQUE constraints, and M:N associations (curators,
exhibitions, exhibition_artifacts), an AFTER DELETE audit trigger, multi-column indexes,
and a denormalized SQL view (artifact_details) were added. The automated test suite was
expanded to 16 unit tests, all passing cleanly.

2. DELIVERABLES MATRIX
• Phase 1 (Cleanup):
  - Added museum.db to .gitignore; removed from git cache.
  - Deleted package-lock.json, templates/details.html, static/style.css.
  - Cleaned README personal Windows paths and removed 'Antigravity IDE'.

• Phase 2 (Fixes):
  - Sanitized 'next' parameter in toggle_favorite against open redirects.
  - Made FLASK_DEBUG configurable from environment (default off); added SECRET_KEY warning.
  - Removed legacy destructive DROP TABLE migration logic in database.py.
  - Added NOT NULL on FKs, CHECK(discovery_year <= 2026), CHECK(length(trim(name)) > 0),
    UNIQUE(name, civilization_id); handled duplicate IntegrityError in add/edit routes.
  - Assigned distinct Unsplash URLs for Roman Denarius and Chola Gold Coin.

• Phase 3 (DBMS Add-ons):
  - Created curators, exhibitions, and exhibition_artifacts (M:N junction).
  - Created indexes: idx_artifacts_name, idx_artifacts_civ_cat.
  - Created SQL View artifact_details and integrated into app.py's _artifact_query.
  - Created deleted_artifacts_log table and trg_artifact_deleted AFTER DELETE trigger.
  - Built minimal UI with /exhibitions list and /exhibitions/<id> detail pages with nav link.

• Phase 4 (Docs & Diagram):
  - Created queries.sql with 14+ documented DBMS queries (verified on seeded DB).
  - Updated README with schema, Mermaid ER diagram, and 1NF/2NF/3NF normalization.
  - Generated high-resolution docs/er_diagram.png matching the final schema.

• Phase 5 (Automated Tests):
  - Added 8 new unit tests in test_app.py (16 tests total). All 16 tests pass in 0.6s.
"""
        ax.text(0.08, 0.86, p1_text.strip(), ha="left", va="top", fontsize=8.2,
                family="monospace", color="#2C241E")
        pdf.savefig(fig)
        plt.close()

        # Page 2: Schema, Test Results, Security & Execution
        fig2, ax2 = plt.subplots(figsize=(8.5, 11), dpi=200)
        ax2.axis("off")
        fig2.patch.set_facecolor("#FAF8F5")

        ax2.text(0.5, 0.94, "DATABASE SCHEMA, TEST RESULTS & SECURITY",
                ha="center", fontsize=15, fontweight="bold", color="#2C241E")
        ax2.plot([0.08, 0.92], [0.91, 0.91], color="#A45A2A", lw=1.5)

        p2_text = """
3. FINAL RELATIONAL SCHEMA OVERVIEW
• civilizations (id PK, name NOT NULL UNIQUE, region, period, description)
• categories (id PK, name NOT NULL UNIQUE, description)
• artifacts (id PK, name NOT NULL, description NOT NULL, period, discovery_location,
  discovery_year, material, image_url, civilization_id FK NOT NULL, category_id FK NOT NULL,
  created_at, CHECK(discovery_year <= 2026), CHECK(length(trim(name)) > 0),
  UNIQUE(name, civilization_id))
• favorites (id PK, artifact_id FK NOT NULL UNIQUE ON DELETE CASCADE, created_at)
• curators (id PK, name NOT NULL, email NOT NULL UNIQUE, specialization)
• exhibitions (id PK, title NOT NULL UNIQUE, start_date NOT NULL, end_date NOT NULL,
  curator_id FK ON DELETE SET NULL, CHECK(end_date >= start_date))
• exhibition_artifacts (exhibition_id FK, artifact_id FK, PRIMARY KEY (exhibition_id, artifact_id),
  both ON DELETE CASCADE)
• deleted_artifacts_log (id PK, artifact_id NOT NULL, name NOT NULL, deleted_at)
• View: artifact_details (artifacts JOIN civilizations JOIN categories)
• Trigger: trg_artifact_deleted (AFTER DELETE ON artifacts INSERT INTO deleted_artifacts_log)
• Indexes: idx_artifacts_name ON artifacts(name), idx_artifacts_civ_cat ON (civilization_id, category_id)

4. UNITTEST EXECUTION SUMMARY
Ran 16 tests in 0.619s — Status: OK (All passed)
Tests covered: schema tables, idempotency, homepage, catalog search/filter, detail/404,
CRUD lifecycle, favorites cascade, civs/cats views, empty name validation, missing civ validation,
duplicate name rejection, open redirect sanitization, CHECK constraints, trigger logging,
exhibition routes HTTP 200, and M:N junction cascade.

5. SECURITY ENHANCEMENTS
• Open-redirect vulnerability eliminated via strict validation on 'next' URL parameter.
• FLASK_DEBUG parsed safely from environment variables, defaulting to disabled in production.
• SECRET_KEY loaded from environment with clear console warnings when dev fallback is used.
• Full parameterized queries across all database access functions to prevent SQL injection.

6. HOW TO RUN THE APPLICATION
1. python -m pip install -r requirements.txt
2. python database.py
3. python -m unittest test_app
4. python app.py  (visit http://127.0.0.1:5000)
"""
        ax2.text(0.08, 0.88, p2_text.strip(), ha="left", va="top", fontsize=8.2,
                 family="monospace", color="#2C241E")
        pdf.savefig(fig2)
        plt.close()

    print(f"[OK] Report PDF successfully generated: {output_pdf}")

if __name__ == "__main__":
    generate_pdf("REPORT.pdf")
