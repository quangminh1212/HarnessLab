#Requires -Version 5.1
<#
.SYNOPSIS
  Attach NexusLab to local Hermes Agent (junctions only).
  SoT stays in C:\Dev\NexusLab - no hermes-agent source edits.
#>
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Hermes = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA 'hermes' }
$SkillsSrc = Join-Path $Root 'skills'
$SkillsDstRoot = Join-Path $Hermes 'skills'

Write-Host "== NexusLab attach ==" -ForegroundColor Cyan
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

# Thin /harnesslab alias — NEVER junction to nexuslab (duplicate frontmatter name: nexuslab breaks skill_view)
$hlDst = Join-Path $SkillsDstRoot 'harnesslab'
$hlSkill = Join-Path $hlDst 'SKILL.md'
$hlBody = @'
---
name: harnesslab
description: >
  Alias of NexusLab multi-AI harness/council. Prefer skill_view("nexuslab") or /nexuslab.
  Same CLI: python -m nexuslab smoke|doctor|council|...
compatibility: terminal; gh recommended
metadata:
  hermes:
    tags: [alias, nexuslab, harness]
    category: development
    requires_toolsets: [terminal]
---

# harnesslab (alias)

**Canonical skill:** `nexuslab` → SoT NexusLab `skills/nexuslab`

```powershell
python -m nexuslab smoke
python -m nexuslab doctor
```

Load **nexuslab** for the full workflow.
'@
if (Test-Path $hlDst) {
  $item = Get-Item $hlDst -Force
  $isLink = [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
  if ($isLink) {
    Write-Host "Replacing harnesslab junction with thin alias skill"
    cmd /c "rmdir `"$hlDst`"" | Out-Null
  }
}
New-Item -ItemType Directory -Force -Path $hlDst | Out-Null
Set-Content -Path $hlSkill -Value $hlBody -Encoding UTF8
Write-Host "Wrote thin alias: $hlSkill"

$ctxSrc = Join-Path $Root 'templates\HERMES.md'
$ctxDst = Join-Path $Hermes 'nexuslab-HERMES.md'
if (Test-Path $ctxSrc) {
  Copy-Item $ctxSrc $ctxDst -Force
  Write-Host "Wrote $ctxDst"
}

# Best-effort: editable CLI into Hermes agent venv (terminal tool can run python -m nexuslab)
$HermesPyCandidates = @(
  (Join-Path $Hermes 'hermes-agent\venv\Scripts\python.exe'),
  (Join-Path $Hermes 'hermes-agent\.venv\Scripts\python.exe')
)
foreach ($py in $HermesPyCandidates) {
  if (Test-Path $py) {
    Write-Host "Installing nexuslab CLI into Hermes venv: $py"
    & $py -m pip install -e $Root -q
    if ($LASTEXITCODE -ne 0) {
      Write-Warning "pip install into Hermes venv failed (skills still attached)"
    } else {
      Write-Host "CLI OK: $py -m nexuslab"
    }
    break
  }
}

Write-Host ""
Write-Host "OK. NexusLab attached (junction only)." -ForegroundColor Green
Write-Host "In Hermes chat: /nexuslab  (multi-AI GitHub council)"
Write-Host "Detach: powershell -File $Root\scripts\uninstall.ps1"
Write-Host "CLI:    cd $Root; python -m pip install -e .; python -m nexuslab smoke"
Write-Host "Council: python -m nexuslab council init demo --ref owner/repo#1 --topic '...'"
