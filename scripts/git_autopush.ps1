param(
    [string]$Message
)

$ErrorActionPreference = "Stop"

function Write-LatestCommitFile {
    param(
        [string]$RepoUrl,
        [string]$CommitHash
    )
    $utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $content = @"
# Latest Commit

- repo_url: `$RepoUrl`
- branch: `main`
- last_commit: `$CommitHash`
- date: `$utc`
"@
    if (-not (Test-Path "docs")) {
        New-Item -ItemType Directory -Path "docs" | Out-Null
    }
    Set-Content -Path "docs/LATEST_COMMIT.md" -Value $content -Encoding UTF8
}

git rev-parse --is-inside-work-tree | Out-Null

Write-Host "== git status =="
git status --short

$porcelain = git status --porcelain
if (-not $porcelain) {
    Write-Host "No changes"
    exit 0
}

if (-not $Message) {
    $Message = Read-Host "Commit message"
}
if ([string]::IsNullOrWhiteSpace($Message)) {
    $Message = "chore: update files"
}

git add -A
$staged = git diff --cached --name-only
if (-not $staged) {
    Write-Host "No changes"
    exit 0
}

git commit -m $Message
$commitHash = (git rev-parse --short HEAD).Trim()

$repoUrl = "NO_REMOTE_CONFIGURED"
try {
    $candidate = (git remote get-url origin 2>$null).Trim()
    if ($candidate) {
        $repoUrl = $candidate
    }
} catch {
    $repoUrl = "NO_REMOTE_CONFIGURED"
}

Write-LatestCommitFile -RepoUrl $repoUrl -CommitHash $commitHash
git add docs/LATEST_COMMIT.md
$markerDiff = git diff --cached --name-only
if ($markerDiff) {
    git commit -m "chore: update latest commit marker ($commitHash)"
}

if ($repoUrl -ne "NO_REMOTE_CONFIGURED") {
    git push origin main
} else {
    Write-Warning "origin remote is not configured. Commit created locally only."
}

$head = (git rev-parse --short HEAD).Trim()
Write-Host ""
Write-Host "repo_url: $repoUrl"
Write-Host "last_commit_saved: $commitHash"
Write-Host "current_head: $head"
