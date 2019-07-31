#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import magic
import threading
import imagehash
from PIL import Image
from time import sleep
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

# Temp, here to simulate polling client-server
tempGlobalStatus = []

app = Flask(__name__)
# Set database file to "Database.db" in current directory
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Database.db'
# Remove annoying warning messange until next releas of SQLAlchemy
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Table "Files" in SQLite DB
class Files(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    path = db.Column(db.String(512), nullable = False) # unique = True
    hashes = db.Column(db.String(512), nullable = False)
    file_name = db.Column(db.String(512), nullable = False)
    file_size = db.Column(db.Integer, nullable = True)
    image_size = db.Column(db.String(128), nullable = True)
    capture_time = db.Column(db.String(256), nullable = True)
    
    def __repr__(self):
        return "<Files {0},{1},{2},{3},{4}>".format(self.path, self.hashes, self.file_size, self.image_size, self.capture_time)

# Create all tables into DB
db.create_all()

# Index endpoint, display all images collected in database
@app.route('/')
def index():
    item = db.session.query(Files).all()
    return render_template("index.html",dblist=item)

# Add a path to database
@app.route('/add', methods=['POST'])
def add():
    path = request.form['path']
    imagesList = exploreDir(path)
    # Process image and add to db
    threading.Thread(target=hashList, args=(imagesList,)).start()
    return render_template("add.html", path=path)

# Explorer path to get a list of all its files and subdirectories
def exploreDir(path):
    for root, directories, filenames in os.walk(path, topdown=True):
        # Process file into root
        for filename in filenames:
            filepath = os.path.join(root,filename)
            if isImage(filepath):
                yield filepath
        # Then process subdirectories
        for subdir in directories:
            exploreDir(subdir)

# Return true if filepath is a supported image format
def isImage(filepath):
    fullSupportedFormats = ['gif', 'jp2', 'jpeg', 'pcx', 'png', 'tiff', 'x-ms-bmp', 'x-portable-pixmap', 'x-xbitmap']
    try:
        mime = magic.from_file(filepath, mime=True)
        return mime.rsplit('/', 1)[1] in fullSupportedFormats
    except IndexError:
        return False

# Hash a list of images
def hashList(imagesList):
    tempList = list()
    for path in imagesList:
        tempList.append(path)
        tempGlobalStatus.append(path)
    
    for path in tempList:
        print(path)
        data = hashImage(path)
        db.session.add(Files(path = data[0],
                            hashes = data[1],
                            file_name = data[2],
                            file_size = data[3],
                            image_size = data[4],
                            capture_time = data[5]))
        tempGlobalStatus.remove(path)
        try:
            db.session.commit()
            # Create symbolic link in static/symlinks
            # os.symlink(src, dest)
        except IntegrityError as e:
            print(e)
        try:
            os.symlink(path, "static/symlinks/{0}".format(os.path.basename(path)))
        except FileExistsError as e:
            print(e)

# Calculate hash of an image and return other usefull data
def hashImage(file):
    try:
        hashes = []
        img = Image.open(file)
        file_name = os.path.basename(file)
        file_size = get_file_size(file)
        image_size = get_image_size(img)
        capture_time = get_capture_time(img)

        # hash the image 4 times and rotate it by 90 degrees each time
        for angle in [ 0, 90, 180, 270 ]:
            if angle > 0:
                turned_img = img.rotate(angle, expand=True)
            else:
                turned_img = img
            hashes.append(str(imagehash.phash(turned_img)))

        hashes = ''.join(sorted(hashes))

        #print("Hashed {0}".format(file))
        return file, hashes, file_name, file_size, image_size, capture_time
    except OSError:
        #print("Unable to open {0}".format(file))
        return None

# Get image size in byte format
def get_file_size(path):
    try:
        return os.path.getsize(path)
    except FileNotFoundError:
        return 0

# Get image size in pixel (width x height)
def get_image_size(img):
    return "{} x {}".format(*img.size)

# Extract capture time from an image
def get_capture_time(img):
    try:
        exif = {
            ExifTags.TAGS[k]: v
            for k, v in img._getexif().items()
            if k in ExifTags.TAGS
        }
        return exif["DateTimeOriginal"]
    except:
        return "Time unknown"

# Get status of current working threads
@app.route("/add/status")
def status():
    return json.dumps(tempGlobalStatus)

# Remove an image from database, not local disk
@app.route("/remove/<int:id>")
def remove(id):
    print(id)
    return "ok"

# Start Flask web server
app.run(debug = True)