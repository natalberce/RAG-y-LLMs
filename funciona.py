#ESTO ES CON EL BOTON PERO SIN MEMORIA

import streamlit as st
#separar el rag con la interfaz, historial que se le pase al llm
import urllib.parse
import requests
from langchain_chroma import Chroma #langchain_chroma
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from utils.db_utils import  load_name_files, clean_files, buscar_en_wikipedia, save_name_files
from utils.wikipedia_utils import store_wikipedia_articles
from config import INDEX_NAME, FILE_LIST, EMBEDDING_MODEL, LLM_MODEL, LLM_BASE_URL, CHROMA_HOST
import chromadb
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


# Configuración de Chroma y Embeddings
chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=8000)
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vstore = Chroma(
    collection_name=INDEX_NAME,
    embedding_function=embeddings,
    client=chroma_client 
)

st.set_page_config('PreguntaWiki')
st.header("Pregunta sobre Historia y Guerras")

with st.sidebar:
    query = st.text_input("Buscar en Wikipedia:")
    num_articles = st.number_input("Número de artículos", min_value=1, max_value=500, value=5)
    
    if st.button("Buscar y Procesar"):
        store_wikipedia_articles(query, num_articles)
        st.session_state.archivos = load_name_files(FILE_LIST)
        st.success(f"{num_articles} artículos sobre '{query}' procesados y almacenados.")


    if 'archivos' not in st.session_state:
        st.session_state.archivos = load_name_files(FILE_LIST)

    st.write("Artículos procesados:")
    for arch in st.session_state.archivos:
        st.write(arch)

    if st.button('Borrar artículos'):
        clean_files(FILE_LIST)
        st.session_state.archivos = []
        st.success("Base de datos limpiada.")

user_question = st.text_input("Pregunta sobre los artículos:")

if user_question:
    retriever = vstore.as_retriever(search_type='similarity', search_kwargs={"k": 5})
    retrieved_docs = retriever.invoke(user_question)

    context_chunks = [doc.page_content.strip() for doc in retrieved_docs if doc.page_content.strip()]
    contexto_completo = " ".join(context_chunks)

    if contexto_completo and len(contexto_completo) >= 50:
        llm = ChatOllama(model=LLM_MODEL, temperature=0.7, num_predict=500, base_url=LLM_BASE_URL)

        prompt = f"""
Eres un asistente experto en historia y conflictos militares.
Responde **solo** si la información en el contexto es relevante.
Si no puedes encontrar la respuesta en el contexto, di:
**"No tengo información almacenada en mi base de datos para responder esa pregunta."**

Contexto:
{contexto_completo}

Pregunta: {user_question}

Respuesta:
"""
        respuesta_llm = llm.invoke(prompt)
        respuesta_final = respuesta_llm.content if hasattr(respuesta_llm, "content") else respuesta_llm
    else:
        respuesta_final = "**No tengo información almacenada en mi base de datos para responder esa pregunta.**"

    st.write(respuesta_final)


    if "no tengo información almacenada" in respuesta_final.lower():
        if st.button("🔎 Buscar en Wikipedia"):
            titulo_articulo = buscar_en_wikipedia(user_question)
            if titulo_articulo:
                termino_codificado = urllib.parse.quote(titulo_articulo)
                wiki_url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{termino_codificado}"
                wiki_response = requests.get(wiki_url)
                if wiki_response.status_code == 200:
                    data = wiki_response.json()
                    contenido_wikipedia = data.get("extract", "") #esto es para extraer la información codificada de wikipe
                    
                    st.write(f"**Wikipedia:** {data.get('title', 'Sin título')}")
                    st.write(contenido_wikipedia)
                    st.write(f"[Ver en Wikipedia]({data.get('content_urls', {}).get('desktop', {}).get('page', '#')})")

                    #Botón para guardar en la base de datos
                    if st.button("Guardar este contenido en mi base de datos"):
                        doc = Document(page_content=contenido_wikipedia, metadata={"source": titulo_articulo})
                        splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)
                        chunks = splitter.split_documents([doc])
                        vstore.add_documents(chunks)  

                        collection = chroma_client.get_collection(name=INDEX_NAME)
                        st.write(f"Documentos en la colección: {len(collection.get()['ids'])}")


                        previos = set(load_name_files(FILE_LIST))
                        nuevos = save_name_files(FILE_LIST, [titulo_articulo])
                        if titulo_articulo not in previos:
                            st.session_state.archivos.append(titulo_articulo)
                            st.success(f"Contenido de '{titulo_articulo}' guardado correctamente.")
                        else:
                            st.info(f"El artículo '{titulo_articulo}' ya estaba guardado.")

                        with st.sidebar:
                                archivos = load_name_files(FILE_LIST)
                                if archivos:
                                    st.write("Artículos procesados:")
                                    for arch in archivos:
                                        st.write(arch)
            else:
                st.error("No se pudo obtener información de Wikipedia.")
    elif contexto_completo:
        with st.expander("Fuentes utilizadas"):
            for doc in retrieved_docs:
                st.write(f"- **{doc.metadata.get('source', 'Desconocido')}**: {doc.page_content[:300]}...")





