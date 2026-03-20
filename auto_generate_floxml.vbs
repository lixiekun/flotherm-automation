' ========================================
' FloXML Auto Generator
' 自动打开 Excel 并运行宏生成 FloXML
' ========================================

Option Explicit

Dim objExcel, objWorkbook
Dim excelFile, outputFile

' 配置
excelFile = "D:\Program Files\Siemens\SimcenterFlotherm\2504\flotherm-automation\floxml_output\materials_modified.xlsm"
outputFile = "c:\temp\materials_output.xml"

WScript.Echo "========================================"
WScript.Echo "FloXML Auto Generator"
WScript.Echo "========================================"
WScript.Echo ""

' 创建 Excel 对象
On Error Resume Next
Set objExcel = CreateObject("Excel.Application")

If Err.Number <> 0 Then
    WScript.Echo "[ERROR] Cannot create Excel object"
    WScript.Echo "Error: " & Err.Description
    WScript.Quit 1
End If
On Error GoTo 0

' 配置 Excel
objExcel.Visible = True
objExcel.DisplayAlerts = False

' 打开工作簿
WScript.Echo "[1/3] Opening Excel file..."
On Error Resume Next
Set objWorkbook = objExcel.Workbooks.Open(excelFile)

If Err.Number <> 0 Then
    WScript.Echo "[ERROR] Cannot open file"
    WScript.Echo "Error: " & Err.Description
    objExcel.Quit
    WScript.Quit 1
End If
On Error GoTo 0

' 尝试运行 Auto_Open
WScript.Echo "[2/3] Running Auto_Open..."
On Error Resume Next
objExcel.Run "Auto_Open"
If Err.Number <> 0 Then
    ' 如果 Auto_Open 不存在，尝试 Workbook_Open
    Err.Clear
    objExcel.Run "Workbook_Open"
End If
If Err.Number <> 0 Then
    ' 尝试直接运行宏
    Err.Clear
    objExcel.Run "CREATEMATERIALS"
End If
If Err.Number <> 0 Then
    Err.Clear
    objExcel.Run "CREATEMODEL"
End If

' 等待宏完成
WScript.Sleep 3000

' 保存并关闭
WScript.Echo "[3/3] Saving and closing..."
objWorkbook.Save
objWorkbook.Close
objExcel.Quit

WScript.Echo ""
WScript.Echo "[OK] Done!"
WScript.Echo "Check output: " & outputFile
WScript.Echo "========================================"

' 清理
Set objWorkbook = Nothing
Set objExcel = Nothing
