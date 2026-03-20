VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "DC_Class"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Public Sub LoadToFT(flosuite_path As String, PathToPDML_XML As String)
Dim strArgs As String, sStartupSuffix As String
Dim oShell As Object

    If Right(flosuite_path, 1) = "\" Then flosuite_path = Left(flosuite_path, Len(flosuite_path) - 1)

    Set oShell = CreateObject("Wscript.Shell")
    sStartupSuffix = "\flotherm\WinXP\bin\flotherm.bat"
    strArgs = flosuite_path
    strArgs = strArgs & sStartupSuffix
    If Dir(strArgs, vbDirectory) = vbNullString Then
        MsgBox "FloTHERM directory does not exist"
    End If
    strArgs = Chr(34) + strArgs + Chr(34) + " -p \" + Chr(34) + PathToPDML_XML + "\" + Chr(34)
oShell.Run strArgs, 0, True
End Sub

Public Sub gFloorTile(xmldoc, sName As String, Xsz As Double, Ysz As Double, dPrcntOpen As Double, Optional bStrtFlow As Boolean = True, _
        Optional xcoord As Double = 0, Optional ycoord As Double = 0, Optional zcoord As Double = 0, Optional bActive As Boolean = True, _
        Optional bHidden As Boolean = False, Optional Assy As String)
    'supports volume_flow_rate, flow_rate_power, temperature_change
    'provide name of sSurfAttNm
    Dim cNode As MSXML2.IXMLDOMNode

vRot = Array(0, 0, 1, 1, 0, 0, 0, 1, 0)
    
    If Len(Assy) = 0 Then
        Set cNode = xmldoc.SelectSingleNode("//geometry")
    Else
        If Not zAssyExist(xmldoc, Assy) Then 'assembly doesn't exist
            Call gAssembly(xmldoc, Assy)
        End If
        Set cNode = zFindAssyNode(xmldoc, Assy)
    End If
 
        
    With cNode
    .appendChild xmldoc.createElement("perforated_plate")
        With .LastChild
            .appendChild xmldoc.createElement("name")
            .LastChild.Text = sName
            .appendChild xmldoc.createElement("active")
            .LastChild.Text = LCase(CStr(bActive))
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
                .LastChild.Text = Xsz
                .appendChild xmldoc.createElement("y")
                .LastChild.Text = Ysz
            End With
            .appendChild xmldoc.createElement("orientation")
            With .LastChild
                .appendChild xmldoc.createElement("local_x")
                With .LastChild
                    .appendChild xmldoc.createElement("i")
                    .LastChild.Text = vRot(0)
                    .appendChild xmldoc.createElement("j")
                    .LastChild.Text = vRot(1)
                    .appendChild xmldoc.createElement("k")
                    .LastChild.Text = vRot(2)
                End With
                .appendChild xmldoc.createElement("local_y")
                 With .LastChild
                    .appendChild xmldoc.createElement("i")
                    .LastChild.Text = vRot(3)
                    .appendChild xmldoc.createElement("j")
                    .LastChild.Text = vRot(4)
                    .appendChild xmldoc.createElement("k")
                    .LastChild.Text = vRot(5)
                End With
                .appendChild xmldoc.createElement("local_z")
                With .LastChild
                .appendChild xmldoc.createElement("i")
                    .LastChild.Text = vRot(6)
                    .appendChild xmldoc.createElement("j")
                    .LastChild.Text = vRot(7)
                    .appendChild xmldoc.createElement("k")
                    .LastChild.Text = vRot(8)
                End With
            End With
            .appendChild xmldoc.createElement("hole_type")
                    .LastChild.Text = "round"
            .appendChild xmldoc.createElement("coverage")
            With .LastChild
                .appendChild xmldoc.createElement("defined_coverage")
                .LastChild.Text = dPrcntOpen
            End With
'
'            .appendChild xmldoc.createElement("power_dissipation")
'            .LastChild.Text = dPower
'            .appendChild xmldoc.createElement("hidden")
'            .LastChild.Text = LCase(bHidden)
'            .appendChild xmldoc.createElement("flow_type")
'            .LastChild.Text = sFlow_Type
'            .appendChild xmldoc.createElement(sFlow_Type)
'            .LastChild.Text = dFlow_Value
        End With
    End With
End Sub