#ESTO ES CON MEMORIA PERO SIN EL BOTON

import streamlit as st
#separar el rag con la interfaz, historial que se le pase al llm
import urllib.parse
import requests
from langchain_chroma import Chroma #langchain_chroma
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from utils.db_utils import  load_name_files, clean_files, buscar_en_wikipedia, save_name_files
from utils.wikipedia_utils import store_wikipedia_articles
from config import INDEX_NAME, FILE_LIST, EMBEDDING_MODEL, LLM_MODEL, LLM_BASE_URL, CHROMA_HOST
import chromadb
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


# Configuración de Chroma y Embeddings
chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=8000)
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vstore = Chroma(
    collection_name=INDEX_NAME,
    embedding_function=embeddings,
    client=chroma_client 
)

st.set_page_config('PreguntaWiki')
st.header("Pregunta sobre Historia y Guerras")

#Inicializar la memoria de conversación
if 'memory' not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, input_key = "question", output_key = "answer")

# Cargar archivos en sesión si no están
if 'archivos' not in st.session_state:
    st.session_state.archivos = load_name_files(FILE_LIST)


with st.sidebar:
    query = st.text_input("Buscar en Wikipedia:")
    num_articles = st.number_input("Número de artículos", min_value=1, max_value=500, value=5)
    
    if st.button("Buscar y Procesar"):
        store_wikipedia_articles(query, num_articles)
        st.session_state.archivos = load_name_files(FILE_LIST)
        st.success(f"{num_articles} artículos sobre '{query}' procesados y almacenados.")


    st.write("Artículos procesados:")
    for arch in st.session_state.archivos:
        st.write(arch)

    if st.button('Borrar artículos'):
        clean_files(FILE_LIST)
        st.session_state.archivos = []
        st.success("Base de datos limpiada.")

user_question = st.text_input("Pregunta sobre los artículos:")

