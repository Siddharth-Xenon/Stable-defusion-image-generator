from flask import Flask, request, jsonify, render_template, redirect
import os
import uuid
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from google.cloud import storage
from tools import stable, controlNet

from config import (
    BASE_PATH,
    SECRET_KEY, 
    MONGO_URL, 
    DB_NAME, 
    USERNAME, 
    PASSWORD,
    controlnet_api
    )

stable_diffusion = stable.Stable()
controlnet = controlNet.ControlNet(controlnet_api)

app = Flask(__name__)
# Initialize MongoDB client
mongo_client = MongoClient(
    f"mongodb+srv://{USERNAME}:{PASSWORD}@stable.myeot1r.mongodb.net/"
)
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
TEMP_STORAGE_FOLDER = "out/"
if not os.path.exists(TEMP_STORAGE_FOLDER):
    os.makedirs(TEMP_STORAGE_FOLDER)

CHARACTERNAME = None
FILENAME = None
PATH_FILE = None


# Helper function to move files to Google Cloud Storage
def move_to_cloud_storage(filename, folder_name):
    folder_name = "".join(folder_name.split())
    blob = bucket.blob(f"{folder_name}/{filename}")
    blob.upload_from_filename(f"{PATH_FILE}")

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
    global CHARACTERNAME, FILENAME, PATH_FILE
    data = request.form
    character_name = data["characterName"]
    prompt = data["description"]
    outline_image = request.files.get("imageUpload")
    print(
        f"========================================================================\nGENERATED IMAGE\n{character_name} {prompt}\n ================================================================"
    )
    # Save the generated image to temporary storage
    image_id = str(uuid.uuid4())

    if outline_image:
        outline_image_id = str(uuid.uuid4())
        outline_filename = secure_filename(outline_image.filename)

        PATH_FILE = os.path.join(
            TEMP_STORAGE_FOLDER, outline_image_id + "_" + outline_filename
        )

        outline_image.save(PATH_FILE)
        image_url = move_to_cloud_storage(
            outline_image_id + "_" + outline_filename, "#OutlineImages"
        )
        PATH_FILE = None
        PATH_FILE, seed = controlnet.process_request(prompt, image_url)

    else:
        PATH_FILE, seed = stable_diffusion.generate_image(prompt)
        filename = f"txt2img_{seed}.png"

    # Store information about the image in MongoDB
    image_data = {
        "image_id": image_id,
        "character_name": character_name,
        "prompt": prompt,
    }
    collection.insert_one(image_data)

    CHARACTERNAME = character_name
    FILENAME = filename

    # image_url = move_to_cloud_storage(filename, character_name)
    # # # Return the generated image's URL and image ID
    # return jsonify({"image_url": image_url, "image_id": image_id})

    return render_template(
        "index.html", character_name=CHARACTERNAME, filename=FILENAME
    )


@app.route("/save-image", methods=["POST"])
def save_image():
    image_id = request.form["imageID"]

    # Check if the image with the provided image ID exists in temporary storage
    if image_id in saved_images:
        character_name = saved_images[image_id]["character_name"]
        # Move the image to Google Cloud Storage and update its status in the database
        image_url = move_to_cloud_storage(image_id, character_name)
        # You can update the image status in the database here
        return jsonify({"message": "Image saved successfully", "image_url": image_url})
    else:
        return jsonify({"error": "Image not found"}, 404)


@app.route("/discard-image", methods=["DELETE"])
def discard_image():
    print(
        "========================================================================\n\t\DISCARDED IMAGE\n ================================================================"
    )

    image_id = request.form["imageID"]

    # Check if the image with the provided image ID exists in temporary storage
    if image_id in saved_images:
        # Delete the image from temporary storage
        delete_from_temp_storage(image_id)
        # You can also update the database to reflect that the image has been discarded
        del saved_images[image_id]
        return jsonify({"message": "Image discarded successfully"})
    else:
        return jsonify({"error": "Image not found"}, 404)


@app.route("/previous-images/<character_name>", methods=["GET"])
def previous_images(character_name):
    # Query the database to find images associated with the provided character name
    image_urls = [
        move_to_cloud_storage(image["image_id"], character_name)
        for image in collection.find({"character_name": character_name})
    ]
    return jsonify({"image_urls": image_urls})


@app.route("/process", methods=["POST"])
def process():
    global FILENAME, CHARACTERNAME

    if FILENAME == None or CHARACTERNAME == None:
        return redirect("/index")

    action = request.form.get("action")

    if action == "keep":
        image_url = move_to_cloud_storage(FILENAME, CHARACTERNAME)

    file_to_delete = PATH_FILE
    if os.path.exists(file_to_delete):
        os.remove(file_to_delete)

    # Redirect back to the main page or any other desired page
    FILENAME = None
    CHARACTERNAME = None
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
