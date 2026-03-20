VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "FloSCRIPT_Rack"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Function sThisSrvrLibPath(sSrvrNm As String, sDelim As String) As String
Dim rSrv As Range
For Each rSrv In Range("LibraryServers")
    If rSrv.Value = sSrvrNm Then
    Debug.Print CStr(Sheet2.Cells(rSrv.Row, 1).Value)
        sThisSrvrLibPath = CStr(Sheet2.Cells(rSrv.Row, 2).Value) + sDelim + sSrvrNm
        Exit Function
    End If
Next rSrv
End Function

Sub Add_PromoteToRoot(xmldoc, sSrcGeomNm As String, sDelim As String)
Dim FSnode As MSXML2.IXMLDOMNode, CGnode As MSXML2.IXMLDOMNode, iNameAttr As IXMLDOMAttribute
Dim vAssyPath As Variant

    If Right(sSrcGeom, Len(sDelim)) = sDelim Then sSrcGeom = Left(sSrcGeom, Len(sSrcGeom) - Len(sDelim))
    If Left(sSrcGeom, Len(sDelim)) = sDelim Then sSrcGeom = Right(sSrcGeom, Len(sSrcGeom) - Len(sDelim))
    
    vAssyPath = Split(sSrcGeom, sDelim)
    Set FSnode = xmldoc.SelectSingleNode("//xml_log_file")
    Set iNameAttr = xmldoc.createAttribute("row")
    Set FSnode = FSnode.appendChild(xmldoc.createElement("move_geometry_node"))
        iNameAttr.Value = "0"
        FSnode.Attributes.setNamedItem iNameAttr
    Set CGnode = FSnode.appendChild(xmldoc.createElement("geometry_name"))
    Set iNameAttr = xmldoc.createAttribute("name")
    Set CGnode = CGnode.appendChild(xmldoc.createElement("geometry"))
        iNameAttr.Value = "Root Assembly"
        CGnode.Attributes.setNamedItem iNameAttr

    Set iNameAttr = xmldoc.createAttribute("name")
    Set CGnode = CGnode.appendChild(xmldoc.createElement("geometry"))
        iNameAttr.Value = sSrcGeomNm
        CGnode.Attributes.setNamedItem iNameAttr
    
    Set FSnode = FSnode.appendChild(xmldoc.createElement("new_parent"))
    Set iNameAttr = xmldoc.createAttribute("name")
    Set FSnode = FSnode.appendChild(xmldoc.createElement("geometry"))
        iNameAttr.Value = "Root Assembly"
        FSnode.Attributes.setNamedItem iNameAttr

End Sub
Sub Add_modify_geometry(xmldoc, sproperty_name As String, snew_value As String, sSrcGeom As String, sDelim As String)
Dim FSnode As MSXML2.IXMLDOMNode, CGnode As MSXML2.IXMLDOMNode, iNameAttr As IXMLDOMAttribute
Dim vAssyPath As Variant

    If Right(sSrcGeom, Len(sDelim)) = sDelim Then sSrcGeom = Left(sSrcGeom, Len(sSrcGeom) - Len(sDelim))
    If Left(sSrcGeom, Len(sDelim)) = sDelim Then sSrcGeom = Right(sSrcGeom, Len(sSrcGeom) - Len(sDelim))
    
    vAssyPath = Split(sSrcGeom, sDelim)
    Set FSnode = xmldoc.SelectSingleNode("//xml_log_file")
    Set CGnode = FSnode.appendChild(xmldoc.createElement("modify_geometry"))
    Set iNameAttr = xmldoc.createAttribute("new_value")
        iNameAttr.Value = snew_value
        CGnode.Attributes.setNamedItem iNameAttr
    Set iNameAttr = xmldoc.createAttribute("property_name")
        iNameAttr.Value = sproperty_name
        CGnode.Attributes.setNamedItem iNameAttr
    Set CGnode = CGnode.appendChild(xmldoc.createElement("geometry_name"))
    Set iNameAttr = xmldoc.createAttribute("name")
    Set CGnode = CGnode.appendChild(xmldoc.createElement("geometry"))
        iNameAttr.Value = vAssyPath(0)
        CGnode.Attributes.setNamedItem iNameAttr

    For i = 1 To UBound(vAssyPath) - 1 Step 2
        Set iNameAttr = xmldoc.createAttribute("name")
        Set CGnode = CGnode.appendChild(xmldoc.createElement("geometry"))
        iNameAttr.Value = vAssyPath(i)
        CGnode.Attributes.setNamedItem iNameAttr
        Set iNameAttr = xmldoc.createAttribute("position_in_parent")
        'Set CGnode = CGnode.appendChild(xmldoc.createElement("geometry"))
        iNameAttr.Value = vAssyPath(i + 1)
        CGnode.Attributes.setNamedItem iNameAttr
    Next i


