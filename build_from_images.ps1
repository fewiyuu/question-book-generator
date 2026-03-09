param(
    [string]$ImageDir = "images",
    [int]$Start = 1,
    [ValidateSet("time", "name")]
    [string]$Sort = "time",
    [switch]$UseFilenameNumber,
    [switch]$Crop
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$texFile = "main.tex"
$scriptFile = Join-Path $root "generate_questions.py"

Set-Location $root
$pythonArgs = @(
    $scriptFile,
    "--image-dir", $ImageDir,
    "--start", $Start.ToString(),
    "--sort", $Sort
)

if ($UseFilenameNumber) {
    $pythonArgs += "--use-filename-number"
}

if (-not $Crop) {
    $pythonArgs += "--no-crop"
}

& python @pythonArgs
& xelatex "-interaction=nonstopmode" "-halt-on-error" $texFile

$cleanupFiles = @(
    "main.aux",
    "main.log",
    "做题本模板A4一页一题.aux",
    "做题本模板A4一页一题.log",
    "做题本模板A4一页一题.bbl"
)

foreach ($file in $cleanupFiles) {
    if (Test-Path $file) {
        Remove-Item $file -Force
    }
}
