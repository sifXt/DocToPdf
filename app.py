from flask import Flask, request, send_file, render_template, jsonify
from werkzeug.utils import secure_filename
import os
from docx import Document
from fpdf import FPDF

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file and file.filename.endswith('.docx'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            pdf_path = convert_to_pdf(file_path, filename)
            return jsonify({'download_url': f'/download/{os.path.basename(pdf_path)}'}), 200
        else:
            return jsonify({'error': 'Unsupported file format. Please upload a .docx file'}), 400

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(app.config['CONVERTED_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


def convert_to_pdf(docx_path, original_filename):
    try:
        pdf = FPDF()
        pdf.add_page()

        # Add a Unicode-compatible font
        pdf.add_font('DejaVu', '', 'fonts/DejaVuSans.ttf', uni=True)
        pdf.set_font("DejaVu", size=12)

        # Read .docx content
        doc = Document(docx_path)
        for paragraph in doc.paragraphs:
            # Add text to the PDF, handling Unicode characters
            pdf.multi_cell(0, 10, txt=paragraph.text)

        # Save as .pdf
        pdf_filename = original_filename.replace('.docx', '.pdf')
        pdf_path = os.path.join(app.config['CONVERTED_FOLDER'], pdf_filename)
        pdf.output(pdf_path)

        return pdf_path
    except Exception as e:
        raise Exception(f"PDF conversion failed: {str(e)}")


if __name__ == '__main__':
    app.run(debug=True)
