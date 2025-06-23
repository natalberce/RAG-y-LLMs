import os
from config import FILE_LIST, INDEX_NAME
import requests
import urllib
import time 
from config import CHROMA_CLIENT as chroma_client




def buscar_en_wikipedia(pregunta):
    if not pregunta.strip():
        return None  
    termino_codificado = urllib.parse.quote(pregunta)
    url_busqueda = f"https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={termino_codificado}&format=json"
    try:
        time.sleep(1)
        response = requests.get(url_busqueda, timeout=10)
        response.raise_for_status()
        data = response.json()
        resultados = data.get("query", {}).get("search", [])
        if resultados:
            return resultados[0]["title"]
    except Exception as e:
        print(f"Error al buscar en Wikipedia: {e}")

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
    open(path, "w").close()

    existing_collections = chroma_client.list_collections()
    if INDEX_NAME in existing_collections:
        chroma_client.delete_collection(name=INDEX_NAME)

    return True



def delete_specific_articles(titulos):
    """
    Elimina artículos específicos de ChromaDB y del archivo FILE_LIST.
    """
    collection = chroma_client.get_collection(name=INDEX_NAME)
    all_data = collection.get(include=["metadatas"])

    ids = all_data["ids"]
    metadatas = all_data["metadatas"]

    # Buscar los IDs que coincidan con los títulos
    ids_a_borrar = [
        doc_id for doc_id, metadata in zip(ids, metadatas)
        if metadata.get("source", "").lower() in [t.lower() for t in titulos]
    ]

    if ids_a_borrar:
        collection.delete(ids=ids_a_borrar)
        print(f"Se han eliminado {len(ids_a_borrar)} documentos de la base vectorial.")
    else:
        print("No se encontraron documentos con esos títulos en ChromaDB.")

    # Actualiza el archivo eliminando los títulos borrados
    articulos_actuales = load_name_files(FILE_LIST)
    nuevos = [a for a in articulos_actuales if a.lower() not in [t.lower() for t in titulos]]

    with open(FILE_LIST, "w", encoding="utf-8") as f:
        for art in nuevos:
            f.write(art + "\n")




