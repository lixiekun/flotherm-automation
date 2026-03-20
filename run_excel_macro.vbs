' FloXML Generator - Excel VBA Automation
' Usage: cscript run_excel_macro.vbs <excel_file> <macro_name>

Option Explicit

Dim objExcel, objWorkbook, excelFile, macroName

' Get arguments
If WScript.Arguments.Count < 2 Then
    WScript.Echo "Usage: cscript run_excel_macro.vbs <excel_file> <macro_name>"
    WScript.Quit 1
End If

excelFile = WScript.Arguments(0)
macroName = WScript.Arguments(1)

WScript.Echo "========================================"
WScript.Echo "FloXML Generator - Excel VBA Automation"
WScript.Echo "========================================"
WScript.Echo "Excel file: " & excelFile
WScript.Echo "Macro name: " & macroName
WScript.Echo ""

' Create Excel object
On Error Resume Next
Set objExcel = CreateObject("Excel.Application")

If Err.Number <> 0 Then
    WScript.Echo "[ERROR] Cannot create Excel object: " & Err.Description
    WScript.Quit 1
End If
On Error GoTo 0

' Configure Excel
objExcel.Visible = False
objExcel.DisplayAlerts = False

' Open workbook
WScript.Echo "[1/3] Opening Excel file..."
On Error Resume Next
Set objWorkbook = objExcel.Workbooks.Open(excelFile)

If Err.Number <> 0 Then
    WScript.Echo "[ERROR] Cannot open file: " & Err.Description
    objExcel.Quit
    WScript.Quit 1
End If
On Error GoTo 0

' Run macro
WScript.Echo "[2/3] Running macro: " & macroName & "..."
On Error Resume Next
objExcel.Run macroName

If Err.Number <> 0 Then
    WScript.Echo "[ERROR] Macro failed: " & Err.Description
    objWorkbook.Close False
    objExcel.Quit
    WScript.Quit 1
End If
On Error GoTo 0

' Save and close
WScript.Echo "[3/3] Saving and closing..."
objWorkbook.Save
objWorkbook.Close
objExcel.Quit

WScript.Echo ""
WScript.Echo "[OK] Done!"
WScript.Echo "========================================"

' Cleanup
Set objWorkbook = Nothing
Set objExcel = Nothing
