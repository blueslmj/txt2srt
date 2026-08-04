[CmdletBinding()]
param(
    [ValidateSet("auto", "cpu", "nvidia-modern", "nvidia-legacy")]
    [string]$Profile = "auto",

    [string]$VenvPath = "venv",

    [switch]$ForceRecreate,
    [switch]$InstallCudaToolkit,
    [switch]$NonInteractive,
    [switch]$SkipRuntimeCheck,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$ProjectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path))
$VenvFullPath = [IO.Path]::GetFullPath((Join-Path $ProjectRoot $VenvPath))
$ProjectPrefix = $ProjectRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
$TorchVersion = "2.11.0"
$ModelsRoot = Join-Path $ProjectRoot "models"
$RuntimeRoot = Join-Path $ProjectRoot ".runtime"
$TempRoot = Join-Path $RuntimeRoot "temp"

if (-not $VenvFullPath.StartsWith($ProjectPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "The virtual environment must be inside the project: $VenvFullPath"
}

Set-Location $ProjectRoot

function Initialize-ProjectStorage {
    $directories = @(
        $ModelsRoot,
        (Join-Path $ModelsRoot "faster-whisper"),
        (Join-Path $ModelsRoot "openai-whisper"),
        (Join-Path $ModelsRoot "huggingface"),
        (Join-Path $ModelsRoot "torch"),
        $RuntimeRoot,
        $TempRoot,
        (Join-Path $RuntimeRoot "gradio")
    )
    foreach ($directory in $directories) {
        [void](New-Item -ItemType Directory -Path $directory -Force)
    }

    $env:TXT2SRT_PROJECT_ROOT = $ProjectRoot
    $env:TXT2SRT_MODELS_DIR = $ModelsRoot
    $env:TXT2SRT_WHISPER_DOWNLOAD_ROOT = Join-Path $ModelsRoot "openai-whisper"
    $env:HF_HOME = Join-Path $ModelsRoot "huggingface"
    $env:HF_HUB_CACHE = Join-Path $ModelsRoot "faster-whisper"
    $env:HUGGINGFACE_HUB_CACHE = $env:HF_HUB_CACHE
    $env:HF_ASSETS_CACHE = Join-Path $ModelsRoot "huggingface-assets"
    $env:HF_XET_CACHE = Join-Path $ModelsRoot "huggingface-xet"
    $env:TORCH_HOME = Join-Path $ModelsRoot "torch"
    $env:XDG_CACHE_HOME = Join-Path $ModelsRoot "misc"
    $env:GRADIO_TEMP_DIR = Join-Path $RuntimeRoot "gradio"
    $env:NUMBA_CACHE_DIR = Join-Path $RuntimeRoot "numba"
    $env:MPLCONFIGDIR = Join-Path $RuntimeRoot "matplotlib"
    $env:CUDA_CACHE_PATH = Join-Path $RuntimeRoot "nvidia"
    $env:TRITON_CACHE_DIR = Join-Path $RuntimeRoot "triton"
    $env:TORCHINDUCTOR_CACHE_DIR = Join-Path $RuntimeRoot "torchinductor"
    $env:TEMP = $TempRoot
    $env:TMP = $TempRoot
    $env:PIP_NO_CACHE_DIR = "1"
    $env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
}

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Write-Info([string]$Message) {
    Write-Host "    $Message" -ForegroundColor DarkGray
}

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter()][string[]]$Arguments = @()
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE`: $FilePath $($Arguments -join ' ')"
    }
}

function Find-Python312 {
    $launcher = Get-Command "py.exe" -ErrorAction SilentlyContinue
    if ($launcher) {
        $candidate = & $launcher.Source -3.12 -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $candidate) {
            $resolved = $candidate.Trim()
            if (Test-Path -LiteralPath $resolved) {
                return $resolved
            }
        }
    }

    $python = Get-Command "python.exe" -ErrorAction SilentlyContinue
    if ($python) {
        $version = & $python.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($LASTEXITCODE -eq 0 -and $version.Trim() -eq "3.12") {
            return $python.Source
        }
    }
    return $null
}

function Ensure-Python312 {
    $python = Find-Python312
    if ($python) {
        return $python
    }

    if ($DryRun) {
        Write-Info "Python 3.12 was not found. A normal run will install it with winget."
        return "py -3.12"
    }

    $winget = Get-Command "winget.exe" -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "Python 3.12 and winget were not found. Install Python 3.12 from https://www.python.org/downloads/."
    }

    Write-Step "Install Python 3.12 for the current user"
    Invoke-Native $winget.Source @(
        "install", "--id", "Python.Python.3.12", "--exact", "--scope", "user",
        "--silent", "--accept-package-agreements", "--accept-source-agreements",
        "--disable-interactivity"
    )

    $python = Find-Python312
    if (-not $python) {
        throw "Python 3.12 was installed but is not visible yet. Close this window and run setup.bat again."
    }
    return $python
}

function Get-NvidiaGpu {
    $nvidiaSmi = Get-Command "nvidia-smi.exe" -ErrorAction SilentlyContinue
    if (-not $nvidiaSmi) {
        return $null
    }

    $lines = & $nvidiaSmi.Source --query-gpu=name,compute_cap,driver_version --format=csv,noheader 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $lines) {
        return $null
    }

    $bestGpu = $null
    foreach ($line in @($lines)) {
        $parts = $line -split ","
        if ($parts.Count -lt 3) {
            continue
        }

        $capability = 0.0
        [void][double]::TryParse(
            $parts[1].Trim(),
            [Globalization.NumberStyles]::Float,
            [Globalization.CultureInfo]::InvariantCulture,
            [ref]$capability
        )
        $gpu = [pscustomobject]@{
            Name = $parts[0].Trim()
            Capability = $capability
            Driver = $parts[2].Trim()
        }
        if ($null -eq $bestGpu -or $gpu.Capability -gt $bestGpu.Capability) {
            $bestGpu = $gpu
        }
    }
    return $bestGpu
}

function Select-HardwareProfile([string]$RequestedProfile, $Gpu) {
    if ($RequestedProfile -ne "auto") {
        return $RequestedProfile
    }
    if ($null -eq $Gpu -or $Gpu.Capability -lt 5.0) {
        return "cpu"
    }
    if ($Gpu.Capability -ge 12.0) {
        return "nvidia-modern"
    }
    return "nvidia-legacy"
}

function Find-Cuda12Cublas {
    $whereOutput = & where.exe cublas64_12.dll 2>$null
    if ($LASTEXITCODE -eq 0 -and $whereOutput) {
        return @($whereOutput)[0]
    }

    foreach ($variable in Get-ChildItem Env: | Where-Object { $_.Name -like "CUDA_PATH_V12*" }) {
        $candidate = Join-Path $variable.Value "bin\cublas64_12.dll"
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    $cudaRoot = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA"
    if (Test-Path -LiteralPath $cudaRoot) {
        $candidate = Get-ChildItem -LiteralPath $cudaRoot -Directory -Filter "v12.*" |
            Sort-Object Name -Descending |
            ForEach-Object { Join-Path $_.FullName "bin\cublas64_12.dll" } |
            Where-Object { Test-Path -LiteralPath $_ } |
            Select-Object -First 1
        if ($candidate) {
            return $candidate
        }
    }
    return $null
}

function Add-Cuda12ToCurrentPath([string]$CublasPath) {
    if (-not $CublasPath) {
        return
    }
    $cudaBin = Split-Path -Parent $CublasPath
    if (($env:PATH -split ";") -notcontains $cudaBin) {
        $env:PATH = "$cudaBin;$env:PATH"
    }
}

function Ensure-BlackwellCudaRuntime {
    $cublas = Find-Cuda12Cublas
    if ($cublas) {
        Add-Cuda12ToCurrentPath $cublas
        Write-Info "Found the CUDA 12 cuBLAS runtime required by CTranslate2: $cublas"
        return $true
    }

    Write-Warning "Blackwell uses CUDA 13 PyTorch, while Faster-Whisper still requires the CUDA 12.x runtime."
    if ($DryRun) {
        Write-Info "A normal run can install CUDA Toolkit 12.8 or fall back to CPU."
        return $true
    }

    $shouldInstall = $InstallCudaToolkit.IsPresent
    if (-not $shouldInstall -and -not $NonInteractive) {
        $answer = Read-Host "CUDA 12.x was not found. Install CUDA Toolkit 12.8? [Y]es / [C]PU fallback / [Q]uit"
        if ($answer -match "^[Yy]$") {
            $shouldInstall = $true
        } elseif ($answer -match "^[Cc]$") {
            return $false
        } else {
            throw "Installation cancelled by the user"
        }
    }

    if (-not $shouldInstall) {
        Write-Warning "CUDA Toolkit installation was not enabled. Falling back to CPU. Use -InstallCudaToolkit to allow it."
        return $false
    }

    $winget = Get-Command "winget.exe" -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "winget is unavailable. Install CUDA Toolkit 12.8 manually and try again."
    }

    Write-Step "Install NVIDIA CUDA Toolkit 12.8"
    Invoke-Native $winget.Source @(
        "install", "--id", "Nvidia.CUDA", "--exact", "--version", "12.8",
        "--silent", "--accept-package-agreements", "--accept-source-agreements"
    )

    $cublas = Find-Cuda12Cublas
    if (-not $cublas) {
        $defaultCublas = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin\cublas64_12.dll"
        if (Test-Path -LiteralPath $defaultCublas) {
            $cublas = $defaultCublas
        }
    }
    if (-not $cublas) {
        throw "CUDA Toolkit completed but cublas64_12.dll is unavailable. Restart Windows and run setup.bat again."
    }
    Add-Cuda12ToCurrentPath $cublas
    return $true
}

function Get-ProfileSettings([string]$SelectedProfile) {
    switch ($SelectedProfile) {
        "nvidia-modern" {
            return [pscustomobject]@{
                Label = "NVIDIA Blackwell / CUDA 13.0"
                IndexUrl = "https://download.pytorch.org/whl/cu130"
                LocalTag = "+cu130"
                ExpectCuda = $true
            }
        }
        "nvidia-legacy" {
            return [pscustomobject]@{
                Label = "NVIDIA compatible / CUDA 12.6"
                IndexUrl = "https://download.pytorch.org/whl/cu126"
                LocalTag = "+cu126"
                ExpectCuda = $true
            }
        }
        default {
            return [pscustomobject]@{
                Label = "CPU universal"
                IndexUrl = "https://download.pytorch.org/whl/cpu"
                LocalTag = "+cpu"
                ExpectCuda = $false
            }
        }
    }
}

function Ensure-Venv([string]$PythonExe) {
    $venvPython = Join-Path $VenvFullPath "Scripts\python.exe"
    $needsRebuild = $ForceRecreate.IsPresent -or -not (Test-Path -LiteralPath $venvPython)
    if (-not $needsRebuild) {
        $version = & $venvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        $needsRebuild = $LASTEXITCODE -ne 0 -or $version.Trim() -ne "3.12"
    }

    if ($needsRebuild) {
        Write-Step "Create the Python 3.12 virtual environment"
        Invoke-Native $PythonExe @("-m", "venv", "--clear", "--upgrade-deps", $VenvFullPath)
    } else {
        Write-Info "Reusing the existing Python 3.12 environment: $VenvFullPath"
    }
    return $venvPython
}

function Configure-VenvPip {
    $pipConfig = Join-Path $VenvFullPath "pip.ini"
    @(
        "[global]",
        "no-cache-dir = true",
        "disable-pip-version-check = true"
    ) | Set-Content -LiteralPath $pipConfig -Encoding ASCII
}

function Install-TorchProfile($VenvPython, $Settings) {
    $expectedTorch = "$TorchVersion$($Settings.LocalTag)"
    $installedTorch = & $VenvPython -c "import importlib.metadata as m; print(m.version('torch'))" 2>$null
    $installedAudio = & $VenvPython -c "import importlib.metadata as m; print(m.version('torchaudio'))" 2>$null

    if ($LASTEXITCODE -eq 0 -and $installedTorch.Trim() -eq $expectedTorch -and $installedAudio.Trim() -eq $expectedTorch) {
        Write-Info "PyTorch profile already matches: $expectedTorch"
        return
    }

    Write-Step "Install $($Settings.Label)"
    Invoke-Native $VenvPython @(
        "-m", "pip", "install", "--no-cache-dir", "--upgrade", "--force-reinstall",
        "torch==$expectedTorch", "torchaudio==$expectedTorch",
        "--index-url", $Settings.IndexUrl
    )
}

function Test-Runtime($VenvPython, $Settings) {
    Write-Step "Validate dependencies and runtime"
    Invoke-Native $VenvPython @("-m", "pip", "check")
    $validationArguments = @((Join-Path $ProjectRoot "scripts\validate_runtime.py"))
    if ($Settings.ExpectCuda) {
        $validationArguments += "--expect-cuda"
    }
    Invoke-Native $VenvPython $validationArguments
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " txt2srt hardware-aware installer" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Initialize-ProjectStorage
$PythonExe = Ensure-Python312
$Gpu = Get-NvidiaGpu
$SelectedProfile = Select-HardwareProfile $Profile $Gpu

if ($Gpu) {
    Write-Info "NVIDIA GPU: $($Gpu.Name)"
    Write-Info "Compute capability: $($Gpu.Capability); driver: $($Gpu.Driver)"
} else {
    Write-Info "No supported NVIDIA GPU was detected. The CPU profile will be used."
}

if ($SelectedProfile -eq "nvidia-modern") {
    $runtimeReady = Ensure-BlackwellCudaRuntime
    if (-not $runtimeReady) {
        $SelectedProfile = "cpu"
    }
}

$Settings = Get-ProfileSettings $SelectedProfile
Write-Host "`nSelected profile: $($Settings.Label)" -ForegroundColor Green
Write-Info "PyTorch index: $($Settings.IndexUrl)"

