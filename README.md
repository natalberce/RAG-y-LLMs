# PreguntaWiki: Asistente sobre Historia basado en Wikipedia.
**PreguntaWiki** es una aplicación interactiva construida con **Streamlit** que permite hacer preguntas en español sobre temas históricos (en principio este es el dominio elegido, pero se puede modificar al gusto de cada usuario). Utiliza artículos de Wikipedia, una base de datos vectorial con **ChromaDB** y modelos LLM (como **LLaMA 3**) para generar respuestas contextualizadas.

---

## Funcionalidades

- Búsqueda y descarga de artículos desde Wikipedia.
- Almacenamiento y consulta de artículos mediante embeddings y búsqueda semántica.
- Asistente conversacional que responde preguntas basadas únicamente en el contenido descargado.
- Opción para guardar nuevos contenidos relevantes encontrados directamente desde Wikipedia.

---

## Explicación del código

El código está dividido en varios archivos que colaboran entre sí para permitir la interacción con Wikipedia, la creación de una base de datos semántica y la respuesta a preguntas usando un modelo LLM.

### `app.py`

Archivo principal que lanza la interfaz web con **Streamlit**. Contiene:

- La barra lateral donde se puede:
  - Buscar y procesar artículos de Wikipedia.
  - Visualizar los artículos almacenados.
  - Eliminar la base de datos.
- El área principal donde el usuario puede:
  - Escribir una pregunta.
  - Ver la respuesta generada por el modelo LLM.
  - Visualizar fuentes utilizadas.
  - Buscar información adicional si no hay contexto suficiente.
  - Guardar nuevos artículos de Wikipedia en la base de datos.
- Usa memoria de conversación para mantener el historial entre interacciones.

---

### `config.py`

Archivo con variables de configuración reutilizables en todo el proyecto:

- Nombre de la colección en ChromaDB.
- Ruta del archivo con los títulos de artículos procesados.
- Dirección y puerto del servidor Chroma.
- Nombre del modelo de embeddings y del LLM.

---

### `utils/` (carpeta de utilidades)

#### `wikipedia_utils.py`

Contiene funciones para interactuar con la Wikipedia:

- `get_wikipedia_articles`: obtiene títulos de una categoría.
- `get_article_summary`: extrae el resumen de un artículo.
- `store_wikipedia_articles`: guarda artículos seleccionados como documentos, los trocea, vectoriza y almacena en ChromaDB.

#### `db_utils.py`

Utilidades para gestionar la base de datos local:

- `save_name_files` y `load_name_files`: guardan y leen los nombres de los artículos procesados.
- `clean_files`: borra los registros y reinicia la colección en ChromaDB.
- `buscar_en_wikipedia`: busca un término directamente en Wikipedia.

---

### `requirements.txt`

Lista de dependencias necesarias para ejecutar el proyecto. Incluye:

- `streamlit`: para la interfaz web.
- `chromadb`: para la base vectorial.
- `langchain`: para la orquestación del flujo de recuperación + generación.
- `sentence-transformers`: para embeddings.
- `pypdf`: por si se amplía a fuentes en PDF (aunque actualmente no se usa directamente).

---

### `articulos.txt`

Archivo que guarda los nombres de los artículos de Wikipedia que ya han sido procesados, evitando duplicados al almacenar nueva información.

## 🚀 Cómo desplegar el proyecto

Para ejecutar la aplicación de forma local, solo necesitas seguir estos dos pasos principales: lanzar el servidor de ChromaDB usando Docker y ejecutar la interfaz con Streamlit desde la terminal.

---

### 1. Lanzar ChromaDB usando Docker

Asegúrate de tener Docker instalado en tu sistema. Luego, ejecuta el siguiente comando en una terminal para iniciar el servidor de ChromaDB:

docker run -p 8000:8000 ghcr.io/chroma-core/chroma

### 2. Ejecutar la aplicación con Streamlit

Para lanzar la interfaz web de la aplicación, sigue estos pasos:

1. Abre una terminal (CMD o PowerShell).
2. Accede a la carpeta donde tienes tu proyecto. Por ejemplo:

cd C:\Users\TuUsuario\Ruta\Del\Proyecto\tfg_app

3. Ejecuta el siguiente comando para iniciar Streamlit:

python -m streamlit run app.py

Esto abrirá automáticamente la aplicación en tu navegador.
Desde allí podrás interactuar con la interfaz: buscar artículos, hacer preguntas y visualizar respuestas generadas por el modelo.


