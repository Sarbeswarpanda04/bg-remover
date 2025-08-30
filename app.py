from flask import Flask, request, jsonify, render_template
from rembg import remove
from PIL import Image
import os
from io import BytesIO
import base64

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/remove-background', methods=['POST'])
def remove_background():
    if 'image' not in request.files:
        return jsonify({'status': 'error', 'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'status': 'error', 'error': 'No image selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'status': 'error', 'error': 'Invalid file type'}), 400

    try:
        # Read the image from the uploaded file
        input_image = Image.open(file.stream)

        # Ensure image is in RGBA so transparency is preserved
        if input_image.mode != 'RGBA':
            input_image = input_image.convert('RGBA')

        # Remove background
        output_image = remove(input_image)

        # Convert to base64 for preview
        buffered = BytesIO()
        output_image.save(buffered, format="PNG", optimize=True)
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({
            'status': 'success',
            'image': f'data:image/png;base64,{img_str}'
        })

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/apply-background', methods=['POST'])
def apply_background():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'error': 'No JSON payload'}), 400

        image_data = data.get('image')
        background_type = data.get('backgroundType')
        background_value = data.get('backgroundValue')
        output_format = data.get('format', 'PNG')

        if not image_data:
            return jsonify({'status': 'error', 'error': 'No image provided'}), 400

        # helper to accept data URLs or raw base64
        def _extract_bytes(s):
            if not s:
                return None
            if s.startswith('data:'):
                try:
                    return base64.b64decode(s.split(',', 1)[1])
                except Exception:
                    return None
            try:
                return base64.b64decode(s)
            except Exception:
                return None

        img_bytes = _extract_bytes(image_data)
        if img_bytes is None:
            return jsonify({'status': 'error', 'error': 'Invalid image data'}), 400

        image = Image.open(BytesIO(img_bytes))
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        result = None

        if background_type == 'color':
            try:
                bg = Image.new('RGBA', image.size, background_value)
                bg.paste(image, (0, 0), image)
                result = bg
            except Exception:
                return jsonify({'status': 'error', 'error': 'Invalid color value'}), 400

        elif background_type == 'image':
            if not background_value:
                return jsonify({'status': 'error', 'error': 'No background image provided'}), 400
            bg_bytes = _extract_bytes(background_value)
            if bg_bytes is None:
                return jsonify({'status': 'error', 'error': 'Invalid background image data'}), 400
            try:
                background = Image.open(BytesIO(bg_bytes))
                background = background.resize(image.size, Image.LANCZOS)
                if background.mode != 'RGBA':
                    background = background.convert('RGBA')
                background.paste(image, (0, 0), image)
                result = background
            except Exception:
                return jsonify({'status': 'error', 'error': 'Invalid background image'}), 400

        else:
            return jsonify({'status': 'error', 'error': 'Invalid background type'}), 400

        if result is None:
            return jsonify({'status': 'error', 'error': 'No result produced'}), 500

        # Determine output format and save accordingly
        fmt = output_format.upper()
        if fmt in ('JPG', 'JPEG'):
            out = result.convert('RGB')
            save_format = 'JPEG'
        else:
            out = result
            save_format = 'PNG'

        buffered = BytesIO()
        save_kwargs = {}
        if save_format == 'JPEG':
            save_kwargs['quality'] = 95
            save_kwargs['optimize'] = True

        out.save(buffered, format=save_format, **save_kwargs)
        data_b64 = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({'status': 'success', 'image': f'data:image/{save_format.lower()};base64,{data_b64}'})

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
