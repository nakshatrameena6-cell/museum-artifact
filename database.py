"""
database.py — Museum Artifact Explorer
Handles database initialization, schema creation, and sample data seeding.
"""

import sqlite3
import os
from datetime import datetime

DATABASE = os.path.join(os.path.dirname(__file__), "museum.db")


def get_db():
    """Return a database connection with row factory and FK enforcement."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    """Create all tables and seed sample data if the DB is empty."""
    conn = get_db()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS civilizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                region TEXT,
                period TEXT,
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                period TEXT,
                discovery_location TEXT,
                discovery_year INTEGER,
                material TEXT,
                image_url TEXT,
                civilization_id INTEGER,
                category_id INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (civilization_id) REFERENCES civilizations(id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            );

            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artifact_id INTEGER NOT NULL UNIQUE,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (artifact_id) REFERENCES artifacts(id) ON DELETE CASCADE
            );
        """)
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
                "INSERT OR IGNORE INTO civilizations (name, region, period, description) VALUES (?, ?, ?, ?)",
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
                "INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)",
                cat
            )

        conn.commit()

        # Look up IDs by name for reliable FK references
        def civ_id(name):
            return conn.execute("SELECT id FROM civilizations WHERE name=?", (name,)).fetchone()[0]

        def cat_id(name):
            return conn.execute("SELECT id FROM categories WHERE name=?", (name,)).fetchone()[0]

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
                "https://images.unsplash.com/photo-1605792657660-596af9009e82?w=800",
                civ_id("Chola"), cat_id("Coins")
            ),
        ]

        for a in artifacts:
            conn.execute(
                """INSERT OR IGNORE INTO artifacts
                   (name, description, period, discovery_location, discovery_year,
                    material, image_url, civilization_id, category_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                a
            )

        conn.commit()
        print("[DB] Database ready at: " + DATABASE)

    except sqlite3.Error as e:
        print("[DB ERROR] " + str(e))
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    initialize_database()
    print("[DB] Initialization complete.")
