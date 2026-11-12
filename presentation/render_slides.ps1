# Export every slide of the deck to PNG with the installed PowerPoint (visual QA).
param(
  [string]$Deck = "D:\minor project\presentation\AgriVision_AI_Final_Presentation.pptx",
  [string]$Out = "$env:TEMP\agrivision_slides",
  [int[]]$Only = @()
)
New-Item -ItemType Directory -Force $Out | Out-Null
$ppt = New-Object -ComObject PowerPoint.Application
try {
  $pres = $ppt.Presentations.Open($Deck, $true, $false, $false)   # read-only, no window
  $n = $pres.Slides.Count
  for ($i = 1; $i -le $n; $i++) {
    if ($Only.Count -gt 0 -and -not ($Only -contains $i)) { continue }
    $pres.Slides.Item($i).Export((Join-Path $Out ("slide{0:D2}.png" -f $i)), "PNG", 1600, 900)
  }
  $pres.Close()
  "exported $n slides to $Out"
} finally {
  $ppt.Quit()
  [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
}
