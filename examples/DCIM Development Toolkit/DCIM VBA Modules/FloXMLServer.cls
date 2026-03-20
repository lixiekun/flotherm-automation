VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "FloXMLServer"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Public Sub aThermal(xmldoc, tName As String, tPower As Double)
Dim tnode As MSXML2.IXMLDOMNode

If zAttribTypExist(xmldoc, "thermals") And Not zAttribExist(xmldoc, "thermal_att", tName) Then
Set tnode = xmldoc.SelectSingleNode("//thermals")
    With tnode
        .appendChild xmldoc.createElement("thermal_att")
        With .LastChild
            .appendChild xmldoc.createElement("name")
            .LastChild.Text = tName
            .appendChild xmldoc.createElement("power")
            .LastChild.Text = tPower
        End With
    End With
End If
End Sub
Public Function FileBaseName(Fullpath As String) As String
    Const ForReading = 1, ForWriting = 2, ForAppending = 8
    Dim fso
    Set fso = CreateObject("Scripting.FileSystemObject")
    FileBaseName = fso.getbasename(Fullpath)
End Function

Public Function FilePathOnly(Fullpath As String) As String
    Const ForReading = 1, ForWriting = 2, ForAppending = 8
    Dim ThisPath As String
    Dim fso
    Set fso = CreateObject("Scripting.FileSystemObject")
    ThisPath = fso.GetParentFolderName(Fullpath)
    If Right(ThisPath, 1) <> "\" Then ThisPath = ThisPath + "\"
    FilePathOnly = ThisPath
End Function
Function FileWithExt(Fullpath As String) As String
    Const ForReading = 1, ForWriting = 2, ForAppending = 8
    Dim fso
    Set fso = CreateObject("Scripting.FileSystemObject")
    FileWithExt = fso.GetFileName(Fullpath)
End Function
Public Function FileOrDirExists(sPathName As String) As Boolean
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

Public Function mBase_Assembly(PathToDirectory As String, Assy_name As String) As String
Open (PathToDirectory & Assy_name & ".xml") For Output As 1
Print #1, "<?xml version=" + Chr(34) + "1.0" + Chr(34) + " encoding=" + Chr(34) + "UTF-8" + Chr(34) + " standalone=" + Chr(34) + "no" + Chr(34) + " ?>"
Print #1, "<xml_case>"
Print #1, "<name>" + Assy_name + "</name>"
Print #1, "<attributes>"
Print #1, "</attributes>"
Print #1, "<geometry>"
Print #1, "</geometry>"
Print #1, "</xml_case>"
Close #1
mBase_Assembly = PathToDirectory & Assy_name & ".xml"
End Function
Public Sub gAssembly(xmldoc, assyName As String, Optional xcoord As Double = 0, Optional ycoord As Double = 0, Optional zcoord As Double = 0, _
                Optional aParent As String, Optional oIsHidden As Boolean)
    Dim assynode As MSXML2.IXMLDOMNode
    Dim gNode As MSXML2.IXMLDOMNode
    If Len(aParent) = 0 Then
        Set assynode = xmldoc.SelectSingleNode("//geometry")
    Else
        Set assynode = zFindAssyNode(xmldoc, aParent)
    End If
    With assynode
    .appendChild xmldoc.createElement("assembly")
        With .LastChild
            .appendChild xmldoc.createElement("name")
            .LastChild.Text = assyName
            If oIsHidden Then
                .appendChild xmldoc.createElement("hidden")
                .LastChild.Text = "true"
            End If
            .appendChild xmldoc.createElement("position")
            With .LastChild
                .appendChild xmldoc.createElement("x")
                .LastChild.Text = xcoord
                .appendChild xmldoc.createElement("y")
                .LastChild.Text = ycoord
                .appendChild xmldoc.createElement("z")
                .LastChild.Text = zcoord
            End With
        End With
    End With
