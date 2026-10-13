from flask import Flask, render_template, request, abort
import sqlite3
import random

app = Flask(__name__)

DATABASE = "museum.db"


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    db = get_db()

    db.executescript("""
        CREATE TABLE IF NOT EXISTS civilizations (
            civilization_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            region TEXT,
            period TEXT
        );

        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS artifacts (
            artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
            artifact_name TEXT NOT NULL,
            civilization_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            discovery_location TEXT,
            discovery_year INTEGER,
            estimated_age INTEGER,
            condition TEXT DEFAULT 'Good',
            description TEXT,
            image_url TEXT,
            FOREIGN KEY (civilization_id)
                REFERENCES civilizations(civilization_id),
            FOREIGN KEY (category_id)
                REFERENCES categories(category_id)
        );
    """)

    civilization_count = db.execute(
        "SELECT COUNT(*) FROM civilizations"
    ).fetchone()[0]

    if civilization_count == 0:
        db.executemany("""
            INSERT INTO civilizations (name, region, period)
            VALUES (?, ?, ?)
        """, [
            ("Roman", "Europe", "Ancient"),
            ("Egyptian", "North Africa", "Ancient"),
            ("Chola", "South India", "Medieval"),
            ("Greek", "Europe", "Ancient"),
        ])

    category_count = db.execute(
        "SELECT COUNT(*) FROM categories"
    ).fetchone()[0]

    if category_count == 0:
        db.executemany("""
            INSERT INTO categories (category_name)
            VALUES (?)
        """, [
            ("Coins",),
            ("Sculptures",),
            ("Pottery",),
            ("Jewelry",),
        ])

    artifact_count = db.execute(
        "SELECT COUNT(*) FROM artifacts"
    ).fetchone()[0]

    if artifact_count == 0:
        db.executemany("""
            INSERT INTO artifacts (
                artifact_name,
                civilization_id,
                category_id,
                discovery_location,
                discovery_year,
                estimated_age,
                condition,
                description,
                image_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (
                "Roman Silver Coin",
                1, 1, "Rome, Italy", 1890, 1800, "Good",
                "A silver coin representing the monetary history "
                "of ancient Rome.",
                "https://images.unsplash.com/photo-1605792657660-596af9009e82"
            ),
            (
                "Egyptian Gold Jewelry",
                2, 4, "Egypt", 1920, 2500, "Good",
                "An example of the craftsmanship associated "
                "with ancient Egyptian jewelry.",
                "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338"
            ),
            (
                "Chola Bronze Sculpture",
                3, 2, "Tamil Nadu, India", 1950, 900, "Excellent",
                "A bronze sculpture representing the artistic "
                "traditions of the Chola period.",
                "https://images.unsplash.com/photo-1577083552431-6e5fd01aa342"
            ),
            (
                "Ancient Greek Pottery",
                4, 3, "Athens, Greece", 1900, 2200, "Fair",
                "Pottery provides information about the daily "
                "life and artistic traditions of ancient Greece.",
                "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61"
            ),
        ])

    db.commit()
    db.close()


@app.route("/")
def home():
    db = get_db()

    search = request.args.get("search", "").strip()
    civilization_id = request.args.get("civilization", "").strip()
    category_id = request.args.get("category", "").strip()
    period = request.args.get("period", "").strip()

    query = """
        SELECT
            a.*,
            c.name AS civilization,
            c.period AS historical_period,
            cat.category_name
        FROM artifacts a
        JOIN civilizations c
            ON a.civilization_id = c.civilization_id
        JOIN categories cat
            ON a.category_id = cat.category_id
        WHERE 1=1
    """

    params = []

    if search:
        query += " AND a.artifact_name LIKE ?"
        params.append(f"%{search}%")

    if civilization_id.isdigit():
        query += " AND a.civilization_id = ?"
        params.append(int(civilization_id))

    if category_id.isdigit():
        query += " AND a.category_id = ?"
        params.append(int(category_id))

    if period:
        query += " AND c.period = ?"
        params.append(period)

    query += " ORDER BY a.artifact_name"

    artifacts = db.execute(query, params).fetchall()

    civilizations = db.execute("""
        SELECT * FROM civilizations ORDER BY name
    """).fetchall()

    categories = db.execute("""
        SELECT * FROM categories ORDER BY category_name
    """).fetchall()

    periods = db.execute("""
        SELECT DISTINCT period
        FROM civilizations
        WHERE period IS NOT NULL AND period != ''
        ORDER BY period
    """).fetchall()

    total = db.execute("""
        SELECT COUNT(*) FROM artifacts
    """).fetchone()[0]

    featured = db.execute("""
        SELECT
            a.*,
            c.name AS civilization,
            c.period AS historical_period,
            cat.category_name
        FROM artifacts a
        JOIN civilizations c
            ON a.civilization_id = c.civilization_id
        JOIN categories cat
            ON a.category_id = cat.category_id
    """).fetchall()

    artifact_of_day = random.choice(featured) if featured else None

    db.close()

    return render_template(
        "index.html",
        artifacts=artifacts,
        civilizations=civilizations,
        categories=categories,
        periods=periods,
        search=search,
        selected_civilization=civilization_id,
        selected_category=category_id,
        selected_period=period,
        total=total,
        artifact_of_day=artifact_of_day
    )


@app.route("/artifact/<int:artifact_id>")
def details(artifact_id):
    db = get_db()

    artifact = db.execute("""
        SELECT
            a.*,
            c.name AS civilization,
            c.region,
            c.period AS historical_period,
            cat.category_name
        FROM artifacts a
        JOIN civilizations c
            ON a.civilization_id = c.civilization_id
        JOIN categories cat
            ON a.category_id = cat.category_id
        WHERE a.artifact_id = ?
    """, (artifact_id,)).fetchone()

    db.close()

    if artifact is None:
        abort(404)

    return render_template("details.html", artifact=artifact)


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)