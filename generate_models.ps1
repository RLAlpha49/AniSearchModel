param(
    [string]$StartModel
)

$startProcessing = $true

# Define dataset types
$datasetTypes = @("anime", "manga")

Get-Content models.txt | ForEach-Object {
    if ($_ -eq $StartModel) {
        $startProcessing = $true
    }

    if ($startProcessing) {
        foreach ($datasetType in $datasetTypes) {
            Write-Host "Generating embeddings for model: $_ on dataset: $datasetType"
            python sbert.py --model "$_" --type "$datasetType"
        }
    }
}