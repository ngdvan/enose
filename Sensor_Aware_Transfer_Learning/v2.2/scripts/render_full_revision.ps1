param([string]$Name = 'IEEE_Full_Revision_Clean')
$ErrorActionPreference = 'Stop'
$folder = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../author_review/full_revision_001'))
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.Options.UpdateLinksAtOpen = $false
$word.Options.CheckSpellingAsYouType = $false
$word.Options.CheckGrammarAsYouType = $false
$word.WordBasic.FilePrintSetup('Microsoft Print to PDF', [Type]::Missing, [Type]::Missing, 1)
try {
    $sourcePath = Join-Path $folder ($Name + '.docx')
    $pdfPath = Join-Path $folder ($Name + '.pdf')
    Write-Output "Opening $Name"
    $doc = $word.Documents.Open($sourcePath, $false, $true, $false)
    try {
        Write-Output "Exporting $Name"
        $doc.ExportAsFixedFormat($pdfPath, 17)
        Write-Output "Exported $Name"
    }
    finally { $doc.Close(0) }
}
finally {
    $word.Quit()
    [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word)
}
