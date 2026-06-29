# Anomal.ia — TFG · Ingeniería Multimedia

Herramienta web apoyada en IA para asistir al operador SCADA en la
interpretación de datos y la detección de anomalías sobre infraestructuras
técnicas críticas (redes de agua, energía, etc.).

Parte del planteamiento y de la taxonomía propuestos en Arnau-Muñoz et al.
(*Mitigating Cognitive Burden in Water Network Management with LLM-based
Conversational Agents*, 2025) e incorpora dos aportaciones propias:

- Una **comparativa cuantitativa entre modelos** con indicador global
  ponderado `I = 0,55·Calidad + 0,30·Velocidad + 0,15·Concisión`.
- Un **router adaptativo por complejidad** que selecciona un prompt
  especializado según el nivel detectado de la consulta, mitigando el
  *valle de interferencia* identificado en el trabajo de referencia.

---

## Puesta en marcha

### 1. Clonar y entrar

```bash
git clone <url-del-repo>
cd tfg-agentes-ia
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv
source venv/bin/activate          # en Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configurar las claves API

Copia el fichero de plantilla y rellena con tus claves:

```bash
cp .env.example .env
```

Edita `.env` y añade al menos una de las dos claves (con cualquiera de las
dos la app funciona; con ambas puedes comparar entre proveedores):

```env
GROQ_API_KEY=tu_clave_groq
MISTRAL_API_KEY=tu_clave_mistral
```

- Obtén una clave gratuita de Groq en https://console.groq.com/keys
- Obtén una clave gratuita de Mistral en https://console.mistral.ai/api-keys

### 4. Arrancar la app

```bash
streamlit run app.py
```

La interfaz se abre en `http://localhost:8501`.

---

## Estructura del proyecto

```
app.py                       Punto de entrada Streamlit
src/
  config.py                  Catálogo de modelos, rangos operacionales, pesos
  providers.py               Acceso unificado a Mistral AI y Groq (Llama)
  classifier.py              Clasificador híbrido (heurística + LLM)
  prompts.py                 Plantillas de prompt especializadas por nivel
  router.py                  Flujo adaptativo + baseline
  evaluation.py              Evaluador de cinco componentes ponderados
  verification.py            Verificación numérica y aritmética
  scada.py                   Carga de dataset + contexto inyectable al LLM
  reference_bank.py          Lookup de respuestas oficiales del paper
  results_store.py           Persistencia de resultados del router
  ui/
    common.py                Componentes reutilizables
    styles.py                CSS global de la marca
    page_resumen.py          Vista 1 — Resumen
    page_scada.py            Vista 2 — Monitorización SCADA
    page_compare.py          Vista 3 — Comparativa de modelos
    page_router.py           Vista 4 — Router adaptativo
    page_flow.py             Vista 5 — Diagrama del flujo
    page_results.py          Vista 6 — Resultados obtenidos
data/
  dataset_evaluacion.csv     Dataset sintético por defecto (red de agua)
  red_electrica.csv          Dataset sintético alternativo (red eléctrica)
.streamlit/
  config.toml                Tema visual (paleta navy/teal)
.env.example                 Plantilla de configuración
requirements.txt             Dependencias Python
```

---

## Las 6 vistas de la interfaz

1. **Resumen** — marco del TFG, planteamiento del problema y propuesta.
2. **Monitorización SCADA** — selector y uploader del dataset activo;
   inspección tabular de los datos.
3. **Comparativa de modelos** — misma consulta lanzada a varios LLM en
   igualdad de condiciones; ranking según el indicador global
   `I = 0,55·Q + 0,30·V + 0,15·C` que recomienda el modelo óptimo.
4. **Router adaptativo** — clasifica la consulta y contrasta el flujo
   baseline (prompt genérico) frente al flujo adaptativo (prompt
   especializado por nivel + verificación numérica previa).
5. **Flujo del router** — diagrama explicativo del proceso interno.
6. **Resultados obtenidos** — comparación cara a cara entre las
   respuestas del modelo del paper y las del router del TFG sobre el
   banco oficial de consultas.

---

## Stack tecnológico

| Bloque | Librería | Versión mínima | Función |
|---|---|---|---|
| Frontend / UI | `streamlit` | ≥ 1.32 | Construcción de la interfaz web |
| Proveedores LLM | `mistralai` | ≥ 1.0 | SDK oficial de Mistral AI |
| Proveedores LLM | `groq` | ≥ 0.11 | SDK de Groq para inferencia de Llama |
| Procesamiento de datos | `pandas` | ≥ 2.0 | Manipulación de datasets tabulares |
| Configuración | `python-dotenv` | ≥ 1.0 | Carga de claves API desde `.env` |

`numpy` se instala como dependencia transitiva de `pandas`.

---

## Cómo usar la app (recorrido recomendado)

1. **Carga un dataset** en la vista *Monitorización SCADA*. Por defecto se
   usa `dataset_evaluacion.csv`. Puedes subir cualquier CSV propio.
2. **Lanza una consulta** en *Comparativa de modelos* para ver qué LLM
   responde mejor según el indicador global.
3. **Pasa al Router adaptativo** y compara la respuesta baseline (prompt
   genérico) frente a la adaptativa (prompt especializado por nivel).
4. **Consulta el flujo interno** en *Flujo del router* para entender la
   arquitectura del sistema.
5. **Revisa la documentación** experimental en *Resultados obtenidos*.

---

## Limitaciones conocidas

- El sistema requiere conexión a internet y consume cuota de API del
  proveedor seleccionado (Mistral, Groq). Ambos ofrecen tier gratuito
  con cuotas diarias acotadas.
- El clasificador híbrido alterna entre heurística (instantánea) y LLM
  (si la heurística no está segura); la primera llamada del LLM de la
  sesión arrastra un cold start de ~1 s.
- La verificación aritmética detecta errores en cálculos explícitos
  pero no errores conceptuales (uso de fórmula incorrecta con aritmética
  bien hecha).

---

## Cita académica

Este TFG se inspira en y extiende el siguiente trabajo:

> Arnau-Muñoz et al. (2025). *Mitigating Cognitive Burden in Water Network
> Management with LLM-based Conversational Agents.*

El dataset operacional real y las respuestas oficiales del modelo
fine-tuneado de dicho trabajo no se incluyen en este repositorio público
y se han utilizado únicamente en local con fines académicos.

---

## Autor

**Jordi Valentín Ivanov**
TFG · Ingeniería Multimedia
Universidad de Alicante · 2025–26
