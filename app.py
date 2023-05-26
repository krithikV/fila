from distutils.log import debug
from fileinput import filename
from flask import *
import calendar
import datetime
from cryptography.fernet import Fernet
import os,glob
import base64
import sqlite3
app = Flask(__name__)
app.config['DOWNLOAD_FOLDER']='download'
conn = sqlite3.connect('storage_file.db')
conn.execute('''CREATE TABLE IF NOT EXISTS BETA_FILES
         (CID TEXT PRIMARY KEY NOT NULL,
         FILENAME TEXT NOT NULL,
         FILE TEXT NOT NULL,
         UPLOAD_TIME TEXT NOT NULL,
         EXPIRY TEXT NOT NULL);''')
conn.commit()
conn.close()
@app.route('/')

def main():
    conn = sqlite3.connect('storage_file.db')
    c = conn.cursor()
    c.execute("SELECT FILENAME FROM BETA_FILES WHERE EXPIRY='TRUE';")
    data = c.fetchall()
    for i in data:
         os.remove("download/"+"fila_"+i[0])
    return render_template("index.html")

@app.route('/', methods = ['POST'])
def success():
    conn = sqlite3.connect('storage_file.db')
    c = conn.cursor()
    if request.method == 'POST':
        f = request.files['file']
        f.save('upload/'+f.filename)
        filepath = "upload/"+f.filename
        with open(filepath,'rb') as f:
            file_content = f.read()
            enc = base64.encodebytes(file_content)
            enc_str = enc.decode()
            key = Fernet.generate_key()
            key = key.decode()
            date = datetime.datetime.utcnow()
            utc_time = calendar.timegm(date.utctimetuple())
            c.execute("INSERT INTO BETA_FILES (CID,FILENAME,FILE,UPLOAD_TIME,EXPIRY) VALUES ('{}','{}','{}','{}','{}')".format(key,os.path.basename(filepath),enc_str,utc_time,'FALSE'))
            conn.commit()
            conn.close()
        os.remove(filepath)
        return render_template("Acknowledgement.html", cin = request.base_url+"download/"+key)
@app.route('/download/<key>', methods=['GET', 'POST'])
def download(key):
    conn = sqlite3.connect('storage_file.db')
    c = conn.cursor()
    c.execute("SELECT * FROM BETA_FILES WHERE CID = '{}'".format(key))
    data = c.fetchall()[0]
    file_64 = data[2].encode('utf-8')
    with open("download/fila_"+data[1],'wb') as filewriter:
        filewriter.write(base64.decodebytes(file_64))
        c.execute("UPDATE BETA_FILES SET EXPIRY = 'TRUE' WHERE CID = '{}'".format(key))
        conn.commit()
        conn.close()
    full_path = os.path.join(app.root_path, app.config['DOWNLOAD_FOLDER'])
    filename = "fila_"+data[1]
    
    return send_from_directory(full_path, filename,as_attachment=True)

if __name__ == '__main__':
	app.run('127.0.0.1',5500,debug=True)
