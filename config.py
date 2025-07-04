INDEX_NAME = 'wiki_europa_contemporanea'

FILE_LIST = "articulos.txt"
CHROMA_HOST = 'localhost'
CHROMA_PORT = 8000

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL = "llama3"
LLM_BASE_URL = "https://ollama.gsi.upm.es/"

CATEGORIA_INICIAL = "Historia contemporánea de Europa"
NUM_ARTICULOS_INICIALES = 100
import chromadb

CHROMA_CLIENT = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

