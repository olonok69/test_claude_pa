# PDF Document Processor MCP Server - Windows Installation with UV

Complete guide for installing the PDF Document Processor MCP Server on Windows using UV.

## 🚀 Quick Installation

### Option 1: PowerShell Script (Recommended)

1. **Open PowerShell as Administrator**
2. **Run the installation script:**
   ```powershell
   .\install_windows_uv.ps1
   ```

### Option 2: Batch Script

1. **Open Command Prompt as Administrator**
2. **Run the batch installer:**
   ```cmd
   install_windows_uv.bat
   ```

### Option 3: Manual Installation

Follow the step-by-step guide below.

## 📋 Prerequisites

- **Windows 10/11** or Windows Server 2019+
- **PowerShell 5.1+** or **Command Prompt**
- **Internet connection** for downloading dependencies
- **Administrator privileges** (recommended)

## 🔧 Step-by-Step Manual Installation

### Step 1: Install UV

UV is a fast Python package installer and resolver.

**Using PowerShell:**
```powershell
# Install uv
Invoke-RestMethod -Uri "https://astral.sh/uv/install.ps1" | Invoke-Expression

# Verify installation
uv --version
```

**Using Command Prompt:**
```cmd
# Download and run installer
powershell -c "Invoke-RestMethod -Uri 'https://astral.sh/uv/install.ps1' | Invoke-Expression"

# Verify installation (restart cmd first)
uv --version
```

**Alternative - Manual Download:**
1. Download from: https://github.com/astral-sh/uv/releases
2. Extract to a folder (e.g., `C:\uv`)
3. Add to PATH: `C:\uv\bin`

### Step 2: Install Tesseract OCR (Optional but Recommended)

Tesseract is required for OCR functionality (scanned PDFs).

**Option A - Chocolatey (if available):**
```powershell
# Install Chocolatey if not installed
Set-ExecutionPolicy Bypass -Scope Process -Force
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Install Tesseract
choco install tesseract -y
```

**Option B - Manual Installation:**
1. **Download:** https://github.com/UB-Mannheim/tesseract/wiki
2. **Run installer as Administrator**
3. **During installation:**
   - ✅ Check "Add to PATH"
   - ✅ Install Spanish language pack
   - ✅ Install English language pack
4. **Restart PowerShell/Command Prompt**
5. **Verify:** `tesseract --version`

**Option C - Winget (Windows 11):**
```cmd
winget install --id UB-Mannheim.TesseractOCR
```

### Step 3: Create Project

**Using PowerShell/Command Prompt:**
```cmd
# Create and navigate to project directory
uv init pdf-processor-mcp --no-readme
cd pdf-processor-mcp
```

### Step 4: Install Python Dependencies

```cmd
# Install all required dependencies
uv add "mcp[cli]>=1.2.0"
uv add "PyMuPDF>=1.23.0"
uv add "pytesseract>=0.3.10"
uv add "Pillow>=10.0.0"
uv add "opencv-python>=4.8.0"
```

### Step 5: Setup Server Files

1. **Copy server files** to the project directory:
   - `pdf_processor_server.py`
   - `prompts.json`

2. **Test the installation:**
   ```cmd
   uv run python pdf_processor_server.py
   ```

## 🔌 Claude Desktop Integration

### Configuration File Location

The Claude Desktop configuration file is located at:
```
%APPDATA%\Claude\claude_desktop_config.json
```

To open this location:
1. Press `Win + R`
2. Type: `%APPDATA%\Claude`
3. Press Enter

