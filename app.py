from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date
from database import init_db, get_db

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key"

init_db()


def calculate_age_in_months(birth_date, measurement_date):
    months = (
        (measurement_date.year - birth_date.year) * 12
        + (measurement_date.month - birth_date.month)
    )
    if measurement_date.day < birth_date.day:
        months -= 1
    return max(months, 0)


def valid_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


@app.template_filter("date_id")
def date_id(value):
    return value.strftime("%d-%m-%Y") if value else ""


@app.route("/")
def index():
    db = get_db()
    children = db.execute("""
        SELECT c.*,
               (SELECT height FROM measurements m
                WHERE m.child_id = c.id
                ORDER BY measurement_date DESC, id DESC LIMIT 1) AS latest_height,
               (SELECT weight FROM measurements m
                WHERE m.child_id = c.id
                ORDER BY measurement_date DESC, id DESC LIMIT 1) AS latest_weight,
               (SELECT measurement_date FROM measurements m
                WHERE m.child_id = c.id
                ORDER BY measurement_date DESC, id DESC LIMIT 1) AS latest_date
        FROM children c
        ORDER BY c.name
    """).fetchall()
    db.close()
    return render_template("index.html", children=children)


@app.route("/anak/tambah", methods=["GET", "POST"])
def tambah_anak():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        gender = request.form.get("gender", "")
        birth_date = request.form.get("birth_date", "")
        parent_name = request.form.get("parent_name", "").strip()
        notes = request.form.get("notes", "").strip()

        birth = valid_date(birth_date)

        if not name or gender not in ("L", "P") or birth is None:
            flash("Nama, jenis kelamin, dan tanggal lahir wajib diisi dengan benar.", "danger")
            return render_template("tambah_anak.html")

        if birth > date.today():
            flash("Tanggal lahir tidak boleh di masa depan.", "danger")
            return render_template("tambah_anak.html")

        db = get_db()
        db.execute(
            """
            INSERT INTO children (name, gender, birth_date, parent_name, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, gender, birth_date, parent_name, notes),
        )
        db.commit()
        db.close()

        flash("Data anak berhasil ditambahkan.", "success")
        return redirect(url_for("index"))

    return render_template("tambah_anak.html")


@app.route("/anak/<int:child_id>/edit", methods=["GET", "POST"])
def edit_anak(child_id):
    db = get_db()
    child = db.execute(
        "SELECT * FROM children WHERE id = ?", (child_id,)
    ).fetchone()

    if child is None:
        db.close()
        return "Anak tidak ditemukan", 404

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        gender = request.form.get("gender", "")
        birth_date = request.form.get("birth_date", "")
        parent_name = request.form.get("parent_name", "").strip()
        notes = request.form.get("notes", "").strip()

        birth = valid_date(birth_date)

        if not name or gender not in ("L", "P") or birth is None:
            flash("Nama, jenis kelamin, dan tanggal lahir wajib diisi dengan benar.", "danger")
            db.close()
            return render_template("edit_anak.html", child=child)

        if birth > date.today():
            flash("Tanggal lahir tidak boleh di masa depan.", "danger")
            db.close()
            return render_template("edit_anak.html", child=child)

        measurements = db.execute(
            "SELECT id, measurement_date FROM measurements WHERE child_id = ?",
            (child_id,),
        ).fetchall()

        for m in measurements:
            measurement = valid_date(m["measurement_date"])
            if measurement and measurement < birth:
                flash(
                    "Tanggal lahir baru tidak boleh setelah salah satu tanggal pengukuran. "
                    "Ubah/hapus pengukuran yang lebih lama terlebih dahulu.",
                    "danger",
                )
                db.close()
                return render_template("edit_anak.html", child=child)

        db.execute(
            """
            UPDATE children
            SET name = ?, gender = ?, birth_date = ?, parent_name = ?, notes = ?
            WHERE id = ?
            """,
            (name, gender, birth_date, parent_name, notes, child_id),
        )

        # Jika tanggal lahir berubah, usia (bulan) semua riwayat dihitung ulang.
        for m in measurements:
            measurement = valid_date(m["measurement_date"])
            if measurement:
                age_months = calculate_age_in_months(birth, measurement)
                db.execute(
                    "UPDATE measurements SET age_months = ? WHERE id = ?",
                    (age_months, m["id"]),
                )

        db.commit()
        db.close()

        flash("Data anak berhasil diperbarui.", "success")
        return redirect(url_for("detail_anak", child_id=child_id))

    db.close()
    return render_template("edit_anak.html", child=child)


@app.route("/anak/<int:child_id>/hapus", methods=["POST"])
def hapus_anak(child_id):
    db = get_db()
    child = db.execute(
        "SELECT name FROM children WHERE id = ?", (child_id,)
    ).fetchone()

    if child is None:
        db.close()
        return "Anak tidak ditemukan", 404

    db.execute("DELETE FROM measurements WHERE child_id = ?", (child_id,))
    db.execute("DELETE FROM children WHERE id = ?", (child_id,))
    db.commit()
    db.close()

    flash(f'Data anak "{child["name"]}" dan seluruh riwayat pengukurannya berhasil dihapus.', "success")
    return redirect(url_for("index"))


@app.route("/anak/<int:child_id>")
def detail_anak(child_id):
    db = get_db()
    child = db.execute(
        "SELECT * FROM children WHERE id = ?", (child_id,)
    ).fetchone()
    measurements = db.execute(
        """
        SELECT * FROM measurements
        WHERE child_id = ?
        ORDER BY measurement_date ASC, id ASC
        """,
        (child_id,),
    ).fetchall()
    db.close()

    if child is None:
        return "Anak tidak ditemukan", 404

    today = date.today()
    birth = date.fromisoformat(child["birth_date"])
    current_age = calculate_age_in_months(birth, today)

    return render_template(
        "anak.html",
        child=child,
        measurements=measurements,
        current_age=current_age,
    )


@app.route("/anak/<int:child_id>/pengukuran/tambah", methods=["GET", "POST"])
def tambah_pengukuran(child_id):
    db = get_db()
    child = db.execute(
        "SELECT * FROM children WHERE id = ?", (child_id,)
    ).fetchone()

    if child is None:
        db.close()
        return "Anak tidak ditemukan", 404

    if request.method == "POST":
        measurement_date = request.form.get("measurement_date", "")
        height = request.form.get("height", "")
        weight = request.form.get("weight", "")
        notes = request.form.get("notes", "").strip()

        measurement = valid_date(measurement_date)
        birth = valid_date(child["birth_date"])

        try:
            height_value = float(height)
            weight_value = float(weight)
        except (TypeError, ValueError):
            height_value = -1
            weight_value = -1

        if (
            measurement is None
            or birth is None
            or measurement < birth
            or height_value <= 0
            or weight_value <= 0
        ):
            flash(
                "Tanggal, tinggi, dan berat harus diisi dengan benar. "
                "Tanggal pengukuran tidak boleh sebelum tanggal lahir.",
                "danger",
            )
            db.close()
            return render_template(
                "tambah_pengukuran.html",
                child=child,
                today=measurement_date or date.today().isoformat(),
            )

        existing = db.execute(
            """
            SELECT id FROM measurements
            WHERE child_id = ? AND measurement_date = ?
            """,
            (child_id, measurement_date),
        ).fetchone()

        if existing:
            flash(
                "Sudah ada pengukuran untuk tanggal tersebut. "
                "Gunakan menu Edit pada pengukuran yang sudah ada.",
                "danger",
            )
            db.close()
            return render_template(
                "tambah_pengukuran.html",
                child=child,
                today=measurement_date,
            )

        age_months = calculate_age_in_months(birth, measurement)

        db.execute(
            """
            INSERT INTO measurements
            (child_id, measurement_date, age_months, height, weight, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                child_id,
                measurement_date,
                age_months,
                height_value,
                weight_value,
                notes,
            ),
        )
        db.commit()
        db.close()

        flash("Pengukuran berhasil disimpan.", "success")
        return redirect(url_for("detail_anak", child_id=child_id))

    db.close()
    return render_template(
        "tambah_pengukuran.html",
        child=child,
        today=date.today().isoformat(),
    )


