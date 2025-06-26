# Guía de Chainlit: Construyendo Aplicaciones de IA Conversacional

## ¿Qué es Chainlit?

Chainlit es un paquete de Python de código abierto para construir IA Conversacional lista para producción. Permite a los desarrolladores crear aplicaciones de IA conversacional listas para producción en minutos, no semanas, proporcionando una interfaz similar a ChatGPT con código mínimo y cero complejidad de front-end.

### Características Principales

Chainlit ofrece varias características poderosas:
- **Construcción rápida**: Comienza en un par de líneas de Python  
- **Autenticación**: Integra con proveedores de identidad corporativa e infraestructura de autenticación existente  
- **Persistencia de datos**: Recopila, monitorea y analiza datos de tus usuarios  
- **Visualiza razonamiento multi-paso**: Comprende los pasos intermedios que produjeron una salida de un vistazo  
- **Multiplataforma**: Escribe la lógica de tu asistente una vez, úsala en todas partes

### Integraciones Populares

Chainlit es compatible con todos los programas y bibliotecas de Python. Dicho esto, viene con un conjunto de integraciones con bibliotecas y frameworks populares, incluyendo:

- **LangChain** - Para construir flujos de trabajo de agentes
- **OpenAI** - Integración directa con APIs de OpenAI
- **Mistral AI** - Soporte para modelos Mistral
- **LlamaIndex** - Para indexación y recuperación de documentos
- **Autogen** - Conversaciones multi-agente

## Ciclo de Vida del Chat

Cada vez que un usuario se conecta a tu aplicación Chainlit, se crea una nueva sesión de chat. Una sesión de chat pasa por un ciclo de vida de eventos, a los cuales puedes responder definiendo hooks.

### Hooks Principales del Ciclo de Vida

Los principales eventos del ciclo de vida a los que puedes responder son:

#### 1. Inicio del Chat
El decorador `@cl.on_chat_start` se usa para definir un hook que se llama cuando inicia una nueva sesión de chat:

```python
@cl.on_chat_start
def on_chat_start():
    print("¡Una nueva sesión de chat ha comenzado!")
```

#### 2. Manejo de Mensajes
El decorador `@cl.on_message` se usa para definir un hook que se llama cuando se recibe un nuevo mensaje del usuario:

```python
@cl.on_message
def on_message(msg: cl.Message):
    print("El usuario envió: ", msg.content)
```

#### 3. Detener Chat
El decorador `@cl.on_stop` se usa para definir un hook que se llama cuando el usuario hace clic en el botón de detener mientras una tarea estaba ejecutándose:

```python
@cl.on_stop
def on_stop():
    print("¡El usuario quiere detener la tarea!")
```

#### 4. Fin del Chat
El decorador `@cl.on_chat_end` se usa para definir un hook que se llama cuando la sesión de chat termina, ya sea porque el usuario se desconectó o comenzó una nueva sesión de chat:

```python
@cl.on_chat_end
def on_chat_end():
    print("¡El usuario se desconectó!")
```

#### 5. Reanudar Chat
El decorador `@cl.on_chat_resume` se usa para definir un hook que se llama cuando un usuario reanuda una sesión de chat que fue previamente desconectada. Esto solo puede suceder si la autenticación y la persistencia de datos están habilitadas.

## Conceptos Centrales

### Mensajes

Un Mensaje es una pieza de información que se envía del usuario a un asistente y viceversa. Junto con los hooks del ciclo de vida, son los bloques de construcción de un chat. Un mensaje tiene contenido, una marca de tiempo y no puede ser anidado.

#### Ejemplo Básico de Mensaje

```python
import chainlit as cl

@cl.on_message
async def on_message(message: cl.Message):
    response = f"¡Hola, acabas de enviar: {message.content}!"
    await cl.Message(response).send()
```

#### Contexto del Chat

Dado que los LLMs son sin estado, a menudo tendrás que acumular los mensajes de la conversación actual en una lista para proporcionar el contexto completo al LLM con cada consulta. Podrías hacer eso manualmente con user_session. Sin embargo, Chainlit proporciona una forma integrada de hacer esto:

