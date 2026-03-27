
const form = document.getElementById('preguntaForm');
const respuestaDiv = document.getElementById('textoRespuesta');
const submitBtn = document.getElementById('submitBtn');
const translateBtn = document.getElementById('translateBtn');
let selectedPdf = null;
let currentAnswer = ""; 
let isTranslated = false; 


document.querySelectorAll('.card').forEach(card => {
    card.addEventListener('click', () => {
        document.querySelectorAll('.card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        selectedPdf = card.getAttribute('data-pdf');
        console.log("PDF seleccionado:", selectedPdf);
    });
});


translateBtn.addEventListener('click', () => {
    if (!currentAnswer) return; 

    if (!isTranslated) {
        
        const translatedText = translateToSpanish(currentAnswer);
        respuestaDiv.textContent = translatedText;
        translateBtn.textContent = "Mostrar Original";
        isTranslated = true;
    } else {
        
        respuestaDiv.textContent = currentAnswer;
        translateBtn.textContent = "Traducir a Español";
        isTranslated = false;
    }
});


form.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!selectedPdf) {
        alert("Por favor, selecciona un PDF haciendo clic en una de las tarjetas.");
        return;
    }

    const query = document.getElementById('query').value;

    if (!query.trim()) {
        alert("Por favor, escribe tu pregunta.");
        return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Procesando...";

    respuestaDiv.textContent = "Buscando respuesta...";
    translateBtn.style.display = "none"; 
    isTranslated = false; 
    translateBtn.textContent = "Traducir a Español"; 
    currentAnswer = ""; 

    try {
        const response = await fetch('http://127.0.0.1:8000/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query, pdf: selectedPdf }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Error ${response.status}: ${errorData.detail || 'Error desconocido del servidor.'}`);
        }

        const data = await response.json();
        currentAnswer = data.answer || "No se recibió respuesta."; 
        respuestaDiv.textContent = currentAnswer;

        if (currentAnswer && currentAnswer !== "No se recibió respuesta.") {
            translateBtn.style.display = "block"; 
        } else {
            translateBtn.style.display = "none";
        }

    } catch (error) {
        console.error("Error al procesar la consulta:", error);
        respuestaDiv.textContent = `Error: ${error.message || "No se pudo conectar con el servidor."}`;
        translateBtn.style.display = "none";
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Enviar";
    }
});


function translateToSpanish(text) {
    console.log("Intentando traducir:", text);
    
    
    return "TRADUCCIÓN DE: " + text;
}
