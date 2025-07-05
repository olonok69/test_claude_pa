# 🎬 Traductor de Videos con IA

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-requerido-red.svg)](https://ffmpeg.org/)
[![License: MIT](https://img.shields.io/badge/Licencia-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Multiplataforma](https://img.shields.io/badge/plataforma-Windows%20%7C%20Linux-lightgrey.svg)]()

Un potente sistema de traducción de videos impulsado por IA, **completamente gratuito** y **local**, que traduce videos en español al inglés utilizando modelos de aprendizaje automático de vanguardia. Sin servicios en la nube, sin suscripciones, sin preocupaciones de privacidad de datos: ¡todo funciona en tu máquina!

## ✨ Características Principales

- 🎯 **Alta Precisión** en transcripción y traducción usando modelos de IA de vanguardia
- ⚡ **Procesamiento Rápido** con soporte GPU/CUDA para aceleración por hardware
- 🔧 **Manejo Robusto de Errores** para procesamiento confiable de varios formatos de video
- 📱 **Soporte Multiplataforma** (Windows 10/11 y Ubuntu Linux)
- 🎨 **Múltiples Opciones de Voz** incluyendo Edge TTS de alta calidad y voces del sistema
- 📹 **Amplio Soporte de Formatos** (.mp4, .avi, .mov, .mkv, .webm)
- ⏱️ **Soporte para Videos Largos** hasta 2+ horas con procesamiento inteligente por segmentos
- 🔄 **Eficiente en Memoria** procesamiento basado en segmentos para archivos grandes
- 🎤 **Procesamiento Avanzado de Audio** con reducción de ruido y normalización
- 🔒 **100% Procesamiento Local** - tus videos nunca salen de tu computadora

## 🎥 Cómo Funciona

![Proceso de Traducción de Video](pipeline.png)

El proceso de traducción sigue estos pasos:

### 1. 🎵 Extracción de Audio
- Extrae la pista de audio del video usando FFmpeg
- Optimiza el audio para reconocimiento de voz (16kHz PCM, canal mono)
- Aplica filtros de reducción de ruido y normalización

### 2. 🎤 Reconocimiento de Voz
- Transcribe audio en español a texto usando **OpenAI Whisper**
- Soporta múltiples tamaños de modelo (base, medium, large)
- Manejo robusto de errores para varias calidades de audio

### 3. 🌐 Traducción de Texto
- Traduce texto en español al inglés usando **transformador Helsinki-NLP**
- Fragmentación inteligente de texto para calidad óptima de traducción
- Mantiene el contexto a través de textos largos

### 4. 🗣️ Texto a Voz
- Genera audio en inglés usando **Edge TTS** o TTS del sistema
- Múltiples opciones de voz con habla de sonido natural
- Calidad de audio y sincronización optimizadas

### 5. 🎬 Procesamiento de Video
- Reemplaza el audio original con el audio traducido
- Preserva la calidad del video y sincronización
- Mantiene el formato original del video y metadatos

### 6. 💾 Generación de Salida
- Crea el video final con pista de audio en inglés
- Sin pérdida de calidad en el procesamiento de video
- Compatible con todos los reproductores de video principales

## 🤖 Modelos de IA Utilizados

![Arquitectura de Modelos de IA](ai_models_use.png)

| Modelo | Propósito | Descripción |
|--------|-----------|-------------|
| **OpenAI Whisper** | Reconocimiento de Voz | Modelo de vanguardia entrenado con 680,000 horas de datos de audio multilingües |
| **Helsinki-NLP opus-mt** | Traducción | Traducción automática neuronal de alta calidad específicamente para Español→Inglés |
| **Edge TTS / pyttsx3** | Texto a Voz | Motores TTS avanzados que proporcionan voces en inglés de sonido natural |

## 🚀 Inicio Rápido

### Requisitos Previos
- Python 3.11 o 3.12
- FFmpeg (para procesamiento de video/audio)
- Al menos 4GB RAM (8GB+ recomendado para videos largos)

### Instalación

**Opción 1: Windows**
```bash
# Instalar Python, FFmpeg y Visual C++ Redistributable
# Ver guía detallada de instalación para Windows abajo

# Instalar gestor de paquetes UV
irm https://astral.sh/uv/install.ps1 | iex

# Crear proyecto
mkdir video-translator && cd video-translator
uv init && uv venv
.venv\Scripts\activate

# Instalar dependencias
uv pip install -r requirements.txt
```

**Opción 2: Ubuntu Linux**
```bash
# Instalar dependencias del sistema
sudo apt update && sudo apt install -y python3-dev ffmpeg build-essential

# Instalar gestor de paquetes UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Crear proyecto
mkdir video-translator && cd video-translator
uv init && uv venv
source .venv/bin/activate

# Instalar dependencias
uv pip install -r requirements.txt
```

### Uso Básico

```bash
# Traducción simple
python video_translator.py video_español.mp4 video_ingles.mp4

# Traducción de alta calidad con Edge TTS
python video_translator.py entrada.mp4 salida.mp4 --edge-tts

# Para videos largos (2+ horas)
python video_translator.py pelicula_larga.mp4 pelicula_larga_en.mp4 --edge-tts --segment-length 600

# Archivo batch de Windows (arrastrar y soltar)
translate_video.bat "Mi Video.mp4" "My Video.mp4"
```

## 📋 Scripts Disponibles

| Script | Propósito | Mejor Para |
|--------|-----------|------------|
| `video_translator.py` | Traducción estándar de video | Videos menores a 1 hora |
| `test_installation.py` | Verificar instalación | Probar configuración |
| `audio_debug_script.py` | Depurar problemas de audio | Solución de problemas |
| `translate_video.bat` | Wrapper de Windows | Uso fácil en Windows |

## 🎤 Opciones de Voz

### Voces Edge TTS (Recomendadas)
| Voz | Género | Acento | Estilo |
|-----|--------|---------|--------|
| `en-US-AriaNeural` | Femenina | Americano | Natural (predeterminada) |
| `en-US-JennyNeural` | Femenina | Americano | Amigable |
| `en-US-GuyNeural` | Masculina | Americano | Natural |
| `en-US-DavisNeural` | Masculina | Americano | Expresiva |
| `en-GB-SoniaNeural` | Femenina | Británico | Natural |
| `en-GB-RyanNeural` | Masculina | Británico | Natural |

### Ejemplos de Uso
```bash
# Usar voz específica
python video_translator.py entrada.mp4 salida.mp4 --edge-tts --voice en-US-GuyNeural

# Acento británico
python video_translator.py entrada.mp4 salida.mp4 --edge-tts --voice en-GB-SoniaNeural
```

## ⚙️ Configuración Avanzada

### Procesamiento de Videos Largos
Para videos más largos de 1 hora, usa procesamiento basado en segmentos:

```bash
# Procesar película de 2 horas con segmentos de 10 minutos
python video_translator.py pelicula.mp4 pelicula_en.mp4 --segment-length 600

# Segmentos más pequeños para mejor uso de memoria
python video_translator.py pelicula.mp4 pelicula_en.mp4 --segment-length 300
```

### Aceleración GPU
Para procesamiento más rápido con GPUs NVIDIA:

```bash
# Instalar PyTorch habilitado para CUDA
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# El sistema detecta y usa GPU automáticamente
```

### Depurar Problemas de Audio
```bash
# Analizar y corregir problemas de audio
python audio_debug_script.py video_problematico.mp4

# Probar diferentes métodos de extracción
python audio_debug_script.py video.mp4 --extract-only
```

## 📊 Estimaciones de Rendimiento

| Duración del Video | Tiempo de Procesamiento | Uso de RAM | Almacenamiento Necesario |
|-------------------|------------------------|------------|-------------------------|
| 30 minutos | 15-60 minutos | 2-4 GB | 5 GB temp |
| 1 hora | 30-120 minutos | 4-6 GB | 10 GB temp |
| 2 horas | 1-2 horas | 6-8 GB | 20 GB temp |

*Los tiempos varían según el hardware, calidad del video y modelos elegidos*

## 🛠️ Guías Detalladas de Instalación

<details>
<summary><strong>🪟 Instalación en Windows (Clic para expandir)</strong></summary>

### Requisitos Previos
1. **Instalar Python 3.11 o 3.12**
   - Descargar de [python.org](https://www.python.org/downloads/windows/)
   - ✅ **IMPORTANTE**: Marcar "Add Python to PATH"

2. **Instalar FFmpeg**
   ```powershell
   # Opción 1: Chocolatey (recomendado)
   choco install ffmpeg
   
   # Opción 2: Descarga manual de ffmpeg.org
   # Extraer a C:\ffmpeg y agregar C:\ffmpeg\bin al PATH
   ```

3. **Instalar Visual C++ Redistributable**
   - Descargar del [sitio web de Microsoft](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Pasos de Configuración
```cmd
# Instalar gestor de paquetes UV
irm https://astral.sh/uv/install.ps1 | iex

# Crear proyecto
mkdir video-translator
cd video-translator
uv init
uv venv

# Activar entorno
.venv\Scripts\activate

# Instalar dependencias
uv pip install -r requirements.txt
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Probar instalación
python test_installation.py
```

### Uso
```cmd
# Uso básico
python video_translator.py "video_español.mp4" "video_ingles.mp4"

# O usar el archivo batch
translate_video.bat "Mi Video.mp4" "My Video.mp4" --edge-tts
```

</details>

<details>
<summary><strong>🐧 Instalación en Ubuntu Linux (Clic para expandir)</strong></summary>

### Requisitos Previos
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y build-essential curl git python3-dev python3-pip

# Instalar FFmpeg y librerías de audio
sudo apt install -y ffmpeg libavcodec-extra espeak espeak-data

# Instalar PortAudio para procesamiento de audio
sudo apt install -y portaudio19-dev python3-pyaudio libasound2-dev

# Dependencias del sistema de audio
sudo apt install -y pulseaudio pulseaudio-utils alsa-utils
```

### Pasos de Configuración
```bash
# Instalar gestor de paquetes UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Crear proyecto
mkdir video-translator && cd video-translator
uv init && uv venv

# Activar entorno
source .venv/bin/activate

# Instalar dependencias
uv pip install -r requirements.txt
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Probar instalación
python test_installation.py
```

### Uso
```bash
# Uso básico
python video_translator.py video_español.mp4 video_ingles.mp4

# O usar el script shell
./translate_video.sh video_español.mp4 video_ingles.mp4
```

</details>

## 🔧 Solución de Problemas

### Problemas Comunes

**🎵 Problemas de Audio/TTS**
```bash
# Probar audio del sistema
speaker-test -t sine -f 1000 -l 1

# Instalar voces adicionales (Ubuntu)
sudo apt install -y espeak-ng espeak-ng-data

# Windows: Verificar voces TTS de Windows en Configuración
```

**🎬 FFmpeg No Encontrado**
```bash
# Verificar instalación de FFmpeg
ffmpeg -version
ffprobe -version

# Ubuntu: Instalar FFmpeg
sudo apt install -y ffmpeg

# Windows: Agregar al PATH o reinstalar
```

**🧠 Problemas de Memoria (Videos Largos)**
```bash
# Usar segmentos más pequeños
python video_translator.py pelicula.mp4 pelicula_en.mp4 --segment-length 300

# Forzar procesamiento CPU (más estable)
CUDA_VISIBLE_DEVICES= python video_translator.py entrada.mp4 salida.mp4
```

**🤖 Errores de Whisper NaN/Logits**
```bash
# Depurar el audio primero
python audio_debug_script.py video_problematico.mp4

# Usar configuraciones más conservadoras
python video_translator.py entrada.mp4 salida.mp4 --conservative
```

### Obtener Ayuda

1. **Ejecutar el script de prueba**: `python test_installation.py`
2. **Verificar la herramienta de depuración**: `python audio_debug_script.py tu_video.mp4`
3. **Revisar logs**: Todas las operaciones se registran con mensajes de error detallados
4. **Probar segmentos más pequeños**: Para videos largos, reducir `--segment-length`

## 📁 Estructura del Proyecto

```
video-translator/
├── .venv/                      # Entorno virtual
├── video_translator.py         # Aplicación principal (videos estándar)
├── audio_debug_script.py       # Herramienta de depuración de audio
├── test_installation.py        # Verificación de instalación
├── translate_video.bat         # Wrapper batch de Windows
├── translate_video.sh          # Wrapper shell de Linux
├── requirements.txt            # Dependencias de Python
├── pyproject.toml             # Configuración del proyecto UV
├── pipeline.html              # Visualización del proceso
├── pipeline.png               # Diagrama de flujo del proceso
├── ai_models_use.png          # Arquitectura de modelos de IA
└── README.md                  # Este archivo
```

## 🔄 Flujos de Trabajo de Ejemplo

### Traducción Básica
```bash
# 1. Poner tu video en español en la carpeta del proyecto
# 2. Ejecutar traducción
python video_translator.py "conferencia_español.mp4" "conference_english.mp4"

# 3. El video traducido se creará con audio en inglés
```

### Traducción de Alta Calidad
```bash
# Usar Edge TTS para mejor calidad de voz
python video_translator.py entrada.mp4 salida.mp4 \
  --edge-tts \
  --voice en-US-AriaNeural
```

### Procesamiento de Videos Largos
```bash
# Para videos de 2+ horas, usar procesamiento por segmentos
python video_translator.py "pelicula_larga.mp4" "long_movie_en.mp4" \
  --edge-tts \
  --segment-length 600  # Segmentos de 10 minutos
```

## 📈 Formatos Soportados

### Formatos de Entrada
- **Video**: .mp4, .avi, .mov, .mkv, .webm, .flv
- **Audio**: .wav, .mp3, .m4a, .flac (para procesamiento solo de audio)

### Formatos de Salida
- **Video**: Mismo formato que la entrada
- **Audio**: Codificación AAC para amplia compatibilidad

## 🎯 Casos de Uso

- **📚 Contenido Educativo**: Traducir conferencias, tutoriales, cursos en español
- **🎬 Entretenimiento**: Traducir películas, documentales, programas
- **💼 Negocios**: Traducir presentaciones, reuniones, videos de entrenamiento
- **📺 Creación de Contenido**: Traducir videos de YouTube, vlogs, entrevistas
- **🏛️ Accesibilidad**: Hacer contenido en español accesible para hablantes de inglés

## ⚡ Consejos de Rendimiento

1. **Usar almacenamiento SSD** para operaciones más rápidas de E/S de archivos
2. **Cerrar programas innecesarios** durante el procesamiento
3. **Habilitar aceleración GPU** para mejora de velocidad de 2-3x
4. **Usar modelos Whisper más grandes** (medium/large) para mejor precisión
5. **Optimizar longitud de segmento** basado en RAM disponible
6. **Usar Edge TTS** para salida de voz de mayor calidad

## 🆚 Comparación con Otras Soluciones

| Característica | Esta Herramienta | Servicios en la Nube | Otras Herramientas Locales |
|---------------|------------------|---------------------|---------------------------|
| **Costo** | Gratis | $10-50/hora | $50-500 pago único |
| **Privacidad** | 100% Local | Basado en la nube | Varía |
| **Calidad** | Alta | Muy Alta | Media |
| **Velocidad** | Rápida | Muy Rápida | Lenta |
| **Sin Internet** | ✅ Sí | ❌ No | ✅ Sí |
| **Uso Ilimitado** | ✅ Sí | ❌ No | ✅ Sí |

## 🛡️ Privacidad y Seguridad

- **🔒 Privacidad Completa**: Todo el procesamiento ocurre localmente en tu máquina
- **🚫 Sin Recolección de Datos**: Sin telemetría, analíticas o subida de datos
- **📁 Almacenamiento Local**: Videos y modelos almacenados solo en tu computadora
- **🔓 Código Abierto**: Todo el código es transparente y auditable
- **⚡ Operación Sin Internet**: Funciona sin conexión a internet (después de la configuración inicial)

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor, siéntete libre de enviar un Pull Request. Para cambios importantes, por favor abre un issue primero para discutir lo que te gustaría cambiar.

## 💡 Mejoras Futuras

- 🌍 Pares de idiomas adicionales (Francés↔Inglés, Alemán↔Inglés)
- 🎥 Traducción en tiempo real para transmisiones en vivo
- 🎛️ Interfaz gráfica para usuarios no técnicos
- 🔧 Más opciones de voz TTS y personalización
- 📱 Versión de aplicación móvil
- 🎨 Generación e incrustación de subtítulos
- 🤖 Integración con otros modelos de IA

## 📞 Soporte

Si encuentras algún problema o tienes preguntas:

1. Revisar la sección de solución de problemas arriba
2. Ejecutar `python test_installation.py` para verificar tu configuración
3. Usar `python audio_debug_script.py` para problemas relacionados con audio
4. Revisar los logs de error detallados para problemas específicos

---