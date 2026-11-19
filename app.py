
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "agenda_contactos_2026"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def conectar_db():
    conexion = sqlite3.connect("agenda.db")
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_tabla():
    conexion = conectar_db()
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS contactos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            correo TEXT,
            foto TEXT
        )
    """)
    conexion.commit()
    conexion.close()


def extension_permitida(nombre):
    return (
        "." in nombre
        and nombre.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/")
def inicio():
    conexion = conectar_db()
    contactos = conexion.execute(
        "SELECT * FROM contactos ORDER BY nombre"
    ).fetchall()
    conexion.close()

    return render_template("index.html", contactos=contactos)


@app.route("/agregar", methods=["GET", "POST"])
def agregar():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        correo = request.form.get("correo", "").strip()

        if not nombre:
            flash("El nombre es obligatorio.")
            return redirect(url_for("agregar"))

        foto = None
        archivo = request.files.get("foto")

        if archivo and archivo.filename:
            if not extension_permitida(archivo.filename):
                flash("Formato de imagen no permitido.")
                return redirect(url_for("agregar"))

            nombre_foto = secure_filename(archivo.filename)
            nombre_foto = f"{os.urandom(8).hex()}_{nombre_foto}"
            archivo.save(os.path.join(UPLOAD_FOLDER, nombre_foto))
            foto = nombre_foto

        conexion = conectar_db()
        conexion.execute(
            """INSERT INTO contactos
            (nombre, telefono, correo, foto)
            VALUES (?, ?, ?, ?)""",
            (nombre, telefono, correo, foto)
        )
        conexion.commit()
        conexion.close()

        return redirect(url_for("inicio"))

    return render_template("agregar.html")


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    conexion = conectar_db()
    contacto = conexion.execute(
        "SELECT * FROM contactos WHERE id = ?", (id,)
    ).fetchone()

    if contacto is None:
        conexion.close()
        return redirect(url_for("inicio"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        correo = request.form.get("correo", "").strip()
        foto = contacto["foto"]

        archivo = request.files.get("foto")

        if not nombre:
            conexion.close()
            flash("El nombre es obligatorio.")
            return redirect(url_for("editar", id=id))

        if archivo and archivo.filename:
            if not extension_permitida(archivo.filename):
                conexion.close()
                flash("Formato de imagen no permitido.")
                return redirect(url_for("editar", id=id))

            if foto:
                ruta_anterior = os.path.join(UPLOAD_FOLDER, foto)
                if os.path.exists(ruta_anterior):
                    os.remove(ruta_anterior)

            nombre_foto = secure_filename(archivo.filename)
            nombre_foto = f"{os.urandom(8).hex()}_{nombre_foto}"
            archivo.save(os.path.join(UPLOAD_FOLDER, nombre_foto))
            foto = nombre_foto

        conexion.execute(
            """UPDATE contactos
            SET nombre = ?, telefono = ?, correo = ?, foto = ?
            WHERE id = ?""",
            (nombre, telefono, correo, foto, id)
        )

        conexion.commit()
        conexion.close()

        return redirect(url_for("inicio"))

    conexion.close()
    return render_template("editar.html", contacto=contacto)


@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    conexion = conectar_db()
    contacto = conexion.execute(
        "SELECT * FROM contactos WHERE id = ?", (id,)
    ).fetchone()

    if contacto:
        if contacto["foto"]:
            ruta = os.path.join(UPLOAD_FOLDER, contacto["foto"])
            if os.path.exists(ruta):
                os.remove(ruta)

        conexion.execute(
            "DELETE FROM contactos WHERE id = ?", (id,)
        )
        conexion.commit()

    conexion.close()
    return redirect(url_for("inicio"))


if __name__ == "__main__":
    crear_tabla()
    app.run(debug=True)
