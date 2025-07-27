# Repositorio de IA & ML - Guía Completa

Una colección integral de proyectos de IA/ML que muestra implementaciones de vanguardia en visión por computadora, procesamiento de lenguaje natural, análisis financiero, sistemas distribuidos y patrones modernos de integración de IA.

## 📋 Tabla de Contenidos

| Categoría | Proyecto | Descripción | Documentación |
|-----------|----------|-------------|---------------|
| **Procesamiento de Video OpenAI** | Traductor de Videos con IA | Sistema completo de traducción de videos local impulsado por IA de español a inglés usando OpenAI Whisper, transformadores Helsinki-NLP y Edge TTS | [📖 Español](OpenAI/Video_Translation/readme_es.md) |
| **IA Médica** | Anonimización DICOM | Anonimización de imágenes médicas DICOM usando Microsoft Presidio | [📖 Español](DICOM_FHIR/Readme_es.md) |
| **Google AI** | Resumidor de Videos | Transcripción y resumen de videos con IA usando Gemini Pro | [📖 Español](Google_AI/Video_summarizer/Readme_es.md) |
| **Google AI** | Caché de Contenido | Optimización de caché de contexto de Google AI con API Gemini | [📖 Español](Google_AI/content_caching/Readme_es.md) |
| **OCR Distribuido** | Sistema OCR NATS | Sistema OCR distribuido con mensajería NATS y RapidOCR | [📖 Español](Nats/Readme_es.md) |
| **RAG Financiero** | Análisis Financiero | Sistema RAG para análisis financiero fundamental con datos en tiempo real | [📖 Español](RAG/Intro/Readme_es.md) |
| **Estrategia Trading** | Estrategia Bollinger RSI | Estrategia de trading combinando Bandas de Bollinger y cruce RSI | [📖 Español](RAG/bollinger%20z-score%20rsi%20startegy/Readme_es.md) |
| **Análisis Trading** | Z-Score Bollinger | Análisis de trading financiero con Bandas de Bollinger y Z-Score | [📖 Español](RAG/bollinger%20z-score/Readme_es.md) |
| **Estrategia Trading** | Bollinger Fibonacci | Estrategia avanzada combinando Bandas de Bollinger y retrocesos Fibonacci | [📖 Español](RAG/bollinger-fibonacci_retracements/Readme_es.md) |
| **Estrategia Trading** | Estrategia Connors RSI | Oscilador de momentum avanzado con integración LangGraph para señales mejoradas de reversión a la media | [📖 Español](RAG/connor-rsi/Readme_es.md) |
| **Estrategia Trading** | MACD Donchian | Estrategia de trading combinada MACD y Canales de Donchian | [📖 Español](RAG/macd_downchain%20startegy/Readme_es.md) |
| **Base de Datos Grafos** | Sistema RAG Neo4j | Interfaz de lenguaje natural para bases de datos grafos Neo4j | [📖 Español](RAG/speak%20with%20your%20Graph%20Database/Readme_es.md) |
| **Integración MCP** | Servidores MCP | Servidores del Protocolo de Contexto de Modelo para integración Claude AI | [📖 Español](mcp/mcp_server/readme_es.md) |
| **Desarrollo MCP** | Cliente/Servidor Python MCP | Servidor de análisis financiero Python MCP con transporte SSE | [📖 Español](mcp/python_client_server/README_es.md) |
| **Cliente MCP** | Cliente MCP Multi-Lenguaje | Cliente MCP integral con herramientas de análisis financiero y soporte multi-servidor | [📖 Español](mcp/mcp-client/Readme_es.md) |
| **Chatbot MCP** | Bot Chainlit MCP | Chatbot de IA conversacional que integra Neo4j y HubSpot a través del protocolo MCP | [📖 Español](mcp/chainlit_bot/Readme_es.md) |
| **Plataforma MCP** | Plataforma Streamlit CRM y Grafos | Aplicación full-stack de grado empresarial con IA que integra Neo4j, CRM HubSpot y Yahoo Finance con autenticación empresarial | [📖 Español](mcp/Streamlit_chatbot/README_ES.md) |
| **Desarrollo MCP** | Creando MCP con LLMs | Guía completa para acelerar el desarrollo de servidores MCP usando modelos de lenguaje como Claude, con ejemplo práctico de procesador de documentos PDF | [📖 Español](mcp/Build%20MCP%20with%20LLMs/README_es.md) |
| **Plataforma de Búsqueda MCP** | Plataforma de Integración MCP de Búsqueda Impulsada por IA | Una aplicación integral que proporciona interacciones impulsadas por IA con Google Search y Perplexity AI a través de servidores Model Context Protocol (MCP) con seguridad HTTPS opcional, autenticación de usuarios y caching avanzado | [📖 Español](mcp/Motor_busqueda_AI_google_perplexity/Readme_es.md) |
| **Claude Desktop** | Guía de Configuración Claude Desktop | Guía completa para instalación de Claude Desktop y configuración MCP | [📖 Español](mcp/claude_desktop/Readme_es.md) |