Public Sub gCooler(xmldoc, sName As String, dTSupply As Double, dFlow_Value As Double, Optional xcoord As Double = 0, Optional ycoord As Double = 0, Optional zcoord As Double = 0, _
             Optional bActive As Boolean = True, Optional Assy As String)
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
    .appendChild xmldoc.createElement("cooler")
        With .LastChild
            .appendChild xmldoc.createElement("name")
            .LastChild.Text = sName
            .appendChild xmldoc.createElement("active")
            .LastChild.Text = LCase(CStr(bActive))
            .appendChild xmldoc.createElement("position")
            With .LastChild
                .appendChild xmldoc.createElement("x")
                .LastChild.Text = xcoord
                .appendChild xmldoc.createElement("y")
                .LastChild.Text = ycoord
                .appendChild xmldoc.createElement("z")
                .LastChild.Text = zcoord
            End With
            .appendChild xmldoc.createElement("airflow_type")
            .LastChild.Text = "fixed"
            .appendChild xmldoc.createElement("flow_rate")
            .LastChild.Text = dFlow_Value
            .appendChild xmldoc.createElement("temperature_set_point")
            .LastChild.Text = dTSupply
            .appendChild xmldoc.createElement("temperature_set_point_location")
            .LastChild.Text = "supply"
        End With
    End With
End Sub
Public Sub gRack(xmldoc, sName As String, dPower As Double, dFlow_Value As Double, Optional xcoord As Double = 0, Optional ycoord As Double = 0, Optional zcoord As Double = 0, _
            Optional sFlow_Type As String = "volume_flow_rate", Optional bActive As Boolean = True, Optional bHidden As Boolean = False, Optional Assy As String)
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
            .appendChild xmldoc.createElement("active")
            .LastChild.Text = LCase(CStr(bActive))
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
            Optional xcoord As Double = 0, Optional ycoord As Double = 0, Optional zcoord As Double = 0, _
            Optional bRotCW90 As Boolean)
    'supports volume_flow_rate, flow_rate_power, temperature_change
    'provide name of sSurfAttNm
    Dim cNode As MSXML2.IXMLDOMNode
    Dim sSupply As String, sPlural As String
    
    If bRotCW90 Then
        vRot = Array(0, 0, 1, 0, 1, 0, -1, 0, 0)
    Else
        vRot = Array(1, 0, 0, 0, 1, 0, 0, 0, 1)
    End If
   
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
            .appendChild xmldoc.createElement("orientation")
            With .LastChild
                .appendChild xmldoc.createElement("local_x")
                With .LastChild
                    .appendChild xmldoc.createElement("i")
                    .LastChild.Text = vRot(0)
                    .appendChild xmldoc.createElement("j")
                    .LastChild.Text = vRot(1)
                    .appendChild xmldoc.createElement("k")
                    .LastChild.Text = vRot(2)
                End With
                .appendChild xmldoc.createElement("local_y")
                 With .LastChild
                    .appendChild xmldoc.createElement("i")
                    .LastChild.Text = vRot(3)
                    .appendChild xmldoc.createElement("j")
                    .LastChild.Text = vRot(4)
                    .appendChild xmldoc.createElement("k")
                    .LastChild.Text = vRot(5)
                End With
                .appendChild xmldoc.createElement("local_z")
                With .LastChild
                .appendChild xmldoc.createElement("i")
                    .LastChild.Text = vRot(6)
                    .appendChild xmldoc.createElement("j")
                    .LastChild.Text = vRot(7)
                    .appendChild xmldoc.createElement("k")
                    .LastChild.Text = vRot(8)
                End With
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
Public Sub gCoolerSupplyExtract(xmldoc, sCoolerName As String, sSupplyExtractName As String, bIsSupply As Boolean, xSize As Double, ySize As Double, _
            Optional xcoord As Double = 0, Optional ycoord As Double = 0, Optional zcoord As Double = 0, _
            Optional bRotCWx90 As Boolean)
    'supports volume_flow_rate, flow_rate_power, temperature_change
    'provide name of sSurfAttNm
    Dim cNode As MSXML2.IXMLDOMNode
    Dim sSupply As String, sPlural As String
    
    If bRotCWx90 Then
        vRot = Array(1, 0, 0, 0, 0, 1, 0, -1, 0)
    Else
        vRot = Array(1, 0, 0, 0, 1, 0, 0, 0, 1)
    End If

    sSupply = "extract"
    sPlural = "extracts"
    If bIsSupply Then
        sSupply = "supply"
        sPlural = "supplies"
    End If
    If xmldoc.SelectSingleNode("//cooler[name=" + Chr(34) + sCoolerName + Chr(34) + "]/" + sPlural) Is Nothing Then
        Set cNode = xmldoc.SelectSingleNode("//cooler[name=" + Chr(34) + sCoolerName + Chr(34) + "]")
        cNode.appendChild xmldoc.createElement(sPlural)
    End If
        Set cNode = xmldoc.SelectSingleNode("//cooler[name=" + Chr(34) + sCoolerName + Chr(34) + "]/" + sPlural)
        
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
            .appendChild xmldoc.createElement("orientation")
            With .LastChild
                .appendChild xmldoc.createElement("local_x")
                With .LastChild
                    .appendChild xmldoc.createElement("i")
                    .LastChild.Text = vRot(0)
                    .appendChild xmldoc.createElement("j")
                    .LastChild.Text = vRot(1)
                    .appendChild xmldoc.createElement("k")
                    .LastChild.Text = vRot(2)
                End With
                .appendChild xmldoc.createElement("local_y")
                 With .LastChild
                    .appendChild xmldoc.createElement("i")
                    .LastChild.Text = vRot(3)
                    .appendChild xmldoc.createElement("j")
                    .LastChild.Text = vRot(4)
                    .appendChild xmldoc.createElement("k")
                    .LastChild.Text = vRot(5)
                End With
                .appendChild xmldoc.createElement("local_z")
                With .LastChild
                .appendChild xmldoc.createElement("i")
                    .LastChild.Text = vRot(6)
                    .appendChild xmldoc.createElement("j")
                    .LastChild.Text = vRot(7)
                    .appendChild xmldoc.createElement("k")
                    .LastChild.Text = vRot(8)
                End With
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

