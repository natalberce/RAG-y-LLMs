import requests
from langchain.document_loaders import WikipediaLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from utils.db_utils import save_name_files, load_name_files
from config import FILE_LIST, INDEX_NAME, EMBEDDING_MODEL, CHROMA_HOST
import chromadb
from langchain.schema import Document

chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=8000)

def get_wikipedia_articles(category, limit=500):
    """Consulta los títulos de artículos de una categoría de Wikipedia."""
    URL = "https://es.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": f"Categoría:{category}",
        "cmlimit": limit
    }
    response = requests.get(url=URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    return [item["title"] for item in data["query"]["categorymembers"] if "Categoría:" not in item["title"]]


def get_article_summary(title):
    """
    Devuelve el extracto (resumen) y URL de un artículo de Wikipedia.
    """
    url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        return data.get("extract", ""), data.get("content_urls", {}).get("desktop", {}).get("page", "")
    return "", ""





def store_wikipedia_articles(category, limit=500):
    articles = get_wikipedia_articles(category, limit)
    if not articles:
        print(f"No se encontraron artículos en la categoría '{category}'.")
        return

    previos = set(load_name_files(FILE_LIST))
    nuevos_docs = []
    nuevos_titulos = []

    for title in articles:
        if title in previos:
            continue
        content, url = get_article_summary(title)
        if content:
            doc = Document(page_content=content, metadata={"source": title, "url": url})
            nuevos_docs.append(doc)
            nuevos_titulos.append(title)

    if nuevos_docs:
        # Dividir en chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)
        chunks = splitter.split_documents(nuevos_docs)

        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

        # Guardar en ChromaDB
        Chroma.from_documents(chunks, embedding_function=embeddings, client=chroma_client, collection_name=INDEX_NAME)

        # Registrar artículos almacenados
        save_name_files(FILE_LIST, nuevos_titulos)
        print(f"Se han almacenado {len(nuevos_titulos)} nuevos artículos en ChromaDB.")
    else:
        print("No hay nuevos artículos para almacenar.")



'''def store_wikipedia_articles(category, limit=500):
    """Carga y almacena artículos de Wikipedia en ChromaDB."""
    articles = get_wikipedia_articles(category, limit)
    if not articles:
        print(f"No se encontraron artículos en la categoría '{category}'.")
        return

    loader = WikipediaLoader(query=articles, lang="es")
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)
    chunks = text_splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    Chroma.from_documents(chunks, embeddings, client=chroma_client, collection_name=INDEX_NAME)
    vstore = Chroma(
    collection_name=INDEX_NAME,
    embedding_function=embeddings,
    client=chroma_client 
)


    save_name_files(FILE_LIST, articles)
    print(f"Se han almacenado {len(articles)} artículos en ChromaDB.")

   ''' 


categoria = "Historia_de_Europa"  
store_wikipedia_articles(categoria, limit=500)
