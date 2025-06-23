import os
import chromadb
from config import FILE_LIST, INDEX_NAME, CHROMA_HOST, CHROMA_PORT
import requests
import urllib

chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)



def buscar_en_wikipedia(pregunta):
    if not pregunta.strip():
        return None  
    termino_codificado = urllib.parse.quote(pregunta)
    url_busqueda = f"https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={termino_codificado}&format=json"
    response = requests.get(url_busqueda)

    if response.status_code == 200:
        try:
            data = response.json()
            resultados = data.get("query", {}).get("search", [])
            if resultados:
                return resultados[0]["title"]
        except Exception as e:
            print(f"Error al procesar la respuesta: {e}")
    else:
        print(f"Error en la petición HTTP: {response.status_code}")

    return None






def save_name_files(path, new_files):
    """Guarda nombres de archivos en un fichero, evitando duplicados."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    old_files = load_name_files(path)
    with open(path, "a", encoding="utf-8") as file:
        for item in new_files:
            if item not in old_files:
                file.write(item + "\n")
                old_files.append(item)
    return old_files


def load_name_files(path):
    """Carga nombres de artículos previamente almacenados."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file]


def clean_files(path):
    """Limpia el fichero de artículos y reinicia la colección en ChromaDB."""
    open(path, "w").close()
    chroma_client.delete_collection(name=INDEX_NAME)
    chroma_client.create_collection(name=INDEX_NAME)
    return True


