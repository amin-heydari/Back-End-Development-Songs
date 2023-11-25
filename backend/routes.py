from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
from flask import Flask, jsonify


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OK"})

@app.route("/count")
def count():
    """Return length of data."""
    count = db.songs.count_documents({})  # Count all documents
    return jsonify({"count": count}), 200

@app.route("/song", methods=["GET"])
def songs():
    """Return all songs."""
    songs_cursor = db.songs.find({})
    list_of_songs = [parse_json(song) for song in songs_cursor]  # Convert cursor to a list
    return jsonify({"songs": list_of_songs}), 200

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    """Return a song by its ID."""
    song = db.songs.find_one({"id": id})
    if not song:
        return jsonify({"message": "song with id not found"}), 404
    return jsonify(parse_json(song)), 200


@app.route("/song", methods=["POST"])
def create_song():
    song_data = request.json
    if db.songs.find_one({"id": song_data["id"]}):  # Check if song with given id exists
        return jsonify({"Message": f"song with id {song_data['id']} already present"}), 302
    result = db.songs.insert_one(song_data)  # Insert the new song
    return jsonify({"inserted id": str(result.inserted_id)}), 201

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    song_data = request.json
    song = db.songs.find_one({"id": id})
    if not song:
        return jsonify({"message": "song not found"}), 404
    
    update_result = db.songs.update_one(
        {"id": id}, 
        {"$set": song_data}
    )

    if update_result.modified_count == 0:
        return jsonify({"message": "song found, but nothing updated"}), 200

    updated_song = db.songs.find_one({"id": id})
    return jsonify(parse_json(updated_song)), 200


@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    delete_result = db.songs.delete_one({"id": id})
    if delete_result.deleted_count == 0:
        return jsonify({"message": "song not found"}), 404
    
    return '', 204  # HTTP 204 No Content
