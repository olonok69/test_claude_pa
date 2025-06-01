import ast
import asyncio
import json
import os
import re
from typing import Dict, List, Optional, Any, Tuple, Union
from loguru import logger
import httpx
from httpx import AsyncClient as _BaseAsyncClient

from mcp import ClientSession
from mcp.client.sse import sse_client
from openai import OpenAI
import mcp.client.sse as _sse_mod

from dotenv import load_dotenv

# Load environment variables
load_dotenv("./keys/.env")

# Patch httpx to always follow redirects
_orig_request = httpx.AsyncClient.request


async def _patched_request(self, method, url, *args, **kwargs):
    kwargs.setdefault("follow_redirects", True)
    return await _orig_request(self, method, url, *args, **kwargs)


httpx.AsyncClient.request = _patched_request


class LLMClient:
    """Client for interacting with LLM services."""

    @staticmethod
    def get_completion(message: str, model: str = "gpt-4o-mini") -> str:
        """Get completion from LLM."""
        client = OpenAI()

        completion = client.chat.completions.create(
            model=model,
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

        return completion.choices[0].message.content


class PromptGenerator:
    """Generates prompts for tool selection and response processing."""

    @staticmethod
    def identify_tool_and_arguments(query: str, tools: Any, context: List) -> str:
        """Generate prompt to identify which tool to use and with what arguments."""
        tools_description = "\n".join(
            [
                f"{tool.name}: {tool.description}, {tool.inputSchema}"
                for tool in tools.tools
            ]
        )

        return (
            "You are a helpful assistant with access to these tools and context:\n\n"
            f"CONTEXT: {context} \n"
            f"{tools_description}\n"
            "Choose the appropriate tool based on the user's question. \n"
            f"User's Question: {query}\n"
            "IMPORTANT: If the user's question can be answered directly without using any of the tools "
            "(such as general knowledge questions, translations, or anything not related to financial analysis), "
            'respond with {{"direct_response": true, "response": "Your detailed answer here"}}.\n\n'
            "IMPORTANT: Only use tools for financial analysis queries that require specific calculations or data.\n\n"
            "IMPORTANT: When you need to use a tool, you must ONLY respond with "
            "the exact JSON object format below, DO NOT ADD any other comment.:\n"
            "{\n"
            '    "tool": "tool-name",\n'
            '    "arguments": {\n'
            '        "argument-name": "value"\n'
            "    }\n"
            "}\n\n"
        )

    @staticmethod
    def process_tool_response(query: str, tool_response: str, context: List) -> str:
        """Generate prompt to process a tool's response."""
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


class ResponseParser:
    """Parser for LLM responses."""

    @staticmethod
    def parse_tool_call(response: str) -> Dict:
        """Parse the tool call JSON from LLM response."""
        try:
            # Try direct JSON parsing first
            json_response = json.loads(response)

            # Check if this is a direct response (not a tool call)
            if (
                "direct_response" in json_response
                and json_response["direct_response"] is True
            ):
                return {
                    "direct_response": True,
                    "response": json_response.get(
                        "response", "I don't have a specific answer for that."
                    ),
                }

            return json_response
        except json.JSONDecodeError:
            # Check if this looks like a conversational response rather than a tool call
            if not re.search(r'"tool"\s*:', response) and not re.search(
                r'"arguments"\s*:', response
            ):
                # This is likely a direct response, not a tool call
                return {"direct_response": True, "response": response.strip()}

            # Extract JSON using regex if parsing fails
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                try:
                    json_dict = json.loads(json_match.group(0))
                    # Check if this is a direct response
                    if (
                        "direct_response" in json_dict
                        and json_dict["direct_response"] is True
                    ):
                        return {
                            "direct_response": True,
                            "response": json_dict.get(
                                "response", "I don't have a specific answer for that."
                            ),
                        }
                    return json_dict
                except json.JSONDecodeError:
                    logger.error("Failed to parse tool call JSON even after extraction")
            else:
                logger.error("No JSON object found in the response")

            # If it doesn't look like a JSON tool call, treat it as a direct response
            if not re.search(r'"tool"\s*:', response) and not re.search(
                r'"arguments"\s*:', response
            ):
                return {"direct_response": True, "response": response.strip()}

            # Return error response if parsing fails
            return {
                "tool": "error",
                "arguments": {"message": "Failed to parse tool call"},
            }

    @staticmethod
    def parse_final_response(response: str) -> Dict:
        """Parse the final response from LLM using multiple methods."""
        # Method 1: Try direct JSON parsing
        try:
            json_dict = json.loads(response)
            if not isinstance(json_dict, Dict):
                raise ValueError("Response not a valid dictionary")
            logger.info("Successfully parsed response with json.loads()")
            return json_dict
        except json.JSONDecodeError:
            logger.info("Direct JSON parsing failed, trying alternative methods")

        # Method 2: Try to extract with regex and clean up the string
        try:
            json_match = re.search(r"\{.*\}", response.replace("\n", " "))
            if json_match:
                json_str = json_match.group(0)
                logger.info(f"Extracted potential JSON: {json_str}")
                json_dict = json.loads(json_str)
                logger.info("Successfully parsed extracted JSON")
                return json_dict
        except Exception as e:
            logger.error(f"Regex extraction failed: {e}")

        # Method 3: Parse "action" and "response" fields separately
        try:
            action_match = re.search(r'"action":\s*"([^"]*)"', response)
            response_match = re.search(r'"response":\s*"([^"]*)"', response)

            if action_match and response_match:
                action = action_match.group(1)
                response_text = response_match.group(1)
                logger.info(
                    f"Extracted action: {action}, response: (truncated for log)"
                )
                return {"action": action, "response": response_text}
        except Exception as e:
            logger.error(f"Field extraction failed: {e}")

        # Method 4: Extract the response content
        try:
            if "respond_to_user" in response:
                content_match = re.search(
                    r'"response":\s*"(.*?)"(?:\s*\}|$)', response, re.DOTALL
                )
                if content_match:
                    response_content = content_match.group(1)
                else:
                    content_match = re.search(r"```(.*?)```", response, re.DOTALL)
                    if content_match:
                        response_content = content_match.group(1)
                    else:
                        parts = response.split('"response":')
                        if len(parts) > 1:
                            response_content = parts[1].strip()
                        else:
                            response_content = response

                logger.info("Created response using content extraction")
                return {
                    "action": "respond_to_user",
                    "response": response_content.strip('" \t\n}'),
                }
        except Exception as e:
            logger.error(f"Content extraction failed: {e}")

        # Method 5: Final fallback
        logger.warning("All parsing methods failed, using fallback response")
        return {
            "action": "respond_to_user",
            "response": "I processed your request but couldn't properly format the response. Here's what I found: "
            + response,
        }


class AgentProcessor:
    """Processes user queries through the agent framework."""

    def __init__(self, sse_url: str = "http://localhost:8100/sse"):
        self.sse_url = sse_url
        self.llm_client = LLMClient()
        self.prompt_generator = PromptGenerator()
        self.response_parser = ResponseParser()

    async def process_query(self, query: str, memory: List) -> Dict:
        """Process a user query using the agent framework."""
        try:
            # Connect to SSE server and create MCP session
            async with sse_client(url=self.sse_url) as (in_stream, out_stream):
                async with ClientSession(in_stream, out_stream) as session:
                    return await self._process_with_session(session, query, memory)
        except Exception as e:
            logger.error(f"Error in process_query: {e}")
            return {
                "action": "respond_to_user",
                "response": "I encountered an error processing your request. Please try again.",
            }

    async def _process_with_session(self, session, query: str, memory: List) -> Dict:
        """Process query with an active MCP session."""
        # Initialize session
        info = await session.initialize()
        logger.info(f"Connected to {info.serverInfo.name} v{info.serverInfo.version}")

        # Get available tools
        tools = await session.list_tools()
        logger.info(f"Available tools: {[t.name for t in tools.tools]}")

        # Identify tool or direct response
        tool_response = await self._identify_tool(query, tools, memory)

        # Handle direct response from LLM (no tool needed)
        if (
            "direct_response" in tool_response
            and tool_response["direct_response"] is True
        ):
            return {"action": "respond_to_user", "response": tool_response["response"]}

        # Handle tool error
        if tool_response.get("tool") == "error":
            return {
                "action": "respond_to_user",
                "response": "I'm having trouble processing your request. Please try again.",
            }

        # Call the identified tool
        tool_result = await self._call_tool(session, tool_response)

        # Process tool response
        return await self._process_response(query, tool_result, memory)

    async def _identify_tool(self, query: str, tools: Any, memory: List) -> Dict:
        """Identify which tool to use for a query or respond directly."""
        # Generate prompt for tool identification
        prompt = self.prompt_generator.identify_tool_and_arguments(query, tools, memory)
        logger.info(f"Tool identification prompt:\n{prompt}")

        # Get LLM response
        response = self.llm_client.get_completion(prompt)
        logger.info(f"LLM response for tool identification:\n{response}")

        # Parse tool call or direct response from LLM
        return self.response_parser.parse_tool_call(response)

    async def _call_tool(self, session, tool_call: Dict) -> str:
        """Call a tool with the specified arguments."""
        try:
            result = await session.call_tool(
                tool_call["tool"], arguments=tool_call["arguments"]
            )
            return result.content[0].text
        except Exception as e:
            logger.error(f"Error calling tool: {e}")
            return f"Error calling tool {tool_call['tool']}: {str(e)}"

    async def _process_response(
        self, query: str, tool_response: str, memory: List
    ) -> Dict:
        """Process a tool's response to determine next steps."""
        # Generate prompt for response processing
        prompt = self.prompt_generator.process_tool_response(
            query, tool_response, memory
        )
        logger.info(f"Response processing prompt:\n{prompt}")

        # Get LLM response
        response = self.llm_client.get_completion(prompt)
        logger.info(f"LLM response for response processing:\n{response}")

        # Parse final response
        return self.response_parser.parse_final_response(response)


class AgentChatbot:
    """Main chatbot interface using the agent framework."""

    def __init__(self):
        self.agent_processor = AgentProcessor()
        self.memory = []

    async def run(self):
        """Run the chatbot interface."""
        print("Chat Agent: Hello! How can I assist you today?")

        while True:
            user_input = input("You: ")

            # Check for exit command
            if user_input.lower() in ["exit", "bye", "close"]:
                print("Chat Agent: See you later!")
                break

            # Process user input
            try:
                # Add user input to memory
                self.memory.append(user_input)

                # Process query
                response = await self.agent_processor.process_query(
                    user_input, self.memory
                )

                # Validate response
                if not isinstance(response, dict):
                    logger.error(f"Invalid response format: {response}")
                    response = {
                        "action": "respond_to_user",
                        "response": "I encountered an error processing your request. Please try again.",
                    }

                # Add response to memory
                self.memory.append(response)

                # Handle response based on action
                if response.get("action") == "respond_to_user":
                    print(
                        "Chat Agent:", response.get("response", "No response content")
                    )
                else:
                    # Handle intermediate step
                    logger.info(
                        f"Intermediate step: {response.get('response', 'No content')}"
                    )

                    # Check if we need to continue or get more user input
                    if response.get("response"):
                        # Continue processing with the intermediate response
                        user_input = response.get("response")
                        self.memory.append(user_input)
                    else:
                        # Get more information from user
                        print("Chat Agent: I need more information to proceed.")
                        continue

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                print(
                    "Chat Agent: I encountered an error. Let's start a new conversation."
                )
                # Reset memory if there's an error
                self.memory = []


async def main():
    """Main entry point."""
    chatbot = AgentChatbot()
    await chatbot.run()


if __name__ == "__main__":
    asyncio.run(main())
