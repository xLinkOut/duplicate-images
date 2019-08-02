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
from sqlalchemy import func
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
    path = db.Column(db.String(512))
    name = db.Column(db.String(512))
    hashes = db.Column(db.String(512))
    file_size = db.Column(db.Integer)
    image_size = db.Column(db.String(128))
    capture_time = db.Column(db.String(256))
    
    def __repr__(self):
        return "<Files {0},{1},{2},{3},{4},{5},{6}>".format(self.id,self.path,self.name,self.hashes,self.file_size,self.image_size,self.capture_time)

# Create all tables into DB
db.create_all()

# Index endpoint, display all images collected in database
@app.route('/')
@app.route('/dashboard/')
def index():
   return render_template("dashboard.html")

# Add a path to database
@app.route('/add', methods=['POST'])
def add():
    path = request.form['path']
    imagesList = exploreDir(path)
    # Check if folder exists
    # Process image and add to db
    threading.Thread(target=hashList, args=(imagesList,)).start()
    return "1" # Return negative status if something fail

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
        db.session.add(Files(path = data['path'],
                            name = data['name'],
                            hashes = data['hashes'],
                            file_size = data['file_size'],
                            image_size = data['image_size'],
                            capture_time = data['capture_time']))
        tempGlobalStatus.remove(path)
        
        try:
            db.session.commit()
        except IntegrityError as e:
            print(e)
        
        try:
            # Create symbolic link in static/symlinks
            # os.symlink(src, dest)
            os.symlink(path, "static/symlinks/{0}".format(data['name']))
        except FileExistsError as e:
            print(e)

# Calculate hash of an image and return other usefull data
def hashImage(filepath):
    try:
        img = Image.open(filepath)
        hashes = []
        # First hash image in its original orientation
        hashes.append(str(imagehash.phash(img)))
        # Then rotate image by 90, 180 and 270 degree and append its hashes
        for angle in [ 90, 180, 270 ]:
            hashes.append(str(imagehash.phash(img.rotate(angle, expand=True))))

        #print("Hashed {0}".format(file))
        return {
            'path': os.path.dirname(filepath),
            'name': os.path.basename(filepath),
            'hashes': ''.join(sorted(hashes)),
            'file_size': get_file_size(filepath),
            'image_size': get_image_size(img),
            'capture_time': get_capture_time(img)
        }
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
    if db.session.query(Files).filter(Files.id == id).delete():
        db.session.commit()
        return "1"
    else:
        return "0"

# Compare hashes to find duplicate images
@app.route("/duplicates/")
def find():
    duplicates = db.session.query(Files) \
                .filter(Files.hashes.in_(db.session.query(Files.hashes) \
                                        .group_by(Files.hashes) \
                                        .having(func.count() > 1))) \
                .order_by(Files.hashes) \
                .all()
    response = []
    for dup in duplicates:
        response.append({
            'id': dup.id,
            'path': dup.path,
            'name': dup.name,
            'hashes': dup.hashes,
            'file_size': dup.file_size,
            'image_size': dup.image_size,
            'capture_time': dup.capture_time
        })
    
    return render_template("find.html", duplicates=response)

@app.route('/folders/')
def folders():
    response = {}
    paths = db.session.query(Files.path).distinct().all()
    for path, in paths: #, because sqlalchemy return a namedtuple even with a single column
        imagesInPath = db.session.query(Files).filter(Files.path == path).all()
        response[path] = []
        for image in imagesInPath:
            response[path].append({
                'id': image.id,
                'path': image.path,
                'name': image.name,
                'hashes': image.hashes,
                'file_size': image.file_size,
                'image_size': image.image_size,
                'capture_time': image.capture_time
            })

    return render_template("folders.html",data=response)

# Start Flask web server
app.run(debug = True)