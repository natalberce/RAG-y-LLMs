import streamlit as st
from utils.db_utils import load_name_files, clean_files, buscar_en_wikipedia, save_name_files, delete_specific_articles
from utils.wikipedia_utils import store_wikipedia_articles, get_article_summary
from config import INDEX_NAME, FILE_LIST, CHROMA_CLIENT
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from main import init_vector_store, get_llm, get_qa_chain, init_memory
from utils.reset_utils import resetear_aplicacion

if 'reset_done' not in st.session_state:
    resetear_aplicacion()
    st.session_state.reset_done = True

st.set_page_config('PreguntaWiki')

st.markdown("""<style>
        /* Estilos base del contenedor principal */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            font-family: 'Segoe UI', sans-serif;
        }

        /* Color del header principal */
        h1 {
            color: #00629b;  /* Color secundario UPM para contraste */
        }

        /* Input fields */
        input, textarea {
            border-radius: 10px !important;
            background-color: #f9f9f9 !important;
            border: 1px solid #00a9e0 !important;
            padding: 8px;
        }

        /* Botones */
        .stButton>button {
            color: white !important;
            background-color: #00a9e0 !important;  /* Color GSI */
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: bold;
        }

        .stButton>button:hover {
            background-color: #008bbf !important;  /* Tonalidad más oscura del GSI */
            transition: 0.3s ease-in-out;
        }

        /* Expander y sidebar scroll */
        .stExpanderHeader, .st-emotion-cache-6qob1r {
            background-color: #e6f7fc !important;
            color: #004766 !important;
        }

        /* Scroll lateral */
        .sidebar .css-1d391kg {
            background-color: #f0f8fb !important;
        }

        /* Respuestas resaltadas */
        .respuesta-box {
            background-color: #e6f7fc;
            padding: 15px;
            border-radius: 10px;
            border-left: 6px solid #00a9e0;
            margin-top: 10px;
        }

        /* Separadores */
        hr {
            border: none;
            height: 2px;
            background-color: #00a9e0;
        }

    </style>
""", unsafe_allow_html=True)

# Inicializar sesión
if 'archivos' not in st.session_state:
    st.session_state.archivos = load_name_files(FILE_LIST)

if 'memory' not in st.session_state:
    st.session_state.memory = init_memory()

if 'vstore' not in st.session_state:
    st.session_state.vstore = init_vector_store()


# Diseño principal
st.markdown("""
<h1 style='text-align: center; color: #2c3e50;'>Pregunta sobre Historia y Guerras</h1>
<hr style='margin-top: -10px;'>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.write("Selecciona artículos a eliminar:")
    articulos_a_borrar = st.multiselect("Artículos disponibles", st.session_state.archivos)

    if st.button("Borrar artículos seleccionados"):

        delete_specific_articles(articulos_a_borrar)
        st.session_state.archivos = [a for a in st.session_state.archivos if a not in articulos_a_borrar]
        st.success(f"Se eliminaron {len(articulos_a_borrar)} artículos.")

    if st.button("Borrar artículos"):
        clean_files(FILE_LIST)
        st.session_state.archivos = []
        st.success("Base de datos limpiada.")

    if st.button("Ver documentos en Chroma"):
        collection = CHROMA_CLIENT.get_collection(name=INDEX_NAME)
        st.write(f"Documentos en la colección: {len(collection.get()['ids'])}")

    if st.button("Reiniciar memoria de conversación"):
        st.session_state.memory.clear()
        st.success("Memoria de conversación reiniciada.")

    st.markdown("---")
    st.subheader("Buscar artículo existente")
    titulo_busqueda = st.text_input("Introduce el título del artículo:")

    if titulo_busqueda:
        if titulo_busqueda.lower() in [a.lower() for a in st.session_state.archivos]:
            st.success(f"El artículo '{titulo_busqueda}' ya está en la base de datos.")
        else:
            st.warning(f"El artículo '{titulo_busqueda}' no está almacenado.")

    st.markdown("---")
    query = st.text_input("Buscar en Wikipedia:")
    num_articles = st.number_input("Número de artículos", min_value=1, max_value=500, value=5)

    if st.button("Buscar y Procesar"):
        store_wikipedia_articles(query, num_articles, vstore=st.session_state.vstore)
        st.session_state.archivos = load_name_files(FILE_LIST)
        st.success(f"{num_articles} artículos sobre '{query}' procesados y almacenados.")

    with st.sidebar.expander("Artículos procesados", expanded=True):
        for arch in st.session_state.archivos:
            st.write(arch)



st.markdown("### Escribe tu pregunta:")
user_question = st.text_input("", placeholder="Ej. ¿De qué trata la Guerra Civil Europea?")

if user_question:
    llm = get_llm()
    retriever = st.session_state.vstore.as_retriever(search_type='similarity', search_kwargs={"k": 5})
    qa_chain = get_qa_chain(llm, retriever, st.session_state.memory)

    response = qa_chain.invoke({"question": user_question})
    respuesta_final = response.get("answer", "No se pudo generar una respuesta.")

    st.markdown(f"""
    <div class="respuesta-box">
    <b>Respuesta:</b><br>{respuesta_final}
    </div>
    """, unsafe_allow_html=True)

    retrieved_docs = response.get("source_documents", [])

    if retrieved_docs:
        with st.expander("Documentos utilizados para esta respuesta"):
            for doc in retrieved_docs:
                st.markdown(f"**Fuente:** {doc.metadata.get('source', 'Desconocido')}")
                st.text(doc.page_content[:500])

    if "no tengo información almacenada" in respuesta_final.lower():
        if 'wikipedia_data' not in st.session_state:
            st.session_state.wikipedia_data = {}

        if st.button("Buscar en Wikipedia"):
            titulo_articulo = buscar_en_wikipedia(user_question)
            if titulo_articulo:
                contenido_wikipedia, url = get_article_summary(titulo_articulo)
                if contenido_wikipedia:
                    st.session_state.wikipedia_data = {
                        "titulo": titulo_articulo,
                        "contenido": contenido_wikipedia,
                        "url": url
                    }
                else:
                    st.error("No se pudo obtener información de Wikipedia.")

        if st.session_state.wikipedia_data:
            data = st.session_state.wikipedia_data
            st.write(f"**Wikipedia:** {data['titulo']}")
            st.write(data['contenido'])
            st.write(f"[Ver en Wikipedia]({data['url']})")

            if st.button("Guardar este contenido en mi base de datos"):
                doc = Document(page_content=data['contenido'], metadata={"source": data['titulo']})
                splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)
                chunks = splitter.split_documents([doc])
                st.session_state.vstore.add_documents(chunks)

                collection = CHROMA_CLIENT.get_collection(name=INDEX_NAME)
                st.write(f"Documentos en la colección: {len(collection.get()['ids'])}")

                previos = set(load_name_files(FILE_LIST))
                nuevos = save_name_files(FILE_LIST, [data['titulo']])
                if data['titulo'] not in previos:
                    st.session_state.archivos.append(data['titulo'])
                    st.success(f"Contenido de '{data['titulo']}' guardado correctamente.")
                else:
                    st.info(f"El artículo '{data['titulo']}' ya estaba guardado.")


# Historial de conversación
if st.session_state.memory.buffer:
    st.subheader("Historial de conversación")
    for i, mensaje in enumerate(st.session_state.memory.buffer, 1):
        rol = "Usuario" if mensaje.type == "human" else "Asistente"
        st.markdown(f"**{rol} {i}:** {mensaje.content}")
