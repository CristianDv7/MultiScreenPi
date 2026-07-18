# Instalador del agente de escritorio de MultiScreenPi para Windows.
#
# Uso (en PowerShell, parado en esta carpeta o desde cualquier lado):
#   powershell -ExecutionPolicy Bypass -File install.ps1
#
# Es seguro correrlo varias veces: no pisa agent_config.json si ya existe.

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== MultiScreenPi: instalando agente de escritorio ==="
Write-Host "Carpeta: $scriptDir"

Write-Host ""
Write-Host "--- 1/3: Dependencias de Python (pycaw, comtypes) ---"
python -m pip install --user pycaw comtypes

Write-Host ""
Write-Host "--- 2/3: Archivo de configuracion ---"
$configPath = Join-Path $scriptDir "agent_config.json"
$examplePath = Join-Path $scriptDir "agent_config.example.json"
if (-not (Test-Path $configPath)) {
    Copy-Item $examplePath $configPath
    Write-Host "Se creo agent_config.json a partir del ejemplo."
    Write-Host "IMPORTANTE: editalo con tu token y las rutas de tus apps antes de usarlo:"
    Write-Host "  notepad `"$configPath`""
} else {
    Write-Host "agent_config.json ya existe, no se toca."
}

Write-Host ""
Write-Host "--- 3/3: Autoarranque con Windows ---"
$pythonwPath = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $pythonwPath) {
    $pythonwPath = "pythonw.exe"
    Write-Host "No se encontro pythonw.exe en el PATH, se usara 'pythonw.exe' a secas (puede fallar si no esta en el PATH del inicio de sesion)."
}

$agentPath = Join-Path $scriptDir "agent.py"
$startupDir = [Environment]::GetFolderPath("Startup")
$vbsPath = Join-Path $startupDir "MultiScreenPi-Agent.vbs"

$vbsContent = "Set WshShell = CreateObject(`"WScript.Shell`")`r`nWshShell.Run `"$pythonwPath `"`"$agentPath`"`"`", 0, False"
Set-Content -Path $vbsPath -Value $vbsContent -Encoding ASCII

Write-Host "Lanzador instalado en: $vbsPath"
Write-Host "El agente arrancara solo (sin ventana) la proxima vez que inicies sesion en Windows."

Write-Host ""
Write-Host "=== Listo ==="
Write-Host "1. Edita agent_config.json con tu token y tus apps (si no lo hiciste ya)."
Write-Host "2. Arranca el agente ahora mismo para probarlo:"
Write-Host "     python `"$agentPath`""
Write-Host "3. Copia la URL (http://TU_IP:5566) y el token en el panel web de la Pi, seccion Secretos > Mi PC."
