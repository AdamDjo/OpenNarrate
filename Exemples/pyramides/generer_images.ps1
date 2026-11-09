# Images reelles de l'exemple des pyramides. Relancable : saute les images deja faites.
# Option : donner des noms d'images pour ne generer que celles-la.
$seul = $args
$d = $PSScriptRoot
$out = "$d\images"
New-Item -ItemType Directory -Force "$out\logs" | Out-Null
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { "$env:USERPROFILE\.codex" }

$style = "Style: hand-painted gouache illustration, visible brush strokes, palette of warm sand, ochre, turquoise and deep blue, ancient Egypt. Not photorealistic, not Disney, not Pixar. No text, no hieroglyphs, no logo, no watermark."

function Gen($nom, $prompt, $imgs) {
  if ($seul.Count -gt 0 -and $seul -notcontains $nom) { return }
  $dest = "$out\$nom.png"
  if (Test-Path $dest) { Write-Host "DEJA FAIT $nom"; return }
  Write-Host "=== $nom ..."
  $a = @("exec", "--skip-git-repo-check", "Call your image generation tool to create one image, wide 16:9 landscape format. $prompt")
  foreach ($i in $imgs) { $a += "-i"; $a += $i }
  $log = & codex.cmd @a 2>&1 | ForEach-Object { "$_" }
  $log | Out-File "$out\logs\$nom.txt" -Encoding utf8
  $sid = ($log | Select-String -Pattern 'session id:\s*([0-9a-fA-F-]+)' | Select-Object -First 1).Matches.Groups[1].Value
  $png = $null
  if ($sid) { $png = Get-ChildItem "$codexHome\generated_images\$sid" -Filter *.png -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1 }
  if ($png) { Copy-Item $png.FullName $dest; Write-Host "OK $nom" } else { Write-Host "ECHEC $nom (session $sid) - voir logs" }
}

$nefret = "Nefret, an ancient Egyptian woman of about forty-five, calm kind face, brown skin, black braided hair, simple white linen dress, a modest turquoise bead necklace"

Gen "F1_sable" "$nefret, seated large in the foreground on warm sand at the foot of the Great Pyramid at dusk, looking at the viewer and gesturing gently toward the sand beside her, a lit clay oil lamp and round loaves of bread on a reed mat next to her, natural hands. $style" @()
Gen "V01_blanche" "The Great Pyramid of Giza newly finished, covered in smooth gleaming white limestone casing under blazing sun, tiny boats on a canal in the foreground, edges of the image fading into desert haze. $style" @()
Gen "F3_titre" "Silhouettes of the three pyramids of Giza in the lower part of the image at sunset, the upper half of the image is calm empty orange and turquoise sky. $style" @()
Gen "V02_traineau" "A team of ancient Egyptian workers in white kilts hauling an enormous limestone block on a wooden sledge with thick ropes over packed desert ground, one man pouring water in front of the sledge, strong and dignified, edges of the image fading into desert haze. $style" @()
Gen "C01_carte" "An old ink map on aged parchment, top-down view of the river Nile winding through a desert valley, several tiny drawn boats on the river, one small drawn pyramid symbol on the west bank, compass rose, sepia ink only, absolutely no letters and no words on the map. $style" @()
Gen "V03_mystere" "A half-built pyramid at dusk, its upper part unfinished and lost in haze, tiny workers carrying torches on its steps, mysterious and majestic, edges of the image fading into desert haze. $style" @()
Gen "F4_aube" "$nefret, standing seen from behind at medium distance on the sand at dawn, facing the pyramids of Giza far ahead, calm pale sky with empty space in the upper part of the image. $style" @("$out\F1_sable.png")
Write-Host "FINI"