End Sub
Public Sub gRack(xmldoc, sName As String, dPower As Double, dFlow_Value As Double, Optional xcoord As Double = 0, Optional ycoord As Double = 0, Optional zcoord As Double = 0, _
            Optional sFlow_Type As String = "volume_flow_rate", Optional bHidden As Boolean = False, Optional Assy As String)
    'supports volume_flow_rate, flow_rate_power, temperature_change
    'provide name of sSurfAttNm
    Dim cNode As MSXML2.IXMLDOMNode
    
    
    If Len(Assy) = 0 Then
        Set cNode = xmldoc.SelectSingleNode("//geometry")
    Else
        If Not zAssyExist(xmldoc, Assy) Then 'assembly doesn't exist
            Call gAssembly(xmldoc, Assy)
        End If
        Set cNode = zFindAssyNode(xmldoc, Assy)
    End If
 
        
    With cNode
    .appendChild xmldoc.createElement("rack")
        With .LastChild
            .appendChild xmldoc.createElement("name")
            .LastChild.Text = sName
            .appendChild xmldoc.createElement("position")
            With .LastChild
                .appendChild xmldoc.createElement("x")
                .LastChild.Text = xcoord
                .appendChild xmldoc.createElement("y")
                .LastChild.Text = ycoord
                .appendChild xmldoc.createElement("z")
                .LastChild.Text = zcoord
            End With
            .appendChild xmldoc.createElement("power_dissipation")
            .LastChild.Text = dPower
            .appendChild xmldoc.createElement("hidden")
            .LastChild.Text = LCase(bHidden)
            .appendChild xmldoc.createElement("flow_type")
            .LastChild.Text = sFlow_Type
            .appendChild xmldoc.createElement(sFlow_Type)
            .LastChild.Text = dFlow_Value
        End With
    End With
End Sub
Public Sub gRackSupplyExtract(xmldoc, sRackName As String, sSupplyExtractName As String, bIsSupply As Boolean, xSize As Double, ySize As Double, _
            Optional xcoord As Double = 0, Optional ycoord As Double = 0, Optional zcoord As Double = 0)
    'supports volume_flow_rate, flow_rate_power, temperature_change
    'provide name of sSurfAttNm
    Dim cNode As MSXML2.IXMLDOMNode
    Dim sSupply As String, sPlural As String
    
    sSupply = "extract"
    sPlural = "extracts"
    If bIsSupply Then
        sSupply = "supply"
        sPlural = "supplies"
    End If
    If xmldoc.SelectSingleNode("//rack[name=" + Chr(34) + sRackName + Chr(34) + "]/" + sPlural) Is Nothing Then
        Set cNode = xmldoc.SelectSingleNode("//rack[name=" + Chr(34) + sRackName + Chr(34) + "]")
        cNode.appendChild xmldoc.createElement(sPlural)
    End If
        Set cNode = xmldoc.SelectSingleNode("//rack[name=" + Chr(34) + sRackName + Chr(34) + "]/" + sPlural)
        
    With cNode
    .appendChild xmldoc.createElement(sSupply)
        With .LastChild
            .appendChild xmldoc.createElement("name")
            .LastChild.Text = sSupplyExtractName
            .appendChild xmldoc.createElement("position")
            With .LastChild
                .appendChild xmldoc.createElement("x")
                .LastChild.Text = xcoord
                .appendChild xmldoc.createElement("y")
                .LastChild.Text = ycoord
                .appendChild xmldoc.createElement("z")
                .LastChild.Text = zcoord
            End With
            .appendChild xmldoc.createElement("size")
            With .LastChild
                .appendChild xmldoc.createElement("x")
                .LastChild.Text = xSize
                .appendChild xmldoc.createElement("y")
                .LastChild.Text = ySize
            End With
            If bIsSupply Then 'free_area_ratio
                .appendChild xmldoc.createElement("free_area_ratio")
                .LastChild.Text = 1
            End If
        End With
    End With
End Sub

