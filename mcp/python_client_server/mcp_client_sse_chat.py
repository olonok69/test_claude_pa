import ast
import asyncio
import json
import os
from typing import Dict, Optional
from mcp import ClientSession
from mcp.client.sse import sse_client
from openai import OpenAI
import mcp.client.sse as _sse_mod
from httpx import AsyncClient as _BaseAsyncClient
from loguru import logger

from dotenv import load_dotenv

load_dotenv("./keys/.env")  # load environment variables from .env

import httpx

_orig_request = httpx.AsyncClient.request


async def _patched_request(self, method, url, *args, **kwargs):
    # ensure follow_redirects is set so 307 → /messages/ works
    kwargs.setdefault("follow_redirects", True)
    return await _orig_request(self, method, url, *args, **kwargs)


httpx.AsyncClient.request = _patched_request


def llm_client(message: str):
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an intelligent Assistant. You will execute tasks as instructed",
            },
            {
                "role": "user",
                "content": message,
            },
        ],
    )

    result = completion.choices[0].message.content
    return result


def get_prompt_to_identify_tool_and_arguments(query: str, tools: any, context=list):
    tools_description = "\n".join(
        [f"{tool.name}: {tool.description}, {tool.inputSchema}" for tool in tools.tools]
    )
    return (
        "You are a helpful assistant with access to these tools and context:\n\n"
        f"CONTEXT: {context} \n"
        f"{tools_description}\n"
        "Choose the appropriate tool based on the user's question. \n"
        f"User's Question: {query}\n"
        "If no tool is needed, reply directly.\n\n"
        "IMPORTANT: Always identify a single tool only."
        "IMPORTANT: When you need to use a tool, you must ONLY respond with "
        "the exact JSON object format below, DO NOT ADD any other comment.:\n"
        "Keep the values in str "
        "{\n"
        '    "tool": "tool-name",\n'
        '    "arguments": {\n'
        '        "argument-name": "value"\n'
        "    }\n"
        "}\n\n"
    )


def get_prompt_to_process_tool_response(query: str, tool_response: str, context: list):
    return (
        "You are a helpful assistant."
        " Your job is to decide whether to respond directly to the user or continue processing using additional tools, based on:"
        "\n- The user's query"
        "\n- The tool's response"
        "\n- The conversation context."
        "\nSometimes, multiple tools may be needed to fully address the user's request."
        "\nCarefully analyze the query, tool response, and context together."
        "\nIf no further processing is needed, respond directly to the user and set the action to 'respond_to_user' with your response."
        "\nIf more processing is needed (for example, if a query has multiple tasks but only one has been handled), clearly state what's pending and leave the action blank."
        "\n\n### CRITICAL INSTRUCTIONS FOR RESPONSE FORMAT ###"
        "\nYou MUST return ONLY a valid JSON object in the following format without any additional text or explanation:"
        "\n{"
        '\n    "action": "", // Set to "respond_to_user" if this is a final response, otherwise leave empty'
        '\n    "response": "" // Your response to the user or next processing step'
        "\n}"
        "\n\n### DO NOT include any other text or explanation outside of the JSON object ###"
        "\n\nInputs:"
        f"\nUser's query: {query}"
        f"\nTool response: {tool_response}"
        f"\nCONTEXT: {context}"
    )


