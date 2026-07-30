#Requires -Version 5.1
<#
.SYNOPSIS
  Attach HarnessLab to local Hermes Agent (junctions only).
  SoT stays in C:\Dev\HarnessLab - no hermes-agent source edits.
#>
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Hermes = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA 'hermes' }
$SkillsSrc = Join-Path $Root 'skills'
$SkillsDstRoot = Join-Path $Hermes 'skills'

Write-Host "== HarnessLab attach ==" -ForegroundColor Cyan
Write-Host "Repo:   $Root"
Write-Host "Hermes: $Hermes"

if (-not (Test-Path $Hermes)) {
  throw "Hermes home not found: $Hermes - install Hermes Agent first."
}
if (-not (Test-Path $SkillsSrc)) {
  throw "skills/ missing under $Root"
}

function Ensure-Junction($dst, $src) {
  $parent = Split-Path $dst -Parent
  New-Item -ItemType Directory -Force -Path $parent | Out-Null
  $want = (Resolve-Path $src).Path
  if (Test-Path $dst) {
    $item = Get-Item $dst -Force
    $isLink = [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
    $target = $null
    if ($isLink -and $item.Target) { $target = @($item.Target)[0] }
    if ($isLink -and $target) {
      $resolved = Resolve-Path $target -ErrorAction SilentlyContinue
      if ($resolved -and $resolved.Path -eq $want) {
        Write-Host "Junction OK: $dst -> $src"
        return
      }
      Write-Host "Re-pointing junction: $dst"
      cmd /c "rmdir `"$dst`"" | Out-Null
    } else {
      # Replace plain stock skill dir (e.g. old harness-integration copy)
      Write-Host "Replacing non-junction path: $dst"
      Remove-Item -Recurse -Force $dst
    }
  }
  cmd /c mklink /J "$dst" "$src" | Write-Host
}

Get-ChildItem $SkillsSrc -Directory | ForEach-Object {
  $skillMd = Join-Path $_.FullName 'SKILL.md'
  if (-not (Test-Path $skillMd)) { return }
  $dst = Join-Path $SkillsDstRoot $_.Name
  Ensure-Junction $dst $_.FullName
}

# Thin /nexuslab alias — NEVER junction to harnesslab (duplicate frontmatter name breaks skill_view)
$nxDst = Join-Path $SkillsDstRoot 'nexuslab'
$nxSkill = Join-Path $nxDst 'SKILL.md'
$nxBody = @'
---
name: nexuslab
description: >
  Alias of HarnessLab multi-AI harness/council. Prefer skill_view("harnesslab") or /harnesslab.
  Same CLI: python -m harnesslab smoke|doctor|council|...
compatibility: terminal; gh recommended
metadata:
  hermes:
    tags: [alias, harnesslab, nexuslab, harness]
    category: development
    requires_toolsets: [terminal]
---

# nexuslab (alias)

**Canonical skill:** `harnesslab` → SoT HarnessLab `skills/harnesslab`

```powershell
python -m harnesslab smoke
python -m harnesslab doctor
```

Load **harnesslab** for the full workflow.
'@
if (Test-Path $nxDst) {
  $item = Get-Item $nxDst -Force
  $isLink = [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
  if ($isLink) {
    Write-Host "Replacing nexuslab junction with thin alias skill"
    cmd /c "rmdir `"$nxDst`"" | Out-Null
  }
}
New-Item -ItemType Directory -Force -Path $nxDst | Out-Null
Set-Content -Path $nxSkill -Value $nxBody -Encoding UTF8
Write-Host "Wrote thin alias: $nxSkill"

$ctxSrc = Join-Path $Root 'templates\HERMES.md'
$ctxDst = Join-Path $Hermes 'harnesslab-HERMES.md'
if (Test-Path $ctxSrc) {
  Copy-Item $ctxSrc $ctxDst -Force
  Write-Host "Wrote $ctxDst"
}

# Best-effort: editable CLI into Hermes agent venv (terminal tool can run python -m harnesslab)
$HermesPyCandidates = @(
  (Join-Path $Hermes 'hermes-agent\venv\Scripts\python.exe'),
  (Join-Path $Hermes 'hermes-agent\.venv\Scripts\python.exe')
)
foreach ($py in $HermesPyCandidates) {
  if (Test-Path $py) {
    Write-Host "Installing harnesslab CLI into Hermes venv: $py"
    & $py -m pip install -e $Root -q
    if ($LASTEXITCODE -ne 0) {
      Write-Warning "pip install into Hermes venv failed (skills still attached)"
    } else {
      Write-Host "CLI OK: $py -m harnesslab"
    }
    break
  }
}

Write-Host ""
Write-Host "OK. HarnessLab attached (junction only)." -ForegroundColor Green
Write-Host "In Hermes chat: /harnesslab  (multi-AI GitHub council)"
Write-Host "Detach: powershell -File $Root\scripts\uninstall.ps1"
Write-Host "CLI:    cd $Root; python -m pip install -e .; python -m harnesslab smoke"
Write-Host "Council: python -m harnesslab council init demo --ref owner/repo#1 --topic '...'"
