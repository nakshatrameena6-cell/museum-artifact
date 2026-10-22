"""
test_app.py — Comprehensive Test Suite for Museum Artifact Explorer
Runs automated tests using Flask test client with an isolated temporary SQLite database.
"""

import unittest
import tempfile
import os
import sqlite3
import app
import database


class MuseumArtifactExplorerTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary file for the isolated test database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)

        # Patch DATABASE path in both database and app modules
        self.orig_db = database.DATABASE
        database.DATABASE = self.db_path
        app.DATABASE = self.db_path

        # Configure app for testing
        app.app.config["TESTING"] = True
        app.app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.app.test_client()

        # Initialize test database
        database.initialize_database()

    def tearDown(self):
        # Restore original DB path and delete temp file
        database.DATABASE = self.orig_db
        app.DATABASE = self.orig_db
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_01_schema_and_tables(self):
        """Verify that all 4 required tables exist."""
        conn = database.get_db()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        table_names = {row["name"] for row in tables}
        conn.close()

        required = {"civilizations", "categories", "artifacts", "favorites"}
        self.assertTrue(required.issubset(table_names), f"Missing tables: {required - table_names}")

    def test_02_sample_data_and_idempotence(self):
        """Verify initial seed counts and ensure re-initializing does not duplicate."""
        conn = database.get_db()
        civ_count = conn.execute("SELECT COUNT(*) FROM civilizations").fetchone()[0]
        cat_count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        art_count = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
        conn.close()

        self.assertGreaterEqual(civ_count, 5, "Expected at least 5 civilizations")
        self.assertGreaterEqual(cat_count, 6, "Expected at least 6 categories")
        self.assertGreaterEqual(art_count, 12, "Expected at least 12 artifacts")

        # Run initialize again to test idempotency
        database.initialize_database()

        conn = database.get_db()
        civ_count2 = conn.execute("SELECT COUNT(*) FROM civilizations").fetchone()[0]
        cat_count2 = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        art_count2 = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
        conn.close()

        self.assertEqual(civ_count, civ_count2, "Civilization count changed on re-initialization!")
        self.assertEqual(cat_count, cat_count2, "Category count changed on re-initialization!")
        self.assertEqual(art_count, art_count2, "Artifact count changed on re-initialization!")

    def test_03_homepage(self):
        """Test home route responds with 200 and renders museum statistics."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("MUSEUM", html)
        self.assertIn("Artifact of the Day", html)

    def test_04_artifacts_listing_and_filtering(self):
        """Test artifact catalog, search, and civilization/category filters."""
        # 1. Base catalog
        res = self.client.get("/artifacts")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("Mohenjo-daro Dancing Girl", html)

        # 2. Search query
        res_search = self.client.get("/artifacts?search=Denarius")
        self.assertEqual(res_search.status_code, 200)
        search_html = res_search.data.decode("utf-8")
        self.assertIn("Roman Silver Denarius", search_html)
        self.assertNotIn("Mohenjo-daro Dancing Girl", search_html)

        # 3. Filter by civilization (Egyptian)
        conn = database.get_db()
        egypt_id = conn.execute("SELECT id FROM civilizations WHERE name='Egyptian'").fetchone()[0]
        conn.close()

        res_civ = self.client.get(f"/artifacts?civilization={egypt_id}")
        self.assertEqual(res_civ.status_code, 200)
        civ_html = res_civ.data.decode("utf-8")
        self.assertIn("Egyptian", civ_html)
        self.assertNotIn("Chola Nataraja Bronze", civ_html)

    def test_05_artifact_detail_and_404(self):
        """Test viewing artifact details and 404 on invalid ID."""
        conn = database.get_db()
        first_id = conn.execute("SELECT id FROM artifacts LIMIT 1").fetchone()[0]
        conn.close()

        # Valid ID
        res = self.client.get(f"/artifact/{first_id}")
        self.assertEqual(res.status_code, 200)

        # Invalid ID
        res_404 = self.client.get("/artifact/999999")
        self.assertEqual(res_404.status_code, 404)
        self.assertIn("404", res_404.data.decode("utf-8"))

    def test_06_add_edit_delete_crud(self):
        """Test complete CRUD cycle for an artifact."""
        conn = database.get_db()
        civ_id = conn.execute("SELECT id FROM civilizations LIMIT 1").fetchone()[0]
        cat_id = conn.execute("SELECT id FROM categories LIMIT 1").fetchone()[0]
        conn.close()

        # CREATE
        post_data = {
            "name": "Test Ancient Helmet",
            "description": "An experimental Corinthian bronze helmet for testing.",
            "period": "Classical Period",
            "discovery_location": "Olympia, Greece",
            "discovery_year": "1954",
            "material": "Bronze",
            "image_url": "https://example.com/test_helmet.jpg",
            "civilization_id": str(civ_id),
            "category_id": str(cat_id)
        }
        res_add = self.client.post("/artifact/add", data=post_data, follow_redirects=True)
        self.assertEqual(res_add.status_code, 200)

        conn = database.get_db()
        created = conn.execute("SELECT * FROM artifacts WHERE name=?", ("Test Ancient Helmet",)).fetchone()
        self.assertIsNotNone(created, "Artifact was not inserted into database")
        art_id = created["id"]
        conn.close()

        # READ DETAIL
        res_view = self.client.get(f"/artifact/{art_id}")
        self.assertEqual(res_view.status_code, 200)
        self.assertIn("Test Ancient Helmet", res_view.data.decode("utf-8"))

        # UPDATE (EDIT)
        edit_data = {
            "name": "Test Ancient Helmet (Updated)",
            "description": "Updated description with new archaeological findings.",
            "period": "Late Classical Period",
            "discovery_location": "Olympia, Greece",
            "discovery_year": "1954",
            "material": "Gilded Bronze",
            "image_url": "https://example.com/test_helmet.jpg",
            "civilization_id": str(civ_id),
            "category_id": str(cat_id)
        }
        res_edit = self.client.post(f"/artifact/{art_id}/edit", data=edit_data, follow_redirects=True)
        self.assertEqual(res_edit.status_code, 200)

        conn = database.get_db()
        updated = conn.execute("SELECT * FROM artifacts WHERE id=?", (art_id,)).fetchone()
        self.assertEqual(updated["name"], "Test Ancient Helmet (Updated)")
        self.assertEqual(updated["material"], "Gilded Bronze")
        conn.close()

        # DELETE
        res_del = self.client.post(f"/artifact/{art_id}/delete", follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)

        conn = database.get_db()
        deleted = conn.execute("SELECT * FROM artifacts WHERE id=?", (art_id,)).fetchone()
        conn.close()
        self.assertIsNone(deleted, "Artifact was not deleted from database")

    def test_07_favorites_and_cascade_delete(self):
        """Test adding/removing favorites, unique constraint, and cascade deletion."""
        conn = database.get_db()
        art = conn.execute("SELECT id FROM artifacts LIMIT 1").fetchone()
        art_id = art["id"]
        conn.close()

        # 1. Add to favorites
        res_fav = self.client.post(f"/artifact/{art_id}/favorite/toggle", follow_redirects=True)
        self.assertEqual(res_fav.status_code, 200)

        conn = database.get_db()
        fav_entry = conn.execute("SELECT * FROM favorites WHERE artifact_id=?", (art_id,)).fetchone()
        self.assertIsNotNone(fav_entry, "Artifact was not added to favorites")
        conn.close()

        # 2. View favorites page
        res_page = self.client.get("/favorites")
        self.assertEqual(res_page.status_code, 200)
        self.assertIn("Saved Favorites", res_page.data.decode("utf-8"))

        # 3. Toggle off (remove from favorites)
        res_unfav = self.client.post(f"/artifact/{art_id}/favorite/toggle", follow_redirects=True)
        self.assertEqual(res_unfav.status_code, 200)

        conn = database.get_db()
        unfav_entry = conn.execute("SELECT * FROM favorites WHERE artifact_id=?", (art_id,)).fetchone()
        self.assertIsNone(unfav_entry, "Artifact was not removed from favorites")

        # 4. Test Cascade Delete: add again, then delete artifact
        self.client.post(f"/artifact/{art_id}/favorite/toggle", follow_redirects=True)
        # Delete the artifact
        self.client.post(f"/artifact/{art_id}/delete", follow_redirects=True)

        conn = database.get_db()
        cascaded_fav = conn.execute("SELECT * FROM favorites WHERE artifact_id=?", (art_id,)).fetchone()
        conn.close()
        self.assertIsNone(cascaded_fav, "Favorite entry was not cascade-deleted when artifact was deleted")

    def test_08_civilizations_and_categories_pages(self):
        """Test civilizations and categories overview and filter subpages."""
        # Civilizations overview
        res_civ = self.client.get("/civilizations")
        self.assertEqual(res_civ.status_code, 200)
        self.assertIn("Indus Valley", res_civ.data.decode("utf-8"))

        # Categories overview
        res_cat = self.client.get("/categories")
        self.assertEqual(res_cat.status_code, 200)
        self.assertIn("Sculpture", res_cat.data.decode("utf-8"))

    def test_09_empty_name_validation(self):
        """Test that submitting an empty or whitespace-only name is rejected."""
        conn = database.get_db()
        civ_id = conn.execute("SELECT id FROM civilizations LIMIT 1").fetchone()[0]
        cat_id = conn.execute("SELECT id FROM categories LIMIT 1").fetchone()[0]
        initial_count = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
        conn.close()

        res = self.client.post("/artifact/add", data={
            "name": "   ",
            "description": "Valid description.",
            "civilization_id": str(civ_id),
            "category_id": str(cat_id)
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("Artifact name is required.", html)

        conn = database.get_db()
        new_count = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
        conn.close()
        self.assertEqual(initial_count, new_count, "Artifact with empty name should not be saved")

    def test_10_missing_civilization_validation(self):
        """Test that submitting without a civilization is rejected."""
        conn = database.get_db()
        cat_id = conn.execute("SELECT id FROM categories LIMIT 1").fetchone()[0]
        conn.close()

        res = self.client.post("/artifact/add", data={
            "name": "Valid Name",
            "description": "Valid description.",
            "civilization_id": "",
            "category_id": str(cat_id)
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("Please select a civilization.", html)

    def test_11_duplicate_name_rejection(self):
        """Test that adding an artifact with duplicate (name, civilization_id) is rejected."""
        conn = database.get_db()
        existing = conn.execute("SELECT name, civilization_id, category_id FROM artifacts LIMIT 1").fetchone()
        conn.close()

        res = self.client.post("/artifact/add", data={
            "name": existing["name"],
            "description": "Different description.",
            "civilization_id": str(existing["civilization_id"]),
            "category_id": str(existing["category_id"])
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("already exists for this civilization", html)

    def test_12_open_redirect_blocked(self):
        """Test that open redirects via malicious next URLs are sanitized and blocked."""
        conn = database.get_db()
        art_id = conn.execute("SELECT id FROM artifacts LIMIT 1").fetchone()[0]
        conn.close()

        # External full URL attack
        res_ext = self.client.post(
            f"/artifact/{art_id}/favorite/toggle",
            data={"next": "https://malicious-site.com"},
            follow_redirects=False
        )
        self.assertEqual(res_ext.status_code, 302)
        self.assertFalse(res_ext.location.startswith("https://malicious-site.com"))
        self.assertEqual(res_ext.location, f"/artifact/{art_id}")

        # Protocol-relative URL attack
        res_proto = self.client.post(
            f"/artifact/{art_id}/favorite/toggle",
            data={"next": "//evil.com/phish"},
            follow_redirects=False
        )
        self.assertEqual(res_proto.status_code, 302)
        self.assertFalse(res_proto.location.startswith("//evil.com"))
        self.assertEqual(res_proto.location, f"/artifact/{art_id}")

    def test_13_check_constraint_future_year(self):
        """Test CHECK constraints: discovery_year <= 2026 and length(trim(name)) > 0."""
        conn = database.get_db()
        civ_id = conn.execute("SELECT id FROM civilizations LIMIT 1").fetchone()[0]
        cat_id = conn.execute("SELECT id FROM categories LIMIT 1").fetchone()[0]

        # 1. Year > 2026 must violate CHECK constraint
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                """INSERT INTO artifacts (name, description, discovery_year, civilization_id, category_id)
                   VALUES ('Futuristic Relic', 'From the future', 2099, ?, ?)""",
                (civ_id, cat_id)
            )

        # 2. Blank whitespace-only name must violate CHECK constraint
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                """INSERT INTO artifacts (name, description, discovery_year, civilization_id, category_id)
                   VALUES ('   ', 'Empty name relic', 2020, ?, ?)""",
                (civ_id, cat_id)
            )

        conn.close()

    def test_14_trigger_logs_on_delete(self):
        """Test that deleting an artifact fires the AFTER DELETE trigger and records in audit log."""
        conn = database.get_db()
        civ_id = conn.execute("SELECT id FROM civilizations LIMIT 1").fetchone()[0]
        cat_id = conn.execute("SELECT id FROM categories LIMIT 1").fetchone()[0]

        # Insert a distinct artifact to delete
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO artifacts (name, description, civilization_id, category_id)
               VALUES ('Trigger Test Relic', 'To be deleted for trigger audit test', ?, ?)""",
            (civ_id, cat_id)
        )
        art_id = cur.lastrowid
        conn.commit()

        # Delete artifact via app endpoint
        res = self.client.post(f"/artifact/{art_id}/delete", follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Verify entry in deleted_artifacts_log
        log_entry = conn.execute(
            "SELECT * FROM deleted_artifacts_log WHERE artifact_id = ?",
            (art_id,)
        ).fetchone()
        conn.close()

        self.assertIsNotNone(log_entry, "Trigger did not create a row in deleted_artifacts_log")
        self.assertEqual(log_entry["name"], "Trigger Test Relic")
        self.assertIsNotNone(log_entry["deleted_at"], "Log entry timestamp must not be null")

    def test_15_exhibition_pages(self):
        """Test /exhibitions list page and /exhibitions/<id> detail page return HTTP 200."""
        # 1. Exhibitions list
        res_list = self.client.get("/exhibitions")
        self.assertEqual(res_list.status_code, 200)
        html_list = res_list.data.decode("utf-8")
        self.assertIn("Featured Exhibitions", html_list)
        self.assertIn("Echoes of the Indus", html_list)

        # 2. Exhibition detail
        conn = database.get_db()
        exh = conn.execute("SELECT id, title FROM exhibitions LIMIT 1").fetchone()
        conn.close()
        self.assertIsNotNone(exh)

        res_detail = self.client.get(f"/exhibitions/{exh['id']}")
        self.assertEqual(res_detail.status_code, 200)
        html_detail = res_detail.data.decode("utf-8")
        self.assertIn(exh["title"], html_detail)
        self.assertIn("Curated by", html_detail)

    def test_16_many_to_many_cascade(self):
        """Test many-to-many ON DELETE CASCADE on exhibition_artifacts."""
        conn = database.get_db()
        curator = conn.execute("SELECT id FROM curators LIMIT 1").fetchone()
        civ_id  = conn.execute("SELECT id FROM civilizations LIMIT 1").fetchone()[0]
        cat_id  = conn.execute("SELECT id FROM categories LIMIT 1").fetchone()[0]

        # Create temporary exhibition and artifact
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO exhibitions (title, start_date, end_date, curator_id) VALUES ('Temp Expo', '2026-01-01', '2026-02-01', ?)",
            (curator["id"],)
        )
        temp_exh_id = cur.lastrowid

        cur.execute(
            "INSERT INTO artifacts (name, description, civilization_id, category_id) VALUES ('Cascade Test Art', 'Desc', ?, ?)",
            (civ_id, cat_id)
        )
        temp_art_id = cur.lastrowid

        # Link in junction table
        cur.execute(
            "INSERT INTO exhibition_artifacts (exhibition_id, artifact_id) VALUES (?, ?)",
            (temp_exh_id, temp_art_id)
        )
        conn.commit()

        # Verify link exists
        link = conn.execute(
            "SELECT * FROM exhibition_artifacts WHERE exhibition_id=? AND artifact_id=?",
            (temp_exh_id, temp_art_id)
        ).fetchone()
        self.assertIsNotNone(link)

        # Delete exhibition -> junction row must cascade delete
        conn.execute("DELETE FROM exhibitions WHERE id=?", (temp_exh_id,))
        conn.commit()

        link_after_exh = conn.execute(
            "SELECT * FROM exhibition_artifacts WHERE exhibition_id=? AND artifact_id=?",
            (temp_exh_id, temp_art_id)
        ).fetchone()
        self.assertIsNone(link_after_exh, "exhibition_artifacts row was not cascaded on exhibition delete")

        # Now test deleting artifact cascades as well
        cur.execute(
            "INSERT INTO exhibitions (title, start_date, end_date, curator_id) VALUES ('Temp Expo 2', '2026-01-01', '2026-02-01', ?)",
            (curator["id"],)
        )
        temp_exh_id2 = cur.lastrowid
        cur.execute(
            "INSERT INTO exhibition_artifacts (exhibition_id, artifact_id) VALUES (?, ?)",
            (temp_exh_id2, temp_art_id)
        )
        conn.commit()

        conn.execute("DELETE FROM artifacts WHERE id=?", (temp_art_id,))
        conn.commit()

        link_after_art = conn.execute(
            "SELECT * FROM exhibition_artifacts WHERE exhibition_id=? AND artifact_id=?",
            (temp_exh_id2, temp_art_id)
        ).fetchone()
        self.assertIsNone(link_after_art, "exhibition_artifacts row was not cascaded on artifact delete")
        conn.close()


if __name__ == "__main__":
    unittest.main()

