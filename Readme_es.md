# Repositorio de IA & ML - Guía Completa

Una colección integral de proyectos de IA/ML que muestra implementaciones de vanguardia en visión por computadora, procesamiento de lenguaje natural, análisis financiero, sistemas distribuidos y patrones modernos de integración de IA.

## 📋 Tabla de Contenidos

| Categoría | Proyecto | Descripción | Documentación |
|-----------|----------|-------------|---------------|
| **IA Médica** | Anonimización DICOM | Anonimización de imágenes médicas DICOM usando Microsoft Presidio | [📖 Español](DICOM_FHIR/Readme_es.md) |
| **Google AI** | Resumidor de Videos | Transcripción y resumen de videos con IA usando Gemini Pro | [📖 Español](Google_AI/Video_summarizer/Readme_es.md) |
| **Google AI** | Caché de Contenido | Optimización de caché de contexto de Google AI con API Gemini | [📖 Español](Google_AI/content_caching/Readme_es.md) |
| **OCR Distribuido** | Sistema OCR NATS | Sistema OCR distribuido con mensajería NATS y RapidOCR | [📖 Español](Nats/Readme_es.md) |
| **RAG Financiero** | Análisis Financiero | Sistema RAG para análisis financiero fundamental con datos en tiempo real | [📖 Español](RAG/Intro/Readme_es.md) |
| **Estrategia Trading** | Estrategia Bollinger RSI | Estrategia de trading combinando Bandas de Bollinger y cruce RSI | [📖 Español](RAG/bollinger%20z-score%20rsi%20startegy/Readme_es.md) |
| **Análisis Trading** | Z-Score Bollinger | Análisis de trading financiero con Bandas de Bollinger y Z-Score | [📖 Español](RAG/bollinger%20z-score/Readme_es.md) |
| **Estrategia Trading** | Bollinger Fibonacci | Estrategia avanzada combinando Bandas de Bollinger y retrocesos Fibonacci | [📖 Español](RAG/bollinger-fibonacci_retracements/Readme_es.md) |
| **Estrategia Trading** | MACD Donchian | Estrategia de trading combinada MACD y Canales de Donchian | [📖 Español](RAG/macd_downchain%20startegy/Readme_es.md) |
| **Base de Datos Grafos** | Sistema RAG Neo4j | Interfaz de lenguaje natural para bases de datos grafos Neo4j | [📖 Español](RAG/speak%20with%20your%20Graph%20Database/Readme_es.md) |
| **Integración MCP** | Servidores MCP | Servidores del Protocolo de Contexto de Modelo para integración Claude AI | [📖 Español](mcp/mcp_server/readme_es.md) |
| **Desarrollo MCP** | Cliente/Servidor Python MCP | Servidor de análisis financiero Python MCP con transporte SSE | [📖 Español](mcp/python_client_server/README_es.md) |

## 🌟 Descripción General del Repositorio

Este repositorio representa una exploración integral de las tecnologías modernas de IA/ML, demostrando implementaciones prácticas a través de múltiples dominios:

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
  - Bandas de Bollinger con análisis de cruce RSI
  - Análisis estadístico Z-Score para posicionamiento de mercado
  - Integración de retrocesos Fibonacci para puntos precisos de entrada/salida
  - Combinación MACD y Canales de Donchian para análisis de momentum

### 🔗 Bases de Datos de Grafos y Sistemas de Conocimiento
- **Integración RAG Neo4j**: Interfaz de lenguaje natural para interacciones complejas de bases de datos de grafos, permitiendo consultas conversacionales a través de estructuras de datos interconectadas.

### 🔌 Protocolo de Contexto de Modelo (MCP)
- **Ecosistema de Servidores MCP**: Implementación completa del estándar MCP de Anthropic, demostrando el "USB-C para integraciones de IA" con múltiples configuraciones de servidor.
- **Framework Python MCP**: Servidor avanzado de análisis financiero con transporte Server-Sent Events, mostrando integración de herramientas IA en tiempo real.

## 🛠️ Stack Tecnológico

### Frameworks Core de IA/ML
- **LangChain & LangGraph**: Orquestación avanzada de IA y flujos de trabajo de agentes
- **Google Gemini Pro**: Modelos de lenguaje de última generación para varias aplicaciones
- **Modelos GPT de OpenAI**: Integración con la API de OpenAI para procesamiento inteligente
- **Microsoft Presidio**: Framework de protección de privacidad y detección de PII

### Procesamiento de Datos y Análisis
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
- **Qdrant**: Base de datos vectorial para búsqueda de similitud y aplicaciones RAG
- **Google Cloud Storage**: Integración de almacenamiento en la nube escalable

