from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from utils.db_utils import save_name_files
import wikipedia
import requests
import time
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from config import EMBEDDING_MODEL, INDEX_NAME, CHROMA_HOST, CHROMA_PORT, FILE_LIST
import chromadb


wikipedia.set_lang("es")



def get_wikipedia_articles(category, limit=500, max_depth=2):
    """
    Explora recursivamente una categoría de Wikipedia y sus subcategorías hasta un límite de artículos.
    """
    import requests

    acumulados = []
    visitadas = set()

    def explorar(categoria, profundidad):
        nonlocal acumulados, visitadas

        if profundidad > max_depth or len(acumulados) >= limit or categoria in visitadas:
            return

        visitadas.add(categoria)

        URL = "https://es.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtitle": f"Categoría:{categoria}",
            "cmlimit": 500
        }

        try:
            time.sleep(1)
            response = requests.get(URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            members = data.get("query", {}).get("categorymembers", [])

            for item in members:
                title = item["title"]

                if title.startswith("Categoría:"):
                    if len(acumulados) < limit:
                        subcat = title.replace("Categoría:", "")
                        explorar(subcat, profundidad + 1)
                else:
                    if title not in acumulados:
                        acumulados.append(title)

                if len(acumulados) >= limit:
                    break

        except Exception as e:
            print(f"⚠️ Error explorando '{categoria}': {e}")

    # Empieza la exploración desde la categoría principal
    explorar(category, profundidad=0)
    return acumulados[:limit]


def get_article_summary(title):
    url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}"
    try:
        time.sleep(1)
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("extract", ""), data.get("content_urls", {}).get("desktop", {}).get("page", "")
    except Exception as e:
        print(f"Error en get_article_summary('{title}'): {e}")
    return "", ""


def is_article_in_chroma(title, collection):
    """
    Devuelve True si un artículo con ese título ya está en ChromaDB.
    """
    results = collection.get(include=["metadatas"], limit=10000)
    for meta in results["metadatas"]:
        if meta.get("source", "").lower() == title.lower():
            return True
    return False



def store_wikipedia_articles(category, limit=500, vstore = None):
    """
    Descarga artículos completos desde Wikipedia y los guarda en ChromaDB en chunks.
    """

    if vstore is None:
        raise ValueError("Debes pasar un 'vstore' válido a la función.")
    
    titles = get_wikipedia_articles("Historia contemporánea de Europa", limit=500)

    if not titles:
        print(f"No se encontraron artículos en la categoría '{category}'.")
        return


    collection = vstore._collection 
    nuevos_docs = []
    nuevos_titulos = []

    for title in titles:
        if is_article_in_chroma(title, collection):
            continue
        try:
            page = wikipedia.page(title)
            content = page.content
            url = page.url

            if content.strip():  # Validar que tenga contenido
                doc = Document(
                    page_content=content,
                    metadata={"source": title, "url": url}
                )
                nuevos_docs.append(doc)
                nuevos_titulos.append(title)

        except Exception as e:
            print(f"Error al obtener '{title}': {e}")
            continue

    if not nuevos_docs:
        print("No hay nuevos artículos válidos para almacenar.")
        return

    # Dividir en chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)
    chunks = splitter.split_documents(nuevos_docs)

    # Guardar chunks en ChromaDB
    vstore.add_documents(chunks)
    print(f"Se han añadido {len(chunks)} chunks en {len(nuevos_docs)} artículos.")

    collection = vstore._collection  # acceso interno al objeto
    ids = collection.get()["ids"]
    print(f"Total de documentos en la colección '{INDEX_NAME}': {len(ids)}")

    # Registrar artículos procesados
    save_name_files(FILE_LIST, nuevos_titulos)
    print(f"Artículos guardados: {', '.join(nuevos_titulos[:5])}...")



if __name__ == "__main__":

    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vstore = Chroma(
        collection_name=INDEX_NAME,
        embedding_function=embeddings,
        client=chroma_client
    )