Public Sub gCuboid(xmldoc, cName As String, xSize As Double, ySize As Double, zSize As Double, _
            Optional xcoord As Double = 0, Optional ycoord As Double = 0, Optional zcoord As Double = 0, _
            Optional cMaterial As String, Optional cPower As Double, Optional thermAttr As String, _
            Optional Monitor_Pnt As Boolean, Optional sSurfAttFc As String = "all", _
            Optional sSurfAttNm As String, Optional Assy As String)
    'optional sSurfAttFc- supply:x_high, x_low,y_high,...,all
    'provide name of sSurfAttNm
    Dim cNode As MSXML2.IXMLDOMNode
    Dim mpx As Double, mpy As Double, mpz As Double
    
    
    If Len(Assy) = 0 Then
        Set cNode = xmldoc.SelectSingleNode("//geometry")
    Else
        If Not zAssyExist(xmldoc, Assy) Then 'assembly doesn't exist
            Call gAssembly(xmldoc, Assy)
        End If
        Set cNode = zFindAssyNode(xmldoc, Assy)
    End If
 
        
    With cNode
    .appendChild xmldoc.createElement("cuboid")
        With .LastChild
            .appendChild xmldoc.createElement("name")
            .LastChild.Text = cName
            .appendChild xmldoc.createElement("position")
            With .LastChild
                .appendChild xmldoc.createElement("x")
                .LastChild.Text = xcoord
                .appendChild xmldoc.createElement("y")
                .LastChild.Text = ycoord
                .appendChild xmldoc.createElement("z")
                .LastChild.Text = zcoord
            End With
            .appendChild xmldoc.createElement("size")
            With .LastChild
                .appendChild xmldoc.createElement("x")
                .LastChild.Text = xSize
                .appendChild xmldoc.createElement("y")
                .LastChild.Text = ySize
                .appendChild xmldoc.createElement("z")
                .LastChild.Text = zSize
            End With
            If Len(cMaterial) > 0 Then
                .appendChild xmldoc.createElement("material")
                .LastChild.Text = cMaterial
            End If
            If cPower <> 0 Or Len(thermAttr) <> 0 Then
                .appendChild xmldoc.createElement("thermal")
                If Len(thermAttr) > 0 Then
                    .LastChild.Text = thermAttr
                Else
                    '.LastChild.Text = cName + ": " + CStr(cPower) + "W"
                    .LastChild.Text = "Thermal: " + CStr(cPower) + "W"
                    Call aThermal(xmldoc, "Thermal: " + CStr(cPower) + "W", cPower)
                End If
            End If
            If Len(sSurfAttNm) > 0 Then
                .appendChild xmldoc.createElement(sSurfAttFc + "_surface")
                .LastChild.Text = sSurfAttNm
            End If
            If Monitor_Pnt = True Then
                mpx = xcoord + xSize / 2
                mpy = ycoord + ySize / 2
                mpz = zcoord + zSize / 2
                Call gMonitorPoint(xmldoc, cName + ":monitor", mpx, mpy, mpz, Assy)
            End If
        End With
    End With
End Sub

Public Sub gMonitorPoint(xmldoc, MPName As String, xcoord As Double, ycoord As Double, _
                zcoord As Double, Optional Assy As String)
    
    Dim mpNode As MSXML2.IXMLDOMNode
    If Len(Assy) = 0 Then
        Set mpNode = xmldoc.SelectSingleNode("//geometry")
    Else
        If Not zAssyExist(xmldoc, Assy) Then 'assembly doesn't exist
            Call gAssembly(xmldoc, Assy, , , , "")
        End If
        Set mpNode = zFindAssyNode(xmldoc, Assy)
    End If
    
    With mpNode
    .appendChild xmldoc.createElement("monitor_point")
        With .LastChild
            .appendChild xmldoc.createElement("name")
            .LastChild.Text = MPName
            .appendChild xmldoc.createElement("position")
            With .LastChild
                .appendChild xmldoc.createElement("x")
                .LastChild.Text = xcoord
                .appendChild xmldoc.createElement("y")
                .LastChild.Text = ycoord
                .appendChild xmldoc.createElement("z")
                .LastChild.Text = zcoord
            End With
        End With
    End With
   End Sub

