import os
from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


@app.route("/")
def index():
    categoria_filtro = request.args.get("categoria") or None

    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if categoria_filtro:
        cur.execute(
            "SELECT id, descripcion, monto, categoria, fecha FROM gastos "
            "WHERE categoria = %s ORDER BY fecha DESC;",
            (categoria_filtro,),
        )
    else:
        cur.execute(
            "SELECT id, descripcion, monto, categoria, fecha FROM gastos "
            "ORDER BY fecha DESC;"
        )
    gastos = cur.fetchall()

    if categoria_filtro:
        cur.execute(
            "SELECT COALESCE(SUM(monto), 0) AS total FROM gastos WHERE categoria = %s;",
            (categoria_filtro,),
        )
    else:
        cur.execute("SELECT COALESCE(SUM(monto), 0) AS total FROM gastos;")
    total = cur.fetchone()["total"]

    cur.execute(
        "SELECT DISTINCT categoria FROM gastos WHERE categoria IS NOT NULL "
        "AND categoria != '' ORDER BY categoria;"
    )
    categorias = [row["categoria"] for row in cur.fetchall()]

    cur.close()
    conn.close()
    return render_template(
        "index.html",
        gastos=gastos,
        total=total,
        categorias=categorias,
        categoria_filtro=categoria_filtro,
    )


@app.route("/agregar", methods=["POST"])
def agregar():
    descripcion = request.form.get("descripcion")
    monto = request.form.get("monto")
    categoria = request.form.get("categoria")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO gastos (descripcion, monto, categoria) VALUES (%s, %s, %s);",
        (descripcion, monto, categoria),
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("index"))


@app.route("/eliminar/<int:gasto_id>", methods=["POST"])
def eliminar(gasto_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM gastos WHERE id = %s;", (gasto_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=8000)