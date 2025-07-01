# Set execution policy for current session
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

Write-Host "🚀 LinkedIn MCP Server Installation Script" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green

function Write-Status {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if uv is installed
$uvInstalled = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvInstalled) {
    Write-Status "Installing uv package manager..."
    try {
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
        # Refresh PATH
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
        Write-Status "uv installed successfully!"
    }
    catch {
        Write-Error "Failed to install uv: $_"
        exit 1
    }
}
else {
    Write-Status "uv is already installed"
}

# Check Python version
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+\.\d+)") {
        $version = [version]$matches[1]
        $requiredVersion = [version]"3.10"
        
        if ($version -lt $requiredVersion) {
            Write-Error "Python 3.10+ is required. Found: $($matches[1])"
            Write-Error "Please install Python from https://python.org"
            exit 1
        }
        Write-Status "Python version check passed: $($matches[1])"
    }
}
catch {
    Write-Error "Python not found. Please install Python 3.10+ from https://python.org"
    exit 1
}

# Create project directory
$projectDir = "linkedin-mcp-server"
if (Test-Path $projectDir) {
    Write-Warning "Directory $projectDir already exists. Backing up..."
    $backupName = "${projectDir}_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Rename-Item $projectDir $backupName
}

Write-Status "Creating project directory: $projectDir"
New-Item -ItemType Directory -Path $projectDir -Force | Out-Null
Set-Location $projectDir

# Create virtual environment
Write-Status "Creating virtual environment..."
uv venv

# Activate virtual environment
Write-Status "Activating virtual environment..."
& ".venv\Scripts\Activate.ps1"

# Create requirements.txt
Write-Status "Creating requirements.txt..."
@"
mcp>=1.2.0
open-linkedin-api>=2.3.0
python-dotenv>=1.0.0
pydantic>=2.0.0
requests>=2.32.0
beautifulsoup4>=4.13.0
lxml>=5.3.0
"@ | Out-File -FilePath "requirements.txt" -Encoding UTF8

# Install dependencies
Write-Status "Installing Python dependencies..."
uv pip install -r requirements.txt

# Create .env.example
Write-Status "Creating environment configuration template..."
@"
# LinkedIn API Credentials
# Get these from your LinkedIn account
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password

# Optional: Debug mode (set to true for verbose logging)
DEBUG_MODE=false
"@ | Out-File -FilePath ".env.example" -Encoding UTF8

# Copy .env.example to .env
Copy-Item ".env.example" ".env"

Write-Status "Environment template created: .env"
Write-Warning "Please edit .env file with your LinkedIn credentials before running the server"

Write-Status "✅ Installation completed successfully!"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Edit .env file with your LinkedIn credentials:"
Write-Host "   notepad .env"
Write-Host ""
Write-Host "2. Copy the server code to linkedin_server.py"
Write-Host ""
Write-Host "3. Test the server:"
Write-Host "   .venv\Scripts\Activate.ps1"
Write-Host "   python linkedin_server.py"
Write-Host ""
Write-Host "4. Test with MCP inspector:"
Write-Host "   uv run mcp dev linkedin_server.py"
Write-Host ""
Write-Host "5. Integrate with Claude Desktop by updating claude_desktop_config.json"

# Display current directory
Write-Host ""
Write-Host "Project created in: $(Get-Location)"