### Herramientas de Desarrollo
- **Gestor de Paquetes UV**: Gestión rápida de paquetes Python
- **Jupyter Notebooks**: Desarrollo interactivo y documentación
- **Gestión de Entornos**: Configuración segura con variables de entorno

## 🚀 Características Clave e Innovaciones

### 🔥 Patrones Avanzados de Integración de IA
- **Retrieval-Augmented Generation (RAG)**: Múltiples implementaciones mostrando diferentes enfoques para combinar recuperación con generación
- **IA Multi-Modal**: Integración de capacidades de procesamiento de texto, imagen y video
- **Sistemas Basados en Agentes**: Agentes inteligentes que pueden descubrir y usar herramientas dinámicamente

### 📊 Análisis Financiero Sofisticado
- **Estrategias Multi-Indicador**: Estrategias de trading complejas combinando 3-4 indicadores técnicos
- **Sistemas de Puntuación**: Puntuación estandarizada (-100 a +100) para interpretación consistente de señales
- **Procesamiento en Tiempo Real**: Integración de datos de mercado en vivo con análisis inteligente

### 🏗️ Arquitectura Lista para Producción
- **Diseño de Microservicios**: Sistemas distribuidos con clara separación de responsabilidades
- **Mejores Prácticas de Seguridad**: Autenticación, autorización y protección de datos apropiadas
- **Infraestructura Escalable**: Diseños nativos de la nube con soporte de containerización

### 🔧 Experiencia del Desarrollador
- **Documentación Integral**: READMEs detallados con instrucciones de configuración y ejemplos
- **Notebooks Interactivos**: Notebooks Jupyter para aprendizaje y experimentación
- **Seguridad de Tipos**: Type hints de Python y validación de esquemas en todo el código

## 🎯 Casos de Uso y Aplicaciones

### Salud y Medicina
- **Anonimización de Imágenes Médicas**: Procesamiento de imágenes médicas compatible con HIPAA
- **Integración de Flujos Clínicos**: Integración fluida con sistemas médicos existentes

### Servicios Financieros
- **Trading Algorítmico**: Generación y análisis automatizado de señales de trading
- **Evaluación de Riesgo**: Métricas avanzadas de riesgo y análisis de portfolios
- **Investigación de Mercado**: Análisis inteligente de tendencias y patrones financieros

### IA Empresarial
- **Procesamiento de Documentos**: Extracción y análisis automatizado de documentos empresariales
- **Gestión del Conocimiento**: Sistemas de conocimiento basados en grafos para relaciones de datos complejas
- **Análisis Potenciado por IA**: Integración de capacidades de IA en flujos de trabajo empresariales existentes

### Medios y Contenido
- **Análisis de Video**: Transcripción automatizada, resumen y análisis de contenido
- **Procesamiento en Tiempo Real**: Análisis de contenido en vivo e insights inteligentes

## 🚦 Primeros Pasos

### Configuración Rápida
1. **Elige tu Dominio**: Selecciona un proyecto de la tabla anterior basado en tus intereses
2. **Sigue la Documentación**: Cada proyecto tiene instrucciones de configuración integrales
3. **Configuración del Entorno**: La mayoría de proyectos usan Python con gestión específica de dependencias
4. **Claves API**: Asegura tus claves API en variables de entorno

### Ruta de Aprendizaje Recomendada
1. **Comienza con Sistemas RAG**: Inicia con el RAG de Análisis Financiero para conceptos fundamentales
2. **Explora Estrategias de Trading**: Progresa a través de las diferentes implementaciones de algoritmos de trading
3. **Integración Avanzada**: Avanza a servidores MCP para entender patrones modernos de integración de IA
4. **Aplicaciones Especializadas**: Profundiza en aplicaciones específicas del dominio como IA médica u OCR distribuido



## ⚖️ Licencia y Descargo de Responsabilidad

Este repositorio contiene implementaciones educativas y de investigación. Los proyectos individuales pueden tener términos de licencia específicos. Por favor revisa la documentación de cada proyecto para:

- **Derechos de Uso**: Casos de uso apropiados y restricciones
- **Términos de API**: Términos y condiciones de servicios de terceros
- **Descargo Financiero**: Advertencias de riesgo de inversión y trading
- **Descargo Médico**: Limitaciones de aplicaciones de salud

---

**Este repositorio representa la convergencia de la experiencia tradicional del dominio con capacidades de IA de vanguardia, demostrando cómo los sistemas modernos de IA pueden integrarse en aplicaciones del mundo real mientras mantienen estándares de calidad de producción y mejores prácticas.**