Sub UpdateLayout(ByVal Target As Range)
Dim iCnt As Integer, iCol As Integer, iRow As Integer
Dim rRack As Range
Dim iOffset As Integer
Dim bIsActive As Boolean

With Range("DC_Racks")
    For iCnt = 1 To .Areas.Count
        If .Areas(iCnt).Cells(1).value = "" Then
            bIsActive = False
        Else
            bIsActive = True
        End If
        Select Case .Areas(iCnt).Cells(1).Column
            Case 9, 22, 35
                iOffset = 3
            Case 16, 29, 42
                iOffset = -2
        End Select
        iRow = .Cells.Areas(iCnt).Cells(1).Row
        iCol = iOffset + .Cells.Areas(iCnt).Cells(1).Column
        
        If bIsActive Then
            Sheet1.Cells(iRow, iCol).Interior.Color = RGB(255, 255, 205)
        Else
            Sheet1.Cells(iRow, iCol).Interior.Color = RGB(255, 255, 255)
            .Cells.Areas(iCnt).Cells(1).Interior.Color = RGB(255, 255, 255)
        End If
    Next iCnt
End With
End Sub
Function BuildRoomModel(sDCname As String, sXMLPath As String, dTamb As Double, dRoom_szX As Double, dRoom_szY As Double, dRoom_szZ As Double, _
 Optional bRaisedFloor As Boolean = True, Optional dRaisedFloorHeight As Double = 0.6) As String

Dim dRmYloc As Double
    
    dTamb = dTamb + 273.15
    dRmYloc = 0
    If bRaisedFloor Then dRmYloc = 0 - dRaisedFloorHeight
    