Public Sub UpdateIOColor()
Dim lMatColor As Long, lOutletColor As Long, lInletColor As Long
Dim iOffset As Integer
    lMatColor = Sheet1.Range("$E$7").Interior.Color
    lOutletColor = RGB(207, 139, 139)
    lInletColor = RGB(221, 235, 247)

    If Sheet1.Range("N3").Value = "Open" Then
        Sheet1.Range("N4").Interior.Color = lOutletColor
    Else
        Sheet1.Range("N4").Interior.Color = lMatColor
    End If
    If Sheet1.Range("O3").Value = "Open" Then
        Sheet1.Range("O4").Interior.Color = lOutletColor
    Else
        Sheet1.Range("O4").Interior.Color = lMatColor
    End If
    If Sheet1.Range("P3").Value = "Open" Then
        Sheet1.Range("P4").Interior.Color = lOutletColor
    Else
        Sheet1.Range("P4").Interior.Color = lMatColor
    End If
    If Sheet1.Range("Q3").Value = "Open" Then
        Sheet1.Range("Q4").Interior.Color = lOutletColor
    Else
        Sheet1.Range("Q4").Interior.Color = lMatColor
    End If
    If Sheet1.Range("M13").Value = "Open" Then
        Sheet1.Range("M10").Interior.Color = lInletColor
    Else
        Sheet1.Range("M10").Interior.Color = lMatColor
    End If
    If Sheet1.Range("N13").Value = "Open" Then
        Sheet1.Range("N10").Interior.Color = lInletColor
    Else
        Sheet1.Range("N10").Interior.Color = lMatColor
    End If
    If Sheet1.Range("O13").Value = "Open" Then
        Sheet1.Range("O10").Interior.Color = lInletColor
    Else
        Sheet1.Range("O10").Interior.Color = lMatColor
    End If
    If Sheet1.Range("P13").Value = "Open" Then
        Sheet1.Range("P10").Interior.Color = lInletColor
    Else
        Sheet1.Range("P10").Interior.Color = lMatColor
    End If

End Sub
Public Sub UpdateServerColor()
Dim lMatColor As Long


    lMatColor = Sheet1.Range("$E$7").Interior.Color
    With Sheet1.Range("Inlet").Borders
        .Color = lMatColor
        .Weight = xlMedium
    End With
    With Sheet1.Range("Outlet").Borders
        .Color = lMatColor
        .Weight = xlMedium
    End With
    ActiveSheet.Shapes.Range(Array("Uright")).Select
    With Selection.ShapeRange.Line
        .ForeColor.RGB = RGB(lMatColor Mod 256, (lMatColor \ 256) Mod 256, lMatColor \ 65536)
    End With
    ActiveSheet.Shapes.Range(Array("Lright")).Select
    With Selection.ShapeRange.Line
        .ForeColor.RGB = RGB(lMatColor Mod 256, (lMatColor \ 256) Mod 256, lMatColor \ 65536)
    End With
    ActiveSheet.Shapes.Range(Array("Uleft")).Select
    With Selection.ShapeRange.Line
        .ForeColor.RGB = RGB(lMatColor Mod 256, (lMatColor \ 256) Mod 256, lMatColor \ 65536)
    End With
    ActiveSheet.Shapes.Range(Array("Lleft")).Select
    With Selection.ShapeRange.Line
        .ForeColor.RGB = RGB(lMatColor Mod 256, (lMatColor \ 256) Mod 256, lMatColor \ 65536)
    End With
    Call UpdateIOColor
End Sub
Public Sub CopyBackUp(sBkUpShtNm As String)
    If Not WorksheetExists(sBkUpShtNm) Then Sheets.Add.Name = sBkUpShtNm
    Sheets(sBkUpShtNm).Range("A1:Q25").Value = Sheet1.Range("A1:Q25").Value
    'Sheets(sBkUpShtNm).Visible = False
End Sub
Public Function WorksheetExists(ByVal WorksheetName As String) As Boolean
    On Error Resume Next
    WorksheetExists = (Sheets(WorksheetName).Name <> "")
    On Error GoTo 0
