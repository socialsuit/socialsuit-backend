# PowerShell script to commit OpenAPI files

# Navigate to the project root
Set-Location -Path "c:\Users\hhp\social_suit"

# Add the OpenAPI files to git
git add social-suit/docs/openapi/openapi.json
git add sparkr-backend/docs/openapi/openapi.json
git add docs/openapi.md

# Commit the changes
git commit -m "Add OpenAPI documentation with versioning, tags, and security schemes"

# Output success message
Write-Host "OpenAPI files committed successfully" -ForegroundColor Green