```python
@cl.on_message
async def on_message(message: cl.Message):
    # Obtener todos los mensajes en la conversación en formato OpenAI
    print(cl.chat_context.to_openai())
    # Enviar la respuesta
    response = f"¡Hola, acabas de enviar: {message.content}!"
    await cl.Message(response).send()
```

### Pasos

Los Asistentes impulsados por LLM toman múltiples pasos para procesar la solicitud de un usuario, formando una cadena de pensamiento. A diferencia de un Mensaje, un Paso tiene un tipo, una entrada/salida y un inicio/fin. Dependiendo de la configuración config.ui.cot, la cadena completa de pensamiento puede mostrarse completa, oculta o solo las llamadas de herramientas.

#### Ejemplo de Paso

```python
import chainlit as cl

@cl.step(type="tool")
async def tool():
    # Simular una tarea en ejecución
    await cl.sleep(2)
    return "¡Respuesta de la herramienta!"

@cl.on_message
async def main(message: cl.Message):
    # Llamar a la herramienta
    tool_res = await tool()
    # Enviar la respuesta final
    await cl.Message(content="Esta es la respuesta final").send()
```

### Sesiones de Usuario

La sesión de usuario está diseñada para persistir datos en memoria a través del ciclo de vida de una sesión de chat. Cada sesión de usuario es única para un usuario y una sesión de chat dada.

#### Ejemplo de Gestión de Sesión

```python
import chainlit as cl

@cl.on_chat_start
def on_chat_start():
    cl.user_session.set("counter", 0)

@cl.on_message
async def on_message(message: cl.Message):
    counter = cl.user_session.get("counter")
    counter += 1
    cl.user_session.set("counter", counter)
    await cl.Message(content=f"¡Enviaste {counter} mensaje(s)!").send()
```

## Construyendo Tu Primera Aplicación Chainlit

### Instalación

Primero, instala Chainlit:

```bash
pip install chainlit
```

### Bot Echo Simple

Crea un archivo llamado `app.py`:

```python
import chainlit as cl

@cl.on_chat_start
async def on_chat_start():
    await cl.Message(content="¡Hola! Soy tu asistente. ¿Cómo puedo ayudarte hoy?").send()

@cl.on_message
async def on_message(message: cl.Message):
    # Hacer eco del mensaje del usuario
    response = f"Dijiste: '{message.content}'"
    await cl.Message(content=response).send()
```

Ejecuta la aplicación:

```bash
chainlit run app.py
```

### Aplicación Mejorada con Acciones

```python
import chainlit as cl

@cl.on_chat_start
async def start():
    # Crear botones interactivos
    actions = [
        cl.Action(
            name="help_button",
            label="🤝 Obtener Ayuda", 
            payload={"value": "help"}
        ),
        cl.Action(
            name="about_button",
            label="ℹ️ Acerca de",
            payload={"value": "about"}
        )
    ]
    
    await cl.Message(
        content="¡Bienvenido! Elige una opción a continuación:",
        actions=actions
    ).send()

@cl.action_callback("help_button")
async def on_help_button(action):
    await cl.Message(content="Aquí está cómo usar este chatbot...").send()

@cl.action_callback("about_button") 
async def on_about_button(action):
    await cl.Message(content="¡Esta es una aplicación demo de Chainlit!").send()

@cl.on_message
async def on_message(message: cl.Message):
    # Procesar el mensaje del usuario
    response = f"Recibí: {message.content}. ¿En qué más puedo ayudar?"
    await cl.Message(content=response).send()
```

### Integración con LLMs

Aquí hay un ejemplo usando OpenAI:

```python
import chainlit as cl
import openai

# Establecer tu clave API de OpenAI
openai.api_key = "tu-clave-api-aqui"

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("messages", [])
    await cl.Message(content="¡Hola! Estoy impulsado por GPT. ¡Pregúntame cualquier cosa!").send()

@cl.on_message
async def on_message(message: cl.Message):
    # Obtener historial de conversación
    messages = cl.user_session.get("messages", [])
    
    # Agregar mensaje del usuario al historial
    messages.append({"role": "user", "content": message.content})
    
    # Llamar a la API de OpenAI
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=messages
    )
    
    # Obtener respuesta del asistente
    assistant_message = response.choices[0].message.content
    
    # Agregar respuesta del asistente al historial
    messages.append({"role": "assistant", "content": assistant_message})
    cl.user_session.set("messages", messages)
    
    # Enviar respuesta al usuario
    await cl.Message(content=assistant_message).send()
```

