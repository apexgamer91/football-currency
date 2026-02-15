from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

# --- Database helper ---
def get_db():
    conn = sqlite3.connect("football_currency.db")
    conn.row_factory = sqlite3.Row
    return conn

# --- Upload config ---
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Role-based access decorator ---
def login_required(role=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if "role" not in session:
                flash("You must log in first!")
                return redirect(url_for("login"))
            if role and session["role"] != role:
                flash("Access denied!")
                return redirect(url_for("login"))
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

# --- Home ---
@app.route("/")
def home():
    return redirect(url_for("login"))

# --- Signup ---
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        profile_pic = None
        if "profile_pic" in request.files:
            file = request.files["profile_pic"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                profile_pic = filename

        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO players (username,password,balance,bank_cash,cash,fc_coin,card_limit,registration_date,profile_pic,is_banned)
                VALUES (?,?,?,?,?,?,?,datetime('now'),?,0)
            """,(username,password,1000,500,200,50,1000,profile_pic))
            conn.commit()
            flash("Signup successful! Please login.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists.")
            return redirect(url_for("signup"))
        finally:
            conn.close()
    return render_template("signup.html")

# --- Login ---
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM players WHERE username=? AND password=?", (username, password)).fetchone()
        if user:
            if user["is_banned"]:
                flash(f"You are banned by {user['banned_by'] or 'Admin'}.")
                conn.close()
                return redirect(url_for("login"))
            session["playerID"] = user["playerID"]
            session["role"] = "player"
            conn.close()
            flash("Login successful!")
            return redirect(url_for("dashboard"))

        admin = conn.execute("SELECT * FROM admins WHERE username=? AND password=?", (username, password)).fetchone()
        conn.close()
        if admin:
            session["adminID"] = admin["adminID"]
            session["role"] = "admin"
            flash("Admin login successful!")
            return redirect(url_for("admin_panel"))

        flash("Invalid credentials.")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for("login"))

# --- Player Dashboard ---
@app.route("/dashboard")
@login_required(role="player")
def dashboard():
    conn = get_db()
    user = conn.execute("SELECT * FROM players WHERE playerID=?", (session["playerID"],)).fetchone()
    conn.close()
    return render_template("dashboard.html", user=user)

# --- Profile ---
@app.route("/profile")
@login_required(role="player")
def profile():
    conn = get_db()
    user = conn.execute("SELECT * FROM players WHERE playerID=?", (session["playerID"],)).fetchone()
    conn.close()
    return render_template("profile.html", user=user)

# --- Friends ---
@app.route("/friends")
@login_required(role="player")
def friends():
    conn = get_db()
    friends = conn.execute("SELECT playerID, username FROM players WHERE playerID!=?", (session["playerID"],)).fetchall()
    conn.close()
    return render_template("friends.html", friends=friends)

# --- Player List ---
@app.route("/players")
@login_required(role="player")
def player_list():
    conn = get_db()
    players = conn.execute("SELECT playerID, username, is_banned FROM players").fetchall()
    conn.close()
    return render_template("player_list.html", players=players)

# --- Chat ---
@app.route("/chat", methods=["GET","POST"])
@login_required(role="player")
def chat():
    conn = get_db()
    if request.method=="POST":
        content = request.form["content"]
        conn.execute("INSERT INTO messages (senderID,receiverID,content,timestamp) VALUES (?,?,?,datetime('now'))",
                     (session["playerID"],0,content))
        conn.commit()
    messages = conn.execute("SELECT * FROM messages ORDER BY timestamp DESC").fetchall()
    conn.close()
    return render_template("chat.html", messages=messages)

# --- Support ---
@app.route("/support")
@login_required(role="player")
def support():
    conn = get_db()
    support = conn.execute("SELECT * FROM support").fetchall()
    conn.close()
    return render_template("support.html", support=support)

# --- Player Notice ---
@app.route("/notice")
@login_required(role="player")
def player_notice():
    conn = get_db()
    notices = conn.execute("SELECT * FROM notices ORDER BY timestamp DESC").fetchall()
    conn.close()
    return render_template("notice.html", notices=notices)

# --- Shop ---
@app.route("/shop", methods=["GET","POST"])
@login_required(role="player")
def shop():
    conn = get_db()
    if request.method == "POST":
        name = request.form["name"]
        conn.execute("""
            INSERT INTO shop_items (playerID, name, status, timestamp)
            VALUES (?, ?, 'Pending', datetime('now'))
        """, (session["playerID"], name))
        conn.commit()
    items = conn.execute("SELECT * FROM shop_items WHERE playerID=?", (session["playerID"],)).fetchall()
    conn.close()
    return render_template("shop.html", items=items)

# --- Leaderboard ---
@app.route("/leaderboard")
@login_required(role="player")
def leaderboard():
    conn = get_db()
    leaderboard = conn.execute("SELECT username, balance FROM players ORDER BY balance DESC").fetchall()
    conn.close()
    return render_template("leaderboard.html", leaderboard=leaderboard)

# --- Admin Panel ---
@app.route("/admin", methods=["GET"])
@login_required(role="admin")
def admin_panel():
    return render_template("admin_panel.html")

# --- Admin Shop ---
@app.route("/admin_shop", methods=["GET","POST"])
@login_required(role="admin")
def admin_shop():
    conn = get_db()
    if request.method == "POST":
        item_id = request.form["item_id"]
        conn.execute("UPDATE shop_items SET status='Verified' WHERE id=?", (item_id,))
        conn.commit()
    items = conn.execute("SELECT * FROM shop_items").fetchall()
    conn.close()
    return render_template("admin_shop.html", items=items)

# --- Admin Notice ---
@app.route("/admin_notice", methods=["GET","POST"])
@login_required(role="admin")
def admin_notice():
    conn = get_db()
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        conn.execute("""
            INSERT INTO notices (title, content, timestamp)
            VALUES (?, ?, datetime('now'))
        """, (title, content))
        conn.commit()
    notices = conn.execute("SELECT * FROM notices ORDER BY timestamp DESC").fetchall()
    conn.close()
    return render_template("admin_notice.html", notices=notices)

# --- Admin Players ---
@app.route("/admin_players", methods=["GET","POST"])
@login_required(role="admin")
def admin_players():
    conn = get_db()
    if request.method == "POST":
        action = request.form["action"]
        player_id = request.form["player_id"]

        if action == "ban":
            conn.execute("UPDATE players SET is_banned=1 WHERE playerID=?", (player_id,))
        elif action == "unban":
            conn.execute("UPDATE players SET is_banned=0 WHERE playerID=?", (player_id,))
        elif action == "reset_balance":
            conn.execute("UPDATE players SET balance=1000, bank_cash=500, cash=200, fc_coin=50 WHERE playerID=?", (player_id,))
        conn.commit()

    players = conn.execute("SELECT * FROM players").fetchall()
    conn.close()
    return render_template("admin_players.html", players=players)

# --- Run App ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render sets PORT
    app.run(host="0.0.0.0", port=port, debug=True)