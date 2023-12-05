from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from PIL import Image
import cryptography
import cv2
import numpy as np
import os
from create_mockups import mockup_generator
from description_creation import description_creation

# Load environment variables from .env file
load_dotenv()

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_uploaded_files(files):
    print("Starting the process")
    processed_data = []
    total_files = len(files)
    for idx, file in enumerate(files):
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Run through functions
            processed_file_path = metadata_strip(file_path)
            resize_image(file_path)
            mockup_generator(file_path)
            description_creation(file_path)

            # Perform image processing here and calculate processing percentage
            processing_percentage = (idx + 1) * 100 / total_files

            if processed_file_path:
                processing_percentage = (idx + 1) * 100 / total_files
                # Store processed data for each file including the processing percentage
                processed_data.append({
                    'filename': filename,
                    'file_path': processed_file_path,
                    'processing_percentage': processing_percentage
                })
            else:
                # Handle the case where processing fails
                return jsonify({'error': 'Failed to process one or more files'})

    return processed_data

# Function to upload and process the image files
def upload_file():
    if 'image' not in request.files:
        return jsonify({'error': 'No files part'})

    files = request.files.getlist('image')

    # Filter allowed files and process them
    allowed_files = [file for file in files if allowed_file(file.filename)]

    if not allowed_files:
        return jsonify({'error': 'No valid files uploaded'})

    processed_data = process_uploaded_files(allowed_files)
    
    # Return processed data as JSON response
    return jsonify({'processed_data': processed_data})

# This function rewrites metadata
def metadata_strip(file_path):
    try:
        # Open the image
        image = Image.open(file_path)

        # Strip all metadata from the image
        image_without_metadata = Image.new(image.mode, image.size)
        image_without_metadata.putdata(list(image.getdata()))

        # Add custom metadata
        image_without_metadata.info['Author'] = 'Lemouniq'
        image_without_metadata.info['Website'] = 'https://lemouniq.com'
        image_without_metadata.info['Email'] = 'info@lemouniq.com'

        # Save the processed image, overwriting the existing image
        image_without_metadata.save(file_path)

        return file_path  # Return the path to the processed image (same as input path)

    except Exception as e:
        print(f"Error processing image: {e}")
        return None

# This function resizes the file
def resize_image(input_image_path):
    try:
        # Open the original image
        original_image = Image.open(input_image_path)

        # Calculate the smaller side based on 20 inches at 300 DPI
        target_size = int(20 * 300)  # 20 inches * 300 DPI
        smaller_side = min(original_image.width, original_image.height)

        # Calculate new dimensions while maintaining aspect ratio
        new_width, new_height = original_image.size
        if smaller_side < target_size:
            # Calculate scaling factor to upscale the image
            scaling_factor = target_size / float(smaller_side)
            new_width = int(original_image.width * scaling_factor)
            new_height = int(original_image.height * scaling_factor)

        # Resize the image using nearest-neighbor interpolation (no quality loss)
        resized_image = original_image.resize((new_width, new_height), Image.NEAREST)


        # Construct new filename by appending the resized file ending to the original filename
        original_filename, original_extension = os.path.splitext(os.path.basename(input_image_path))
        resized_file_ending = os.getenv('RESIZED_FILE_ENDING')
        new_filename = f"{original_filename}{resized_file_ending}"

        # Define the output path in the "resized" folder
        output_folder = os.getenv('OUTPUT_FOLDER')
        os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(output_folder, new_filename)

        # Save the processed image as PNG in the "resized" folder
        resized_image.save(output_path, format='PNG', dpi=(300, 300))

        return output_path  # Return the path to the processed image

    except Exception as e:
        print(f"Error resizing image: {e}")
        return None
        
if __name__ == '__main__':
    app.run(debug=True, ssl_context='adhoc')
