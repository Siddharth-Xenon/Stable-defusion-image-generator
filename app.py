from flask import Flask, request, jsonify, render_template
import os
import uuid
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from google.cloud import storage
from config import (
    BASE_PATH,
    SECRET_KEY,
    MONGO_URL,
    DB_NAME,
    USERNAME,
    PASSWORD

)


app = Flask(__name__)

# Initialize MongoDB client
mongo_client = MongoClient(f"mongodb+srv://{USERNAME}:{PASSWORD}@stable.myeot1r.mongodb.net/")
db = mongo_client["image_data"]
collection = db["images"]

# Initialize Google Cloud Storage client
os.environ[
    "GOOGLE_APPLICATION_CREDENTIALS"
] = f"{BASE_PATH}/key/clever-obelisk-402805-a6790dbab289.json"
storage_client = storage.Client()
bucket_name = "rimorai_bucket1"
bucket = storage_client.get_bucket(bucket_name)

# Temporary storage for uploaded images
TEMP_STORAGE_FOLDER = "temp_storage/"
if not os.path.exists(TEMP_STORAGE_FOLDER):
    os.makedirs(TEMP_STORAGE_FOLDER)


# Helper function to move files to Google Cloud Storage
def move_to_cloud_storage(filename, character_name):
    blob = bucket.blob(f"{character_name}/{filename}")
    blob.upload_from_filename(os.path.join(TEMP_STORAGE_FOLDER, filename))
    return blob.public_url


# Helper function to delete files from temporary storage
def delete_from_temp_storage(filename):
    file_path = os.path.join(TEMP_STORAGE_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)


# Stores information about saved images
saved_images = {}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate-image", methods=["POST"])
def generate_image():
    data = request.form
    character_name = data["characterName"]
    prompt = data["prompt"]
    outline_image = request.files.get("outlineImage")

    # Process the image using the appropriate model based on the presence of an outline image
    # Replace this with your model logic

    # Save the generated image to temporary storage
    image_id = str(uuid.uuid4())
    if outline_image:
        filename = secure_filename(outline_image.filename)
        outline_image.save(os.path.join(TEMP_STORAGE_FOLDER, image_id + "_" + filename))
    else:
        # Generate image without an outline
        pass  # Replace with your model call

    # Store information about the image in MongoDB
    image_data = {
        "image_id": image_id,
        "character_name": character_name,
        "prompt": prompt,
    }
    collection.insert_one(image_data)

    # Return the generated image's URL and image ID
    image_url = move_to_cloud_storage(image_id + "_" + filename, character_name)
    return jsonify({"image_url": image_url, "image_id": image_id})


@app.route("/save-image", methods=["POST"])
def save_image():
    data = request.form
    image_id = data["imageID"]

    if image_id in saved_images:
        character_name = saved_images[image_id]["character_name"]
        image_url = move_to_cloud_storage(image_id, character_name)
        return jsonify({"message": "Image saved successfully", "image_url": image_url})
    else:
        return jsonify({"error": "Image not found"}, 404)


@app.route("/discard-image", methods=["DELETE"])
def discard_image():
    image_id = request.form["imageID"]
    if image_id in saved_images:
        del saved_images[image_id]
        delete_from_temp_storage(image_id)  # Delete from temporary storage
        return jsonify({"message": "Image discarded successfully"})
    else:
        return jsonify({"error": "Image not found"}, 404)


@app.route("/previous-images/<character_name>", methods=["GET"])
def previous_images(character_name):
    image_urls = [
        move_to_cloud_storage(image["image_id"], character_name)
        for image in collection.find({"character_name": character_name})
    ]
    return jsonify({"image_urls": image_urls})


if __name__ == "__main__":
    app.run(debug=True)
