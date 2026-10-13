from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "museum.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            origin TEXT,
            year INTEGER,
            description TEXT,
            image_url TEXT
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM artifacts")
    if cursor.fetchone()[0] == 0:
        sample_artifacts = [
            ("Golden Death Mask", "Jewelry", "Egypt", -1323, "Funerary mask of Pharaoh Tutankhamun, made of solid gold.", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/CairoEgMuseum_TutankhamunMaskFront.jpg/400px-CairoEgMuseum_TutankhamunMaskFront.jpg"),
            ("Rosetta Stone", "Inscriptions", "Egypt", -196, "Granodiorite stele inscribed with three versions of a decree issued at Memphis.", "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/Rosetta_Stone.JPG/400px-Rosetta_Stone.JPG"),
            ("Venus de Milo", "Sculpture", "Greece", -100, "Ancient Greek marble statue and one of the most famous works of ancient Greek sculpture.", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Venus_de_Milo_%28Louvre%2C_Ma_399%29.jpg/400px-Venus_de_Milo_%28Louvre%2C_Ma_399%29.jpg"),
            ("Terracotta Army", "Sculpture", "China", -210, "Collection of terracotta sculptures depicting the armies of Qin Shi Huang.", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Dragon_terra_cotta_warriors_2009.jpg/400px-Dragon_terra_cotta_warriors_2009.jpg"),
            ("Moai Statues", "Sculpture", "Easter Island", 1400, "Monolithic human figures carved by the Rapa Nui people.", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Moai_Rano_raraku.jpg/400px-Moai_Rano_raraku.jpg"),
        ]
        cursor.executemany(
            "INSERT INTO artifacts (name, category, origin, year, description, image_url) VALUES (?, ?, ?, ?, ?, ?)",
            sample_artifacts
        )
    conn.commit()
    conn.close()


@app.route("/")
def index():
    search = request.args.get("search", "")
    category = request.args.get("category", "")
    conn = get_db()
    query = "SELECT * FROM artifacts WHERE 1=1"
    params = []
    if search:
        query += " AND (name LIKE ? OR origin LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    if category:
        query += " AND category = ?"
        params.append(category)
    artifacts = conn.execute(query, params).fetchall()
    categories = conn.execute("SELECT DISTINCT category FROM artifacts").fetchall()
    conn.close()
    return render_template("index.html", artifacts=artifacts, categories=categories, search=search, category=category)


@app.route("/artifact/<int:artifact_id>")
def details(artifact_id):
    conn = get_db()
    artifact = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    conn.close()
    if artifact is None:
        return redirect(url_for("index"))
    return render_template("details.html", artifact=artifact)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
