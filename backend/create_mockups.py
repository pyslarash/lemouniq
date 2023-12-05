import os
import requests
import time
from dotenv import load_dotenv
from PIL import Image
import base64

# Load environment variables from .env file
load_dotenv()

# Replace 'YOUR_API_KEY' with your actual Printful API key
api_key = os.getenv('PRINTFUL_TOKEN')
imgbb_api_key = os.getenv('IMG_BB_TOKEN')  # Replace with your imgbb API key

# Getting the filename
def get_base_filename(file_path):
    # Get the base filename without the extension
    base_filename = os.path.basename(file_path)
    filename_without_extension = os.path.splitext(base_filename)[0]
    return filename_without_extension

def upload_image_to_imgbb(image_path):
    # Set the API endpoint for imgbb
    url = "https://api.imgbb.com/1/upload"

    # Read the image file and encode as base64
    with open(image_path, "rb") as file:
        image_data = base64.b64encode(file.read()).decode('utf-8')

    # Prepare the payload with base64-encoded image data
    payload = {
        "key": imgbb_api_key,
        "image": image_data,
        "expiration": 600  # Optional: Set expiration time in seconds (e.g., 600 seconds)
    }

    # Make the POST request to imgbb
    response = requests.post(url, data=payload)

    # Check if the request was successful
    if response.status_code == 200:
        result = response.json()
        image_url = result["data"]["url"]
        print(f"Image uploaded successfully. URL: {image_url}")
        return image_url
    else:
        print(f"Image upload failed. Status Code: {response.status_code}")
        return None

def get_image_orientation(image_path):
    # Check if the image is square, vertical, or horizontal
    with Image.open(image_path) as img:
        width, height = img.size
        if width == height:
            return "square"
        elif width < height:
            return "vertical"
        else:
            return "horizontal"

def mockup_generator(image_path):
    
    filename = get_base_filename(image_path)
    print(f"Filename is {filename}")
    
    # Upload the local image to imgbb and get the image URL
    uploaded_image_url = upload_image_to_imgbb(image_path)
    if not uploaded_image_url:
        print("Image upload to imgbb failed. Aborting mockup generation.")
        return

    # Determine the image orientation
    image_orientation = get_image_orientation(image_path)
    print(f"Image Orientation: {image_orientation}")

    # Define API endpoints
    url_create_task_canvas = 'https://api.printful.com/mockup-generator/create-task/3'
    url_create_task_poster = 'https://api.printful.com/mockup-generator/create-task/171'
    url_task_status = 'https://api.printful.com/mockup-generator/task'

    # Headers including API key
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # Define option groups for canvas
    canvas_option_groups = [
        "Lifestyle",
        "Lifestyle 10",
        "Lifestyle 11",
        "Lifestyle 2",
        "Lifestyle 3",
        "Lifestyle 4",
        "Lifestyle 5",
        "Lifestyle 6",
        "Lifestyle 7",
        "Lifestyle 8",
        "Lifestyle 9",
        "Person",
        "Wall"
    ]

    # Define option groups for poster
    poster_option_groups = [
        "Flat",
        "Halloween",
        "Holiday season",
        "Lifestyle",
        "Lifestyle 10",
        "Lifestyle 2",
        "Lifestyle 3",
        "Lifestyle 4",
        "Lifestyle 5",
        "Lifestyle 6",
        "Lifestyle 7",
        "Lifestyle 8",
        "Lifestyle 9",
        "Lifestyle, Premium",
        "Person",
        "Spring/summer vibes"
    ]

    # Define variant IDs for canvas and poster based on orientation
    variant_ids = {
        "square": {"canvas": 823, "poster": 6873},
        "vertical": {"canvas": 5, "poster": 6875},
        "horizontal": {"canvas": 5, "poster": 6875}
    }

    # Prepare payload templates for canvas and poster
    payload_template = {
        "variant_ids": [],
        "format": "jpg",
        "files": [
            {
                "placement": "default",
                "image_url": uploaded_image_url
            }
        ]
    }
    
    position_settings = {
        "square": {"area_width": 1800, "area_height": 1800, "width": 1800, "height": 1800, "top": 0, "left": 0
            },
        "vertical": {"area_width": 1800, "area_height": 2400, "width": 1800, "height": 2400, "top": 0, "left": 0
            },
        "horizontal": {"area_width": 2400, "area_height": 1800, "width": 2400, "height": 1800, "top": 0, "left": 0
            }
    }

    payload_canvas = payload_template.copy()
    payload_canvas["variant_ids"] = [variant_ids[image_orientation]["canvas"]]
    payload_canvas["files"][0]["position"] = position_settings[image_orientation]
    payload_canvas["option_groups"] = canvas_option_groups
    response = requests.post(url_create_task_canvas, json=payload_canvas, headers=headers)
    handle_mockup_response(response, f"{filename}_canvas", url_task_status, headers)

    payload_poster = payload_template.copy()
    payload_poster["variant_ids"] = [variant_ids[image_orientation]["poster"]]
    payload_poster["files"][0]["position"] = position_settings[image_orientation]
    payload_poster["option_groups"] = poster_option_groups
    response = requests.post(url_create_task_poster, json=payload_poster, headers=headers)
    handle_mockup_response(response, f"{filename}_poster", url_task_status, headers)
    
# This function saves the file

def save_file(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        # Define the output path in the "processed" folder
        output_folder = os.getenv('MOCKUP_FOLDER')
        os.makedirs(output_folder, exist_ok=True)
        with open(os.path.join(output_folder, filename), 'wb') as f:
            f.write(response.content)
        print(f"Saved file: {filename}")
    else:
        print(f"Failed to download file from {url}")

def handle_mockup_response(response, product_type, url_task_status, headers):
    if response.status_code == 200:
        task_key = response.json().get("result", {}).get("task_key")
        print(f"Mockup generation task created for {product_type}. Task Key: {task_key}")

        # Poll for task completion
        for _ in range(10):  # Max 10 attempts
            task_response = requests.get(f'{url_task_status}?task_key={task_key}', headers=headers)
            task_status = task_response.json().get("result", {}).get("status")

            if task_status == "completed":
                # Extract mockups and extra files
                mockups = task_response.json().get("result", {}).get("mockups", [])
                extra_files = mockups[0].get("extra", [])
                print (f"Extra response: {extra_files}")

                # Save the default mockup
                default_mockup_url = mockups[0].get("mockup_url")
                save_file(default_mockup_url, f"{product_type}_default_mockup.jpg")

                # Iterate through extra mockups
                for j, mockup in enumerate(extra_files):
                    url_data = mockup.get("url")  # Get the URL data which might be a dictionary
                    print(f"Extra URL: {url_data}")
                    filename = f'{product_type}_mockup_{j+1}.jpg'
                    save_file(url_data, filename)

                print(f"Mockups for {product_type} saved to the 'processed' folder.")
                break
            elif task_status == "failed":
                print(f"Mockup generation task for {product_type} failed.")
                break
            else:
                print(f"Mockup generation in progress for {product_type}. Checking again in 10 seconds.")
                time.sleep(10)
    else:
        print(f"Error in creating mockup task for {product_type}: {response.status_code} - {response.text}")