## 🌟 Descripción General del Repositorio

Este repositorio representa una exploración integral de las tecnologías modernas de IA/ML, demostrando implementaciones prácticas a través de múltiples dominios:

### 🎬 Procesamiento y Traducción de Video OpenAI
- **Traductor de Videos con IA**: Un potente sistema de traducción de videos impulsado por IA, completamente gratuito y local, que traduce videos en español al inglés utilizando modelos de aprendizaje automático de vanguardia. Cuenta con transcripción de alta precisión con OpenAI Whisper, traducción automática neuronal con transformadores Helsinki-NLP y síntesis de voz de sonido natural con Edge TTS. Soporta videos largos (2+ horas) con procesamiento inteligente por segmentos, múltiples opciones de voz y procesamiento 100% local garantizando privacidad completa. Sin servicios en la nube, suscripciones o preocupaciones de privacidad de datos.

### 🏥 IA Médica y Visión por Computadora
- **Anonimización DICOM**: Sistema avanzado de procesamiento de imágenes médicas que detecta y redacta automáticamente Información de Salud Personal (PHI) en imágenes médicas DICOM usando el framework Presidio de Microsoft, garantizando el cumplimiento de HIPAA.

### 🤖 Ecosistema Google AI
- **Resumidor de Videos**: Aprovecha el modelo Gemini 2.0 Flash de Google para análisis inteligente de contenido de video, proporcionando resúmenes estructurados y transcripciones completas con integración en la nube.
- **Caché de Contenido**: Optimiza el uso de tokens y reduce costos a través de la función de Caché de Contexto de Google, demostrando 99.5% de reducción de tokens y mejoras de velocidad de 12-18x.

### ⚡ Sistemas Distribuidos
- **Sistema OCR NATS**: Procesamiento OCR distribuido de alto rendimiento usando NATS JetStream para entrega confiable de mensajes y RapidOCR para extracción de texto, perfecto para arquitecturas de microservicios.

### 💰 Análisis Financiero y Trading
- **Sistema RAG Integral**: Análisis financiero fundamental combinando técnicas tradicionales con IA/ML moderna, con integración de datos en tiempo real e insights inteligentes.
- **Múltiples Estrategias de Trading**: Implementación de algoritmos de trading sofisticados incluyendo:
  - **Bandas de Bollinger con análisis de cruce RSI**: Confirmación multi-indicador para mercados con tendencia
  - **Análisis estadístico Z-Score**: Posicionamiento de mercado y señales de reversión a la media
  - **Integración de retrocesos Fibonacci**: Puntos precisos de entrada/salida con sistemas de puntuación avanzados
  - **Estrategia Connors RSI**: Oscilador de momentum avanzado desarrollado por Larry Connors combinando tres componentes distintos:
    - **RSI de Precio (33.33%)**: RSI de 3 días para momentum reciente de precios
    - **RSI de Rachas (33.33%)**: RSI aplicado a movimientos consecutivos al alza/baja
    - **Rango Percentil (33.33%)**: Ranking percentil sobre ventana móvil de 100 días
    - **Características Mejoradas**: Integración Z-Score, sistema de puntuación combinado (-100 a +100), integración de agente LangGraph
  - **Combinación MACD y Canales de Donchian**: Análisis de momentum con indicadores de volatilidad

### 🔗 Bases de Datos de Grafos y Sistemas de Conocimiento
- **Integración RAG Neo4j**: Interfaz de lenguaje natural para interacciones complejas de bases de datos de grafos, permitiendo consultas conversacionales a través de estructuras de datos interconectadas.

