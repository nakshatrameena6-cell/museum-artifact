"""
database.py — Museum Artifact Explorer
Handles PostgreSQL database connection, schema initialization, and sample data seeding on Supabase.
"""

import os
import re
from pathlib import Path
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)

# Configurable search path schema, primarily used for test suite isolation
SCHEMA = None


def validate_database_url(db_url):
    """Validate DATABASE_URL ensuring it is present and not an unedited placeholder."""
    if not db_url or not db_url.strip():
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please edit .env in the project root with your actual Supabase connection string."
        )
    placeholders = ["YOUR_PASSWORD", "YOUR_PROJECT_REF", "YOUR_REGION", "[", "]"]
    if any(p in db_url for p in placeholders):
        raise ValueError(
            "DATABASE_URL in .env contains placeholder text (e.g. YOUR_PASSWORD, YOUR_PROJECT_REF) or square brackets. "
            "Please edit .env in the project root and replace placeholders with your actual Supabase credentials."
        )
    return db_url.strip()


class CursorWrapper:
    """Wrapper around psycopg2.extras.DictCursor supporting row['col'] and row[0]."""
    def __init__(self, cur):
        self._cur = cur

    def execute(self, sql, params=None):
        pg_sql = sql.replace("?", "%s")
        if params is not None:
            self._cur.execute(pg_sql, tuple(params))
        else:
            self._cur.execute(pg_sql)
        return self

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def fetchmany(self, size=None):
        return self._cur.fetchmany(size)

    def close(self):
        return self._cur.close()

    @property
    def rowcount(self):
        return self._cur.rowcount

    def __iter__(self):
        return iter(self._cur)


class DatabaseWrapper:
    """Connection wrapper with execute(sql, params), commit, rollback, and close."""
    def __init__(self, conn, schema=None):
        self._conn = conn
        self.schema = schema

    def execute(self, sql, params=None):
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        wrapper = CursorWrapper(cur)
        wrapper.execute(sql, params)
        return wrapper

    def cursor(self):
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        return CursorWrapper(cur)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    @property
    def raw_connection(self):
        return self._conn


def get_db(schema=None):
    """Return a wrapped PostgreSQL database connection using DATABASE_URL (sslmode=require)."""
    load_dotenv(ENV_PATH)
    db_url = validate_database_url(os.environ.get("DATABASE_URL"))
    conn = psycopg2.connect(db_url, sslmode="require")
    active_schema = schema or SCHEMA
    if active_schema:
        with conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{active_schema}", public')
    return DatabaseWrapper(conn, active_schema)


