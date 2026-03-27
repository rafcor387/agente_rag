# 🇧🇴 Conoce Bolivia: Sistema RAG Inteligente

Sistema de **Retrieval-Augmented Generation (RAG)** diseñado para consultar documentos históricos y de actualidad sobre Bolivia. Utiliza **Groq** para inferencia de alta velocidad y **HuggingFace** para embeddings locales gratuitos.

## 🚀 Características
- **Filtrado Específico:** Permite consultar documentos individuales (Independencia, Guerras, Actualidad) de forma aislada.
- **Inferencia Ultra-rápida:** Integración con la API de Groq Cloud.
- **Privacidad y Costo Cero en Embeddings:** Generación de vectores localmente con `sentence-transformers`.
- **Arquitectura Moderna:** Backend con FastAPI y Frontend interactivo con Vanilla CSS/JS.

## 🛠️ Requisitos Técnicos
- Python 3.10+
- Groq API Key (Obtenla en [Groq Console](https://console.groq.com/))
- Documentos PDF en la carpeta `./docs`

## 📦 Instalación

1. **Clonar el repositorio y crear entorno virtual:**
   ```powershell
   git clone <tu-repo-url>
   cd rag-bolivia
   python -m venv venv
   ./venv/Scripts/Activate.ps1
   ```

2. **Instalar dependencias:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno (`.env`):**
   Crea un archivo `.env` en la raíz con:
   ```env
   GROQ_API_KEY=tu_gsk_clave_aqui
   GROQ_MODEL_NAME=llama-3.3-70b-versatile
   ```

## 📖 Guía de Uso

### Paso 1: Indexación de Documentos
Antes de usar la API, debes procesar los PDFs para crear la base de datos vectorial:
```powershell
python main_rag.py
```
*Este paso generará la carpeta `chroma_db/`*

### Paso 2: Iniciar el Servidor Backend
Lanza la API de FastAPI con Uvicorn:
```powershell
uvicorn api:app --reload
```

### Paso 3: Interfaz Frontend
Simplemente abre el archivo `index.html` en tu navegador. Selecciona una tarjeta de tema y realiza tu pregunta.

## 📂 Estructura del Proyecto
- `main_rag.py`: Lógica de procesamiento de documentos y CLI de prueba.
- `api.py`: Servidor FastAPI con endpoints de consulta filtrada.
- `docs/`: Carpeta contenedora de los archivos PDF fuente.
- `chroma_db/`: Base de datos vectorial local (SQLite + Vectores).
- `requirements.txt`: Lista depurada de dependencias principales.

## 🛠️ Tecnologías Utilizadas
- **LLM:** [Groq Cloud]
- **Framework RAG:** [LangChain]
- **Base de Datos Vectorial:** [ChromaDB]
- **Embeddings:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (HuggingFace)
- **Backend:** [FastAPI] + [Uvicorn]
- **Frontend:** HTML5, Vanilla CSS, JavaScript (ES6+)

## ⚖️ Licencia
Este proyecto es de código abierto. ¡Siéntete libre de contribuir!

---
*Este proyecto fue desarrollado con fines educativos para preservar y difundir el conocimiento histórico de Bolivia mediante Inteligencia Artificial.*
