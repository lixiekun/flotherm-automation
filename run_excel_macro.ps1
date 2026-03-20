# FloXML Generator - PowerShell Excel Automation
# Usage: powershell -ExecutionPolicy Bypass -File run_excel_macro.ps1 <excel_file> [macro_name]

param(
    [Parameter(Mandatory=$true)]
    [string]$ExcelFile,

    [string]$MacroName = ""
)

Write-Host "========================================"
Write-Host "FloXML Generator - Excel VBA Automation"
Write-Host "========================================"
Write-Host "Excel file: $ExcelFile"
Write-Host ""

try {
    # Create Excel object
    Write-Host "[1/3] Creating Excel object..."
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false

    # Open workbook
    Write-Host "[2/3] Opening Excel file..."
    $workbook = $excel.Workbooks.Open($ExcelFile)

    # Try to list and run macros
    Write-Host "[3/3] Checking VBA macros..."

    # Try different macro name patterns
    $macroPatterns = @(
        "CREATEMATERIALS",
        "CreateMaterials",
        "Module1.CREATEMATERIALS",
        "XML_Subs_FloCOREv11.CREATEMODEL",
        "CREATEMODEL",
        "CreateModel",
        "EXPORT",
        "Export"
    )

    if ($MacroName -ne "") {
        $macroPatterns = @($MacroName) + $macroPatterns
    }

    $success = $false
    foreach ($macro in $macroPatterns) {
        try {
            Write-Host "  Trying: $macro"
            $excel.Run($macro)
            Write-Host "  [OK] Macro '$macro' executed successfully!"
            $success = $true
            break
        } catch {
            # Continue to next macro
        }
    }

    if (-not $success) {
        Write-Host ""
        Write-Host "[INFO] Could not auto-detect macro name."
        Write-Host "[INFO] Please open Excel and press Alt+F8 to see available macros."
        Write-Host ""
        Write-Host "Common macro names to try:"
        foreach ($m in $macroPatterns) {
            Write-Host "  - $m"
        }
    }

    # Save and close
    Write-Host ""
    Write-Host "Saving and closing..."
    $workbook.Save()
    $workbook.Close()
    $excel.Quit()

    Write-Host ""
    Write-Host "[OK] Done!"
    Write-Host "========================================"

} catch {
    Write-Host "[ERROR] $($_.Exception.Message)"
    if ($excel) {
        try { $excel.Quit() } catch {}
    }
    exit 1
} finally {
    # Release COM objects
    if ($workbook) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) | Out-Null }
    if ($excel) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null }
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
