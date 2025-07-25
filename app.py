import os
from flask import Flask, render_template, request, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
from docx import Document
from fpdf import FPDF
import uuid
import shutil
import unicodedata  

#  tesseract.exe location
pytesseract.pytesseract.tesseract_cmd = r"D:\Tesseract\tesseract.exe"

#  Upload folder
UPLOAD_FOLDER = r"D:\ocr_web_app\uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Language support
LANGUAGES = {'English': 'eng', 'Hindi': 'hin', 'Bengali': 'ben'}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        lang = request.form['lang']
        lang_code = LANGUAGES.get(lang, 'eng')

        files = request.files.getlist('images')
        all_text = ""
        session_id = str(uuid.uuid4())
        session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        os.makedirs(session_folder, exist_ok=True)

        for file in files:
            filename = secure_filename(file.filename)
            path = os.path.join(session_folder, filename)
            file.save(path)

            image = Image.open(path)
            text = pytesseract.image_to_string(image, lang=lang_code)
            all_text += text + "\n"

        #  Word
        word_path = os.path.join(session_folder, 'output.docx')
        doc = Document()
        doc.add_paragraph(all_text)
        doc.save(word_path)

        #  PDF 
        pdf_path = os.path.join(session_folder, 'output.pdf')
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for line in all_text.split('\n'):
            clean_line = unicodedata.normalize('NFKD', line).encode('ascii', 'ignore').decode('ascii')
            pdf.multi_cell(0, 10, clean_line)

        pdf.output(pdf_path)

        return render_template('index.html', text=all_text, session_id=session_id)

    return render_template('index.html')

@app.route('/download/<session_id>/<filename>')
def download(session_id, filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], session_id, filename)
    response = send_file(path, as_attachment=True)

    # Auto-del session folder
    shutil.rmtree(os.path.join(app.config['UPLOAD_FOLDER'], session_id), ignore_errors=True)
    return response

@app.route('/clear', methods=['POST'])
def clear():
    shutil.rmtree(app.config['UPLOAD_FOLDER'], ignore_errors=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