Open (sXMLPath) For Output As 1
    Call write_header(sDCname)
        Call start_model_inputs
            Call turbulence_setup(1, 2, 0, 0, 0, 0)
            Call gravity_setup(1, 2, 0, 0, 0, 9.81)
            Call global_setup(101325, dTamb, dTamb, 0, 0, 0, 0, 0, 0, 0)
    Call end_model_inputs
    Call start_solver_inputs
        'Call overall_control_setup(1500, 1, 0.2, 45, 200, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0.2, 0, 0)
        Call overall_control_setup(1500, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.2, 0, 0)
    Call end_solver_inputs
    Call start_grid_inputs
        Call system_grid_setup(0.005, 1, 0.2, 0.002, 1, 0.1, 0.005, 1, 0.2, 0, 0, 0, 0, 0, 0)
    Call end_grid_inputs
    Call start_attributes
        Call start_materials
            Call create_material("Steel", 50, 50, 50, 7800, 480, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            Call create_material("Concrete", 0.19, 0.19, 0.19, 600, 1000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            Call create_material("Chipboard", 0.15, 0.15, 0.15, 800, 2093, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        Call end_materials
        Call start_ambients
            Call create_ambient("Exterior_Temp", 0, dTamb, dTamb, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0000000001, 0.0000000001, 0)
        Call end_ambients
        Call start_fluids
            Call create_fluid("Air", 0, 0.0261, 0, 0, 0, 0.0000184, 0, 0, 0, 1.19, 1005, 0.00333, 0, 0)
        Call end_fluids
    Call end_attributes
    Call start_geometry
    'room_definition
    notes = 0
    Call build_assembly("Room architecture", 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
    Call build_enclosure("Room", 0, dRmYloc, 0, dRoom_szX, dRoom_szY, dRoom_szZ, 0.2, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, "Concrete", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
    If bRaisedFloor Then
        Call build_cuboid("Raised floor", 0, 0, 0, dRoom_szX, 0.0254, dRoom_szZ, 1, 0, 0, 0, 1, 0, 0, 0, 1, 2, 0, "Chipboard", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
    End If
    Call end_assembly
    Call build_assembly("Floor Tiles", 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
    Call end_assembly
    Call build_assembly("Vent System", 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
    Call end_assembly
    Call build_assembly("Equipment", 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
    Call end_assembly
Call end_geometry
Call build_domain(0, dRmYloc, 0, dRoom_szX, dRoom_szY, dRoom_szZ, "Exterior_Temp", "Exterior_Temp", "Exterior_Temp", "Exterior_Temp", "Exterior_Temp", "Exterior_Temp", 0, 0, 0, 0, 0, 0, "Air", 0)
Call write_footer
Close #1

BuildRoomModel = sXMLPath
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
Public Sub gAssembly(xmldoc, assyName As String, Optional xcoord As Double = 0, Optional ycoord As Double = 0, Optional zcoord As Double = 0, _
                Optional aParent As String, Optional oIsHidden As Boolean, Optional iCWRotY As Integer)
    Dim assynode As MSXML2.IXMLDOMNode
    Dim gNode As MSXML2.IXMLDOMNode
    
    vRot = Array(1, 0, 0, 0, 1, 0, 0, 0, 1)
    Select Case iCWRotY
        Case 90
            vRot = Array(0, 0, -1, 0, 1, 0, -1, 0, 0)
        Case 180
            vRot = Array(-1, 0, 0, 0, 1, 0, 0, 0, -1)
        Case 270
            vRot = Array(0, 0, 1, 0, 1, 0, 1, 0, 0)
    End Select
    
    
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
                        .appendChild xmldoc.createElement("orientation")
            With .LastChild
                .appendChild xmldoc.createElement("local_x")
                With .LastChild
                    .appendChild xmldoc.createElement("i")
                    .LastChild.Text = vRot(0)
                    .appendChild xmldoc.createElement("j")
                    .LastChild.Text = vRot(1)
                    .appendChild xmldoc.createElement("k")
                    .LastChild.Text = vRot(2)
                End With
                .appendChild xmldoc.createElement("local_y")
                 With .LastChild
                    .appendChild xmldoc.createElement("i")
                    .LastChild.Text = vRot(3)
                    .appendChild xmldoc.createElement("j")
                    .LastChild.Text = vRot(4)
                    .appendChild xmldoc.createElement("k")
                    .LastChild.Text = vRot(5)
                End With
                .appendChild xmldoc.createElement("local_z")
                With .LastChild
                .appendChild xmldoc.createElement("i")
                    .LastChild.Text = vRot(6)
                    .appendChild xmldoc.createElement("j")
                    .LastChild.Text = vRot(7)
                    .appendChild xmldoc.createElement("k")
                    .LastChild.Text = vRot(8)
                End With
            End With

        End With
    End With
End Sub
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
Public Sub aSurface(xmldoc, sSrfNm As String, Optional dEmissivity As Double = 1, _
                    Optional dStoSRes As Double, Optional vRGBColor As Variant)

Dim snode As MSXML2.IXMLDOMNode

    If dEmissivity < 0 Or dEmissivity > 1 Then dEmissivity = 1

    If zAttribTypExist(xmldoc, "surfaces") And Not zAttribExist(xmldoc, "surface_att", sSrfNm) Then
        Set snode = xmldoc.SelectSingleNode("//surfaces")
    End If

    With snode
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