End Sub

Sub Add_create_geometry(xmldoc, sgeometry_type As String, sSrcGeom As String, sDelim As String)
Dim FSnode As MSXML2.IXMLDOMNode, CGnode As MSXML2.IXMLDOMNode, iNameAttr As IXMLDOMAttribute
Dim vAssyPath As Variant

    If Right(sSrcGeom, Len(sDelim)) = sDelim Then sSrcGeom = Left(sSrcGeom, Len(sSrcGeom) - Len(sDelim))
    If Left(sSrcGeom, Len(sDelim)) = sDelim Then sSrcGeom = Right(sSrcGeom, Len(sSrcGeom) - Len(sDelim))
    
    vAssyPath = Split(sSrcGeom, sDelim)
    Set FSnode = xmldoc.SelectSingleNode("//xml_log_file")
    Set CGnode = FSnode.appendChild(xmldoc.createElement("create_geometry"))
    Set iNameAttr = xmldoc.createAttribute("geometry_type")
        iNameAttr.Value = sgeometry_type
        CGnode.Attributes.setNamedItem iNameAttr
    Set CGnode = CGnode.appendChild(xmldoc.createElement("source_geometry"))
    Set iNameAttr = xmldoc.createAttribute("name")
    Set CGnode = CGnode.appendChild(xmldoc.createElement("geometry"))
        iNameAttr.Value = vAssyPath(0)
        CGnode.Attributes.setNamedItem iNameAttr

    For i = 1 To UBound(vAssyPath) - 1 Step 2
        Set iNameAttr = xmldoc.createAttribute("name")
        Set CGnode = CGnode.appendChild(xmldoc.createElement("geometry"))
        iNameAttr.Value = vAssyPath(i)
        CGnode.Attributes.setNamedItem iNameAttr
        Set iNameAttr = xmldoc.createAttribute("position_in_parent")
        'Set CGnode = CGnode.appendChild(xmldoc.createElement("geometry"))
        iNameAttr.Value = vAssyPath(i + 1)
        CGnode.Attributes.setNamedItem iNameAttr
    Next i

End Sub
Public Sub Add_load_from_library(xmldoc, sPathToLibrary As String, sDelim As String, _
             Optional sPathToAssy As String)
Dim FSnode As MSXML2.IXMLDOMNode, LFLnode As MSXML2.IXMLDOMNode, iNameAttr As IXMLDOMAttribute
    'Dim Node_Used As IXMLDOMElement
