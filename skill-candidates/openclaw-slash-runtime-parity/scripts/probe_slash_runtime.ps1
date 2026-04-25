param(
  [string]$RuntimeBase = "http://127.0.0.1:5175",
  [string]$ModelBase = "http://127.0.0.1:9000/v1",
  [string]$ShimUrl = "http://127.0.0.1:9000",
  [string]$Provider = "openai_compat",
  [string]$Model = "huihui-qwen3.5-27b-abliterated",
  [string]$RouteMode = "local",
  [string[]]$Commands = @("/status", "/tasks", "/help", "/tts on"),
  [int]$TimeoutSec = 300,
  [int]$PollSec = 2,
  [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

function Get-LatestSessionLogPath {
  $logRoot = "%USERPROFILE%\AppData\Roaming\@vrm-sandbox\logs"
  if (-not (Test-Path $logRoot)) {
    return $null
  }
  $latest = Get-ChildItem -Path $logRoot -Filter "session-*.json" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
  return $latest.FullName
}

function Read-SessionEventsSince {
  param(
    [string]$Path,
    [DateTime]$StartUtc
  )
  if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path $Path)) {
    return @()
  }
  $events = @()
  foreach ($line in Get-Content -Path $Path -ErrorAction SilentlyContinue) {
    if ([string]::IsNullOrWhiteSpace($line)) {
      continue
    }
    try {
      $entry = $line | ConvertFrom-Json -ErrorAction Stop
    } catch {
      continue
    }
    $timestampText = [string]$entry.timestamp
    if ([string]::IsNullOrWhiteSpace($timestampText)) {
      continue
    }
    try {
      $ts = [DateTime]::Parse($timestampText).ToUniversalTime()
    } catch {
      continue
    }
    if ($ts -lt $StartUtc) {
      continue
    }
    $events += $entry
  }
  return $events
}

function Get-LatestAssistantMessage {
  param(
    [object]$WindowState
  )
  if ($null -eq $WindowState -or $null -eq $WindowState.messages) {
    return $null
  }
  return @($WindowState.messages | Where-Object { $_.role -eq "assistant" }) | Select-Object -Last 1
}

$results = @()

foreach ($commandText in $Commands) {
  $trimmedCommand = [string]$commandText
  $startUtc = [DateTime]::UtcNow
  $logPath = Get-LatestSessionLogPath

  $payload = @{
    provider = $Provider
    baseUrl = $ModelBase
    model = $Model
    routeMode = $RouteMode
    shimUrl = $ShimUrl
    messages = @(
      @{
        role = "user"
        content = $trimmedCommand
      }
    )
  } | ConvertTo-Json -Depth 8

  $requestOk = $false
  $requestError = $null
  $response = $null
  $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    $response = Invoke-RestMethod -Method Post -Uri "$RuntimeBase/runtime/chat/send" -ContentType "application/json" -Body $payload -TimeoutSec $TimeoutSec
    $requestOk = $true
  } catch {
    $requestError = $_.Exception.Message
  }
  $stopwatch.Stop()

  $windowState = $null
  $assistantMessage = $null
  $pollDeadline = (Get-Date).AddSeconds($TimeoutSec)
  while ((Get-Date) -lt $pollDeadline) {
    try {
      $windowState = Invoke-RestMethod -Uri "$RuntimeBase/runtime/chat/window-state" -TimeoutSec 10
      $assistantMessage = Get-LatestAssistantMessage -WindowState $windowState
    } catch {
      $assistantMessage = $null
    }
    if ($assistantMessage -and -not [string]::IsNullOrWhiteSpace([string]$assistantMessage.text)) {
      break
    }
    Start-Sleep -Seconds $PollSec
  }

  $events = Read-SessionEventsSince -Path $logPath -StartUtc $startUtc
  $ragCount = @($events | Where-Object { $_.type -eq "rag.retrieve" }).Count
  $ttsEvents = @($events | Where-Object { [string]$_.type -like "tts.*" })
  $ttsTerminal = @(
    $ttsEvents | Where-Object {
      $_.type -in @("tts.play", "tts.error", "tts.emoji_only", "tts.stopped", "tts.autoplay_unlock_required")
    }
  )

  $assistantText = [string]$assistantMessage.text
  $responseText = if ($response -and $response.PSObject.Properties.Name -contains "text") { [string]$response.text } else { "" }

  $results += [pscustomobject]@{
    command = $trimmedCommand
    requestMs = $stopwatch.ElapsedMilliseconds
    requestOk = $requestOk
    requestError = $requestError
    responseOk = if ($response -and $response.PSObject.Properties.Name -contains "ok") { [bool]$response.ok } else { $false }
    responseTextLength = $responseText.Length
    responsePreview = if ($responseText.Length -gt 220) { $responseText.Substring(0, 220) } else { $responseText }
    assistantMessageId = [string]$assistantMessage.id
    assistantSpeakStatus = [string]$assistantMessage.speakStatus
    assistantSpeechChunkCount = @($assistantMessage.speechArtifact.chunks).Count
    assistantPreview = if ($assistantText.Length -gt 220) { $assistantText.Substring(0, 220) } else { $assistantText }
    ragRetrieveCount = $ragCount
    ttsEventTypes = @($ttsEvents | ForEach-Object { [string]$_.type })
    ttsTerminalEventCount = $ttsTerminal.Count
    sessionLog = $logPath
  }
}

$report = [pscustomobject]@{
  generatedAtUtc = [DateTime]::UtcNow.ToString("o")
  runtimeBase = $RuntimeBase
  modelBase = $ModelBase
  model = $Model
  timeoutSec = $TimeoutSec
  commands = $Commands
  results = $results
}

$json = $report | ConvertTo-Json -Depth 8
if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
  $outDir = Split-Path -Path $OutputPath -Parent
  if (-not [string]::IsNullOrWhiteSpace($outDir) -and -not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
  }
  Set-Content -Path $OutputPath -Value $json -Encoding UTF8
}

$json
