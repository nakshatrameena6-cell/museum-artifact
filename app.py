"""
app.py — Museum Artifact Explorer
Full Flask application with SQLite backend.
Routes: home, artifacts, artifact detail, add, edit, delete, favorites,
        civilizations, categories, and search/filter.
"""

import os
import random
import sqlite3
from flask import (Flask, render_template, request, redirect,
                   url_for, flash, abort, jsonify)
from database import get_db, initialize_database

# ── App setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)
# Set SECRET_KEY in environment for production; warn if dev fallback is used.
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    print("[WARNING] SECRET_KEY not found in environment; using insecure development fallback!")
    secret_key = "dev-museum-secret-key-change-in-prod"
app.secret_key = secret_key



# ── Helper ───────────────────────────────────────────────────────────────────
def _artifact_query(extra_where="", params=None, order="ad.name"):
    """Return the base artifact SELECT using artifact_details view with optional WHERE clause."""
    sql = """
        SELECT
            ad.id, ad.name, ad.description, ad.period, ad.discovery_location,
            ad.discovery_year, ad.material, ad.image_url, ad.created_at,
            ad.civilization_id, ad.category_id,
            ad.civilization,
            ad.region,
            ad.civ_period,
            ad.category,
            CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END AS is_favorite
        FROM artifact_details ad
        LEFT JOIN favorites f ON f.artifact_id = ad.id
    """
    if extra_where:
        w = extra_where
        w = w.replace("c.name", "ad.civilization")
        w = w.replace("cat.name", "ad.category")
        w = w.replace("c.period", "ad.civ_period")
        w = w.replace("a.", "ad.")
        sql += " WHERE " + w
    order_clause = order.replace("a.", "ad.")
    sql += " ORDER BY " + order_clause
    return sql, (params or [])


# ── Homepage ─────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    db = get_db()
    try:
        total_artifacts = db.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
        total_civs      = db.execute("SELECT COUNT(*) FROM civilizations").fetchone()[0]
        total_cats      = db.execute("SELECT COUNT(*) FROM categories").fetchone()[0]

        sql, params = _artifact_query()
        all_artifacts = db.execute(sql, params).fetchall()

        featured = random.sample(list(all_artifacts), min(3, len(all_artifacts)))
        artifact_of_day = random.choice(all_artifacts) if all_artifacts else None
    finally:
        db.close()

    return render_template(
        "index.html",
        featured=featured,
        artifact_of_day=artifact_of_day,
        total_artifacts=total_artifacts,
        total_civs=total_civs,
        total_cats=total_cats,
    )


# ── Artifact listing + search + filter ───────────────────────────────────────
@app.route("/artifacts")
def artifacts():
    db = get_db()
    try:
        search      = request.args.get("search", "").strip()
        civ_filter  = request.args.get("civilization", "").strip()
        cat_filter  = request.args.get("category", "").strip()
        period_filter = request.args.get("period", "").strip()

        conditions, params = [], []

        if search:
            conditions.append(
                "(a.name LIKE ? OR a.description LIKE ? "
                "OR a.material LIKE ? OR a.period LIKE ? "
                "OR a.discovery_location LIKE ? "
                "OR c.name LIKE ? OR cat.name LIKE ?)"
            )
            term = f"%{search}%"
            params.extend([term] * 7)

        if civ_filter.isdigit():
            conditions.append("a.civilization_id = ?")
            params.append(int(civ_filter))

        if cat_filter.isdigit():
            conditions.append("a.category_id = ?")
            params.append(int(cat_filter))

        if period_filter:
            conditions.append("c.period = ?")
            params.append(period_filter)

        where = " AND ".join(conditions)
        sql, params = _artifact_query(where, params)
        artifact_list = db.execute(sql, params).fetchall()

        civilizations = db.execute("SELECT * FROM civilizations ORDER BY name").fetchall()
        categories    = db.execute("SELECT * FROM categories    ORDER BY name").fetchall()
        periods       = db.execute(
            "SELECT DISTINCT period FROM civilizations WHERE period IS NOT NULL ORDER BY period"
        ).fetchall()
    finally:
        db.close()

    return render_template(
        "artifacts.html",
        artifacts=artifact_list,
        civilizations=civilizations,
        categories=categories,
        periods=periods,
        search=search,
        selected_civ=civ_filter,
        selected_cat=cat_filter,
        selected_period=period_filter,
    )


