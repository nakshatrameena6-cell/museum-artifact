"""
generate_er.py — Generates a clean, professional ER Diagram image matching the Museum Artifact Explorer schema.
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_er_diagram(output_path="docs/er_diagram.png"):
    fig, ax = plt.subplots(figsize=(16, 11), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 11)
    ax.axis("off")
    fig.patch.set_facecolor("#FAF8F5")

    # Title
    ax.text(8, 10.5, "MUSEUM ARTIFACT EXPLORER — ENTITY RELATIONSHIP (ER) DIAGRAM",
            ha="center", va="center", fontsize=15, fontweight="bold", color="#2C241E",
            fontfamily="sans-serif")
    ax.text(8, 10.15, "Relational Schema: 7 Core Tables + Audit Log Table + View & Trigger Architecture",
            ha="center", va="center", fontsize=10.5, color="#796B5F", fontfamily="sans-serif")

    # Tables definitions: (name, x, y, width, height, columns)
    tables = [
        {
            "name": "civilizations",
            "x": 0.8, "y": 6.8, "w": 3.8, "h": 2.6,
            "badge": "Parent Entity (1:N)",
            "cols": [
                ("PK", "id", "INTEGER AUTOINCREMENT"),
                ("UQ", "name", "TEXT NOT NULL"),
                ("", "region", "TEXT"),
                ("", "period", "TEXT"),
                ("", "description", "TEXT")
            ]
        },
        {
            "name": "categories",
            "x": 0.8, "y": 3.4, "w": 3.8, "h": 2.3,
            "badge": "Lookup Entity (1:N)",
            "cols": [
                ("PK", "id", "INTEGER AUTOINCREMENT"),
                ("UQ", "name", "TEXT NOT NULL"),
                ("", "description", "TEXT")
            ]
        },
        {
            "name": "artifacts",
            "x": 5.8, "y": 3.6, "w": 4.4, "h": 5.8,
            "badge": "Core Entity (Hub)",
            "cols": [
                ("PK", "id", "INTEGER AUTOINCREMENT"),
                ("REQ", "name", "TEXT (CHECK trim > 0)"),
                ("REQ", "description", "TEXT NOT NULL"),
                ("", "period", "TEXT"),
                ("", "discovery_location", "TEXT"),
                ("CHK", "discovery_year", "INT (CHECK <= 2026)"),
                ("", "material", "TEXT"),
                ("", "image_url", "TEXT"),
                ("FK", "civilization_id", "INT NOT NULL -> civilizations(id)"),
                ("FK", "category_id", "INT NOT NULL -> categories(id)"),
                ("UQ", "(name, civilization_id)", "UNIQUE COMPOSITE"),
                ("", "created_at", "TEXT DEFAULT datetime('now')")
            ]
        },
        {
            "name": "favorites",
            "x": 1.2, "y": 0.6, "w": 3.8, "h": 2.1,
            "badge": "User Bookmark (1:1 / 0:1)",
            "cols": [
                ("PK", "id", "INTEGER AUTOINCREMENT"),
                ("FK,UQ", "artifact_id", "INT UNIQUE ON DELETE CASCADE"),
                ("", "created_at", "TEXT DEFAULT datetime('now')")
            ]
        },
        {
            "name": "curators",
            "x": 11.4, "y": 7.4, "w": 3.8, "h": 2.2,
            "badge": "Staff Entity (1:N)",
            "cols": [
                ("PK", "id", "INTEGER AUTOINCREMENT"),
                ("REQ", "name", "TEXT NOT NULL"),
                ("UQ", "email", "TEXT NOT NULL UNIQUE"),
                ("", "specialization", "TEXT")
            ]
        },
        {
            "name": "exhibitions",
            "x": 11.4, "y": 4.0, "w": 3.8, "h": 2.6,
            "badge": "Curated Event",
            "cols": [
                ("PK", "id", "INTEGER AUTOINCREMENT"),
                ("UQ", "title", "TEXT NOT NULL UNIQUE"),
                ("", "start_date", "TEXT NOT NULL"),
                ("CHK", "end_date", "TEXT (CHECK >= start_date)"),
                ("FK", "curator_id", "INT -> curators(id) ON DEL SET NULL")
            ]
        },
        {
            "name": "exhibition_artifacts",
            "x": 11.4, "y": 0.8, "w": 3.8, "h": 2.4,
            "badge": "Many-to-Many Association",
            "cols": [
                ("PFK", "exhibition_id", "INT FK -> exhibitions(id) CASCADE"),
                ("PFK", "artifact_id", "INT FK -> artifacts(id) CASCADE"),
                ("PK", "(exhibition_id, artifact_id)", "COMPOSITE PRIMARY KEY")
            ]
        },
        {
            "name": "deleted_artifacts_log",
            "x": 6.1, "y": 0.6, "w": 3.8, "h": 2.2,
            "badge": "Audit Trail (Trigger Populated)",
            "cols": [
                ("PK", "id", "INTEGER AUTOINCREMENT"),
                ("", "artifact_id", "INTEGER NOT NULL"),
                ("", "name", "TEXT NOT NULL"),
                ("", "deleted_at", "TEXT DEFAULT datetime('now')")
            ]
        }
    ]

    header_color = "#3D312A"
    body_color = "#FFFFFF"
    border_color = "#C8B9A6"

    for t in tables:
        x, y, w, h = t["x"], t["y"], t["w"], t["h"]
        # Outer card box with shadow effect
        shadow = patches.FancyBboxPatch((x+0.05, y-0.05), w, h, boxstyle="round,pad=0.08,rounding_size=0.12",
                                        facecolor="#E2DCD5", edgecolor="none", zorder=1)
        ax.add_patch(shadow)

        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.12",
                                     facecolor=body_color, edgecolor=border_color, linewidth=1.5, zorder=2)
        ax.add_patch(box)

        # Header box
        header_h = 0.55
        header_box = patches.FancyBboxPatch((x, y + h - header_h), w, header_h,
                                            boxstyle="round,pad=0.08,rounding_size=0.08",
                                            facecolor=header_color, edgecolor="none", zorder=3)
        ax.add_patch(header_box)

        # Table title & badge
        ax.text(x + 0.15, y + h - 0.28, t["name"].upper(), fontsize=9.5, fontweight="bold",
                color="#F5EFE6", va="center", zorder=4)
        ax.text(x + w - 0.1, y + h - 0.28, t["badge"], fontsize=7, color="#E6C280",
                ha="right", va="center", zorder=4, fontstyle="italic")

        # Columns
        col_y = y + h - header_h - 0.25
        for tag, cname, ctype in t["cols"]:
            if tag:
                # tag badge
                tag_color = "#8B2635" if "PK" in tag else ("#1D4E89" if "FK" in tag else "#5A4E3C")
                ax.text(x + 0.15, col_y, f"[{tag}]", fontsize=7.2, fontweight="bold",
                        color=tag_color, va="center", zorder=4)
            ax.text(x + 0.85, col_y, cname, fontsize=8, fontweight="bold" if "PK" in tag or "REQ" in tag else "normal",
                    color="#2C241E", va="center", zorder=4)
            ax.text(x + w - 0.12, col_y, ctype, fontsize=7.2, color="#796B5F",
                    ha="right", va="center", zorder=4)
            col_y -= 0.33

    # Connectors / Relationships with arrows
    def draw_arrow(start, end, label=""):
        arrow = patches.FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=14,
                                        color="#A45A2A", linewidth=1.8, linestyle="solid", zorder=5)
        ax.add_patch(arrow)
        if label:
            mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
            ax.text(mx, my + 0.12, label, fontsize=7.5, fontweight="bold",
                    color="#A45A2A", ha="center", va="center",
                    bbox=dict(boxstyle="square,pad=0.1", fc="#FAF8F5", ec="none"), zorder=6)

    # 1. Civilizations (1) -> Artifacts (N)
    draw_arrow((4.7, 7.8), (5.7, 7.8), "1 : N")
    # 2. Categories (1) -> Artifacts (N)
    draw_arrow((4.7, 4.6), (5.7, 5.2), "1 : N")
    # 3. Artifacts (1) -> Favorites (0..1)
    draw_arrow((6.4, 3.5), (5.1, 1.8), "1 : 1 (ON DEL CASCADE)")
    # 4. Curators (1) -> Exhibitions (N)
    draw_arrow((13.3, 7.3), (13.3, 6.7), "1 : N (SET NULL)")
    # 5. Exhibitions (1) -> Exhibition_Artifacts (M:N junction)
    draw_arrow((13.3, 3.9), (13.3, 3.3), "1 : N (CASCADE)")
    # 6. Artifacts (1) -> Exhibition_Artifacts (M:N junction)
    draw_arrow((10.3, 5.0), (11.3, 2.4), "1 : N (CASCADE)")
    # 7. Artifacts (Trigger) -> deleted_artifacts_log
    draw_arrow((8.0, 3.5), (8.0, 2.9), "AFTER DELETE TRIGGER")

    # Legend / Architecture Footer
    footer_text = (
        "Schema Highlights:\n"
        "• View: `artifact_details` joins artifacts + civilizations + categories\n"
        "• Indexes: `idx_artifacts_name` on artifacts(name), `idx_artifacts_civ_cat` on (civilization_id, category_id)\n"
        "• Constraints: CHECK(discovery_year <= 2026), CHECK(length(trim(name)) > 0), UNIQUE(name, civilization_id)"
    )
    ax.text(0.8, 0.25, footer_text, fontsize=8, color="#5A4E3C", va="bottom",
            bbox=dict(boxstyle="round,pad=0.3", fc="#EFECE6", ec="#C8B9A6", lw=1))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"[OK] ER diagram saved successfully to: {output_path}")

if __name__ == "__main__":
    generate_er_diagram("docs/er_diagram.png")
