# PowerShell installation script for PDF Document Processor MCP Server on Windows using uv

param(
    [switch]$SkipTesseract,
    [string]$InstallPath = ".",
    [switch]$Help
)

if ($Help) {
    Write-Host @"
PDF Document Processor MCP Server - Windows Installation Script

USAGE:
    .\install_windows_uv.ps1 [OPTIONS]

OPTIONS:
    -SkipTesseract    Skip Tesseract OCR installation
    -InstallPath      Installation directory (default: current directory)
    -Help             Show this help message

EXAMPLES:
    .\install_windows_uv.ps1
    .\install_windows_uv.ps1 -SkipTesseract
    .\install_windows_uv.ps1 -InstallPath "C:\MCP\PDFProcessor"

"@
    exit 0
}

Write-Host "🚀 Installing PDF Document Processor MCP Server on Windows..." -ForegroundColor Green
Write-Host "📁 Installation path: $InstallPath" -ForegroundColor Cyan

# Set execution policy for current session
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Function to check if a command exists
function Test-Command {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Function to download and install uv
function Install-UV {
    Write-Host "📦 Installing uv..." -ForegroundColor Yellow
    
    try {
        # Download and install uv using the official installer
        Invoke-RestMethod -Uri "https://astral.sh/uv/install.ps1" | Invoke-Expression
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        # Verify installation
        if (Test-Command "uv") {
            $uvVersion = uv --version
            Write-Host "✅ uv installed successfully: $uvVersion" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ uv installation failed" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Error installing uv: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to install Tesseract OCR
function Install-Tesseract {
    Write-Host "👁️ Installing Tesseract OCR..." -ForegroundColor Yellow
    
    # Check if Tesseract is already installed
    if (Test-Command "tesseract") {
        $tesseractVersion = tesseract --version 2>&1 | Select-Object -First 1
        Write-Host "✅ Tesseract already installed: $tesseractVersion" -ForegroundColor Green
        return $true
    }
    
    # Check if Chocolatey is available
    if (Test-Command "choco") {
        Write-Host "📦 Installing Tesseract via Chocolatey..." -ForegroundColor Cyan
        try {
            choco install tesseract -y
            # Refresh environment variables
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            
            if (Test-Command "tesseract") {
                Write-Host "✅ Tesseract installed successfully via Chocolatey" -ForegroundColor Green
                return $true
            }
        } catch {
            Write-Host "⚠️ Chocolatey installation failed, trying manual installation..." -ForegroundColor Yellow
        }
    }
    
    # Manual installation instructions
    Write-Host @"
⚠️ Automatic Tesseract installation not available.

Please install Tesseract OCR manually:

1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer as Administrator
3. During installation, make sure to:
   - Install additional language packs (Spanish and English)
   - Add Tesseract to PATH
4. Restart PowerShell after installation

Alternatively, install Chocolatey first:
    Set-ExecutionPolicy Bypass -Scope Process -Force
    iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

Then run this script again.
"@ -ForegroundColor Yellow
    
    $response = Read-Host "Continue without Tesseract? OCR functionality will not work. (y/N)"
    return $response -eq "y" -or $response -eq "Y"
}

# Main installation process
try {
    # Create installation directory
    if (!(Test-Path $InstallPath)) {
        New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
        Write-Host "📁 Created installation directory: $InstallPath" -ForegroundColor Cyan
    }
    
    Set-Location $InstallPath
    
    # Step 1: Check and install uv
    Write-Host "`n🔧 Step 1: Checking uv installation..." -ForegroundColor Cyan
    if (!(Test-Command "uv")) {
        if (!(Install-UV)) {
            throw "Failed to install uv"
        }
    } else {
        $uvVersion = uv --version
        Write-Host "✅ uv already installed: $uvVersion" -ForegroundColor Green
    }
    
    # Step 2: Install Tesseract OCR
    if (!$SkipTesseract) {
        Write-Host "`n🔧 Step 2: Installing Tesseract OCR..." -ForegroundColor Cyan
        if (!(Install-Tesseract)) {
            Write-Host "⚠️ Continuing without Tesseract. OCR functionality will be limited." -ForegroundColor Yellow
        }
    } else {
        Write-Host "`n⏭️ Step 2: Skipping Tesseract installation as requested" -ForegroundColor Yellow
    }
    
    # Step 3: Initialize Python project with uv
    Write-Host "`n🔧 Step 3: Initializing Python project..." -ForegroundColor Cyan
    
    # Initialize uv project with --no-workspace to avoid conflicts
    uv init pdf-processor-mcp --no-readme --no-workspace
    Set-Location "pdf-processor-mcp"
    
    # Step 4: Install dependencies
    Write-Host "`n🔧 Step 4: Installing Python dependencies..." -ForegroundColor Cyan
    
    # Add dependencies using uv
    uv add "mcp[cli]>=1.2.0"
    uv add "PyMuPDF>=1.23.0"
    uv add "pytesseract>=0.3.10"
    uv add "Pillow>=10.0.0"
    uv add "opencv-python>=4.8.0"
    
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
    
    # Step 5: Download server files
    Write-Host "`n🔧 Step 5: Setting up server files..." -ForegroundColor Cyan
    
    # Create server files (you'll need to copy these manually or download them)
    Write-Host @"
📋 Next steps:

1. Copy the following files to this directory:
   - pdf_processor_server.py
   - prompts.json

2. Test the installation:
   uv run python pdf_processor_server.py

3. For Claude Desktop integration, add this to your configuration:
   {
     "mcpServers": {
       "pdf-processor": {
         "command": "uv",
         "args": ["run", "python", "$((Get-Location).Path)\pdf_processor_server.py"]
       }
     }
   }

"@ -ForegroundColor Cyan
    
    Write-Host "✅ Installation completed successfully!" -ForegroundColor Green
    Write-Host "📁 Project directory: $(Get-Location)" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Installation failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please check the error messages above and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "`n🎉 Installation complete! Don't forget to copy the server files." -ForegroundColor Green