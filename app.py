from flask import Flask, request, jsonify, render_template_string
from PIL import Image, ImageStat
import io, numpy as np, base64

app = Flask(__name__)

HTML = """
<!doctype html>
<title>Lightroom Colour Assistant</title>
<h2>Upload images for analysis</h2>
<form method=post enctype=multipart/form-data>
  <input type=file name=file multiple>
  <input type=submit value=Upload>
</form>
{% if results %}
  <h3>Results</h3>
  <pre>{{results}}</pre>
{% endif %}
"""

def analyse_image(img):
    # Resize for speed
    img = img.convert("RGB").resize((512, 512))
    arr = np.asarray(img) / 255.0
    mean = arr.mean(axis=(0,1))
    r,g,b = mean
    # Estimate white balance shift
    kelvin = 5500 + (r - b) * 2500
    tint = (g - (r+b)/2) * 100
    # Simple tone curve suggestion
    contrast = float(np.std(arr))
    curve = "soft" if contrast < 0.12 else "standard" if contrast < 0.18 else "cinematic"
    return {"kelvin": round(kelvin), "tint": round(tint,1), "tone_curve": curve}

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    results = []
    if request.method == 'POST':
        files = request.files.getlist("file")
        for f in files:
            img = Image.open(io.BytesIO(f.read()))
            data = analyse_image(img)
            results.append({f.filename: data})
    return render_template_string(HTML, results=results if results else None)

@app.route('/api', methods=['POST'])
def api():
    file = request.files['file']
    img = Image.open(io.BytesIO(file.read()))
    return jsonify(analyse_image(img))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
