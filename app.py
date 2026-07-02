from flask import Flask, jsonify, render_template, abort, request, redirect, session
import sqlite3
from datetime import datetime
import secrets
import os

app = Flask(__name__)
app.secret_key = 'streamfmb_clave_secreta_super_segura'

# --- LA MAGIA PARA QUE FUNCIONE EN PYTHONANYWHERE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'streamfmb.db')
# ----------------------------------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos y carga datos de prueba si está vacía"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_usuario TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contenidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            tipo TEXT,
            genero TEXT,
            anio_estreno INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resenas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            calificacion INTEGER,
            comentario TEXT,
            usuario_id INTEGER,
            contenido_id INTEGER,
            censurada INTEGER DEFAULT 0,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (contenido_id) REFERENCES contenidos(id)
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (nombre_usuario, email, password) VALUES ('admin', 'admin@mail.com', '1234')")
        cursor.execute("INSERT INTO contenidos (titulo, tipo, genero, anio_estreno) VALUES ('Inception', 'Pelicula', 'Ciencia Ficción', 2010)")
        cursor.execute("INSERT INTO contenidos (titulo, tipo, genero, anio_estreno) VALUES ('Breaking Bad', 'Serie', 'Drama', 2008)")
        cursor.execute("INSERT INTO resenas (calificacion, comentario, usuario_id, contenido_id, censurada) VALUES (5, 'Una obra maestra absoluta.', 1, 1, 0)")
        
    conn.commit()
    conn.close()

# Ejecuta la creación de la base de datos al iniciar
init_db()

# --- SEGURIDAD CSRF (Hito 3) ---
@app.context_processor
def inject_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return dict(csrf_token=session['csrf_token'])

def validar_csrf():
    if request.form.get('csrf_token') != session.get('csrf_token'):
        abort(400, "Error de validación CSRF. Petición rechazada.")

# ==========================================
# ENDPOINTS DE LA API REST COMPLETA (HITO 3)
# ==========================================
@app.route('/api/resumen/', methods=['GET'])
def api_resumen():
    db = get_db()
    total_contenidos = db.execute("SELECT COUNT(*) FROM contenidos").fetchone()[0]
    total_resenas = db.execute("SELECT COUNT(*) FROM resenas").fetchone()[0]
    total_usuarios = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    db.close()
    return jsonify({
        "estadisticas": {
            "total_obras": total_contenidos,
            "total_resenas": total_resenas,
            "total_usuarios": total_usuarios
        }
    }), 200

@app.route('/api/contenidos/', methods=['GET', 'POST'])
def api_contenidos():
    db = get_db()
    if request.method == 'GET':
        cursor = db.execute("SELECT * FROM contenidos")
        contenidos = [dict(row) for row in cursor.fetchall()]
        db.close()
        return jsonify(contenidos), 200
        
    if request.method == 'POST':
        datos = request.get_json()
        if not datos or not 'titulo' in datos or not 'anio_estreno' in datos:
            return jsonify({"error": "Faltan datos requeridos", "status": 400}), 400
            
        if len(datos['titulo']) > 100:
            return jsonify({"error": "El título supera los 100 caracteres", "status": 400}), 400
        if int(datos['anio_estreno']) < 1888 or int(datos['anio_estreno']) > datetime.now().year:
            return jsonify({"error": "Año de estreno no válido", "status": 400}), 400

        cursor = db.execute('INSERT INTO contenidos (titulo, tipo, genero, anio_estreno) VALUES (?, ?, ?, ?)',
                   (datos['titulo'], datos.get('tipo', 'Pelicula'), datos.get('genero', ''), int(datos['anio_estreno'])))
        db.commit()
        nuevo_id = cursor.lastrowid
        db.close()
        return jsonify({"mensaje": "Contenido creado con éxito", "id": nuevo_id}), 201

