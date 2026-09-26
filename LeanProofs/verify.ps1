$ErrorActionPreference = 'Stop'

function Invoke-LeanCheck([string[]] $Arguments) {
    & lake @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "lake $Arguments failed with exit code $LASTEXITCODE"
    }
}

Invoke-LeanCheck @('build')
Invoke-LeanCheck @('env', 'lean', '--error=warning', 'CausalAtlasBridge.lean')
Invoke-LeanCheck @('env', 'lean', '--error=warning', 'AxiomAudit.lean')