### Configuration Content

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pdf-processor": {
      "command": "uv",
      "args": [
        "run", 
        "python", 
        "C:\\path\\to\\your\\pdf-processor-mcp\\pdf_processor_server.py"
      ],
      "cwd": "C:\\path\\to\\your\\pdf-processor-mcp",
      "env": {
        "TESSDATA_PREFIX": "C:\\Program Files\\Tesseract-OCR\\tessdata"
      }
    }
  }
}
```

**Replace `C:\\path\\to\\your\\pdf-processor-mcp`** with your actual project path.

### Finding Your Project Path

```cmd
# In your project directory, run:
echo %CD%
```

## 🧪 Testing the Installation

### Quick Test

```cmd
# In your project directory
uv run python -c "import mcp; import fitz; import pytesseract; print('All dependencies imported successfully!')"
```

### Full Test

```cmd
# Run the test client
uv run python test_client.py
```

### Tesseract Test

```cmd
# Test Tesseract installation
tesseract --version
```

## 🔧 Troubleshooting

### Common Issues

#### 1. UV not found after installation
**Solution:**
- Restart PowerShell/Command Prompt
- Or manually add to PATH: `%USERPROFILE%\.cargo\bin`

#### 2. Tesseract not found
**Solutions:**
- Ensure Tesseract is in PATH
- Set environment variable: `TESSDATA_PREFIX=C:\Program Files\Tesseract-OCR\tessdata`
- Reinstall with "Add to PATH" option checked

#### 3. Permission errors
**Solutions:**
- Run as Administrator
- Check antivirus software
- Use different installation directory

#### 4. SSL/Certificate errors
**Solutions:**
```cmd
# Trust Python certificates
uv pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --upgrade pip
```

#### 5. Import errors
**Solutions:**
```cmd
# Reinstall problematic package
uv remove package-name
uv add "package-name>=version"
```

### Environment Variables

If needed, set these environment variables:

```cmd
# PowerShell
$env:TESSDATA_PREFIX = "C:\Program Files\Tesseract-OCR\tessdata"
$env:PYTHONPATH = "C:\path\to\your\pdf-processor-mcp"

# Command Prompt
set TESSDATA_PREFIX=C:\Program Files\Tesseract-OCR\tessdata
set PYTHONPATH=C:\path\to\your\pdf-processor-mcp
```

### Antivirus Issues

Some antivirus software may block UV or Python installations:

1. **Temporarily disable real-time protection**
2. **Add exceptions for:**
   - UV installation directory
   - Project directory
   - Python executables

## 📁 Directory Structure

After installation, your project should look like:

```
pdf-processor-mcp/
├── .python-version
├── pyproject.toml
├── uv.lock
├── pdf_processor_server.py    # ← Copy this file
├── prompts.json              # ← Copy this file
├── test_client.py            # ← Optional test file
└── README.md
```

## 🚀 Usage

Once installed and configured:

1. **Start Claude Desktop**
2. **Look for the hammer icon** (🔨) - indicates MCP tools are available
3. **Available tools:**
   - List prompts
   - Extract PDF to markdown
   - Extract scanned PDF to markdown
   - Apply prompts to content
   - Complete PDF processing workflow

## 📞 Support

### Getting Help

1. **Check this troubleshooting section**
2. **Review UV documentation:** https://docs.astral.sh/uv/
3. **Check MCP documentation:** https://modelcontextprotocol.io/
4. **Verify Tesseract installation:** https://github.com/UB-Mannheim/tesseract/wiki

### System Information

When reporting issues, include:

```cmd
# Get system info
systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type"
python --version
uv --version
tesseract --version
```

## 🎯 Performance Tips

1. **Use SSD storage** for better performance
2. **Ensure adequate RAM** (8GB+ recommended)
3. **Close unnecessary applications** during installation
4. **Use latest Windows updates**
5. **Keep UV and dependencies updated:**
   ```cmd
   # Update UV
   uv self update
   
   # Update dependencies
   uv lock --upgrade
   ```

## 🔄 Updating

To update the server:

```cmd
# Update UV itself
uv self update

# Update dependencies
cd pdf-processor-mcp
uv lock --upgrade
uv sync

# Update server files (copy new versions)
# Copy updated pdf_processor_server.py and prompts.json
```