def initialize_database(schema=None):
    """Create all tables, view, trigger, indexes and seed sample data idempotently."""
    conn = get_db(schema)
    try:
        ddl_statements = [
            """
            CREATE TABLE IF NOT EXISTS civilizations (
                id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                region TEXT,
                period TEXT,
                description TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS artifacts (
                id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                period TEXT,
                discovery_location TEXT,
                discovery_year INT,
                material TEXT,
                image_url TEXT,
                civilization_id INT NOT NULL REFERENCES civilizations(id),
                category_id INT NOT NULL REFERENCES categories(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT check_discovery_year CHECK (discovery_year IS NULL OR discovery_year <= 2026),
                CONSTRAINT check_artifact_name CHECK (length(trim(name)) > 0),
                CONSTRAINT uq_artifact_civ UNIQUE (name, civilization_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS favorites (
                id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                artifact_id INT NOT NULL UNIQUE REFERENCES artifacts(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS curators (
                id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                specialization TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS exhibitions (
                id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                title TEXT NOT NULL UNIQUE,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                curator_id INT REFERENCES curators(id) ON DELETE SET NULL,
                CONSTRAINT check_exhibition_dates CHECK (end_date >= start_date)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS exhibition_artifacts (
                exhibition_id INT NOT NULL REFERENCES exhibitions(id) ON DELETE CASCADE,
                artifact_id INT NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
                PRIMARY KEY (exhibition_id, artifact_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS deleted_artifacts_log (
                id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                artifact_id INT NOT NULL,
                name TEXT NOT NULL,
                deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_artifacts_name ON artifacts (name)",
            "CREATE INDEX IF NOT EXISTS idx_artifacts_civ_cat ON artifacts (civilization_id, category_id)",
            """
            CREATE OR REPLACE VIEW artifact_details AS
            SELECT
                a.id,
                a.name,
                a.description,
                a.period,
                a.discovery_location,
                a.discovery_year,
                a.material,
                a.image_url,
                a.created_at,
                a.civilization_id,
                a.category_id,
                c.name AS civilization,
                c.region AS region,
                c.period AS civ_period,
                cat.name AS category
            FROM artifacts a
            JOIN civilizations c ON a.civilization_id = c.id
            JOIN categories cat ON a.category_id = cat.id
            """,
            """
            CREATE OR REPLACE FUNCTION log_deleted_artifact()
            RETURNS TRIGGER AS $$
            BEGIN
                INSERT INTO deleted_artifacts_log (artifact_id, name, deleted_at)
                VALUES (OLD.id, OLD.name, CURRENT_TIMESTAMP);
                RETURN OLD;
            END;
            $$ LANGUAGE plpgsql
            """,
            "DROP TRIGGER IF EXISTS trg_artifact_deleted ON artifacts",
            """
            CREATE TRIGGER trg_artifact_deleted
            AFTER DELETE ON artifacts
            FOR EACH ROW
            EXECUTE FUNCTION log_deleted_artifact()
            """,
            "ALTER TABLE civilizations ENABLE ROW LEVEL SECURITY",
            "ALTER TABLE categories ENABLE ROW LEVEL SECURITY",
            "ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY",
            "ALTER TABLE favorites ENABLE ROW LEVEL SECURITY",
            "ALTER TABLE curators ENABLE ROW LEVEL SECURITY",
            "ALTER TABLE exhibitions ENABLE ROW LEVEL SECURITY",
            "ALTER TABLE exhibition_artifacts ENABLE ROW LEVEL SECURITY",
            "ALTER TABLE deleted_artifacts_log ENABLE ROW LEVEL SECURITY",
        ]

        for stmt in ddl_statements:
            conn.execute(stmt)
        conn.commit()

        # ── Seed civilizations ──────────────────────────────────────────────
        civs = [
            ("Indus Valley", "South Asia", "Bronze Age (3300-1300 BCE)",
             "One of the world's earliest urban civilizations, known for advanced city planning, sewage systems, and standardized weights."),
            ("Egyptian", "North Africa", "Ancient (3100-30 BCE)",
             "A civilization renowned for its monumental architecture, hieroglyphic writing, and rich religious traditions along the Nile River."),
            ("Roman", "Europe / Mediterranean", "Ancient (753 BCE-476 CE)",
             "A vast empire that shaped Western civilization through law, engineering, language, and governance."),
            ("Greek", "Europe / Mediterranean", "Ancient (800-146 BCE)",
             "The birthplace of democracy, philosophy, and the Olympic Games; pivotal in shaping modern Western thought."),
            ("Chola", "South India", "Medieval (300-1279 CE)",
             "A powerful Tamil dynasty celebrated for its bronze sculptures, temple architecture, and naval prowess across Southeast Asia."),
        ]
        for civ in civs:
            conn.execute(
                "INSERT INTO civilizations (name, region, period, description) VALUES (?, ?, ?, ?) ON CONFLICT (name) DO NOTHING",
                civ
            )

        # ── Seed categories ─────────────────────────────────────────────────
        cats = [
            ("Pottery",       "Ceramic vessels and objects shaped from clay, fired to create durable containers and art."),
            ("Sculpture",     "Three-dimensional works of art crafted from stone, metal, or clay."),
            ("Coins",         "Metal currency pieces stamped with images and inscriptions, serving as both money and historical records."),
            ("Tools",         "Implements made from stone, metal, or bone used in daily life, farming, or warfare."),
            ("Jewellery",     "Ornamental items worn as personal adornment, often reflecting social status and artistic mastery."),
            ("Inscriptions",  "Engraved or painted text on stone, metal, or clay tablets, preserving language and history."),
        ]
        for cat in cats:
            conn.execute(
                "INSERT INTO categories (name, description) VALUES (?, ?) ON CONFLICT (name) DO NOTHING",
                cat
            )

        conn.commit()

        def civ_id(name):
            row = conn.execute("SELECT id FROM civilizations WHERE name=?", (name,)).fetchone()
            return row[0] if row else None

        def cat_id(name):
            row = conn.execute("SELECT id FROM categories WHERE name=?", (name,)).fetchone()
            return row[0] if row else None

        # ── Seed artifacts ──────────────────────────────────────────────────
        artifacts = [
            (
                "Mohenjo-daro Dancing Girl",
                "A small bronze figurine of a dancing girl discovered at Mohenjo-daro. "
                "Cast using the lost-wax technique, this 4,500-year-old figure is one of the "
                "earliest known examples of Indian bronze sculpture.",
                "Bronze Age (2300-1750 BCE)", "Mohenjo-daro, Pakistan", 1926, "Bronze",
                "https://images.unsplash.com/photo-1577083552431-6e5fd01aa342?w=800",
                civ_id("Indus Valley"), cat_id("Sculpture")
            ),
            (
                "Indus Valley Terracotta Figurine",
                "A terracotta female figurine with ornate headdress, believed to represent a mother goddess. "
                "Such figurines are found across Indus Valley sites and reflect early religious practices.",
                "Bronze Age (2600-1900 BCE)", "Harappa, Pakistan", 1921, "Terracotta",
                "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=800",
                civ_id("Indus Valley"), cat_id("Sculpture")
            ),
            (
                "Indus Seal with Script",
                "A square steatite stamp seal engraved with an animal figure and undeciphered Indus script. "
                "Over 4,000 such seals have been found, hinting at a complex trade network.",
                "Bronze Age (2500-1900 BCE)", "Mohenjo-daro, Pakistan", 1931, "Steatite",
                "https://images.unsplash.com/photo-1606761568499-6d2451b23c66?w=800",
                civ_id("Indus Valley"), cat_id("Inscriptions")
            ),
            (
                "Rosetta Stone Inscription",
                "A granodiorite stele inscribed with a decree in three scripts -- hieroglyphic, Demotic, "
                "and Ancient Greek. The key to deciphering Egyptian hieroglyphics, discovered in 1799.",
                "Ptolemaic Period (196 BCE)", "Rosetta (Rashid), Egypt", 1799, "Granodiorite",
                "https://images.unsplash.com/photo-1608889453582-1b3a35a8e8e7?w=800",
                civ_id("Egyptian"), cat_id("Inscriptions")
            ),
            (
                "Canopic Jar of Qebehsenuef",
                "A limestone canopic jar with a falcon-headed lid, used to store mummified internal organs. "
                "Protected by the god Qebehsenuef, it reflects Egyptian beliefs about the afterlife.",
                "New Kingdom (1550-1070 BCE)", "Valley of the Kings, Luxor", 1905, "Limestone",
                "https://images.unsplash.com/photo-1594736797933-d0501ba2fe65?w=800",
                civ_id("Egyptian"), cat_id("Pottery")
            ),
            (
                "Egyptian Gold Pectoral",
                "A elaborate gold pectoral necklace inlaid with semi-precious stones and faience, "
                "worn by royalty and high priests as a symbol of divine protection.",
                "Middle Kingdom (2055-1650 BCE)", "Dahshur, Egypt", 1894, "Gold, Carnelian, Lapis Lazuli",
                "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=800",
                civ_id("Egyptian"), cat_id("Jewellery")
            ),
            (
                "Roman Silver Denarius",
                "A silver denarius bearing the profile of Emperor Augustus and a reverse depicting "
                "the Ara Pacis. Such coins formed the backbone of trade across the Roman Empire.",
                "Early Empire (27 BCE-14 CE)", "Rome, Italy", 1892, "Silver",
                "https://images.unsplash.com/photo-1605792657660-596af9009e82?w=800",
                civ_id("Roman"), cat_id("Coins")
            ),
            (
                "Roman Garum Amphora",
                "A large ceramic amphora used to transport garum, a fermented fish sauce that was the "
                "ketchup of ancient Rome. Stamped with the merchant's mark for traceability.",
                "Imperial Period (1st-3rd CE)", "Pompeii, Italy", 1885, "Terracotta",
                "https://images.unsplash.com/photo-1578301978018-3005759f48f7?w=800",
                civ_id("Roman"), cat_id("Pottery")
            ),
            (
                "Roman Legionary Gladius",
                "A double-edged short sword of iron with a carved bone handle, standard issue for "
                "Roman legionaries. Its design allowed close-quarters thrusting in formation.",
                "Republican-Imperial Period (300 BCE-400 CE)", "Britannia (England)", 1978, "Iron, Bone",
                "https://images.unsplash.com/photo-1551269901-5c5e14c25df7?w=800",
                civ_id("Roman"), cat_id("Tools")
            ),
            (
                "Athenian Black-Figure Amphora",
                "A large ceramic amphora painted in the black-figure technique, depicting the "
                "myth of Achilles and Ajax playing dice. A masterpiece of 6th-century BCE Attic pottery.",
                "Archaic Period (540-530 BCE)", "Athens, Greece", 1908, "Terracotta",
                "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800",
                civ_id("Greek"), cat_id("Pottery")
            ),
            (
                "Chola Nataraja Bronze",
                "A masterwork of Indian metalwork depicting Shiva as Lord of the Dance. "
                "Cast in the lost-wax method and noted for its dynamic ring of fire and cosmic symbolism.",
                "Chola Period (10th-11th CE)", "Thanjavur, Tamil Nadu, India", 1912, "Bronze",
                "https://images.unsplash.com/photo-1490806843957-31f4c9a91c65?w=800",
                civ_id("Chola"), cat_id("Sculpture")
            ),
            (
                "Chola Gold Coin (Kalanjarai Pon)",
                "A pure gold coin stamped with the Chola tiger emblem and Tamil inscription, "
                "used in temple treasury transactions and long-distance maritime trade.",
                "Medieval (985-1014 CE)", "Thanjavur District, Tamil Nadu", 1960, "Gold",
                "https://images.unsplash.com/photo-1621416894569-0f39ed31d247?w=800",
                civ_id("Chola"), cat_id("Coins")
            ),
        ]

        for a in artifacts:
            conn.execute(
                """INSERT INTO artifacts
                   (name, description, period, discovery_location, discovery_year,
                    material, image_url, civilization_id, category_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT (name, civilization_id) DO NOTHING""",
                a
            )

        conn.commit()

        # ── Seed curators ───────────────────────────────────────────────────
        curators = [
            ("Dr. Evelyn Reed", "e.reed@museum.org", "Ancient Mediterranean & Near Eastern Antiquities"),
            ("Dr. Rajesh Sharma", "r.sharma@museum.org", "Indus Valley & South Asian Archaeology"),
            ("Prof. Amara Mansour", "a.mansour@museum.org", "Dynastic Egypt & Nile Civilizations"),
        ]
        for cur in curators:
            conn.execute(
                "INSERT INTO curators (name, email, specialization) VALUES (?, ?, ?) ON CONFLICT (email) DO NOTHING",
                cur
            )
        conn.commit()

        def curator_id(email):
            row = conn.execute("SELECT id FROM curators WHERE email = ?", (email,)).fetchone()
            return row[0] if row else None

        # ── Seed exhibitions ────────────────────────────────────────────────
        exhibitions = [
            (
                "Echoes of the Indus: Dawn of Urbanity",
                "2026-03-01",
                "2026-06-30",
                curator_id("r.sharma@museum.org")
            ),
            (
                "Treasures of the Nile: Gold & Eternity",
                "2026-04-15",
                "2026-09-15",
                curator_id("a.mansour@museum.org")
            ),
            (
                "Imperial Grandeur: Rome and the Classical World",
                "2026-05-01",
                "2026-10-31",
                curator_id("e.reed@museum.org")
            ),
        ]
        for exh in exhibitions:
            conn.execute(
                "INSERT INTO exhibitions (title, start_date, end_date, curator_id) VALUES (?, ?, ?, ?) ON CONFLICT (title) DO NOTHING",
                exh
            )
        conn.commit()

        def exh_id(title):
            row = conn.execute("SELECT id FROM exhibitions WHERE title = ?", (title,)).fetchone()
            return row[0] if row else None

        def art_id(name):
            row = conn.execute("SELECT id FROM artifacts WHERE name = ?", (name,)).fetchone()
            return row[0] if row else None

        # ── Seed exhibition_artifacts (many-to-many links) ──────────────────
        links = [
            ("Echoes of the Indus: Dawn of Urbanity", "Mohenjo-daro Dancing Girl"),
            ("Echoes of the Indus: Dawn of Urbanity", "Indus Valley Terracotta Figurine"),
            ("Echoes of the Indus: Dawn of Urbanity", "Indus Seal with Script"),
            ("Treasures of the Nile: Gold & Eternity", "Rosetta Stone Inscription"),
            ("Treasures of the Nile: Gold & Eternity", "Canopic Jar of Qebehsenuef"),
            ("Treasures of the Nile: Gold & Eternity", "Egyptian Gold Pectoral"),
            ("Imperial Grandeur: Rome and the Classical World", "Roman Silver Denarius"),
            ("Imperial Grandeur: Rome and the Classical World", "Roman Garum Amphora"),
            ("Imperial Grandeur: Rome and the Classical World", "Roman Legionary Gladius"),
            ("Imperial Grandeur: Rome and the Classical World", "Athenian Black-Figure Amphora"),
        ]
        for title, art_name in links:
            eid = exh_id(title)
            aid = art_id(art_name)
            if eid and aid:
                conn.execute(
                    "INSERT INTO exhibition_artifacts (exhibition_id, artifact_id) VALUES (?, ?) ON CONFLICT (exhibition_id, artifact_id) DO NOTHING",
                    (eid, aid)
                )
        conn.commit()
        print("[DB] PostgreSQL database ready on Supabase.")

    except psycopg2.Error as e:
        print("[DB ERROR] " + str(e))
        conn.rollback()
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    initialize_database()
    print("[DB] Initialization complete.")