# ── Artifact detail ───────────────────────────────────────────────────────────
@app.route("/artifact/<int:artifact_id>")
def artifact_detail(artifact_id):
    db = get_db()
    try:
        sql, _ = _artifact_query("a.id = ?", [artifact_id])
        artifact = db.execute(sql, [artifact_id]).fetchone()
    finally:
        db.close()

    if artifact is None:
        abort(404)

    return render_template("artifact_detail.html", artifact=artifact)


# ── Add artifact ──────────────────────────────────────────────────────────────
@app.route("/artifact/add", methods=["GET", "POST"])
def add_artifact():
    db = get_db()
    try:
        civilizations = db.execute("SELECT * FROM civilizations ORDER BY name").fetchall()
        categories    = db.execute("SELECT * FROM categories    ORDER BY name").fetchall()

        if request.method == "POST":
            name             = request.form.get("name", "").strip()
            description      = request.form.get("description", "").strip()
            period           = request.form.get("period", "").strip()
            discovery_loc    = request.form.get("discovery_location", "").strip()
            discovery_year   = request.form.get("discovery_year", "").strip()
            material         = request.form.get("material", "").strip()
            image_url        = request.form.get("image_url", "").strip()
            civilization_id  = request.form.get("civilization_id", "").strip()
            category_id      = request.form.get("category_id", "").strip()

            errors = []
            if not name:
                errors.append("Artifact name is required.")
            if not description:
                errors.append("Description is required.")
            if not civilization_id.isdigit():
                errors.append("Please select a civilization.")
            if not category_id.isdigit():
                errors.append("Please select a category.")

            if errors:
                for e in errors:
                    flash(e, "error")
            else:
                year_val = int(discovery_year) if discovery_year.lstrip("-").isdigit() else None
                try:
                    db.execute(
                        """INSERT INTO artifacts
                           (name, description, period, discovery_location, discovery_year,
                            material, image_url, civilization_id, category_id)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (name, description, period or None, discovery_loc or None,
                         year_val, material or None, image_url or None,
                         int(civilization_id), int(category_id))
                    )
                    db.commit()
                    flash(f'"{name}" has been added to the collection!', "success")
                    return redirect(url_for("artifacts"))
                except sqlite3.IntegrityError as e:
                    db.rollback()
                    err_msg = str(e).lower()
                    if "unique" in err_msg:
                        flash(f'An artifact named "{name}" already exists for this civilization.', "error")
                    elif "check" in err_msg:
                        flash("Validation failed: Artifact name cannot be blank and discovery year must be \u2264 2026.", "error")
                    else:
                        flash(f"Database constraint error: {e}", "error")

        return render_template("add_artifact.html",
                               civilizations=civilizations,
                               categories=categories,
                               form=request.form)
    finally:
        db.close()


# ── Edit artifact ─────────────────────────────────────────────────────────────
@app.route("/artifact/<int:artifact_id>/edit", methods=["GET", "POST"])
def edit_artifact(artifact_id):
    db = get_db()
    try:
        artifact      = db.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
        if artifact is None:
            abort(404)

        civilizations = db.execute("SELECT * FROM civilizations ORDER BY name").fetchall()
        categories    = db.execute("SELECT * FROM categories    ORDER BY name").fetchall()

        if request.method == "POST":
            name             = request.form.get("name", "").strip()
            description      = request.form.get("description", "").strip()
            period           = request.form.get("period", "").strip()
            discovery_loc    = request.form.get("discovery_location", "").strip()
            discovery_year   = request.form.get("discovery_year", "").strip()
            material         = request.form.get("material", "").strip()
            image_url        = request.form.get("image_url", "").strip()
            civilization_id  = request.form.get("civilization_id", "").strip()
            category_id      = request.form.get("category_id", "").strip()

            errors = []
            if not name:
                errors.append("Artifact name is required.")
            if not description:
                errors.append("Description is required.")
            if not civilization_id.isdigit():
                errors.append("Please select a civilization.")
            if not category_id.isdigit():
                errors.append("Please select a category.")

            if errors:
                for e in errors:
                    flash(e, "error")
            else:
                year_val = int(discovery_year) if discovery_year.lstrip("-").isdigit() else None
                try:
                    db.execute(
                        """UPDATE artifacts SET
                           name=?, description=?, period=?, discovery_location=?,
                           discovery_year=?, material=?, image_url=?,
                           civilization_id=?, category_id=?
                           WHERE id=?""",
                        (name, description, period or None, discovery_loc or None,
                         year_val, material or None, image_url or None,
                         int(civilization_id), int(category_id), artifact_id)
                    )
                    db.commit()
                    flash(f'"{name}" has been updated successfully!', "success")
                    return redirect(url_for("artifact_detail", artifact_id=artifact_id))
                except sqlite3.IntegrityError as e:
                    db.rollback()
                    err_msg = str(e).lower()
                    if "unique" in err_msg:
                        flash(f'An artifact named "{name}" already exists for this civilization.', "error")
                    elif "check" in err_msg:
                        flash("Validation failed: Artifact name cannot be blank and discovery year must be \u2264 2026.", "error")
                    else:
                        flash(f"Database constraint error: {e}", "error")

        return render_template("edit_artifact.html",
                               artifact=artifact,
                               civilizations=civilizations,
                               categories=categories)
    finally:
        db.close()


# ── Delete artifact ───────────────────────────────────────────────────────────
@app.route("/artifact/<int:artifact_id>/delete", methods=["POST"])
def delete_artifact(artifact_id):
    db = get_db()
    try:
        artifact = db.execute("SELECT name FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
        if artifact is None:
            abort(404)
        name = artifact["name"]
        db.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
        db.commit()
        flash(f'"{name}" has been removed from the collection.', "success")
    finally:
        db.close()
    return redirect(url_for("artifacts"))


# ── Favorites ─────────────────────────────────────────────────────────────────
@app.route("/favorites")
def favorites():
    db = get_db()
    try:
        sql = """
            SELECT
                a.id, a.name, a.description, a.period,
                a.image_url, a.material,
                c.name   AS civilization,
                cat.name AS category,
                f.created_at AS saved_at
            FROM favorites f
            JOIN artifacts a    ON f.artifact_id = a.id
            JOIN civilizations c   ON a.civilization_id = c.id
            JOIN categories    cat ON a.category_id     = cat.id
            ORDER BY f.created_at DESC
        """
        fav_artifacts = db.execute(sql).fetchall()
    finally:
        db.close()

    return render_template("favorites.html", favorites=fav_artifacts)


@app.route("/artifact/<int:artifact_id>/favorite/toggle", methods=["POST"])
def toggle_favorite(artifact_id):
    db = get_db()
    try:
        artifact = db.execute("SELECT name FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
        if artifact is None:
            abort(404)

        existing = db.execute(
            "SELECT id FROM favorites WHERE artifact_id = ?", (artifact_id,)
        ).fetchone()

        if existing:
            db.execute("DELETE FROM favorites WHERE artifact_id = ?", (artifact_id,))
            db.commit()
            flash(f'"{artifact["name"]}" removed from favorites.', "info")
            action = "removed"
        else:
            db.execute("INSERT INTO favorites (artifact_id) VALUES (?)", (artifact_id,))
            db.commit()
            flash(f'"{artifact["name"]}" added to favorites!', "success")
            action = "added"
    finally:
        db.close()

    # If the request wants JSON (AJAX), return JSON
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({"action": action})

    # Otherwise redirect back safely
    default_url = url_for("artifact_detail", artifact_id=artifact_id)
    next_url = request.form.get("next")
    if not next_url or not (next_url.startswith("/") and not next_url.startswith("//")):
        next_url = default_url
    return redirect(next_url)


# ── Civilizations ─────────────────────────────────────────────────────────────
@app.route("/civilizations")
def civilizations():
    db = get_db()
    try:
        rows = db.execute("""
            SELECT c.*,
                   COUNT(a.id) AS artifact_count
            FROM civilizations c
            LEFT JOIN artifacts a ON a.civilization_id = c.id
            GROUP BY c.id
            ORDER BY c.name
        """).fetchall()
    finally:
        db.close()
    return render_template("civilizations.html", civilizations=rows)


@app.route("/civilizations/<int:civ_id>")
def civilization_detail(civ_id):
    db = get_db()
    try:
        civ = db.execute("SELECT * FROM civilizations WHERE id = ?", (civ_id,)).fetchone()
        if civ is None:
            abort(404)
        sql, params = _artifact_query("a.civilization_id = ?", [civ_id])
        artifact_list = db.execute(sql, params).fetchall()
    finally:
        db.close()
    return render_template("artifacts.html",
                           artifacts=artifact_list,
                           civilizations=[], categories=[], periods=[],
                           search="", selected_civ=str(civ_id),
                           selected_cat="", selected_period="",
                           page_title=f"Artifacts — {civ['name']} Civilization")


# ── Categories ────────────────────────────────────────────────────────────────
@app.route("/categories")
def categories():
    db = get_db()
    try:
        rows = db.execute("""
            SELECT cat.*,
                   COUNT(a.id) AS artifact_count
            FROM categories cat
            LEFT JOIN artifacts a ON a.category_id = cat.id
            GROUP BY cat.id
            ORDER BY cat.name
        """).fetchall()
    finally:
        db.close()
    return render_template("categories.html", categories=rows)


@app.route("/categories/<int:cat_id>")
def category_detail(cat_id):
    db = get_db()
    try:
        cat = db.execute("SELECT * FROM categories WHERE id = ?", (cat_id,)).fetchone()
        if cat is None:
            abort(404)
        sql, params = _artifact_query("a.category_id = ?", [cat_id])
        artifact_list = db.execute(sql, params).fetchall()
    finally:
        db.close()
    return render_template("artifacts.html",
                           artifacts=artifact_list,
                           civilizations=[], categories=[], periods=[],
                           search="", selected_civ="",
                           selected_cat=str(cat_id), selected_period="",
                           page_title=f"Artifacts — {cat['name']}")


# ── Exhibitions ───────────────────────────────────────────────────────────────
@app.route("/exhibitions")
def exhibitions():
    db = get_db()
    try:
        sql = """
            SELECT
                e.id, e.title, e.start_date, e.end_date,
                c.name AS curator_name, c.specialization AS curator_specialization,
                COUNT(ea.artifact_id) AS artifact_count
            FROM exhibitions e
            LEFT JOIN curators c ON e.curator_id = c.id
            LEFT JOIN exhibition_artifacts ea ON e.id = ea.exhibition_id
            GROUP BY e.id
            ORDER BY e.start_date ASC
        """
        rows = db.execute(sql).fetchall()
    finally:
        db.close()
    return render_template("exhibitions.html", exhibitions=rows)


@app.route("/exhibitions/<int:exh_id>")
def exhibition_detail(exh_id):
    db = get_db()
    try:
        exh = db.execute("""
            SELECT
                e.id, e.title, e.start_date, e.end_date,
                c.id AS curator_id, c.name AS curator_name,
                c.email AS curator_email, c.specialization AS curator_specialization
            FROM exhibitions e
            LEFT JOIN curators c ON e.curator_id = c.id
            WHERE e.id = ?
        """, (exh_id,)).fetchone()
        if exh is None:
            abort(404)

        sql = """
            SELECT
                ad.*,
                CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END AS is_favorite
            FROM exhibition_artifacts ea
            JOIN artifact_details ad ON ea.artifact_id = ad.id
            LEFT JOIN favorites f ON f.artifact_id = ad.id
            WHERE ea.exhibition_id = ?
            ORDER BY ad.name ASC
        """
        artifact_list = db.execute(sql, (exh_id,)).fetchall()
    finally:
        db.close()

    return render_template("exhibition_detail.html", exhibition=exh, artifacts=artifact_list)


# ── Error handlers ────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("404.html", error_code=500,
                           error_msg="Internal Server Error"), 500


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    initialize_database()
    debug_mode = os.environ.get("FLASK_DEBUG", "0").strip().lower() in ("1", "true", "yes")
    app.run(debug=debug_mode)