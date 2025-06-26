# Chainlit Guide: Building Conversational AI Applications

## What is Chainlit?

Chainlit is an open-source Python package to build production ready Conversational AI. It enables developers to build python production-ready conversational AI applications in minutes, not weeks, providing a ChatGPT-like interface with minimal code and zero front-end complexity.

### Key Features

Chainlit offers several powerful features:
- **Build fast**: Get started in a couple lines of Python  
- **Authentication**: Integrate with corporate identity providers and existing authentication infrastructure  
- **Data persistence**: Collect, monitor and analyze data from your users  
- **Visualize multi-steps reasoning**: Understand the intermediary steps that produced an output at a glance  
- **Multi Platform**: Write your assistant logic once, use everywhere

### Popular Integrations

Chainlit is compatible with all Python programs and libraries. That being said, it comes with a set of integrations with popular libraries and frameworks, including:

- **LangChain** - For building agent workflows
- **OpenAI** - Direct integration with OpenAI APIs
- **Mistral AI** - Support for Mistral models
- **LlamaIndex** - For document indexing and retrieval
- **Autogen** - Multi-agent conversations

## Chat Lifecycle

Whenever a user connects to your Chainlit app, a new chat session is created. A chat session goes through a life cycle of events, which you can respond to by defining hooks.

### Core Lifecycle Hooks

The main lifecycle events you can respond to are:

#### 1. Chat Start
The `@cl.on_chat_start` decorator is used to define a hook that is called when a new chat session starts:

```python
@cl.on_chat_start
def on_chat_start():
    print("A new chat session has started!")
```

#### 2. Message Handling
The `@cl.on_message` decorator is used to define a hook that is called when a new message is received from the user:

```python
@cl.on_message
def on_message(msg: cl.Message):
    print("The user sent: ", msg.content)
```

#### 3. Chat Stop
The `@cl.on_stop` decorator is used to define a hook that is called when the user clicks the stop button while a task was running:

```python
@cl.on_stop
def on_stop():
    print("The user wants to stop the task!")
```

#### 4. Chat End
The `@cl.on_chat_end` decorator is used to define a hook that is called when the chat session ends either because the user disconnected or started a new chat session:

```python
@cl.on_chat_end
def on_chat_end():
    print("The user disconnected!")
```

#### 5. Chat Resume
The `@cl.on_chat_resume` decorator is used to define a hook that is called when a user resumes a chat session that was previously disconnected. This can only happen if authentication and data persistence are enabled.

## Core Concepts

### Messages

A Message is a piece of information that is sent from the user to an assistant and vice versa. Coupled with life cycle hooks, they are the building blocks of a chat. A message has a content, a timestamp and cannot be nested.

#### Basic Message Example

```python
import chainlit as cl

@cl.on_message
async def on_message(message: cl.Message):
    response = f"Hello, you just sent: {message.content}!"
    await cl.Message(response).send()
```

#### Chat Context

Since LLMs are stateless, you will often have to accumulate the messages of the current conversation in a list to provide the full context to LLM with each query. You could do that manually with the user_session. However, Chainlit provides a built-in way to do this:

```python
@cl.on_message
async def on_message(message: cl.Message):
    # Get all the messages in the conversation in the OpenAI format
    print(cl.chat_context.to_openai())
    # Send the response
    response = f"Hello, you just sent: {message.content}!"
    await cl.Message(response).send()
```

### Steps

LLM powered Assistants take multiple steps to process a user's request, forming a chain of thought. Unlike a Message, a Step has a type, an input/output and a start/end. Depending on the config.ui.cot setting, the full chain of thought can be displayed in full, hidden or only the tool calls.

#### Step Example

```python
import chainlit as cl

@cl.step(type="tool")
async def tool():
    # Simulate a running task
    await cl.sleep(2)
    return "Response from the tool!"

@cl.on_message
async def main(message: cl.Message):
    # Call the tool
    tool_res = await tool()
    # Send the final answer
    await cl.Message(content="This is the final answer").send()
```

### User Sessions

The user session is designed to persist data in memory through the life cycle of a chat session. Each user session is unique to a user and a given chat session.

#### Session Management Example

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
    await cl.Message(content=f"You sent {counter} message(s)!").send()
```

## Building Your First Chainlit Application

### Installation

First, install Chainlit:

```bash
pip install chainlit
```

### Simple Echo Bot

Create a file called `app.py`:

```python
import chainlit as cl

@cl.on_chat_start
async def on_chat_start():
    await cl.Message(content="Hello! I'm your assistant. How can I help you today?").send()

