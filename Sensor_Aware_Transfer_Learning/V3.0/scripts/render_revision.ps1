$ErrorActionPreference = 'Stop'
$folder = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../submission'))
$renderer = 'E:/projects/ENose_cleanup_archive_2026-09-20/Sensor_Aware_Transfer_Learning/v2.2/revision_artifacts/render_tools/LibreOffice/program/soffice.com'
$profilePath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../.render_profile'))
$profileUri = ([System.Uri]$profilePath).AbsoluteUri
foreach ($name in @('IEEE_Revision_3.0_Clean','IEEE_Revision_3.0_Highlighted','SUPPLEMENTARY_EVIDENCE','RESPONSE_TO_REVIEWERS')) {
    & $renderer "-env:UserInstallation=$profileUri" --headless --convert-to pdf --outdir $folder (Join-Path $folder ($name + '.docx'))
    if ($LASTEXITCODE -ne 0) { throw "Rendering failed: $name" }
}