## Características Avanzadas

### Respuestas en Streaming

Chainlit soporta streaming en tiempo real de respuestas LLM. Esto significa que puedes enviar contenido al usuario incrementalmente mientras se genera:

```python
@cl.on_message
async def on_message(message: cl.Message):
    await cl.Message(content="Pensando...").send()
    
    async for chunk in llm.astream(message.content):
        await cl.Message(content=chunk, author="LLM", stream=True).send()
```

### Subida de Archivos

Habilita la subida de archivos en tu `config.toml`:

```toml
[features.spontaneous_file_upload]
enabled = true
accept = ["*/*"]
max_files = 5
max_size_mb = 500
```

Maneja subidas de archivos en tu código:

```python
@cl.on_message
async def on_message(message: cl.Message):
    if message.elements:
        for element in message.elements:
            if element.type == "file":
                # Procesar el archivo subido
                content = element.content
                await cl.Message(f"Archivo recibido: {element.name}").send()
```

### Configuraciones del Chat

Agregar configuraciones personalizables:

```python
@cl.on_chat_start
async def on_chat_start():
    settings = cl.ChatSettings([
        cl.Select(
            id="model",
            label="Modelo de IA",
            values=["gpt-3.5-turbo", "gpt-4", "claude-3"],
            initial_index=0
        ),
        cl.Slider(
            id="temperature",
            label="Temperatura",
            initial=0.7,
            min=0,
            max=2,
            step=0.1
        )
    ])
    await settings.send()

@cl.on_settings_update
async def on_settings_update(settings):
    cl.user_session.set("model", settings["model"])
    cl.user_session.set("temperature", settings["temperature"])
```

## Configuración

Crea un archivo `config.toml` para personalizar tu aplicación:

```toml
[project]
name = "Mi App Chainlit"
description = "Una aplicación personalizada de IA conversacional"

[UI]
name = "Mi Asistente"
default_expand_messages = true
default_collapse_content = false

[features]
spontaneous_file_upload = true
latex = true

[features.speech_to_text]
enabled = false

[theme]
primary_color = "#1976d2"
```

## Despliegue

### Desarrollo Local
```bash
chainlit run app.py
```

### Despliegue de Producción
```bash
chainlit run app.py --host 0.0.0.0 --port 8000
```

### Despliegue con Docker
Crea un `Dockerfile`:

```dockerfile
FROM python:3.9
RUN pip install chainlit
COPY . /app
WORKDIR /app
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
```

## Mejores Prácticas

1. **Manejo de Errores**: Siempre envuelve tus llamadas LLM en bloques try-catch
2. **Limitación de Velocidad**: Implementa limitación de velocidad para aplicaciones de producción  
3. **Autenticación**: Habilita autenticación para seguimiento de usuarios y persistencia de datos
4. **Monitoreo**: Usa las analíticas integradas de Chainlit o integra con monitoreo externo
5. **Pruebas**: Prueba tu aplicación con varias entradas de usuario y casos extremos

## Recursos

- **Documentación Oficial**: https://docs.chainlit.io/
- **Repositorio GitHub**: https://github.com/Chainlit/chainlit
- **Ejemplos de la Comunidad**: https://docs.chainlit.io/examples/community
- **Comunidad Discord**: Únete para soporte y discusiones

Chainlit hace increíblemente fácil construir aplicaciones de IA conversacional. Puedes encontrar varios ejemplos de aplicaciones Chainlit que aprovechan herramientas y servicios como OpenAI, Anthropic, LangChain, LlamaIndex, ChromaDB, Pinecone y más.

La simplicidad del framework, combinada con sus características poderosas, lo convierte en una excelente opción para desarrolladores que buscan crear aplicaciones de IA conversacional listas para producción de manera rápida y eficiente.