@app.route('/api/contenidos/<int:id>/', methods=['GET', 'PUT', 'DELETE'])
def api_detalle_contenido_rest(id):
    db = get_db()
    row = db.execute("SELECT * FROM contenidos WHERE id = ?", (id,)).fetchone()
    
    if not row:
        db.close()
        return jsonify({"error": "Contenido no encontrado", "status": 404}), 404

    if request.method == 'GET':
        db.close()
        return jsonify(dict(row)), 200
        
    if request.method == 'PUT':
        datos = request.get_json()
        db.execute('UPDATE contenidos SET titulo=?, tipo=?, genero=?, anio_estreno=? WHERE id=?',
                   (datos.get('titulo', row['titulo']), datos.get('tipo', row['tipo']), datos.get('genero', row['genero']), datos.get('anio_estreno', row['anio_estreno']), id))
        db.commit()
        db.close()
        return jsonify({"mensaje": "Contenido actualizado con éxito"}), 200
        
    if request.method == 'DELETE':
        db.execute("DELETE FROM resenas WHERE contenido_id = ?", (id,))
        db.execute("DELETE FROM contenidos WHERE id = ?", (id,))
        db.commit()
        db.close()
        return jsonify({"mensaje": "Contenido eliminado con éxito"}), 200

# ==========================================
# RUTAS PÚBLICAS Y BÚSQUEDA
# ==========================================
@app.route('/')
def inicio():
    db = get_db()
    total_obras = db.execute("SELECT COUNT(*) FROM contenidos").fetchone()[0]
    total_resenas = db.execute("SELECT COUNT(*) FROM resenas").fetchone()[0]
    db.close()
    return render_template('inicio.html', total_obras=total_obras, total_resenas=total_resenas)

@app.route('/contenidos/')
def lista_contenidos():
    query = request.args.get('q', '') 
    db = get_db()
    
    if query:
        contenidos = db.execute("SELECT * FROM contenidos WHERE titulo LIKE ?", ('%' + query + '%',)).fetchall()
    else:
        contenidos = db.execute("SELECT * FROM contenidos").fetchall()
        
    db.close()
    return render_template('lista.html', contenidos=contenidos, query=query)

@app.route('/contenidos/<int:id>')
def detalle_contenido(id):
    db = get_db()
    contenido = db.execute("SELECT * FROM contenidos WHERE id = ?", (id,)).fetchone()
    if not contenido: 
        abort(404)
        
    resenas_obra = db.execute('''
        SELECT r.*, u.nombre_usuario 
        FROM resenas r JOIN usuarios u ON r.usuario_id = u.id
        WHERE r.contenido_id = ?
    ''', (id,)).fetchall()
    
    promedio = sum(r['calificacion'] for r in resenas_obra) / len(resenas_obra) if resenas_obra else 0
    db.close()
    return render_template('detalle.html', contenido=contenido, resenas=resenas_obra, promedio=round(promedio, 1))

