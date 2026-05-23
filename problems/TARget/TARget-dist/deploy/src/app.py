from flask import Flask, request, jsonify
import os, shutil, subprocess, uuid, time

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024  # Limit upload size to 1KB

@app.route('/untar', methods=['POST'])
def untar_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and (file.filename.endswith('.tar')):
        UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', str(int(time.time())))
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        random_name = f"{uuid.uuid4().hex}.tar"
        tar_path = os.path.join(UPLOAD_FOLDER, random_name)

        file.save(tar_path)

        try:
            subprocess.check_output(['tar', '-xf', tar_path, '-C', UPLOAD_FOLDER])
            return jsonify({'message': 'File untarred successfully'}), 200
        except Exception as e:
            return jsonify({'error': 'File untarred unsuccessfully'}), 500
        finally:
            shutil.rmtree(UPLOAD_FOLDER, ignore_errors=True)
    else:
        return jsonify({'error': 'Invalid file type. Only TAR files are allowed.'}), 400

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Max size is 1KB.'}), 413

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)