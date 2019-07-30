#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
import magic

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

app.run(debug = True)