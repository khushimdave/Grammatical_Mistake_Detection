from flask import render_template
#from textdetection import read_image
import os
from flask import Flask, request
from werkzeug.utils import secure_filename
from video_op import video2audio, audio_to_text, check_grammer, tabularization
import requests
cwd = os.getcwd()

UPLOAD_FOLDER = os.path.join(cwd,'static','vids')
ALLOWED_EXTENSIONS = {'mp4', 'wav'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

## To do
## Add a reset link, this will reset all the variable values in the html file.
## Add CSS in the webpage.

@app.route('/', methods=['POST', "GET"])
def image_read():
    if request.method == 'POST':
        # check if the post request has the file part
        print("Here ....")
        print(request.files['file'])
        if 'file' not in request.files:
            # flash('No file part')
            print("File not found!!")
            return render_template('index.html')
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            print("File name empty!")
            # flash('No selected file')
            return render_template('index.html')
        if file and allowed_file(file.filename):
            print("File found", file.filename)
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            
            ## Checking for grammer mistakes.
            ext = filename.split('.')[-1]
            if ext in ["wav", "mp3"]:
                text, items_df = audio_to_text(file_path, filename)
                transcripts = text
            elif ext in 'mp4':
                audio_path = video2audio(filename, file_path)
            
                if isinstance(audio_path, str) and audio_path == "INSERT_SMALLER_CLIP":
                    ## Have to return some error message....
                    print(audio_path)
                    return render_template('index.html', data = 0, len = 0)
                text = audio_to_text(file_path, filename)
            
            if isinstance(text, str) and text == None:
                print(text)
                return render_template('index.html', data = 0, len = 0)
            
            matches = check_grammer(text)
            table, csv_path = tabularization(matches, filename)
            
            if isinstance(table, str) and table == "NO_MISTAKES_FOUND":
                print(table)
                return render_template('index.html', data = 0, len = 0)            
            table = table.head()
            length = len(table["Message"])
            csv_path = "static/transcripts/changed/" + filename.split(".")[0] + '.csv'
            return render_template('index.html', tables=[table.to_html(classes='data')], titles=table.columns.values, csv = csv_path,\
                 foobar=[items_df.to_html(classes="data")], transcript=transcripts, foo_titles=list(items_df.columns))
        return render_template('index.html')
    return render_template('index.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

 
if __name__ == "__main__":
    app.run(debug=True)