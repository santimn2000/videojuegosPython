from http.client import NOT_FOUND
from flask import Flask, flash, jsonify, redirect, render_template, request, send_file, url_for, session
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO
#from videojuego import Videojuego



app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)


class Videojuego(db.Model):
    __tablename__ = 'videojuegos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80))
    categoria = db.Column(db.String(80))
    blob_img = db.Column(db.BLOB, nullable=True)
    url_img = db.Column(db.String(80), nullable=True)
    multijugador = db.Column(db.Integer)  # Campo entero para indicar si es multijugador
    precio = db.Column(db.Float)  # Campo de tipo flotante para el precio
    desarrolladora = db.Column(db.String(80))
    # Otros campos de tu tabla videojuegos

    def __repr__(self):
        return f'<Videojuego {self.nombre}>'

class Plataforma(db.Model):
    __tablename__ = 'plataforma'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    plataforma_compra = db.Column(db.String(80), nullable=True)
    # Otros campos de tu tabla usuarios

    def __repr__(self):
        return f'<Plataforma {self.nombre}>'

class VideojuegoPlataforma(db.Model):
    __tablename__ = 'videojuego_plataforma'

    id = db.Column(db.Integer, primary_key=True)
    videojuego_id = db.Column(db.Integer, db.ForeignKey('videojuegos.id'), nullable=False)
    plataforma_id = db.Column(db.Integer, db.ForeignKey('plataforma.id'), nullable=False)

    videojuego = db.relationship("Videojuego", backref="plataformas_relacionadas")
    plataforma = db.relationship("Plataforma", backref="videojuegos_relacionados")


class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(80), unique=True, nullable=False)
    passwd = db.Column(db.String(1000), nullable=False)
    permisos = db.Column(db.String(80), nullable=False)
    # Otros campos de tu tabla usuarios

    def __repr__(self):
        return f'<Usuario {self.usuario}>'

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/features')
def features():
    return render_template('features.html')


@app.route('/imagen/<int:id>')
def obtener_imagen(id):
    videojuego = Videojuego.query.get_or_404(id)
    if videojuego.blob_img:
        # Procesar los datos de la imagen como un archivo en memoria
        img_stream = BytesIO(videojuego.blob_img)
        img_stream.seek(0)
        return send_file(img_stream, mimetype='image/png')
    else:
        return "No se encontró imagen para este videojuego"

@app.route('/lista')
def lista():
    videojuegos = Videojuego.query.all()
    return render_template('lista.html', videojuegos=videojuegos)

@app.route('/add')
def add():
    return render_template('add.html')

#Method Post
@app.route('/addVideojuego', methods=['POST'])
def addVideojuego():
    nombre = request.form['nombre']
    precio = request.form['precio']
    desarrolladora = request.form['desarrolladora']
    multijugador = request.form['multijugador']
    categoria = request.form['categoria']
    
    imagen = request.files['imagen']
    blob_img = imagen.read() if imagen else None
    imagen_nombre = imagen.filename if imagen else None

    if nombre and categoria and multijugador and precio and desarrolladora:
        # Buscar si ya existe un juego con ese nombre
        existente = Videojuego.query.filter_by(nombre=nombre).first()

        if existente:
            # Si el juego ya existe, actualiza sus datos
            existente.precio = precio
            existente.desarrolladora = desarrolladora
            existente.multijugador = multijugador
            existente.categoria = categoria
            existente.blob_img = blob_img
            existente.url_img = imagen_nombre
        else:
            # Si no existe, crea uno nuevo con la imagen
            nuevo_juego = Videojuego(
                nombre = nombre,
                multijugador = multijugador,
                precio = precio,
                desarrolladora = desarrolladora,
                categoria = categoria,
                blob_img = blob_img,
                url_img = imagen_nombre
                
            )
            db.session.add(nuevo_juego)

        db.session.commit()

        return redirect(url_for('lista'))
    else:
        return "Faltan campos obligatorios"


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/comprobarLogin', methods=['POST'])
def comprobarLogin():
    username = request.form['username']
    password = request.form['password']

    # Verificar si el usuario existe en la base de datos
    usuario = Usuario.query.filter_by(usuario=username, passwd=password).first()

    if usuario:
        # Autenticación exitosa, devolver datos como JSON
        return jsonify({
            'success': True,
            'usuario': usuario.usuario,
            'permisos': usuario.permisos
        })
    else:
        # Autenticación fallida, devolver datos como JSON
        return jsonify({'success': False})

