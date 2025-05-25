
import streamlit as st
#separar el rag con la interfaz, historial que se le pase al llm
import urllib.parse
import requests
from langchain_chroma import Chroma #langchain_chroma
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from utils.db_utils import  load_name_files, clean_files, buscar_en_wikipedia, save_name_files
from utils.wikipedia_utils import store_wikipedia_articles, get_article_summary
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
    st.session_state.memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        input_key="question",
        output_key="answer"
    )

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
    # Inicializar modelo LLM
    llm = ChatOllama(
        model=LLM_MODEL,
        temperature=0.7,
        num_predict=500,
        base_url=LLM_BASE_URL
    )

    prompt_template = PromptTemplate.from_template("""
Eres un experto en historia y conflictos militares. Responde siempre en **español**.
Responde solo si la respuesta está explícitamente en el contexto proporcionado.
Si no puedes encontrar la información en el contexto, responde exactamente esta frase:
"No tengo información almacenada en mi base de datos para responder esa pregunta."

Historial de conversación (puede ayudarte a entender el contexto):
{chat_history}

Contexto recuperado de la base de datos:
{context}

Pregunta: {question}

Respuesta:
""")
    # Recuperar documentos relacionados desde la base vectorial
    retriever = vstore.as_retriever(search_type='similarity', search_kwargs={"k": 5})

    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=st.session_state.memory,
        return_source_documents=True,
        output_key="answer",
        combine_docs_chain_kwargs={"prompt": prompt_template}
    )

    response = qa_chain.invoke({"question": user_question})
    respuesta_final = response['answer']
    retrieved_docs = response.get("source_documents", [])

    # Mostrar resultado
    st.write(respuesta_final)


    if "no tengo información almacenada" in respuesta_final.lower():

        if 'wikipedia_data' not in st.session_state:
            st.session_state.wikipedia_data = {}

        if st.button("🔎 Buscar en Wikipedia"):
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