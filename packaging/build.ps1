# Build script for GDrive Tools GUI application (Windows)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

Write-Host "Building GDrive Tools GUI application..."
Write-Host "Project directory: $ProjectDir"

Set-Location $ProjectDir

# Install dependencies
Write-Host "Installing dependencies..."
pip install -e .
pip install pyinstaller

# Run PyInstaller
Write-Host "Running PyInstaller..."
pyinstaller packaging\gdrive-gui.spec --clean --distpath dist\

# Show result
Write-Host ""
Write-Host "Build complete!"

$ExePath = Join-Path $ProjectDir "dist\GDrive Tools.exe"
if (Test-Path $ExePath) {
    $FileSize = (Get-Item $ExePath).Length / 1MB
    Write-Host ("Executable: {0}" -f $ExePath)
    Write-Host ("Size: {0:N2} MB" -f $FileSize)
    Write-Host ""
    Write-Host "To run: double-click the executable or run from command line"
}