### 🔌 Protocolo de Contexto de Modelo (MCP)
- **Ecosistema de Servidores MCP**: Implementación completa del estándar MCP de Anthropic, demostrando el "USB-C para integraciones de IA" con múltiples configuraciones de servidor.
- **Framework Python MCP**: Servidor avanzado de análisis financiero con transporte Server-Sent Events, mostrando integración de herramientas IA en tiempo real.
- **Cliente MCP Multi-Lenguaje**: Implementación integral de cliente que conecta Claude AI con herramientas externas, con capacidades especializadas de análisis financiero a través de servidores Python y Node.js.
- **Chatbot Chainlit MCP**: Aplicación sofisticada de IA conversacional que conecta sin problemas bases de datos de grafos Neo4j y CRM de HubSpot a través del Protocolo de Contexto de Modelo, construida con Chainlit para una interfaz de chat intuitiva. Características incluyen exploración inteligente de datos, análisis entre sistemas y consultas en lenguaje natural a través de múltiples fuentes de datos.
- **Plataforma Streamlit CRM y Grafos**: Aplicación full-stack de grado empresarial que proporciona interacciones impulsadas por IA con bases de datos de grafos Neo4j, sistemas CRM de HubSpot y datos de Yahoo Finance a través de servidores MCP. Incluye autenticación integral, soporte IA multi-proveedor y arquitectura lista para producción con más de 25 herramientas especializadas para análisis, gestión y automatización completos a través de infraestructura de base de datos, CRM y datos financieros.
- **Creando MCP con LLMs**: Guía completa que demuestra cómo acelerar el desarrollo de servidores MCP usando modelos de lenguaje como Claude. Incluye un ejemplo práctico completo de un procesador de documentos PDF con capacidades OCR, prompts personalizados y generación de salida en markdown, mostrando cómo la IA puede acelerar significativamente los flujos de trabajo de desarrollo MCP.
- **Plataforma de Integración MCP de Búsqueda Impulsada por IA**: Una aplicación integral que proporciona interacciones impulsadas por IA con Google Search y Perplexity AI a través de servidores Model Context Protocol (MCP). Esta plataforma permite búsqueda web sin interrupciones, análisis impulsado por IA y extracción de contenido con seguridad HTTPS opcional, autenticación de usuarios y caching avanzado para rendimiento óptimo. Incluye sistema de caching inteligente con 40-70% de reducción de uso de API, seguridad de nivel empresarial con autenticación bcrypt y soporte SSL/HTTPS, integración dual de motores de búsqueda (Google Custom Search y Perplexity AI), y 10 herramientas especializadas para búsqueda, extracción de contenido y gestión de cache. El sistema proporciona tiempos de respuesta 80-95% más rápidos para contenido en cache y capacidades integrales de monitoreo.
- **Integración Claude Desktop**: Guía completa de configuración para la aplicación Claude Desktop con configuración de servidores MCP, habilitando interacciones perfectas IA-herramientas en tu escritorio.

## 🛠️ Stack Tecnológico

### Frameworks Core de IA/ML
- **OpenAI Whisper**: Modelo de reconocimiento de voz de vanguardia entrenado con 680,000 horas de datos de audio multilingües
- **Transformadores Helsinki-NLP**: Traducción automática neuronal de alta calidad para Español→Inglés
- **Edge TTS & pyttsx3**: Motores avanzados de texto a voz con voces de sonido natural
- **LangChain & LangGraph**: Orquestación avanzada de IA y flujos de trabajo de agentes
- **Google Gemini Pro**: Modelos de lenguaje de última generación para varias aplicaciones
- **Modelos GPT de OpenAI**: Integración con la API de OpenAI para procesamiento inteligente
- **Microsoft Presidio**: Framework de protección de privacidad y detección de PII
- **Chainlit**: Framework de Python para construir aplicaciones de IA conversacional
- **Streamlit**: Framework de Python para construir aplicaciones web interactivas y dashboards de datos

