@echo off
chcp 65001 >nul
echo ========================================
echo FloXML Generator - Excel VBA Automation
echo ========================================
echo.
echo This script will:
echo 1. Open Excel with the modified template
echo 2. Run the VBA macro to generate FloXML
echo 3. Close Excel
echo.
echo Output will be saved to: c:\temp\test_materials.xml
echo.
pause

set EXCEL_FILE=D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\floxml_output\materials_modified.xlsm

echo Starting Excel...
start "" /wait "%EXCEL_FILE%"

echo.
echo ========================================
echo Done! Please check c:\temp\test_materials.xml
echo ========================================
pause
