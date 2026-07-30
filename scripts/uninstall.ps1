#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Hermes = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA 'hermes' }
$SkillsSrc = Join-Path $Root 'skills'
$SkillsDstRoot = Join-Path $Hermes 'skills'

Write-Host "== HarnessLab detach ==" -ForegroundColor Cyan

Get-ChildItem $SkillsSrc -Directory -ErrorAction SilentlyContinue | ForEach-Object {
  $dst = Join-Path $SkillsDstRoot $_.Name
  if (Test-Path $dst) {
    $item = Get-Item $dst -Force
    $isLink = [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
    if ($isLink) {
      cmd /c "rmdir `"$dst`"" | Out-Null
      Write-Host "Removed junction: $dst"
    } else {
      Write-Host "Skip non-junction: $dst" -ForegroundColor Yellow
    }
  }
}

foreach ($name in @('harnesslab-HERMES.md', 'nexuslab-HERMES.md')) {
  $note = Join-Path $Hermes $name
  if (Test-Path $note) {
    Remove-Item $note -Force
    Write-Host "Removed $note"
  }
}

# Thin alias skill (plain dir, not junction)
$nxAlias = Join-Path $SkillsDstRoot 'nexuslab'
if (Test-Path $nxAlias) {
  $item = Get-Item $nxAlias -Force
  $isLink = [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
  if ($isLink) {
    cmd /c "rmdir `"$nxAlias`"" | Out-Null
  } else {
    Remove-Item -Recurse -Force $nxAlias
  }
  Write-Host "Removed alias: $nxAlias"
}

Write-Host "OK. HarnessLab detached." -ForegroundColor Green
