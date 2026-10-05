$ErrorActionPreference = "Stop"
$dir = Join-Path $env:LOCALAPPDATA "square"
$exe = Join-Path $dir "square.exe"

Get-Process square -ErrorAction SilentlyContinue | Stop-Process -Force
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Write-Host "Downloading square..."
Invoke-WebRequest "https://github.com/wpinrui/square/releases/latest/download/square.exe" -OutFile $exe -UseBasicParsing

$shell = New-Object -ComObject WScript.Shell
$menu = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath("Programs")) "Square.lnk"))
$menu.TargetPath = $exe
$menu.Save()

Start-Process $exe
Write-Host "Square installed. It starts hidden with Windows (toggle in the tray icon menu)."
