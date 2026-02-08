from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "FCSuperKey"

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fc.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), default="player")  # player or admin
    balance = db.Column(db.Integer, default=100)
    profile_pic = db.Column(db.String(200), nullable=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)

# Helpers
def login_required(f):
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Login required")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def admin_required(f):
    def wrapper(*args, **kwargs):
        user = User.query.get(session.get("user_id"))
        if not user or user.role != "admin":
            flash("Admin access required")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# Routes
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Signup successful, please login")
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("Login successful")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out")
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    user = User.query.get(session["user_id"])
    return render_template("dashboard.html", user=user)

@app.route("/shop")
@login_required
def shop():
    items = Item.query.all()
    return render_template("shop.html", items=items)

@app.route("/buy/<int:item_id>")
@login_required
def buy(item_id):
    user = User.query.get(session["user_id"])
    item = Item.query.get(item_id)
    if user.balance >= item.price:
        user.balance -= item.price
        db.session.commit()
        flash("Purchase successful")
    else:
        flash("Not enough balance")
    return redirect(url_for("shop"))

@app.route("/friends")
@login_required
def friends():
    return render_template("friends.html")

@app.route("/chat")
@login_required
def chat():
    return render_template("chat.html")

@app.route("/support")
@login_required
def support():
    return render_template("support.html")

@app.route("/leaderboard")
@login_required
def leaderboard():
    users = User.query.order_by(User.balance.desc()).all()
    return render_template("leaderboard.html", users=users)

@app.route("/profile")
@login_required
def profile():
    user = User.query.get(session["user_id"])
    return render_template("profile.html", user=user)

# ... (imports, config, models, helpers remain the same)

# Admin Routes
@app.route("/admin")
@admin_required
def admin_panel():
    users = User.query.all()
    items = Item.query.all()
    return render_template("admin.html", users=users, items=items)

@app.route("/admin/users")
@admin_required
def admin_users():
    users = User.query.all()
    return render_template("admin_users.html", users=users)

@app.route("/admin/user/<int:user_id>/delete")
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted")
    return redirect(url_for("admin_users"))

@app.route("/admin/user/<int:user_id>/promote")
@admin_required
def promote_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.role = "admin"
        db.session.commit()
        flash("User promoted to admin")
    return redirect(url_for("admin_users"))

@app.route("/admin/items")
@admin_required
def admin_items():
    items = Item.query.all()
    return render_template("admin_items.html", items=items)

@app.route("/admin/item/add", methods=["GET", "POST"])
@admin_required
def add_item():
    if request.method == "POST":
        name = request.form["name"]
        price = int(request.form["price"])
        item = Item(name=name, price=price)
        db.session.add(item)
        db.session.commit()
        flash("Item added")
        return redirect(url_for("admin_items"))
    return render_template("add_item.html")

@app.route("/admin/item/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_item(item_id):
    item = Item.query.get(item_id)
    if request.method == "POST":
        item.name = request.form["name"]
        item.price = int(request.form["price"])
        db.session.commit()
        flash("Item updated")
        return redirect(url_for("admin_items"))
    return render_template("edit_item.html", item=item)

@app.route("/admin/item/<int:item_id>/delete")
@admin_required
def delete_item(item_id):
    item = Item.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash("Item deleted")
    return redirect(url_for("admin_items"))


# Initialize DB with sample data
@app.before_first_request
def setup():
    db.create_all()
    if not Item.query.first():
        db.session.add_all([
            Item(name="Football Jersey", price=50),
            Item(name="Boots", price=80),
            Item(name="Energy Drink", price=20)
        ])
        db.session.commit()

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)