# ==========================================
# AUTENTICACIÓN Y REGISTRO DE USUARIOS
# ==========================================
@app.route('/registro', methods=['GET', 'POST'])
def registro_usuario():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = get_db()
        try:
            db.execute("INSERT INTO usuarios (nombre_usuario, email, password) VALUES (?, ?, ?)", 
                       (username, email, password))
            db.commit()
            return redirect('/login') 
        except sqlite3.IntegrityError:
            error = "El nombre de usuario o correo ya está registrado."
        finally:
            db.close()
            
    return render_template('registro.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login_usuario():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_db()
        usuario = db.execute("SELECT * FROM usuarios WHERE nombre_usuario = ?", (username,)).fetchone()
        db.close()
        
        if usuario and usuario['password'] == password:
            session['usuario_id'] = usuario['id']
            session['nombre_usuario'] = usuario['nombre_usuario']
            return redirect('/contenidos/')
        else:
            error = "Usuario o contraseña incorrectos."
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout_usuario():
    session.pop('usuario_id', None)
    session.pop('nombre_usuario', None)
    return redirect('/')

@app.route('/resenas/nueva', methods=['GET', 'POST'])
def nueva_resena():
    if not session.get('usuario_id'): return redirect('/login')
        
    db = get_db()
    if request.method == 'POST':
        db.execute('''
            INSERT INTO resenas (calificacion, comentario, usuario_id, contenido_id, censurada)
            VALUES (?, ?, ?, ?, 0)
        ''', (int(request.form.get('calificacion')), request.form.get('comentario'), session['usuario_id'], int(request.form.get('contenido_id'))))
        db.commit()
        cont_id = request.form.get('contenido_id')
        db.close()
        return redirect(f"/contenidos/{cont_id}")
        
    contenidos = db.execute("SELECT * FROM contenidos").fetchall()
    db.close()
    return render_template('form.html', contenidos=contenidos)

# ==========================================
# PANEL ADMIN: CRUD (HITO 3)
# ==========================================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        if request.form.get('usuario') == 'admin' and request.form.get('password') == '1234':
            session['admin_logged_in'] = True
            return redirect('/admin/dashboard')
        else:
            error = "Credenciales incorrectas."
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'): return redirect('/admin/login')
    db = get_db()
    contenidos = db.execute("SELECT * FROM contenidos").fetchall()
    resenas = db.execute('''
        SELECT r.*, u.nombre_usuario 
        FROM resenas r
        JOIN usuarios u ON r.usuario_id = u.id
    ''').fetchall()
    db.close()
    return render_template('admin_dashboard.html', contenidos=contenidos, resenas=resenas)

@app.route('/admin/agregar_contenido', methods=['GET', 'POST'])
def admin_agregar_contenido():
    if not session.get('admin_logged_in'): return redirect('/admin/login')
    anio_actual = datetime.now().year
    error = None
    
    if request.method == 'POST':
        validar_csrf() 
        titulo = request.form.get('titulo')
        anio = int(request.form.get('anio_estreno'))
        
        if len(titulo) > 100:
            error = "Error: El título no puede superar los 100 caracteres."
        elif anio < 1888 or anio > anio_actual:
            error = f"Error: El año de estreno debe estar entre 1888 y {anio_actual}."
        else:
            db = get_db()
            db.execute('INSERT INTO contenidos (titulo, tipo, genero, anio_estreno) VALUES (?, ?, ?, ?)',
                       (titulo, request.form.get('tipo'), request.form.get('genero'), anio))
            db.commit()
            db.close()
            return redirect('/admin/dashboard')
    
    return render_template('form_crear.html', anio_actual=anio_actual, error=error)

@app.route('/admin/editar_contenido/<int:id>', methods=['GET', 'POST'])
def admin_editar_contenido(id):
    if not session.get('admin_logged_in'): return redirect('/admin/login')
    anio_actual = datetime.now().year
    error = None
    
    db = get_db()
    contenido = db.execute("SELECT * FROM contenidos WHERE id = ?", (id,)).fetchone()
    
    if request.method == 'POST':
        validar_csrf()
        titulo = request.form.get('titulo')
        anio = int(request.form.get('anio_estreno'))
        
        if len(titulo) > 100:
            error = "Error: El título no puede superar los 100 caracteres."
        elif anio < 1888 or anio > anio_actual:
            error = f"Error: El año de estreno debe estar entre 1888 y {anio_actual}."
        else:
            db.execute('UPDATE contenidos SET titulo=?, tipo=?, genero=?, anio_estreno=? WHERE id=?',
                       (titulo, request.form.get('tipo'), request.form.get('genero'), anio, id))
            db.commit()
            db.close()
            return redirect('/admin/dashboard')
            
    db.close()
    if not contenido: abort(404)
    return render_template('form_editar.html', contenido=contenido, anio_actual=anio_actual, error=error)

@app.route('/admin/eliminar_contenido/<int:id>', methods=['GET', 'POST'])
def admin_eliminar_contenido(id):
    if not session.get('admin_logged_in'): return redirect('/admin/login')
    
    db = get_db()
    contenido = db.execute("SELECT * FROM contenidos WHERE id = ?", (id,)).fetchone()
    if not contenido:
        db.close()
        abort(404)
        
    if request.method == 'POST':
        validar_csrf()
        db.execute("DELETE FROM resenas WHERE contenido_id = ?", (id,))
        db.execute("DELETE FROM contenidos WHERE id = ?", (id,))
        db.commit()
        db.close()
        return redirect('/admin/dashboard')
        
    db.close()
    return render_template('confirmar_eliminar.html', contenido=contenido)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)