### Procesamiento de Datos y Análisis
- **FFmpeg & Librosa**: Kit de herramientas completo para procesamiento y análisis de audio/video
- **PyTorch**: Framework de deep learning para ejecutar modelos de IA
- **Yahoo Finance & APIs Financieras**: Datos financieros en tiempo real e históricos
- **PyDICOM**: Procesamiento de imágenes médicas y cumplimiento del estándar DICOM
- **Pandas & NumPy**: Manipulación y análisis integral de datos
- **Plotly & Matplotlib**: Visualización avanzada de datos y gráficos interactivos

### Sistemas Distribuidos y Mensajería
- **NATS JetStream**: Sistema de mensajería distribuida de alto rendimiento
- **FastAPI**: Framework web moderno y rápido para construir APIs
- **Docker**: Containerización para despliegue escalable
- **Server-Sent Events (SSE)**: Comunicación bidireccional en tiempo real

### Bases de Datos y Almacenamiento
- **Neo4j**: Base de datos de grafos para modelado complejo de relaciones
- **HubSpot CRM**: Gestión de relaciones con clientes y seguimiento de pipeline de ventas
- **Qdrant**: Base de datos vectorial para búsqueda de similitud y aplicaciones RAG
- **Google Cloud Storage**: Integración de almacenamiento en la nube escalable

#### **Desarrollo MCP**
```yaml
Framework: Protocolo de Contexto de Modelo (Anthropic)
Lenguajes: Python, Node.js, TypeScript
Transporte: STDIO, SSE, HTTP
Herramientas: FastMCP, procesamiento PDF, OCR
Aceleración de Desarrollo: Desarrollo asistido por LLM
```

### Herramientas de Desarrollo
- **Gestor de Paquetes UV**: Gestión rápida de paquetes Python
- **Jupyter Notebooks**: Desarrollo interactivo y documentación
- **Gestión de Entornos**: Configuración segura con variables de entorno

## 🚀 Características Clave e Innovaciones

### 🔥 Patrones Avanzados de Integración de IA
- **Procesamiento Local de IA**: Traducción de video que preserva la privacidad completamente sin dependencias de la nube
- **Procesamiento IA Multi-Modal**: Integración de reconocimiento de voz, traducción de texto y síntesis de voz
- **Retrieval-Augmented Generation (RAG)**: Múltiples implementaciones mostrando diferentes enfoques para combinar recuperación con generación
- **IA Multi-Modal**: Integración de capacidades de procesamiento de texto, imagen y video
- **Sistemas Basados en Agentes**: Agentes inteligentes que pueden descubrir y usar herramientas dinámicamente
- **Protocolo de Contexto de Modelo**: Integración estandarizada IA-herramientas a través de múltiples lenguajes y plataformas
- **IA Conversacional**: Interfaces de chatbot interactivas para exploración de datos en lenguaje natural
- **Aplicaciones Web Empresariales**: Plataformas web listas para producción con autenticación integral y soporte multi-usuario
- **Desarrollo Acelerado por LLM**: Uso de modelos de lenguaje para acelerar significativamente el desarrollo de servidores MCP y reducir código repetitivo

### 📊 Análisis Financiero Sofisticado
- **Estrategias Multi-Indicador**: Estrategias de trading complejas combinando 3-4 indicadores técnicos
- **Análisis Avanzado de Momentum**: Implementación Connors RSI con análisis de componentes y recomendaciones potenciadas por IA
- **Sistemas de Puntuación**: Puntuación estandarizada (-100 a +100) para interpretación consistente de señales
- **Procesamiento en Tiempo Real**: Integración de datos de mercado en vivo con análisis inteligente
- **Integración Cross-Platform**: Herramientas financieras accesibles vía múltiples mecanismos de transporte
- **Plataforma Financiera Empresarial**: Análisis financiero full-stack con integración CRM y conectividad de base de datos de grafos

### 🏗️ Arquitectura Lista para Producción
- **Diseño de Microservicios**: Sistemas distribuidos con clara separación de responsabilidades
- **Mejores Prácticas de Seguridad**: Autenticación, autorización y protección de datos apropiadas
- **Infraestructura Escalable**: Diseños nativos de la nube con soporte de containerización
- **Soporte Multi-Transporte**: Mecanismos de transporte STDIO, SSE y HTTP para despliegue flexible
- **Interfaces Conversacionales**: Interfaces de chat amigables para interacciones de datos complejas
- **Autenticación Empresarial**: Gestión avanzada de usuarios con cifrado bcrypt, gestión de sesiones y soporte SSL/TLS
- **Desarrollo Asistido por LLM**: Flujos de trabajo de desarrollo acelerados usando modelos de lenguaje para generar servidores MCP, reduciendo el tiempo de desarrollo de días a horas

