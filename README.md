# PreguntaWiki: Asistente sobre Historia basado en Wikipedia.
**PreguntaWiki** es una aplicación interactiva construida con **Streamlit** que permite hacer preguntas en español sobre historia contemporánea en Europa (en principio este es el dominio elegido, pero se puede modificar al gusto de cada usuario). Utiliza artículos de Wikipedia, una base de datos vectorial con **ChromaDB** y modelos LLM (como **LLaMA 3**) para generar respuestas contextualizadas.

---

## Funcionalidades

- Búsqueda de artículos por categoría directamente desde Wikipedia.
- Descarga, vectorización y almacenamiento local de artículos.
- Consulta semántica de contenidos usando embeddings.
- Asistente conversacional que responde preguntas basadas únicamente en los documentos almacenados.
- Visualización, gestión y limpieza del contenido descargado.
- Opción para buscar directamente en Wikipedia si no hay suficiente contexto.

---

## Explicación del código

El código está dividido en varios archivos que colaboran entre sí para permitir la interacción con Wikipedia, la creación de una base de datos semántica y la respuesta a preguntas usando un modelo LLM.

### `app.py` – Interfaz de usuario (Streamlit)

Este es el archivo principal que se ejecuta para lanzar la aplicación. Se encarga de:

- Mostrar el título y menú lateral.
- Permitir búsquedas de artículos por categoría de Wikipedia.
- Descargar y almacenar artículos en una base vectorial.
- Mostrar artículos ya almacenados.
- Realizar preguntas basadas en los artículos procesados.
- Visualizar las respuestas generadas y el historial conversacional.
- Ofrecer búsquedas adicionales en Wikipedia si no hay contexto suficiente.

> Este archivo gestiona toda la interacción del usuario y llama a las funciones del backend.

---
### `main.py` – Lógica central de procesamiento
Contiene funciones clave para:

- Descargar artículos y trocearlos para vectorización.
- Generar embeddings usando un modelo de HuggingFace.
- Crear prompts y enviar preguntas al modelo LLaMA 3.
- Recuperar documentos similares por búsqueda semántica.
- Buscar directamente en Wikipedia si no se encuentra información suficiente en la base local.

> Este archivo orquesta todo el flujo RAG (retrieval-augmented generation).

---
### `config.py`

Archivo con variables de configuración reutilizables en todo el proyecto:

- `INDEX_NAME`: nombre de la colección en ChromaDB.
- `FILE_LIST`: archivo local donde se guardan los títulos de artículos descargados.
- `CHROMA_HOST` y `CHROMA_PORT`: configuración de red del servidor Chroma.
- `EMBEDDING_MODEL`: modelo de embeddings usado para vectorización.
- `LLM_MODEL`: nombre del modelo LLama que se utilizará vía `ollama`.
- `LLM_BASE_URL`
- `CHROMA_CLIENT`: inicializa el cliente de Chroma.
- `CATEGORIA_INICIAL`: la categoría con la que se quiere trabajar en la aplicación.
- 

> Centraliza todos los valores de configuración para facilitar mantenimiento y cambios.
---

### `utils/` (carpeta de utilidades)

#### `wikipedia_utils.py`

Contiene funciones para interactuar con la Wikipedia:

- `get_wikipedia_articles`: obtiene títulos de una categoría.
- `get_article_summary`: extrae el resumen de un artículo.
- `is_article_in_chroma`: comprueba si el artículo está guardado en la base de datos vectorial.
- `store_wikipedia_articles`: guarda artículos seleccionados como documentos, los trocea, vectoriza y almacena en ChromaDB.

#### `db_utils.py`

Utilidades para gestionar la base de datos local:

- `save_name_files` y `load_name_files`: guardan y leen los nombres de los artículos procesados.
- `clean_files`: borra los registros y reinicia la colección en ChromaDB.
- `buscar_en_wikipedia`: busca un término directamente en Wikipedia.
- `delete_specific_articles`: elimina artículos específicos de los que están ya guardados.

#### `reset_utils.py`

Función que se encarga de resetear la aplicación cada vez que se cierra para que si un usuario hace algún cambio, que la siguiente
persona que utilice el sistema no se encuentre con los cambios del anterior usuario.

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