if user_question:
    llm = ChatOllama(model=LLM_MODEL, temperature=0.7, num_predict=500, base_url=LLM_BASE_URL,
                     system="Eres un experto en historia y conflictos militares. "
           "Responde solo si la respuesta está explícitamente en el contexto proporcionado. "
           "Si no puedes encontrar la información en el contexto, responde exactamente: "
           "'No tengo información almacenada en mi base de datos para responder esa pregunta.'")

    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vstore.as_retriever(search_type='similarity', search_kwargs={"k": 5}),
        memory=st.session_state.memory,
        return_source_documents=True,
        output_key="answer"
    )

    result = qa_chain.invoke({"question": user_question})
    respuesta_final = result["answer"]
    retrieved_docs = result.get("source_documents", [])

    st.write(respuesta_final)

    if "no tengo información almacenada" in respuesta_final.lower():
        if st.button("🔎 Buscar en Wikipedia"):
            titulo_articulo = buscar_en_wikipedia(user_question)
            if titulo_articulo:
                termino_codificado = urllib.parse.quote(titulo_articulo)
                wiki_url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{termino_codificado}"
                wiki_response = requests.get(wiki_url)
                if wiki_response.status_code == 200:
                    data = wiki_response.json()
                    contenido_wikipedia = data.get("extract", "") #esto es para extraer la información codificada de wikipe
                    
                    st.write(f"**Wikipedia:** {data.get('title', 'Sin título')}")
                    st.write(contenido_wikipedia)
                    st.write(f"[Ver en Wikipedia]({data.get('content_urls', {}).get('desktop', {}).get('page', '#')})")

                    #Botón para guardar en la base de datos
                    if st.button("Guardar este contenido en mi base de datos"):
                        doc = Document(page_content=contenido_wikipedia, metadata={"source": titulo_articulo})
                        splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)
                        chunks = splitter.split_documents([doc])
                        ids = vstore.add_documents(chunks)  
                        st.write(f"Documentos añadidos a Chroma: {len(ids)}")

                        collection = chroma_client.get_collection(name=INDEX_NAME)
                        st.write(f"Documentos en la colección: {len(collection.get()['ids'])}")


                        previos = set(load_name_files(FILE_LIST))
                        nuevos = save_name_files(FILE_LIST, [titulo_articulo])
                        if titulo_articulo not in previos:
                            st.session_state.archivos.append(titulo_articulo)
                            st.success(f"Contenido de '{titulo_articulo}' guardado correctamente.")
                        else:
                            st.info(f"El artículo '{titulo_articulo}' ya estaba guardado.")

            else:
                st.error("No se pudo obtener información de Wikipedia.")
    elif retrieved_docs:
        with st.expander("Fuentes utilizadas"):
            for doc in retrieved_docs:
                st.write(f"- **{doc.metadata.get('source', 'Desconocido')}**: {doc.page_content[:300]}...")


if st.session_state.memory.buffer:
    st.subheader("Historial de conversación")
    for i, mensaje in enumerate(st.session_state.memory.buffer, 1):
        rol = "Usuario" if mensaje.type == "human" else "Asistente"
        st.markdown(f"**{rol} {i}:** {mensaje.content}")


#ESTO ES SIN LO DE LA MEMORIA PERO EL SEGUNDO BOTÓN SI FUNCIONA

import streamlit as st
#separar el rag con la interfaz, historial que se le pase al llm
import urllib.parse
import requests
from langchain_chroma import Chroma #langchain_chroma
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from utils.db_utils import  load_name_files, clean_files, buscar_en_wikipedia, save_name_files
from utils.wikipedia_utils import store_wikipedia_articles
from config import INDEX_NAME, FILE_LIST, EMBEDDING_MODEL, LLM_MODEL, LLM_BASE_URL, CHROMA_HOST
import chromadb
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


# Configuración de Chroma y Embeddings
chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=8000)
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vstore = Chroma(
    collection_name=INDEX_NAME,
    embedding_function=embeddings,
    client=chroma_client 
)

st.set_page_config('PreguntaWiki')
st.header("Pregunta sobre Historia y Guerras")

#Inicializar la memoria de conversación
if 'memory' not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, input_key = "question", output_key = "answer")



with st.sidebar:
    query = st.text_input("Buscar en Wikipedia:")
    num_articles = st.number_input("Número de artículos", min_value=1, max_value=500, value=5)
    
    if st.button("Buscar y Procesar"):
        store_wikipedia_articles(query, num_articles)
        st.session_state.archivos = load_name_files(FILE_LIST)
        st.success(f"{num_articles} artículos sobre '{query}' procesados y almacenados.")

    if 'archivos' not in st.session_state:
        st.session_state.archivos = load_name_files(FILE_LIST)


    st.write("Artículos procesados:")
    for arch in st.session_state.archivos:
        st.write(arch)

    if st.button('Borrar artículos'):
        clean_files(FILE_LIST)
        st.session_state.archivos = []
        st.success("Base de datos limpiada.")

user_question = st.text_input("Pregunta sobre los artículos:")