@app.route(
    "/anak/<int:child_id>/pengukuran/<int:measurement_id>/edit",
    methods=["GET", "POST"],
)
def edit_pengukuran(child_id, measurement_id):
    db = get_db()

    child = db.execute(
        "SELECT * FROM children WHERE id = ?", (child_id,)
    ).fetchone()
    measurement = db.execute(
        """
        SELECT * FROM measurements
        WHERE id = ? AND child_id = ?
        """,
        (measurement_id, child_id),
    ).fetchone()

    if child is None or measurement is None:
        db.close()
        return "Data tidak ditemukan", 404

    if request.method == "POST":
        measurement_date = request.form.get("measurement_date", "")
        height = request.form.get("height", "")
        weight = request.form.get("weight", "")
        notes = request.form.get("notes", "").strip()

        new_date = valid_date(measurement_date)
        birth = valid_date(child["birth_date"])

        try:
            height_value = float(height)
            weight_value = float(weight)
        except (TypeError, ValueError):
            height_value = -1
            weight_value = -1

        if (
            new_date is None
            or birth is None
            or new_date < birth
            or height_value <= 0
            or weight_value <= 0
        ):
            flash(
                "Tanggal, tinggi, dan berat harus diisi dengan benar. "
                "Tanggal pengukuran tidak boleh sebelum tanggal lahir.",
                "danger",
            )
            db.close()
            return render_template(
                "edit_pengukuran.html",
                child=child,
                measurement=measurement,
            )

        existing = db.execute(
            """
            SELECT id FROM measurements
            WHERE child_id = ? AND measurement_date = ? AND id != ?
            """,
            (child_id, measurement_date, measurement_id),
        ).fetchone()

        if existing:
            flash("Sudah ada pengukuran lain pada tanggal tersebut.", "danger")
            db.close()
            return render_template(
                "edit_pengukuran.html",
                child=child,
                measurement=measurement,
            )

        age_months = calculate_age_in_months(birth, new_date)

        db.execute(
            """
            UPDATE measurements
            SET measurement_date = ?, age_months = ?, height = ?, weight = ?, notes = ?
            WHERE id = ? AND child_id = ?
            """,
            (
                measurement_date,
                age_months,
                height_value,
                weight_value,
                notes,
                measurement_id,
                child_id,
            ),
        )
        db.commit()
        db.close()

        flash("Pengukuran berhasil diperbarui.", "success")
        return redirect(url_for("detail_anak", child_id=child_id))

    db.close()
    return render_template(
        "edit_pengukuran.html",
        child=child,
        measurement=measurement,
    )


@app.route("/anak/<int:child_id>/pengukuran/<int:measurement_id>/hapus", methods=["POST"])
def hapus_pengukuran(child_id, measurement_id):
    db = get_db()
    db.execute(
        "DELETE FROM measurements WHERE id = ? AND child_id = ?",
        (measurement_id, child_id),
    )
    db.commit()
    db.close()

    flash("Pengukuran berhasil dihapus.", "success")
    return redirect(url_for("detail_anak", child_id=child_id))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
