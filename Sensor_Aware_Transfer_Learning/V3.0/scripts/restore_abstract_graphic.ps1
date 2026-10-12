$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
Add-Type -AssemblyName System.IO.Compression.FileSystem
$w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
$a='http://schemas.openxmlformats.org/drawingml/2006/main'
$r='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
function Read-XmlEntry($zip) {
 $reader=[IO.StreamReader]::new($zip.GetEntry('word/document.xml').Open())
 try { [xml]$xml=$reader.ReadToEnd();return ,$xml } finally {$reader.Dispose()}
}
function Namespaces($xml) {
 $ns=[Xml.XmlNamespaceManager]::new($xml.NameTable)
 $ns.AddNamespace('w',$w);$ns.AddNamespace('a',$a);$ns.AddNamespace('r',$r)
 return ,$ns
}
$base=[IO.Compression.ZipFile]::OpenRead((Join-Path $root '../v2.2/author_review/full_revision_001/IEEE_Full_Revision_Clean.docx'))
try {$source=Read-XmlEntry $base} finally {$base.Dispose()}
$sn=Namespaces $source
$blip=$source.SelectSingleNode('//a:blip[@r:embed="rId8"]',$sn)
if ($null -eq $blip) {throw 'V2.2 abstract graphic not found'}
$object=$blip
while ($object.ParentNode.LocalName -ne 'p') {$object=$object.ParentNode}
foreach ($name in @('IEEE_Revision_3.0_Clean','IEEE_Revision_3.0_Highlighted')) {
 $path=Join-Path $root "submission/$name.docx"
 $zip=[IO.Compression.ZipFile]::Open($path,'Update')
 try {
  $xml=Read-XmlEntry $zip;$ns=Namespaces $xml
  $paragraph=$null
  foreach ($p in $xml.SelectNodes('//w:p',$ns)) {
   $text=($p.SelectNodes('.//w:t',$ns) | ForEach-Object {$_.InnerText}) -join ''
   if ($text.StartsWith('Abstract')) {$paragraph=$p;break}
  }
  if ($null -eq $paragraph) {throw 'Abstract not found'}
  if ($null -eq $paragraph.SelectSingleNode('.//a:blip[@r:embed="rId8"]',$ns)) {
   $copy=$xml.ImportNode($object,$true)
   # Preserve the anchored drawing but do not duplicate any text from its run.
   foreach ($t in @($copy.SelectNodes('.//w:t',$ns))) {$t.ParentNode.RemoveChild($t) | Out-Null}
   $firstRun=$paragraph.SelectSingleNode('w:r',$ns)
   $paragraph.InsertBefore($copy,$firstRun) | Out-Null
  }
  $zip.GetEntry('word/document.xml').Delete()
  $stream=$zip.CreateEntry('word/document.xml').Open();$xml.Save($stream);$stream.Dispose()
 } finally {$zip.Dispose()}
}
$renderer='E:/projects/ENose_cleanup_archive_2026-09-20/Sensor_Aware_Transfer_Learning/v2.2/revision_artifacts/render_tools/LibreOffice/program/soffice.com'
$profileUri=([Uri](Join-Path $root '.graphic_restore_profile')).AbsoluteUri
foreach ($name in @('IEEE_Revision_3.0_Clean','IEEE_Revision_3.0_Highlighted')) {
 & $renderer "-env:UserInstallation=$profileUri" --headless --convert-to pdf --outdir (Join-Path $root 'submission') (Join-Path $root "submission/$name.docx")
 if ($LASTEXITCODE -ne 0) {throw "Rendering failed: $name"}
}