End Function
Public Function ConvertTemperature(sInputVal As Double, sInputUnit As String, sOutputUnit) As Double
sInputUnit = Right(sInputUnit, 1)
sOutputUnit = Right(sOutputUnit, 1)
Select Case sInputUnit
    Case "C"
        Select Case sOutputUnit
            Case "C"
                ConvertTemperature = sInputVal
            Case "F"
                ConvertTemperature = 32 + 9 / 5 * sInputVal
            Case "K"
                ConvertTemperature = sInputVal + 273.15
            Case "R"
                ConvertTemperature = (sInputVal + 273.15) * 9 / 5
        End Select
    Case "F"
        Select Case sOutputUnit
            Case "C"
                ConvertTemperature = (sInputVal - 32) * 5 / 9
            Case "F"
                ConvertTemperature = sInputVal
            Case "K"
                ConvertTemperature = (sInputVal + 459.67) * 5 / 9
            Case "R"
                ConvertTemperature = sInputVal + 459.67
        End Select
    Case "K"
        Select Case sOutputUnit
            Case "C"
                ConvertTemperature = sInputVal - 273.15
            Case "F"
                ConvertTemperature = 9 / 5 * sInputVal - 459.67
            Case "K"
                ConvertTemperature = sInputVal
            Case "R"
                ConvertTemperature = sInputVal * 9 / 5
        End Select
    Case "R"
        Select Case sOutputUnit
            Case "C"
                ConvertTemperature = (sInputVal - 491.67) * 5 / 9
            Case "F"
                ConvertTemperature = sInputVal - 459.67
            Case "K"
                ConvertTemperature = sInputVal * 5 / 9
            Case "R"
                ConvertTemperature = sInputVal
        End Select
End Select
End Function
Public Function UnitMltPlr(sInputUnit As String, sOutputUnit) As Double

