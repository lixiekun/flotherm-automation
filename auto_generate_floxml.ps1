# ========================================
# FloXML Auto Generator - PowerShell
# ========================================

param(
    [string]$ExcelFile = "D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\floxml_output\materials_modified.xlsm",
    [string]$OutputPath = "c:\temp\materials_output.xml"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FloXML Auto Generator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 方法1: 直接打开 Excel（如果有 Workbook_Open 事件会自动运行）
Write-Host "[Method 1] Opening Excel directly..." -ForegroundColor Yellow
Write-Host "Excel file: $ExcelFile"
Write-Host "Output will be saved to: $OutputPath"
Write-Host ""

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $true
    $excel.DisplayAlerts = $false

    Write-Host "[1/4] Opening workbook..."
    $workbook = $excel.Workbooks.Open($ExcelFile)

    # 尝试运行各种可能的宏名称
    Write-Host "[2/4] Attempting to run macros..."

    $macroNames = @(
        "Auto_Open",
        "Workbook_Open",
        "CREATEMATERIALS",
        "CREATEMODEL",
        "CreateMaterials",
        "CreateModel",
        "Module1.CREATEMATERIALS",
        "Module1.CREATEMODEL"
    )

    $macroRun = $false
    foreach ($macroName in $macroNames) {
        try {
            Write-Host "  Trying: $macroName"
            $excel.Run($macroName) | Out-Null
            Write-Host "  [SUCCESS] Macro '$macroName' executed!" -ForegroundColor Green
            $macroRun = $true
            break
        } catch {
            # Continue to next macro
        }
    }

    if (-not $macroRun) {
        Write-Host ""
        Write-Host "[INFO] No macro found. Please add Auto_Open to your Excel file:" -ForegroundColor Yellow
        Write-Host "  1. Open Excel and press Alt+F11"
        Write-Host "  2. Insert -> Module"
        Write-Host "  3. Add this code:"
        Write-Host ""
        Write-Host "     Sub Auto_Open()"
        Write-Host "         Call CREATEMATERIALS  ' or your macro name"
        Write-Host "     End Sub"
        Write-Host ""
    }

    # 等待一下让宏完成
    Write-Host "[3/4] Waiting for macro to complete..."
    Start-Sleep -Seconds 2

    # 保存并关闭
    Write-Host "[4/4] Saving and closing..."
    $workbook.Save()
    $workbook.Close()
    $excel.Quit()

    Write-Host ""
    Write-Host "[OK] Done!" -ForegroundColor Green
    Write-Host "Check output: $OutputPath"

} catch {
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    if ($excel) {
        try { $excel.Quit() } catch {}
    }
} finally {
    # 释放 COM 对象
    if ($workbook) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) | Out-Null }
    if ($excel) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null }
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}

Write-Host "========================================" -ForegroundColor Cyan
