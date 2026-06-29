"""Sistema de diseño · Caudal.

Define tokens de color, tipografía y espaciado usados en toda la aplicación.
Paleta principal: navy + teal como color de marca, con fondos fríos neutros.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --c-navy-900: #0A1F3D;
    --c-navy-800: #132B52;
    --c-navy-700: #1E3A5F;
    --c-navy-500: #334E7A;

    --c-teal-700: #0F766E;
    --c-teal-600: #0D9488;
    --c-teal-500: #14B8A6;
    --c-teal-400: #2DD4BF;
    --c-teal-100: #CCFBF1;
    --c-teal-50: #F0FDFA;

    --c-gray-950: #0F172A;
    --c-gray-700: #334155;
    --c-gray-600: #475569;
    --c-gray-500: #64748B;
    --c-gray-400: #94A3B8;
    --c-gray-300: #CBD5E1;
    --c-gray-200: #E2E8F0;
    --c-gray-100: #F1F5F9;
    --c-gray-50: #F8FAFC;

    --c-success: #10B981;
    --c-warning: #F59E0B;
    --c-danger: #EF4444;
    --c-danger-50: #FEF2F2;
    --c-danger-200: #FECACA;
    --c-danger-700: #991B1B;

    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 14px;
    --radius-pill: 999px;

    --shadow-sm: 0 1px 2px rgba(15,23,42,0.06);
    --shadow-md: 0 4px 14px rgba(15,23,42,0.08);
    --shadow-lg: 0 12px 32px rgba(10,31,61,0.12);

    --gradient-brand: linear-gradient(135deg, #14B8A6 0%, #0EA5E9 100%);
    --gradient-sidebar: linear-gradient(180deg, #0A1F3D 0%, #132B52 60%, #1E3A5F 100%);
}

/* ============================================================
   BASE
   ============================================================ */

html, body, [class*="css"] {
    font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;
    font-weight: 400;
    color: var(--c-gray-950);
    -webkit-font-smoothing: antialiased;
}

.stApp {
    background: linear-gradient(180deg, #F5F8FC 0%, #EEF2F8 100%);
    overflow-x: hidden;
}

/* Capa 1 · manchas de color en movimiento lento */
.stApp::before {
    content: '';
    position: fixed;
    inset: -15%;
    pointer-events: none;
    background:
        radial-gradient(circle 520px at 18% 28%,
            rgba(20, 184, 166, 0.22), transparent 62%),
        radial-gradient(circle 640px at 82% 72%,
            rgba(14, 165, 233, 0.18), transparent 62%),
        radial-gradient(circle 420px at 62% 18%,
            rgba(45, 212, 191, 0.14), transparent 62%),
        radial-gradient(circle 480px at 28% 88%,
            rgba(59, 130, 246, 0.10), transparent 62%);
    filter: blur(6px);
    animation: caudal-bg-drift 26s ease-in-out infinite;
    z-index: 0;
}

/* Capa 2 · rejilla técnica estática con desvanecido al borde */
.stApp::after {
    content: '';
    position: fixed;
    inset: 0;
    pointer-events: none;
    background-image:
        linear-gradient(rgba(15, 23, 42, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(15, 23, 42, 0.03) 1px, transparent 1px);
    background-size: 44px 44px;
    mask-image: radial-gradient(ellipse at center,
        rgba(0, 0, 0, 0.55), transparent 75%);
    -webkit-mask-image: radial-gradient(ellipse at center,
        rgba(0, 0, 0, 0.55), transparent 75%);
    z-index: 0;
}

@keyframes caudal-bg-drift {
    0%   { transform: translate3d(0, 0, 0)       scale(1);    }
    25%  { transform: translate3d(-2.5%, 2%, 0)  scale(1.04); }
    50%  { transform: translate3d(2%, -2.5%, 0)  scale(1.02); }
    75%  { transform: translate3d(-1.5%, -2%, 0) scale(1.06); }
    100% { transform: translate3d(0, 0, 0)       scale(1);    }
}

@media (prefers-reduced-motion: reduce) {
    .stApp::before { animation: none; }
}

.main .block-container,
section[data-testid="stSidebar"] {
    position: relative;
    z-index: 1;
}

[data-testid="stHeader"],
.stApp > header {
    background: transparent !important;
    display: flex !important;
    visibility: visible !important;
    min-height: 2.5rem !important;
    pointer-events: auto !important;
}

[data-testid="stDecoration"],
[data-testid="stStatusWidget"] {
    display: none !important;
    height: 0 !important;
    visibility: hidden !important;
}

/* Mantener stToolbar y sus controles visibles (incluye el botón de toggle sidebar) */
[data-testid="stToolbar"] {
    background: transparent !important;
    pointer-events: auto !important;
    visibility: visible !important;
    display: flex !important;
}

/* Botones de colapsar/expandir visibles (permitir ocultar y recuperar la sidebar) */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
button[kind="headerNoPadding"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    z-index: 1000 !important;
}

/* Control flotante para re-abrir la sidebar: pequeño y en la esquina superior derecha */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
    position: fixed !important;
    top: 0 !important;
    right: 0.3rem !important;
    left: auto !important;
    transform: scale(0.75) !important;
    transform-origin: top right !important;
}

/* Reducir también cualquier botón de toggle dentro del header/toolbar */
[data-testid="stToolbar"] button[kind*="header"],
[data-testid="stHeader"] button[kind*="header"],
[data-testid="stSidebarCollapseButton"] {
    transform: scale(0.8) !important;
    transform-origin: center !important;
}

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section.main {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

.main .block-container,
[data-testid="stMain"] .block-container,
section.main > div.block-container {
    max-width: 1280px;
    padding-top: 0 !important;
    padding-bottom: 1rem;
    margin-top: 1rem !important;
}

.main .block-container > div:first-child,
.main .block-container > div:first-child > div:first-child,
.main .block-container [data-testid="stVerticalBlock"]:first-child,
.main .block-container [data-testid="stVerticalBlockBorderWrapper"]:first-child {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* Títulos del contenido principal — fuera de la sidebar */
.main h1,
.main h2,
.main h3,
.main h4,
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3,
[data-testid="stMain"] h4 {
    font-family: 'Manrope', sans-serif !important;
    color: var(--c-navy-900) !important;
    letter-spacing: -0.02em;
    line-height: 1.2;
}

.main h1, [data-testid="stMain"] h1 { font-size: 4rem; font-weight: 300; letter-spacing: -0.03em; margin-top: 0; }
.main h2, [data-testid="stMain"] h2 { font-size: 2rem; font-weight: 400; margin-top: 0.8rem; }
.main h3, [data-testid="stMain"] h3 { font-size: 1.125rem; font-weight: 500; color: var(--c-navy-700) !important; margin-top: 0.8rem; }
.main h4, [data-testid="stMain"] h4 { font-size: 1rem; font-weight: 500; color: var(--c-navy-700) !important; margin-top: 0.6rem; }

p, div, span, label {
    font-family: 'Manrope', sans-serif;
    font-weight: 400;
    line-height: 1.55;
}

code, pre, .stCode, .stCode * {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
}

/* ============================================================
   SIDEBAR · brand + navigation
   ============================================================ */

section[data-testid="stSidebar"] {
    background: var(--gradient-sidebar);
    border-right: none;
    padding-top: 0 !important;
    overflow: hidden !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    overflow: hidden !important;
}

section[data-testid="stSidebar"] > div:first-child,
section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* stSidebarHeader saca de flujo para que no ocupe espacio arriba del logo */
[data-testid="stSidebarHeader"] {
    position: absolute !important;
    top: 0 !important;
    right: 0 !important;
    height: auto !important;
    min-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    z-index: 10 !important;
    background: transparent !important;
}

section[data-testid="stSidebar"] * {
    color: #E2E8F0;
}

section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4 {
    color: #FFFFFF;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
    color: #94A3B8 !important;
    margin-top: 1.4rem;
    margin-bottom: 0.5rem;
}

/* Brand: bloque a ancho completo con centrado de su texto hijo */
.caudal-brand {
    display: block;
    width: 100%;
    box-sizing: border-box;
    padding: 0 0 1rem 0;
    margin: 1.5rem 0 0.8rem 0;
    text-align: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

/* El wrapper de Streamlit que envuelve nuestro markdown: padding 0 para que .caudal-brand ocupe todo el ancho real del sidebar */
section[data-testid="stSidebar"] [data-testid="element-container"]:has(.caudal-brand) {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
}

section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]:has(.caudal-brand) {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
}

/* Logo: inline-block para que text-align:center del padre lo centre */
.caudal-logo {
    display: inline-block;
    font-family: 'Manrope', sans-serif;
    font-size: 1.6rem;
    letter-spacing: -0.03em;
    line-height: 1;
    filter: drop-shadow(0 4px 14px rgba(20, 184, 166, 0.25));
}

section[data-testid="stSidebar"] .caudal-logo-name {
    color: #FFFFFF !important;
    font-weight: 300;
}

section[data-testid="stSidebar"] .caudal-logo-ai {
    color: #2DD4BF !important;
    font-weight: 600;
}

.caudal-name {
    font-family: 'Manrope', sans-serif;
    font-weight: 300;
    font-size: 1.5rem;
    color: #FFFFFF;
    letter-spacing: -0.03em;
    display: inline-flex;
    align-items: baseline;
    gap: 0.02rem;
}

.caudal-ai {
    font-family: 'Manrope', sans-serif;
    font-size: 1.5rem;
    font-weight: 500;
    letter-spacing: -0.03em;
    color: #2DD4BF;
    text-transform: lowercase;
    padding: 0;
    background: none;
    box-shadow: none;
    border-radius: 0;
    position: static;
    top: auto;
    opacity: 0.95;
}

.caudal-tag {
    font-size: 0.68rem;
    color: #94A3B8;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.2rem;
    font-weight: 600;
}

/* Radio navigation */
section[data-testid="stSidebar"] div[role="radiogroup"] {
    width: 100%;
}

section[data-testid="stSidebar"] div[role="radiogroup"] > label {
    display: flex !important;
    width: 100% !important;
    box-sizing: border-box;
}

section[data-testid="stSidebar"] label[data-baseweb="radio"] {
    padding: 0.45rem 0.6rem;
    border-radius: 8px;
    transition: background 0.15s, border-left-color 0.15s;
    margin-bottom: 0.15rem;
    border-left: 3px solid transparent;
    width: 100%;
    box-sizing: border-box;
}

section[data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
    background: rgba(255,255,255,0.05);
    border-left-color: var(--c-teal-500);
}

section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) {
    background: rgba(20, 184, 166, 0.14);
    border-left-color: var(--c-teal-400);
}

section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) div[data-testid*="stMarkdownContainer"] p {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] label[data-baseweb="radio"] > div:first-child {
    display: none !important;  /* hide the radio circle */
}

section[data-testid="stSidebar"] label[data-baseweb="radio"] div[data-testid*="stMarkdownContainer"] p {
    color: #CBD5E1;
    font-size: 0.92rem;
    font-weight: 500;
}

/* Footer anclado al fondo del sidebar mediante posicionamiento absoluto.
   La sección del sidebar se hace position:relative para servir de ancla,
   y el ElementContainer que envuelve el footer se posiciona absoluto al
   fondo. Robusto frente a cambios del DOM interno de Streamlit. */
section[data-testid="stSidebar"] {
    position: relative !important;
}
section[data-testid="stSidebar"]
    [data-testid="stElementContainer"]:has(.caudal-sidebar-footer) {
    position: absolute !important;
    bottom: 2.5rem !important;
    left: 1.5rem !important;
    right: 1.5rem !important;
    width: auto !important;
    margin: 0 !important;
}
.caudal-sidebar-footer {
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    font-size: 0.72rem;
    color: #64748B;
    letter-spacing: 0.04em;
    line-height: 1.45;
}

/* ============================================================
   PAGE HEAD · breadcrumb + kicker + title + lede (editorial)
   ============================================================ */

.caudal-page-head {
    background: transparent;
    padding: 0;
    margin-bottom: 1rem;
    box-shadow: none;
}

.caudal-page-head-hero {
    margin-bottom: 1.2rem;
}

.caudal-topbar {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    padding-top: 0;
    padding-bottom: 0.5rem;
    margin-top: 0;
    margin-bottom: 0.8rem;
    border-bottom: 1px solid var(--c-gray-200);
    display: flex;
    gap: 0.6rem;
    align-items: center;
}

.caudal-topbar-brand {
    color: var(--c-gray-400);
}

.caudal-topbar-sep {
    color: var(--c-gray-300);
}

.caudal-topbar-mark {
    color: var(--c-teal-600);
    font-weight: 600;
    letter-spacing: 0.22em;
}

.caudal-topbar-dataset {
    margin-left: auto;
    display: inline-flex;
    align-items: baseline;
    gap: 0.5rem;
    padding: 0.25rem 0.7rem;
    background: var(--c-teal-50);
    border: 1px solid var(--c-teal-100);
    border-radius: 999px;
}

.caudal-topbar-ds-label {
    color: var(--c-gray-400);
    font-weight: 600;
    font-size: 10px;
    letter-spacing: 0.18em;
}

.caudal-topbar-ds-name {
    color: var(--c-teal-700);
    font-weight: 700;
    font-family: 'Manrope', sans-serif;
    font-size: 11px;
    letter-spacing: 0.04em;
    text-transform: none;
}

.caudal-page-title {
    font-family: 'Manrope', sans-serif !important;
    font-weight: 300 !important;
    color: var(--c-navy-900) !important;
    letter-spacing: -0.03em;
    line-height: 1.08;
    margin: 0 0 10px 0;
    font-size: 28px;
    max-width: 900px;
}

.caudal-page-title-hero {
    font-size: 48px;
    letter-spacing: -0.035em;
    line-height: 1.05;
    margin-bottom: 12px;
}

.caudal-page-title em {
    color: var(--c-teal-500) !important;
    font-weight: 500 !important;
    font-style: normal !important;
}

/* ============================================================
   MODAL · st.dialog con backdrop blur + animación de entrada
   ============================================================ */

/* Backdrop con blur sobre toda la pantalla */
[data-testid="stDialog"]::backdrop,
div[role="dialog"] + div,
.stDialog ~ div[data-baseweb="modal"] [class*="backdrop"] {
    backdrop-filter: blur(8px) !important;
    -webkit-backdrop-filter: blur(8px) !important;
    background: rgba(10, 31, 61, 0.35) !important;
}

/* Diálogo: animación de entrada (escala + fade) */
[data-testid="stDialog"] > div,
div[role="dialog"] {
    animation: caudal-modal-pop 0.32s cubic-bezier(0.2, 0.9, 0.3, 1.2);
    border-radius: 14px !important;
    box-shadow: 0 20px 48px rgba(10, 31, 61, 0.28) !important;
}

@keyframes caudal-modal-pop {
    0% {
        opacity: 0;
        transform: scale(0.85) translateY(12px);
    }
    100% {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}

.caudal-lede {
    font-family: 'Manrope', sans-serif;
    font-weight: 400;
    color: var(--c-gray-600);
    max-width: 720px;
    margin: 0;
    line-height: 1.55;
    font-size: 15px;
}

.caudal-lede-hero {
    font-size: 17px;
}

/* ============================================================
   SECTION HEADER · (legacy, mantenido para compatibilidad)
   ============================================================ */

.caudal-section-head {
    display: flex;
    align-items: center;
    gap: 0.9rem;
    margin-bottom: 0.3rem;
    padding-bottom: 0.9rem;
    border-bottom: 1px solid var(--c-gray-200);
    position: relative;
}

.caudal-section-head::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    width: 64px;
    height: 3px;
    background: var(--gradient-brand);
    border-radius: 2px;
}

.caudal-section-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--c-teal-700);
    font-weight: 600;
    background: var(--c-teal-50);
    padding: 0.3rem 0.7rem;
    border-radius: var(--radius-pill);
    white-space: nowrap;
    border: 1px solid var(--c-teal-100);
    letter-spacing: 0.05em;
}

.caudal-section-title {
    font-family: 'Manrope', sans-serif;
    font-size: 2rem;
    font-weight: 400;
    color: var(--c-navy-900);
    margin: 0;
    letter-spacing: -0.025em;
    line-height: 1.2;
}

.tfg-caption {
    color: var(--c-gray-500);
    font-size: 0.92rem;
    margin-top: 0.6rem;
    margin-bottom: 1.5rem;
    max-width: 780px;
    line-height: 1.55;
}

/* ============================================================
   CARDS
   ============================================================ */

.tfg-card {
    background: #FFFFFF;
    border: 1px solid var(--c-gray-200);
    border-radius: var(--radius-md);
    padding: 0.9rem 1.15rem;
    margin-bottom: 0.6rem;
    box-shadow: var(--shadow-sm);
    transition: border-color 0.2s, box-shadow 0.2s;
    max-height: 260px;
    overflow-y: auto;
}

.tfg-card:hover {
    border-color: var(--c-teal-400);
    box-shadow: var(--shadow-md);
}

.tfg-card-muted {
    background: var(--c-gray-50);
    border: 1px solid var(--c-gray-200);
    border-left: 3px solid var(--c-teal-500);
    border-radius: var(--radius-sm);
    padding: 0.7rem 0.95rem;
    margin-bottom: 0.5rem;
    white-space: pre-wrap;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: var(--c-gray-700);
    line-height: 1.55;
    max-height: 220px;
    overflow-y: auto;
}

/* ============================================================
   TAGS
   ============================================================ */

.tfg-tag {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: var(--radius-pill);
    font-size: 0.76rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    background: var(--c-gray-100);
    color: var(--c-navy-700);
    margin-right: 0.35rem;
    border: 1px solid var(--c-gray-200);
}

.tfg-tag-alert {
    background: var(--c-danger-50);
    color: var(--c-danger-700);
    border-color: var(--c-danger-200);
}

.tfg-tag-ok {
    background: var(--c-teal-50);
    color: var(--c-teal-700);
    border-color: var(--c-teal-100);
}

/* ============================================================
   BUTTONS
   ============================================================ */

.stButton button {
    border-radius: var(--radius-md) !important;
    font-weight: 500 !important;
    padding: 0.55rem 1.3rem !important;
    transition: all 0.2s !important;
    border: 1px solid var(--c-gray-300) !important;
    font-family: 'Manrope', sans-serif !important;
    font-size: 0.92rem !important;
}

.stButton button:hover {
    border-color: var(--c-teal-500) !important;
    color: var(--c-teal-700) !important;
}

.stButton button[kind="primary"] {
    background: var(--c-navy-900) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--c-navy-900) !important;
    box-shadow: var(--shadow-sm) !important;
}

.stButton button[kind="primary"]:hover {
    background: var(--c-navy-700) !important;
    border-color: var(--c-navy-700) !important;
    color: #FFFFFF !important;
    transform: translateY(-1px);
    box-shadow: var(--shadow-md) !important;
}

/* ============================================================
   METRICS
   ============================================================ */

div[data-testid="stMetricValue"] {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--c-navy-900);
    font-family: 'Inter', sans-serif;
}

div[data-testid="stMetricLabel"] {
    color: var(--c-gray-500);
    font-weight: 600;
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

div[data-testid="metric-container"] {
    background: #FFFFFF;
    padding: 1rem 1.15rem;
    border-radius: var(--radius-md);
    border: 1px solid var(--c-gray-200);
    box-shadow: var(--shadow-sm);
}

/* ============================================================
   INPUTS
   ============================================================ */

div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] textarea,
div[data-baseweb="input"] input {
    border-radius: var(--radius-md) !important;
    border-color: var(--c-gray-300) !important;
    transition: all 0.15s;
}

div[data-baseweb="select"] > div:focus-within,
div[data-baseweb="textarea"] textarea:focus,
div[data-baseweb="input"] input:focus {
    border-color: var(--c-teal-500) !important;
    box-shadow: 0 0 0 3px rgba(20,184,166,0.12) !important;
}

.stNumberInput div[data-baseweb] {
    border-radius: var(--radius-md) !important;
}

/* ============================================================
   DATAFRAMES
   ============================================================ */

.stDataFrame {
    border: 1px solid var(--c-gray-200);
    border-radius: var(--radius-md);
    overflow: hidden;
    box-shadow: var(--shadow-sm);
}

/* ============================================================
   FLOW DIAGRAM (section 5)
   ============================================================ */

.flow-wrap {
    display: flex;
    flex-direction: column;
    gap: 0.12rem;
    margin-top: 0.4rem;
}

.flow-title {
    text-align: center;
    font-weight: 700;
    color: var(--c-navy-900);
    font-size: 1rem;
    padding: 0.75rem 0.7rem;
    border-radius: var(--radius-md);
    margin-bottom: 0.5rem;
    background: var(--c-gray-100);
    border: 1px solid var(--c-gray-200);
}

.flow-title-alt {
    background: linear-gradient(135deg, var(--c-teal-50) 0%, var(--c-teal-100) 100%);
    border-color: var(--c-teal-500);
    color: var(--c-teal-700);
}

.flow-step {
    background: #FFFFFF;
    border: 1px solid var(--c-gray-300);
    border-radius: var(--radius-md);
    padding: 0.75rem 0.95rem;
    text-align: center;
    color: var(--c-gray-700);
    font-size: 0.92rem;
    line-height: 1.35;
    box-shadow: var(--shadow-sm);
    transition: all 0.15s;
}

.flow-step b { color: var(--c-navy-900); font-weight: 700; }

.flow-step-accent {
    border-color: var(--c-teal-500);
    border-left: 4px solid var(--c-teal-500);
    background: #FFFFFF;
}

.flow-step-muted {
    border-style: dashed;
    color: var(--c-gray-500);
    background: var(--c-gray-50);
    box-shadow: none;
}

.flow-step-highlight {
    box-shadow: 0 0 0 3px rgba(20,184,166,0.15), var(--shadow-sm);
    font-size: 0.95rem;
}

.flow-arrow {
    text-align: center;
    color: var(--c-teal-500);
    font-size: 1.25rem;
    line-height: 1;
    padding: 0.3rem 0;
    user-select: none;
    font-weight: 700;
}

.flow-phase {
    text-align: center;
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--c-gray-500);
    margin: 0.8rem 0 0.4rem 0;
    padding: 0.3rem 0.5rem;
    font-weight: 600;
}

.flow-phase-alt {
    color: var(--c-teal-700);
}

.level-strip {
    display: flex;
    justify-content: center;
    gap: 0.35rem;
    flex-wrap: wrap;
    margin-top: 0.7rem;
}

.level-chip {
    padding: 0.2rem 0.6rem;
    border-radius: var(--radius-pill);
    border: 1px solid var(--c-gray-200);
    background: #FFFFFF;
    color: var(--c-navy-700);
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}

.flow-tag-neg {
    display: block;
    color: var(--c-danger-700);
    font-size: 0.84rem;
    margin-top: 0.3rem;
    font-weight: 500;
}

.flow-tag-pos {
    display: block;
    color: var(--c-teal-700);
    font-size: 0.84rem;
    margin-top: 0.3rem;
    font-weight: 500;
}

/* ============================================================
   EXPANDER
   ============================================================ */

div[data-testid="stExpander"] {
    border: 1px solid var(--c-gray-200) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-sm);
}

div[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: var(--c-navy-700) !important;
    font-size: 0.9rem;
}

/* ============================================================
   SPINNER
   ============================================================ */

div[data-testid="stSpinner"] > div {
    border-top-color: var(--c-teal-500) !important;
}

/* ============================================================
   HIDE STREAMLIT CHROME
   ============================================================ */

footer {visibility: hidden;}
#MainMenu {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent; height: 0;}

</style>
"""
