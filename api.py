from fastapi import FastAPI, HTTPException 
from pydantic import BaseModel 
import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from fastapi.middleware.cors import CORSMiddleware 
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

PDF_DIR = "./docs"
CHROMA_DB_PATH = "./chroma_db" 

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME") or "llama-3.3-70b-versatile"

if not GROQ_API_KEY:
    raise ValueError("Error: GROQ_API_KEY no está configurada en el archivo .env.")

llm = ChatGroq(
    model=GROQ_MODEL_NAME,
    groq_api_key=GROQ_API_KEY,
    temperature=0.0
)

# Usar embeddings locales gratuitos (HuggingFace)
# Esto descargará un pequeño modelo la primera vez (~400MB)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

def get_retriever(db_path: str = CHROMA_DB_PATH):
    """
    Carga la base de datos vectorial existente y devuelve un retriever.
    """
    if not os.path.exists(db_path) or not os.listdir(db_path):
        raise RuntimeError(f"La base de datos vectorial no existe o está vacía en '{db_path}'. Ejecuta 'python main_rag.py' primero para crearla.")

    vectorstore = Chroma(persist_directory=db_path, embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    return retriever

def create_rag_chain(retriever):
    """
    Crea la cadena RAG utilizando LangChain.
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

app = FastAPI(
    title="RAG PDF API con Llama",
    description="API para consultar PDFs usando un sistema RAG con Llama (vía API).",
    version="1.0.0",
)

origins = [
    "http://localhost",
    "http://localhost:8000", 
    "http://127.0.0.1:8000",
    "null", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      
    allow_credentials=True,      
    allow_methods=["*"],         
    allow_headers=["*"],         
)

rag_chain = None 
retriever_initialized = False 

@app.on_event("startup")
async def startup_event():
    global rag_chain, retriever_initialized
    try:
        print("Iniciando la carga del sistema RAG para la API...")
        current_retriever = get_retriever()
        rag_chain = create_rag_chain(current_retriever)
        retriever_initialized = True
        print("Sistema RAG cargado y listo para la API.")
    except RuntimeError as e:
        print(f"ERROR: No se pudo inicializar el sistema RAG para la API: {e}")
        print("Por favor, asegúrate de haber ejecutado 'python main_rag.py' al menos una vez para crear la base de datos vectorial.")

class QueryRequest(BaseModel):
    query: str 
    pdf: str

class QueryResponse(BaseModel):
    answer: str 

@app.get("/", summary="Estado de la API")
async def read_root():
    """
    Endpoint de prueba para verificar si la API está funcionando.
    """
    if retriever_initialized:
        return {"message": "RAG PDF API está en funcionamiento y el sistema RAG ha sido cargado exitosamente."}
    else:
        return {"message": "RAG PDF API está en funcionamiento, pero el sistema RAG NO pudo ser cargado. Revise los logs del servidor para ver el error de inicialización."}
    
@app.post("/query", response_model=QueryResponse, summary="Realiza una pregunta sobre un PDF específico")
async def query_pdf(request: QueryRequest): 
    global rag_chain 
    
    if not retriever_initialized: 
        raise HTTPException(status_code=500, detail="El sistema RAG no se pudo inicializar. Verifique los logs del servidor para más detalles.")

    try:
        print(f"Recibida consulta: '{request.query}' para PDF: '{request.pdf}'")
        
        vectorstore = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embeddings)
        
        retriever = vectorstore.as_retriever(
            search_kwargs={
                "k": 4, 
                "filter": {"source": request.pdf} 
            }
        )

        current_rag_chain = create_rag_chain(retriever)
        
        response = current_rag_chain.invoke(request.query)
        
        print(f"Respuesta generada para '{request.pdf}'.")
        return QueryResponse(answer=response)
    except Exception as e:
        print(f"Error al procesar la consulta: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar la consulta: {str(e)}")
