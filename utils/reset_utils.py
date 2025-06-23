




import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from config import FILE_LIST, INDEX_NAME, EMBEDDING_MODEL, CATEGORIA_INICIAL, NUM_ARTICULOS_INICIALES
from utils.db_utils import clean_files
from utils.wikipedia_utils import store_wikipedia_articles

import time

def resetear_aplicacion():
    clean_files(FILE_LIST)
    from config import CHROMA_CLIENT as chroma_client

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    # Eliminar (ya lo hace clean_files), crear colección
    chroma_client.create_collection(name=INDEX_NAME)
    time.sleep(5) 

    vstore = Chroma(
        collection_name=INDEX_NAME,
        embedding_function=embeddings,
        client=chroma_client
    )

    store_wikipedia_articles(CATEGORIA_INICIAL, NUM_ARTICULOS_INICIALES, vstore)

