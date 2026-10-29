# Usage: .\install.ps1 <git-url-of-ub-mode>
#        .\install.ps1                      (rerun: updates an existing install)
# Env:   UB_MODE_DIR  install location, default %USERPROFILE%\.claude\skills\ub-mode
#        PIP_INDEX_URL                           internal PyPI mirror (Artifactory)
#        TREE_SITTER_LANGUAGE_PACK_MANIFEST_URL  internal parser mirror (scripts/mirror_parsers.py)
param([string]$RepoUrl = "")

$ErrorActionPreference = "Stop"
$SkillDir = if ($env:UB_MODE_DIR) { $env:UB_MODE_DIR } else { Join-Path $HOME ".claude\skills\ub-mode" }
$Tools = @("crapper", "dryer", "mutator")

function Fail([string]$Message) { Write-Host "ERROR: $Message" -ForegroundColor Red; exit 1 }
function Step([string]$Message) { Write-Host "==> $Message" }

function Invoke-Checked([string]$Exe, [string[]]$Arguments) {
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { Fail "$Exe $($Arguments -join ' ') failed." }
}

function Assert-Git {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Fail "git is not installed." }
}

function Find-Python {
    $candidates = @(
        @("py", "-3.13"), @("py", "-3.12"), @("py", "-3.11"), @("py", "-3"),
        @("python3"), @("python")
    )
    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate[0] -ErrorAction SilentlyContinue)) { continue }
        $prefix = @($candidate | Select-Object -Skip 1)
        & $candidate[0] @prefix -c "import sys; sys.exit(sys.version_info < (3, 11))" 2>$null
        if ($LASTEXITCODE -eq 0) { return , $candidate }
    }
    Fail "Python 3.11 or newer is required. Install it from python.org."
}

function Get-DefaultRepoUrl {
    $url = git -C $PSScriptRoot remote get-url origin 2>$null
    if ($LASTEXITCODE -eq 0) { return $url }
    return ""
}

function Sync-Repo {
    if (Test-Path (Join-Path $SkillDir ".git")) {
        Step "Updating $SkillDir"
        Invoke-Checked git @("-C", $SkillDir, "pull", "--ff-only")
        return
    }
    if (-not $script:RepoUrl -and $PSScriptRoot) { $script:RepoUrl = Get-DefaultRepoUrl }
    if (-not $script:RepoUrl) { Fail "Pass the GitLab URL: .\install.ps1 <git-url>" }
    if (Test-Path $SkillDir) { Fail "$SkillDir exists and is not a git checkout. Move it away first." }
    Step "Cloning $script:RepoUrl into $SkillDir"
    New-Item -ItemType Directory -Force -Path (Split-Path $SkillDir) | Out-Null
    Invoke-Checked git @("clone", $script:RepoUrl, $SkillDir)
}

function Install-Tools($Python) {
    $venvPython = Join-Path $SkillDir ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Step "Creating virtualenv"
        $prefix = @($Python | Select-Object -Skip 1)
        Invoke-Checked $Python[0] ($prefix + @("-m", "venv", (Join-Path $SkillDir ".venv")))
    }
    Step "Installing pinned packages from requirements.lock"
    Invoke-Checked $venvPython @("-m", "pip", "install", "--quiet", "-r", (Join-Path $SkillDir "requirements.lock"))
    $editable = foreach ($tool in $Tools) { "-e"; (Join-Path $SkillDir "tools\$tool") }
    Step "Installing $($Tools -join ', ')"
    Invoke-Checked $venvPython (@("-m", "pip", "install", "--quiet", "--no-deps", "--no-build-isolation") + $editable)
}

function Get-Parsers {
    Step "Downloading tree-sitter parsers"
    $venvPython = Join-Path $SkillDir ".venv\Scripts\python.exe"
    $script = "import sys; from tree_sitter_language_pack import download; download(open(sys.argv[1]).read().split())"
    & $venvPython -c $script (Join-Path $SkillDir "parser-languages.txt")
    if ($LASTEXITCODE -ne 0) {
        Fail "Parser download failed. On a closed network set TREE_SITTER_LANGUAGE_PACK_MANIFEST_URL."
    }
}

function Test-Tools {
    foreach ($tool in $Tools) {
        & (Join-Path $SkillDir ".venv\Scripts\$tool.exe") --help | Out-Null
        if ($LASTEXITCODE -ne 0) { Fail "$tool does not start." }
    }
    Step "Verified: $($Tools -join ', ')"
}

function Test-Symlinks {
    $probe = Join-Path ([IO.Path]::GetTempPath()) ("ub-mode-link-" + [guid]::NewGuid())
    try {
        New-Item -ItemType SymbolicLink -Path $probe -Target $SkillDir -ErrorAction Stop | Out-Null
        Remove-Item $probe -Force
    } catch {
        Write-Host "WARNING: this user cannot create symlinks. mutator needs them." -ForegroundColor Yellow
        Write-Host "         Turn on Settings > System > For developers > Developer Mode." -ForegroundColor Yellow
    }
}

Assert-Git
$python = Find-Python
Sync-Repo
Install-Tools $python
Get-Parsers
Test-Tools
Test-Symlinks
Write-Host ""
Write-Host "ub-mode is installed in $SkillDir"
Write-Host "Open Claude Code in a Python project and run: /ub-mode <your request>"
