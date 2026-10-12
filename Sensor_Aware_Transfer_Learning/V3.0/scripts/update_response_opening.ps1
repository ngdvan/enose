$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$opening = 'We sincerely thank the reviewers for their in-depth assessment and thoughtful comments. Their substantial contributions have helped us strengthen both the study and its presentation. We would welcome the opportunity to acknowledge these contributions in the article, if the journal permits.'
$utf8 = [Text.UTF8Encoding]::new($false)
foreach ($rel in @('submission/RESPONSE_TO_REVIEWERS.md','scripts/build_response.py')) {
 $path = Join-Path $root $rel
 $text = [IO.File]::ReadAllText($path)
 $text = $text.Replace('We thank the reviewer for the detailed assessment.', $opening)
 [IO.File]::WriteAllText($path,$text,$utf8)
}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$path = Join-Path $root 'submission/RESPONSE_TO_REVIEWERS.docx'
$zip = [IO.Compression.ZipFile]::Open($path,'Update')
try {
 $entry=$zip.GetEntry('word/document.xml')
 $reader=[IO.StreamReader]::new($entry.Open()); [xml]$xml=$reader.ReadToEnd(); $reader.Dispose()
 $ns=[Xml.XmlNamespaceManager]::new($xml.NameTable); $ns.AddNamespace('w','http://schemas.openxmlformats.org/wordprocessingml/2006/main')
 $changed=$false
 foreach ($p in $xml.SelectNodes('//w:p',$ns)) {
  $nodes=$p.SelectNodes('.//w:t',$ns)
  $text=($nodes | ForEach-Object {$_.InnerText}) -join ''
  if ($text.StartsWith('We thank the reviewer for the detailed assessment.')) {
   $nodes[0].InnerText=$text.Replace('We thank the reviewer for the detailed assessment.',$opening)
   for ($i=1;$i -lt $nodes.Count;$i++) {$nodes[$i].InnerText=''}
   $changed=$true
  }
 }
 if (-not $changed) {throw 'Original introduction not found'}
 $entry.Delete();$new=$zip.CreateEntry('word/document.xml');$stream=$new.Open();$xml.Save($stream);$stream.Dispose()
} finally {$zip.Dispose()}
$renderer='E:/projects/ENose_cleanup_archive_2026-09-20/Sensor_Aware_Transfer_Learning/v2.2/revision_artifacts/render_tools/LibreOffice/program/soffice.com'
$profileUri=([Uri](Join-Path $root '.response_opening_profile')).AbsoluteUri
& $renderer "-env:UserInstallation=$profileUri" --headless --convert-to pdf --outdir (Join-Path $root 'submission') $path
if ($LASTEXITCODE -ne 0) {throw 'PDF conversion failed'}
