$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$abstract = 'Self-supervised transfer learning can reduce the number of labeled examples needed to calibrate a multigas electronic nose, although its benefits vary across gases and experimental conditions. We investigate this approach by first training a shared temporal encoder to reconstruct masked sensor responses without concentration labels, then fine-tuning it on a small set of labeled concentration pairs. Across ten random seeds, transfer learning reduces mean absolute error relative to training from scratch by 13.9% for NH3, 21.5% for H2, 27.5% for CO, and 25.7% for ethylene. These results come from six held-out identifier partitions for NH3/H2 using a predefined early-response window and three rolling chronological folds for CO/ethylene. To express label efficiency more directly, we also compare models trained with different calibration budgets. Using 10 labeled pairs, including validation labels, fine-tuning achieves approximately the NH3 and ethylene errors of scratch training with 20 pairs and a lower mean CO error, but does not match its H2 performance. Sensor identity and cross-sensor attention contribute unevenly, with NH3 showing the weakest evidence of benefit. Transfer also improves concentration regression in two of three future drift partitions when gas identity is known. Overall, the findings support selective use of self-supervised transfer for label-efficient calibration within the same sensor system. However, the proposed model does not outperform the strongest full-budget baseline on any target, and the NH3/H2 evaluation does not establish generalization across acquisition days.'
$utf8 = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText((Join-Path $root 'submission/ABSTRACT.md'), "# Self-Supervised Transfer Learning for Label-Efficient Multigas Electronic Nose Calibration`n`n$abstract`n`nWord count (whitespace-delimited): 230`n", $utf8)
$builder = Join-Path $PSScriptRoot 'build_revision.py'
$src = [IO.File]::ReadAllText($builder)
$src = [regex]::Replace($src, '(?s)ABSTRACT=\(.*?\)\r?\nassert', "ABSTRACT='$abstract'`nassert")
[IO.File]::WriteAllText($builder, $src, $utf8)
Add-Type -AssemblyName System.IO.Compression.FileSystem
foreach ($name in @('IEEE_Revision_3.0_Clean','IEEE_Revision_3.0_Highlighted','RESPONSE_TO_REVIEWERS')) {
  $path = Join-Path $root "submission/$name.docx"
  $zip = [IO.Compression.ZipFile]::Open($path, 'Update')
  try {
    $entry = $zip.GetEntry('word/document.xml')
    $reader = [IO.StreamReader]::new($entry.Open())
    [xml]$xml = $reader.ReadToEnd(); $reader.Dispose()
    $ns = [Xml.XmlNamespaceManager]::new($xml.NameTable)
    $ns.AddNamespace('w','http://schemas.openxmlformats.org/wordprocessingml/2006/main')
    foreach ($p in $xml.SelectNodes('//w:p',$ns)) {
      $nodes = $p.SelectNodes('.//w:t',$ns)
      $text = ($nodes | ForEach-Object { $_.InnerText }) -join ''
      if ($name -like 'IEEE*' -and $text.StartsWith('Abstract')) {
        $nodes[0].InnerText = 'Abstract' + [char]0x2014 + ' ' + $abstract
        for ($i=1;$i -lt $nodes.Count;$i++) { $nodes[$i].InnerText = '' }
      }
      if ($name -eq 'RESPONSE_TO_REVIEWERS') {
        foreach ($t in $nodes) { $t.InnerText = $t.InnerText.Replace('184 whitespace-delimited words','230 whitespace-delimited words').Replace('leads with the primary gains against scratch','presents the approach and primary gains against scratch in connected prose') }
      }
    }
    $entry.Delete(); $new = $zip.CreateEntry('word/document.xml')
    $stream = $new.Open(); $xml.Save($stream); $stream.Dispose()
  } finally { $zip.Dispose() }
}
foreach ($rel in @('submission/RESPONSE_TO_REVIEWERS.md','scripts/build_response.py')) {
 $path = Join-Path $root $rel
 $text = [IO.File]::ReadAllText($path).Replace('184 whitespace-delimited words','230 whitespace-delimited words').Replace('leads with the primary gains against scratch','presents the approach and primary gains against scratch in connected prose')
 [IO.File]::WriteAllText($path,$text,$utf8)
}
Write-Output 'Updated abstract source, builders, manuscript pair and response: 230 words.'