@app.route('/eliminar_juego/<int:juego_id>', methods=['DELETE'])
def eliminar_juego(juego_id):
    juego = Videojuego.query.get_or_404(juego_id)
    db.session.delete(juego)
    db.session.commit()
    return jsonify({'mensaje': 'Juego con id '+str(juego_id)+' eliminado exitosamente'})


@app.route('/vincular')
def formulario_videojuego_plataforma():
    videojuegos = Videojuego.query.all()
    plataformas = Plataforma.query.all()
    return render_template('vincular.html', videojuegos=videojuegos, plataformas=plataformas)


@app.route('/procesar_vincular', methods=['POST'])
def procesar_vincular():
    videojuego_id = request.form['videojuego']  # Obtener el ID del videojuego seleccionado
    plataformas_seleccionadas = request.form.getlist('plataforma[]')  # Obtener las plataformas seleccionadas

    try:
        # Eliminar todas las filas que tienen el id del juego seleccionado
        VideojuegoPlataforma.query.filter_by(videojuego_id=videojuego_id).delete()

        # Insertar nuevas filas para las plataformas seleccionadas
        for plataforma_id in plataformas_seleccionadas:
            nueva_relacion = VideojuegoPlataforma(videojuego_id=videojuego_id, plataforma_id=plataforma_id)
            db.session.add(nueva_relacion)

        # Confirmar los cambios en la base de datos
        db.session.commit()

        return redirect(url_for('lista'))

    except Exception as e:
        db.session.rollback()  # En caso de error, revertir los cambios
        return f"Error al procesar el formulario: {str(e)}"


@app.route('/ver_juego/<int:id>')
def ver_juego(id):
    # Aquí obtienes los detalles del juego con el ID proporcionado desde la base de datos
    # Supongamos que tienes una función get_juego_by_id que obtiene los detalles del juego
    juego = Videojuego.query.get(id)
    plataformas_asociadas = (
            db.session.query(Plataforma)
            .join(VideojuegoPlataforma)
            .filter(VideojuegoPlataforma.videojuego_id == juego.id)
            .all()
        )

    # Renderizas una plantilla con los detalles del juego
    return render_template('ver_juego.html', juego=juego, plataformas = plataformas_asociadas)


@app.route('/modificar_juego/<int:id>', methods=['GET'])
def modificar_juego(id):
    juego = Videojuego.query.get(id)  # Aquí necesitarás una función que obtenga el juego por su ID desde la base de datos
    plataformas = (
            db.session.query(Plataforma)
            .join(VideojuegoPlataforma)
            .filter(VideojuegoPlataforma.videojuego_id == juego.id)
            .all()
        )  # Función para obtener las plataformas asociadas al juego
    
    if juego:
        return render_template('modificar_juego.html', juego=juego, plataformas=plataformas)
    else:
        flash('Juego no encontrado', 'error')
        return redirect(url_for('lista'))


@app.route('/procesar_modificar_juego', methods=['POST'])
def procesar_modificar_juego():
    juego_id = request.form.get('juego_id')
    nombre = request.form['nombre']
    precio = request.form['precio']
    desarrolladora = request.form['desarrolladora']
    multijugador = request.form['multijugador']
    categoria = request.form['categoria']
    
    imagen = request.files['imagen']
    blob_img = imagen.read() if imagen else None
    imagen_nombre = imagen.filename if imagen else None

    # Obtener el juego a modificar
    juego = Videojuego.query.get_or_404(juego_id)

    # Actualizar los campos del juego
    juego.nombre = nombre
    juego.precio = precio
    juego.desarrolladora = desarrolladora
    juego.multijugador = multijugador
    juego.categoria = categoria
    juego.blob_img = blob_img
    juego.url_img = imagen_nombre

    # Guardar los cambios en la base de datos
    db.session.commit()

    return redirect(url_for('lista'))



if __name__ == '__main__':
    app.run(debug=True)