import sqlite3
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

app = Flask(__name__)
app.secret_key = "flask-message-secret-key"

DB_PATH = Path(__file__).parent / "messages.db"

DELETE_PASSWORD = "Blahaj"


def get_db():
    """Open a SQLite connection that returns dict-like rows."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            message TEXT NOT NULL,
            likes INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = get_db()
    # Most liked first; ties broken by newest first.
    greetings = conn.execute(
        """
        SELECT id, name, message, likes, created_at
        FROM messages
        ORDER BY likes DESC, id DESC
        """
    ).fetchall()
    conn.close()
    return render_template("index.html", greetings=greetings)


@app.route("/add", methods=["POST"])
def add():
    name = request.form.get("name", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not message:
        flash("Name and message are both required.", "error")
        return redirect(url_for("index"))

    conn = get_db()
    conn.execute(
        "INSERT INTO messages (name, message, likes, created_at) VALUES (?, ?, 0, ?)",
        (name, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()

    flash("Greeting added successfully!", "success")
    return redirect(url_for("index"))


@app.route("/like/<int:message_id>", methods=["POST"])
def like(message_id):
    # Anyone may like as many times as they want — each click is +1.
    conn = get_db()
    cur = conn.execute(
        "UPDATE messages SET likes = likes + 1 WHERE id = ?", (message_id,)
    )
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        flash("That message no longer exists.", "error")
    return redirect(url_for("index"))


@app.route("/delete/<int:message_id>", methods=["POST"])
def delete(message_id):
    if request.form.get("password", "") != DELETE_PASSWORD:
        flash("Incorrect password. The greeting was not deleted.", "error")
        return redirect(url_for("index"))

    conn = get_db()
    cur = conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        flash("That message no longer exists.", "error")
    else:
        flash("Greeting deleted.", "success")
    return redirect(url_for("index"))


@app.route("/delete_all", methods=["POST"])
def delete_all():
    if request.form.get("password", "") != DELETE_PASSWORD:
        flash("Incorrect password. Nothing was deleted.", "error")
        return redirect(url_for("index"))

    conn = get_db()
    conn.execute("DELETE FROM messages")
    conn.commit()
    conn.close()

    flash("All greetings deleted.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(port=5678)
