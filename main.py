#!/bin/env python3

import os, time

from random import getrandbits
from base64 import urlsafe_b64encode
from flask import Flask, \
		send_from_directory, url_for, flash, \
		request, redirect, Response, \
		render_template_string
from werkzeug.utils import secure_filename

import config

app = Flask(__name__)
app.secret_key = config.secret_key
app.config['MAX_CONTENT_LENGTH'] = config.max_content_length

@app.route('/', methods=['GET'])
def homepage():
    return render_template_string('''
    A simple ephemeral filebin
    The current file TTL is: {{ c.ttl / 3600}} hours

    USAGE:

    POST to / with the field `file`

    EXAMPLE:

    curl -F "file=@somefile"{{ c.app_url }}

    HTML Form available at /upload for browser use

    ''', c=config)

@app.route('/upload', methods=['GET'])
def upload_page():
    return render_template_string('''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
     <form method=post enctype=multipart/form-data action='/'>
      <input type=file name=file><input type=submit value=Upload>
    </form>
    ''')

@app.route('/', methods=['POST'])
def receive_file():
    if "file" not in request.files:
        return "No file sent", 400

    f = request.files['file']
    if f.filename == '':
        # Handle case when no file is selected in the form.
        # Browsers will submit a part with an empty filename
        flash('Please choose a file')
        return redirect(request.url)

    if not request.headers['token'] or request.headers['token'] not in config.tokens:
        return "Unauthorized", 401

    rand_name = urlsafe_b64encode((getrandbits(config.path_length * 8)) \
                        .to_bytes(config.path_length, 'little')).decode('utf-8')

    path = os.path.join(rand_name[:2], rand_name[2:4])
    filepath = os.path.join(path, rand_name + secure_filename(f.filename))

    try:
        os.makedirs(name=os.path.join(config.base_dir, path), exist_ok=True)
        f.save(os.path.join(config.base_dir, filepath))
    except Exception as e:
        print("ERROR: unable to save file: {}".format(e,))
        return "Internal Server Error", 500
    r = Response(config.app_url + url_for('send_file', path=filepath))
    r.headers['Location'] = url_for('send_file', path=filepath)
    return r, 200
    # Wanted to use 303, but ShareX does not handle this correctly

@app.route('/f/<path:path>', methods=['GET'])
def send_file(path):
    '''
    Reads file from disk and sends it to the user

    This function should never get called in production
    since an httpd would be serving all static files
    '''
    try:
        os_path = os.path.join(config.base_dir, path)
        path_mtime = os.stat(os_path).st_mtime
        if time.time() - path_mtime > config.ttl:
            os.remove(os_path)
            return "File not found", 404
        return send_from_directory(config.base_dir, path)
    except Exception as e:
        print("ERROR: ", e)
        return "File not found", 404

@app.route('/purge', methods=['GET'])
def file_purge():
    if not request.headers['token'] or request.headers['token'] not in config.tokens:
        return "Unauthorized", 401
    prune_count = 0
    for root, dirs, files in os.walk(config.base_dir):
        for f in files:
            path = os.path.join(root, f)
            if time.time() - os.stat(path).st_mtime > config.ttl:
                os.remove(path)
                prune_count += 1
    return "Pruned {} files".format(prune_count)

if __name__ == '__main__':
    app.debug = config.debug
    app.run()
