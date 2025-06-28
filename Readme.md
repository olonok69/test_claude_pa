# PDF Document Processor MCP Server

A Model Context Protocol (MCP) server that provides tools for extracting content from PDF documents and applying custom prompts for analysis and summarization.

## Features

- **PDF Text Extraction**: Extract text content from regular PDF documents
- **OCR Support**: Extract text from scanned PDFs using Optical Character Recognition
- **Custom Prompts**: Apply predefined prompts to extracted content for analysis
- **Markdown Output**: Generate well-formatted markdown from extracted content
- **Prompt Management**: List and manage custom analysis prompts

## Installation

### Prerequisites

1. **Python 3.8+** is required
2. **Tesseract OCR** for scanned document processing:

#### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng
```

#### On macOS:
```bash
brew install tesseract tesseract-lang
```

#### On Windows:
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Setup

1. **Clone or download the server files**
2. **Place the `prompts.json` file** in the same directory as the server script
3. **Install dependencies** as shown above
4. **Test the server**:
   ```bash
   python pdf_processor_server.py
   ```

## Usage

### Available Tools

#### 1. `list_prompts()`
Lists all available prompts with their IDs, names, and keywords.

#### 2. `extract_pdf_to_markdown(pdf_base64, filename)`
Extracts text content from a PDF and converts it to markdown format.
- `pdf_base64`: Base64 encoded PDF file content
- `filename`: Original filename (optional)

#### 3. `extract_scanned_pdf_to_markdown(pdf_base64, filename)`
Extracts text from scanned PDFs using OCR and converts to markdown.
- `pdf_base64`: Base64 encoded PDF file content
- `filename`: Original filename (optional)

#### 4. `get_prompt_by_id(prompt_id)`
Retrieves a specific prompt by its ID.
- `prompt_id`: The ID of the prompt to retrieve

#### 5. `apply_prompt_to_content(content, prompt_id)`
Applies a specific prompt to extracted content for analysis.
- `content`: The extracted content
- `prompt_id`: The ID of the prompt to apply

#### 6. `process_pdf_with_prompt(pdf_base64, prompt_id, filename, use_ocr)`
Complete workflow: extracts PDF content and applies a prompt.
- `pdf_base64`: Base64 encoded PDF file content
- `prompt_id`: The ID of the prompt to apply
- `filename`: Original filename (optional)
- `use_ocr`: Whether to use OCR for scanned documents

### Integration with Claude Desktop

Add this server to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "pdf-processor": {
      "command": "python",
      "args": ["/path/to/pdf_processor_server.py"],
      "env": {}
    }
  }
}
```

## Prompts Configuration

The server uses a `prompts.json` file containing an array of prompt objects. Each prompt should have:

```json
{
  "id": "unique-identifier",
  "name_prompt": "Human readable name",
  "prompt": "The actual prompt instructions...",
  "keywords": "comma,separated,keywords"
}
```

### Example prompts.json structure:
```json
[
  {
    "id": "638f3f81-0082-4df9-929f-e7b120d4f954",
    "name_prompt": "Medical Report Summary",
    "prompt": "Summarize the medical information in this document...",
    "keywords": "medical,summary,health"
  }
]
```

## Example Workflow

1. **Upload a PDF document** (converted to base64)
2. **List available prompts** to see analysis options
3. **Process the PDF** with a specific prompt:
   ```python
   # Example using the complete workflow
   result = await process_pdf_with_prompt(
       pdf_base64="<base64_content>",
       prompt_id="638f3f81-0082-4df9-929f-e7b120d4f954",
       filename="medical_report.pdf",
       use_ocr=False
   )
   ```

## Troubleshooting

### Common Issues

1. **Tesseract not found**: Ensure Tesseract OCR is properly installed and in your PATH
2. **PDF processing errors**: Check that the PDF file is not corrupted or password-protected
3. **Memory issues with large PDFs**: Consider processing large documents in smaller chunks

### Logging

The server provides detailed logging. Check the console output for error messages and processing status.

## Dependencies

- `mcp[cli]>=1.2.0` - Model Context Protocol framework
- `PyMuPDF>=1.23.0` - PDF text extraction
- `pytesseract>=0.3.10` - OCR functionality
- `Pillow>=10.0.0` - Image processing
- `opencv-python>=4.8.0` - Optional image preprocessing

## License

This project is open source. Please check the license file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the MCP documentation at https://modelcontextprotocol.io
3. Open an issue in the repository