if ($DryRun) {
    Write-Host "`nDryRun complete: the virtual environment was not changed." -ForegroundColor Yellow
    exit 0
}

$VenvPython = Ensure-Venv $PythonExe
Configure-VenvPip
Write-Step "Upgrade pip"
Invoke-Native $VenvPython @("-m", "pip", "install", "--no-cache-dir", "--upgrade", "pip")
Install-TorchProfile $VenvPython $Settings

Write-Step "Install common project dependencies"
Invoke-Native $VenvPython @("-m", "pip", "install", "--no-cache-dir", "-r", (Join-Path $ProjectRoot "requirements-common.txt"))

if (-not $SkipRuntimeCheck) {
    Test-Runtime $VenvPython $Settings
}

$profileRecord = [ordered]@{
    profile = $SelectedProfile
    label = $Settings.Label
    torch_version = "$TorchVersion$($Settings.LocalTag)"
    gpu = if ($Gpu) { $Gpu.Name } else { $null }
    compute_capability = if ($Gpu) { $Gpu.Capability } else { $null }
    models_directory = $ModelsRoot
    runtime_directory = $RuntimeRoot
    installed_at = (Get-Date).ToString("s")
}
$profileRecord | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $VenvFullPath "hardware-profile.json") -Encoding UTF8

Write-Host "`nInstallation complete." -ForegroundColor Green
Write-Host "Start Web UI:        start_ui.bat"
Write-Host "Start desktop UI:    start_tkinter_ui.bat"
Write-Host "Activate venv:       venv\Scripts\activate"
Write-Host "Models directory:    models"
Write-Host "Temporary directory: .runtime"