### 🔧 Experiencia del Desarrollador
- **Documentación Integral**: READMEs detallados con instrucciones de configuración y ejemplos
- **Notebooks Interactivos**: Notebooks Jupyter para aprendizaje y experimentación
- **Seguridad de Tipos**: Type hints de Python y validación de esquemas en todo el código
- **Descubrimiento de Herramientas**: Descubrimiento automático y orquestación de capacidades disponibles
- **Desarrollo Basado en Chat**: Interfaces de lenguaje natural para exploración y análisis de datos
- **Interfaces Basadas en Web**: Interfaces modernas con pestañas para gestión integral del sistema

## 🎯 Casos de Uso y Aplicaciones

### Procesamiento de Medios y Contenido
- **Traducción de Videos**: Traducción automatizada de videos español-inglés con síntesis de voz profesional
- **Contenido Educativo**: Traducir conferencias, tutoriales, cursos en español para accesibilidad
- **Entretenimiento**: Traducir películas, documentales, programas preservando la calidad del video
- **Contenido Empresarial**: Traducir presentaciones, reuniones, videos de entrenamiento para equipos internacionales
- **Creación de Contenido**: Traducir videos de YouTube, vlogs, entrevistas para audiencias más amplias
- **Procesamiento en Tiempo Real**: Análisis de contenido en vivo e insights inteligentes

### Salud y Medicina
- **Anonimización de Imágenes Médicas**: Procesamiento de imágenes médicas compatible con HIPAA
- **Integración de Flujos Clínicos**: Integración fluida con sistemas médicos existentes

### Servicios Financieros
- **Trading Algorítmico**: Generación y análisis automatizado de señales de trading incluyendo estrategias avanzadas de momentum
- **Análisis de Reversión a la Media**: Estrategias basadas en Connors RSI y Z-Score para condiciones de sobrecompra/sobreventa
- **Evaluación de Riesgo**: Métricas avanzadas de riesgo y análisis de portfolios
- **Investigación de Mercado**: Análisis inteligente de tendencias y patrones financieros
- **Acceso Multi-Plataforma**: Análisis financiero accesible a través de interfaces web, escritorio y API
- **Gestión Financiera Empresarial**: Plataforma integral que combina análisis técnico, integración CRM e insights de base de datos de grafos

### IA Empresarial
- **Procesamiento de Documentos**: Extracción y análisis automatizado de documentos empresariales
- **Gestión del Conocimiento**: Sistemas de conocimiento basados en grafos para relaciones de datos complejas
- **Análisis Potenciado por IA**: Integración de capacidades de IA en flujos de trabajo empresariales existentes
- **Orquestación de Herramientas**: Descubrimiento inteligente y coordinación de servicios externos
- **Integración de IA de Escritorio**: Aplicación nativa Claude Desktop con soporte de protocolo MCP para productividad mejorada
- **CRM Conversacional**: Interfaces basadas en chat para gestión de relaciones con clientes y exploración de datos
- **Plataformas IA Full-Stack**: Aplicaciones web de grado empresarial con autenticación integral, soporte multi-usuario e integración de datos entre sistemas

### Integración y Análisis de Datos
- **Conectividad Entre Sistemas**: Integración perfecta entre bases de datos de grafos Neo4j y CRM de HubSpot
- **Consultas en Lenguaje Natural**: Interfaces basadas en chat para exploración compleja de datos
- **Análisis Multi-Fuente**: Correlación inteligente y análisis a través de diferentes plataformas de datos
- **Gestión de Datos Empresariales**: Plataformas integrales para gestionar y analizar datos a través de múltiples fuentes con insights impulsados por IA

