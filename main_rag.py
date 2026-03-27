import os
from dotenv import load_dotenv, find_dotenv 
from pypdf import PdfReader    
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma 
from langchain_core.prompts import ChatPromptTemplate 
from langchain_core.runnables import RunnablePassthrough 
from langchain_core.output_parsers import StrOutputParser 
import tiktoken 

load_dotenv() 

dotenv_path = find_dotenv()
print(f"DEBUG: .env file found at: {dotenv_path}") 

if dotenv_path:
    with open(dotenv_path, 'r') as f:
        print("DEBUG: Content of .env file (as read by Python):")
        print(f.read()) 
else:
    print("DEBUG: .env file NOT FOUND. Please ensure it exists in the project root or a parent directory.")


load_dotenv(dotenv_path=dotenv_path) 

PDF_DIR = "./docs" 
CHROMA_DB_PATH = "./chroma_db" 

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME") or "llama-3.3-70b-versatile"

if not GROQ_API_KEY:
    raise ValueError("Error: GROQ_API_KEY no está configurada en el archivo .env.")

print(f"Usando Groq con modelo: {GROQ_MODEL_NAME}")

llm = ChatGroq(
    model=GROQ_MODEL_NAME,
    groq_api_key=GROQ_API_KEY,
    temperature=0.0 
)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

encoding = tiktoken.get_encoding("cl100k_base")

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrae todo el texto de un archivo PDF."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or "" 
    return text

def load_pdfs_from_directory(directory_path: str) -> dict[str, str]:
    """Carga todos los PDFs de un directorio y extrae su texto."""
    pdf_texts = {}
    if not os.path.exists(directory_path):
        print(f"Advertencia: El directorio '{directory_path}' no existe. Creando uno.")
        os.makedirs(directory_path)
        print("Por favor, coloca tus archivos PDF en esta carpeta y ejecuta de nuevo.")
        return {} 
        
    for filename in os.listdir(directory_path):
        if filename.endswith(".pdf"): 
            file_path = os.path.join(directory_path, filename)
            print(f"Extrayendo texto de: {filename}")
            pdf_texts[filename] = extract_text_from_pdf(file_path)
    return pdf_texts

def create_vector_database(pdf_texts: dict[str, str], db_path: str = CHROMA_DB_PATH):
    """
    Crea una base de datos vectorial (ChromaDB) a partir de textos de PDFs.
    Los textos se dividen en chunks, se generan embeddings y se almacenan.
    """
    all_texts = []
    metadata = []

    for filename, text in pdf_texts.items():
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,      
            chunk_overlap=200,    
            length_function=len,
            is_separator_regex=False,
        )
        chunks = text_splitter.split_text(text)
        print(f"  Dividido '{filename}' en {len(chunks)} chunks.")

        for i, chunk in enumerate(chunks):
            num_tokens = len(encoding.encode(chunk)) 
            
            all_texts.append(chunk)
            metadata.append({"source": filename, "chunk_id": i, "tokens": num_tokens})

    print(f"Total de chunks procesados para indexación: {len(all_texts)}")

    
    vectorstore = Chroma.from_texts(
    texts=all_texts,
    embedding=embeddings, 
    metadatas=metadata,
    persist_directory=db_path 
    )
    
    print(f"Base de datos vectorial creada y guardada en {db_path}")
    return vectorstore

def get_retriever(db_path: str = CHROMA_DB_PATH):
    """
    Carga la base de datos vectorial existente y devuelve un 'retriever'.
    El retriever es el que busca los chunks relevantes.
    """
    
    if not os.path.exists(db_path) or not os.listdir(db_path):
        raise RuntimeError(f"La base de datos vectorial no existe o está vacía en '{db_path}'. Ejecuta este script con PDFs en './docs' para crearla primero.")
    
    vectorstore = Chroma(persist_directory=db_path, embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4}) 
    return retriever


def create_rag_chain(retriever):
    """
    Crea la cadena RAG usando LangChain.
    Esta cadena:
    1. Toma tu pregunta.
    2. Usa el 'retriever' para buscar contexto en la base de datos.
    3. Combina tu pregunta con el contexto en una plantilla (prompt).
    4. Envía el prompt al LLM (Llama) para generar la respuesta.
    5. Parsea la respuesta del LLM a texto simple.
    """
    
    template = """Responde a la pregunta basándote **únicamente** en el siguiente contexto proporcionado.
    Si la respuesta no se encuentra en el contexto, simplemente di que no tienes suficiente información.

    Contexto:
    {context}

    Pregunta: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)

    
    rag_chain = (
        
        
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain


def main():
    """
    Función principal que orquesta todo el proceso:
    1. Carga o crea la base de datos vectorial.
    2. Entra en un bucle para que el usuario pueda hacer preguntas.
    """
    
    print("\n--- Iniciando sistema RAG ---")

    if not os.path.exists(CHROMA_DB_PATH) or not os.listdir(CHROMA_DB_PATH):
        print("La base de datos vectorial no existe o está vacía. Procesando PDFs para crearla...")
        pdf_documents = load_pdfs_from_directory(PDF_DIR)
        if not pdf_documents:
            print("No se encontraron PDFs en el directorio './docs'. Por favor, agrega tus PDFs y vuelve a ejecutar.")
            return 
        vector_db = create_vector_database(pdf_documents)
    else:
        print(f"Cargando base de datos vectorial existente desde {CHROMA_DB_PATH}...")
        
    try:
        retriever = get_retriever()
        rag_chain = create_rag_chain(retriever)
        print("¡Sistema RAG listo para recibir preguntas!")
        print("Escribe 'salir' para terminar.")
    except RuntimeError as e:
        print(f"Error crítico al preparar el sistema RAG: {e}")
        print("Asegúrate de que tus PDFs están en la carpeta './docs' y tu archivo .env está configurado correctamente.")
        return 

    
    while True:
        question = input("\nTu pregunta (o 'salir' para terminar): ")
        if question.lower() == 'salir':
            print("Saliendo del sistema RAG. ¡Hasta pronto!")
            break
        
        print("Buscando en tus documentos y generando respuesta...")
        try:
            
            response = rag_chain.invoke(question)
            print(f"\nRespuesta del RAG: {response}")
        except Exception as e:
            print(f"Ocurrió un error al procesar tu pregunta: {e}")
            print("Asegúrate de que tu clave API, la URL base y el nombre del modelo son correctos y que tienes conexión a internet.")


if __name__ == "__main__":
    main() 