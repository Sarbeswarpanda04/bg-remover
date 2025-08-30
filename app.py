from flask import Flask, request, jsonify, render_template, send_file
from rembg import remove
from PIL import Image
import os
import cv2
import numpy as np
from io import BytesIO
import base64

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
        # Read the image
        input_image = Image.open(file)
        
        # Convert image to RGB if it's in CMYK or other formats
        if input_image.mode not in ['RGB', 'RGBA']:
            input_image = input_image.convert('RGB')
        
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
        return jsonify({'error': str(e)}), 500

@app.route('/apply-background', methods=['POST'])
def apply_background():
    try:
        data = request.get_json()
        image_data = data.get('image')
        background_type = data.get('backgroundType')
        background_value = data.get('backgroundValue')
        output_format = data.get('format', 'PNG')
        
        # Decode base64 image
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        if background_type == 'color':
            # Create background with solid color
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            background = Image.new('RGBA', image.size, background_value)
            background.paste(image, (0, 0), image)
            result = background
        elif background_type == 'image':
            try:
                # Use custom background image
                background = Image.open(BytesIO(base64.b64decode(background_value.split(',')[1])))
                background = background.resize(image.size, Image.Resampling.LANCZOS)
                if background.mode != 'RGBA':
                    background = background.convert('RGBA')
                if image.mode != 'RGBA':
                    image = image.convert('RGBA')
                background.paste(image, (0, 0), image)
                result = background
            except Exception as e:
                return jsonify({'error': 'Invalid background image'}), 400
                
        # Convert to RGB if JPEG output is requested
        if output_format.upper() == 'JPEG':
            result = result.convert('RGB')
        
        # Convert result to base64
        buffered = BytesIO()
        result.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            'status': 'success',
            'image': f'data:image/png;base64,{img_str}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
