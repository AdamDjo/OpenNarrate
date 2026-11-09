# Modèle pour générer plusieurs images avec Codex. Copier dans le projet, remplir, puis lancer dans le terminal de l'utilisateur :
#   powershell -ExecutionPolicy Bypass -File generer_images.ps1      (relançable : saute les images déjà faites)
$d = $PSScriptRoot
$out = "$d\images"
New-Item -ItemType Directory -Force "$out\logs" | Out-Null
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { "$env:USERPROFILE\.codex" }

# Une phrase de style réutilisée dans chaque prompt (une seule ligne, sans le mot « using »).
$style = "Style: <style de l'univers>. Not photorealistic, not Disney, not Pixar. No text, no logo, no watermark."

function Gen($nom, $prompt, $imgs) {
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

# Gen "V01_premiere_vision" "Description de l'image. $style" @("$d\refs\reference.jpg")
