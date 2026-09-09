from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

DATABASE = "tickets.db"


# -------------------------------
# Database Connection
# -------------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------------
# Create Database Table
# -------------------------------
def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            tags TEXT,
            created_at TEXT NOT NULL,
            response_deadline TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# -------------------------------
# Calculate Response Deadline
# -------------------------------
def calculate_response_deadline(created_at):
    """
    Returns exactly 3 business days after created_at.
    Business days = Monday to Friday.
    """

    current_date = created_at
    business_days = 0

    while business_days < 3:
        current_date += timedelta(days=1)

        # Monday = 0, Sunday = 6
        if current_date.weekday() < 5:
            business_days += 1

    return current_date


# -------------------------------
# POST /tickets
# Create New Ticket
# -------------------------------
@app.route("/tickets", methods=["POST"])
def create_ticket():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON data is required"
        }), 400

    title = data.get("title")
    description = data.get("description")
    status = data.get("status", "Open")
    tags = data.get("tags", "")

    if not title or not description:
        return jsonify({
            "error": "title and description are required"
        }), 400

    allowed_status = ["Open", "In Progress", "Closed"]

    if status not in allowed_status:
        return jsonify({
            "error": "Invalid status. Use Open, In Progress, or Closed."
        }), 400

    # Current date and time
    created_at = datetime.now()

    # Calculate deadline
    deadline = calculate_response_deadline(created_at)

    conn = get_db_connection()

    cursor = conn.execute("""
        INSERT INTO tickets
        (title, description, status, tags, created_at, response_deadline)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        title,
        description,
        status,
        tags,
        created_at.isoformat(),
        deadline.isoformat()
    ))

    conn.commit()

    ticket_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "message": "Ticket created successfully",
        "ticket": {
            "id": ticket_id,
            "title": title,
            "description": description,
            "status": status,
            "tags": tags,
            "created_at": created_at.isoformat(),
            "response_deadline": deadline.isoformat()
        }
    }), 201


# -------------------------------
# GET /tickets
# Get All Tickets
# -------------------------------
@app.route("/tickets", methods=["GET"])
def get_tickets():

    conn = get_db_connection()

    tickets = conn.execute("""
        SELECT * FROM tickets
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    ticket_list = []

    for ticket in tickets:
        ticket_list.append(dict(ticket))

    return jsonify(ticket_list)


# -------------------------------
# GET /tickets/<id>
# Get Specific Ticket
# -------------------------------
@app.route("/tickets/<int:ticket_id>", methods=["GET"])
def get_ticket(ticket_id):

    conn = get_db_connection()

    ticket = conn.execute("""
        SELECT * FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    conn.close()

    if ticket is None:
        return jsonify({
            "error": "Ticket not found"
        }), 404

    return jsonify(dict(ticket))


# -------------------------------
# POST /tickets/web-submit
# Legacy Web Form
# -------------------------------
@app.route("/tickets/web-submit", methods=["POST"])
def web_submit():

    data = request.form

    title = data.get("title")
    description = data.get("description")
    status = data.get("status", "Open")
    tags = data.get("tags", "")

    if not title or not description:
        return "<h1>Title and description are required!</h1>", 400

    created_at = datetime.now()
    deadline = calculate_response_deadline(created_at)

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO tickets
        (title, description, status, tags, created_at, response_deadline)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        title,
        description,
        status,
        tags,
        created_at.isoformat(),
        deadline.isoformat()
    ))

    conn.commit()
    conn.close()

    return "<h1>Ticket Created Successfully!</h1>"


# -------------------------------
# Run Application
# -------------------------------
if __name__ == "__main__":
    init_db()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