Dim vLibPath As Variant, vAssyPath As Variant

    If Right(sPathToAssy, Len(sDelim)) = sDelim Then sPathToAssy = Left(sPathToAssy, Len(sPathToAssy) - Len(sDelim))
    If Left(sPathToAssy, Len(sDelim)) = sDelim Then sPathToAssy = Right(sPathToAssy, Len(sPathToAssy) - Len(sDelim))
    If Right(sPathToLibrary, Len(sDelim)) = sDelim Then sPathToLibrary = Left(sPathToLibrary, Len(sPathToLibrary) - Len(sDelim))
    If Left(sPathToLibrary, Len(sDelim)) = sDelim Then sPathToLibrary = Right(sPathToLibrary, Len(sPathToLibrary) - Len(sDelim))
    
    vLibPath = Split(sPathToLibrary, sDelim)
    vAssyPath = Split(sPathToAssy, sDelim)
    Set FSnode = xmldoc.SelectSingleNode("//xml_log_file")
    Set LFLnode = FSnode.appendChild(xmldoc.createElement("load_from_library"))
    If Len(sPathToAssy) <> 0 Then
        Set FSnode = LFLnode.appendChild(xmldoc.createElement("geometry_name"))
        Set FSnode = FSnode.appendChild(xmldoc.createElement("geometry"))
        Set iNameAttr = xmldoc.createAttribute("name")
            iNameAttr.Value = vAssyPath(0)
            FSnode.Attributes.setNamedItem iNameAttr
    
        For i = 1 To UBound(vAssyPath) - 1 Step 2
            Set iNameAttr = xmldoc.createAttribute("name")
            Set FSnode = FSnode.appendChild(xmldoc.createElement("geometry"))
            iNameAttr.Value = vAssyPath(i)
            FSnode.Attributes.setNamedItem iNameAttr
            Set iNameAttr = xmldoc.createAttribute("position_in_parent")
            iNameAttr.Value = vAssyPath(i + 1)
            FSnode.Attributes.setNamedItem iNameAttr
        Next i
    End If
    Set FSnode = LFLnode.appendChild(xmldoc.createElement("library_name"))
    'Set FSnode = xmldoc.SelectSingleNode("//library_name[last()]") '(//element[@name='D'])[last()]
        For i = 0 To UBound(vLibPath)
            Set iNameAttr = xmldoc.createAttribute("name")
            Set FSnode = FSnode.appendChild(xmldoc.createElement("library"))
            If vLibPath(i) = "Libraries" Then
                iNameAttr.Value = "Library"
            Else
                iNameAttr.Value = vLibPath(i)
            End If
            FSnode.Attributes.setNamedItem iNameAttr
        Next i
End Sub
Private Sub Add_XML_Attribute(xmldoc, Node_Used As IXMLDOMElement, Attribute_Name As String, Attribute_Value As Variant)
    Dim Attribute_holder As IXMLDOMAttribute
    Set Attribute_holder = xmldoc.createAttribute(Attribute_Name)
    Attribute_holder.NodeValue = Attribute_Value
    Node_Used.setAttributeNode Attribute_holder
End Sub
Public Function FilePathOnly(Fullpath As String) As String
    Const ForReading = 1, ForWriting = 2, ForAppending = 8
    Dim ThisPath As String
    Dim fso
    Set fso = CreateObject("Scripting.FileSystemObject")
    ThisPath = fso.GetParentFolderName(Fullpath)
    If Right(ThisPath, 1) <> "\" Then ThisPath = ThisPath + "\"
    FilePathOnly = ThisPath
End Function

Sub UpdateServerLibrary()
Dim oFSC As New FloSCRIPT_Rack
Dim sLibPath As String, vLibPrts As Variant
Dim sFloSuitePath As String
Dim rVpath As Range, bPrevPath As Boolean
Dim sCurPath As String
Dim lLstRow As Long, lnLstRow As Long, bInLst As Boolean

sLibPath = Sheet1.Range("O6").Value
sFloSuitePath = Sheet1.Range("O4").Value
If Right(sFloSuitePath, 1) <> "\" Then sFloSuitePath = sFloSuitePath + "\"
If Left(sLibPath, 1) = "." Then
    sLibPath = Right(sLibPath, Len(sLibPath) - 1)
    If Left(sLibPath, 1) <> "\" Then sLibPath = "\" + sLibPath
    sLibPath = sFloSuitePath + "flotherm\flocentral\Libraries" + sLibPath
End If
    vLibPrts = oFSC.FTLibToArray(sLibPath)
If Not IsEmpty(vLibPrts) Then
    With Sheet2
        sCurPath = oFSC.sLibraryPath(sLibPath, "/*/")
        lLstRow = .Range("C" & .Rows.Count).End(xlUp).Row
        For i = 1 To UBound(vLibPrts)
        bInLst = False
            For j = 1 To lLstRow
                If .Cells(j + 2, 3).Value = vLibPrts(i) Then bInLst = True
           Next j
            If bInLst = False Then
                nlLstRow = .Range("C" & .Rows.Count).End(xlUp).Row
               .Cells(nlLstRow + 1, 2).Value = sCurPath
               .Cells(nlLstRow + 1, 3).Value = vLibPrts(i)
               .Cells(nlLstRow + 1, 4).Value = oFSC.iSrvrUHght(CStr(vLibPrts(i)))
            End If
        Next i
        Range("LibraryServers").Resize(.Range("C" & .Rows.Count).End(xlUp).Row - 2, 1).Name = "LibraryServers"
        Range("ValidatedPaths").Resize(.Range("C" & .Rows.Count).End(xlUp).Row - 2, 1).Name = "ValidatedPaths"
    End With
End If

End Sub

Function CreateBaseFloSCRIPT(PathToFloSCRIPT As String) As String
Open (PathToFloSCRIPT) For Output As 1
Print #1, "<?xml version=" + Chr(34) + "1.0" + Chr(34) + " encoding=" + Chr(34) + "UTF-8" + Chr(34) + " ?>"
Print #1, "<xml_log_file version=" + Chr(34) + "1.0" + Chr(34) + " > "
Print #1, "<!--Copyright 2015 Mentor Graphics Corporation-->"
Print #1, "<!--All Rights Reserved-->"
Print #1, "<!--THIS WORK CONTAINS TRADE SECRET AND PROPRIETARY-->"
Print #1, "<!--INFORMATION WHICH IS THE PROPERTY OF MENTOR-->"
Print #1, "<!--GRAPHICS CORPORATION OR ITS LICENSORS AND IS-->"
Print #1, "<!--SUBJECT TO LICENSE TERMS.-->"
Print #1, "</xml_log_file>"
Close #1
CreateBaseFloSCRIPT = PathToFloSCRIPT
End Function
Function sLibraryPath(ByVal sLibFTPath As String, sStrDelim As String) As String
Const ForReading = 1, ForWriting = 2, ForAppending = 8
Dim sSum As String
Dim fso As Object
Dim InFile As Object, oSubF As Object, oF As Object, OFname As Object
Dim sStr As String

sStr = sLibFTPath
Set fso = CreateObject("Scripting.FileSystemObject")
If Right(sStr, 1) = "\" Then sStr = Left(sStr, Len(sStr) - 1)
Do While FileOrDirExists(sStr + "\library.cfg")

    Set InFile = fso.OpenTextFile(sStr + "\library.cfg", ForReading)
    sSum = InFile.readline + sStrDelim + sSum
    InFile.Close
    sStr = fso.GetParentFolderName(sStr)
Loop
sSum = Left(sSum, Len(sSum) - Len(sStrDelim))
sLibraryPath = sSum
End Function

Public Function FTLibToArray(ByVal sLibFilePath As String) As Variant
    Const ForReading = 1, ForWriting = 2, ForAppending = 8
    Dim fso As Object
    Dim vLib() As Variant
    Dim InFile As Object
    Dim sLibString As String, sline As String
    Dim iCnt As Integer
    Dim sAddDelim As String
    Dim sUseBlnkTxt As String
    
    sUseBlnkTxt = "Use Blank"
    
    If Right(sLibFilePath, 1) <> "\" Then sLibFilePath = sLibFilePath + "\"
    sLibFilePath = sLibFilePath + "library.catalog"
    
    If Not FileOrDirExists(sLibFilePath) Then
        MsgBox "No library models found in the provided directory"
        Sheet1.Range("O6").Select
        Exit Function
    End If
    
    sAddDelim = "\*\"
    iCnt = 0
    Set fso = CreateObject("Scripting.FileSystemObject")
    
    Set InFile = fso.OpenTextFile(sLibFilePath, ForReading) '.readall
    Do Until InFile.atendofstream
        sline = InFile.readline
        sLibString = sLibString + sAddDelim + sline
        iCnt = iCnt + 1
        sline = InFile.readline
        sline = InFile.readline
    Loop
    InFile.Close
    If iCnt > 0 Then
        ReDim vLib(1 To iCnt + 2)
        vLib(1) = "Open Slot"
        vLib(2) = sUseBlnkTxt
        For iCnt = 3 To UBound(vLib)
        vLib(iCnt) = Split(sLibString, sAddDelim)(iCnt - 2)
        Next iCnt
        FTLibToArray = vLib
    Else
        MsgBox "No library models found in the provided directory"
        Sheet1.Range("O6").Select
        Exit Function
    End If
End Function
Public Sub ArrayDataToSheet(InputArray As Variant, NameOfSheet As String, StrtRowNum As Integer, StrtColNum As Integer, RngNm As String)
Dim rIs1D As Range
Dim iCnt As Integer
iCnt = 1
If RangeExists(RngNm) Then Range(RngNm).Clear

Sheets(NameOfSheet).Range(Cells(StrtRowNum, StrtColNum).Address).Name = RngNm

    If ArrayDim(InputArray) = 1 Then
        Range(RngNm).Resize(UBound(InputArray, 1), 1).Name = RngNm
        Range(RngNm).ClearContents
        For Each rIs1D In Range(RngNm)
            rIs1D.Value = InputArray(iCnt)
            iCnt = iCnt + 1
        Next rIs1D
    Else
        Range(RngNm).Resize(UBound(InputArray, 1), UBound(InputArray, 2)).Name = RngNm
        Range(RngNm).ClearContents
        Range(RngNm).Value = InputArray
    End If
    
End Sub
Function RangeExists(R As String) As Boolean
    Dim Test As Range
    On Error Resume Next
    Set Test = Range(R)
    RangeExists = Err.Number = 0
End Function
Function ArrayDim(v As Variant) As Long
 'Returns number of dimensions of an array or 0 for
 'an undimensioned array or -1 if no array at all.
 'Reverse("moc.LiborPlus.www") V0.1 PB 10-May-2010
 Dim i As Long
 ArrayDim = -1
 If Not IsArray(v) Then Exit Function
 On Error Resume Next
Err.Clear
 Do While IsNumeric(UBound(v, i + 1))
     If Err.Number <> 0 Then Exit Do
     i = i + 1
 Loop
 ArrayDim = i
 End Function
Function FileOrDirExists(sPathName As String) As Boolean
    Dim retval As Integer
    On Error Resume Next
    retval = GetAttr(sPathName)
    
    Select Case Err.Number
    Case Is = 0
        FileOrDirExists = True
    Case Else
        FileOrDirExists = False
    End Select
    On Error GoTo 0
End Function
Public Function GetLibFolder(sFloSuite As String) As String
Dim strPath As String
Dim fldr As FileDialog
Dim sItem As String
If Right(sFloSuite, 1) <> "\" Then sFloSuite = sFloSuite + "\"
strPath = sFloSuite + "flotherm\flocentral\Libraries"
Set fldr = Application.FileDialog(msoFileDialogFolderPicker)
With fldr
    .Title = "Select a Folder"
    .AllowMultiSelect = False
    .InitialFileName = strPath
    If .Show <> -1 Then GoTo NextCode
    sItem = .SelectedItems(1)
End With
NextCode:
GetLibFolder = sItem
Set fldr = Nothing
End Function
Sub UpdateLayout(ByVal rRng As Range)

Dim iCnt As Integer, iCol As Integer, iRow As Integer, sThisSrvrNm As String
Dim rSrvr As Range, iThisHeight As Integer

vCOpen = RGB(255, 255, 205)
vCBlck = RGB(220, 235, 245)
vCBlnk = RGB(215, 215, 215)
vCSrvr = RGB(220, 235, 245)
For Each rSrvr In rRng.Rows
    With Sheet1.Cells(rSrvr.Row, 5).Interior
        If rSrvr.Cells(1, 1).Value = "Open Slot" Then
            .Color = vCOpen
        ElseIf rSrvr.Cells(1, 1).Value = "" Then
            rSrvr.Cells(1, 1).Value = "Open Slot"
        ElseIf InStr(1, LCase(rSrvr.Cells(1, 1).Value), "blank") Then
            .Color = vCBlnk
        Else
            .Color = vCSrvr
        End If
        .Pattern = xlSolid
    End With
    Sheet1.Cells(rSrvr.Row, 5).NumberFormat = "General"
Next rSrvr

For Each rSrvr In rRng.Rows
    sThisSrvrNm = rSrvr.Cells(1, 1).Value
    If bIsServer(sThisSrvrNm) Then
        iThisHeight = iSrvrUHght(sThisSrvrNm)
        For i = 1 To iThisHeight - 1
        If (rSrvr.Row - i) < 4 Then Exit For
            With Sheet1.Cells(rSrvr.Row - i, 5).Interior
                .Color = vCBlck
                .Pattern = xlGray8
                .PatternColorIndex = xlAutomatic
                .TintAndShade = 0
                .PatternTintAndShade = 0
            End With
            Sheet1.Cells(rSrvr.Row - i, 5).NumberFormat = ";;;"

        Next i
    End If
Next rSrvr
End Sub
Function iSrvrUHght(sSrvrNm As String) As Integer
Dim sStr As String, iInt As Integer
iInt = InStr(1, sSrvrNm, "U")
If Not iInt > 1 Then
    iSrvrUHght = 1
    Exit Function
End If
sStr = Mid(sSrvrNm, iInt - 1, 1)
If IsNumeric(sStr) Then
    iSrvrUHght = CInt(sStr)
Else
    iSrvrUHght = 1
End If
End Function
Function bIsServer(sSrvrNm As String) As Boolean
Dim rSrvr As Range
bIsServer = False

If Len(sSrvrNm) < 1 Then bIsServer = False: Exit Function
If InStr(1, LCase(sSrvrNm), "blank") Then bIsServer = False: Exit Function
For Each rSrvr In Range("LibraryServers")
     If rSrvr.Value = sSrvrNm Then bIsServer = True: Exit Function
Next rSrvr
End Function
Public Sub PlayFloscript(flosuite_path As String, floscript_path As String)
    Dim myPath As String, myFile As String, mynewFile As String, strArgs As String, sStartupSuffix As String
    Dim oShell As Object
    'Run the new FloSCRIPT
    Set oShell = CreateObject("Wscript.Shell")
    sStartupSuffix = "\flotherm\WinXP\bin\flotherm.bat"
    strArgs = flosuite_path & sStartupSuffix
    If Dir(strArgs, vbDirectory) = vbNullString Then
        MsgBox "FloTHERM directory does not exist"
    Else
        strArgs = Chr(34) + strArgs + Chr(34) + " -f \" + Chr(34) + floscript_path + "\" + Chr(34)
        oShell.Run strArgs, 0, False
        'True to wait until shell command finishes before proceeding
        '0-Windows style hidden
    End If
End Sub

