#!/usr/bin/env python3
"""
PDF Document Processor MCP Server

This server provides tools to:
1. Extract content from PDF documents to markdown
2. Apply custom prompts to extracted content for analysis/summarization
3. List available prompts
"""

import json
import os
import tempfile
import base64
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio
import logging

# MCP imports
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, ImageContent, EmbeddedResource

# PDF processing imports
import fitz  # PyMuPDF for regular PDFs
import pytesseract
from PIL import Image
import io

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("PDF Document Processor")

# Global variables
PROMPTS_FILE = "prompts.json"
prompts_data: List[Dict[str, str]] = []

def load_prompts():
    """Load prompts from JSON file"""
    global prompts_data
    try:
        if os.path.exists(PROMPTS_FILE):
            with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                prompts_data = json.load(f)
            logger.info(f"Loaded {len(prompts_data)} prompts from {PROMPTS_FILE}")
        else:
            logger.warning(f"Prompts file {PROMPTS_FILE} not found")
            prompts_data = []
    except Exception as e:
        logger.error(f"Error loading prompts: {e}")
        prompts_data = []

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using PyMuPDF"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            
            if page_text.strip():
                text += f"\n\n## Page {page_num + 1}\n\n"
                text += page_text
            else:
                # If no text found, page might be scanned - extract as image
                logger.info(f"No text found on page {page_num + 1}, treating as scanned")
                ocr_text = extract_text_from_scanned_page(page)
                if ocr_text.strip():
                    text += f"\n\n## Page {page_num + 1} (OCR)\n\n"
                    text += ocr_text
        
        doc.close()
        return text.strip()
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise

def extract_text_from_scanned_page(page) -> str:
    """Extract text from a scanned PDF page using OCR"""
    try:
        # Convert page to image
        pix = page.get_pixmap()
        img_data = pix.tobytes("png")
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(img_data))
        
        # Perform OCR
        text = pytesseract.image_to_string(image, lang='spa+eng')  # Spanish and English
        return text
        
    except Exception as e:
        logger.error(f"Error performing OCR: {e}")
        return ""