Select Case sInputUnit
    Case "m"
        Select Case sOutputUnit
            Case "mm"
                UnitMltPlr = 1000
            Case "m"
                UnitMltPlr = 1
            Case "micron"
                UnitMltPlr = 1000000
            Case "in"
                UnitMltPlr = 1 / 0.0254
            Case "mil"
                UnitMltPlr = 1 / 0.0000254
            Case "U"
                UnitMltPlr = 1 / (1.75 * 0.0254)
        End Select

    Case "mm"
        Select Case sOutputUnit
            Case "mm"
                UnitMltPlr = 1
            Case "m"
                UnitMltPlr = 0.001
            Case "micron"
                UnitMltPlr = 1000
            Case "in"
                UnitMltPlr = 1 / 25.4
            Case "mil"
                UnitMltPlr = 1000 / 25.4
            Case "U"
                UnitMltPlr = 1 / (1.75 * 25.4)
        End Select
    Case "micron"
        Select Case sOutputUnit
            Case "mm"
                UnitMltPlr = 0.001
            Case "m"
                UnitMltPlr = 0.000001
            Case "micron"
                UnitMltPlr = 1
            Case "in"
                UnitMltPlr = 0.001 / 25.4
            Case "mil"
                UnitMltPlr = 10 / 25.4
            Case "U"
                UnitMltPlr = 1 / (1.75 * 25400)
        End Select
    Case "in"
        Select Case sOutputUnit
            Case "mm"
                UnitMltPlr = 25.4
            Case "m"
                UnitMltPlr = 0.0254
            Case "micron"
                UnitMltPlr = 25400
            Case "in"
                UnitMltPlr = 1
            Case "mil"
                UnitMltPlr = 1000
            Case "U"
                UnitMltPlr = 1 / 1.75
        End Select
    Case "mil"
        Select Case sOutputUnit
            Case "mm"
                UnitMltPlr = 0.0254
            Case "m"
                UnitMltPlr = 0.0000254
            Case "micron"
                UnitMltPlr = 25.4
            Case "in"
                UnitMltPlr = 0.001
            Case "mil"
                UnitMltPlr = 1
            Case "U"
                UnitMltPlr = 1 / (1.75 * 1000)
        End Select
    Case "U"
        Select Case sOutputUnit
            Case "mm"
                UnitMltPlr = 1.75 * 25.4
            Case "m"
                UnitMltPlr = 1.75 * 0.0254
            Case "micron"
                UnitMltPlr = 1.75 * 25400
            Case "in"
                UnitMltPlr = 1.75
            Case "mil"
                UnitMltPlr = 1.75 * 1000
            Case "U"
                UnitMltPlr = 1
        End Select
    Case "W"
        Select Case sOutputUnit
            Case "W"
                UnitMltPlr = 1
            Case "kW"
                UnitMltPlr = 1 / 1000
            Case "BTU/hr"
                UnitMltPlr = 3.40952
        End Select
    Case "kW"
        Select Case sOutputUnit
            Case "W"
                UnitMltPlr = 1000
            Case "kW"
                UnitMltPlr = 1
            Case "BTU/hr"
                UnitMltPlr = 3.40952 * 1000
        End Select
    Case "BTU/hr"
        Select Case sOutputUnit
            Case "W"
                UnitMltPlr = 1 / 3.40952
            Case "kW"
                UnitMltPlr = 1 / (3.40952 * 1000)
            Case "BTU/hr"
                UnitMltPlr = 1
        End Select
    Case "cfm"
        Select Case sOutputUnit
            Case "cfm"
                UnitMltPlr = 1
            Case "l/s"
                UnitMltPlr = (12 * 2.54) ^ 3 / (60 * CLng(1000))
            Case "m^3/s"
                UnitMltPlr = (12 * 0.0254) ^ 3 / 60
            Case "m^3/hr"
                UnitMltPlr = (12 * 0.0254) ^ 3 * 60
        End Select
    Case "l/s"
        Select Case sOutputUnit
            Case "cfm"
                UnitMltPlr = 1 / ((12 * 2.54) ^ 3 / (60 * CLng(1000)))
            Case "l/s"
                UnitMltPlr = 1
            Case "m^3/s"
                UnitMltPlr = 0.001
            Case "m^3/hr"
                UnitMltPlr = 0.001 * 60 * 60
        End Select
    Case "m^3/s"
        Select Case sOutputUnit
            Case "cfm"
                UnitMltPlr = 1 / ((12 * 0.0254) ^ 3 / 60)
            Case "l/s"
                UnitMltPlr = 1000
            Case "m^3/s"
                UnitMltPlr = 1
            Case "m^3/hr"
                UnitMltPlr = 60 * 60
        End Select
    Case "m^3/hr"
        Select Case sOutputUnit
            Case "cfm"
                UnitMltPlr = 1 / ((12 * 0.0254) ^ 3 * 60)
            Case "l/s"
                UnitMltPlr = 1000 / (60 * 60)
            Case "m^3/s"
                UnitMltPlr = 1 / (60 * 60)
            Case "m^3/hr"
                UnitMltPlr = 1
        End Select
    Case "cfm/kW"
        Select Case sOutputUnit
            Case "cfm/kW"
                UnitMltPlr = 1
            Case "(l/s)/kW"
                UnitMltPlr = (12 * 2.54) ^ 3 / (60 * CLng(1000))
            Case "(m^3/s)/W"
                UnitMltPlr = (12 * 0.0254) ^ 3 / 60 / CLng(1000)
            Case "(m^3/s)/kW"
                UnitMltPlr = (12 * 0.0254) ^ 3 / 60
        End Select
    Case "(l/s)/kW"
        Select Case sOutputUnit
            Case "cfm/kW"
                UnitMltPlr = (60 * CLng(1000)) / ((12 * 2.54) ^ 3)
            Case "(l/s)/kW"
                UnitMltPlr = 1
            Case "(m^3/s)/W"
                UnitMltPlr = 0.000001
            Case "(m^3/s)/kW"
                UnitMltPlr = 0.001
        End Select
    Case "(m^3/s)/W"
        Select Case sOutputUnit
            Case "cfm/kW"
                UnitMltPlr = 1 / ((12 * 0.0254) ^ 3 / 60) * CLng(1000)
            Case "(l/s)/kW"
                UnitMltPlr = (12 * 2.54) ^ 3 / (60 * CLng(1000))
            Case "(m^3/s)/W"
                UnitMltPlr = 1
            Case "(m^3/s)/kW"
                UnitMltPlr = 1000
        End Select
    Case "(m^3/s)/kW"
        Select Case sOutputUnit
            Case "cfm/kW"
                UnitMltPlr = 1 / ((12 * 0.0254) ^ 3 / 60)
            Case "(l/s)/kW"
                UnitMltPlr = 1000
            Case "(m^3/s)/W"
                UnitMltPlr = 0.001
            Case "(m^3/s)/kW"
                UnitMltPlr = 1
        End Select
