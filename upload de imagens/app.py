from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import os
import psycopg2
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_URL = "postgresql://neondb_owner:npg_izJKD7Qm0kEh@ep-wandering-resonance-a9e1300q-pooler.gwc.azure.neon.tech/neondb?sslmode=require"

def connect_db():
    return psycopg2.connect(DB_URL)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        image = request.files['image']
        name = request.form['name']
        phone = request.form['phone']

        if image and allowed_file(image.filename):
            if image.content_length > MAX_FILE_SIZE:
                flash("Imagem excede o tamanho permitido (5MB).")
                return redirect(request.url)
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            conn = connect_db()
            cur = conn.cursor()
            cur.execute("INSERT INTO images (image_name, filename, phone_number) VALUES (%s, %s, %s)",
                        (name, filename, phone))
            conn.commit()
            cur.close()
            conn.close()
            flash("Imagem enviada com sucesso!")
            return redirect(url_for('index'))
        else:
            flash("Formato de imagem inválido.")
    return render_template('index.html')

@app.route('/view/<name>')
def view_image(name):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM images WHERE image_name = %s", (name,))
    img = cur.fetchone()
    cur.close()
    conn.close()
    if img:
        return render_template('image_view.html', img=img)
    else:
        return "Nome não encontrado"

@app.route('/like/<int:image_id>')
def like_image(image_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("UPDATE images SET likes = likes + 1 WHERE id = %s", (image_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('next_image', current_id=image_id))

@app.route('/dislike/<int:image_id>')
def dislike_image(image_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("UPDATE images SET dislikes = dislikes + 1 WHERE id = %s", (image_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('next_image', current_id=image_id))

@app.route('/next/<int:current_id>')
def next_image(current_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM images WHERE id > %s ORDER BY id ASC LIMIT 1", (current_id,))
    next_img = cur.fetchone()
    cur.close()
    conn.close()
    if next_img:
        return render_template('image_view.html', img=next_img)
    else:
        return "Não há mais imagens."

@app.route('/delete/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    senha = request.form.get('senha')
    if senha != '9181':
        return "Senha incorreta!"
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM images WHERE id = %s", (image_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
