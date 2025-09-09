# PowerShell script to run database migration commands for both projects

param (
    [Parameter(Mandatory=$true)]
    [ValidateSet("social-suit", "sparkr")]
    [string]$Project,
    
    [Parameter(Mandatory=$true)]
    [ValidateSet("generate", "upgrade", "downgrade")]
    [string]$Command,
    
    [Parameter(Mandatory=$false)]
    [string]$Message = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Revision = "head"
)

$rootDir = $PSScriptRoot

# Set project directory
$projectDir = ""
if ($Project -eq "social-suit") {
    $projectDir = Join-Path $rootDir "social-suit"
} elseif ($Project -eq "sparkr") {
    $projectDir = Join-Path $rootDir "sparkr-backend"
}

# Execute the appropriate command
if ($Command -eq "generate") {
    if ([string]::IsNullOrEmpty($Message)) {
        Write-Error "Error: Migration message is required for generate command"
        exit 1
    }
    
    Write-Host "Generating migration for $Project with message: $Message"
    Set-Location $projectDir
    python scripts/generate_migration.py "$Message"
}
elseif ($Command -eq "upgrade") {
    Write-Host "Upgrading $Project database to revision: $Revision"
    Set-Location $projectDir
    python scripts/run_migrations.py $Revision
}
elseif ($Command -eq "downgrade") {
    Write-Host "Downgrading $Project database to revision: $Revision"
    Set-Location $projectDir
    python scripts/run_migrations.py --down $Revision
}

Write-Host "Migration command completed"