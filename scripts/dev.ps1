# PowerShell script for development startup
# Sets environment variables and starts Next.js dev server

Write-Host "🚀 Starting Seraaj Development Environment" -ForegroundColor Green

# Set environment variables for frontend
$env:NEXT_PUBLIC_BFF_URL = "http://127.0.0.1:8000/api"

Write-Host "Environment configured:" -ForegroundColor Yellow
Write-Host "  NEXT_PUBLIC_BFF_URL = $env:NEXT_PUBLIC_BFF_URL" -ForegroundColor Cyan

# Change to web app directory and start dev server
Set-Location "apps\web"

Write-Host "Starting Next.js development server..." -ForegroundColor Yellow
pnpm dev