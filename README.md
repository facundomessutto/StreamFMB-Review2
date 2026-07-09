# StreamFMB - Plataforma de Reseñas de Películas y Series 

StreamFMB es una aplicación web interactiva desarrollada con Python y Flask que permite a los usuarios explorar un catálogo de películas y series, visualizar sus portadas, y compartir sus opiniones mediante un sistema de reseñas y calificaciones.

## Características Principales

* **Catálogo Dinámico:** Visualización de obras con sus respectivas portadas, géneros y años de estreno.

* **Sistema de Reseñas:** Los usuarios pueden calificar (1 a 5 estrellas) y comentar sobre el contenido

* **Panel de Administración:** Un área restringida (con inicio de sesión) exclusiva para administradores.

* **Moderación y Censura:** Los administradores pueden ocultar comentarios que infrinjan las normas (mostrando un aviso de censura en la vista pública sin borrar el registro del usuario).

* **Diseño Responsivo:** Interfaz adaptable a computadoras, tablets y dispositivos móviles gracias a la integración de Bootstrap.

* **Cálculo Automático:** Promedio global de puntuación calculado en tiempo real basado en las reseñas de la comunidad.

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python 3, Flask
* **Base de Datos:** SQLite3 (con consultas SQL puras)
* **Frontend:** HTML5, CSS3, Jinja2 (Motor de plantillas)
* **Framework CSS:** Bootstrap 5
* **Control de Versiones:** Git y GitHub
* **Despliegue en la Nube:** PythonAnywhere

## ⚙️ Instalación y Ejecución Local

Sigue estos pasos para ejecutar el proyecto en tu propia computadora:

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/TuUsuario/StreamFMB-Review.git](https://github.com/TuUsuario/StreamFMB-Review.git)
   cd StreamFMB-Review


    #Activación del Entorno:

   # En Windows:
python -m venv venv
venv\Scripts\activate

    #Instalar Dependencias
pip install -r requirements.txt

    #Ejecución de la Aplicación:
python app.py