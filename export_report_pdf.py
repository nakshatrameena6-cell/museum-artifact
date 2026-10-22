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
        ax.text(0.5, 0.91, "Flask + PostgreSQL on Supabase (psycopg2) Cloud DBMS Hardening",
                ha="center", fontsize=10, color="#796B5F")
        ax.plot([0.08, 0.92], [0.89, 0.89], color="#A45A2A", lw=1.5)

        p1_text = """
1. EXECUTIVE SUMMARY
The Museum Artifact Explorer was fully migrated from local SQLite to cloud-hosted
PostgreSQL on Supabase using plain SQL via psycopg2-binary. Database integrity is
enforced with GENERATED ALWAYS AS IDENTITY, TIMESTAMP/DATE data types, CHECK, NOT NULL,
and UNIQUE constraints, Many-to-Many associations (curators, exhibitions,
exhibition_artifacts), a PL/pgSQL AFTER DELETE audit trigger, multi-column indexes,
and a denormalized SQL view (artifact_details). Row Level Security (RLS) is enabled
across all tables to protect against unauthorized Supabase PostgREST exposure.
The test suite runs with complete schema-level isolation.

2. DELIVERABLES MATRIX
• Phase 1 (Database Connection & Wrapper):
  - database.py connects via DATABASE_URL using python-dotenv (sslmode=require).
  - Built DatabaseWrapper and CursorWrapper with psycopg2.extras.DictCursor.
  - Transparently translates '?' parameter placeholders to '%s'.
  - Dict rows support both row['col'] and row[0] indexing; keep commit/rollback/close.

• Phase 2 (PostgreSQL Schema Conversion):
  - Replaced AUTOINCREMENT with INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY.
  - Set created_at to TIMESTAMP DEFAULT CURRENT_TIMESTAMP; exhibition dates to DATE.
  - Created PL/pgSQL function log_deleted_artifact() and trg_artifact_deleted trigger.
  - Replaced SQLite seed logic with INSERT ... ON CONFLICT DO NOTHING.
  - Eliminated executescript and PRAGMA statements; schema creation is idempotent.

• Phase 3 (Security & Row Level Security):
  - ALTER TABLE ... ENABLE ROW LEVEL SECURITY on all 8 tables.
  - Prevents public exposure through Supabase's auto-generated PostgREST APIs.
  - App connects as administrative 'postgres' role, which naturally bypasses RLS.

• Phase 4 (Application & Query Hardening):
  - app.py uses ILIKE for case-insensitive search.
  - Catches psycopg2 UniqueViolation and CheckViolation; executes db.rollback().
  - Converted queries.sql to PostgreSQL: STRING_AGG(DISTINCT a.material, ', ').

• Phase 5 (Testing & Documentation):
  - test_app.py uses isolated temporary test schemas (CREATE SCHEMA, search_path).
  - Created .env.example with placeholders; updated requirements.txt and README.md.
  - Recompiled high-resolution REPORT.pdf document.
"""
        ax.text(0.08, 0.86, p1_text.strip(), ha="left", va="top", fontsize=8.0,
                family="monospace", color="#2C241E")
        pdf.savefig(fig)
        plt.close()

        # Page 2: Schema, Test Results, Security & Execution
        fig2, ax2 = plt.subplots(figsize=(8.5, 11), dpi=200)
        ax2.axis("off")
        fig2.patch.set_facecolor("#FAF8F5")

        ax2.text(0.5, 0.94, "POSTGRESQL SCHEMA, TEST ARCHITECTURE & SECURITY",
                ha="center", fontsize=15, fontweight="bold", color="#2C241E")
        ax2.plot([0.08, 0.92], [0.91, 0.91], color="#A45A2A", lw=1.5)

        p2_text = """
3. FINAL RELATIONAL SCHEMA OVERVIEW
• civilizations (id INT IDENTITY PK, name TEXT UNIQUE, region, period, description)
• categories (id INT IDENTITY PK, name TEXT UNIQUE, description)
• artifacts (id INT IDENTITY PK, name NOT NULL, description NOT NULL, period,
  discovery_location, discovery_year INT, material, image_url, civilization_id INT FK,
  category_id INT FK, created_at TIMESTAMP, CHECK(discovery_year <= 2026),
  CHECK(length(trim(name)) > 0), UNIQUE(name, civilization_id))
• favorites (id INT IDENTITY PK, artifact_id INT FK UNIQUE ON DELETE CASCADE, created_at)
• curators (id INT IDENTITY PK, name NOT NULL, email NOT NULL UNIQUE, specialization)
• exhibitions (id INT IDENTITY PK, title NOT NULL UNIQUE, start_date DATE, end_date DATE,
  curator_id INT FK ON DELETE SET NULL, CHECK(end_date >= start_date))
• exhibition_artifacts (exhibition_id INT FK, artifact_id INT FK, PRIMARY KEY, CASCADE)
• deleted_artifacts_log (id INT IDENTITY PK, artifact_id INT NOT NULL, name, deleted_at)
• View: artifact_details (CREATE OR REPLACE VIEW joining artifacts, civs, categories)
• Trigger: trg_artifact_deleted (PL/pgSQL AFTER DELETE trigger inserting to audit log)
• RLS: ALTER TABLE <table> ENABLE ROW LEVEL SECURITY on all 8 tables

4. TEST ARCHITECTURE & ISOLATION
• Dynamic Test Schema: setUpClass creates a dedicated temporary schema (test_museum_<uuid>).
• Search Path Switching: Dynamically executes SET search_path TO "<test_schema>", public.
• Zero Real Data Touch: Tests run exclusively within the temporary test schema.
• Automated Teardown: tearDownClass executes DROP SCHEMA IF EXISTS ... CASCADE.
• 16 Unit Tests: Covers schema tables, idempotency, catalog, ILIKE search, detail/404,
  CRUD, favorites cascade, views, constraints, PL/pgSQL trigger, and M:N cascades.

5. SECURITY ENHANCEMENTS
• Supabase Row Level Security (RLS) blocks unauthorized PostgREST API exposure.
• SSL encrypted wire protocol (sslmode=require) for all PostgreSQL connections.
• Database constraint violations trigger clean transaction rollback (db.rollback()).
• Open-redirect vulnerability eliminated via strict validation on 'next' URL parameter.
• FLASK_DEBUG parsed safely from environment variables; SECRET_KEY warning fallback.

6. HOW TO RUN THE APPLICATION
1. Copy-Item .env.example .env (set DATABASE_URL to your Supabase PostgreSQL URI)
2. python -m pip install -r requirements.txt
3. python database.py (creates tables, view, trigger, RLS, and seeds data)
4. python -m unittest test_app.py (runs 16 isolated unit tests)
5. python app.py (starts Flask server at http://127.0.0.1:5000)
"""
        ax2.text(0.08, 0.88, p2_text.strip(), ha="left", va="top", fontsize=8.0,
                 family="monospace", color="#2C241E")
        pdf.savefig(fig2)
        plt.close()

    print(f"[OK] Report PDF successfully generated: {output_pdf}")

if __name__ == "__main__":
    generate_pdf("REPORT.pdf")
