from flask import Flask, render_template, render_template_string, request, redirect, url_for
import sqlite3
import os
import pandas as pd

app = Flask(__name__)

DB_PATH = 'outpass.db'
DATA_PATH = 'Dataset.csv.xlsx'

# -------------------------------
# Load Dataset Once
# -------------------------------
df = pd.read_excel(DATA_PATH)
df.columns = [c.strip().replace(" ", "_").upper() for c in df.columns]

# -------------------------------
# Home Page
# -------------------------------
@app.route('/')
def welcome():
    return render_template('home.html')

# -------------------------------
# Enrollment Verification Page
# -------------------------------
@app.route('/verify', methods=['GET', 'POST'])
def verify_enrollment():
    html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Enrollment Verification | GRW Polytechnic Tasgaon</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
            body {
                margin: 0; padding: 0; height: 100vh;
                font-family: 'Poppins', sans-serif;
                background-image: url("{{ url_for('static', filename='college_bg.jpg') }}");
                background-size: cover; background-position: center;
                display: flex; justify-content: center; align-items: center;
                overflow: hidden;
            }
            body::before {
                content: ""; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.3); backdrop-filter: blur(8px); z-index: 0;
            }
            .container {
                position: relative; z-index: 1;
                background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(15px);
                border-radius: 20px; padding: 40px 50px; text-align: center; width: 380px;
                box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4); animation: fadeIn 1s ease-in-out;
            }
            h1 { font-size: 22px; color: #ffffff; margin-bottom: 10px; }
            h2 { font-size: 18px; color: #d9f1ff; margin-bottom: 25px; }
            input { width: 100%; padding: 12px; border: none; border-radius: 8px;
                    margin-bottom: 20px; outline: none; font-size: 15px; text-align: center;
                    background: rgba(255,255,255,0.25); color: #fff; }
            input::placeholder { color: #e6e6e6; }
            button { width: 100%; padding: 12px; border: none; border-radius: 8px;
                     background: linear-gradient(90deg, #007bff, #00c6ff);
                     color: white; font-weight: bold; font-size: 15px; cursor: pointer;
                     transition: 0.3s; }
            button:hover { transform: scale(1.05); background: linear-gradient(90deg, #006be6, #00aaff); }
            .footer { margin-top: 15px; font-size: 13px; color: #e1e1e1; }
            @keyframes fadeIn { from {opacity:0; transform:translateY(30px);} to {opacity:1; transform:translateY(0);} }
        </style>
        <script> function showAlert(msg){ alert(msg); } </script>
    </head>
    <body>
        <div class="container">
            <h1>🏫 Government Residence Women Polytechnic, Tasgaon</h1>
            <h2>Enrollment Verification</h2>
            <form method="POST">
                <input type="text" name="enroll" placeholder="Enter Enrollment Number" required>
                <button type="submit">Verify Enrollment</button>
            </form>
            <div class="footer">© 2025 GRW Polytechnic Tasgaon</div>
        </div>
        {% if alert %}<script>showAlert("{{ alert }}");</script>{% endif %}
    </body>
    </html>
    '''

    if request.method == 'POST':
        enroll = request.form['enroll'].strip()
        student = df.loc[df['ENROLLMENT_NO'].astype(str) == str(enroll)]
        if not student.empty:
            return redirect(url_for('outpass_form', enroll=enroll))
        else:
            return render_template_string(html, alert="❌ Invalid Enrollment Number! Try again.")
    return render_template_string(html)

# -------------------------------
# Outpass Form
# -------------------------------
@app.route('/form', methods=['GET', 'POST'])
def outpass_form():
    enroll_no = request.args.get('enroll', None)
    if request.method == 'POST':
        enroll_no = request.form['enroll']
        from_date = request.form['from_date']
        to_date = request.form['to_date']
        reason = request.form['reason']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS OutpassRequests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Enrollment_No TEXT,
                From_Date TEXT,
                To_Date TEXT,
                Reason TEXT,
                Status TEXT
            )
        ''')
        cursor.execute("""
            INSERT INTO OutpassRequests (Enrollment_No, From_Date, To_Date, Reason, Status)
            VALUES (?, ?, ?, ?, ?)
        """, (enroll_no, from_date, to_date, reason, "Pending"))
        conn.commit()
        conn.close()

        return redirect(url_for('success_page', enroll=enroll_no,
                                from_date=from_date, to_date=to_date, reason=reason))
    return render_template('index.html', enroll_no=enroll_no)

# -------------------------------
# Success Page (with student image + check status link)
# -------------------------------
@app.route('/success/<enroll>')
def success_page(enroll):
    student = df.loc[df['ENROLLMENT_NO'].astype(str) == str(enroll)]
    if student.empty:
        return "<h3 style='color:red;'>Student not found!</h3>"

    record = student.iloc[0].to_dict()
    from_date = request.args.get('from_date', 'N/A')
    to_date = request.args.get('to_date', 'N/A')
    reason = request.args.get('reason', 'N/A')

    img_folder = os.path.join('static', 'IMAGE_DATASET COTY')
    image_found = None
    for ext in ['.jpg', '.jpeg', '.png']:
        possible_path = os.path.join(img_folder, f"{enroll}{ext}")
        if os.path.exists(possible_path):
            image_found = possible_path
            break
    if not image_found:
        image_found = os.path.join('static', 'default.jpg')
    img_url = '/' + image_found.replace('\\', '/')

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Outpass Submitted | GRW Polytechnic</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
            body {{ margin:0; height:100vh; font-family:'Poppins', sans-serif;
                   background-image:url('/static/college_bg.jpg'); background-size:cover;
                   display:flex; justify-content:center; align-items:center; }}
            body::before {{ content:""; position:absolute; top:0; left:0; right:0; bottom:0;
                            background: rgba(0,0,0,0.4); backdrop-filter: blur(10px); z-index:0; }}
            .card {{ position:relative; z-index:1; background: rgba(255,255,255,0.15);
                     backdrop-filter: blur(20px); border-radius: 25px; padding:50px 70px;
                     width:650px; color:#fff; text-align:center; box-shadow:0 8px 40px rgba(0,0,0,0.6); }}
            img {{ width:130px; height:130px; border-radius:50%; border:3px solid white; object-fit:cover; margin-bottom:20px; }}
            h2 {{ font-size:24px; margin-bottom:15px; color:#fff; }}
            table {{ width:100%; color:#f2f2f2; text-align:left; border-collapse:collapse; font-size:16px; margin:0 auto; }}
            td {{ padding:8px 0; }}
            a.btn {{
                background: linear-gradient(90deg,#007bff,#00c6ff);
                color:white; border:none;
                padding:12px 25px; border-radius:10px;
                font-weight:bold; cursor:pointer; margin:10px 5px;
                text-decoration:none; display:inline-block;
                transition:0.3s;
            }}
            a.btn:hover {{ transform:scale(1.05); background: linear-gradient(90deg,#006be6,#00aaff); }}
        </style>
    </head>
    <body>
        <div class="card">
            <img src="{img_url}" alt="Student Photo">
            <h2>{record.get('NAME','N/A')}</h2>
            <table>
                <tr><td><b>Enrollment No:</b></td><td>{enroll}</td></tr>
                <tr><td><b>Roll No:</b></td><td>{record.get('ROLL_NO','N/A')}</td></tr>
                <tr><td><b>Department:</b></td><td>{record.get('DEPARTMENT','N/A')}</td></tr>
                <tr><td><b>Year:</b></td><td>{record.get('YEAR','N/A')}</td></tr>
                <tr><td><b>Academic Year:</b></td><td>{record.get('YEAR.1','N/A')}</td></tr>
                <tr><td><b>Student Phone:</b></td><td>{record.get('STUDENT_PHONE_NO','N/A')}</td></tr>
                <tr><td><b>Parent Phone:</b></td><td>{record.get('PARENTS_PHONE_NO','N/A')}</td></tr>
                <tr><td colspan="2"><hr></td></tr>
                <tr><td><b>From Date:</b></td><td>{from_date}</td></tr>
                <tr><td><b>To Date:</b></td><td>{to_date}</td></tr>
                <tr><td><b>Reason:</b></td><td>{reason}</td></tr>
            </table>

            <!-- 3 Buttons -->
            <a href="/warden" class="btn">📨 Submit (Go to Warden)</a>
            <a href="/" class="btn">🏠 Back to Home</a>
            <a href="/check_status?enroll={enroll}" class="btn">📋 Check Status</a>

        </div>
    </body>
    </html>
    """
    return html

# -------------------------------
# Warden Dashboard
# -------------------------------
@app.route('/warden')
def warden_dashboard():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM OutpassRequests")
    rows = cursor.fetchall()
    conn.close()

    enriched = []
    for r in rows:
        req_id, enroll, from_date, to_date, reason, status = r
        student = df.loc[df['ENROLLMENT_NO'].astype(str) == str(enroll)]
        if not student.empty:
            rec = student.iloc[0]
            name = rec.get('NAME', 'N/A')
            student_phone = rec.get('STUDENT_PHONE_NO', 'N/A')
            parent_phone = rec.get('PARENTS_PHONE_NO', 'N/A')
        else:
            name, student_phone, parent_phone = 'N/A', 'N/A', 'N/A'

        enriched.append({
            'id': req_id, 'enroll': enroll, 'name': name,
            'student_phone': student_phone, 'parent_phone': parent_phone,
            'from_date': from_date, 'to_date': to_date,
            'reason': reason, 'status': status
        })

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Warden Dashboard</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f0f7ff; }
            h2 { text-align: center; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: center; font-size:14px; }
            th { background: #007bff; color: white; }
            tr:nth-child(even) { background: #f9f9f9; }
            a.call-btn, a.whatsapp-btn {
                display: inline-block; color:white; font-weight:bold; padding:6px 10px; border-radius:6px;
                text-decoration:none; margin:2px; transition:0.2s;
            }
            a.call-btn { background: linear-gradient(90deg,#28a745,#4cd964); }
            a.whatsapp-btn { background: linear-gradient(90deg,#25D366,#128C7E); }
            a.call-btn:hover, a.whatsapp-btn:hover { transform: scale(1.05); }
            input { padding:8px; width:300px; margin-bottom:10px; }
        </style>
        <script>
            function searchTable() {
                var input = document.getElementById("searchBox").value.toLowerCase();
                var rows = document.querySelectorAll("#reqTable tbody tr");
                rows.forEach(row => { row.style.display = row.innerText.toLowerCase().includes(input) ? "" : "none"; });
            }
        </script>
    </head>
    <body>
        <h2>🏫 Warden Dashboard - Outpass Requests</h2>
        <input id="searchBox" placeholder="🔍 Search..." onkeyup="searchTable()">
        <table id="reqTable">
          <thead>
            <tr>
              <th>ID</th><th>Enrollment</th><th>Name</th><th>Student Contact</th><th>Parent Contact</th>
              <th>From</th><th>To</th><th>Reason</th><th>Status</th><th>Action</th>
            </tr>
          </thead>
          <tbody>
          {% for r in enriched %}
            <tr>
              <td>{{ r.id }}</td>
              <td>{{ r.enroll }}</td>
              <td>{{ r.name }}</td>
              <td>
                {% if r.student_phone != 'N/A' %}
                  <a href="tel:{{ r.student_phone }}" class="call-btn">📞 Call</a>
                  <a href="https://wa.me/{{ r.student_phone }}" target="_blank" class="whatsapp-btn">💬 WhatsApp</a><br>
                  <small>{{ r.student_phone }}</small>
                {% else %} N/A {% endif %}
              </td>
              <td>
                {% if r.parent_phone != 'N/A' %}
                  <a href="tel:+91{{ r.parent_phone }}" class="call-btn">📞 Call</a>
                  <a href="https://wa.me/91{{ r.parent_phone }}" target="_blank" class="whatsapp-btn">💬 WhatsApp</a><br>
                  <small>+91 {{ r.parent_phone }}</small>
                {% else %} N/A {% endif %}
              </td>
              <td>{{ r.from_date }}</td>
              <td>{{ r.to_date }}</td>
              <td>{{ r.reason }}</td>
              <td>{{ r.status }}</td>
              <td>
                {% if r.status == 'Pending' %}
                  <a href="/update_status/{{ r.id }}/Approved">Approve</a> |
                  <a href="/update_status/{{ r.id }}/Rejected">Reject</a>
                {% else %} - {% endif %}
              </td>
            </tr>
          {% endfor %}
          </tbody>
        </table>
    </body>
    </html>
    """, enriched=enriched)

# -------------------------------
# Update Status
# -------------------------------
@app.route('/update_status/<int:req_id>/<status>')
def update_status(req_id, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE OutpassRequests SET Status=? WHERE id=?", (status, req_id))
    conn.commit()
    conn.close()
    return redirect(url_for('warden_dashboard'))

# -------------------------------
# Check Status (Student view)
# -------------------------------
@app.route('/check_status', methods=['GET', 'POST'])
def check_status():
    results = None
    enroll = request.args.get('enroll','')
    if request.method == 'POST':
        enroll = request.form['enroll'].strip()
    if enroll:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT From_Date, To_Date, Reason, Status FROM OutpassRequests WHERE Enrollment_No=?", (enroll,))
        rows = cursor.fetchall()
        conn.close()
        results = [{'from_date': r[0], 'to_date': r[1], 'reason': r[2], 'status': r[3]} for r in rows]

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Check Outpass Status</title>
        <style>
            body { font-family: Arial; padding:20px; background:#f0f7ff; }
            h2 { text-align:center; }
            table { border-collapse: collapse; width:60%; margin:20px auto; }
            th, td { border:1px solid #ccc; padding:10px; text-align:center; }
            th { background:#007bff; color:white; }
            td.status-approved { color:green; font-weight:bold; }
            td.status-rejected { color:red; font-weight:bold; }
            td.status-pending { color:orange; font-weight:bold; }
            input, button { padding:10px; margin:5px; }
        </style>
    </head>
    <body>
        <h2>Check Your Outpass Status</h2>
        <form method="POST" style="text-align:center;">
            <input type="text" name="enroll" placeholder="Enter Enrollment No" value="{{ enroll }}" required>
            <button type="submit">Check Status</button>
        </form>
        {% if results %}
        <table>
            <tr><th>From</th><th>To</th><th>Reason</th><th>Status</th></tr>
            {% for r in results %}
            <tr>
                <td>{{ r.from_date }}</td>
                <td>{{ r.to_date }}</td>
                <td>{{ r.reason }}</td>
                <td class="status-{{ r.status|lower }}">{{ r.status }}</td>
            </tr>
            {% endfor %}
        </table>
        {% elif enroll %}<p style="text-align:center;">No outpass found for this enrollment number.</p>{% endif %}
    </body>
    </html>
    """
    return render_template_string(html, results=results, enroll=enroll)

# -------------------------------
# Run App
# -------------------------------
if __name__ == '__main__':
    app.run(debug=True)
