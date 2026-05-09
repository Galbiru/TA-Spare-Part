from flask import Flask, render_template, request, redirect, send_file, session, flash
from reportlab.pdfgen import canvas
from openpyxl import Workbook
import cv2
import pytesseract
import mysql.connector

app = Flask(__name__)
app.secret_key = "sparepart123"

# =========================
# KONEKSI DATABASE
# =========================
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    port="3307",
    database="sparepart_db"
)

cursor = db.cursor(dictionary=True)

# =========================
# LOKASI TESSERACT
# =========================
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# =========================
# HAPUS DATA
# =========================
@app.route('/hapus/<int:id>')
def hapus(id):

    sql = "DELETE FROM hasil_scan WHERE id = %s"
    val = (id,)

    cursor.execute(sql, val)
    db.commit()

    flash('OCR berhasil diproses!', 'success')

    return redirect('/')


# =========================
# LOGIN
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin123':

            session['login'] = True

        return redirect('/')

    return render_template('login.html')


# =========================
# HOME
# =========================
@app.route('/', methods=['GET', 'POST'])
def index():

    if 'login' not in session:

        return redirect('/login')

    hasil = ""
    kategori = ""

    # =========================
    # OCR SCAN
    # =========================
    if request.method == 'POST':

        file = request.files['gambar']

        if file:

            # simpan file
            file.save(file.filename)

            # baca gambar
            img = cv2.imread(file.filename)

            # grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # OCR
            text = pytesseract.image_to_string(gray)

            # uppercase
            text = text.upper()

            hasil = text

            # klasifikasi
            if "SSD" in text:
                kategori = "SSD"

            elif "RAM" in text:
                kategori = "RAM"

            elif "LCD" in text:
                kategori = "LCD"

            else:
                kategori = "Tidak Diketahui"

            # simpan ke database
            sql = "INSERT INTO hasil_scan (hasil_ocr, kategori) VALUES (%s, %s)"
            val = (hasil, kategori)

            cursor.execute(sql, val)
            db.commit()

        # =========================
    # SEARCH
    # =========================
    search = request.args.get('search')

    if search:

        sql = """
        SELECT * FROM hasil_scan
        WHERE kategori LIKE %s
        ORDER BY id DESC
        """

        val = ("%" + search + "%",)

        cursor.execute(sql, val)

    else:

        cursor.execute("""
        SELECT * FROM hasil_scan
        ORDER BY id DESC
        """)

    riwayat = cursor.fetchall()


    # =========================
    # TOTAL DASHBOARD
    # =========================

    # total semua scan
    cursor.execute("SELECT COUNT(*) as total FROM hasil_scan")
    total_scan = cursor.fetchone()['total']

    # total SSD
    cursor.execute("""
    SELECT COUNT(*) as total 
    FROM hasil_scan 
    WHERE kategori='SSD'
    """)

    total_ssd = cursor.fetchone()['total']

    # total RAM
    cursor.execute("""
    SELECT COUNT(*) as total 
    FROM hasil_scan 
    WHERE kategori='RAM'
    """)

    total_ram = cursor.fetchone()['total']

    # total LCD
    cursor.execute("""
    SELECT COUNT(*) as total 
    FROM hasil_scan 
    WHERE kategori='LCD'
    """)

    total_lcd = cursor.fetchone()['total']

    # =========================
    # CHART DATA
    # =========================
    cursor.execute("""
    SELECT kategori, COUNT(*) as jumlah
    FROM hasil_scan
    GROUP BY kategori
    """)

    chart_data = cursor.fetchall()

    label_chart = []
    data_chart = []

    for item in chart_data:

        label_chart.append(item['kategori'])
        data_chart.append(item['jumlah'])

    # =========================
    # RENDER
    # =========================
    return render_template(
        'index.html',
        hasil=hasil,
        kategori=kategori,
        riwayat=riwayat,
        label_chart=label_chart,
        data_chart=data_chart,

        total_scan=total_scan,
        total_ssd=total_ssd,
        total_ram=total_ram,
        total_lcd=total_lcd
    )


# =========================
# EXPORT PDF
# =========================
@app.route('/export/pdf')
def export_pdf():

    cursor.execute("""
    SELECT * FROM hasil_scan
    ORDER BY id DESC
    """)

    data = cursor.fetchall()

    pdf = canvas.Canvas("riwayat_scan.pdf")

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 800, "Riwayat Scan OCR")

    y = 760

    pdf.setFont("Helvetica", 12)

    for item in data:

        text = f"""
ID: {item['id']} | 
OCR: {item['hasil_ocr']} | 
Kategori: {item['kategori']}
"""

        pdf.drawString(50, y, text)

        y -= 30

    pdf.save()

    return send_file(
        "riwayat_scan.pdf",
        as_attachment=True
    )


# =========================
# EXPORT EXCEL
# =========================
@app.route('/export/excel')
def export_excel():

    cursor.execute("""
    SELECT * FROM hasil_scan
    ORDER BY id DESC
    """)

    data = cursor.fetchall()

    wb = Workbook()
    ws = wb.active

    ws.title = "Riwayat Scan"

    # HEADER
    ws.append([
        "ID",
        "Hasil OCR",
        "Kategori",
        "Waktu Scan"
    ])

    # DATA
    for item in data:

        ws.append([
            item['id'],
            item['hasil_ocr'],
            item['kategori'],
            str(item['waktu_scan'])
        ])

    wb.save("riwayat_scan.xlsx")

    return send_file(
        "riwayat_scan.xlsx",
        as_attachment=True
    )


# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')


# =========================
# CAMERA PAGE
# =========================
@app.route('/camera')
def camera():

    return render_template('camera.html')

# =========================
# OCR CAMERA
# =========================
@app.route('/scan_camera', methods=['POST'])
def scan_camera_new():

    image = request.files['image']

    image.save('camera_capture.png')

    img = cv2.imread('camera_capture.png')

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    text = pytesseract.image_to_string(gray)

    text = text.upper()

    kategori = "Tidak Diketahui"

    if "SSD" in text:
        kategori = "SSD"

    elif "RAM" in text:
        kategori = "RAM"

    elif "LCD" in text:
        kategori = "LCD"

    # simpan database
    sql = """
    INSERT INTO hasil_scan (hasil_ocr, kategori)
    VALUES (%s, %s)
    """

    val = (text, kategori)

    cursor.execute(sql, val)
    db.commit()

    return {
        "hasil": text,
        "kategori": kategori
    }

# =========================
# RUN
# =========================
app.run(debug=True)