def extract_text_from_scanned_pdf(pdf_path: str) -> str:
    """Extract text from completely scanned PDF using OCR"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = extract_text_from_scanned_page(page)
            
            if page_text.strip():
                text += f"\n\n## Page {page_num + 1} (OCR)\n\n"
                text += page_text
        
        doc.close()
        return text.strip()
        
    except Exception as e:
        logger.error(f"Error extracting text from scanned PDF: {e}")
        raise

def convert_to_markdown(text: str) -> str:
    """Convert extracted text to markdown format"""
    if not text.strip():
        return "# Document\n\nNo text content could be extracted from this document."
    
    # Basic markdown formatting
    markdown = f"# Extracted Document Content\n\n{text}"
    
    # Clean up extra whitespace
    lines = markdown.split('\n')
    cleaned_lines = []
    
    for line in lines:
        cleaned_line = line.strip()
        if cleaned_line or (cleaned_lines and cleaned_lines[-1].strip()):
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

@mcp.tool()
async def list_prompts() -> str:
    """List all available prompts with their IDs, names, and keywords"""
    if not prompts_data:
        return "No prompts available. Please ensure prompts.json file is present."
    
    result = "# Available Prompts\n\n"
    
    for i, prompt in enumerate(prompts_data, 1):
        result += f"## {i}. {prompt.get('name_prompt', 'Unnamed Prompt')}\n\n"
        result += f"**ID:** `{prompt.get('id', 'N/A')}`\n\n"
        result += f"**Keywords:** {prompt.get('keywords', 'N/A')}\n\n"
        
        # Show first 200 characters of the prompt
        prompt_text = prompt.get('prompt', '')
        if len(prompt_text) > 200:
            prompt_preview = prompt_text[:200] + "..."
        else:
            prompt_preview = prompt_text
        
        result += f"**Preview:** {prompt_preview}\n\n"
        result += "---\n\n"
    
    return result

@mcp.tool()
async def extract_pdf_to_markdown(
    pdf_base64: str,
    filename: str = "document.pdf"
) -> str:
    """
    Extract content from a PDF file and convert to markdown format.
    
    Args:
        pdf_base64: Base64 encoded PDF file content
        filename: Original filename of the PDF (optional)
    
    Returns:
        Extracted content in markdown format
    """
    try:
        # Decode base64 content
        pdf_data = base64.b64decode(pdf_base64)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_data)
            temp_path = temp_file.name
        
        try:
            # Extract text from PDF
            extracted_text = extract_text_from_pdf(temp_path)
            
            # Convert to markdown
            markdown_content = convert_to_markdown(extracted_text)
            
            # Add metadata
            result = f"# Document: {filename}\n\n"
            result += f"**Extraction Date:** {asyncio.get_event_loop().time()}\n\n"
            result += markdown_content
            
            return result
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        return f"Error processing PDF: {str(e)}"

@mcp.tool()
async def extract_scanned_pdf_to_markdown(
    pdf_base64: str,
    filename: str = "document.pdf"
) -> str:
    """
    Extract content from a scanned PDF file using OCR and convert to markdown format.
    
    Args:
        pdf_base64: Base64 encoded PDF file content
        filename: Original filename of the PDF (optional)
    
    Returns:
        Extracted content in markdown format using OCR
    """
    try:
        # Decode base64 content
        pdf_data = base64.b64decode(pdf_base64)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_data)
            temp_path = temp_file.name
        
        try:
            # Extract text from scanned PDF using OCR
            extracted_text = extract_text_from_scanned_pdf(temp_path)
            
            # Convert to markdown
            markdown_content = convert_to_markdown(extracted_text)
            
            # Add metadata
            result = f"# Scanned Document: {filename}\n\n"
            result += f"**Extraction Method:** OCR (Optical Character Recognition)\n\n"
            result += f"**Extraction Date:** {asyncio.get_event_loop().time()}\n\n"
            result += markdown_content
            
            return result
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Error processing scanned PDF: {e}")
        return f"Error processing scanned PDF: {str(e)}"

@mcp.tool()
async def get_prompt_by_id(prompt_id: str) -> str:
    """
    Get a specific prompt by its ID.
    
    Args:
        prompt_id: The ID of the prompt to retrieve
    
    Returns:
        The prompt details in markdown format
    """
    if not prompts_data:
        return "No prompts available. Please ensure prompts.json file is present."
    
    for prompt in prompts_data:
        if prompt.get('id') == prompt_id:
            result = f"# {prompt.get('name_prompt', 'Unnamed Prompt')}\n\n"
            result += f"**ID:** `{prompt.get('id', 'N/A')}`\n\n"
            result += f"**Keywords:** {prompt.get('keywords', 'N/A')}\n\n"
            result += f"## Prompt Content\n\n{prompt.get('prompt', 'No content available')}\n\n"
            return result
    
    return f"Prompt with ID '{prompt_id}' not found."

@mcp.tool()
async def apply_prompt_to_content(
    content: str,
    prompt_id: str
) -> str:
    """
    Apply a specific prompt to extracted content for analysis/summarization.
    
    Args:
        content: The extracted content (usually from PDF extraction)
        prompt_id: The ID of the prompt to apply
    
    Returns:
        Instructions for applying the prompt to the content
    """
    if not prompts_data:
        return "No prompts available. Please ensure prompts.json file is present."
    
    # Find the prompt
    selected_prompt = None
    for prompt in prompts_data:
        if prompt.get('id') == prompt_id:
            selected_prompt = prompt
            break
    
    if not selected_prompt:
        return f"Prompt with ID '{prompt_id}' not found."
    
    # Create the instruction for the LLM
    result = f"# Analysis Request\n\n"
    result += f"## Selected Prompt: {selected_prompt.get('name_prompt', 'Unnamed Prompt')}\n\n"
    result += f"**Keywords:** {selected_prompt.get('keywords', 'N/A')}\n\n"
    result += f"## Instructions\n\n"
    result += f"{selected_prompt.get('prompt', 'No instructions available')}\n\n"
    result += f"## Content to Analyze\n\n"
    result += f"```\n{content}\n```\n\n"
    result += f"---\n\n"
    result += f"**Note:** Please apply the above instructions to analyze the provided content and generate your response accordingly.\n"
    
    return result

@mcp.tool()
async def process_pdf_with_prompt(
    pdf_base64: str,
    prompt_id: str,
    filename: str = "document.pdf",
    use_ocr: bool = False
) -> str:
    """
    Complete workflow: Extract PDF content and apply a prompt for analysis.
    
    Args:
        pdf_base64: Base64 encoded PDF file content
        prompt_id: The ID of the prompt to apply
        filename: Original filename of the PDF (optional)
        use_ocr: Whether to use OCR for scanned documents (default: False)
    
    Returns:
        Combined extraction and prompt application results
    """
    try:
        # Step 1: Extract content from PDF
        if use_ocr:
            extracted_content = await extract_scanned_pdf_to_markdown(pdf_base64, filename)
        else:
            extracted_content = await extract_pdf_to_markdown(pdf_base64, filename)
        
        # Step 2: Apply prompt to extracted content
        prompt_result = await apply_prompt_to_content(extracted_content, prompt_id)
        
        # Combine results
        result = f"# Complete PDF Processing Results\n\n"
        result += f"## Step 1: PDF Extraction\n\n"
        result += extracted_content + "\n\n"
        result += f"## Step 2: Prompt Application\n\n"
        result += prompt_result
        
        return result
        
    except Exception as e:
        logger.error(f"Error in complete PDF processing: {e}")
        return f"Error in complete PDF processing: {str(e)}"

# Load prompts when the server starts
load_prompts()

if __name__ == "__main__":
    # Run the server
    mcp.run()