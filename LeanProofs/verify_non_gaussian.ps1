param(
  [string]$LeanBinary = 'lean',
  [string]$MathlibProject = $PSScriptRoot
)
$ErrorActionPreference = 'Stop'
$modules = @('NonGaussianProbability', 'NonGaussianDesign', 'NonGaussianEuclidean',
  'NonGaussianMoments', 'NonGaussianMatrix', 'NonGaussianTargetUpdate',
  'NonGaussianBridge', 'NonGaussianAxiomAudit')
$packageRoot = Join-Path $MathlibProject '.lake\packages'
if (-not (Test-Path -LiteralPath $packageRoot)) {
  throw "Missing cached packages at $packageRoot. Run lake update / lake exe cache get first."
}
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'lake-manifest.json') -Raw | ConvertFrom-Json
$expectedMathlib = ($manifest.packages | Where-Object { $_.name -eq 'mathlib' }).rev
$mathlibDir = Join-Path $packageRoot 'mathlib'
$mathlibHead = (Get-Content -LiteralPath (Join-Path $mathlibDir '.git\HEAD') -Raw).Trim()
if ($mathlibHead.StartsWith('ref: ')) {
  $reference = $mathlibHead.Substring(5)
  $referenceFile = Join-Path (Join-Path $mathlibDir '.git') $reference
  if (Test-Path -LiteralPath $referenceFile) {
    $mathlibHead = (Get-Content -LiteralPath $referenceFile -Raw).Trim()
  } else {
    $packed = Get-Content -LiteralPath (Join-Path $mathlibDir '.git\packed-refs') |
      Where-Object { $_ -match ('^[0-9a-f]+ ' + [regex]::Escape($reference) + '$') }
    if (@($packed).Count -ne 1) { throw 'Cannot resolve cached mathlib revision.' }
    $mathlibHead = ($packed -split ' ')[0]
  }
}
if ($mathlibHead -ne $expectedMathlib) { throw 'Cached mathlib revision does not match the lockfile.' }
$buildDir = Join-Path $PSScriptRoot '.lake\non_gaussian'
$reportDir = Join-Path (Split-Path -Parent $PSScriptRoot) 'revision\non_gaussian_bridge'
New-Item -ItemType Directory -Path $buildDir -Force | Out-Null
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
$dependencyPaths = @(Get-ChildItem -LiteralPath $packageRoot -Directory |
  ForEach-Object { Join-Path $_.FullName '.lake\build\lib\lean' } |
  Where-Object { Test-Path -LiteralPath $_ })
$previousLeanPath = $env:LEAN_PATH
$env:LEAN_PATH = (@($buildDir) + $dependencyPaths) -join ';'
$checks = @()
$transcript = @()
$utf8 = New-Object System.Text.UTF8Encoding($false)
Push-Location $PSScriptRoot
try {
  $version = (& $LeanBinary --version 2>&1 | Out-String).Trim()
  if ($LASTEXITCODE -ne 0) { throw 'Lean version check failed.' }
  foreach ($module in $modules) {
    $source = Join-Path $PSScriptRoot ($module + '.lean')
    $object = Join-Path $buildDir ($module + '.olean')
    $output = & $LeanBinary --error=warning -o $object ($module + '.lean') 2>&1
    $exitCode = $LASTEXITCODE
    $lines = @($output | ForEach-Object { $_.ToString() })
    $transcript += @("MODULE $module", "EXIT $exitCode") + $lines
    $checks += [ordered]@{
      module = $module
      exit_code = $exitCode
      sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash.ToLowerInvariant()
      output = $lines
    }
    Write-Output "$module : exit $exitCode"
    if ($exitCode -ne 0) {
      $lines | Write-Output
      throw "Lean verification failed: $module"
    }
  }
  $text = $transcript -join "`n"
  if ($text -match '\bsorryAx\b') { throw 'Unexpected sorryAx dependency.' }
  $result = [ordered]@{
    verified_at = (Get-Date).ToString('o')
    lean_version = $version
    warning_as_error = $true
    mathlib_revision = $mathlibHead
    source_of_mathlib_revision = 'Cached package Git HEAD verified against LeanProofs/lake-manifest.json'
    checks = $checks
    passed = $true
  }
  [System.IO.File]::WriteAllText((Join-Path $reportDir 'lean_verification.json'),
    ($result | ConvertTo-Json -Depth 8) + "`n", $utf8)
  [System.IO.File]::WriteAllText((Join-Path $reportDir 'lean_verification.txt'), $text + "`n", $utf8)
} finally {
  Pop-Location
  $env:LEAN_PATH = $previousLeanPath
}