if user_question:
    # Recuperar historial de conversación de memoria
    historial = ""
    if st.session_state.memory.buffer:
        historial = "\n".join(
            [f"{'Usuario' if m.type == 'human' else 'Asistente'}: {m.content}" 
             for m in st.session_state.memory.buffer]
        )

    # Recuperar documentos relacionados desde la base vectorial
    retriever = vstore.as_retriever(search_type='similarity', search_kwargs={"k": 5})
    retrieved_docs = retriever.invoke(user_question)
    context_chunks = [doc.page_content.strip() for doc in retrieved_docs if doc.page_content.strip()]
    contexto_completo = " ".join(context_chunks)

    # Crear LLM
    llm = ChatOllama(
        model=LLM_MODEL,
        temperature=0.7,
        num_predict=500,
        base_url=LLM_BASE_URL
    )

    # Construir prompt personalizado
    prompt = f"""
Eres un experto en historia y conflictos militares. Responde siempre en **español**.
Responde solo si la respuesta está explícitamente en el contexto proporcionado.
Si no puedes encontrar la información en el contexto, responde exactamente esta frase:
"No tengo información almacenada en mi base de datos para responder esa pregunta."

Historial de conversación:
{historial}

Contexto recuperado de la base de datos:
{contexto_completo}

Pregunta: {user_question}

Respuesta:
"""

    # Llamar al modelo
    respuesta_llm = llm.invoke(prompt)
    respuesta_final = respuesta_llm.content if hasattr(respuesta_llm, "content") else respuesta_llm

    # Mostrar resultado
    st.write(respuesta_final)

    # Guardar en la memoria
    st.session_state.memory.chat_memory.add_user_message(user_question)
    st.session_state.memory.chat_memory.add_ai_message(respuesta_final)


    if "no tengo información almacenada" in respuesta_final.lower():

        if 'wikipedia_data' not in st.session_state:
            st.session_state.wikipedia_data = {}

        if st.button("🔎 Buscar en Wikipedia"):
            titulo_articulo = buscar_en_wikipedia(user_question)
            if titulo_articulo:
                termino_codificado = urllib.parse.quote(titulo_articulo)
                wiki_url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{termino_codificado}"
                wiki_response = requests.get(wiki_url)
                if wiki_response.status_code == 200:
                    data = wiki_response.json()
                    contenido_wikipedia = data.get("extract", "")
                    st.session_state.wikipedia_data = {
                        "titulo": titulo_articulo,
                        "contenido": contenido_wikipedia,
                        "url": data.get("content_urls", {}).get("desktop", {}).get("page", "#")
                    }
                else:
                    st.error("No se pudo obtener información de Wikipedia.")

        # Mostrar contenido si ya se hizo la búsqueda
        if st.session_state.wikipedia_data:
            data = st.session_state.wikipedia_data
            st.write(f"**Wikipedia:** {data['titulo']}")
            st.write(data['contenido'])
            st.write(f"[Ver en Wikipedia]({data['url']})")

            if st.button("Guardar este contenido en mi base de datos"):
                doc = Document(page_content=data['contenido'], metadata={"source": data['titulo']})
                splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)
                chunks = splitter.split_documents([doc])
                vstore.add_documents(chunks)

                collection = chroma_client.get_collection(name=INDEX_NAME)
                st.write(f"Documentos en la colección: {len(collection.get()['ids'])}")

                previos = set(load_name_files(FILE_LIST))
                nuevos = save_name_files(FILE_LIST, [data['titulo']])
                if data['titulo'] not in previos:
                    st.session_state.archivos.append(data['titulo'])
                    st.success(f"Contenido de '{data['titulo']}' guardado correctamente.")
                else:
                    st.info(f"El artículo '{data['titulo']}' ya estaba guardado.")
    
    elif retrieved_docs:
        with st.expander("Fuentes utilizadas"):
            for doc in retrieved_docs:
                st.write(f"- **{doc.metadata.get('source', 'Desconocido')}**: {doc.page_content[:300]}...")


if st.session_state.memory.buffer:
    st.subheader("Historial de conversación")
    for i, mensaje in enumerate(st.session_state.memory.buffer, 1):
        rol = "Usuario" if mensaje.type == "human" else "Asistente"
        st.markdown(f"**{rol} {i}:** {mensaje.content}")



#SE SUPONE QUE FUNCIONA TODO