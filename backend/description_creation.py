from openai import OpenAI
from dotenv import load_dotenv
import os
import re

# Load environment variables from .env file
load_dotenv()

client = OpenAI()

# Function to create a directory if it doesn't exist
def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        
# Function to get the keyword from a filename
def get_keyword_from_filename(file_path):
    # Get the base filename without the extension
    base_filename = os.path.basename(file_path)
    keyword = re.sub(r'[-_ ]', ' ', os.path.splitext(base_filename)[0])
    
    return keyword

# Writing meta description
def meta_description(keyword):
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a highly-skilled SEO marketer who is focused on amazing meta descriptions."},
        {"role": "user", "content": f"Write a general meta description for a keyword '{keyword}' for a downloadable digital print. No longer than 150 characters."}
    ]
    )

    return(completion.choices[0].message.content)

# Writing product description   
def product_description(keyword):
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a highly-skilled SEO marketer who is focused on amazing SEO descriptions."},
        {"role": "user", "content": f"Write a lengthy description for a keyword '{keyword}' for a downloadable digital print created by AI. It should be a minimum of 400 words. Do not overuse the keyword, but use it enough times. The print will have 300dpi with the shorter edge of maximum 20 inches. Do not mention dimensions otherwise as some prints might be square or rectangular and I'm using this description for all of them. Use human-like writing style and avoid detection by ChatGPT detectors."}
    ]
    )

    return(completion.choices[0].message.content)

# Combining everything
def description_creation(file_name):
    keyword = get_keyword_from_filename(file_name)
    meta = meta_description(keyword)
    product = product_description(keyword)
    descriptions_dir = os.getenv('DESCRIPTION_FOLDER')

    # Create the "descriptions" directory if it doesn't exist
    create_directory(descriptions_dir)

    # Create a file with the keyword as the filename
    filename = f"{descriptions_dir}/{keyword}.txt"
    
    # Save meta and product descriptions to the file
    with open(filename, 'w') as file:
        file.write("Meta Description:\n")
        file.write(meta)
        file.write("\n\nProduct Description:\n")
        file.write(product)

# Example usage
keyword = "abstract bird"
description_creation(keyword)