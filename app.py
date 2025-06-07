from flask import Flask, request, render_template, send_file
from generate_rams import generate_all_rams
import zipfile
import os

app = Flask(__name__)

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/generate', methods=['POST'])
def generate():
    answers = [request.form.get(f"q{i+1}") for i in range(20)]
    output_paths = generate_all_rams(answers)

    zip_path = "/tmp/RAMS_Output.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for path in output_paths:
            zipf.write(path, os.path.basename(path))

    return send_file(zip_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
