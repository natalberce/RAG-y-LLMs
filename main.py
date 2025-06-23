from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from config import INDEX_NAME, EMBEDDING_MODEL, LLM_MODEL, LLM_BASE_URL, CHROMA_CLIENT


def init_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def init_vector_store():
    embeddings = init_embeddings()
    return Chroma(
        collection_name=INDEX_NAME,
        embedding_function=embeddings,
        client=CHROMA_CLIENT
    )


def get_prompt_template():
    return PromptTemplate.from_template("""
Eres un experto en historia y conflictos militares. Responde siempre en español.

RESPONDE SÓLO SI PUEDES ENCONTRAR LA INFORMACIÓN EN EL CONTEXTO DE ABAJO.
IGNORA el historial de conversación si contradice el contexto.
SI EL CONTEXTO ESTÁ VACÍO o no contiene la información, responde exactamente esta frase:
"No tengo información almacenada en mi base de datos para responder esa pregunta."

======== CONTEXTO ========
{context}

======== HISTORIAL ========
{chat_history}

======== PREGUNTA ========
{question}

======== RESPUESTA ========
""")


def init_memory():
    return ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        input_key="question",
        output_key="answer"
    )


def get_llm():
    return ChatOllama(
        model=LLM_MODEL,
        temperature=0.7,
        num_predict=500,
        base_url=LLM_BASE_URL
    )


def get_qa_chain(llm, retriever, memory):
    prompt_template = get_prompt_template()
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        output_key="answer",
        combine_docs_chain_kwargs={"prompt": prompt_template}
    )
