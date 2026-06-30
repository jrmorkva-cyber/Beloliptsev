# Минимальный статический сервер для предпросмотра страниц сайта.
# Корень раздачи = родитель папки .claude (корень проекта).
# -Port позволяет поднять НЕСКОЛЬКО изолированных серверов (по слоту на страницу),
# чтобы параллельные сессии не дёргали друг друга через preview/eval.
param([int]$Port = 8123)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$prefix = "http://localhost:$Port/"
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add($prefix)
try { $listener.Start() } catch { Write-Output "LISTENER_ERROR: $($_.Exception.Message)"; exit 1 }
Write-Output "SERVING $root AT $prefix"
$mime = @{
  '.html'='text/html; charset=utf-8'; '.htm'='text/html; charset=utf-8';
  '.css'='text/css; charset=utf-8'; '.js'='text/javascript; charset=utf-8';
  '.mjs'='text/javascript; charset=utf-8'; '.json'='application/json; charset=utf-8';
  '.svg'='image/svg+xml'; '.png'='image/png'; '.jpg'='image/jpeg'; '.jpeg'='image/jpeg';
  '.gif'='image/gif'; '.webp'='image/webp'; '.ttf'='font/ttf'; '.otf'='font/otf';
  '.woff'='font/woff'; '.woff2'='font/woff2'; '.ico'='image/x-icon'; '.txt'='text/plain; charset=utf-8'
}
while ($listener.IsListening) {
  try { $ctx = $listener.GetContext() } catch { break }
  $req = $ctx.Request; $res = $ctx.Response
  try {
    $rel = [System.Uri]::UnescapeDataString($req.Url.AbsolutePath)
    if ($rel -eq '/') { $rel = '/index.html' }
    $rel = $rel.TrimStart('/')
    $path = Join-Path $root $rel
    if (Test-Path -LiteralPath $path -PathType Container) { $path = Join-Path $path 'index.html' }
    if (Test-Path -LiteralPath $path -PathType Leaf) {
      $bytes = [System.IO.File]::ReadAllBytes($path)
      $ext = [System.IO.Path]::GetExtension($path).ToLower()
      if ($mime.ContainsKey($ext)) { $res.ContentType = $mime[$ext] }
      $res.Headers.Add('Access-Control-Allow-Origin','*')
      $res.Headers.Add('Cache-Control','no-cache, no-store, must-revalidate')
      $res.ContentLength64 = $bytes.Length
      $res.OutputStream.Write($bytes, 0, $bytes.Length)
    } else {
      $res.StatusCode = 404
      $msg = [System.Text.Encoding]::UTF8.GetBytes("404: $rel")
      $res.OutputStream.Write($msg, 0, $msg.Length)
    }
  } catch { try { $res.StatusCode = 500 } catch {} }
  finally { try { $res.OutputStream.Close() } catch {} }
}
