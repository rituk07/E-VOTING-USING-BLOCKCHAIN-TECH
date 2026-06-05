from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
import base64
from time import time
from face_auth import verify_identity, is_duplicate_face, get_face_roi
from blockchain_logic import Blockchain

app = Flask(__name__)
app.secret_key = "voterchain_ultimate_secret"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Directories
FACE_DIR = "static/faces"
if not os.path.exists(FACE_DIR):
    os.makedirs(FACE_DIR)

# Initialize Blockchain
blockchain = Blockchain()

def get_db():
    conn = sqlite3.connect("evoting.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        voter_id = request.form.get('voter_id')
        password = request.form.get('password')
        image_data = request.form.get('image_data')

        if not all([name, voter_id, password, image_data]):
            flash("All fields and face capture are required!", "error")
            return redirect(url_for('register'))

        # 1. Temporarily save face for check
        temp_path = os.path.join(FACE_DIR, f"temp_{voter_id}.jpg")
        try:
            img_bytes = base64.b64decode(image_data.split(',')[1])
            with open(temp_path, "wb") as f:
                f.write(img_bytes)
        except:
            flash("Invalid image data received.", "error")
            return redirect(url_for('register'))

        # 2. Security Check: Face detection
        if get_face_roi(temp_path) is None:
            os.remove(temp_path)
            flash("No clear face detected! Please look directly at the camera.", "error")
            return redirect(url_for('register'))

        # 3. Security Check: Duplicate Face Detection (Global)
        if is_duplicate_face(temp_path, FACE_DIR):
            os.remove(temp_path)
            flash("FRAUD DETECTED: This person is already registered with another account!", "error")
            return redirect(url_for('register'))

        # 4. Success: Save permanently and add to DB
        final_path = os.path.join(FACE_DIR, f"{voter_id}.jpg")
        os.rename(temp_path, final_path)

        try:
            with get_db() as conn:
                conn.execute("INSERT INTO users (name, voter_id, password, face_path) VALUES (?, ?, ?, ?)",
                            (name, voter_id, password, final_path))
                conn.commit()
            flash("Registration successful! Welcome to VoterChain.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            if os.path.exists(final_path): os.remove(final_path)
            flash("Voter ID already exists!", "error")
        except Exception as e:
            flash(f"System Error: {str(e)}", "error")

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        voter_id = request.form.get('voter_id')
        password = request.form.get('password')

        with get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE voter_id=? AND password=?", (voter_id, password)).fetchone()

        if user:
            session.clear()
            session['user'] = voter_id
            session['name'] = user['name']
            flash(f"Login successful. Welcome, {user['name']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials. Please try again.", "error")

    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE voter_id=?", (session['user'],)).fetchone()
    return render_template("dashboard.html", user=user)

@app.route('/verify')
def verify():
    if 'user' not in session: return redirect(url_for('login'))
    with get_db() as conn:
        user = conn.execute("SELECT voted FROM users WHERE voter_id=?", (session['user'],)).fetchone()
    if user['voted']:
        flash("You have already cast your vote!", "error")
        return redirect(url_for('dashboard'))
    return render_template("verify.html")

@app.route('/api/verify', methods=['POST'])
def api_verify():
    if 'user' not in session: return jsonify({"status": "error", "message": "Session expired"}), 401
    
    data = request.json
    if not data or 'image' not in data: return jsonify({"status": "error", "message": "No data"}), 400

    temp_path = f"static/verify_{session['user']}.jpg"
    try:
        img_bytes = base64.b64decode(data['image'].split(',')[1])
        with open(temp_path, "wb") as f: f.write(img_bytes)
    except: return jsonify({"status": "error", "message": "Upload failed"}), 400

    with get_db() as conn:
        user = conn.execute("SELECT face_path FROM users WHERE voter_id=?", (session['user'],)).fetchone()
    
    result = verify_identity(user['face_path'], temp_path)
    if os.path.exists(temp_path): os.remove(temp_path)

    if result == "MATCH":
        session['is_verified'] = True
        return jsonify({"status": "success", "message": "Identity Verified!"})
    else:
        return jsonify({"status": "error", "message": result})

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if 'user' not in session: return redirect(url_for('login'))
    if not session.get('is_verified'):
        flash("Please verify your identity first!", "error")
        return redirect(url_for('verify'))

    if request.method == 'POST':
        candidate = request.form.get('candidate')
        if not candidate:
            flash("Please select a candidate.", "error")
            return redirect(url_for('vote'))

        # Blockchain entry
        blockchain.add_vote(session['user'], candidate) # simple version

        with get_db() as conn:
            conn.execute("UPDATE users SET voted=1 WHERE voter_id=?", (session['user'],))
            conn.commit()

        session.pop('is_verified', None)
        flash(f"Vote cast successfully for {candidate}!", "success")
        return redirect(url_for('dashboard'))

    return render_template("vote.html")

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)