### Búsqueda Avanzada e Investigación
- **Búsqueda Web Impulsada por IA**: Capacidades de búsqueda inteligente combinando Google Custom Search y Perplexity AI con caching avanzado
- **Extracción y Análisis de Contenido**: Extracción automatizada de contenido de páginas web con resumen inteligente
- **Automatización de Investigación**: Flujos de trabajo de investigación simplificados con correlación de datos entre plataformas
- **Soluciones de Búsqueda Empresarial**: Plataformas de búsqueda listas para producción con autenticación, soporte SSL/HTTPS y monitoreo de rendimiento

## 🚦 Primeros Pasos

### Configuración Rápida
1. **Elige tu Dominio**: Selecciona un proyecto de la tabla anterior basado en tus intereses
2. **Sigue la Documentación**: Cada proyecto tiene instrucciones de configuración integrales
3. **Configuración del Entorno**: La mayoría de proyectos usan Python con gestión específica de dependencias
4. **Claves API**: Asegura tus claves API en variables de entorno

### Ruta de Aprendizaje Recomendada
1. **Comienza con Procesamiento Local de IA**: Inicia con el Traductor de Videos con IA para entender flujos de trabajo de IA local y procesamiento multi-modal
2. **Progresa a Sistemas RAG**: Avanza al RAG de Análisis Financiero para conceptos fundamentales
3. **Explora Estrategias de Trading**: Progresa a través de las diferentes implementaciones de algoritmos de trading
   - Comienza con análisis básico de Z-Score de Bollinger
   - Avanza al Connors RSI para análisis sofisticado de momentum
   - Explora estrategias combinadas como Bollinger-Fibonacci
4. **Integración Avanzada**: Avanza a servidores MCP para entender patrones modernos de integración de IA
5. **Desarrollo Multi-Plataforma**: Explora el cliente MCP para orquestación de herramientas cross-language
6. **Desarrollo Acelerado por LLM**: Aprende cómo usar Claude y otros LLMs para desarrollar rápidamente servidores MCP personalizados con el ejemplo integral del procesador de PDF
7. **IA Conversacional**: Configura el chatbot Chainlit MCP para interacción de datos en lenguaje natural
8. **Plataformas Empresariales**: Despliega la Plataforma Streamlit CRM y Grafos para experiencia de aplicación IA empresarial full-stack
9. **Integración de Búsqueda Avanzada**: Explora la Plataforma de Integración MCP de Búsqueda Impulsada por IA para capacidades de búsqueda integrales con caching inteligente
10. **Integración de IA de Escritorio**: Configura Claude Desktop con servidores MCP para interacciones nativas IA-herramientas
11. **Aplicaciones Especializadas**: Profundiza en aplicaciones específicas del dominio como IA médica u OCR distribuido

### Áreas de Investigación
- **Procesamiento Local de IA**: Flujos de trabajo de IA que preservan la privacidad sin dependencias de la nube
- **IA Multimodal**: Integración avanzada de diferentes modalidades de IA
- **Aprendizaje Federado**: Implementaciones de machine learning distribuido
- **Edge Computing**: Capacidades de procesamiento de IA desplegadas en el edge
- **Computación Cuántica**: Algoritmos mejorados con quantum para optimización
- **Ciencia de Datos Conversacional**: Interfaces de lenguaje natural para análisis complejo de datos
- **Plataformas IA Empresariales**: Aplicaciones full-stack que combinan múltiples servicios de IA y fuentes de datos
- **Desarrollo Rápido MCP**: Patrones de desarrollo asistido por LLM para acelerar proyectos de integración de IA
- **Sistemas de Búsqueda Inteligente**: Arquitecturas de búsqueda avanzadas con análisis impulsado por IA y caching

## ⚖️ Licencia y Descargo de Responsabilidad

Este repositorio contiene implementaciones educativas y de investigación. Los proyectos individuales pueden tener términos de licencia específicos. Por favor revisa la documentación de cada proyecto para:

- **Derechos de Uso**: Casos de uso apropiados y restricciones
- **Términos de API**: Términos y condiciones de servicios de terceros
- **Descargo Financiero**: Advertencias de riesgo de inversión y trading
- **Descargo Médico**: Limitaciones de aplicaciones de salud

---

**Este repositorio representa la convergencia de la experiencia tradicional del dominio con capacidades de IA de vanguardia, demostrando cómo los sistemas modernos de IA pueden integrarse en aplicaciones del mundo real mientras mantienen estándares de calidad de producción y mejores prácticas.**