@cl.on_message
async def on_message(message: cl.Message):
    # Echo back the user's message
    response = f"You said: '{message.content}'"
    await cl.Message(content=response).send()
```

Run the application:

```bash
chainlit run app.py
```

### Enhanced Application with Actions

```python
import chainlit as cl

@cl.on_chat_start
async def start():
    # Create interactive buttons
    actions = [
        cl.Action(
            name="help_button",
            label="🤝 Get Help", 
            payload={"value": "help"}
        ),
        cl.Action(
            name="about_button",
            label="ℹ️ About",
            payload={"value": "about"}
        )
    ]
    
    await cl.Message(
        content="Welcome! Choose an option below:",
        actions=actions
    ).send()

@cl.action_callback("help_button")
async def on_help_button(action):
    await cl.Message(content="Here's how to use this chatbot...").send()

@cl.action_callback("about_button") 
async def on_about_button(action):
    await cl.Message(content="This is a Chainlit demo application!").send()

@cl.on_message
async def on_message(message: cl.Message):
    # Process the user's message
    response = f"I received: {message.content}. How else can I help?"
    await cl.Message(content=response).send()
```

### Integration with LLMs

Here's an example using OpenAI:

```python
import chainlit as cl
import openai

# Set your OpenAI API key
openai.api_key = "your-api-key-here"

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("messages", [])
    await cl.Message(content="Hi! I'm powered by GPT. Ask me anything!").send()

@cl.on_message
async def on_message(message: cl.Message):
    # Get conversation history
    messages = cl.user_session.get("messages", [])
    
    # Add user message to history
    messages.append({"role": "user", "content": message.content})
    
    # Call OpenAI API
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=messages
    )
    
    # Get assistant response
    assistant_message = response.choices[0].message.content
    
    # Add assistant response to history
    messages.append({"role": "assistant", "content": assistant_message})
    cl.user_session.set("messages", messages)
    
    # Send response to user
    await cl.Message(content=assistant_message).send()
```

## Advanced Features

### Streaming Responses

Chainlit supports real-time streaming of LLM responses. This means you can send content to the user incrementally as it's generated:

```python
@cl.on_message
async def on_message(message: cl.Message):
    await cl.Message(content="Thinking...").send()
    
    async for chunk in llm.astream(message.content):
        await cl.Message(content=chunk, author="LLM", stream=True).send()
```

### File Uploads

Enable file uploads in your `config.toml`:

```toml
[features.spontaneous_file_upload]
enabled = true
accept = ["*/*"]
max_files = 5
max_size_mb = 500
```

Handle file uploads in your code:

```python
@cl.on_message
async def on_message(message: cl.Message):
    if message.elements:
        for element in message.elements:
            if element.type == "file":
                # Process the uploaded file
                content = element.content
                await cl.Message(f"Received file: {element.name}").send()
```

### Chat Settings

Add customizable settings:

```python
@cl.on_chat_start
async def on_chat_start():
    settings = cl.ChatSettings([
        cl.Select(
            id="model",
            label="AI Model",
            values=["gpt-3.5-turbo", "gpt-4", "claude-3"],
            initial_index=0
        ),
        cl.Slider(
            id="temperature",
            label="Temperature",
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

## Configuration

Create a `config.toml` file to customize your application:

```toml
[project]
name = "My Chainlit App"
description = "A custom conversational AI application"

[UI]
name = "My Assistant"
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

## Deployment

### Local Development
```bash
chainlit run app.py
```

### Production Deployment
```bash
chainlit run app.py --host 0.0.0.0 --port 8000
```

### Docker Deployment
Create a `Dockerfile`:

```dockerfile
FROM python:3.9
RUN pip install chainlit
COPY . /app
WORKDIR /app
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
```

## Best Practices

1. **Error Handling**: Always wrap your LLM calls in try-catch blocks
2. **Rate Limiting**: Implement rate limiting for production applications  
3. **Authentication**: Enable authentication for user tracking and data persistence
4. **Monitoring**: Use Chainlit's built-in analytics or integrate with external monitoring
5. **Testing**: Test your application with various user inputs and edge cases

## Resources

- **Official Documentation**: https://docs.chainlit.io/
- **GitHub Repository**: https://github.com/Chainlit/chainlit
- **Community Examples**: https://docs.chainlit.io/examples/community
- **Discord Community**: Join for support and discussions

Chainlit makes it incredibly easy to build conversational AI applications. You can find various examples of Chainlit apps that leverage tools and services such as OpenAI, Anthropic, LangChain, LlamaIndex, ChromaDB, Pinecone and more.

The framework's simplicity, combined with its powerful features, makes it an excellent choice for developers looking to create production-ready conversational AI applications quickly and efficiently.