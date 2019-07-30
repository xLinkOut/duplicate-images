#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy

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
    return render_template("add.html", path=path)

app.run(debug = True)