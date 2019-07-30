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

# Temp, here to simulate polling client-server
tempGlobalStatus = []

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Database.db'
# Remove annoying warning messange until next releas of SQLAlchemy
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Table "Files" in SQLite DB
class Files(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    path = db.Column(db.String(512),unique = True, nullable = False)
    hashes = db.Column(db.String(512), nullable = False)
    file_size = db.Column(db.Integer, nullable = True)
    image_size = db.Column(db.String(128), nullable = True)
    capture_time = db.Column(db.String(256), nullable = True)
    
    def __repr__(self):
        return "<Files %s>" % self.path

# Create all tables into DB
#db.create_all()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/add', methods=['POST'])
def add():
    path = request.form['path']
    imagesList = exploreDir(path)
    # Process image and add to db
    threading.Thread(target=hashList,args=(imagesList,)).start()
    return render_template("add.html", path=path)

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

def isImage(filepath):
    full_supported_formats = ['gif', 'jp2', 'jpeg', 'pcx', 'png', 'tiff', 'x-ms-bmp', 'x-portable-pixmap', 'x-xbitmap']
    try:
        mime = magic.from_file(filepath, mime=True)
        return mime.rsplit('/', 1)[1] in full_supported_formats
    except IndexError:
        return False

def hashList(imagesList):
    tempList = list()
    for path in imagesList:
        tempList.append(path)
        tempGlobalStatus.append(path)
    
    for path in tempList:
        print(path)
        data = hashImage(path)
        sleep(3)
        db.session.add(Files(path=path))
        tempGlobalStatus.remove(path)
    
    db.session.commit()

def hashImage(file):
    try:
        hashes = []
        img = Image.open(file)
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

        print("\tHashed {}".format(file), "blue")
        return file, hashes, file_size, image_size, capture_time
    except OSError:
        print("\tUnable to open {}".format(file), "red")
        return None


def get_file_size(file_name):
    try:
        return os.path.getsize(file_name)
    except FileNotFoundError:
        return 0

def get_image_size(img):
    return "{} x {}".format(*img.size)

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

@app.route('/add/status')
def status():
    return json.dumps(tempGlobalStatus)
app.run(debug = True)