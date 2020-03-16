#!/bin/env python3

import os, builtins, time

from random import getrandbits, choice
from base64 import urlsafe_b64encode
from flask import Flask, \
		render_template, url_for, flash, \
		request, redirect, Response, abort, \
		get_flashed_messages, make_response, send_from_directory
from werkzeug.utils import secure_filename

import config

app = Flask(__name__)
app.secret_key = config.secret_key
app.config['MAX_CONTENT_LENGTH'] = config.max_content_length


# TODO: replace with a template, implement a base layout
#       Implement custom http status code templates with black background

@app.route('/', methods=['GET'])
def homepage():
    return '''
    USAGE:
    POST to / with the field `file`

    Example:
    curl -F "file=@somefile" https://example.com/

    HTML Form available at /upload for browser use

    '''

@app.route('/upload', methods=['GET'])
def upload_page():
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data action='/'>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

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

    rand_name = urlsafe_b64encode((getrandbits(config.path_length * 8)) \
                        .to_bytes(config.path_length, 'little')).decode('utf-8')

    path = os.path.join(rand_name[:2],rand_name[2:4])
    filepath = os.path.join(path, rand_name + secure_filename(f.filename))

    try:
        os.makedirs(name=os.path.join(config.base_dir,path), exist_ok=True)
        f.save(os.path.join(config.base_dir,filepath))
    except Exception as e:
        print("ERROR: unable to save file: {}".format(e,))
        return "Internal Server Error", 500
    r = Response()
    r.headers['Location'] = url_for('send_file', path=filepath)
    return r, 303

@app.route('/<path:path>', methods=['GET'])
def send_file(path):
    '''
    Reads file from disk and sends it to the user

    This function should never get called in production
    since an httpd would be serving all static files
    '''
    try:
        os_path = os.path.join(config.base_dir, path)
        path_mtime = int(os.stat(os_path).st_mtime)
        if int(time.time()) - path_mtime > config.ttl:

            os.remove(os_path)
            raise
        return send_from_directory(config.base_dir, path)
    except Exception as e:
        print("ERROR: ", e)
        return "File not found", 404

# TODO: implement function to be called periodically to purge all expired files
#       use

if __name__ == '__main__':
	app.debug = True
	app.run()