async def sse_ops(query: str, memory: list):
    sse_url = "http://localhost:8100/sse"

    # 1) Open SSE → yields (in_stream, out_stream)
    async with sse_client(url=sse_url) as (in_stream, out_stream):
        # 2) Create an MCP session over those streams
        async with ClientSession(in_stream, out_stream) as session:
            # 3) Initialize
            info = await session.initialize()
            logger.info(
                f"Connected to {info.serverInfo.name} v{info.serverInfo.version}"
            )

            # 4) List tools
            tools = await session.list_tools()
            print(tools)
            # print("Available tools:", [t.name for t in tools])

            prompt = get_prompt_to_identify_tool_and_arguments(
                query=query, tools=tools, context=memory
            )
            logger.info(f"Printing tool identification prompt\n {prompt}")

            response = llm_client(prompt)
            logger.info(f"Response from LLM {response}")

            try:
                tool_call = json.loads(response)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract the JSON part using regex or string operations
                import re

                json_match = re.search(r"\{[\s\S]*\}", response)
                if json_match:
                    try:
                        tool_call = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        logger.error(
                            "Failed to parse tool call JSON even after extraction"
                        )
                        return {
                            "action": "respond_to_user",
                            "response": "I'm having trouble processing your request. Please try again.",
                        }
                else:
                    logger.error("No JSON object found in the response")
                    return {
                        "action": "respond_to_user",
                        "response": "I'm having trouble processing your request. Please try again.",
                    }

            result = await session.call_tool(
                tool_call["tool"], arguments=tool_call["arguments"]
            )

            tool_response = result.content[0].text

            response_prompt = get_prompt_to_process_tool_response(
                query=query, tool_response=tool_response, context=memory
            )
            logger.info(f"Printing tool process response prompt\n {response_prompt}")
            final_response = llm_client(response_prompt)

            # Fix for parsing the response - use multiple approaches
            logger.info(f"Final response from LLM: {final_response}")

            # Method 1: Try direct JSON parsing
            try:
                json_dict = json.loads(final_response)
                if not isinstance(json_dict, Dict):
                    raise ValueError("Response not a valid dictionary")
                logger.info("Successfully parsed response with json.loads()")
                return json_dict
            except json.JSONDecodeError:
                logger.info("Direct JSON parsing failed, trying alternative methods")

            # Method 2: Try to extract with regex and clean up the string
            try:
                import re

                # Look for JSON-like pattern and extract it
                json_match = re.search(r"\{.*\}", final_response.replace("\n", " "))
                if json_match:
                    json_str = json_match.group(0)
                    logger.info(f"Extracted potential JSON: {json_str}")
                    # Try to parse the extracted string
                    json_dict = json.loads(json_str)
                    logger.info("Successfully parsed extracted JSON")
                    return json_dict
            except Exception as e:
                logger.error(f"Regex extraction failed: {e}")

            # Method 3: Parse "action" and "response" fields separately
            try:
                import re

                action_match = re.search(r'"action":\s*"([^"]*)"', final_response)
                response_match = re.search(r'"response":\s*"([^"]*)"', final_response)

                if action_match and response_match:
                    action = action_match.group(1)
                    response_text = response_match.group(1)
                    logger.info(
                        f"Extracted action: {action}, response: (truncated for log)"
                    )

                    # If we found both fields, create a dict manually
                    json_dict = {"action": action, "response": response_text}
                    return json_dict
            except Exception as e:
                logger.error(f"Field extraction failed: {e}")

            # Method 4: Extract the most important part - the actual content
            try:
                # Look for a clear "respond_to_user" pattern
                if "respond_to_user" in final_response:
                    # Extract everything after "response":
                    content_match = re.search(
                        r'"response":\s*"(.*?)"(?:\s*\}|$)', final_response, re.DOTALL
                    )
                    if content_match:
                        response_content = content_match.group(1)
                    else:
                        # Fallback to extracting content between triple backticks if present
                        content_match = re.search(
                            r"```(.*?)```", final_response, re.DOTALL
                        )
                        if content_match:
                            response_content = content_match.group(1)
                        else:
                            # Just use everything after "response":
                            parts = final_response.split('"response":')
                            if len(parts) > 1:
                                response_content = parts[1].strip()
                            else:
                                response_content = final_response

                    logger.info("Created response using content extraction")
                    return {
                        "action": "respond_to_user",
                        "response": response_content.strip('" \t\n}'),
                    }
            except Exception as e:
                logger.error(f"Content extraction failed: {e}")

            # Method 5: Final fallback - manually create a response with the full text
            logger.warning("All parsing methods failed, using fallback response")
            return {
                "action": "respond_to_user",
                "response": "I processed your request but couldn't properly format the response. Here's what I found: "
                + final_response,
            }


async def main():
    memory = []

    ##Use this as the query to the agent = "What is the z-score of AAPL for the last 20 days?"
    print("Chat Agent: Hello! How can I assist you today?")
    user_input = input("You: ")

    while True:
        if user_input.lower() in ["exit", "bye", "close"]:
            print("See you later!")
            break

        try:
            response = await sse_ops(user_input, memory)

            # Make sure we have a valid response
            if not isinstance(response, dict):
                logger.error(f"Invalid response format: {response}")
                response = {
                    "action": "respond_to_user",
                    "response": "I encountered an error processing your request. Please try again.",
                }

            memory.append(response)

            if response.get("action") == "respond_to_user":
                print(
                    "Response from Agent:",
                    response.get("response", "No response content"),
                )
                user_input = input("You: ")
                memory.append(user_input)
            else:
                # If no action or not respond_to_user, treat as intermediate step
                logger.info(
                    f"Intermediate step: {response.get('response', 'No content')}"
                )
                user_input = response.get("response", "")
                if not user_input:
                    # If empty response, ask user for input instead of continuing
                    print("Response from Agent: I need more information to proceed.")
                    user_input = input("You: ")
                    memory.append(user_input)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            print(
                "Response from Agent: I encountered an error. Let's start a new conversation."
            )
            user_input = input("You: ")
            # Reset memory if we have an error to avoid cascading issues
            memory = [user_input]


if __name__ == "__main__":
    asyncio.run(main())