End Select
End Function
Public Sub aSurface(xmldoc, sSrfNm As String, Optional dEmissivity As Double = 1, _
                    Optional dStoSRes As Double, Optional vRGBColor As Variant)

Dim sNode As MSXML2.IXMLDOMNode

    If dEmissivity < 0 Or dEmissivity > 1 Then dEmissivity = 1

    If zAttribTypExist(xmldoc, "surfaces") And Not zAttribExist(xmldoc, "surface_att", sSrfNm) Then
        Set sNode = xmldoc.SelectSingleNode("//surfaces")
    End If

    With sNode
        .appendChild xmldoc.createElement("surface_att")
        With .LastChild
            .appendChild xmldoc.createElement("name")
            .LastChild.Text = sSrfNm
            .appendChild xmldoc.createElement("emissivity")
            .LastChild.Text = dEmissivity
            If dStoSRes > 0 Then
                .appendChild xmldoc.createElement("rsurf_solid")
                .LastChild.Text = dStoSRes
            End If
        End With
        If Not IsMissing(vRGBColor) Then
            With .LastChild
                .appendChild xmldoc.createElement("display_settings")
                With .LastChild
                    .appendChild xmldoc.createElement("color")
                    With .LastChild
                        .appendChild xmldoc.createElement("red")
                        .LastChild.Text = vRGBColor(0) / 255
                        .appendChild xmldoc.createElement("green")
                        .LastChild.Text = vRGBColor(1) / 255
                        .appendChild xmldoc.createElement("blue")
                        .LastChild.Text = vRGBColor(2) / 255
                    End With
                End With
                With .LastChild
                .appendChild xmldoc.createElement("shininess")
                .LastChild.Text = "0.5"
                .appendChild xmldoc.createElement("brightness")
                .LastChild.Text = "0.5"
                End With
            End With
        End If
    End With
End Sub
Private Function zAttribExist(xmldoc, AttribTyp As String, AttribNm As String) As Boolean
Dim aNode As MSXML2.IXMLDOMNode
Dim aNodelst As MSXML2.IXMLDOMNodeList
zAttribExist = False
    Set aNodelist = xmldoc.SelectNodes("//" + AttribTyp)
    If Not (aNodelist Is Nothing) Then
        For Each aNode In aNodelist
            If aNode.FirstChild.Text = AttribNm Then
                zAttribExist = True
                Exit Function
            End If
        Next aNode
    End If
End Function
Private Function zAttribTypExist(xmldoc, AttribTyp As String) As Boolean
Dim tnode As MSXML2.IXMLDOMNode
If xmldoc.SelectSingleNode("//" + AttribTyp) Is Nothing Then
    Set tnode = xmldoc.SelectSingleNode("//attributes")
    tnode.appendChild xmldoc.createElement(AttribTyp)
End If
zAttribTypExist = True
End Function
Private Function zAssyExist(xmldoc, assyNm As String) As Boolean
'check to see if attribute has been created
Dim aNode As MSXML2.IXMLDOMNode
Dim aNodelst As MSXML2.IXMLDOMNodeList
    zAssyExist = False
             Set aNodelist = xmldoc.getElementsByTagName("assembly")
             For Each aNode In aNodelist
                If aNode.FirstChild.FirstChild.Text = assyNm Then
                zAssyExist = True
                End If
             Next
End Function
Private Function zFindAssyNode(xmldoc, assyName As String) As IXMLDOMNode
'Finds assembly node and determines if there is a geometry node within
'If there is no geometry node then it creates it

Dim assynode As MSXML2.IXMLDOMNode
Dim assynodes As MSXML2.IXMLDOMNodeList

    Set zFindAssyNode = xmldoc.SelectSingleNode("//geometry")

    Set assynodes = xmldoc.getElementsByTagName("assembly")
    For Each assynode In assynodes
       If assynode.FirstChild.Text = assyName Then
           If Not assynode.LastChild.nodeName = "geometry" Then
               assynode.appendChild xmldoc.createElement("geometry")
           End If
           Set zFindAssyNode = assynode.LastChild 'should be geometry node
       Exit Function
       End If
    Next
End Function

