VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Class_XML_Subs_FCv11"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Sub CREATEMODEL()

Dim strArgs As String

'THIS SUBROUTINE IS PROVIDED AS AN EXAMPLE TO ILLUSTRATE THE STRUCTURE AND ORDER OF THE SUBROUTINE CALLS REQUIRED...
'TO CREATE A VALID FLOTHERM OR FLOVENT FLOXML MODEL.  THIS WILL CREATE C:\My_Model.xml, A PROJECT XML FILE, THAT ...
'CONTAINS EXAMPLES OF MOST OF THE OBJECTS AND ATTRIBUTES THAT ARE SUPPORTED IN THE V10.1 FLOXML SCHEMA.

'CREATE AND OPEN THE FILE TO BE WRITTEN
Open ("c:\My_Model.xml") For Output As 1

'CREATE THE XML HEADER - REQUIRED
Call write_header("My Model")

'DEFINE BASIC MODEL SETTINGS AND ASSUMPTIONS FOR XML PROJECTS
Call start_model_inputs
    Call start_model_modeling
        Call model_modeling_setup(0, 1, 1, 1, 1)
        Call model_modeling_store_options(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        Call model_modeling_solar_setup(0, 0, 45, 45, 15, 6, 12, 1, 0, 0.5)
    Call end_model_modeling
    Call turbulence_setup(1, 1, 0, 0, 0, 0)
    Call gravity_setup(1, 4, 0, 0, 0, 9.81)
    Call global_setup(101325, 300, 300, 0, 0, 0, 0, 0, 0, 0)
    Call start_transient_setup(0, 60, 60, 0.0001, 0)                'TRANSIENT INPUTS NOT REQUIRED FOR STEADY STATE MODELS
        Call create_time_grid_patch("First", 0, 30, 0, 15, 1, 1.4)  'TRANSIENT INPUTS NOT REQUIRED FOR STEADY STATE MODELS
        Call create_time_grid_patch("Second", 30, 60, 0, 12, 0, 1)  'TRANSIENT INPUTS NOT REQUIRED FOR STEADY STATE MODELS
    Call end_transient_setup                                        'TRANSIENT INPUTS NOT REQUIRED FOR STEADY STATE MODELS
    Call start_initial_variables_setup(0, 0, 1)
        Call set_individual_initial_variables(1, 2, 2.444)
    Call end_initial_variables_setup
    
'END OF MODEL SETTINGS
Call end_model_inputs

'SET UP BASIC SOLVER CONTROLS FOR XML PROJECTS
Call start_solver_inputs
    monitor_point_termination_string = "MP-01,200"
    Call overall_control_setup(1500, 1, 0.2, 30, 10, 0, 0, 0.9, 0, 1, 0, 0, 1, 0, 0.2, 1, monitor_point_termination_string)
    Call start_variable_controls
        Call variable_control(1, 1, 10, 1.5, 0, 1, 0, 1)
        Call variable_control(2, 1, 10, 1.5, 0, 1, 0, 1)
    Call end_variable_controls
    Call start_solver_controls
        Call solver_control(0, 0.3, 0)
    Call end_solver_controls
Call end_solver_inputs

'SET UP SYSTEM GRID FOR XML PROJECTS
Call start_grid_inputs
    Call system_grid_setup(0.001, 1, 0.01, 0.001, 1, 0.01, 0.001, 0, 24, 1, 12, 12, 12, 0, 0)
    Call start_grid_patches
        Call grid_patch("X-GRID", 0, 1, 1.1, 0, 12, 0, 1)
    Call end_grid_patches
Call end_grid_inputs

'DEFINE ALL ATTRIBUTES FOR XML PROJECTS AND XML ASSEMBLIES
Call start_attributes

    'MATERIAL ATTRIBUTE LIST
    Call start_materials
        Call create_material("Aluminum", 160, 160, 160, 2300, 455, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        Call create_material("FR4", 0.3, 0.3, 0.3, 1200, 880, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        Call create_material("Copper", 400, 400, 400, 8930, 385, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    Call end_materials

    'SURFACE ATTRIBUTE LIST
    Call start_surfaces
        Call create_surface("Paint", 0.88, 0, 0, 0, 1, 0, 0.3, 0.5, 1, 0, 0, 0, "Paint Notes")
    Call end_surfaces

    'AMBIENT ATTRIBUTE LIST
    Call start_ambients
        Call create_ambient("Outside World", 0, 293, 293, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    Call end_ambients

    'THERMAL ATTRIBUTE LIST
    Call start_thermals
        Call create_thermal("Heat", 1, 12.5, 0, 0, 0, 2.1, 0, 0, "Transient1", 0)
    Call end_thermals

    'GRID CONSTRAINT ATTRIBUTE LIST
    Call start_gridconstraints
        Call create_gridconstraint("Grid Constraint 1", 1, 0.001, 1, 43, 0, 0.005, 1, 23, 0, 0, 0, 0)
    Call end_gridconstraints

    'FLUID ATTRIBUTE LIST
    Call start_fluids
        Call create_fluid("Air", 0, 0.0261, 0, 0, 0, 0.000018, 0, 0, 0, 1.16, 1008, 0.003, 0, "AIR STANDARD PROPERTIES")
    Call end_fluids

    'RADIATION ATTRIBUTE LIST
    Call start_radiations
        Call create_radiation("Sub-Divided1", 2, 0, 0.01)
    Call end_radiations

    'SOURCE ATTRIBUTE LIST
    Call start_sources
        Call create_source("23.3 Watts", 0, 3, 23.3, 44, 0, 0, 0, 0, "This is a 23.3 Watt source")
    Call end_sources

    'RESISTANCE ATTRIBUTE LIST
    Call start_resistances
        Call create_resistance("Flow Resistance", 1, 1, 1, 2, 0.1, 1, 1.1, 2, 2, 0.2, 1, 1.2, 12.2, 12.2, 1, 1, 2, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "RESISTANCE ATTRIBUTE NOTES")
    Call end_resistances
    
    'TRANSIENT ATTRIBUTE LIST
    Call start_transients
        transient_curve_string = "0,2,2,3,4,5" 'Transient Multiplier vs Time curve'
        inc_temp_curve_string = "25,1,90,1,95,0.1,115,0.1"   'Transient Multiplier vs Temperature curve [for increasing temperatures]
        dec_temp_curve_string = "25,1,70,1,75,0.1,95,0.1"   'Transient Multiplier vs Temperature curve [for decreasing temperatures]
    Call create_transient("Transient1", 1, 1, 1, transient_curve_string, inc_temp_curve_string, dec_temp_curve_string, "MP-01", 0, 0)
    
    Call create_transient_with_functions_start("Functions-Example", 0, 0, 1, 1, 1, inc_temp_curve_string, dec_temp_curve_string, "MP-01")
        Call create_transient_sub_function_linear("Linear Function", 0, 5, 1, 0, 2.5)
        Call create_transient_sub_function_pulse("Pulse Function", 5, 6, 2.3, 2, 2, 2)
    Call end_transient_with_functions
    
    Call end_transients

    'FAN ATTRIBUTE LIST
    Call start_fans
        fan_curve_string = "0,200,0.1,195,0.2,164,0.3,112,0.4,44,0.5,0.0"
        Call create_ftfan("Fan Curve 1", 0, 0, 0, 0, 1, 0, 400, 2, 100, 200, fan_curve_string)
    Call end_fans
    
    'SURFACE EXCHANGE ATTRIBUTE LIST
    Call start_surface_exchanges
        string_containing_profile_points = "0,200,0.1,195,0.2,164,0.3,112,0.4,44,0.5,0.0"
        Call create_surface_exchange("VolumeHT", 1, 0.005, 3, string_containing_profile_points, 14, 0.003, 0, 255, "SURFACE EX NOTES")
        Call create_surface_exchange("Surface", 0, 0, 0, 0, 0, 0, 0, 0, 0)
    Call end_surface_exchanges

'CLOSE ATTRIBUTE LIST SECTION
Call end_attributes

'BEGIN THE GEOMETRY DESCRIPTION SECTION FOR XML PROJECTS AND XML ASSEMBLIES
'THIS SECTION PROVIDES AN EXAMPLE OF HOW ONE COULD USE THE INCLUDED SUBROUTINES TO BUILD EACH TYPE OF OBJECT
Call start_geometry

' AXIAL FAN EXAMPLE
    Call build_axial_fan("Fan-1", 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0.05, 0.15, 0.01, 6, 0, 0.03, 1, 1, 0, 44, 1, "Fan Curve 1", 0, 0, 0, 0, 0, 0, 0, "Transient1", 0, 0, 0, 1)

' CUBOID EXAMPLE
    Call build_cuboid("Block", 1.1, 2.2, 3.3, 3, 2, 11, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, "Aluminum", "Heat", 0, 0, 0, "Grid Constraint 1", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "Sub-Divided1", 0, 0, 0, 0, 0, 0, 0, "NOTES", 0, 0, 1)

' PRISM EXAMPLE
    Call build_prism("Prism1", 0.1, 0, 0.2, 1, 2, 3, 1, 0, 0, 0, 1, 0, 0, 0, 1, "Aluminum", 0, 0, 0, 0, "Grid Constraint 1", "Paint", 0, 0, 0, 0, 0, 0, 0, 0, 0, "Sub-Divided1", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)

' TET EXAMPLE
    Call build_tet("Tet22", 0, 0, 0, 1, 1, 2, 1, 0, 0, 0, 1, 0, 0, 0, 1, "Aluminum", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)

' INVERTED TET EXAMPLE
    Call build_inverted_tet("ITET", 10, 10, 10, 10, 20, 30, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

' SLOPING BLOCK EXAMPLE
    Call build_sloping_block("BAFFLE", 0, 0, 0, 0.15, 0, 0.005, 0, 43, 1.2, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, "Aluminum", "Heat", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1)

' SOURCE EXAMPLE
    Call build_source("Source-1", 0, 1, -0.3212323, 1, 2, 3333, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, "23.3 Watts", 1, 0, 0, 0, 0, 0, 0, 0, 0, 1)

' RESISTANCE EXAMPLE
    Call build_resistance("Flow Resistance", 10, 10, 10, 10, 10, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, "Flow Resistance", 0, 0, 0, 0, "RES", 0, 0, 1)

' REGION EXAMPLE
    Call build_region("Region", -0.2, -0.2, -0.2, 0.4, 0.4, 0.4, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, "Grid Constraint 1", 0, 0, 0, 0, 1, 0, 1)

' MONITOR POINT EXAMPLE
    Call build_monitor_point("MP-01", 0, 0, 33.23, "THERMOCOUPLE A44", 0, 1)

' CYLINDER EXAMPLE
    Call build_cylinder("Cap", 1, 2, 3, 0.125, 0.3, 16, 1, 0, 0, 0, 1, 0, 0, 0, 1, "Aluminum", "Heat", "Paint", "Sub-Divided1", 0, 0, 0, 0, "CAP", 0, 0, 1)
    
' ASSEMBLY EXAMPLE
    
    Call build_assembly("1206", 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, "Aluminum", 0, 0, 0, 0, 0, 0, 0, 0, 1)
   ' CONTENTS OF ASSEMBLY GO HERE
            
            Call build_cuboid("R22 [1206, 13-23825-07]", 0, 0, 0, 0.005, 0.005, 0.001, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "Sub-Divided1", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
            Call build_region("GR-R22 [1206, 13-23825-07]", 0, 0, 0, 0.005, 0.005, 0.001, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1)

    Call end_assembly
    
' ENCLOSURE SMARTPART EXAMPLE
    Call build_enclosure("Chassis", 1, 1, 1, 2, 2, 2, 0.001, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, "Aluminum", "Sub-Divided1", 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
    
' FIXED FLOW SMARTPART EXAMPLE
    Call build_fixed_flow("Fixed Flow", -1, -2, -3, 1.1, 2.2, 0.99, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0.05, 0, 0, 0, 0, 0, 0, 0, 0, "Outside World", "Grid Constraint 1", "Grid Constraint 1", "Grid Constraint 1", 0, 0, 0, 0, 1)
    
' PERFORATED PLATE SMARTPART EXAMPLE
    Call build_perforated_plate("Floor Tile", 0, 0, 0, 1.2, 1.2, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.005, 0, 0.02, 0.03, 0.55, 1, 0, 22.12, 0, 0, 0, 0, 1, 0, "Grid Constraint 1", 0, "Grid Constraint 1", 0, 0, 0, 0, 1)
    
' PDML FILE REFERENCING EXAMPLE
'    Call build_PDML("Test 1", "C:\TEST.PDML", 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0)

' POWERMAP FILE REFERENCING EXAMPLE
 '   Call build_powermap("PowerMap1", "c:\Thermal_VDD.txt", 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, "Copper", "Grid Constraint 1", 0, 0, 0, "Paint", "Sub-Divided1", 0, 0, 1, 1)
    
' CUBOID WITH HOLES EXAMPLE
    Call build_block_with_holes_start("Block with Holes", 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, "Aluminum", "Heat", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
    Call build_hole("Hole Number 1", 0.2, 0.2, 0.3, 0.3, 1, 1, 1, 0.04, "Aluminum", 0, 0, 0, 0, 0, 0, 1)
    Call build_hole("Hole Number 2", 0.5, 0.5, 0.1, 0.1, 1, 1, 1, 0.04, "Aluminum", 0, 0, 0, 0, 0, 0, 1)
    Call build_block_with_holes_end
    
' RECIRCULATION DEVICE EXAMPLE [There are four different subroutines to cover all Recirculation options]
'       build_recirc_deltaT_start : For fixed DeltaT configurations
'       build_recirc_heat_input_start: For fixed heat input configurations
'       build_recirc_HX_start: For the HX configuration
'       build_recirc_crac_start: For the CRAC configuration

    Call build_recirc_deltaT_start("Recirc-01", 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.55, 0, 0, 0, 0, 13.3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
   
    Call build_supply_list_start
    Call build_supply("Supply1", 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0.12, 0.22, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
    Call build_supply_list_end
    Call build_extract_list_start
    Call build_extract("Extract1", 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0.22, 0.33, 0, 0, 0, 0, 0, 0, 1)
    Call build_extract_list_end
    Call build_recirc_device_end
    
' RACK SMARTPART EXAMPLE [FLOTHERM ONLY]
    
    Call build_rack_start("Rack-001", 0.1, 0.2, 0.3, 1, 0, 0, 0, 1, 0, 0, 0, 1, 12500, 1, 12.2, 0, 0, 0, 0, 0, 0, 0, "Grid Constraint 1", 0, 0, 0, 0, 0, 0, 1)
    Call build_supply_list_start
    Call build_supply("Supply1", 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0.12, 0.22, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
    Call build_supply_list_end
    Call build_extract_list_start
    Call build_extract("Extract1", 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0.22, 0.33, 0, 0, 0, 0, 0, 0, 1)
    Call build_extract_list_end
    Call build_rack_end
    
' COOLER SMARTPART EXAMPLE [FLOTHERM ONLY]
    Call build_cooler_start("Cooler-001", 0.1, 0.2, 0.3, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 100, 0, 15, 110, 84, 35, 113, 84, 0, 34, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
    Call build_supply_list_start
    Call build_supply("Supply1", 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0.12, 0.22, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
    Call build_supply_list_end
    Call build_extract_list_start
    Call build_extract("Extract1", 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0.22, 0.33, 0, 0, 0, 0, 0, 0, 1)
    Call build_extract_list_end
    Call build_cooler_end
    
' NETWORK ASSEMBLY EXAMPLE.  THE CALLS BELOW CREATE A 2R COMPONENT [FLOTHERM ONLY]
   resistancestring = "Junction,Case,1.2,Junction,PCB,22.2"
   capstring = "Junction,3.3,Case,4.4,PCB,1.1"
   Call build_network_assembly_start("Network Assembly Example", 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, resistancestring, capstring, 0, 0, 0, 0, 0, 0, 0, 1)
   Call build_network_node_start("Junction", "Heat", "Junction", 0)
   Call build_network_node_cuboid_list_start
   Call build_network_cuboid("J1", 0, 0, 0, 0.04, 0.04, 0.001, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
   Call build_network_node_cuboid_list_end
   Call build_network_node_monitor_point_list_start
   Call build_monitor_point("Junction Temperature", 0.02, 0.02, 0.0005, 0, 0, 1)
   Call build_network_node_monitor_point_list_end
   Call build_network_node_end
   Call build_network_node_start("Case", 0, 0, 0)
   Call build_network_node_cuboid_list_start
   Call build_network_cuboid("C1", 0, 0, 0.001, 0.04, 0.04, 0.001, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
   Call build_network_cuboid("C2", 0, 0, 0.002, 0.04, 0.04, 0.001, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
   Call build_network_node_cuboid_list_end
   Call build_network_node_end
   Call build_network_node_start("PCB", 0, 0, 0)
   Call build_network_node_cuboid_list_start
   Call build_network_cuboid("PCB1", 0, 0, 0, 0.04, 0.04, 0.001, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
   Call build_network_node_cuboid_list_end
   Call build_network_node_end
   Call build_network_assembly_end
    
' HEAT SINK EXAMPLES.  PLATE FIN AND PIN FIN OPTIONS ARE SUPPORTED WITH DIFFERENT SUBROUTINES
Call build_heat_sink_plate_fin("Plate Fin Heat Sink", 0.455, 0.4875, 0.4595, 0.09, 0.08099997, 0.005, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 31, 0.02, 0, 0.001, 0.0005, 0, 0, 0, 3, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "Aluminum", 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
Call build_heat_sink_pin_fin("Pin Fin Heat Sink", 0.49, 0.49, 0.49, 0.02, 0.02, 0.0035, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0.0165, 0, 0, 0.002, 0.0016, 0.001, 0.001, 0.0005, 4, 0, 6, 5, 0, 0, 3, 0, 0, 0, 0, 0, "Aluminum", 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)

' PCB SMARTPART WITH COMPONENTS
Call build_pcb_start("Printed Circuit Board", 0.005, 0.005, 0.004, 0.2, 0.1, 0.0016, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 12, 0, 0, "FR4", "Copper", 0, 0, 0, 0, 0, 0, 0, 0, 1)
    Call build_pcb_component("U1", 0.04, 0.04, 0.01, 0.01, 0.0015, 0, 0.55, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, "Aluminum", 0, 0, 0, 0, 0, 0)
Call build_pcb_end

' DIE SMARTPART EXAMPLE - FLOTHERM ONLY
Call build_die_discrete_sources("Die SmartPart", 0, 0, 0, 0.001, 0.001, 0.0003, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 3.233, 0, "Aluminum", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
    
' CUTOUT EXAMPLE
Call build_cutout("Cutout Example", 0, 0, 0, 0.2, 0.3, 0.4, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "One face with Symmetry", 0, 1)
    
' HEATPIPE EXAMPLE
Call build_heatpipe_start("Simple Heat Pipe", 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0.33, 12, 0, 0, 0, 0, 0, 0, 0, 1)
    Call build_network_cuboid("Heat Pipe Geometry", 0, 0, 0, 0.002, 0.002, 0.045, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
Call build_heatpipe_end

' TEC EXAMPLE
Call build_tec("Thermoelectric", 0, 0, 0, 0.04, 0.04, 0.002, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0.0005, 1, 25, 4, 35, 1.5, 5, 50, 2, 44, 1.6, 5, "Aluminum", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
    
'END THE GEOMETRY DESCRIPTION
Call end_geometry

'DEFINE THE COMPUTATIONAL DOMAIN - REQUIRED FOR XML PROJECTS, OMIT FOR XML ASSEMBLIES
Call build_domain(0, 0, 0, 0.05, 0.05, 0.05, "Outside World", 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, "Air", 0)

'CREATE THE XML FOOTER - REQUIRED FOR ALL XML FILES
Call write_footer

'CLOSE THE XML FILE
Close #1

' EXAMPLE OF HOW TO CALL THE SOLVER TO SOLVE A SPECIFIED XML FILE
' THE COMMENTED LINES BELOW CALL FLOTHERM.BAT, INDICATE THAT C:\FLOTHERM-MODEL.XML IS TO BE SOLVED
' AND THAT TABLES DATA SHOULD BE WRITTEN TO C:\TEMP
'Set oShell = CreateObject("Wscript.Shell")
'strArgs = "c:\Progra~1\MentorMA\flosuite_v11\flotherm\WinXP\bin\flotherm.bat"
'If Dir(strArgs, vbDirectory) = vbNullString Then
'    strArgs = "c:\Progra~2\MentorMA\flosuite_v11\flotherm\WinXP\bin\flotherm.bat"
'End If
'strArgs = strArgs + " -b c:\FloTHERM.xml -o c:\temp"
'oShell.Run strArgs, 0, True
'oShell = Null

End Sub
Sub write_header(model_name)

Print #1, "<?xml version=" + Chr(34) + "1.0" + Chr(34) + " encoding=" + Chr(34) + "UTF-8" + Chr(34) + " standalone=" + Chr(34) + "no" + Chr(34) + " ?>"
Print #1, "<xml_case>"
Print #1, "<name>" + model_name + "</name>"
End Sub
Sub write_footer()
Print #1, "</xml_case>"
End Sub
Sub start_attributes()
Print #1, "<attributes>"
End Sub
Sub end_attributes()
Print #1, "</attributes>"
End Sub
Sub start_materials()
Print #1, "<materials>"
End Sub
Sub create_material(name, kx, ky, kz, rho, cp, coeff, tref, electrical_resistivity_type_0_constant_1_temperature_dependant, resistivity_value, electrical_coeff, electrical_t_ref, electrical_t_low, electrical_t_high, transparent_0_false_1_true, transparency_model_number_0_1, model_0_absorption_coeff, model_0_refractive_index, model_1_transmittance, model_1_reflectance, surface, notes)

If (coeff = 0 And kx = ky And kx = kz And ky = kz) Then
Print #1, "<isotropic_material_att>"
Print #1, "<name>" + CStr(name) + "</name>"
Print #1, "<conductivity>" + CStr(kx) + "</conductivity>"
Print #1, "<density>" + CStr(rho) + "</density>"
Print #1, "<specific_heat>" + CStr(cp) + "</specific_heat>"

If (electrical_resistivity_type_0_constant_1_temperature_dependant = 0) Then
Print #1, "<electrical_resistivity>"
Print #1, "<type>constant</type>"
Print #1, "<resistivity_value>" + CStr(resistivity_value) + "</resistivity_value>"
ElseIf (electrical_resistivity_type_0_constant_1_temperature_dependant = 1) Then
Print #1, "<electrical_resistivity>"
Print #1, "<type>temperature_dependant</type>"
Print #1, "<resistivity_value>" + CStr(resistivity_value) + "</resistivity_value>"
Print #1, "<coeff>" + CStr(electrical_coeff) + "</coeff>"
Print #1, "<t_ref>" + CStr(electrical_t_ref) + "</t_ref>"
Print #1, "<t_low>" + CStr(electrical_t_low) + "</t_low>"
Print #1, "<t_high>" + CStr(electrical_t_high) + "</t_high>"
End If
Print #1, "</electrical_resistivity>"

If (transparent_0_false_1_true = 1) Then
    If (transparency_model_number_0_1 = 1) Then
        Print #1, "<transparent>true</transparent>"
        Print #1, "<transparency>"
        Print #1, "<model_0>"
        Print #1, "<absorption_coeff>" + CStr(model_0_absorption_coeff) + "</absorption_coeff>"
        Print #1, "<refractive_index>" + CStr(model_0_refractive_index) + "</refractive_index>"
        Print #1, "</model_0>"
    ElseIf (transparency_model_number_0_1 = 0) Then
        Print #1, "<transparent>true</transparent>"
        Print #1, "<transparency>"
        Print #1, "<model_1>"
        Print #1, "<transmittance>" + CStr(model_1_transmittance) + "</transmittance>"
        Print #1, "<reflectance>" + CStr(model_1_reflectance) + "</reflectance>"
        Print #1, "</model_1>"
    End If
    Print #1, "</transparency>"
End If

If (CStr(surface) <> "0") Then
Print #1, "<surface>" + CStr(surface) + "</surface>"
End If

If (CStr(notes) <> "0") Then
Print #1, "<notes>" + CStr(notes) + "</notes>"
End If

Print #1, "</isotropic_material_att>"
End If

If (coeff = 0) Then
If (kx <> ky Or kx <> kz Or ky <> kz) Then
Print #1, "<orthotropic_material_att>"
Print #1, "<name>" + CStr(name) + "</name>"
Print #1, "<x_conductivity>" + CStr(kx) + "</x_conductivity>"
Print #1, "<y_conductivity>" + CStr(ky) + "</y_conductivity>"
Print #1, "<z_conductivity>" + CStr(kz) + "</z_conductivity>"
Print #1, "<density>" + CStr(rho) + "</density>"
Print #1, "<specific_heat>" + CStr(cp) + "</specific_heat>"

If (electrical_resistivity_type_0_constant_1_temperature_dependant = 0) Then
Print #1, "<electrical_resistivity>"
Print #1, "<type>constant</type>"
Print #1, "<resistivity_value>" + CStr(resistivity_value) + "</resistivity_value>"
ElseIf (electrical_resistivity_type_0_constant_1_temperature_dependant = 1) Then
Print #1, "<electrical_resistivity>"
Print #1, "<type>temperature_dependant</type>"
Print #1, "<resistivity_value>" + CStr(resistivity_value) + "</resistivity_value>"
Print #1, "<coeff>" + CStr(electrical_coeff) + "</coeff>"
Print #1, "<t_ref>" + CStr(electrical_t_ref) + "</t_ref>"
Print #1, "<t_low>" + CStr(electrical_t_low) + "</t_low>"
Print #1, "<t_high>" + CStr(electrical_t_high) + "</t_high>"
End If
Print #1, "</electrical_resistivity>"

If (transparent_0_false_1_true = 1) Then
If (transparency_model_number_0_1 = 0) Then
Print #1, "<transparent>true</transparent>"
Print #1, "<transparency>"
Print #1, "<model_0>"
Print #1, "<absorption_coeff>" + CStr(model_0_absorption_coeff) + "</absorption_coeff>"
Print #1, "<refractive_index>" + CStr(model_0_refractive_index) + "</refractive_index>"
ElseIf (transparency_model_number_0_1 = 1) Then
Print #1, "<transparent>true</transparent>"
Print #1, "<transparency>"
Print #1, "<model_1>"
Print #1, "<transmittance>" + CStr(model_1_transmittance) + "</transmittance>"
Print #1, "<reflectance>" + CStr(model_1_reflectance) + "</reflectance>"
End If
Print #1, "</transparency>"
End If

If (CStr(surface) <> "0") Then
Print #1, "<surface>" + CStr(surface) + "</surface>"
End If

If (CStr(notes) <> "0") Then
Print #1, "<notes>" + CStr(notes) + "</notes>"
End If

Print #1, "</orthotropic_material_att>"
End If
End If

If (coeff <> 0) Then
Print #1, "<temperature_dependant_material_att>"
Print #1, "<name>" + CStr(name) + "</name>"
Print #1, "<conductivity>" + CStr(kx) + "</conductivity>"
Print #1, "<coeff>" + CStr(coeff) + "</coeff>"
Print #1, "<tref>" + CStr(tref) + "</tref>"
Print #1, "<density>" + CStr(rho) + "</density>"
Print #1, "<specific_heat>" + CStr(cp) + "</specific_heat>"

If (electrical_resistivity_type_0_constant_1_temperature_dependant = 0) Then
Print #1, "<electrical_resistivity>"
Print #1, "<type>constant</type>"
Print #1, "<resistivity_value>" + CStr(resistivity_value) + "</resistivity_value>"
ElseIf (electrical_resistivity_type_0_constant_1_temperature_dependant = 1) Then
Print #1, "<electrical_resistivity>"
Print #1, "<type>temperature_dependant</type>"
Print #1, "<resistivity_value>" + CStr(resistivity_value) + "</resistivity_value>"
Print #1, "<coeff>" + CStr(electrical_coeff) + "</coeff>"
Print #1, "<t_ref>" + CStr(electrical_t_ref) + "</t_ref>"
Print #1, "<t_low>" + CStr(electrical_t_low) + "</t_low>"
Print #1, "<t_high>" + CStr(electrical_t_high) + "</t_high>"
End If
Print #1, "</electrical_resistivity>"

If (transparent_0_false_1_true = 1) Then
If (transparency_model_number_0_1 = 0) Then
Print #1, "<transparent>true</transparent>"
Print #1, "<transparency>"
Print #1, "<model_0>"
Print #1, "<absorption_coeff>" + CStr(model_0_absorption_coeff) + "</absorption_coeff>"
Print #1, "<refractive_index>" + CStr(model_0_refractive_index) + "</refractive_index>"
ElseIf (transparency_model_number_0_1 = 1) Then
Print #1, "<transparent>true</transparent>"
Print #1, "<transparency>"
Print #1, "<model_1>"
Print #1, "<transmittance>" + CStr(model_1_transmittance) + "</transmittance>"
Print #1, "<reflectance>" + CStr(model_1_reflectance) + "</reflectance>"
End If
Print #1, "</transparency>"
End If

If (CStr(surface) <> "0") Then
Print #1, "<surface>" + CStr(surface) + "</surface>"
End If

If (CStr(notes) <> "0") Then
Print #1, "<notes>" + CStr(notes) + "</notes>"
End If

Print #1, "</temperature_dependant_material_att>"
End If

End Sub
Sub end_materials()
Print #1, "</materials>"
End Sub
Sub start_surfaces()
Print #1, "<surfaces>"
End Sub
Sub create_surface(name, emissivity, roughness, rsurf_fluid, rsurf_solid, area_factor, solar_reflectivity, red, green, blue, shininess, brightness, electrical_resistance, notes)
Print #1, "<surface_att>"
Print #1, "<name>" + name + "</name>"
Print #1, "<emissivity>" + CStr(emissivity) + "</emissivity>"
Print #1, "<roughness>" + CStr(roughness) + "</roughness>"
Print #1, "<rsurf_fluid>" + CStr(rsurf_fluid) + "</rsurf_fluid>"
Print #1, "<rsurf_solid>" + CStr(rsurf_solid) + "</rsurf_solid>"
Print #1, "<area_factor>" + CStr(area_factor) + "</area_factor>"
Print #1, "<solar_reflectivity>" + CStr(solar_reflectivity) + "</solar_reflectivity>"
Print #1, "<electrical_resistance>" + CStr(electrical_resistance) + "</electrical_resistance>"

Print #1, "<display_settings>"
Print #1, "<color>"
Print #1, "<red>" + CStr(red) + "</red>"
Print #1, "<green>" + CStr(green) + "</green>"
Print #1, "<blue>" + CStr(blue) + "</blue>"
Print #1, "</color>"
Print #1, "<shininess>" + CStr(shininess) + "</shininess>"
Print #1, "<brightness>" + CStr(brightness) + "</brightness>"
Print #1, "</display_settings>"

If (CStr(notes) <> "0") Then
Print #1, "<notes>" + CStr(notes) + "</notes>"
End If

Print #1, "</surface_att>"
End Sub
Sub end_surfaces()
Print #1, "</surfaces>"
End Sub
Sub start_ambients()
Print #1, "<ambients>"
End Sub
Sub create_ambient(name, pressure, temperature, radiant_temperature, htc, velocity_x, velocity_y, velocity_z, temperature_transient, radiant_temperature_transient, concentration1, concentration2, concentration3, concentration4, concentration5, turbulent_kinetic_energy, turbulent_dissipation_rate, notes)
Print #1, "<ambient_att>"
Print #1, "<name>" + name + "</name>"
Print #1, "<pressure>" + CStr(pressure) + "</pressure>"
Print #1, "<temperature>" + CStr(temperature) + "</temperature>"
Print #1, "<radiant_temperature>" + CStr(radiant_temperature) + "</radiant_temperature>"
Print #1, "<heat_transfer_coeff>" + CStr(htc) + "</heat_transfer_coeff>"
Print #1, "<velocity><x>" + CStr(velocity_x) + "</x><y>" + CStr(velocity_y) + "</y><z>" + CStr(velocity_z) + "</z></velocity>"
Print #1, "<turbulent_kinetic_energy>" + CStr(turbulent_kinetic_energy) + "</turbulent_kinetic_energy>"
Print #1, "<turbulent_dissipation_rate>" + CStr(turbulent_dissipation_rate) + "</turbulent_dissipation_rate>"
Print #1, "<concentration_1>" + CStr(concentration1) + "</concentration_1>"
Print #1, "<concentration_2>" + CStr(concentration2) + "</concentration_2>"
Print #1, "<concentration_3>" + CStr(concentration3) + "</concentration_3>"
Print #1, "<concentration_4>" + CStr(concentration4) + "</concentration_4>"
Print #1, "<concentration_5>" + CStr(concentration5) + "</concentration_5>"
If (CStr(temperature_transient) <> "0") Then
Print #1, "<ambient_transient>" + CStr(temperature_transient) + "</ambient_transient>"
End If
If (CStr(radiant_temperature_transient) <> "0") Then
Print #1, "<radiant_transient>" + CStr(radiant_temperature_transient) + "</radiant_transient>"
End If
If (CStr(notes) <> "0") Then
Print #1, "<notes>" + CStr(notes) + "</notes>"
End If

Print #1, "</ambient_att>"
End Sub
Sub end_ambients()
Print #1, "</ambients>"
End Sub
Sub start_thermals()
Print #1, "<thermals>"
End Sub
Sub create_thermal(name, thermal_model_type_0_conduction_1_fixed_heat_flow_total_power_2_fixed_heat_flow_power_area_3_fixed_temperature_4_joule_heating, power, power_area, fixed_temperature, joule_heating_0_current_1_voltage, current, voltage, joule_heating_direction_0_longest_1_X_2_Y_3_Z, transient, notes)
Print #1, "<thermal_att>"
Print #1, "<name>" + name + "</name>"

If (thermal_model_type_0_conduction_1_fixed_heat_flow_total_power_2_fixed_heat_flow_power_area_3_fixed_temperature_4_joule_heating = 0) Then
Print #1, "<thermal_model>conduction</thermal_model>"
Print #1, "<power>" + CStr(power) + "</power>"

ElseIf (thermal_model_type_0_conduction_1_fixed_heat_flow_total_power_2_fixed_heat_flow_power_area_3_fixed_temperature_4_joule_heating = 1) Then
Print #1, "<thermal_model>fixed_heat_flow</thermal_model>"
Print #1, "<fixed_heat_flow>total_power</fixed_heat_flow>"
Print #1, "<power>" + CStr(power) + "</power>"

ElseIf (thermal_model_type_0_conduction_1_fixed_heat_flow_total_power_2_fixed_heat_flow_power_area_3_fixed_temperature_4_joule_heating = 2) Then
Print #1, "<thermal_model>fixed_heat_flow</thermal_model>"
Print #1, "<fixed_heat_flow>power_area</fixed_heat_flow>"
Print #1, "<power_area>" + CStr(power_area) + "</power_area>"

ElseIf (thermal_model_type_0_conduction_1_fixed_heat_flow_total_power_2_fixed_heat_flow_power_area_3_fixed_temperature_4_joule_heating = 3) Then
Print #1, "<thermal_model>fixed_temperature</thermal_model>"
Print #1, "<fixed_temperature>" + CStr(fixed_temperature) + "</fixed_temperature>"

ElseIf (thermal_model_type_0_conduction_1_fixed_heat_flow_total_power_2_fixed_heat_flow_power_area_3_fixed_temperature_4_joule_heating = 4) Then
Print #1, "<thermal_model>joule_heating</thermal_model>"
Print #1, "<joule_heating>"

    If (joule_heating_0_current_1_voltage = 0) Then
        Print #1, "<using>current</using>"
        Print #1, "<current>" + CStr(current) + "</current>"
    Else
        Print #1, "<using>voltage</using>"
        Print #1, "<voltage>" + CStr(voltage) + "</voltage>"
    End If

    If (joule_heating_direction_0_longest_1_X_2_Y_3_Z = 0) Then
        Print #1, "<joule_heating_flow_direction>longest</joule_heating_flow_direction>"
    ElseIf (joule_heating_direction_0_longest_1_X_2_Y_3_Z = 1) Then
        Print #1, "<joule_heating_flow_direction>x</joule_heating_flow_direction>"
    ElseIf (joule_heating_direction_0_longest_1_X_2_Y_3_Z = 2) Then
        Print #1, "<joule_heating_flow_direction>y</joule_heating_flow_direction>"
    ElseIf (joule_heating_direction_0_longest_1_X_2_Y_3_Z = 3) Then
        Print #1, "<joule_heating_flow_direction>z</joule_heating_flow_direction>"
    End If
Print #1, "</joule_heating>"

End If

If (CStr(transient) <> "0") Then
Print #1, "<transient>" + CStr(transient) + "</transient>"
End If
If (CStr(notes) <> "0") Then
Print #1, "<notes>" + CStr(notes) + "</notes>"
End If
Print #1, "</thermal_att>"
End Sub
Sub end_thermals()
Print #1, "</thermals>"
End Sub
Sub start_occupancies()
Print #1, "<occupancies>"
End Sub
Sub create_occupancy(name, occupancy_level, activity_level_0_low_1_medium_2_high_3_specified, specified_activity_value, notes)
Print #1, "<occupancy_att>"
Print #1, "<name>" + name + "</name>"
Print #1, "<occupancy_level>" + CStr(occupancy_level) + "</occupancy_level>"

If (activity_level_0_low_1_medium_2_high_3_specified = 0) Then
Print #1, "<activity_level>low</activity_level>"
ElseIf (activity_level_0_low_1_medium_2_high_3_specified = 1) Then
Print #1, "<activity_level>medium</activity_level>"
ElseIf (activity_level_0_low_1_medium_2_high_3_specified = 2) Then
Print #1, "<activity_level>high</activity_level>"
ElseIf (activity_level_0_low_1_medium_2_high_3_specified = 3) Then
Print #1, "<activity_level>specified</activity_level>"
Print #1, "<specified_activity_value>" + CStr(specified_activity_value) + "</specified_activity_value>"
End If

If (CStr(notes) <> "0") Then
Print #1, "<notes>" + CStr(notes) + "</notes>"
End If

Print #1, "</occupancy_att>"
End Sub
Sub end_occupancies()
Print #1, "</occupancies>"
End Sub
Sub start_resistances()
Print #1, "<resistances>"
End Sub
Sub create_resistance(name, standard_0_advanced_1, planar_0_volume_1, x_a_coefficient, x_b_coefficient, x_far, x_length_scale, x_index, y_a_coefficient, y_b_coefficient, y_far, y_length_scale, y_index, z_a_coefficient, z_b_coefficient, z_far, z_length_scale, z_index, loss_coefficients_based_on_0_approach_velocity_1_device_velocity_2_accelerated, angled_external_resistance_0_true_1_false, angled_external_x, angled_external_y, angled_external_z, transparent_to_radiation_0_true_1_false, concentration_1_filter_percentage, concentration_2_filter_percentage, concentration_3_filter_percentage, concentration_4_filter_percentage, concentration_5_filter_percentage, concentration_filter_reference_length, notes)

'For a planar resistance only the z parameters are required.
'For a standard resistance, the 'a_coefficient' serves as the 'loss coefficient'

Print #1, "<resistance_att>"
Print #1, "<name>" + name + "</name>"
If (planar_0_volume_1 = 0) Then

If (standard_0_advanced_1 = 0) Then

Print #1, "<resistance_z>"
Print #1, "<loss_coefficient>" + CStr(z_a_coefficient) + "</loss_coefficient>"
Print #1, "</resistance_z>"
End If

If (standard_0_advanced_1 = 1) Then

Print #1, "<resistance_z>"
Print #1, "<a_coefficient>" + CStr(z_a_coefficient) + "</a_coefficient>"
Print #1, "<b_coefficient>" + CStr(z_b_coefficient) + "</b_coefficient>"
Print #1, "<free_area_ratio>" + CStr(z_far) + "</free_area_ratio>"
Print #1, "<length_scale>" + CStr(z_length_scale) + "</length_scale>"
Print #1, "<index>" + CStr(z_index) + "</index>"
Print #1, "</resistance_z>"
End If

End If

If (planar_0_volume_1 = 1) Then

If (standard_0_advanced_1 = 0) Then
Print #1, "<resistance_x>"
Print #1, "<loss_coefficient>" + CStr(x_a_coefficient) + "</loss_coefficient>"
Print #1, "</resistance_x>"
Print #1, "<resistance_y>"
Print #1, "<loss_coefficient>" + CStr(y_a_coefficient) + "</loss_coefficient>"
Print #1, "</resistance_y>"
Print #1, "<resistance_z>"
Print #1, "<loss_coefficient>" + CStr(z_a_coefficient) + "</loss_coefficient>"
Print #1, "</resistance_z>"
End If

If (standard_0_advanced_1 = 1) Then
Print #1, "<resistance_x>"
Print #1, "<a_coefficient>" + CStr(x_a_coefficient) + "</a_coefficient>"
Print #1, "<b_coefficient>" + CStr(x_b_coefficient) + "</b_coefficient>"
Print #1, "<free_area_ratio>" + CStr(x_far) + "</free_area_ratio>"
Print #1, "<length_scale>" + CStr(x_length_scale) + "</length_scale>"
Print #1, "<index>" + CStr(x_index) + "</index>"
Print #1, "</resistance_x>"
Print #1, "<resistance_y>"
Print #1, "<a_coefficient>" + CStr(y_a_coefficient) + "</a_coefficient>"
Print #1, "<b_coefficient>" + CStr(y_b_coefficient) + "</b_coefficient>"
Print #1, "<free_area_ratio>" + CStr(y_far) + "</free_area_ratio>"
Print #1, "<length_scale>" + CStr(y_length_scale) + "</length_scale>"
Print #1, "<index>" + CStr(y_index) + "</index>"
Print #1, "</resistance_y>"
Print #1, "<resistance_z>"
Print #1, "<a_coefficient>" + CStr(z_a_coefficient) + "</a_coefficient>"
Print #1, "<b_coefficient>" + CStr(z_b_coefficient) + "</b_coefficient>"
Print #1, "<free_area_ratio>" + CStr(z_far) + "</free_area_ratio>"
Print #1, "<length_scale>" + CStr(z_length_scale) + "</length_scale>"
Print #1, "<index>" + CStr(z_index) + "</index>"
Print #1, "</resistance_z>"
End If

End If

If (loss_coefficients_based_on_0_approach_velocity_1_device_velocity_2_accelerated = 0) Then
    Print #1, "<loss_coefficients_based_on>approach_velocity</loss_coefficients_based_on>"
ElseIf (loss_coefficients_based_on_0_approach_velocity_1_device_velocity_2_accelerated = 1) Then
    Print #1, "<loss_coefficients_based_on>device_velocity</loss_coefficients_based_on>"
ElseIf (loss_coefficients_based_on_0_approach_velocity_1_device_velocity_2_accelerated = 2) Then
    Print #1, "<loss_coefficients_based_on>accelerated</loss_coefficients_based_on>"
End If

If (angled_external_resistance_0_true_1_false = 0) Then
    Print #1, "<angle_mode>angled</angle_mode>"
    Print #1, "<external_angled_resistance><x>" + CStr(angled_external_x) + "<x><y>" + CStr(angled_external_y) + "</y><z>" + CStr(angled_external_z) + "</z></external_angled_resistance>"
End If

If (transparent_to_radiation_0_true_1_false = 0) Then
    Print #1, "<transparent_to_radiation>true</transparent_to_radiation>"
End If

If (concentration_1_filter_percentage <> 0 And concentration_2_filter_percentage <> 0 And concentration_3_filter_percentage <> 0 And concentration_4_filter_percentage <> 0 And concentration_5_filter_percentage <> 0) Then

    Print #1, "<percentage_filter_effiency>"
    Print #1, "<active>true</active>"
    Print #1, "<reference_length>" + CStr(concentration_filter_reference_length) + "</reference_length>"
    Print #1, "<concentration_1_filter_percentage>" + CStr(concentration_1_filter_percentage) + "</concentration_1_filter_percentage>"
    Print #1, "<concentration_2_filter_percentage>" + CStr(concentration_2_filter_percentage) + "</concentration_2_filter_percentage>"
    Print #1, "<concentration_3_filter_percentage>" + CStr(concentration_3_filter_percentage) + "</concentration_3_filter_percentage>"
    Print #1, "<concentration_4_filter_percentage>" + CStr(concentration_4_filter_percentage) + "</concentration_4_filter_percentage>"
    Print #1, "<concentration_5_filter_percentage>" + CStr(concentration_5_filter_percentage) + "</concentration_5_filter_percentage>"
End If

If (CStr(notes) <> "0") Then
Print #1, "<notes>" + CStr(notes) + "</notes>"
End If

Print #1, "</resistance_att>"
End Sub
Sub end_resistances()
Print #1, "</resistances>"
End Sub
Sub start_gridconstraints()
Print #1, "<grid_constraints>"
End Sub
Sub create_gridconstraint(name, min_size_active_0_false_1_true, min_cell_size, number_cells_control_0_max_size_1_min_number, max_size_or_min_number, high_inflation_0_size_1_percent, high_size_or_percent, high_cells_control_0_max_size_1_min_number, high_max_size_or_min_number, low_inflation_0_size_1_percent, low_size_or_percent, low_cells_control_0_max_size_1_min_number, low_max_size_or_min_number)
Print #1, "<grid_constraint_att>"
Print #1, "<name>" + name + "</name>"
If (min_size_active_0_false_1_true = 0) Then
Print #1, "<enable_min_cell_size>false</enable_min_cell_size>"
Else
Print #1, "<enable_min_cell_size>true</enable_min_cell_size>"
Print #1, "<min_cell_size>" + CStr(min_cell_size) + "</min_cell_size>"
End If

If (number_cells_control_0_max_size_1_min_number = 0) Then
Print #1, "<number_cells_control>max_size</number_cells_control>"
Print #1, "<max_size>" + CStr(max_size_or_min_number) + "</max_size>"
Else
Print #1, "<number_cells_control>min_number</number_cells_control>"
Print #1, "<min_number>" + CStr(max_size_or_min_number) + "</min_number>"
End If

If (high_size_or_percent <> 0) Then
Print #1, "<high_inflation>"
If (high_inflation_0_size_1_percent = 0) Then
Print #1, "<inflation_type>size</inflation_type>"
Print #1, "<inflation_size>" + CStr(high_size_or_percent) + "</inflation_size>"
Else
Print #1, "<inflation_type>percent</inflation_type>"
Print #1, "<inflation_percent>" + CStr(high_size_or_percent) + "</inflation_percent>"
End If

If (high_cells_control_0_max_size_1_min_number = 0) Then
Print #1, "<number_cells_control>max_size</number_cells_control>"
Print #1, "<max_size>" + CStr(high_max_size_or_min_number) + "</max_size>"
Else
Print #1, "<number_cells_control>min_number</number_cells_control>"
Print #1, "<min_number>" + CStr(high_max_size_or_min_number) + "</min_number>"
End If
Print #1, "</high_inflation>"
End If

If (low_size_or_percent <> 0) Then
Print #1, "<low_inflation>"
If (low_inflation_0_size_1_percent = 0) Then
Print #1, "<inflation_type>size</inflation_type>"
Print #1, "<inflation_size>" + CStr(low_size_or_percent) + "</inflation_size>"
Else
Print #1, "<inflation_type>percent</inflation_type>"
Print #1, "<inflation_percent>" + CStr(low_size_or_percent) + "</inflation_percent>"
End If

If (low_cells_control_0_max_size_1_min_number = 0) Then
Print #1, "<number_cells_control>max_size</number_cells_control>"
Print #1, "<max_size>" + CStr(low_max_size_or_min_number) + "</max_size>"
Else
Print #1, "<number_cells_control>min_number</number_cells_control>"
Print #1, "<min_number>" + CStr(low_max_size_or_min_number) + "</min_number>"
End If
Print #1, "</low_inflation>"
End If

Print #1, "</grid_constraint_att>"
End Sub
Sub end_gridconstraints()
Print #1, "</grid_constraints>"
End Sub
Sub start_radiations()
Print #1, "<radiations>"
End Sub
Sub create_radiation(name, type_0_nonradiating_1_single_2_subdivided, min_area, subdivided_surface_tolerance)
Print #1, "<radiation_att>"
Print #1, "<name>" + name + "</name>"

If (type_0_nonradiating_1_single_2_subdivided = 0) Then
Print #1, "<surface>non_radiating</surface>"
ElseIf (type_0_nonradiating_1_single_2_subdivided = 1) Then
Print #1, "<surface>single_radiating</surface>"
Else
Print #1, "<surface>subdivided_radiating</surface>"
End If
Print #1, "<min_area>" + CStr(min_area) + "</min_area>"
Print #1, "<subdivided_surface_tolerance>" + CStr(subdivided_surface_tolerance) + "</subdivided_surface_tolerance>"
Print #1, "</radiation_att>"
End Sub
Sub end_radiations()
Print #1, "</radiations>"
End Sub
Sub start_surface_exchanges()
Print #1, "<surface_exchanges>"
End Sub
Sub create_surface_exchange(name, heat_transfer_method_0_surface_1_volume, extent_of_heat_transfer, heat_transfer_coefficient_0_calculated_1_specified_2_constant_3_profile, string_containing_profile_points, specified_constant_value, wetted_area_volume_transfer, reference_temperature_type_0_calculated_1_specified, reference_temperature_value, notes)
Dim points() As String
Dim k As Integer

Print #1, "<surface_exchange_att>"
Print #1, "<name>" + name + "</name>"

If (heat_transfer_method_0_surface_1_volume = 0) Then
Print #1, "<heat_transfer_method>surface</heat_transfer_method>"

ElseIf (heat_transfer_method_0_surface_1_volume = 1) Then
Print #1, "<heat_transfer_method>volume</heat_transfer_method>"
Print #1, "<extent_of_heat_transfer>" + CStr(extent_of_heat_transfer) + "</extent_of_heat_transfer>"
Print #1, "<wetted_area_volume_transfer>" + CStr(wetted_area_volume_transfer) + "</wetted_area_volume_transfer>"
End If


If (heat_transfer_coefficient_0_calculated_1_specified_2_constant_3_profile = 0) Then
Print #1, "<heat_transfer_coefficient>calculated</heat_transfer_coefficient>"
ElseIf (heat_transfer_coefficient_0_calculated_1_specified_2_constant_3_profile = 1) Then
Print #1, "<heat_transfer_coefficient>specified</heat_transfer_coefficient>"
ElseIf (heat_transfer_coefficient_0_calculated_1_specified_2_constant_3_profile = 2) Then
Print #1, "<heat_transfer_coefficient>constant</heat_transfer_coefficient>"
ElseIf (heat_transfer_coefficient_0_calculated_1_specified_2_constant_3_profile = 3) Then
Print #1, "<heat_transfer_coefficient>profile</heat_transfer_coefficient>"

Print #1, "<profile>"
points() = Split(string_containing_profile_points, ",")

For k = 0 To UBound(points) Step 2
Print #1, "<heat_sink_curve_point>"
Print #1, "<speed>" + points(k) + "</speed><thermal_resistance>" + points(k + 1) + "</thermal_resistance>"
Print #1, "</heat_sink_curve_point>"

Next k

Print #1, "</profile>"

End If

Print #1, "<specified_constant_value>" + CStr(specified_constant_value) + "</specified_constant_value>"

If (reference_temperature_type_0_calculated_1_specified = 0) Then
Print #1, "<reference_temperature>calculated</reference_temperature>"
ElseIf (reference_temperature_type_0_calculated_1_specified = 1) Then
Print #1, "<reference_temperature>specified</reference_temperature>"
End If


Print #1, "<reference_temperature_value>" + CStr(reference_temperature_value) + "</reference_temperature_value>"

If (CStr(notes) <> "0") Then
Print #1, "<notes>" + CStr(notes) + "</notes>"
End If


Print #1, "</surface_exchange_att>"
End Sub
Sub end_surface_exchanges()
Print #1, "</surface_exchanges>"
End Sub
Sub start_fluids()
Print #1, "<fluids>"
End Sub
Sub create_fluid(name, conductivity_type_0_constant_1_temperature_dependant, conductivity, conductivity_coeff, conductivity_tref, viscosity_type_0_constant_1_temperature_dependant, viscosity, viscosity_coeff, viscosity_tref, density_type_0_constant_1_idealgas, density_or_molecular_weight, specific_heat, expansivity, diffusivity, notes)
Print #1, "<fluid_att>"
Print #1, "<name>" + name + "</name>"

If (conductivity_type_0_constant_1_temperature_dependant = 0) Then
Print #1, "<conductivity_type>constant</conductivity_type>"
Print #1, "<conductivity>" + CStr(conductivity) + "</conductivity>"
Else
Print #1, "<conductivity_type>temperature_dependant</conductivity_type>"
Print #1, "<conductivity>" + CStr(conductivity) + "</conductivity>"
Print #1, "<cond_coeff>" + CStr(conductivity_coeff) + "</cond_coeff>"
Print #1, "<cond_tref>" + CStr(conductivity_tref) + "</cond_tref>"
End If

If (viscosity_type_0_constant_1_temperature_dependant = 0) Then
Print #1, "<viscosity_type>constant</viscosity_type>"
Print #1, "<viscosity>" + CStr(viscosity) + "</viscosity>"
Else
Print #1, "<viscosity_type>temperature_dependant</viscosity_type>"
Print #1, "<viscosity>" + CStr(viscosity) + "</viscosity>"
Print #1, "<visc_coeff>" + CStr(viscosity_coeff) + "</visc_coeff>"
Print #1, "<visc_tref>" + CStr(viscosity_tref) + "</visc_tref>"
End If

If (density_type_0_constant_1_idealgas = 0) Then
Print #1, "<density_type>constant</density_type>"
Print #1, "<density>" + CStr(density_or_molecular_weight) + "</density>"
Else
Print #1, "<density_type>ideal_gas</density_type>"
Print #1, "<mol_weight>" + CStr(density_or_molecular_weight) + "</mol_weight>"
End If

Print #1, "<specific_heat>" + CStr(specific_heat) + "</specific_heat>"
Print #1, "<expansivity>" + CStr(expansivity) + "</expansivity>"
Print #1, "<diffusivity>" + CStr(diffusivity) + "</diffusivity>"

If (CStr(notes) <> "0") Then
Print #1, "<notes>" + CStr(notes) + "</notes>"
End If

Print #1, "</fluid_att>"
End Sub
Sub end_fluids()
Print #1, "</fluids>"
End Sub
Sub start_sources()
Print #1, "<sources>"
End Sub
Sub create_source(name, applies_to_0_temperature_1_conc1_2_conc2_3_conc3_4_conc4_5_conc5_6_pressure_7_xvelocity_8_yvelocity_9_zvelocity_10_keturb_11_dissturb_12_potential, type_0_total_1_volume_2_area_3_fixed_4_linear_5_nonlinear, power, value, linear_coefficient, string_containing_non_linear_curve, transient_attribute, apply_transient_to_coeff_0_true_1_false, notes)
Dim points() As String
Dim k As Integer

Print #1, "<source_att>"
Print #1, "<name>" + name + "</name>"

Print #1, "<source_options>"
Print #1, "<option>"

If (applies_to_0_temperature_1_conc1_2_conc2_3_conc3_4_conc4_5_conc5_6_pressure_7_xvelocity_8_yvelocity_9_zvelocity_10_keturb_11_dissturb_12_potential = 0) Then
Print #1, "<applies_to>temperature</applies_to>"

ElseIf (applies_to_0_temperature_1_conc1_2_conc2_3_conc3_4_conc4_5_conc5_6_pressure_7_xvelocity_8_yvelocity_9_zvelocity_10_keturb_11_dissturb_12_potential = 1) Then
Print #1, "<applies_to>concentration_1</applies_to>"

ElseIf (applies_to_0_temperature_1_conc1_2_conc2_3_conc3_4_conc4_5_conc5_6_pressure_7_xvelocity_8_yvelocity_9_zvelocity_10_keturb_11_dissturb_12_potential = 2) Then
Print #1, "<applies_to>concentration_2</applies_to>"

ElseIf (applies_to_0_temperature_1_conc1_2_conc2_3_conc3_4_conc4_5_conc5_6_pressure_7_xvelocity_8_yvelocity_9_zvelocity_10_keturb_11_dissturb_12_potential = 3) Then
Print #1, "<applies_to>concentration_3</applies_to>"

ElseIf (applies_to_0_temperature_1_conc1_2_conc2_3_conc3_4_conc4_5_conc5_6_pressure_7_xvelocity_8_yvelocity_9_zvelocity_10_keturb_11_dissturb_12_potential = 4) Then
Print #1, "<applies_to>concentration_4</applies_to>"

ElseIf (applies_to_0_temperature_1_conc1_2_conc2_3_conc3_4_conc4_5_conc5_6_pressure_7_xvelocity_8_yvelocity_9_zvelocity_10_keturb_11_dissturb_12_potential = 5) Then
Print #1, "<applies_to>concentration_5</applies_to>"

ElseIf (applies_to_0_temperature_1_conc1_2_conc2_3_conc3_4_conc4_5_conc5_6_pressure_7_xvelocity_8_yvelocity_9_zvelocity_10_keturb_11_dissturb_12_potential = 6) Then
Print #1, "<applies_to>pressure</applies_to>"

ElseIf (applies_to_0_temperature_1_conc1_2_conc2_3_conc3_4_conc4_5_conc5_6_pressure_7_xvelocity_8_yvelocity_9_zvelocity_10_keturb_11_dissturb_12_potential = 7) Then
Print #1, "<applies_to>x_velocity</applies_to>"

ElseIf (applies_to_0_temperature_1_conc1_2_conc2_3_conc3_4_conc4_5_conc5_6_pressure_7_xvelocity_8_yvelocity_9_zvelocity_10_keturb_11_dissturb_12_potential = 8) Then
Print #1, "<applies_to>y_velocity</applies_to>"

ElseIf (applies_to_0_temperature_1_conc1_2_conc2_3_conc3_4_conc4_5_conc5_6_pressure_7_xvelocity_8_yvelocity_9_zvelocity_10_keturb_11_dissturb_12_potential = 9) Then
Print #1, "<applies_to>z_velocity</applies_to>"

ElseIf (applies_to_0_temperature_1_conc1_2_conc2_3_conc3_4_conc4_5_conc5_6_pressure_7_xvelocity_8_yvelocity_9_zvelocity_10_keturb_11_dissturb_12_potential = 10) Then
Print #1, "<applies_to>ke_turb</applies_to>"

ElseIf (applies_to_0_temperature_1_conc1_2_conc2_3_conc3_4_conc4_5_conc5_6_pressure_7_xvelocity_8_yvelocity_9_zvelocity_10_keturb_11_dissturb_12_potential = 11) Then
Print #1, "<applies_to>diss_turb</applies_to>"

ElseIf (applies_to_0_temperature_1_conc1_2_conc2_3_conc3_4_conc4_5_conc5_6_pressure_7_xvelocity_8_yvelocity_9_zvelocity_10_keturb_11_dissturb_12_potential = 12) Then
Print #1, "<applies_to>potential</applies_to>"


End If

If (type_0_total_1_volume_2_area_3_fixed_4_linear_5_nonlinear = 0) Then
Print #1, "<type>total</type>"
ElseIf (type_0_total_1_volume_2_area_3_fixed_4_linear_5_nonlinear = 1) Then
Print #1, "<type>volume</type>"
ElseIf (type_0_total_1_volume_2_area_3_fixed_4_linear_5_nonlinear = 2) Then
Print #1, "<type>area</type>"
ElseIf (type_0_total_1_volume_2_area_3_fixed_4_linear_5_nonlinear = 3) Then
Print #1, "<type>fixed</type>"
ElseIf (type_0_total_1_volume_2_area_3_fixed_4_linear_5_nonlinear = 4) Then
Print #1, "<type>linear</type>"
ElseIf (type_0_total_1_volume_2_area_3_fixed_4_linear_5_nonlinear = 5) Then
Print #1, "<type>non_linear</type>"
End If

Print #1, "<value>" + CStr(value) + "</value>"
Print #1, "<power>" + CStr(power) + "</power>"
Print #1, "<linear_coefficient>" + CStr(linear_coefficient) + "</linear_coefficient>"

If (string_containing_non_linear_curve <> "0") Then
Print #1, "<non_linear_curve>"
points() = Split(string_containing_non_linear_curve, ",")

For k = 0 To UBound(points) Step 2
Print #1, "<power_temp_curve_point>"
Print #1, "<temperature>" + points(k) + "</temperature><power>" + points(k + 1) + "</power>"
Print #1, "</power_temp_curve_point>"

Next k

Print #1, "</non_linear_curve>"
End If

If (CStr(transient_attribute) <> "0") Then
Print #1, "<transient>" + CStr(transient_attribute) + "</transient>"
    If (apply_transient_to_coeff_0_true_1_false = 1) Then
        Print #1, "<apply_transient_to_coeff>false</apply_transient_to_coeff>"
    End If
End If

Print #1, "</option>"
Print #1, "</source_options>"

If (CStr(notes) <> "0") Then
Print #1, "<notes>" + CStr(notes) + "</notes>"
End If

Print #1, "</source_att>"
End Sub
Sub end_sources()
Print #1, "</sources>"
End Sub
Sub start_transients()
Print #1, "<transients>"
End Sub
Sub create_transient(name, multiplier_vs_time_active_0_false_1_true, multiplier_vs_MP_active_0_false_1_true, multiplier_vs_MP_hysteresis_active_0_false_1_true, string_containing_time_multiplier_pairs, string_containing_MP_multiplier_pairs_increasing, string_containing_MP_multiplier_pairs_decreasing, associated_monitor_point, peroidic_0_false_1_true, notes)
Dim points() As String
Dim k As Integer


Print #1, "<transient_att>"
Print #1, "<name>" + name + "</name>"

If (multiplier_vs_time_active_0_false_1_true = 1) Then

Print #1, "<transient_time_active>true</transient_time_active>"

Print #1, "<trans_curve_points>"


points() = Split(string_containing_time_multiplier_pairs, ",")

For k = 0 To UBound(points) Step 2
Print #1, "<trans_curve_point>"
Print #1, "<time>" + points(k) + "</time><coef>" + points(k + 1) + "</coef>"
Print #1, "</trans_curve_point>"

Next k

Print #1, "</trans_curve_points>"
Else

Print #1, "<transient_time_active>false</transient_time_active>"

End If

If (multiplier_vs_MP_active_0_false_1_true = 1) Then

Print #1, "<transient_temperature_active>true</transient_temperature_active>"

Print #1, "<associated_monitor_point>" + CStr(associated_monitor_point) + "</associated_monitor_point>"

Print #1, "<temp_curve_points>"

points() = Split(string_containing_MP_multiplier_pairs_increasing, ",")

For k = 0 To UBound(points) Step 2
Print #1, "<temp_curve_point>"
Print #1, "<temp>" + points(k) + "</temp><coef>" + points(k + 1) + "</coef>"
Print #1, "</temp_curve_point>"

Next k

Print #1, "</temp_curve_points>"

If (multiplier_vs_MP_hysteresis_active_0_false_1_true = 1) Then

Print #1, "<hysteresis_active>true</hysteresis_active>"

Print #1, "<decreasing_temp_curve_points>"

points() = Split(string_containing_MP_multiplier_pairs_decreasing, ",")

For k = 0 To UBound(points) Step 2
Print #1, "<temp_curve_point>"
Print #1, "<temp>" + points(k) + "</temp><coef>" + points(k + 1) + "</coef>"
Print #1, "</temp_curve_point>"

Next k

Print #1, "</decreasing_temp_curve_points>"

End If

Else

Print #1, "<transient_temperature_active>false</transient_temperature_active>"

End If

If (peroidic_0_false_1_true = 0) Then
Print #1, "<periodic>false</periodic>"
ElseIf (peroidic_0_false_1_true = 1) Then
Print #1, "<periodic>true</periodic>"
End If

If (CStr(notes) <> "0") Then
Print #1, "<notes>" + CStr(notes) + "</notes>"
End If


Print #1, "</transient_att>"
End Sub
Sub create_transient_sub_function_linear(name, start_time, finish_time, baseline_value, baseline_time, coefficient)
    Print #1, "<sub_fuction>"
    Print #1, "<name>" + name + "</name>"
    Print #1, "<start_time>" + CStr(start_time) + "</start_time>"
    Print #1, "<finish_time>" + CStr(finish_time) + "</finish_time>"
    
    Print #1, "<type>"
    Print #1, "<linear>"
    
    Print #1, "<baseline_value>" + CStr(baseline_value) + "</baseline_value>"
    Print #1, "<baseline_time>" + CStr(baseline_time) + "</baseline_time>"
    Print #1, "<coefficient>" + CStr(coefficient) + "</coefficient>"
    
    Print #1, "</linear>"
    Print #1, "</type>"
    
    Print #1, "</sub_fuction>"
End Sub
Sub create_transient_sub_function_power_law(name, start_time, finish_time, baseline_value, baseline_time, coefficient, power_index)
 Print #1, "<sub_fuction>"
    Print #1, "<name>" + name + "</name>"
    Print #1, "<start_time>" + CStr(start_time) + "</start_time>"
    Print #1, "<finish_time>" + CStr(finish_time) + "</finish_time>"
    
    Print #1, "<type>"
    Print #1, "<power_law>"
    
    Print #1, "<baseline_value>" + CStr(baseline_value) + "</baseline_value>"
    Print #1, "<baseline_time>" + CStr(baseline_time) + "</baseline_time>"
    Print #1, "<coefficient>" + CStr(coefficient) + "</coefficient>"
    Print #1, "<power_index>" + CStr(power_index) + "</power_index>"
    
    Print #1, "</power_law>"
    Print #1, "</type>"
    
    Print #1, "</sub_fuction>"
End Sub
Sub create_transient_sub_function_exponential(name, start_time, finish_time, baseline_value, baseline_time, a_coefficient, b_coefficient)
 Print #1, "<sub_fuction>"
    Print #1, "<name>" + name + "</name>"
    Print #1, "<start_time>" + CStr(start_time) + "</start_time>"
    Print #1, "<finish_time>" + CStr(finish_time) + "</finish_time>"
    
   Print #1, "<type>"
    Print #1, "<exponential>"
    
    Print #1, "<baseline_value>" + CStr(baseline_value) + "</baseline_value>"
    Print #1, "<baseline_time>" + CStr(baseline_time) + "</baseline_time>"
    Print #1, "<a_coefficient>" + CStr(a_coefficient) + "</a_coefficient>"
    Print #1, "<b_coefficient>" + CStr(b_coefficient) + "</b_coefficient>"
    
    Print #1, "</exponential>"
    Print #1, "</type>"
    
    Print #1, "</sub_fuction>"
End Sub
Sub create_transient_sub_function_sinusoidal(name, start_time, finish_time, baseline_value, baseline_time, coefficient, period)
 Print #1, "<sub_fuction>"
    Print #1, "<name>" + name + "</name>"
    Print #1, "<start_time>" + CStr(start_time) + "</start_time>"
    Print #1, "<finish_time>" + CStr(finish_time) + "</finish_time>"
    
    Print #1, "<type>"
    Print #1, "<sinusoidal>"
    
    Print #1, "<baseline_value>" + CStr(baseline_value) + "</baseline_value>"
    Print #1, "<baseline_time>" + CStr(baseline_time) + "</baseline_time>"
    Print #1, "<coefficient>" + CStr(coefficient) + "</coefficient>"
    Print #1, "<period>" + CStr(period) + "</period>"
    
    Print #1, "</sinusoidal>"
    Print #1, "</type>"
    
    Print #1, "</sub_fuction>"
End Sub
Sub create_transient_sub_function_gaussian(name, start_time, finish_time, a_coefficient, b_coefficient, c_coefficient)
 Print #1, "<sub_fuction>"
    Print #1, "<name>" + name + "</name>"
    Print #1, "<start_time>" + CStr(start_time) + "</start_time>"
    Print #1, "<finish_time>" + CStr(finish_time) + "</finish_time>"
    
    Print #1, "<type>"
    Print #1, "<gaussian>"
    
    Print #1, "<a_coefficient>" + CStr(a_coefficient) + "</a_coefficient>"
    Print #1, "<b_coefficient>" + CStr(b_coefficient) + "</b_coefficient>"
    Print #1, "<c_coefficient>" + CStr(c_coefficient) + "</c_coefficient>"
    
    Print #1, "</gaussian>"
    Print #1, "</type>"
    
    Print #1, "</sub_fuction>"
End Sub
Sub create_transient_sub_function_pulse(name, start_time, finish_time, amplitude, rise_time, high_time, fall_time)
 Print #1, "<sub_fuction>"
    Print #1, "<name>" + name + "</name>"
    Print #1, "<start_time>" + CStr(start_time) + "</start_time>"
    Print #1, "<finish_time>" + CStr(finish_time) + "</finish_time>"
    
    Print #1, "<type>"
    Print #1, "<pulse>"
    
    Print #1, "<amplitude>" + CStr(amplitude) + "</amplitude>"
    Print #1, "<rise_time>" + CStr(rise_time) + "</rise_time>"
    Print #1, "<high_time>" + CStr(high_time) + "</high_time>"
    Print #1, "<fall_time>" + CStr(fall_time) + "</fall_time>"
    
    Print #1, "</pulse>"
    Print #1, "</type>"
    
    Print #1, "</sub_fuction>"
End Sub
Sub create_transient_sub_function_double_exp(name, start_time, finish_time, amplitude, decay, rise)
 Print #1, "<sub_fuction>"
    Print #1, "<name>" + name + "</name>"
    Print #1, "<start_time>" + CStr(start_time) + "</start_time>"
    Print #1, "<finish_time>" + CStr(finish_time) + "</finish_time>"
    
    Print #1, "<type>"
    Print #1, "<double_exp>"
    
    Print #1, "<amplitude>" + CStr(amplitude) + "</amplitude>"
    Print #1, "<decay>" + CStr(decay) + "</decay>"
    Print #1, "<rise>" + CStr(rise) + "</rise>"
    
    Print #1, "</double_exp>"
    Print #1, "</type>"
    
    Print #1, "</sub_fuction>"
End Sub
Sub create_transient_with_functions_start(name, overlapping_0_add_1_multiply, peroidic_0_false_1_true, multiplier_vs_time_active_0_false_1_true, multiplier_vs_MP_active_0_false_1_true, multiplier_vs_MP_hysteresis_active_0_false_1_true, string_containing_MP_multiplier_pairs_increasing, string_containing_MP_multiplier_pairs_decreasing, associated_monitor_point)
Dim points() As String
Dim k As Integer


Print #1, "<transient_att>"
Print #1, "<name>" + name + "</name>"

If (multiplier_vs_MP_active_0_false_1_true = 1) Then

Print #1, "<transient_temperature_active>true</transient_temperature_active>"

Print #1, "<associated_monitor_point>" + CStr(associated_monitor_point) + "</associated_monitor_point>"

Print #1, "<temp_curve_points>"

points() = Split(string_containing_MP_multiplier_pairs_increasing, ",")

For k = 0 To UBound(points) Step 2
Print #1, "<temp_curve_point>"
Print #1, "<temp>" + points(k) + "</temp><coef>" + points(k + 1) + "</coef>"
Print #1, "</temp_curve_point>"

Next k

Print #1, "</temp_curve_points>"

If (multiplier_vs_MP_hysteresis_active_0_false_1_true = 1) Then

Print #1, "<hysteresis_active>true</hysteresis_active>"

Print #1, "<decreasing_temp_curve_points>"

points() = Split(string_containing_MP_multiplier_pairs_decreasing, ",")

For k = 0 To UBound(points) Step 2
Print #1, "<temp_curve_point>"
Print #1, "<temp>" + points(k) + "</temp><coef>" + points(k + 1) + "</coef>"
Print #1, "</temp_curve_point>"

Next k

Print #1, "</decreasing_temp_curve_points>"

End If

Else

Print #1, "<transient_temperature_active>false</transient_temperature_active>"

End If


If (multiplier_vs_time_active_0_false_1_true = 1) Then

Print #1, "<transient_time_active>true</transient_time_active>"

Else

Print #1, "<transient_time_active>false</transient_time_active>"

End If

Print #1, "<transient_type>function</transient_type>"

If (overlapping_0_add_1_multiply = 0) Then
    Print #1, "<overlapping_functions>add</overlapping_functions>"
ElseIf (overlapping_0_add_1_multiply = 1) Then
    Print #1, "<overlapping_functions>multiply</overlapping_functions>"
End If

If (peroidic_0_false_1_true = 0) Then
    Print #1, "<periodic>false</periodic>"
ElseIf (peroidic_0_false_1_true = 1) Then
    Print #1, "<periodic>true</periodic>"
End If

If (CStr(notes) <> "0") Then
Print #1, "<notes>" + CStr(notes) + "</notes>"
End If

Print #1, "<sub_functions>"

End Sub
Sub end_transient_with_functions()
    Print #1, "</sub_functions>"
    Print #1, "</transient_att>"
End Sub
Sub end_transients()
Print #1, "</transients>"
End Sub
Sub start_fans()
Print #1, "<fans>"
End Sub
Sub create_ftfan(name, flow_type_0_normal_1_angled_2_swirl, angled_x, angled_y, angled_z, swirl_model_0_constant_1_flow_dependant, swirl_direction_0_clockwise_1_counterclockwise, swirl_speed, curve_type_0_fixed_1_linear_2_nonlinear, open_flow_rate, stagnation_pressure, string_containing_fan_curve)
Dim points() As String
Dim k As Integer

Print #1, "<fan_att>"
Print #1, "<name>" + name + "</name>"

If (flow_type_0_normal_1_angled_2_swirl = 0) Then
Print #1, "<flow_type>normal</flow_type>"

ElseIf (flow_type_0_normal_1_angled_2_swirl = 1) Then
Print #1, "<flow_type>angled</flow_type>"
Print #1, "<flow_direction><x>" + CStr(angled_x) + "</x><y>" + CStr(angled_y) + "</y><z>" + CStr(angled_z) + "</z></flow_direction>"

ElseIf (flow_type_0_normal_1_angled_2_swirl = 2) Then
Print #1, "<flow_type>swirl</flow_type>"

    If (swirl_model_0_constant_1_flow_dependant = 0) Then
    Print #1, "<swirl_model>constant_speed</swirl_model>"
    ElseIf (swirl_model_0_constant_1_flow_dependant = 1) Then
    Print #1, "<swirl_model>flow_dependant_speed</swirl_model>"
    End If
    If (swirl_direction_0_clockwise_1_counterclockwise = 0) Then
    Print #1, "<swirl_direction>clockwise</swirl_direction>"
    ElseIf (swirl_direction_0_clockwise_1_counterclockwise = 1) Then
    Print #1, "<swirl_direction>counter_clockwise</swirl_direction>"
    End If
    Print #1, "<swirl_speed>" + CStr(swirl_speed) + "</swirl_speed>"

End If

If (curve_type_0_fixed_1_linear_2_nonlinear = 0) Then
Print #1, "<flow_spec>fixed</flow_spec>"
Print #1, "<flow_rate>" + CStr(open_flow_rate) + "</flow_rate>"
ElseIf (curve_type_0_fixed_1_linear_2_nonlinear = 1) Then
Print #1, "<flow_spec>linear</flow_spec>"
Print #1, "<open_volume_flow_rate>" + CStr(open_flow_rate) + "</open_volume_flow_rate>"
Print #1, "<stagnation_pressure>" + CStr(stagnation_pressure) + "</stagnation_pressure>"
ElseIf (curve_type_0_fixed_1_linear_2_nonlinear = 2) Then
Print #1, "<flow_spec>non_linear</flow_spec>"
Print #1, "<open_volume_flow_rate>" + CStr(open_flow_rate) + "</open_volume_flow_rate>"
Print #1, "<stagnation_pressure>" + CStr(stagnation_pressure) + "</stagnation_pressure>"

Print #1, "<fan_curve_points>"
points() = Split(string_containing_fan_curve, ",")

For k = 0 To UBound(points) Step 2
Print #1, "<fan_curve_point>"
Print #1, "<volume_flow>" + points(k) + "</volume_flow><pressure>" + points(k + 1) + "</pressure>"
Print #1, "</fan_curve_point>"

Next k

Print #1, "</fan_curve_points>"

End If


Print #1, "</fan_att>"
End Sub
Sub create_fvfan(name, flow_type_0_normal_1_angled_2_swirl_3_circular, angled_x, angled_y, angled_z, swirl_model_0_constant_1_flow_dependant, swirl_direction_0_clockwise_1_counterclockwise, swirl_speed, swirl_angle, twist_angled, jet_angle, curve_type_0_fixed_1_linear_2_nonlinear, open_flow_rate, stagnation_pressure, string_containing_fan_curve)
Dim points() As String
Dim k As Integer

Print #1, "<fan_att>"
Print #1, "<name>" + name + "</name>"

If (flow_type_0_normal_1_angled_2_swirl_3_circular = 0) Then
Print #1, "<flow_type>normal</flow_type>"

ElseIf (flow_type_0_normal_1_angled_2_swirl_3_circular = 1) Then
Print #1, "<flow_type>angled</flow_type>"
Print #1, "<flow_direction><x>" + CStr(angled_x) + "</x><y>" + CStr(angled_y) + "</y><z>" + CStr(angled_z) + "</z></flow_direction>"

ElseIf (flow_type_0_normal_1_angled_2_swirl_3_circular = 2) Then
Print #1, "<flow_type>swirl</flow_type>"

    If (swirl_model_0_constant_1_flow_dependant = 0) Then
    Print #1, "<swirl_model>constant_speed</swirl_model>"
    ElseIf (swirl_model_0_constant_1_flow_dependant = 1) Then
    Print #1, "<swirl_model>flow_dependant_speed</swirl_model>"
    End If
    If (swirl_direction_0_clockwise_1_counterclockwise = 0) Then
    Print #1, "<swirl_direction>clockwise</swirl_direction>"
    ElseIf (swirl_direction_0_clockwise_1_counterclockwise = 1) Then
    Print #1, "<swirl_direction>counter_clockwise</swirl_direction>"
    End If
    Print #1, "<swirl_speed>" + CStr(swirl_speed) + "</swirl_speed>"
    Print #1, "<swirl_angle>" + CStr(swirl_angle) + "</swirl_angle>"
    Print #1, "<twist_angle>" + CStr(twist_angle) + "</twist_angle>"

ElseIf (flow_type_0_normal_1_angled_2_swirl_3_circular = 3) Then
Print #1, "<flow_type>circular</flow_type>"
Print #1, "<jet_angle>" + CStr(jet_angle) + "</jet_angle>"

End If

If (curve_type_0_fixed_1_linear_2_nonlinear = 0) Then
Print #1, "<flow_spec>fixed</flow_spec>"
Print #1, "<flow_rate>" + CStr(open_flow_rate) + "</flow_rate>"
ElseIf (curve_type_0_fixed_1_linear_2_nonlinear = 1) Then
Print #1, "<flow_spec>linear</flow_spec>"
Print #1, "<open_volume_flow_rate>" + CStr(open_flow_rate) + "</open_volume_flow_rate>"
Print #1, "<stagnation_pressure>" + CStr(stagnation_pressure) + "</stagnation_pressure>"
ElseIf (curve_type_0_fixed_1_linear_2_nonlinear = 2) Then
Print #1, "<flow_spec>non_linear</flow_spec>"
Print #1, "<open_volume_flow_rate>" + CStr(open_flow_rate) + "</open_volume_flow_rate>"
Print #1, "<stagnation_pressure>" + CStr(stagnation_pressure) + "</stagnation_pressure>"

Print #1, "<fan_curve_points>"
points() = Split(string_containing_fan_curve, ",")

For k = 0 To UBound(points) Step 2
Print #1, "<fan_curve_point>"
Print #1, "<volume_flow>" + points(k) + "</volume_flow><pressure>" + points(k + 1) + "</pressure>"
Print #1, "</fan_curve_point>"

Next k

Print #1, "</fan_curve_points>"

End If


Print #1, "</fan_att>"
End Sub

Sub end_fans()
Print #1, "</fans>"
End Sub
Sub start_geometry()
Print #1, "<geometry>"
End Sub
Sub end_geometry()
Print #1, "</geometry>"
End Sub
Sub build_rectangular_fan(name, x_position, y_position, z_position, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, rectangular_x_size, rectangular_y_size, rotation_axis_0_none_1_x_axis_2_y_axis, rotation_angle, derating_factor, fan_power, fan_noise, fan_curve_attribute, material_attribute, resistance_attribute, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_grid_constraint, all_radiation, transient, localized_grid_0_false_1_true, hidden_0_false_1_true, fan_failed_0_true_1_false, notes, active_0_false_1_true)

Print #1, "<fan>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

Print #1, "<fan_geometry>"
Print #1, "<rectangular_geom>"
Print #1, "<size>"
Print #1, "<x>" + CStr(rectangular_x_size) + "</x>"
Print #1, "<y>" + CStr(rectangular_y_size) + "</y>"
Print #1, "</size>"

Select Case rotation_axis_0_none_1_x_axis_2_y_axis
    Case 0
        Print #1, "<rotated_about>none</rotated_about>"
    Case 1
        Print #1, "<rotated_about>x_axis</rotated_about>"
        Print #1, "<angle>" + CStr(rotation_angle) + "</angle>"
    Case 2
        Print #1, "<rotated_about>y_axis</rotated_about>"
        Print #1, "<angle>" + CStr(rotation_angle) + "</angle>"
        
End Select

Print #1, "</rectangular_geom>"
Print #1, "</fan_geometry>"

Print #1, "<derating_factor>" + CStr(derating_factor) + "</derating_factor>"
Print #1, "<fan_power>" + CStr(fan_power) + "</fan_power>"
Print #1, "<fan_noise>" + CStr(fan_noise) + "</fan_noise>"

Select Case use_fan_power_0_true_1_false
    Case 0
        Print #1, "<use_fan_power>true</use_fan_power>"
    Case 1
        Print #1, "<use_fan_power>false</use_fan_power>"
End Select

Select Case fan_failed_0_true_1_false
    Case 0
        Print #1, "<fan_failed>true</fan_failed>"
    Case 1
        Print #1, "<fan_failed>false</fan_failed>"
End Select

If (fan_curve_attribute <> "0") Then
Print #1, "<fan>" + fan_curve_attribute + "</fan>"
End If

If (material_attribute <> "0") Then
Print #1, "<material>" + material_attribute + "</material>"
End If

If (resistance_attribute <> "0") Then
Print #1, "<resistance>" + resistance_attribute + "</resistance>"
End If

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint + "</all_grid_constraint>"
End If

If (all_radiation <> "0") Then
Print #1, "<all_radiation>" + all_radiation + "</all_radiation>"
End If

If (transient <> "0") Then
Print #1, "<transient>" + transient + "</transient>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

Print #1, "</fan>"

End Sub
Sub build_axial_fan(name, x_position, y_position, z_position, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, axial_hub_diameter, axial_outer_diameter, axial_depth, axial_modeling_level_0_2d_1_2dHub_2_3d_4facets_3_3d_8facets_4_3d_12facets_5_3d_8facets4hub_6_12facets_4hub, primitive_location_0_front_1_back, free_area_ratio, derating_factor, fan_power, use_fan_power_0_true_1_false, fan_noise, fan_failed_0_true_1_false, fan_curve_attribute, material_attribute, resistance_attribute, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_grid_constraint, all_radiation, transient, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<fan>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"


Print #1, "<fan_geometry>"
Print #1, "<axial_geom>"
Print #1, "<outer_diameter>" + CStr(axial_outer_diameter) + "</outer_diameter>"
Print #1, "<hub_diameter>" + CStr(axial_hub_diameter) + "</hub_diameter>"
Print #1, "<depth>" + CStr(axial_depth) + "</depth>"

Select Case axial_modeling_level_0_2d_1_2dHub_2_3d_4facets_3_3d_8facets_4_3d_12facets_5_3d_8facets4hub_6_12facets_4hub
    Case 0
        Print #1, "<modeling_level>simple_2d</modeling_level>"
    Case 1
        Print #1, "<modeling_level>2d_with_hub</modeling_level>"
    Case 2
        Print #1, "<modeling_level>3d_4_facets</modeling_level>"
    Case 3
        Print #1, "<modeling_level>3d_8_facets</modeling_level>"
    Case 4
        Print #1, "<modeling_level>3d_12_facets</modeling_level>"
    Case 5
        Print #1, "<modeling_level>3d_8_facets_4_hub</modeling_level>"
    Case 6
        Print #1, "<modeling_level>3d_12_facets_4_hub</modeling_level>"
End Select

Select Case primitive_location_0_front_1_back
    Case 0
        Print #1, "<primitive_location>front</primitive_location>"
    Case 1
        Print #1, "<primitive_location>back</primitive_location>"
End Select

Print #1, "</axial_geom>"
Print #1, "</fan_geometry>"

Print #1, "<free_area_ratio>" + CStr(free_area_ratio) + "</free_area_ratio>"
Print #1, "<derating_factor>" + CStr(derating_factor) + "</derating_factor>"
Print #1, "<fan_power>" + CStr(fan_power) + "</fan_power>"
Print #1, "<fan_noise>" + CStr(fan_noise) + "</fan_noise>"

Select Case use_fan_power_0_true_1_false
    Case 0
        Print #1, "<use_fan_power>true</use_fan_power>"
    Case 1
        Print #1, "<use_fan_power>false</use_fan_power>"
End Select

Select Case fan_failed_0_true_1_false
    Case 0
        Print #1, "<fan_failed>true</fan_failed>"
    Case 1
        Print #1, "<fan_failed>false</fan_failed>"
End Select

If (fan_curve_attribute <> "0") Then
Print #1, "<fan>" + fan_curve_attribute + "</fan>"
End If

If (material_attribute <> "0") Then
Print #1, "<material>" + material_attribute + "</material>"
End If

If (resistance_attribute <> "0") Then
Print #1, "<resistance>" + resistance_attribute + "</resistance>"
End If

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint + "</all_grid_constraint>"
End If

If (all_radiation <> "0") Then
Print #1, "<all_radiation>" + all_radiation + "</all_radiation>"
End If

If (transient <> "0") Then
Print #1, "<transient>" + transient + "</transient>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

Print #1, "</fan>"
End Sub
Sub build_prism(name, x_position, y_position, z_position, x_size, y_size, z_size, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, material, thermal, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_directions_grid_constraint, x_low_surface, y_low_surface, z_low_surface, z_high_surface, sloping_surface, all_faces_surface, x_low_radiation, y_low_radiation, z_low_radiation, z_high_radiation, sloping_radiation, all_faces_radiation, x_low_surface_exchange, y_low_surface_exchange, z_low_surface_exchange, z_high_surface_exchange, sloping_surface_exchange, all_faces_surface_exchange, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<prism>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y><z>" + CStr(z_size) + "</z></size>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

If (material <> "0") Then
Print #1, "<material>" + material + "</material>"
End If

If (thermal <> "0") Then
Print #1, "<thermal>" + thermal + "</thermal>"
End If

If (x_low_surface <> "0") Then
Print #1, "<x_low_surface>" + x_low_surface + "</x_low_surface>"
End If

If (y_low_surface <> "0") Then
Print #1, "<y_low_surface>" + y_low_surface + "</y_low_surface>"
End If

If (z_low_surface <> "0") Then
Print #1, "<z_low_surface>" + z_low_surface + "</z_low_surface>"
End If

If (z_high_surface <> "0") Then
Print #1, "<z_high_surface>" + z_high_surface + "</z_high_surface>"
End If

If (sloping_surface <> "0") Then
Print #1, "<sloping_face_surface>" + sloping_surface + "</sloping_face_surface>"
End If

If (all_faces_surface <> "0") Then
Print #1, "<all_surface>" + all_faces_surface + "</all_surface>"
End If

If (x_low_radiation <> "0") Then
Print #1, "<x_low_radiation>" + x_low_radiation + "</x_low_radiation>"
End If

If (y_low_radiation <> "0") Then
Print #1, "<y_low_radiation>" + y_low_radiation + "</y_low_radiation>"
End If

If (z_low_radiation <> "0") Then
Print #1, "<z_low_radiation>" + z_low_radiation + "</z_low_radiation>"
End If

If (z_high_radiation <> "0") Then
Print #1, "<z_high_radiation>" + z_high_radiation + "</z_high_radiation>"
End If

If (sloping_radiation <> "0") Then
Print #1, "<sloping_face_radiation>" + sloping_radiation + "</sloping_face_radiation>"
End If

If (all_faces_radiation <> "0") Then
Print #1, "<all_radiation>" + all_faces_radiation + "</all_radiation>"
End If

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_directions_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_directions_grid_constraint + "</all_grid_constraint>"
End If

If (x_low_surface_exchange <> "0") Then
Print #1, "<x_low_surface_exchange>" + x_low_surface_exchange + "</x_low_surface_exchange>"
End If

If (y_low_surface_exchange <> "0") Then
Print #1, "<y_low_surface_exchange>" + y_low_surface_exchange + "</y_low_surface_exchange>"
End If

If (z_low_surface_exchange <> "0") Then
Print #1, "<z_low_surface_exchange>" + z_low_surface_exchange + "</z_low_surface_exchange>"
End If

If (z_high_surface_exchange <> "0") Then
Print #1, "<z_high_surface_exchange>" + z_high_surface_exchange + "</z_high_surface_exchange>"
End If

If (sloping_surface_exchange <> "0") Then
Print #1, "<sloping_face_surface_exchange>" + sloping_surface_exchange + "</sloping_face_surface_exchange>"
End If

If (all_faces_surface_exchange <> "0") Then
Print #1, "<all_surface_exchange>" + all_faces_surface_exchange + "</all_surface_exchange>"
End If


If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</prism>"

End Sub
Sub build_tet(name, x_position, y_position, z_position, x_size, y_size, z_size, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, material, thermal, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_directions_grid_constraint, x_low_surface, y_low_surface, z_low_surface, sloping_surface, all_faces_surface, x_low_radiation, y_low_radiation, z_low_radiation, sloping_radiation, all_faces_radiation, x_low_surface_exchange, y_low_surface_exchange, z_low_surface_exchange, sloping_surface_exchange, all_faces_surface_exchange, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<tet>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y><z>" + CStr(z_size) + "</z></size>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

If (material <> "0") Then
Print #1, "<material>" + material + "</material>"
End If

If (thermal <> "0") Then
Print #1, "<thermal>" + thermal + "</thermal>"
End If

If (x_low_surface <> "0") Then
Print #1, "<x_low_surface>" + x_low_surface + "</x_low_surface>"
End If

If (y_low_surface <> "0") Then
Print #1, "<y_low_surface>" + y_low_surface + "</y_low_surface>"
End If

If (z_low_surface <> "0") Then
Print #1, "<z_low_surface>" + z_low_surface + "</z_low_surface>"
End If

If (sloping_surface <> "0") Then
Print #1, "<sloping_face_surface>" + sloping_surface + "</sloping_face_surface>"
End If

If (all_faces_surface <> "0") Then
Print #1, "<all_surface>" + all_faces_surface + "</all_surface>"
End If

If (x_low_radiation <> "0") Then
Print #1, "<x_low_radiation>" + x_low_radiation + "</x_low_radiation>"
End If

If (y_low_radiation <> "0") Then
Print #1, "<y_low_radiation>" + y_low_radiation + "</y_low_radiation>"
End If

If (z_low_radiation <> "0") Then
Print #1, "<z_low_radiation>" + z_low_radiation + "</z_low_radiation>"
End If

If (sloping_radiation <> "0") Then
Print #1, "<sloping_face_radiation>" + sloping_radiation + "</sloping_face_radiation>"
End If

If (all_faces_radiation <> "0") Then
Print #1, "<all_radiation>" + all_faces_radiation + "</all_radiation>"
End If

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_directions_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_directions_grid_constraint + "</all_grid_constraint>"
End If

If (x_low_surface_exchange <> "0") Then
Print #1, "<x_low_surface_exchange>" + x_low_surface_exchange + "</x_low_surface_exchange>"
End If

If (y_low_surface_exchange <> "0") Then
Print #1, "<y_low_surface_exchange>" + y_low_surface_exchange + "</y_low_surface_exchange>"
End If

If (z_low_surface_exchange <> "0") Then
Print #1, "<z_low_surface_exchange>" + z_low_surface_exchange + "</z_low_surface_exchange>"
End If

If (sloping_surface_exchange <> "0") Then
Print #1, "<sloping_face_surface_exchange>" + sloping_surface_exchange + "</sloping_face_surface_exchange>"
End If

If (all_faces_surface_exchange <> "0") Then
Print #1, "<all_surface_exchange>" + all_faces_surface_exchange + "</all_surface_exchange>"
End If


If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</tet>"

End Sub
Sub build_inverted_tet(name, x_position, y_position, z_position, x_size, y_size, z_size, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, material, thermal, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_directions_grid_constraint, x_low_surface, x_high_surface, y_low_surface, y_high_surface, z_low_surface, z_high_surface, sloping_surface, all_faces_surface, x_low_radiation, x_high_radiation, y_low_radiation, y_high_radiation, z_low_radiation, z_high_radiation, sloping_radiation, all_faces_radiation, x_low_surface_exchange, x_high_surface_exchange, y_low_surface_exchange, y_high_surface_exchange, z_low_surface_exchange, z_high_surface_exchange, sloping_surface_exchange, all_faces_surface_exchange, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<inverted_tet>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y><z>" + CStr(z_size) + "</z></size>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

If (material <> "0") Then
Print #1, "<material>" + material + "</material>"
End If

If (thermal <> "0") Then
Print #1, "<thermal>" + thermal + "</thermal>"
End If

If (x_low_surface <> "0") Then
Print #1, "<x_low_surface>" + x_low_surface + "</x_low_surface>"
End If

If (x_high_surface <> "0") Then
Print #1, "<x_high_surface>" + x_high_surface + "</x_high_surface>"
End If

If (y_low_surface <> "0") Then
Print #1, "<y_low_surface>" + y_low_surface + "</y_low_surface>"
End If

If (y_high_surface <> "0") Then
Print #1, "<y_high_surface>" + y_high_surface + "</y_high_surface>"
End If

If (z_low_surface <> "0") Then
Print #1, "<z_low_surface>" + z_low_surface + "</z_low_surface>"
End If

If (z_high_surface <> "0") Then
Print #1, "<z_high_surface>" + z_high_surface + "</z_high_surface>"
End If

If (sloping_surface <> "0") Then
Print #1, "<sloping_face_surface>" + sloping_surface + "</sloping_face_surface>"
End If

If (all_faces_surface <> "0") Then
Print #1, "<all_surface>" + all_faces_surface + "</all_surface>"
End If

If (x_low_radiation <> "0") Then
Print #1, "<x_low_radiation>" + x_low_radiation + "</x_low_radiation>"
End If

If (x_high_radiation <> "0") Then
Print #1, "<x_high_radiation>" + x_high_radiation + "</x_high_radiation>"
End If

If (y_low_radiation <> "0") Then
Print #1, "<y_low_radiation>" + y_low_radiation + "</y_low_radiation>"
End If

If (y_high_radiation <> "0") Then
Print #1, "<y_high_radiation>" + y_high_radiation + "</y_high_radiation>"
End If

If (z_low_radiation <> "0") Then
Print #1, "<z_low_radiation>" + z_low_radiation + "</z_low_radiation>"
End If

If (z_high_radiation <> "0") Then
Print #1, "<z_high_radiation>" + z_high_radiation + "</z_high_radiation>"
End If

If (sloping_radiation <> "0") Then
Print #1, "<sloping_face_radiation>" + sloping_radiation + "</sloping_face_radiation>"
End If

If (all_faces_radiation <> "0") Then
Print #1, "<all_radiation>" + all_faces_radiation + "</all_radiation>"
End If

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_directions_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_directions_grid_constraint + "</all_grid_constraint>"
End If

If (x_low_surface_exchange <> "0") Then
Print #1, "<x_low_surface_exchange>" + x_low_surface_exchange + "</x_low_surface_exchange>"
End If

If (x_high_surface_exchange <> "0") Then
Print #1, "<x_high_surface_exchange>" + x_high_surface_exchange + "</x_high_surface_exchange>"
End If

If (y_low_surface_exchange <> "0") Then
Print #1, "<y_low_surface_exchange>" + y_low_surface_exchange + "</y_low_surface_exchange>"
End If

If (y_high_surface_exchange <> "0") Then
Print #1, "<y_high_surface_exchange>" + y_high_surface_exchange + "</y_high_surface_exchange>"
End If

If (z_low_surface_exchange <> "0") Then
Print #1, "<z_low_surface_exchange>" + z_low_surface_exchange + "</z_low_surface_exchange>"
End If

If (z_high_surface_exchange <> "0") Then
Print #1, "<z_high_surface_exchange>" + z_high_surface_exchange + "</z_high_surface_exchange>"
End If

If (sloping_surface_exchange <> "0") Then
Print #1, "<sloping_face_surface_exchange>" + sloping_surface_exchange + "</sloping_face_surface_exchange>"
End If

If (all_faces_surface_exchange <> "0") Then
Print #1, "<all_surface_exchange>" + all_faces_surface_exchange + "</all_surface_exchange>"
End If


If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</inverted_tet>"

End Sub
Sub build_sloping_block(name, x_position, y_position, z_position, width, thick_0_true_1_false, thickness, use_0_angle_1_sides, angle, length, opposite, adjacent, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, material, thermal, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_directions_grid_constraint, x_low_surface, x_high_surface, y_low_surface, y_high_surface, z_low_surface, z_high_surface, all_faces_surface, x_low_radiation, x_high_radiation, y_low_radiation, y_high_radiation, z_low_radiation, z_high_radiation, all_faces_radiation, x_low_surface_exchange, x_high_surface_exchange, y_low_surface_exchange, y_high_surface_exchange, z_low_surface_exchange, z_high_surface_exchange, all_faces_surface_exchange, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<sloping_block>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

If (thick_0_true_1_false = 0) Then
Print #1, "<thick>true</thick>"
ElseIf (thick_0_true_1_false = 1) Then
Print #1, "<thick>false</thick>"
End If

If (use_0_angle_1_sides = 0) Then
Print #1, "<use>use_angle</use>"
Print #1, "<length>" + CStr(length) + "</length>"
Print #1, "<angle>" + CStr(angle) + "</angle>"
ElseIf (use_0_angle_1_sides = 1) Then
Print #1, "<use>use_sides</use>"
Print #1, "<opposite>" + CStr(opposite) + "</opposite>"
Print #1, "<adjacent>" + CStr(adjacent) + "</adjacent>"
End If

Print #1, "<width>" + CStr(width) + "</width>"
Print #1, "<thickness>" + CStr(thickness) + "</thickness>"

If (material <> "0") Then
Print #1, "<material>" + material + "</material>"
End If

If (thermal <> "0") Then
Print #1, "<thermal>" + thermal + "</thermal>"
End If

If (x_low_surface <> "0") Then
Print #1, "<x_low_surface>" + x_low_surface + "</x_low_surface>"
End If

If (x_high_surface <> "0") Then
Print #1, "<x_high_surface>" + x_high_surface + "</x_high_surface>"
End If

If (y_low_surface <> "0") Then
Print #1, "<y_low_surface>" + y_low_surface + "</y_low_surface>"
End If

If (y_high_surface <> "0") Then
Print #1, "<y_high_surface>" + y_high_surface + "</y_high_surface>"
End If

If (z_low_surface <> "0") Then
Print #1, "<z_low_surface>" + z_low_surface + "</z_low_surface>"
End If

If (z_high_surface <> "0") Then
Print #1, "<z_high_surface>" + z_high_surface + "</z_high_surface>"
End If

If (all_faces_surface <> "0") Then
Print #1, "<all_surface>" + all_faces_surface + "</all_surface>"
End If

If (x_low_radiation <> "0") Then
Print #1, "<x_low_radiation>" + x_low_radiation + "</x_low_radiation>"
End If

If (x_high_radiation <> "0") Then
Print #1, "<x_high_radiation>" + x_high_radiation + "</x_high_radiation>"
End If

If (y_low_radiation <> "0") Then
Print #1, "<y_low_radiation>" + y_low_radiation + "</y_low_radiation>"
End If

If (y_high_radiation <> "0") Then
Print #1, "<y_high_radiation>" + y_high_radiation + "</y_high_radiation>"
End If

If (z_low_radiation <> "0") Then
Print #1, "<z_low_radiation>" + z_low_radiation + "</z_low_radiation>"
End If

If (z_high_radiation <> "0") Then
Print #1, "<z_high_radiation>" + z_high_radiation + "</z_high_radiation>"
End If

If (all_faces_radiation <> "0") Then
Print #1, "<all_radiation>" + all_faces_radiation + "</all_radiation>"
End If

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_directions_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_directions_grid_constraint + "</all_grid_constraint>"
End If

If (x_low_surface_exchange <> "0") Then
Print #1, "<x_low_surface_exchange>" + x_low_surface_exchange + "</x_low_surface_exchange>"
End If

If (x_high_surface_exchange <> "0") Then
Print #1, "<x_high_surface_exchange>" + x_high_surface_exchange + "</x_high_surface_exchange>"
End If

If (y_low_surface_exchange <> "0") Then
Print #1, "<y_low_surface_exchange>" + y_low_surface_exchange + "</y_low_surface_exchange>"
End If

If (y_high_surface_exchange <> "0") Then
Print #1, "<y_high_surface_exchange>" + y_high_surface_exchange + "</y_high_surface_exchange>"
End If

If (z_low_surface_exchange <> "0") Then
Print #1, "<z_low_surface_exchange>" + z_low_surface_exchange + "</z_low_surface_exchange>"
End If

If (z_high_surface_exchange <> "0") Then
Print #1, "<z_high_surface_exchange>" + z_high_surface_exchange + "</z_high_surface_exchange>"
End If

If (all_faces_surface_exchange <> "0") Then
Print #1, "<all_surface_exchange>" + all_faces_surface_exchange + "</all_surface_exchange>"
End If


If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</sloping_block>"

End Sub
Sub build_heat_sink_pin_fin(name, x_pos, y_pos, z_pos, base_x_size, base_y_size, base_z_size, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, detailed_0_compact_1, pin_height, pin_style_0_uniform_1_taper, pin_type_0_rect_1_circ, pin_length, pin_width, taper_tip_width, pin_diameter, taper_tip_diameter, pin_facets_4_8_12, pins_0_inline_1_staggered, pins_in_x, pins_in_y, x_centre_gap, y_centre_gap, cells_between_fins, fab_type_0_extruded_1_bonded, groove_depth, groove_width, fin_material, adhesive_material, material, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_directions_grid_constraint, all_faces_radiation, all_faces_surface_exchange, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<heatsink>"
Print #1, "<name>" + name + "</name>"

Print #1, "<heat_sink_type>pin_fin</heat_sink_type>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_pos) + "</x><y>" + CStr(y_pos) + "</y><z>" + CStr(z_pos) + "</z></position>"
Print #1, "<heat_sink_base><x>" + CStr(base_x_size) + "</x><y>" + CStr(base_y_size) + "</y><z>" + CStr(base_z_size) + "</z></heat_sink_base>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"


If (detailed_0_compact_1 = 0) Then
Print #1, "<modeling_method>detailed</modeling_method>"
ElseIf (detailed_0_compact_1 = 1) Then
Print #1, "<modeling_method>compact</modeling_method>"
End If

Print #1, "<pin_definition>"
Print #1, "<pin_geometry>"

Print #1, "<pin_height>" + CStr(pin_height) + "</pin_height>"

If (pin_style_0_uniform_1_taper = 0) Then
Print #1, "<pin_style>uniform</pin_style>"
ElseIf (pin_style_0_uniform_1_taper = 1) Then
Print #1, "<pin_style>full_taper</pin_style>"
End If

If (pin_type_0_rect_1_circ = 0) Then
Print #1, "<pin_type>rectangular</pin_type>"
ElseIf (pin_type_0_rect_1_circ = 1) Then
Print #1, "<pinpin_type_style>circular</pin_type>"
End If

Print #1, "<uniform_length>" + CStr(pin_length) + "</uniform_length>"
Print #1, "<uniform_width>" + CStr(pin_width) + "</uniform_width>"
Print #1, "<tapered_length>" + CStr(pin_length) + "</tapered_length>"
Print #1, "<tapered_base_width>" + CStr(pin_width) + "</tapered_base_width>"
Print #1, "<tapered_tip_width>" + CStr(taper_tip_width) + "</tapered_tip_width>"
Print #1, "<circular_diameter>" + CStr(pin_diameter) + "</circular_diameter>"
Print #1, "<circular_base_diameter>" + CStr(pin_diameter) + "</circular_base_diameter>"
Print #1, "<circular_tip_diameter>" + CStr(taper_tip_diameter) + "</circular_tip_diameter>"

If (pin_facets_4_8_12 <> 0) Then

Select Case pin_facets_4_8_12
    Case 4
        Print #1, "<modeling_level>4 facets</modeling_level>"
    Case 8
        Print #1, "<modeling_level>8 facets</modeling_level>"
    Case 12
        Print #1, "<modeling_level>12 facets</modeling_level>"
End Select

End If
Print #1, "</pin_geometry>"

If (pins_0_inline_1_staggered = 0) Then
Print #1, "<pin_arrangement>inline</pin_arrangement>"
Else
Print #1, "<pin_arrangement>staggered</pin_arrangement>"
End If

Print #1, "<pins_in_x_direction>" + CStr(pins_in_x) + "</pins_in_x_direction>"
Print #1, "<pins_in_y_direction>" + CStr(pins_in_y) + "</pins_in_y_direction>"
Print #1, "<x_center_gap>" + CStr(x_centre_gap) + "</x_center_gap>"
Print #1, "<y_center_gap>" + CStr(y_centre_gap) + "</y_center_gap>"
Print #1, "<cells_between_pins>" + CStr(cells_between_fins) + "</cells_between_pins>"

Print #1, "</pin_definition>"

Print #1, "<fabrication>"

If (fab_type_0_extruded_1_bonded = 0) Then
    Print #1, "<fabrication_type>extruded_cast</fabrication_type>"
Else
    Print #1, "<fabrication_type>bonded</fabrication_type>"
    Print #1, "<groove_depth>" + CStr(groove_depth) + "</groove_depth>"
    Print #1, "<groove_width>" + CStr(groove_width) + "</groove_width>"
        If (fin_material <> "0") Then
            Print #1, "<fin_material>" + fin_material + "</fin_material>"
        End If
        If (adhesive_material <> "0") Then
            Print #1, "<adhesive_material>" + adhesive_material + "</adhesive_material>"
        End If
End If

Print #1, "</fabrication>"


If (material <> "0") Then
Print #1, "<material>" + material + "</material>"
End If

If (all_faces_radiation <> "0") Then
Print #1, "<all_radiation>" + all_faces_radiation + "</all_radiation>"
End If

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_directions_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_directions_grid_constraint + "</all_grid_constraint>"
End If

If (all_faces_surface_exchange <> "0") Then
Print #1, "<all_surface_exchange>" + all_faces_surface_exchange + "</all_surface_exchange>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</heatsink>"

End Sub
Sub build_heat_sink_plate_fin(name, x_pos, y_pos, z_pos, base_x_size, base_y_size, base_z_size, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, detailed_0_compact_1, number_internal_fins, fin_height, fin_style_0_uniform_1_taper, fin_width, taper_tip_width, centre_gap, high_side_fin_inset, low_side_fin_inset, cells_between_fins, left_offset, right_offset, right_fin_standard_0_false_1_true, left_fin_standard_0_false_1_true, right_style_0_uniform_1_taper, right_width, right_taper_tip_width, right_foot_length, right_foot_thickness, left_fin_style_0_uniform_1_full_tap, left_uniform_width, left_tapered_tip_width, left_foot_length, left_foot_thickness, fab_type_0_extruded_1_bonded, groove_depth, groove_width, fin_material, adhesive_material, material, x_grid, y_grid, z_grid, all_directions_grid, all_faces_radiation, all_faces_surface_exchange, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<heatsink>"
Print #1, "<name>" + name + "</name>"

Print #1, "<heat_sink_type>plate_fin</heat_sink_type>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_pos) + "</x><y>" + CStr(y_pos) + "</y><z>" + CStr(z_pos) + "</z></position>"
Print #1, "<heat_sink_base><x>" + CStr(base_x_size) + "</x><y>" + CStr(base_y_size) + "</y><z>" + CStr(base_z_size) + "</z></heat_sink_base>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"


If (detailed_0_compact_1 = 0) Then
Print #1, "<modeling_method>detailed</modeling_method>"
ElseIf (detailed_0_compact_1 = 1) Then
Print #1, "<modeling_method>compact</modeling_method>"
End If

Print #1, "<plate_definition>"
Print #1, "<number_internal_fins>" + CStr(number_internal_fins) + "</number_internal_fins>"
Print #1, "<internal_fins>"
Print #1, "<fin_height>" + CStr(fin_height) + "</fin_height>"

If (fin_style_0_uniform_1_taper = 0) Then
Print #1, "<fin_style>uniform</fin_style>"
ElseIf (fin_style_0_uniform_1_taper = 1) Then
Print #1, "<fin_style>full_taper</fin_style>"
End If

Print #1, "<uniform_width>" + CStr(fin_width) + "</uniform_width>"
Print #1, "<tapered_base_width>" + CStr(fin_width) + "</tapered_base_width>"
Print #1, "<tapered_tip_width>" + CStr(taper_tip_width) + "</tapered_tip_width>"

Print #1, "</internal_fins>"

Print #1, "<center_gap>" + CStr(centre_gap) + "</center_gap>"
Print #1, "<high_side_fin_inset>" + CStr(high_side_fin_inset) + "</high_side_fin_inset>"
Print #1, "<low_side_fin_inset>" + CStr(low_side_fin_inset) + "</low_side_fin_inset>"
Print #1, "<cells_between_fins>" + CStr(cells_between_fins) + "</cells_between_fins>"

Print #1, "<end_fins>"
Print #1, "<left_offset>" + CStr(left_offset) + "</left_offset>"
Print #1, "<right_offset>" + CStr(right_offset) + "</right_offset>"

If (right_fin_standard_0_false_1_true = 1 And left_fin_standard_0_false_1_true = 1) Then
    Print #1, "<end_fin_style>use_as_internal</end_fin_style>"
Else
    Print #1, "<end_fin_style>use_defined</end_fin_style>"
        If (right_fin_standard_0_false_1_true = 0) Then
            Print #1, "<right_fin>"
                If (right_style_0_uniform_1_taper = 0) Then
                Print #1, "<fin_style>uniform</fin_style>"
                ElseIf (right_style_0_uniform_1_taper = 1) Then
                Print #1, "<fin_style>full_taper</fin_style>"
                End If

                Print #1, "<uniform_width>" + CStr(right_width) + "</uniform_width>"
                Print #1, "<tapered_base_width>" + CStr(right_width) + "</tapered_base_width>"
                Print #1, "<tapered_tip_width>" + CStr(right_taper_tip_width) + "</tapered_tip_width>"
            Print #1, "</right_fin>"
            Print #1, "<right_fin_bracket>"
                Print #1, "<foot_length>" + CStr(right_foot_length) + "</foot_length>"
                Print #1, "<foot_thickness>" + CStr(right_foot_thickness) + "</foot_thickness>"
            Print #1, "</right_fin_bracket>"
        End If
        If (left_fin_standard_0_false_1_true = 0) Then
            Print #1, "<left_fin>"
                If (left_style_0_uniform_1_taper = 0) Then
                Print #1, "<fin_style>uniform</fin_style>"
                ElseIf (left_style_0_uniform_1_taper = 1) Then
                Print #1, "<fin_style>full_taper</fin_style>"
                End If

                Print #1, "<uniform_width>" + CStr(left_width) + "</uniform_width>"
                Print #1, "<tapered_base_width>" + CStr(left_width) + "</tapered_base_width>"
                Print #1, "<tapered_tip_width>" + CStr(left_taper_tip_width) + "</tapered_tip_width>"
            Print #1, "</left_fin>"
            Print #1, "<left_fin_bracket>"
                Print #1, "<foot_length>" + CStr(left_foot_length) + "</foot_length>"
                Print #1, "<foot_thickness>" + CStr(left_foot_thickness) + "</foot_thickness>"
            Print #1, "</left_fin_bracket>"
        End If
End If

Print #1, "</end_fins>"
Print #1, "</plate_definition>"
Print #1, "<fabrication>"

If (fab_type_0_extruded_1_bonded = 0) Then
    Print #1, "<fabrication_type>extruded_cast</fabrication_type>"
Else
    Print #1, "<fabrication_type>bonded</fabrication_type>"
    Print #1, "<groove_depth>" + CStr(groove_depth) + "</groove_depth>"
    Print #1, "<groove_width>" + CStr(groove_width) + "</groove_width>"
        If (fin_material <> "0") Then
            Print #1, "<fin_material>" + fin_material + "</fin_material>"
        End If
        If (adhesive_material <> "0") Then
            Print #1, "<adhesive_material>" + adhesive_material + "</adhesive_material>"
        End If
End If

Print #1, "</fabrication>"


If (material <> "0") Then
Print #1, "<material>" + material + "</material>"
End If

If (all_faces_radiation <> "0") Then
Print #1, "<all_radiation>" + all_faces_radiation + "</all_radiation>"
End If

If (x_grid <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid + "</x_grid_constraint>"
End If
If (y_grid <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid + "</y_grid_constraint>"
End If
If (z_grid <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid + "</z_grid_constraint>"
End If
If (all_directions_grid <> "0") Then
Print #1, "<all_grid_constraint>" + all_directions_grid + "</all_grid_constraint>"
End If

If (all_faces_surface_exchange <> "0") Then
Print #1, "<all_surface_exchange>" + all_faces_surface_exchange + "</all_surface_exchange>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</heatsink>"

End Sub
Sub build_tec(name, x_position, y_position, z_position, x_size, y_size, z_size, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, ceramic_thickness, operational_current, hot_side_1_temperature, hot_side_1_q_max, hot_side_1_delta_t_max, hot_side_1_i_max, hot_side_1_v_max, hot_side_2_temperature, hot_side_2_q_max, hot_side_2_delta_t_max, hot_side_2_i_max, hot_side_2_v_max, material, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_directions_grid_constraint, z_low_surface, z_high_surface, z_low_radiation, z_high_radiation, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<tec>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y><z>" + CStr(z_size) + "</z></size>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

Print #1, "<ceramic_thickness>" + CStr(ceramic_thickness) + "</ceramic_thickness>"

If (material <> "0") Then
Print #1, "<ceramic_material>" + material + "</ceramic_material>"
End If

Print #1, "<operational_current>" + CStr(operational_current) + "</operational_current>"

Print #1, "<hot_side_1>"
Print #1, "<temperature>" + CStr(hot_side_1_temperature) + "</temperature>"
Print #1, "<q_max>" + CStr(hot_side_1_q_max) + "</q_max>"
Print #1, "<delta_t_max>" + CStr(hot_side_1_delta_t_max) + "</delta_t_max>"
Print #1, "<i_max>" + CStr(hot_side_1_i_max) + "</i_max>"
Print #1, "<v_max>" + CStr(hot_side_1_v_max) + "</v_max>"
Print #1, "</hot_side_1>"

Print #1, "<hot_side_2>"
Print #1, "<temperature>" + CStr(hot_side_2_temperature) + "</temperature>"
Print #1, "<q_max>" + CStr(hot_side_2_q_max) + "</q_max>"
Print #1, "<delta_t_max>" + CStr(hot_side_2_delta_t_max) + "</delta_t_max>"
Print #1, "<i_max>" + CStr(hot_side_2_i_max) + "</i_max>"
Print #1, "<v_max>" + CStr(hot_side_2_v_max) + "</v_max>"
Print #1, "</hot_side_2>"

If (z_low_surface <> "0") Then
Print #1, "<z_low_surface>" + z_low_surface + "</z_low_surface>"
End If

If (z_high_surface <> "0") Then
Print #1, "<z_high_surface>" + z_high_surface + "</z_high_surface>"
End If

If (z_low_radiation <> "0") Then
Print #1, "<z_low_radiation>" + z_low_radiation + "</z_low_radiation>"
End If

If (z_high_radiation <> "0") Then
Print #1, "<z_high_radiation>" + z_high_radiation + "</z_high_radiation>"
End If

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_directions_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_directions_grid_constraint + "</all_grid_constraint>"
End If


If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</tec>"

End Sub
Sub build_cuboid(name, x_position, y_position, z_position, x_size, y_size, z_size, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, collapse_direction_0_nocollapse_1_x_2_y_3_z, collapse_face_0_lowface_1_midpoint_2_highface, material, thermal, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_directions_grid_constraint, x_low_surface, x_high_surface, y_low_surface, y_high_surface, z_low_surface, z_high_surface, all_faces_surface, x_low_radiation, x_high_radiation, y_low_radiation, y_high_radiation, z_low_radiation, z_high_radiation, all_faces_radiation, x_low_surface_exchange, x_high_surface_exchange, y_low_surface_exchange, y_high_surface_exchange, z_low_surface_exchange, z_high_surface_exchange, all_faces_surface_exchange, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<cuboid>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

If (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
End If



Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y><z>" + CStr(z_size) + "</z></size>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

If (material <> "0") Then
Print #1, "<material>" + material + "</material>"
End If

If (thermal <> "0") Then
Print #1, "<thermal>" + thermal + "</thermal>"
End If

If (x_low_surface <> "0") Then
Print #1, "<x_low_surface>" + x_low_surface + "</x_low_surface>"
End If

If (x_high_surface <> "0") Then
Print #1, "<x_high_surface>" + x_high_surface + "</x_high_surface>"
End If

If (y_low_surface <> "0") Then
Print #1, "<y_low_surface>" + y_low_surface + "</y_low_surface>"
End If

If (y_high_surface <> "0") Then
Print #1, "<y_high_surface>" + y_high_surface + "</y_high_surface>"
End If

If (z_low_surface <> "0") Then
Print #1, "<z_low_surface>" + z_low_surface + "</z_low_surface>"
End If

If (z_high_surface <> "0") Then
Print #1, "<z_high_surface>" + z_high_surface + "</z_high_surface>"
End If

If (all_faces_surface <> "0") Then
Print #1, "<all_surface>" + all_faces_surface + "</all_surface>"
End If

If (x_low_radiation <> "0") Then
Print #1, "<x_low_radiation>" + x_low_radiation + "</x_low_radiation>"
End If

If (x_high_radiation <> "0") Then
Print #1, "<x_high_radiation>" + x_high_radiation + "</x_high_radiation>"
End If

If (y_low_radiation <> "0") Then
Print #1, "<y_low_radiation>" + y_low_radiation + "</y_low_radiation>"
End If

If (y_high_radiation <> "0") Then
Print #1, "<y_high_radiation>" + y_high_radiation + "</y_high_radiation>"
End If

If (z_low_radiation <> "0") Then
Print #1, "<z_low_radiation>" + z_low_radiation + "</z_low_radiation>"
End If

If (z_high_radiation <> "0") Then
Print #1, "<z_high_radiation>" + z_high_radiation + "</z_high_radiation>"
End If

If (all_faces_radiation <> "0") Then
Print #1, "<all_radiation>" + all_faces_radiation + "</all_radiation>"
End If

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_directions_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_directions_grid_constraint + "</all_grid_constraint>"
End If

If (x_low_surface_exchange <> "0") Then
Print #1, "<x_low_surface_exchange>" + x_low_surface_exchange + "</x_low_surface_exchange>"
End If

If (x_high_surface_exchange <> "0") Then
Print #1, "<x_high_surface_exchange>" + x_high_surface_exchange + "</x_high_surface_exchange>"
End If

If (y_low_surface_exchange <> "0") Then
Print #1, "<y_low_surface_exchange>" + y_low_surface_exchange + "</y_low_surface_exchange>"
End If

If (y_high_surface_exchange <> "0") Then
Print #1, "<y_high_surface_exchange>" + y_high_surface_exchange + "</y_high_surface_exchange>"
End If

If (z_low_surface_exchange <> "0") Then
Print #1, "<z_low_surface_exchange>" + z_low_surface_exchange + "</z_low_surface_exchange>"
End If

If (z_high_surface_exchange <> "0") Then
Print #1, "<z_high_surface_exchange>" + z_high_surface_exchange + "</z_high_surface_exchange>"
End If

If (all_faces_surface_exchange <> "0") Then
Print #1, "<all_surface_exchange>" + all_faces_surface_exchange + "</all_surface_exchange>"
End If


If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</cuboid>"

End Sub
Sub build_block_with_holes_start(name, hole_direction_0_x_1_y_2_z, x_position, y_position, z_position, x_size, y_size, z_size, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, collapse_direction_0_nocollapse_1_x_2_y_3_z, collapse_face_0_lowface_1_midpoint_2_highface, material, thermal, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_directions_grid_constraint, x_low_surface, x_high_surface, y_low_surface, y_high_surface, z_low_surface, z_high_surface, all_faces_surface, x_low_radiation, x_high_radiation, y_low_radiation, y_high_radiation, z_low_radiation, z_high_radiation, all_faces_radiation, x_low_surface_exchange, x_high_surface_exchange, y_low_surface_exchange, y_high_surface_exchange, z_low_surface_exchange, z_high_surface_exchange, all_faces_surface_exchange, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<cuboid>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

If (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
End If



Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y><z>" + CStr(z_size) + "</z></size>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

If (material <> "0") Then
Print #1, "<material>" + material + "</material>"
End If

If (thermal <> "0") Then
Print #1, "<thermal>" + thermal + "</thermal>"
End If

If (x_low_surface <> "0") Then
Print #1, "<x_low_surface>" + x_low_surface + "</x_low_surface>"
End If

If (x_high_surface <> "0") Then
Print #1, "<x_high_surface>" + x_high_surface + "</x_high_surface>"
End If

If (y_low_surface <> "0") Then
Print #1, "<y_low_surface>" + y_low_surface + "</y_low_surface>"
End If

If (y_high_surface <> "0") Then
Print #1, "<y_high_surface>" + y_high_surface + "</y_high_surface>"
End If

If (z_low_surface <> "0") Then
Print #1, "<z_low_surface>" + z_low_surface + "</z_low_surface>"
End If

If (z_high_surface <> "0") Then
Print #1, "<z_high_surface>" + z_high_surface + "</z_high_surface>"
End If

If (all_faces_surface <> "0") Then
Print #1, "<all_surface>" + all_faces_surface + "</all_surface>"
End If

If (x_low_radiation <> "0") Then
Print #1, "<x_low_radiation>" + x_low_radiation + "</x_low_radiation>"
End If

If (x_high_radiation <> "0") Then
Print #1, "<x_high_radiation>" + x_high_radiation + "</x_high_radiation>"
End If

If (y_low_radiation <> "0") Then
Print #1, "<y_low_radiation>" + y_low_radiation + "</y_low_radiation>"
End If

If (y_high_radiation <> "0") Then
Print #1, "<y_high_radiation>" + y_high_radiation + "</y_high_radiation>"
End If

If (z_low_radiation <> "0") Then
Print #1, "<z_low_radiation>" + z_low_radiation + "</z_low_radiation>"
End If

If (z_high_radiation <> "0") Then
Print #1, "<z_high_radiation>" + z_high_radiation + "</z_high_radiation>"
End If

If (all_faces_radiation <> "0") Then
Print #1, "<all_radiation>" + all_faces_radiation + "</all_radiation>"
End If

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_directions_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_directions_grid_constraint + "</all_grid_constraint>"
End If

If (x_low_surface_exchange <> "0") Then
Print #1, "<x_low_surface_exchange>" + x_low_surface_exchange + "</x_low_surface_exchange>"
End If

If (x_high_surface_exchange <> "0") Then
Print #1, "<x_high_surface_exchange>" + x_high_surface_exchange + "</x_high_surface_exchange>"
End If

If (y_low_surface_exchange <> "0") Then
Print #1, "<y_low_surface_exchange>" + y_low_surface_exchange + "</y_low_surface_exchange>"
End If

If (y_high_surface_exchange <> "0") Then
Print #1, "<y_high_surface_exchange>" + y_high_surface_exchange + "</y_high_surface_exchange>"
End If

If (z_low_surface_exchange <> "0") Then
Print #1, "<z_low_surface_exchange>" + z_low_surface_exchange + "</z_low_surface_exchange>"
End If

If (z_high_surface_exchange <> "0") Then
Print #1, "<z_high_surface_exchange>" + z_high_surface_exchange + "</z_high_surface_exchange>"
End If

If (all_faces_surface_exchange <> "0") Then
Print #1, "<all_surface_exchange>" + all_faces_surface_exchange + "</all_surface_exchange>"
End If


If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "<holes>"

'Hole Direction
If (hole_direction_0_x_1_y_2_z = 0) Then
Print #1, "<direction>x_direction</direction>"
ElseIf (hole_direction_0_x_1_y_2_z = 1) Then
Print #1, "<direction>y_direction</direction>"
ElseIf (hole_direction_0_x_1_y_2_z = 2) Then
Print #1, "<direction>z_direction</direction>"
End If

End Sub
Sub build_block_with_holes_end()

Print #1, "</holes>"
Print #1, "</cuboid>"

End Sub
Sub build_hole(name, x_position, y_position, x_size, y_size, replace_with_0_none_1_material_2_resistance, modeling_level_0_thin_1_thick, replace_position_0_lowface_1_midpoint_2_highface, thickness, material_attribute, resistance_attribute, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<hole>"

Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y></size>"

If (replace_with_0_none_1_material_2_resistance = 0) Then
Print #1, "<replace_with><type>open</type></replace_with>"
ElseIf (replace_with_0_none_1_material_2_resistance = 1) Then
Print #1, "<replace_with>"
Print #1, "<type>material</type>"

If (material_attribute <> "0") Then
Print #1, "<material>" + material_attribute + "</material>"
End If


If (modeling_level_0_thin_1_thick = 0) Then
Print #1, "<modeling_level>thin</modeling_level>"
ElseIf (modeling_level_0_thin_1_thick = 1) Then
Print #1, "<modeling_level>thick</modeling_level>"
End If


If (replace_position_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<replace_position>low_face</replace_position>"
ElseIf (replace_position_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<replace_position>mid_face</replace_position>"
ElseIf (replace_position_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<replace_position>high_face</replace_position>"
End If

Print #1, "<thickness>" + CStr(thickness) + "</thickness>"

Print #1, "</replace_with>"
ElseIf (replace_with_0_none_1_material_2_resistance = 2) Then
Print #1, "<replace_with>"
Print #1, "<type>resistance</type>"

If (resistance_attribute <> "0") Then
Print #1, "<resistance>" + resistance_attribute + "</resistance>"
End If

If (modeling_level_0_thin_1_thick = 0) Then
Print #1, "<modeling_level>thin</modeling_level>"
ElseIf (modeling_level_0_thin_1_thick = 1) Then
Print #1, "<modeling_level>thick</modeling_level>"
End If

If (replace_position_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<replace_position>low_face</replace_position>"
ElseIf (replace_position_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<replace_position>mid_face</replace_position>"
ElseIf (replace_position_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<replace_position>high_face</replace_position>"
End If

Print #1, "<thickness>" + CStr(thickness) + "</thickness>"

Print #1, "</replace_with>"
End If

Print #1, "</hole>"

End Sub
Sub build_rack_start(name, x_position, y_position, z_position, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, power, rack_type_0_flowrate_per_power_1_temperature_change_2_flow_rate_3_fan_curve, flow_value, string_containing_fan_curve, air_flow_adjustment_0_false_1_true, air_flow_adjustment_critical_temperature, air_flow_adjustment_factor, cooler_group, hot_aisle_group, cold_aisle_group, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_grid_constraint_attribute, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)
Dim points() As String

Print #1, "<rack>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

Print #1, "<power_dissipation>" + CStr(power) + "</power_dissipation>"

If (rack_type_0_flowrate_per_power_1_temperature_change_2_flow_rate_3_fan_curve = 0) Then
Print #1, "<flow_type>flow_rate_power</flow_type>"
Print #1, "<flow_rate_power>" + CStr(flow_value) + "</flow_rate_power>"
ElseIf (rack_type_0_flowrate_per_power_1_temperature_change_2_flow_rate_3_fan_curve = 1) Then
Print #1, "<flow_type>temperature_change</flow_type>"
Print #1, "<temperature_change>" + CStr(flow_value) + "</temperature_change>"
ElseIf (rack_type_0_flowrate_per_power_1_temperature_change_2_flow_rate_3_fan_curve = 2) Then
Print #1, "<flow_type>volume_flow_rate</flow_type>"
Print #1, "<volume_flow_rate>" + CStr(flow_value) + "</volume_flow_rate>"
ElseIf (rack_type_0_flowrate_per_power_1_temperature_change_2_flow_rate_3_fan_curve = 3) Then
Print #1, "<flow_type>curve</flow_type>"
Print #1, "<curve>"
'Print #1, "<fan_curve_points>"

points() = Split(string_containing_fan_curve, ",")

For k = 0 To UBound(points) Step 2
Print #1, "<fan_curve_point>"
Print #1, "<volume_flow>" + points(k) + "</volume_flow><pressure>" + points(k + 1) + "</pressure>"
Print #1, "</fan_curve_point>"

Next k

'Print #1, "</fan_curve_points>"
Print #1, "</curve>"
End If



If (air_flow_adjustment_0_false_1_true = 1) Then
Print #1, "<airflow_adjustment>"
Print #1, "<active>true</active>"
Print #1, "<critical_temperature>" + CStr(air_flow_adjustment_critical_temperature) + "</critical_temperature>"
Print #1, "<factor>" + CStr(air_flow_adjustment_factor) + "</factor>"
Print #1, "</airflow_adjustment>"
End If

If (cooler_group <> "0") Then
Print #1, "<cooler_group>" + cooler_group + "</cooler_group>"
End If
If (hot_aisle_group <> "0") Then
Print #1, "<hot_aisle_group>" + hot_aisle_group + "</hot_aisle_group>"
End If
If (cold_aisle_group <> "0") Then
Print #1, "<cold_aisle_group>" + cold_aisle_group + "</cold_aisle_group>"
End If


If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If
If (all_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint_attribute + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

End Sub
Sub build_perforated_plate(name, x_position, y_position, z_position, x_size, y_size, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, hole_type_0_hexagonal_1_round_2_square, hole_dimension, coverage_type_0_pitch_1_defined, pitch_x, pitch_y, defined_coverage, resistance_type_0_automatic_1_standard_2_advanced, loss_coefficient_based_on_0_approach_velocity_1_device_velocity_2_accelerated, standard_loss_coefficient, advanced_length_scale, advanced_a_coefficient, advanced_b_coefficient, advanced_index, straighten_flow_0_inactive_1_high_side_2_low_side, cold_aisle_group, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_grid_constraint_attribute, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<perforated_plate>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"

Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y></size>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"


If (hole_type_0_hexagonal_1_round_2_square = 0) Then
Print #1, "<hole_type>hexagonal</hole_type>"
Print #1, "<side_length>" + CStr(hole_dimension) + "</side_length>"
ElseIf (hole_type_0_hexagonal_1_round_2_square = 1) Then
Print #1, "<hole_type>round</hole_type>"
Print #1, "<diameter>" + CStr(hole_dimension) + "</diameter>"
ElseIf (hole_type_0_hexagonal_1_round_2_square = 2) Then
Print #1, "<hole_type>square</hole_type>"
Print #1, "<side_length>" + CStr(hole_dimension) + "</side_length>"
End If

If (coverage_type_0_pitch_1_defined = 0) Then
Print #1, "<coverage>"
Print #1, "<pitch><x>" + CStr(pitch_x) + "</x><y>" + CStr(pitch_y) + "</y></pitch>"
Print #1, "</coverage>"
ElseIf (coverage_type_0_pitch_1_defined = 1) Then
Print #1, "<coverage>"
Print #1, "<defined_coverage>" + CStr(defined_coverage) + "</defined_coverage>"
Print #1, "</coverage>"
End If

If (straighten_flow_0_inactive_1_high_side_2_low_side = 0) Then
ElseIf (straighten_flow_0_inactive_1_high_side_2_low_side = 1) Then
Print #1, "<straighten_flow>high_side</straighten_flow>"
ElseIf (straighten_flow_0_inactive_1_high_side_2_low_side = 2) Then
Print #1, "<straighten_flow>low_side</straighten_flow>"
End If

If (resistance_type_0_automatic_1_standard_2_advanced = 0) Then
Print #1, "<resistance_model>automatic</resistance_model>"
ElseIf (resistance_type_0_automatic_1_standard_2_advanced = 1) Then
Print #1, "<resistance_model>standard</resistance_model>"

If (loss_coefficient_based_on_0_approach_velocity_1_device_velocity_2_accelerated = 0) Then
Print #1, "<loss_coefficient_based_on>approach_velocity</loss_coefficient_based_on>"
ElseIf (loss_coefficient_based_on_0_approach_velocity_1_device_velocity_2_accelerated = 1) Then
Print #1, "<loss_coefficient_based_on>device_velocity</loss_coefficient_based_on>"
ElseIf (loss_coefficient_based_on_0_approach_velocity_1_device_velocity_2_accelerated = 2) Then
Print #1, "<loss_coefficient_based_on>accelerated</loss_coefficient_based_on>"
End If

Print #1, "<loss_coefficient>" + CStr(standard_loss_coefficient) + "</loss_coefficient>"

ElseIf (resistance_type_0_automatic_1_standard_2_advanced = 2) Then
Print #1, "<resistance_model>advanced</resistance_model>"

If (loss_coefficient_based_on_0_approach_velocity_1_device_velocity_2_accelerated = 0) Then
Print #1, "<loss_coefficient_based_on>approach_velocity</loss_coefficient_based_on>"
ElseIf (loss_coefficient_based_on_0_approach_velocity_1_device_velocity_2_accelerated = 1) Then
Print #1, "<loss_coefficient_based_on>device_velocity</loss_coefficient_based_on>"
ElseIf (loss_coefficient_based_on_0_approach_velocity_1_device_velocity_2_accelerated = 2) Then
Print #1, "<loss_coefficient_based_on>accelerated</loss_coefficient_based_on>"
End If

Print #1, "<advanced_loss_coefficient>"
Print #1, "<length_scale>+" + CStr(advanced_length_scale) + "</length_scale>"
Print #1, "<a_coefficient>+" + CStr(advanced_a_coefficient) + "</a_coefficient>"
Print #1, "<b_coefficient>+" + CStr(advanced_b_coefficient) + "</b_coefficient>"
Print #1, "<index>+" + CStr(advanced_index) + "</index>"
Print #1, "</advanced_loss_coefficient>"
End If


If (cold_aisle_group <> "0") Then
Print #1, "<cold_aisle_group>" + cold_aisle_group + "</cold_aisle_group>"
End If


If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If
If (all_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint_attribute + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

Print #1, "</perforated_plate>"

End Sub
Sub build_square_diffuser(name, x_position, y_position, z_position, x_size, y_size, z_size, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, volume_flow_rate, jet_angle, x_high_jet_0_ON_1_OFF, x_low_jet_0_ON_1_OFF, y_high_jet_0_ON_1_OFF, y_low_jet_0_ON_1_OFF, ambient_attribute, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_grid_constraint_attribute, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<square_diffuser>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y><z>" + CStr(z_size) + "</z></size>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

Print #1, "<active_jets>"

Select Case x_high_jet_0_ON_1_OFF
    Case 0
        Print #1, "<x_high_jet>true</x_high_jet>"
    Case 1
        Print #1, "<x_high_jet>false</x_high_jet>"
End Select

Select Case x_low_jet_0_ON_1_OFF
    Case 0
        Print #1, "<x_low_jet>true</x_low_jet>"
    Case 1
        Print #1, "<x_low_jet>false</x_low_jet>"
End Select

Select Case y_high_jet_0_ON_1_OFF
    Case 0
        Print #1, "<y_high_jet>true</y_high_jet>"
    Case 1
        Print #1, "<y_high_jet>false</y_high_jet>"
End Select

Select Case y_low_jet_0_ON_1_OFF
    Case 0
        Print #1, "<y_low_jet>true</y_low_jet>"
    Case 1
        Print #1, "<y_low_jet>false</y_low_jet>"
End Select

Print #1, "</active_jets>"

Print #1, "<volume_flow_rate>" + CStr(volume_flow_rate) + "</volume_flow_rate>"
Print #1, "<jet_angle>" + CStr(jet_angle) + "</jet_angle>"

If (ambient_attribute <> "0") Then
Print #1, "<ambient>" + ambient_attribute + "</ambient>"
End If

If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If
If (all_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint_attribute + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

Print #1, "</square_diffuser>"

End Sub
Sub build_fixed_flow(name, x_position, y_position, z_position, x_size, y_size, free_area_ratio, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, airflow_type_0_normal_velocity_1_volume_flow_rate, flow_value, flow_direction_0_inflow_1_outflow, angled_flow_0_false_1_true, angled_x_component, angled_y_component, angled_z_component, transparent_to_radiation_0_false_1_true, hot_aisle_group, cold_aisle_group, ambient_attribute, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_grid_constraint_attribute, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)


Print #1, "<fixed_flow>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y></size>"
Print #1, "<free_area_ratio>" + CStr(free_area_ratio) + "</free_area_ratio>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

'Airflow type options
Print #1, "<flow>"
If (airflow_type_0_normal_velocity_1_volume_flow_rate = 0) Then
Print #1, "<flow_type>normal_velocity</flow_type>"
Print #1, "<normal_velocity>" + CStr(flow_value) + "</normal_velocity>"
ElseIf (airflow_type_0_normal_velocity_1_volume_flow_rate = 1) Then
Print #1, "<flow_type>volume_flow_rate</flow_type>"
Print #1, "<volume_flow_rate>" + CStr(flow_value) + "</volume_flow_rate>"

End If
Print #1, "</flow>"

' Inflow or Outflow options

If (flow_direction_0_inflow_1_outflow = 0) Then
Print #1, "<flow_direction>inflow</flow_direction>"
ElseIf (flow_direction_0_inflow_1_outflow = 1) Then
Print #1, "<flow_direction>outflow</flow_direction>"
End If

' Angled Flow Options

If (angled_flow_0_false_1_true = 0) Then
Print #1, "<flow_angle>normal</flow_angle>"
ElseIf (angled_flow_0_false_1_true = 1) Then
Print #1, "<flow_angle>angled</flow_angle>"
Print #1, "<x>" + CStr(angled_x_component) + "</x><y>" + CStr(angled_y_component) + "</y><z>" + CStr(angled_z_component) + "</z>"
End If

' Transparent to Radiation Option

If (transparent_to_radiation_0_false_1_true = 0) Then
Print #1, "<transparent_to_radiation>false</transparent_to_radiation>"
ElseIf (transparent_to_radiation_0_false_1_true = 1) Then
Print #1, "<transparent_to_radiation>true</transparent_to_radiation>"
End If

If (hot_aisle_group <> "0") Then
Print #1, "<hot_aisle_group>" + hot_aisle_group + "</hot_aisle_group>"
End If
If (cold_aisle_group <> "0") Then
Print #1, "<cold_aisle_group>" + cold_aisle_group + "</cold_aisle_group>"
End If

If (ambient_attribute <> "0") Then
Print #1, "<inflow_ambient>" + ambient_attribute + "</inflow_ambient>"
End If

If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If
If (all_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint_attribute + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

Print #1, "</fixed_flow>"

End Sub
Sub build_recirc_deltaT_start(name, x_position, y_position, z_position, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, airflow_type_0_fixed_1_fan_curve_2_fixed_velocity, flow_value, string_containing_fan_curve, inflow_of_primary_fluid_0_false_1_true, inflow_flow_rate, inflow_ambient, temperature_change, use_thermostat_0_false_1_true, control_temperature, deadband_temperature, thermostat_x_pos, thermostat_y_pos, thermostat_z_pos, application_side_0_control_side_1_secondary_side, filtration_active_0_false_1_true, concentration_1_filtration, concentration_2_filtration, concentration_3_filtration, concentration_4_filtration, concentration_5_filtration, cooler_group, hot_aisle_group, cold_aisle_group, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_grid_constraint_attribute, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)
Dim points() As String

Print #1, "<recirc_device>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

'Airflow type options

Select Case airflow_type_0_fixed_1_fan_curve_2_fixed_velocity
    Case 0
        Print #1, "<flow_type>volume_flow_rate</flow_type>"
        Print #1, "<flow_rate>" + CStr(flow_value) + "</flow_rate>"
    Case 1
        Print #1, "<flow_type>non_linear_fan_curve</flow_type>"
        Print #1, "<curve>"
        points() = Split(string_containing_fan_curve, ",")

        For k = 0 To UBound(points) Step 2
        Print #1, "<fan_curve_point>"
        Print #1, "<volume_flow>" + points(k) + "</volume_flow><pressure>" + points(k + 1) + "</pressure>"
        Print #1, "</fan_curve_point>"

        Next k

        Print #1, "</curve>"
    Case 2
        Print #1, "<flow_type>normal_velocity_at_supply</flow_type>"
        Print #1, "<velocity>" + CStr(flow_value) + "</velocity>"
End Select

If (inflow_of_primary_fluid_0_false_1_true = 1) Then
    Print #1, "<inflow_of_primary_fluid>true</inflow_of_primary_fluid>"
    Print #1, "<inflow_flow_rate>" + CStr(inflow_flow_rate) + "</inflow_flow_rate>"
    Print #1, "<inflow_ambient>" + CStr(inflow_ambient) + "</inflow_ambient>"
End If

Print #1, "<thermal_properties>temperature_change</thermal_properties>"
Print #1, "<temperature_change>" + CStr(temperature_change) + "</temperature_change>"


If (use_thermostat_0_false_1_true = 1) Then
    Print #1, "<use_thermostat>true</use_thermostat>"
    Print #1, "<thermostat>"
    Print #1, "<control_temperature>" + CStr(control_temperature) + "</control_temperature>"
    Print #1, "<deadband_temperature>" + CStr(deadband_temperature) + "</deadband_temperature>"
    Print #1, "<position><x>" + CStr(thermostat_x_pos) + "</x><y>" + CStr(thermostat_y_pos) + "</y><z>" + CStr(thermostat_z_pos) + "</z></position>"
    
    Select Case application_side_0_control_side_1_secondary_side
        Case 0
            Print #1, "<application_side>control_side</application_side>"
        Case 1
            Print #1, "<application_side>secondary_side</application_side>"
    End Select
    
    Print #1, "</thermostat>"
End If

If (filtration_active_0_false_1_true = 1) Then
    Print #1, "<filtration_active>true</filtration_active>"
    Print #1, "<concentration_1_filtration>" + CStr(concentration_1_filtration) + "</concentration_1_filtration>"
    Print #1, "<concentration_2_filtration>" + CStr(concentration_2_filtration) + "</concentration_2_filtration>"
    Print #1, "<concentration_3_filtration>" + CStr(concentration_3_filtration) + "</concentration_3_filtration>"
    Print #1, "<concentration_4_filtration>" + CStr(concentration_4_filtration) + "</concentration_4_filtration>"
    Print #1, "<concentration_5_filtration>" + CStr(concentration_5_filtration) + "</concentration_5_filtration>"
End If

If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If
If (all_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint_attribute + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

End Sub
Sub build_recirc_heat_input_start(name, x_position, y_position, z_position, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, airflow_type_0_fixed_1_fan_curve_2_fixed_velocity, flow_value, string_containing_fan_curve, inflow_of_primary_fluid_0_false_1_true, inflow_flow_rate, inflow_ambient, heat_input, use_thermostat_0_false_1_true, control_temperature, deadband_temperature, thermostat_x_pos, thermostat_y_pos, thermostat_z_pos, application_side_0_control_side_1_secondary_side, filtration_active_0_false_1_true, concentration_1_filtration, concentration_2_filtration, concentration_3_filtration, concentration_4_filtration, concentration_5_filtration, cooler_group, hot_aisle_group, cold_aisle_group, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_grid_constraint_attribute, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)
Dim points() As String

Print #1, "<recirc_device>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

'Airflow type options

Select Case airflow_type_0_fixed_1_fan_curve_2_fixed_velocity
    Case 0
        Print #1, "<flow_type>volume_flow_rate</flow_type>"
        Print #1, "<flow_rate>" + CStr(flow_value) + "</flow_rate>"
    Case 1
        Print #1, "<flow_type>non_linear_fan_curve</flow_type>"
        Print #1, "<curve>"
        points() = Split(string_containing_fan_curve, ",")

        For k = 0 To UBound(points) Step 2
        Print #1, "<fan_curve_point>"
        Print #1, "<volume_flow>" + points(k) + "</volume_flow><pressure>" + points(k + 1) + "</pressure>"
        Print #1, "</fan_curve_point>"

        Next k

        Print #1, "</curve>"
    Case 2
        Print #1, "<flow_type>normal_velocity_at_supply</flow_type>"
        Print #1, "<velocity>" + CStr(flow_value) + "</velocity>"
End Select

If (inflow_of_primary_fluid_0_false_1_true = 1) Then
    Print #1, "<inflow_of_primary_fluid>true</inflow_of_primary_fluid>"
    Print #1, "<inflow_flow_rate>" + CStr(inflow_flow_rate) + "</inflow_flow_rate>"
    Print #1, "<inflow_ambient>" + CStr(inflow_ambient) + "</inflow_ambient>"
End If

Print #1, "<thermal_properties>heat_input_extraction_rate</thermal_properties>"
Print #1, "<heat_input_extraction_rate>" + CStr(heat_input) + "</heat_input_extraction_rate>"

If (use_thermostat_0_false_1_true = 1) Then
    Print #1, "<use_thermostat>true</use_thermostat>"
    Print #1, "<thermostat>"
    Print #1, "<control_temperature>" + CStr(control_temperature) + "</control_temperature>"
    Print #1, "<deadband_temperature>" + CStr(deadband_temperature) + "</deadband_temperature>"
    Print #1, "<position><x>" + CStr(thermostat_x_pos) + "</x><y>" + CStr(thermostat_y_pos) + "</y><z>" + CStr(thermostat_z_pos) + "</z></position>"
    
    Select Case application_side_0_control_side_1_secondary_side
        Case 0
            Print #1, "<application_side>control_side</application_side>"
        Case 1
            Print #1, "<application_side>secondary_side</application_side>"
    End Select
    
    Print #1, "</thermostat>"
End If

If (filtration_active_0_false_1_true = 1) Then
    Print #1, "<filtration_active>true</filtration_active>"
    Print #1, "<concentration_1_filtration>" + CStr(concentration_1_filtration) + "</concentration_1_filtration>"
    Print #1, "<concentration_2_filtration>" + CStr(concentration_2_filtration) + "</concentration_2_filtration>"
    Print #1, "<concentration_3_filtration>" + CStr(concentration_3_filtration) + "</concentration_3_filtration>"
    Print #1, "<concentration_4_filtration>" + CStr(concentration_4_filtration) + "</concentration_4_filtration>"
    Print #1, "<concentration_5_filtration>" + CStr(concentration_5_filtration) + "</concentration_5_filtration>"
End If

If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If
If (all_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint_attribute + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

End Sub
Sub build_recirc_HX_start(name, x_position, y_position, z_position, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, airflow_type_0_fixed_1_fan_curve_2_fixed_velocity, flow_value, string_containing_fan_curve, inflow_of_primary_fluid_0_false_1_true, inflow_flow_rate, inflow_ambient, model_0_simple_1_LMTD, HX_temperature, HX_HTC, HX_fluid, HX_vol_flow_rate, HX_type_0_parallel_1_counter, use_thermostat_0_false_1_true, control_temperature, deadband_temperature, thermostat_x_pos, thermostat_y_pos, thermostat_z_pos, application_side_0_control_side_1_secondary_side, filtration_active_0_false_1_true, concentration_1_filtration, concentration_2_filtration, concentration_3_filtration, concentration_4_filtration, concentration_5_filtration, cooler_group, hot_aisle_group, cold_aisle_group, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_grid_constraint, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)
Dim points() As String

Print #1, "<recirc_device>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

'Airflow type options

Select Case airflow_type_0_fixed_1_fan_curve_2_fixed_velocity
    Case 0
        Print #1, "<flow_type>volume_flow_rate</flow_type>"
        Print #1, "<flow_rate>" + CStr(flow_value) + "</flow_rate>"
    Case 1
        Print #1, "<flow_type>non_linear_fan_curve</flow_type>"
        Print #1, "<curve>"
        points() = Split(string_containing_fan_curve, ",")

        For k = 0 To UBound(points) Step 2
        Print #1, "<fan_curve_point>"
        Print #1, "<volume_flow>" + points(k) + "</volume_flow><pressure>" + points(k + 1) + "</pressure>"
        Print #1, "</fan_curve_point>"

        Next k

        Print #1, "</curve>"
    Case 2
        Print #1, "<flow_type>normal_velocity_at_supply</flow_type>"
        Print #1, "<velocity>" + CStr(flow_value) + "</velocity>"
End Select

If (inflow_of_primary_fluid_0_false_1_true = 1) Then
    Print #1, "<inflow_of_primary_fluid>true</inflow_of_primary_fluid>"
    Print #1, "<inflow_flow_rate>" + CStr(inflow_flow_rate) + "</inflow_flow_rate>"
    Print #1, "<inflow_ambient>" + CStr(inflow_ambient) + "</inflow_ambient>"
End If

Print #1, "<thermal_properties>heat_exchanger</thermal_properties>"
Print #1, "<heat_exchanger>"
 Select Case model_0_simple_1_LMTD
    Case 0
        Print #1, "<model>simple</model>"
    Case 1
        Print #1, "<model>lmtd</model>"
 End Select
 Print #1, "<temperature>" + CStr(HX_temperature) + "</temperature>"
 Print #1, "<heat_transfer_coeff>" + CStr(HX_HTC) + "</heat_transfer_coeff>"
 Print #1, "<fluid>" + CStr(HX_fluid) + "</fluid>"
 Print #1, "<volume_flow_rate>" + CStr(HX_vol_flow_rate) + "</volume_flow_rate>"
 Select Case HX_type_0_parallel_1_counter
    Case 0
        Print #1, "<configuration_type>parallel_flow</configuration_type>"
    Case 1
        Print #1, "<configuration_type>counter_flow</configuration_type>"
 End Select
Print #1, "</heat_exchanger>"

If (use_thermostat_0_false_1_true = 1) Then
    Print #1, "<use_thermostat>true</use_thermostat>"
    Print #1, "<thermostat>"
    Print #1, "<control_temperature>" + CStr(control_temperature) + "</control_temperature>"
    Print #1, "<deadband_temperature>" + CStr(deadband_temperature) + "</deadband_temperature>"
    Print #1, "<position><x>" + CStr(thermostat_x_pos) + "</x><y>" + CStr(thermostat_y_pos) + "</y><z>" + CStr(thermostat_z_pos) + "</z></position>"
    
    Select Case application_side_0_control_side_1_secondary_side
        Case 0
            Print #1, "<application_side>control_side</application_side>"
        Case 1
            Print #1, "<application_side>secondary_side</application_side>"
    End Select
    
    Print #1, "</thermostat>"
End If

If (filtration_active_0_false_1_true = 1) Then
    Print #1, "<filtration_active>true</filtration_active>"
    Print #1, "<concentration_1_filtration>" + CStr(concentration_1_filtration) + "</concentration_1_filtration>"
    Print #1, "<concentration_2_filtration>" + CStr(concentration_2_filtration) + "</concentration_2_filtration>"
    Print #1, "<concentration_3_filtration>" + CStr(concentration_3_filtration) + "</concentration_3_filtration>"
    Print #1, "<concentration_4_filtration>" + CStr(concentration_4_filtration) + "</concentration_4_filtration>"
    Print #1, "<concentration_5_filtration>" + CStr(concentration_5_filtration) + "</concentration_5_filtration>"
End If

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If


End Sub
Sub build_recirc_crac_start(name, x_position, y_position, z_position, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, airflow_type_0_fixed_1_fan_curve_2_fixed_velocity, flow_value, string_containing_fan_curve, inflow_of_primary_fluid_0_false_1_true, inflow_flow_rate, inflow_ambient, crac_max_power, crac_desired_temperature, use_thermostat_0_false_1_true, control_temperature, deadband_temperature, thermostat_x_pos, thermostat_y_pos, thermostat_z_pos, application_side_0_control_side_1_secondary_side, filtration_active_0_false_1_true, concentration_1_filtration, concentration_2_filtration, concentration_3_filtration, concentration_4_filtration, concentration_5_filtration, cooler_group, hot_aisle_group, cold_aisle_group, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_grid_constraint_attribute, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)
Dim points() As String

Print #1, "<recirc_device>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

'Airflow type options

Select Case airflow_type_0_fixed_1_fan_curve_2_fixed_velocity
    Case 0
        Print #1, "<flow_type>volume_flow_rate</flow_type>"
        Print #1, "<flow_rate>" + CStr(flow_value) + "</flow_rate>"
    Case 1
        Print #1, "<flow_type>non_linear_fan_curve</flow_type>"
        Print #1, "<curve>"
        points() = Split(string_containing_fan_curve, ",")

        For k = 0 To UBound(points) Step 2
        Print #1, "<fan_curve_point>"
        Print #1, "<volume_flow>" + points(k) + "</volume_flow><pressure>" + points(k + 1) + "</pressure>"
        Print #1, "</fan_curve_point>"

        Next k

        Print #1, "</curve>"
    Case 2
        Print #1, "<flow_type>normal_velocity_at_supply</flow_type>"
        Print #1, "<velocity>" + CStr(flow_value) + "</velocity>"
End Select

If (inflow_of_primary_fluid_0_false_1_true = 1) Then
    Print #1, "<inflow_of_primary_fluid>true</inflow_of_primary_fluid>"
    Print #1, "<inflow_flow_rate>" + CStr(inflow_flow_rate) + "</inflow_flow_rate>"
    Print #1, "<inflow_ambient>" + CStr(inflow_ambient) + "</inflow_ambient>"
End If

Print #1, "<thermal_properties>crac</thermal_properties>"
Print #1, "<crac_max_power>" + CStr(crac_max_power) + "</crac_max_power>"
Print #1, "<crac_desired_temperature>" + CStr(crac_desired_temperature) + "</crac_desired_temperature>"

If (use_thermostat_0_false_1_true = 1) Then
    Print #1, "<use_thermostat>true</use_thermostat>"
    Print #1, "<thermostat>"
    Print #1, "<control_temperature>" + CStr(control_temperature) + "</control_temperature>"
    Print #1, "<deadband_temperature>" + CStr(deadband_temperature) + "</deadband_temperature>"
    Print #1, "<position><x>" + CStr(thermostat_x_pos) + "</x><y>" + CStr(thermostat_y_pos) + "</y><z>" + CStr(thermostat_z_pos) + "</z></position>"
    
    Select Case application_side_0_control_side_1_secondary_side
        Case 0
            Print #1, "<application_side>control_side</application_side>"
        Case 1
            Print #1, "<application_side>secondary_side</application_side>"
    End Select
    
    Print #1, "</thermostat>"
End If

If (filtration_active_0_false_1_true = 1) Then
    Print #1, "<filtration_active>true</filtration_active>"
    Print #1, "<concentration_1_filtration>" + CStr(concentration_1_filtration) + "</concentration_1_filtration>"
    Print #1, "<concentration_2_filtration>" + CStr(concentration_2_filtration) + "</concentration_2_filtration>"
    Print #1, "<concentration_3_filtration>" + CStr(concentration_3_filtration) + "</concentration_3_filtration>"
    Print #1, "<concentration_4_filtration>" + CStr(concentration_4_filtration) + "</concentration_4_filtration>"
    Print #1, "<concentration_5_filtration>" + CStr(concentration_5_filtration) + "</concentration_5_filtration>"
End If

If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If
If (all_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint_attribute + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

End Sub
Sub build_recirc_device_end()

Print #1, "</recirc_device>"

End Sub
Sub build_cooler_start(name, x_pos, y_pos, z_pos, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, airflow_type_0_fixed_1_fan_curve_2_temperature_difference_3_remote_temperature_control, flow_value, string_containing_fan_curve, temperature_difference_set_point, temperature_difference_max_flow_rate, temperature_difference_min_flow_rate, remote_temperature_control_target_temperature, remote_temperature_control_max_flow_rate, remote_temperature_control_min_flow_rate, remote_temperature_control_0_average_1_two_thirds_height, temperature_set_point, temperature_set_point_0_supply_1_return, capacity_limit_type_0_none_1_fixed_2_curve, fixed_capacity_value, string_containing_capacity_curve, variable_capacity_airflow_value, variable_capacity_airflow_exponent, cooler_group, hot_aisle_group, cold_aisle_group, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_grid_constraint, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)
Dim points() As String


Print #1, "<cooler>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_pos) + "</x><y>" + CStr(y_pos) + "</y><z>" + CStr(z_pos) + "</z></position>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

'Airflow type options

If (airflow_type_0_fixed_1_fan_curve_2_temperature_difference_3_remote_temperature_control = 0) Then
Print #1, "<airflow_type>fixed</airflow_type>"
Print #1, "<flow_rate>" + CStr(flow_value) + "</flow_rate>"
ElseIf (airflow_type_0_fixed_1_fan_curve_2_temperature_difference_3_remote_temperature_control = 1) Then
Print #1, "<airflow_type>curve</airflow_type>"

Print #1, "<curve>"
'Print #1, "<fan_curve_points>"

points() = Split(string_containing_fan_curve, ",")

For k = 0 To UBound(points) Step 2
Print #1, "<fan_curve_point>"
Print #1, "<volume_flow>" + points(k) + "</volume_flow><pressure>" + points(k + 1) + "</pressure>"
Print #1, "</fan_curve_point>"

Next k

'Print #1, "</fan_curve_points>"
Print #1, "</curve>"

ElseIf (airflow_type_0_fixed_1_fan_curve_2_temperature_difference_3_remote_temperature_control = 2) Then
Print #1, "<airflow_type>temperature_difference</airflow_type>"
Print #1, "<temperature_difference>"
Print #1, "<temperature>" + CStr(temperature_difference_set_point) + "</temperature>"
Print #1, "<max_flow_rate>" + CStr(temperature_difference_max_flow_rate) + "</max_flow_rate>"
Print #1, "<min_flow_rate>" + CStr(temperature_difference_min_flow_rate) + "</min_flow_rate>"
Print #1, "</temperature_difference>"
ElseIf (airflow_type_0_fixed_1_fan_curve_2_temperature_difference_3_remote_temperature_control = 3) Then

Print #1, "<airflow_type>remote_temperature_control</airflow_type>"

Print #1, "<remote_temperature_control>"

If (remote_temperature_control_0_average_1_two_thirds_height = 0) Then
Print #1, "<inlet_temperature>average</inlet_temperature>"
Else
Print #1, "<inlet_temperature>two_thirds_height</inlet_temperature>"
End If

Print #1, "<target_temperature>" + CStr(remote_temperature_control_target_temperature) + "</target_temperature>"
Print #1, "<max_flow_rate>" + CStr(remote_temperature_control_max_flow_rate) + "</max_flow_rate>"
Print #1, "<min_flow_rate>" + CStr(remote_temperature_control_min_flow_rate) + "</min_flow_rate>"

Print #1, "</remote_temperature_control>"

End If


' Temperature Set Point options

Print #1, "<temperature_set_point>" + CStr(temperature_set_point) + "</temperature_set_point>"

If (temperature_set_point_0_supply_1_return = 0) Then
Print #1, "<temperature_set_point_location>supply</temperature_set_point_location>"
ElseIf (temperature_set_point_0_supply_1_return = 1) Then
Print #1, "<temperature_set_point_location>return</temperature_set_point_location>"
End If

' Capacity Limit Options

If (capacity_limit_type_0_none_1_fixed_2_curve = 0) Then
Print #1, "<capacity_limit>none</capacity_limit>"

ElseIf (capacity_limit_type_0_none_1_fixed_2_curve = 1) Then
Print #1, "<capacity_limit>fixed</capacity_limit>"
Print #1, "<fixed_capacity>" + CStr(fixed_capacity_value) + "</fixed_capacity>"

ElseIf (capacity_limit_type_0_none_1_fixed_2_curve = 2) Then

Print #1, "<capacity_limit>variable</capacity_limit>"
Print #1, "<variable_capacity>"
Print #1, "<airflow>" + CStr(variable_capacity_airflow_value) + "</airflow>"
Print #1, "<airflow_reference_exponent>" + CStr(variable_capacity_airflow_exponent) + "</airflow_reference_exponent>"
Print #1, "<capacity_curve_points>"

points() = Split(string_containing_capacity_curve, ",")

For k = 0 To UBound(points) Step 2
Print #1, "<capacity_curve_point>"
Print #1, "<temperature>" + points(k) + "</temperature><power>" + points(k + 1) + "</power>"
Print #1, "</capacity_curve_point>"

Next k

Print #1, "</capacity_curve_points>"
Print #1, "</variable_capacity>"
End If



If (cooler_group <> "0") Then
Print #1, "<cooler_group>" + cooler_group + "</cooler_group>"
End If
If (hot_aisle_group <> "0") Then
Print #1, "<hot_aisle_group>" + hot_aisle_group + "</hot_aisle_group>"
End If
If (cold_aisle_group <> "0") Then
Print #1, "<cold_aisle_group>" + cold_aisle_group + "</cold_aisle_group>"
End If


If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

End Sub
Sub build_cooler_end()

Print #1, "</cooler>"

End Sub
Sub build_rack_end()

Print #1, "</rack>"

End Sub
Sub build_supply_list_start()

Print #1, "<supplies>"

End Sub
Sub build_supply_list_end()

Print #1, "</supplies>"

End Sub
Sub build_extract_list_start()

Print #1, "<extracts>"

End Sub
Sub build_extract_list_end()

Print #1, "</extracts>"

End Sub
Sub build_supply(name, x_position, y_position, z_position, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, rectangular_x_size, rectangular_y_size, free_area_ratio, direction_type_0_normal_1_angled_2_sheared, angled_x, angled_y, angled_z, shear_direction_0_x_1_y, max_velocity_location_0_high_1_low, shear_model_0_constant_1_flow_dependent, ke_turb, diss_turb, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_grid_constraint, notes, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<supply>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

Print #1, "<size>"
Print #1, "<x>" + CStr(rectangular_x_size) + "</x>"
Print #1, "<y>" + CStr(rectangular_y_size) + "</y>"
Print #1, "</size>"

Print #1, "<free_area_ratio>" + CStr(free_area_ratio) + "</free_area_ratio>"

Select Case direction_type_0_normal_1_angled_2_sheared
Case 0
    Print #1, "<direction_type>normal</direction_type>"
Case 1
    Print #1, "<direction_type>angled</direction_type>"
    Print #1, "<angled_flow_direction><x>" + CStr(angled_x) + "</x><y>" + CStr(angled_y) + "</y><z>" + CStr(angled_z) + "</z></angled_flow_direction>"
Case 2
    Print #1, "<direction_type>sheared</direction_type>"
        Select Case shear_direction_0_x_1_y
        Case 0
            Print #1, "<shear_direction>x</shear_direction>"
        Case 1
            Print #1, "<shear_direction>y</shear_direction>"
        End Select
        
        Select Case max_velocity_location_0_high_1_low
        Case 0
            Print #1, "<max_velocity_location>high</max_velocity_location>"
        Case 1
            Print #1, "<max_velocity_location>low</max_velocity_location>"
        End Select
        
        Select Case shear_model_0_constant_1_flow_dependent
        Case 0
            Print #1, "<shear_model>constant</shear_model>"
        Case 1
            Print #1, "<shear_model>flow_dependent</shear_model>"
        End Select
End Select

Print #1, "<turbulent_kinetic_energy>" + CStr(ke_turb) + "</turbulent_kinetic_energy>"
Print #1, "<turbulent_dissipation_rate>" + CStr(diss_turb) + "</turbulent_dissipation_rate>"

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</supply>"
End Sub
Sub build_extract(name, x_position, y_position, z_position, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, rectangular_x_size, rectangular_y_size, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_grid_constraint, notes, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<extract>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

Print #1, "<size>"
Print #1, "<x>" + CStr(rectangular_x_size) + "</x>"
Print #1, "<y>" + CStr(rectangular_y_size) + "</y>"
Print #1, "</size>"

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If

If (all_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</extract>"
End Sub
Sub build_source(name, x_position, y_position, z_position, x_size, y_size, z_size, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, collapse_direction_0_nocollapse_1_x_2_y_3_z, collapse_face_0_lowface_1_midpoint_2_highface, source_attribute, source_attribute_attachment_side_0_low_1_high, occupancy_attribute, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_directions_grid_constraint_attribute, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<source>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

If (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
End If



Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y><z>" + CStr(z_size) + "</z></size>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

If (source_attribute <> "0") Then
Print #1, "<source>" + source_attribute + "</source>"

If (collapse_direction_0_nocollapse_1_x_2_y_3_z <> 0) Then
If (source_attribute_attachment_side_0_low_1_high = 0) Then
Print #1, "<attachment_side>low_side</attachment_side>"
ElseIf (source_attribute_attachment_side_0_low_1_high = 1) Then
Print #1, "<attachment_side>high_side</attachment_side>"
End If
End If
End If

If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If

If (all_directions_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_directions_grid_constraint_attribute + "</all_grid_constraint>"
End If

If (occupancy_attribute <> "0") Then
Print #1, "<occupancy>" + occupancy_attribute + "</occupancy>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</source>"

End Sub
Sub build_resistance(name, x_position, y_position, z_position, x_size, y_size, z_size, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, collapse_direction_0_nocollapse_1_x_2_y_3_z, collapse_face_0_lowface_1_midpoint_2_highface, rotation_angle, rotated_about_0_None_1_xaxis_2_yaxis_3_zaxis, resistance_attribute, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_grid_constraint_attribute, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<resistance>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

If (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
End If


Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y><z>" + CStr(z_size) + "</z></size>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

'rotation_angle, rotated_about_0_None_1_xaxis_2_yaxis_3_zaxis
Select Case rotated_about_0_None_1_xaxis_2_yaxis_3_zaxis
    Case 1
        Print #1, "<rotation>"
        Print #1, "<angle>" + CStr(rotation_angle) + "</angle>"
        Print #1, "<rotated_about>x_axis</rotated_about>"
        Print #1, "</rotation>"
    Case 2
        Print #1, "<rotation>"
        Print #1, "<angle>" + CStr(rotation_angle) + "</angle>"
        Print #1, "<rotated_about>y_axis</rotated_about>"
        Print #1, "</rotation>"
    Case 3
        Print #1, "<rotation>"
        Print #1, "<angle>" + CStr(rotation_angle) + "</angle>"
        Print #1, "<rotated_about>z_axis</rotated_about>"
        Print #1, "</rotation>"
End Select

If (resistance_attribute <> "0") Then
Print #1, "<resistance>" + resistance_attribute + "</resistance>"
End If

If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If
If (all_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint_attribute + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

Print #1, "</resistance>"

End Sub
Sub build_region(name, x_position, y_position, z_position, x_size, y_size, z_size, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, collapse_direction_0_nocollapse_1_x_2_y_3_z, collapse_face_0_lowface_1_midpoint_2_highface, fluid_attribute, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_grid_constraint, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<region>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

If (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
End If



Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y><z>" + CStr(z_size) + "</z></size>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

If (fluid_attribute <> "0") Then
Print #1, "<fluid>" + fluid_attribute + "</fluid>"
End If

If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If

If (all_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

Print #1, "</region>"

End Sub
Sub build_assembly(name, x_position, y_position, z_position, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, material_attribute, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_grid_constraint_attribute, notes, localized_grid_0_false_1_true, ignore_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<assembly>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

If (ignore_0_false_1_true = 0) Then
Print #1, "<ignore>false</ignore>"
ElseIf (ignore_0_false_1_true = 1) Then
Print #1, "<ignore>true</ignore>"
End If
Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

If (material_attribute <> "0") Then
Print #1, "<material>" + material_attribute + "</material>"
End If

If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If
If (all_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint_attribute + "</all_grid_constraint>"
End If
If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If


If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

Print #1, "<geometry>"

End Sub
Sub end_assembly()
Print #1, "</geometry>"
Print #1, "</assembly>"
End Sub
Sub build_die_discrete_sources(name, x_position, y_position, z_position, x_size, y_size, z_size, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, uniform_dissipation_0_true_1_false, uniform_power, string_containing_discrete_sources, material, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_directions_grid_constraint, x_low_surface, x_high_surface, y_low_surface, y_high_surface, z_low_surface, z_high_surface, all_faces_surface, x_low_radiation, x_high_radiation, y_low_radiation, y_high_radiation, z_low_radiation, z_high_radiation, all_faces_radiation, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)
Dim points() As String

Print #1, "<die>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<name>" + name + "</name>"

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y><z>" + CStr(z_size) + "</z></size>"


Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

If (uniform_dissipation_0_true_1_false = 0) Then
    Print #1, "<power_dissipation_type>uniform</power_dissipation_type>"
    Print #1, "<uniform_power>" + CStr(uniform_power) + "</uniform_power>"
Else
    Print #1, "<power_dissipation_type>non_uniform</power_dissipation_type>"
    Print #1, "<non_uniform_type>discrete</non_uniform_type>"
    
    Print #1, "<discrete_sources>"
    
    
        
    points() = Split(string_containing_discrete_sources, ",")

        For k = 0 To UBound(points) Step 4
            Print #1, "<source><name>" + points(k) + "</name><start>" + points(k + 1) + "</start><end>" + points(k + 2) + "</end><power>" + points(k + 3) + "</power></source>"
        Next k
    
    Print #1, "</discrete_sources>"
    
End If

If (material <> "0") Then
Print #1, "<die_material>" + material + "</die_material>"
End If

If (x_low_surface <> "0") Then
Print #1, "<x_low_surface>" + x_low_surface + "</x_low_surface>"
End If

If (x_high_surface <> "0") Then
Print #1, "<x_high_surface>" + x_high_surface + "</x_high_surface>"
End If

If (y_low_surface <> "0") Then
Print #1, "<y_low_surface>" + y_low_surface + "</y_low_surface>"
End If

If (y_high_surface <> "0") Then
Print #1, "<y_high_surface>" + y_high_surface + "</y_high_surface>"
End If

If (z_low_surface <> "0") Then
Print #1, "<z_low_surface>" + z_low_surface + "</z_low_surface>"
End If

If (z_high_surface <> "0") Then
Print #1, "<z_high_surface>" + z_high_surface + "</z_high_surface>"
End If

If (all_faces_surface <> "0") Then
Print #1, "<all_surface>" + all_faces_surface + "</all_surface>"
End If

If (x_low_radiation <> "0") Then
Print #1, "<x_low_radiation>" + x_low_radiation + "</x_low_radiation>"
End If

If (x_high_radiation <> "0") Then
Print #1, "<x_high_radiation>" + x_high_radiation + "</x_high_radiation>"
End If

If (y_low_radiation <> "0") Then
Print #1, "<y_low_radiation>" + y_low_radiation + "</y_low_radiation>"
End If

If (y_high_radiation <> "0") Then
Print #1, "<y_high_radiation>" + y_high_radiation + "</y_high_radiation>"
End If

If (z_low_radiation <> "0") Then
Print #1, "<z_low_radiation>" + z_low_radiation + "</z_low_radiation>"
End If

If (z_high_radiation <> "0") Then
Print #1, "<z_high_radiation>" + z_high_radiation + "</z_high_radiation>"
End If

If (all_faces_radiation <> "0") Then
Print #1, "<all_radiation>" + all_faces_radiation + "</all_radiation>"
End If

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_directions_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_directions_grid_constraint + "</all_grid_constraint>"
End If

If (notes <> "0") Then
 Print #1, "<notes>" + notes + "</notes>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If


Print #1, "</die>"

End Sub
Sub build_die_total_coverage(name, x_position, y_position, z_position, x_size, y_size, z_size, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, uniform_dissipation_0_true_1_false, uniform_power, number_in_x, number_in_y, string_containing_powers, material, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_directions_grid_constraint, x_low_surface, x_high_surface, y_low_surface, y_high_surface, z_low_surface, z_high_surface, all_faces_surface, x_low_radiation, x_high_radiation, y_low_radiation, y_high_radiation, z_low_radiation, z_high_radiation, all_faces_radiation, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)
Dim points() As String

Print #1, "<die>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<name>" + name + "</name>"

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y><z>" + CStr(z_size) + "</z></size>"


Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

If (uniform_dissipation_0_true_1_false = 0) Then
    Print #1, "<power_dissipation_type>uniform</power_dissipation_type>"
    Print #1, "<uniform_power>" + CStr(uniform_power) + "</uniform_power>"
Else
    Print #1, "<power_dissipation_type>non_uniform</power_dissipation_type>"
    Print #1, "<non_uniform_type>total_coverage</non_uniform_type>"
    
    Print #1, "<total_coverage_sources>"
    Print #1, "<number_in_x>" + CStr(number_in_x) + "</number_in_x>"
    Print #1, "<number_in_y>" + CStr(number_in_y) + "</number_in_y>"
    Print #1, "<powers>"
        
    points() = Split(string_containing_powers, ",")

        For k = 0 To UBound(points) Step 1
            Print #1, "<power>" + points(k) + "</power>"
        Next k
    
    Print #1, "</powers>"
    Print #1, "</total_coverage_sources>"
    
End If

If (material <> "0") Then
Print #1, "<die_material>" + material + "</die_material>"
End If

If (x_low_surface <> "0") Then
Print #1, "<x_low_surface>" + x_low_surface + "</x_low_surface>"
End If

If (x_high_surface <> "0") Then
Print #1, "<x_high_surface>" + x_high_surface + "</x_high_surface>"
End If

If (y_low_surface <> "0") Then
Print #1, "<y_low_surface>" + y_low_surface + "</y_low_surface>"
End If

If (y_high_surface <> "0") Then
Print #1, "<y_high_surface>" + y_high_surface + "</y_high_surface>"
End If

If (z_low_surface <> "0") Then
Print #1, "<z_low_surface>" + z_low_surface + "</z_low_surface>"
End If

If (z_high_surface <> "0") Then
Print #1, "<z_high_surface>" + z_high_surface + "</z_high_surface>"
End If

If (all_faces_surface <> "0") Then
Print #1, "<all_surface>" + all_faces_surface + "</all_surface>"
End If

If (x_low_radiation <> "0") Then
Print #1, "<x_low_radiation>" + x_low_radiation + "</x_low_radiation>"
End If

If (x_high_radiation <> "0") Then
Print #1, "<x_high_radiation>" + x_high_radiation + "</x_high_radiation>"
End If

If (y_low_radiation <> "0") Then
Print #1, "<y_low_radiation>" + y_low_radiation + "</y_low_radiation>"
End If

If (y_high_radiation <> "0") Then
Print #1, "<y_high_radiation>" + y_high_radiation + "</y_high_radiation>"
End If

If (z_low_radiation <> "0") Then
Print #1, "<z_low_radiation>" + z_low_radiation + "</z_low_radiation>"
End If

If (z_high_radiation <> "0") Then
Print #1, "<z_high_radiation>" + z_high_radiation + "</z_high_radiation>"
End If

If (all_faces_radiation <> "0") Then
Print #1, "<all_radiation>" + all_faces_radiation + "</all_radiation>"
End If

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_directions_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_directions_grid_constraint + "</all_grid_constraint>"
End If

If (notes <> "0") Then
 Print #1, "<notes>" + notes + "</notes>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If


Print #1, "</die>"

End Sub
Sub build_PDML(name, PDML_file, x_position, y_position, z_position, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, notes)

Print #1, "<pdml>"
Print #1, "<name>" + name + "</name>"

Print #1, "<file>" + PDML_file + "</file>"

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

If (notes <> "0") Then
 Print #1, "<notes>" + notes + "</notes>"
End If


Print #1, "</pdml>"

End Sub
Sub build_powermap(name, powermap_file, x_position, y_position, z_position, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, material, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_directions_grid_constraint, all_faces_surface, all_faces_radiation, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<powermap>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<file>" + powermap_file + "</file>"

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

If (material <> "0") Then
Print #1, "<material>" + material + "</material>"
End If

If (all_faces_surface <> "0") Then
Print #1, "<all_surface>" + all_faces_surface + "</all_surface>"
End If

If (all_faces_radiation <> "0") Then
Print #1, "<all_radiation>" + all_faces_radiation + "</all_radiation>"
End If

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_directions_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_directions_grid_constraint + "</all_grid_constraint>"
End If


If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</powermap>"

End Sub
Sub build_cylinder(name, x_position, y_position, z_position, radius, height, number_of_facets, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, material_attribute, thermal_attribute, surface_attribute, radiation_attribute, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_directions_grid_constraint_attribute, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

'Number of facets should be 4, 8, 12, etc to a max of 64

Print #1, "<cylinder>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"
Print #1, "<radius>" + CStr(radius) + "</radius>"
Print #1, "<height>" + CStr(height) + "</height>"

Print #1, "<modeling_level>" + CStr(number_of_facets) + " facets</modeling_level>"

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

If (material_attribute <> "0") Then
Print #1, "<material>" + material_attribute + "</material>"
End If

If (thermal_attribute <> "0") Then
Print #1, "<thermal>" + thermal_attribute + "</thermal>"
End If

If (surface_attribute <> "0") Then
Print #1, "<surface>" + surface_attribute + "</surface>"
End If

If (radiation_attribute <> "0") Then
Print #1, "<all_radiation>" + radiation_attribute + "</all_radiation>"
End If

If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If

If (all_directions_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_directions_grid_constraint_attribute + "</all_grid_constraint>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</cylinder>"

End Sub
Sub build_monitor_point(name, x_position, y_position, z_position, notes, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<monitor_point>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</monitor_point>"

End Sub
Sub build_enclosure(name, x_pos, y_pos, z_pos, x_size, y_size, z_size, wall_thickness, modeling_level_0_thick_1_thin, x_high_wall_0_enclosure_1_thick_2_thin_3_removed, x_low_wall_0_enclosure_1_thick_2_thin_3_removed, y_high_wall_0_enclosure_1_thick_2_thin_3_removed, y_low_wall_0_enclosure_1_thick_2_thin_3_removed, z_high_wall_0_enclosure_1_thick_2_thin_3_removed, z_low_wall_0_enclosure_1_thick_2_thin_3_removed, x_low_thickness, x_high_thickness, y_low_thickness, y_high_thickness, z_low_thickness, z_high_thickness, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, material_attribute, radiation_attribute, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_grid_constraint_attribute, all_surface_exchange_attribute, thermal_attribute, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<enclosure>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position><x>" + CStr(x_pos) + "</x><y>" + CStr(y_pos) + "</y><z>" + CStr(z_pos) + "</z></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y><z>" + CStr(z_size) + "</z></size>"

Print #1, "<wall_thickness>" + CStr(wall_thickness) + "</wall_thickness>"
If (modeling_level_0_thick_1_thin = 0) Then
Print #1, "<modeling_level>thick</modeling_level>"
ElseIf (modeling_level_0_thick_1_thin = 1) Then
Print #1, "<modeling_level>thin</modeling_level>"
End If

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

Select Case x_low_wall_0_enclosure_1_thick_2_thin_3_removed
    Case 0
        Print #1, "<x_low_wall>true</x_low_wall>"
    Case 1
        Print #1, "<x_low_wall>true</x_low_wall>"
        Print #1, "<x_low_wall_modeling>thick</x_low_wall_modeling>"
        Print #1, "<x_low_wall_thickness>" + CStr(x_low_thickness) + "</x_low_wall_thickness>"
    Case 2
        Print #1, "<x_low_wall>true</x_low_wall>"
        Print #1, "<x_low_wall_modeling>thin</x_low_wall_modeling>"
        Print #1, "<x_low_wall_thickness>" + CStr(x_low_thickness) + "</x_low_wall_thickness>"
    Case 3
        Print #1, "<x_low_wall>false</x_low_wall>"
End Select

Select Case x_high_wall_0_enclosure_1_thick_2_thin_3_removed
    Case 0
        Print #1, "<x_high_wall>true</x_high_wall>"
    Case 1
        Print #1, "<x_high_wall>true</x_high_wall>"
        Print #1, "<x_high_wall_modeling>thick</x_high_wall_modeling>"
        Print #1, "<x_high_wall_thickness>" + CStr(x_high_thickness) + "</x_high_wall_thickness>"
    Case 2
        Print #1, "<x_high_wall>true</x_high_wall>"
        Print #1, "<x_high_wall_modeling>thin</x_high_wall_modeling>"
        Print #1, "<x_high_wall_thickness>" + CStr(x_high_thickness) + "</x_high_wall_thickness>"
    Case 3
        Print #1, "<x_high_wall>false</x_high_wall>"
End Select

Select Case y_low_wall_0_enclosure_1_thick_2_thin_3_removed
    Case 0
        Print #1, "<y_low_wall>true</y_low_wall>"
    Case 1
        Print #1, "<y_low_wall>true</y_low_wall>"
        Print #1, "<y_low_wall_modeling>thick</y_low_wall_modeling>"
        Print #1, "<y_low_wall_thickness>" + CStr(y_low_thickness) + "</y_low_wall_thickness>"
    Case 2
        Print #1, "<y_low_wall>true</y_low_wall>"
        Print #1, "<y_low_wall_modeling>thin</y_low_wall_modeling>"
        Print #1, "<y_low_wall_thickness>" + CStr(y_low_thickness) + "</y_low_wall_thickness>"
    Case 3
        Print #1, "<y_low_wall>false</y_low_wall>"
End Select

Select Case y_high_wall_0_enclosure_1_thick_2_thin_3_removed
    Case 0
        Print #1, "<y_high_wall>true</y_high_wall>"
    Case 1
        Print #1, "<y_high_wall>true</y_high_wall>"
        Print #1, "<y_high_wall_modeling>thick</y_high_wall_modeling>"
        Print #1, "<y_high_wall_thickness>" + CStr(y_high_thickness) + "</y_high_wall_thickness>"
    Case 2
        Print #1, "<y_high_wall>true</y_high_wall>"
        Print #1, "<y_high_wall_modeling>thin</y_high_wall_modeling>"
        Print #1, "<y_high_wall_thickness>" + CStr(y_high_thickness) + "</y_high_wall_thickness>"
    Case 3
        Print #1, "<y_high_wall>false</y_high_wall>"
End Select

Select Case z_low_wall_0_enclosure_1_thick_2_thin_3_removed
    Case 0
        Print #1, "<z_low_wall>true</z_low_wall>"
    Case 1
        Print #1, "<z_low_wall>true</z_low_wall>"
        Print #1, "<z_low_wall_modeling>thick</z_low_wall_modeling>"
        Print #1, "<z_low_wall_thickness>" + CStr(z_low_thickness) + "</z_low_wall_thickness>"
    Case 2
        Print #1, "<z_low_wall>true</z_low_wall>"
        Print #1, "<z_low_wall_modeling>thin</z_low_wall_modeling>"
        Print #1, "<z_low_wall_thickness>" + CStr(z_low_thickness) + "</z_low_wall_thickness>"
    Case 3
        Print #1, "<z_low_wall>false</z_low_wall>"
End Select

Select Case z_high_wall_0_enclosure_1_thick_2_thin_3_removed
    Case 0
        Print #1, "<z_high_wall>true</z_high_wall>"
    Case 1
        Print #1, "<z_high_wall>true</z_high_wall>"
        Print #1, "<z_high_wall_modeling>thick</z_high_wall_modeling>"
        Print #1, "<z_high_wall_thickness>" + CStr(z_high_thickness) + "</z_high_wall_thickness>"
    Case 2
        Print #1, "<z_high_wall>true</z_high_wall>"
        Print #1, "<z_high_wall_modeling>thin</z_high_wall_modeling>"
        Print #1, "<z_high_wall_thickness>" + CStr(z_high_thickness) + "</z_high_wall_thickness>"
    Case 3
        Print #1, "<z_high_wall>false</z_high_wall>"
End Select

If (material_attribute <> "0") Then
Print #1, "<material>" + material_attribute + "</material>"
End If

If (thermal_attribute <> "0") Then
Print #1, "<thermal>" + thermal_attribute + "</thermal>"
End If

If (radiation_attribute <> "0") Then
Print #1, "<all_radiation>" + radiation_attribute + "</all_radiation>"
End If

If (all_surface_exchange_attribute <> "0") Then
Print #1, "<all_surface_exchange>" + all_surface_exchange_attribute + "</all_surface_exchange>"
End If

If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If
If (all_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint_attribute + "</all_grid_constraint>"
End If


If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</enclosure>"

End Sub
Sub build_subdomain(xpos, ypos, zpos, xsize, ysize, zsize, pressure_initial_value, x_velocity_initial_value, y_velocity_initial_value, z_velocity_initial_value, temperature_initial_value, turb_vis_initial_value, ke_turb_initial_value, diss_turb_initial_value, density_initial_value, concentration_1_initial_value, concentration_2_initial_value, concentration_3_initial_value, concentration_4_initial_value, concentration_5_initial_value, notes)

Print #1, "<subdomain>"
Print #1, "<position>"
Print #1, "<x>" + CStr(xpos) + "</x>"
Print #1, "<y>" + CStr(ypos) + "</y>"
Print #1, "<z>" + CStr(zpos) + "</z>"
Print #1, "</position>"
Print #1, "<size>"
Print #1, "<x>" + CStr(xsize) + "</x>"
Print #1, "<y>" + CStr(ysize) + "</y>"
Print #1, "<z>" + CStr(zsize) + "</z>"
Print #1, "</size>"

Print #1, "<initial_variables>"
Print #1, "<pressure>" + CStr(pressure_initial_value) + "</pressure>"
Print #1, "<x_velocity>" + CStr(x_velocity_initial_value) + "</x_velocity>"
Print #1, "<y_velocity>" + CStr(y_velocity_initial_value) + "</y_velocity>"
Print #1, "<z_velocity>" + CStr(z_velocity_initial_value) + "</z_velocity>"
Print #1, "<temperature>" + CStr(temperature_initial_value) + "</temperature>"
Print #1, "<turb_vis>" + CStr(turb_vis_initial_value) + "</turb_vis>"
Print #1, "<ke_turb>" + CStr(ke_turb_initial_value) + "</ke_turb>"
Print #1, "<diss_turb>" + CStr(diss_turb_initial_value) + "</diss_turb>"
Print #1, "<density>" + CStr(density_initial_value) + "</density>"
Print #1, "<concentration_1>" + CStr(concentration_1_initial_value) + "</concentration_1>"
Print #1, "<concentration_2>" + CStr(concentration_2_initial_value) + "</concentration_2>"
Print #1, "<concentration_3>" + CStr(concentration_3_initial_value) + "</concentration_3>"
Print #1, "<concentration_4>" + CStr(concentration_4_initial_value) + "</concentration_4>"
Print #1, "<concentration_5>" + CStr(concentration_5_initial_value) + "</concentration_5>"

Print #1, "</initial_variables>"

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</subdomain>"

End Sub
Sub build_cutout(name, xpos, ypos, zpos, xsize, ysize, zsize, x_low_ambient_attribute, x_high_ambient_attribute, y_low_ambient_attribute, y_high_ambient_attribute, z_low_ambient_attribute, z_high_ambient_attribute, all_ambient_attribute, x_low_boundary_0_open_1_symmetry, x_high_boundary_0_open_1_symmetry, y_low_boundary_0_open_1_symmetry, y_high_boundary_0_open_1_symmetry, z_low_boundary_0_open_1_symmetry, z_high_boundary_0_open_1_symmetry, all_boundary_0_open_1_symmetry, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_grid_constraint_attribute, notes, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<cutout>"

Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<position>"
Print #1, "<x>" + CStr(xpos) + "</x>"
Print #1, "<y>" + CStr(ypos) + "</y>"
Print #1, "<z>" + CStr(zpos) + "</z>"
Print #1, "</position>"
Print #1, "<size>"
Print #1, "<x>" + CStr(xsize) + "</x>"
Print #1, "<y>" + CStr(ysize) + "</y>"
Print #1, "<z>" + CStr(zsize) + "</z>"
Print #1, "</size>"

If (x_low_ambient_attribute <> "0") Then
Print #1, "<x_low_ambient>" + x_low_ambient_attribute + "</x_low_ambient>"
End If

If (x_high_ambient_attribute <> "0") Then
Print #1, "<x_high_ambient>" + x_high_ambient_attribute + "</x_high_ambient>"
End If

If (y_low_ambient_attribute <> "0") Then
Print #1, "<y_low_ambient>" + y_low_ambient_attribute + "</y_low_ambient>"
End If

If (y_high_ambient_attribute <> "0") Then
Print #1, "<y_high_ambient>" + y_high_ambient_attribute + "</y_high_ambient>"
End If

If (z_low_ambient_attribute <> "0") Then
Print #1, "<z_low_ambient>" + z_low_ambient_attribute + "</z_low_ambient>"
End If

If (z_high_ambient_attribute <> "0") Then
Print #1, "<z_high_ambient>" + z_high_ambient_attribute + "</z_high_ambient>"
End If

If (all_ambient_attribute <> "0") Then
Print #1, "<all_ambient>" + all_ambient_attribute + "</all_ambient>"
End If

If (x_low_boundary_0_open_1_symmetry = 1) Then
Print #1, "<x_low_boundary>symmetry</x_low_boundary>"
End If

If (x_high_boundary_0_open_1_symmetry = 1) Then
Print #1, "<x_high_boundary>symmetry</x_high_boundary>"
End If

If (y_low_boundary_0_open_1_symmetry = 1) Then
Print #1, "<y_low_boundary>symmetry</y_low_boundary>"
End If

If (y_high_boundary_0_open_1_symmetry = 1) Then
Print #1, "<y_high_boundary>symmetry</y_high_boundary>"
End If

If (z_low_boundary_0_open_1_symmetry = 1) Then
Print #1, "<z_low_boundary>symmetry</z_low_boundary>"
End If

If (z_high_boundary_0_open_1_symmetry = 1) Then
Print #1, "<z_high_boundary>symmetry</z_high_boundary>"
End If

If (all_boundary_0_open_1_symmetry = 1) Then
Print #1, "<all_boundary>symmetry</all_boundary>"
End If

If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If
If (all_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint_attribute + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</cutout>"

End Sub
Sub build_domain(xpos, ypos, zpos, xsize, ysize, zsize, x_low_ambient_attribute, x_high_ambient_attribute, y_low_ambient_attribute, y_high_ambient_attribute, z_low_ambient_attribute, z_high_ambient_attribute, x_low_boundary_0_open_1_symmetry, x_high_boundary_0_open_1_symmetry, y_low_boundary_0_open_1_symmetry, y_high_boundary_0_open_1_symmetry, z_low_boundary_0_open_1_symmetry, z_high_boundary_0_open_1_symmetry, fluid_attribute, notes)

Print #1, "<solution_domain>"
Print #1, "<position>"
Print #1, "<x>" + CStr(xpos) + "</x>"
Print #1, "<y>" + CStr(ypos) + "</y>"
Print #1, "<z>" + CStr(zpos) + "</z>"
Print #1, "</position>"
Print #1, "<size>"
Print #1, "<x>" + CStr(xsize) + "</x>"
Print #1, "<y>" + CStr(ysize) + "</y>"
Print #1, "<z>" + CStr(zsize) + "</z>"
Print #1, "</size>"

If (x_low_ambient_attribute <> "0") Then
Print #1, "<x_low_ambient>" + x_low_ambient_attribute + "</x_low_ambient>"
End If

If (x_high_ambient_attribute <> "0") Then
Print #1, "<x_high_ambient>" + x_high_ambient_attribute + "</x_high_ambient>"
End If

If (y_low_ambient_attribute <> "0") Then
Print #1, "<y_low_ambient>" + y_low_ambient_attribute + "</y_low_ambient>"
End If

If (y_high_ambient_attribute <> "0") Then
Print #1, "<y_high_ambient>" + y_high_ambient_attribute + "</y_high_ambient>"
End If

If (z_low_ambient_attribute <> "0") Then
Print #1, "<z_low_ambient>" + z_low_ambient_attribute + "</z_low_ambient>"
End If

If (z_high_ambient_attribute <> "0") Then
Print #1, "<z_high_ambient>" + z_high_ambient_attribute + "</z_high_ambient>"
End If

If (x_low_boundary_0_open_1_symmetry = 1) Then
Print #1, "<x_low_boundary>symmetry</x_low_boundary>"
End If

If (x_high_boundary_0_open_1_symmetry = 1) Then
Print #1, "<x_high_boundary>symmetry</x_high_boundary>"
End If

If (y_low_boundary_0_open_1_symmetry = 1) Then
Print #1, "<y_low_boundary>symmetry</y_low_boundary>"
End If

If (y_high_boundary_0_open_1_symmetry = 1) Then
Print #1, "<y_high_boundary>symmetry</y_high_boundary>"
End If

If (z_low_boundary_0_open_1_symmetry = 1) Then
Print #1, "<z_low_boundary>symmetry</z_low_boundary>"
End If

If (z_high_boundary_0_open_1_symmetry = 1) Then
Print #1, "<z_high_boundary>symmetry</z_high_boundary>"
End If

If (fluid_attribute <> "0") Then
Print #1, "<fluid>" + fluid_attribute + "</fluid>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</solution_domain>"
End Sub
Sub build_2R(name, xpos, ypos, zpos, xsize, ysize, zsize, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, power, thetajb, thetajc, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_directions_grid_constraint, x_low_surface, x_high_surface, y_low_surface, y_high_surface, z_low_surface, z_high_surface, all_faces_surface, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<component2r>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

Print #1, "<position>"
Print #1, "<x>" + CStr(xpos) + "</x>"
Print #1, "<y>" + CStr(ypos) + "</y>"
Print #1, "<z>" + CStr(zpos) + "</z>"
Print #1, "</position>"
Print #1, "<size>"
Print #1, "<x>" + CStr(xsize) + "</x>"
Print #1, "<y>" + CStr(ysize) + "</y>"
Print #1, "<z>" + CStr(zsize) + "</z>"
Print #1, "</size>"
Print #1, "<junction_power>" + CStr(power) + "</junction_power>"
Print #1, "<junction_case_resistance>" + CStr(thetajc) + "</junction_case_resistance>"
Print #1, "<junction_board_resistance>" + CStr(thetajb) + "</junction_board_resistance>"
Print #1, "<radiation>true</radiation>"

If (x_low_surface <> "0") Then
Print #1, "<x_low_surface>" + x_low_surface + "</x_low_surface>"
End If

If (x_high_surface <> "0") Then
Print #1, "<x_high_surface>" + x_high_surface + "</x_high_surface>"
End If

If (y_low_surface <> "0") Then
Print #1, "<y_low_surface>" + y_low_surface + "</y_low_surface>"
End If

If (y_high_surface <> "0") Then
Print #1, "<y_high_surface>" + y_high_surface + "</y_high_surface>"
End If

If (z_low_surface <> "0") Then
Print #1, "<z_low_surface>" + z_low_surface + "</z_low_surface>"
End If

If (z_high_surface <> "0") Then
Print #1, "<z_high_surface>" + z_high_surface + "</z_high_surface>"
End If

If (all_faces_surface <> "0") Then
Print #1, "<all_surface>" + all_faces_surface + "</all_surface>"
End If

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_directions_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_directions_grid_constraint + "</all_grid_constraint>"
End If


If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

Print #1, "</component2r>"

End Sub
Sub build_pcb_start(name, xpos, ypos, zpos, x_size, y_size, thickness, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, keypoint_component_height_0_true_1_false, heat_dissipated_to_air, top_roughness_height, bottom_roughness_height, conducting_type_0_nonconducting_1_percent_by_volume_2_board_mass_3_layer_definition, percent_conductor_by_vol, board_mass, string_containing_stackup, dielectric_material, conductor_material, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_grid_constraint_attribute, all_radiation, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)
Dim points() As String

'Layer Stackup string should be comma seperated pairs of layer thickness (m) and percentage coverage.  0.000035, 22, 0.000070, 95, etc

Print #1, "<pcb>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

Print #1, "<position>"
Print #1, "<x>" + CStr(xpos) + "</x>"
Print #1, "<y>" + CStr(ypos) + "</y>"
Print #1, "<z>" + CStr(zpos) + "</z>"
Print #1, "</position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y></size>"
Print #1, "<thickness>" + CStr(thickness) + "</thickness>"

If (keypoint_component_height_0_true_1_false = 0) Then
    Print #1, "<keypoint_component_height>true</keypoint_component_height>"
Else
    Print #1, "<keypoint_component_height>false</keypoint_component_height>"
End If

Print #1, "<heat_dissipated_to_air>" + CStr(heat_dissipated_to_air) + "</heat_dissipated_to_air>"
Print #1, "<top_roughness_height>" + CStr(top_roughness_height) + "</top_roughness_height>"
Print #1, "<bottom_roughness_height>" + CStr(bottom_roughness_height) + "</bottom_roughness_height>"

Select Case conducting_type_0_nonconducting_1_percent_by_volume_2_board_mass_3_layer_definition
Case 0
     Print #1, "<modeling_level>non_conducting</modeling_level>"
Case 1
    Print #1, "<modeling_level>conducting</modeling_level>"
    Print #1, "<conducting_type>percent_conductor_by_vol</conducting_type>"
    Print #1, "<percent_conductor_by_vol>" + CStr(percent_conductor_by_vol) + "</percent_conductor_by_vol>"
Case 2
    Print #1, "<modeling_level>conducting</modeling_level>"
    Print #1, "<conducting_type>board_mass</conducting_type>"
    Print #1, "<board_mass>" + CStr(board_mass) + "</board_mass>"
Case 3
    Print #1, "<modeling_level>conducting</modeling_level>"
    Print #1, "<conducting_type>layer_definition</conducting_type>"
    Print #1, "<layer_definition>"
    
    
        points() = Split(string_containing_thermal_resistances, ",")

        For k = 0 To UBound(points) Step 2
        Print #1, "<layer>"
        Print #1, "<thickness>" + points(k) + "</thickness><percentage_coverage>" + points(k + 1) + "</percentage_coverage>"
        Print #1, "</layer>"

        Next k

    Print #1, "</layer_definition>"
    
End Select

If (dielectric_material <> "0") Then
Print #1, "<dielectric_material>" + dielectric_material + "</dielectric_material>"
End If

If (conductor_material <> "0") Then
Print #1, "<conductor_material>" + conductor_material + "</conductor_material>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If

If (all_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_constraint_attribute + "</all_grid_constraint>"
End If

If (all_radiation <> "0") Then
Print #1, "<all_radiation>" + all_radiation + "</all_radiation>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "<components>"

End Sub
Sub build_pcb_component(name, x_position, y_position, x_size, y_size, z_size, board_side_0_top_1_bottom, power, modeling_level_0_apply_over_board_1_discrete_solid_2_discrete_footprint, resistance_junction_board, resistance_junction_case, resistance_junction_sides, pattern_0_No_1_Yes, number_in_x, number_in_y, pitch_in_x, pitch_in_y, lump_patterned_components_0_No_1_Yes, material, x_grid_constraint, y_grid_constraint, z_grid_constraint, all_directions_grid_constraint, notes, localized_grid_0_false_1_true)

Print #1, "<component>"
Print #1, "<name>" + name + "</name>"

Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y><z>" + CStr(z_size) + "</z></size>"

Select Case board_side_0_top_1_bottom
    Case 0
        Print #1, "<side>top</side>"
    Case 1
        Print #1, "<side>bottom</side>"
End Select

Print #1, "<power>" + CStr(power) + "</power>"


If (material <> "0") Then
Print #1, "<component_material>" + material + "</component_material>"
End If

Select Case modeling_level_0_apply_over_board_1_discrete_solid_2_discrete_footprint
    Case 0
        Print #1, "<modeling_options>apply_over_board</modeling_options>"
    Case 1
        Print #1, "<modeling_options>discrete</modeling_options>"
        Print #1, "<solid_component>true</solid_component>"
        Print #1, "<resistance_junction_board>" + CStr(resistance_junction_board) + "</resistance_junction_board>"
        Print #1, "<resistance_junction_case>" + CStr(resistance_junction_case) + "</resistance_junction_case>"
        Print #1, "<resistance_junction_sides>" + CStr(resistance_junction_sides) + "</resistance_junction_sides>"
       
        If (pattern_0_No_1_Yes = 1) Then
            Print #1, "<pattern>"
            Print #1, "<number_in_x>" + CStr(number_in_x) + "</number_in_x>"
            Print #1, "<number_in_y>" + CStr(number_in_y) + "</number_in_y>"
            Print #1, "<pitch_in_x>" + CStr(pitch_in_x) + "</pitch_in_x>"
            Print #1, "<pitch_in_y>" + CStr(pitch_in_y) + "</pitch_in_y>"
             If (lump_patterned_components_0_No_1_Yes = 1) Then
                Print #1, "<lump_components>true</lump_components>"
             End If
            Print #1, "</pattern>"
        End If
        
    Case 2
        Print #1, "<modeling_options>discrete</modeling_options>"
        Print #1, "<solid_component>false</solid_component>"
End Select

If (x_grid_constraint <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint + "</x_grid_constraint>"
End If
If (y_grid_constraint <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint + "</y_grid_constraint>"
End If
If (z_grid_constraint <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint + "</z_grid_constraint>"
End If
If (all_directions_grid_constraint <> "0") Then
Print #1, "<all_grid_constraint>" + all_directions_grid_constraint + "</all_grid_constraint>"
End If


If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "</component>"


End Sub
Sub build_pcb_end()
Print #1, "</components>"
Print #1, "</pcb>"
End Sub
Sub build_heatpipe_start(name, xpos, ypos, zpos, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, effective_thermal_resistance, maximum_heat_flow, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_grid_constraint_attribute, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)

Print #1, "<heatpipe>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

Print #1, "<position>"
Print #1, "<x>" + CStr(xpos) + "</x>"
Print #1, "<y>" + CStr(ypos) + "</y>"
Print #1, "<z>" + CStr(zpos) + "</z>"
Print #1, "</position>"


If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

Print #1, "<effective_thermal_resistance>" + CStr(effective_thermal_resistance) + "</effective_thermal_resistance>"
Print #1, "<maximum_heat_flow>" + CStr(maximum_heat_flow) + "</maximum_heat_flow>"

If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If

If (all_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_constraint_attribute + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "<network_cuboids>"

End Sub
Sub build_heatpipe_end()

Print #1, "</network_cuboids>"
Print #1, "</heatpipe>"

End Sub
Sub build_network_assembly_start(name, xpos, ypos, zpos, local_x_i, local_x_j, local_x_k, local_y_i, local_y_j, local_y_k, local_z_i, local_z_j, local_z_k, string_containing_thermal_resistances, string_containing_thermal_capacitances, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_grid_constraint_attribute, notes, localized_grid_0_false_1_true, hidden_0_false_1_true, active_0_false_1_true)
Dim points() As String

Print #1, "<network_assembly>"
Print #1, "<name>" + name + "</name>"

If (active_0_false_1_true = 0) Then
Print #1, "<active>false</active>"
ElseIf (active_0_false_1_true = 1) Then
Print #1, "<active>true</active>"
End If

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

Print #1, "<orientation>"
Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
Print #1, "</orientation>"

Print #1, "<position>"
Print #1, "<x>" + CStr(xpos) + "</x>"
Print #1, "<y>" + CStr(ypos) + "</y>"
Print #1, "<z>" + CStr(zpos) + "</z>"
Print #1, "</position>"


If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

Print #1, "<resistances>"
points() = Split(string_containing_thermal_resistances, ",")

For k = 0 To UBound(points) Step 3
Print #1, "<resistance>"
Print #1, "<i_node>" + points(k) + "</i_node><j_node>" + points(k + 1) + "</j_node><resistance>" + points(k + 2) + "</resistance>"
Print #1, "</resistance>"

Next k

Print #1, "</resistances>"

If (string_containing_thermal_capacitances <> "0") Then
Print #1, "<capacitances>"
points() = Split(string_containing_thermal_capacitances, ",")

For k = 0 To UBound(points) Step 2
Print #1, "<capacitance>"
Print #1, "<i_node>" + points(k) + "</i_node><capacitance>" + points(k + 1) + "</capacitance>"
Print #1, "</capacitance>"

Next k

Print #1, "</capacitances>"
End If


If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If

If (all_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_constraint_attribute + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

Print #1, "<network_nodes>"

End Sub
Sub build_network_assembly_end()

Print #1, "</network_nodes>"
Print #1, "</network_assembly>"

End Sub
Sub build_network_node_start(name, thermal_attribute, notes, hidden_0_false_1_true)

Print #1, "<network_node>"
Print #1, "<name>" + name + "</name>"

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

If (thermal_attribute <> "0") Then
Print #1, "<thermal>" + thermal_attribute + "</thermal>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

End Sub
Sub build_network_node_end()

Print #1, "</network_node>"

End Sub
Sub build_network_node_cuboid_list_start()

Print #1, "<network_cuboids>"

End Sub
Sub build_network_cuboid(name, x_position, y_position, z_position, x_size, y_size, z_size, collapse_direction_0_nocollapse_1_x_2_y_3_z, collapse_face_0_lowface_1_midpoint_2_highface, x_grid_constraint_attribute, y_grid_constraint_attribute, z_grid_constraint_attribute, all_grid_constraint_attribute, x_low_surface_attribute, x_high_surface_attribute, y_low_surface_attribute, y_high_surface_attribute, z_low_surface_attribute, z_high_surface_attribute, all_surface_attribute, x_low_radiation_attribute, x_high_radiation_attribute, y_low_radiation_attribute, y_high_radiation_attribute, z_low_radiation_attribute, z_high_radiation_attribute, all_radiation_attribute, notes, hidden_0_false_1_true, localized_grid_0_false_1_true)

Print #1, "<network_cuboid>"
Print #1, "<name>" + name + "</name>"

If (hidden_0_false_1_true = 1) Then
Print #1, "<hidden>true</hidden>"
End If

If (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 1 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>x_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 2 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>y_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 0) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>low_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 1) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>mid_face</type>"
Print #1, "</collapse>"
ElseIf (collapse_direction_0_nocollapse_1_x_2_y_3_z = 3 And collapse_face_0_lowface_1_midpoint_2_highface = 2) Then
Print #1, "<collapse>"
Print #1, "<direction>z_direction</direction>"
Print #1, "<type>high_face</type>"
Print #1, "</collapse>"
End If



Print #1, "<position><x>" + CStr(x_position) + "</x><y>" + CStr(y_position) + "</y><z>" + CStr(z_position) + "</z></position>"
Print #1, "<size><x>" + CStr(x_size) + "</x><y>" + CStr(y_size) + "</y><z>" + CStr(z_size) + "</z></size>"

'Print #1, "<orientation>"
'Print #1, "<local_x><i>" + CStr(local_x_i) + "</i><j>" + CStr(local_x_j) + "</j><k>" + CStr(local_x_k) + "</k></local_x>"
'Print #1, "<local_y><i>" + CStr(local_y_i) + "</i><j>" + CStr(local_y_j) + "</j><k>" + CStr(local_y_k) + "</k></local_y>"
'Print #1, "<local_z><i>" + CStr(local_z_i) + "</i><j>" + CStr(local_z_j) + "</j><k>" + CStr(local_z_k) + "</k></local_z>"
'Print #1, "</orientation>"

If (x_low_surface_attribute <> "0") Then
Print #1, "<x_low_surface>" + x_low_surface_attribute + "</x_low_surface>"
End If

If (x_high_surface_attribute <> "0") Then
Print #1, "<x_high_surface>" + x_high_surface_attribute + "</x_high_surface>"
End If

If (y_low_surface_attribute <> "0") Then
Print #1, "<y_low_surface>" + y_low_surface_attribute + "</y_low_surface>"
End If

If (y_high_surface_attribute <> "0") Then
Print #1, "<y_high_surface>" + y_high_surface_attribute + "</y_high_surface>"
End If

If (z_low_surface_attribute <> "0") Then
Print #1, "<z_low_surface>" + z_low_surface_attribute + "</z_low_surface>"
End If

If (z_high_surface_attribute <> "0") Then
Print #1, "<z_high_surface>" + z_high_surface_attribute + "</z_high_surface>"
End If

If (all_surface_attribute <> "0") Then
Print #1, "<all_surface>" + all_surface_attribute + "</all_surface>"
End If

If (x_low_radiation_attribute <> "0") Then
Print #1, "<x_low_radiation>" + x_low_radiation_attribute + "</x_low_radiation>"
End If

If (x_high_radiation_attribute <> "0") Then
Print #1, "<x_high_radiation>" + x_high_radiation_attribute + "</x_high_radiation>"
End If

If (y_low_radiation_attribute <> "0") Then
Print #1, "<y_low_radiation>" + y_low_radiation_attribute + "</y_low_radiation>"
End If

If (y_high_radiation_attribute <> "0") Then
Print #1, "<y_high_radiation>" + y_high_radiation_attribute + "</y_high_radiation>"
End If

If (z_low_radiation_attribute <> "0") Then
Print #1, "<z_low_radiation>" + z_low_radiation_attribute + "</z_low_radiation>"
End If

If (z_high_radiation_attribute <> "0") Then
Print #1, "<z_high_radiation>" + z_high_radiation_attribute + "</z_high_radiation>"
End If

If (all_radiation_attribute <> "0") Then
Print #1, "<all_radiation>" + all_radiation_attribute + "</all_radiation>"
End If

If (x_grid_constraint_attribute <> "0") Then
Print #1, "<x_grid_constraint>" + x_grid_constraint_attribute + "</x_grid_constraint>"
End If
If (y_grid_constraint_attribute <> "0") Then
Print #1, "<y_grid_constraint>" + y_grid_constraint_attribute + "</y_grid_constraint>"
End If
If (z_grid_constraint_attribute <> "0") Then
Print #1, "<z_grid_constraint>" + z_grid_constraint_attribute + "</z_grid_constraint>"
End If

If (all_grid_constraint_attribute <> "0") Then
Print #1, "<all_grid_constraint>" + all_grid_constraint_attribute + "</all_grid_constraint>"
End If

If (notes <> "0") Then
Print #1, "<notes>" + notes + "</notes>"
End If

If (localized_grid_0_false_1_true = 0) Then
Print #1, "<localized_grid>false</localized_grid>"
ElseIf (localized_grid_0_false_1_true = 1) Then
Print #1, "<localized_grid>true</localized_grid>"
End If

Print #1, "</network_cuboid>"

End Sub
Sub build_network_node_cuboid_list_end()

Print #1, "</network_cuboids>"

End Sub
Sub build_network_node_monitor_point_list_start()

Print #1, "<network_monitor_points>"

End Sub
Sub build_network_node_monitor_point_list_end()

Print #1, "</network_monitor_points>"

End Sub
Sub start_model_inputs()
Print #1, "<model>"
End Sub
Sub end_model_inputs()
Print #1, "</model>"
End Sub
Sub start_model_modeling()
Print #1, "<modeling>"
End Sub
Sub end_model_modeling()
Print #1, "</modeling>"
End Sub
Sub model_modeling_setup(solution_type_0_flow_and_heat_transfer_1_flow_only_2_conduction_only, radiation_0_off_1_on_2_on_high_accuracy, dimensionality_0_2D_1_3D, transient_0_false_1_true, joule_heating_0_false_1_true)

If (solution_type_0_flow_and_heat_transfer_1_flow_only_2_conduction_only = 0) Then
Print #1, "<solution>flow_heat</solution>"
ElseIf (solution_type_0_flow_and_heat_transfer_1_flow_only_2_conduction_only = 1) Then
Print #1, "<solution>flow_only</solution>"
Else
Print #1, "<solution>conduction_only</solution>"
End If

If (radiation_0_off_1_on_2_on_high_accuracy = 0) Then
Print #1, "<radiation>off</radiation>"
ElseIf (radiation_0_off_1_on_2_on_high_accuracy = 1) Then
Print #1, "<radiation>on</radiation>"
Else
Print #1, "<radiation>high_accuracy</radiation>"
End If

If (dimensionality_0_2D_1_3D = 0) Then
Print #1, "<dimensionality>2d</dimensionality>"
ElseIf (dimensionality_0_2D_1_3D = 1) Then
Print #1, "<dimensionality>3d</dimensionality>"
End If

If (transient_0_false_1_true = 0) Then
Print #1, "<transient>false</transient>"
ElseIf (transient_0_false_1_true = 1) Then
Print #1, "<transient>true</transient>"
End If

If (joule_heating_0_false_1_true = 0) Then
Print #1, "<joule_heating>false</joule_heating>"
ElseIf (transient_0_false_1_true = 1) Then
Print #1, "<joule_heating>true</joule_heating>"
End If

End Sub
Sub model_modeling_store_options(store_mass_flux_0_false_1_true, store_heat_flux_0_false_1_true, store_surface_temperature_0_false_1_true, store_grad_t_0_false_1_true, store_bnsc_0_false_1_true, store_power_density_0_false_1_true, store_mean_radiant_temperature_0_false_1_true, compute_capture_index_0_false_1_true, user_defined_subgroups_for_capture_index_0_false_1_true, store_LMA_0_false_1_true, LMA_recirculation_ratio)

If (store_mass_flux_0_false_1_true = 0) Then
Print #1, "<store_mass_flux>false</store_mass_flux>"
ElseIf (store_mass_flux_0_false_1_true = 1) Then
Print #1, "<store_mass_flux>true</store_mass_flux>"
End If

If (store_heat_flux_0_false_1_true = 0) Then
Print #1, "<store_heat_flux>false</store_heat_flux>"
ElseIf (store_heat_flux_0_false_1_true = 1) Then
Print #1, "<store_heat_flux>true</store_heat_flux>"
End If

If (store_surface_temperature_0_false_1_true = 0) Then
Print #1, "<store_surface_temp>false</store_surface_temp>"
ElseIf (store_surface_temperature_0_false_1_true = 1) Then
Print #1, "<store_surface_temp>true</store_surface_temp>"
End If

If (store_grad_t_0_false_1_true = 0) Then
Print #1, "<store_grad_t>false</store_grad_t>"
ElseIf (store_grad_t_0_false_1_true = 1) Then
Print #1, "<store_grad_t>true</store_grad_t>"
End If

If (store_bnsc_0_false_1_true = 0) Then
Print #1, "<store_bn_sc>false</store_bn_sc>"
ElseIf (store_bnsc_0_false_1_true = 1) Then
Print #1, "<store_bn_sc>true</store_bn_sc>"
End If

If (store_power_density_0_false_1_true = 0) Then
Print #1, "<store_power_density>false</store_power_density>"
ElseIf (store_power_density_0_false_1_true = 1) Then
Print #1, "<store_power_density>true</store_power_density>"
End If

If (store_mean_radiant_temperature_0_false_1_true = 0) Then
Print #1, "<store_mean_radiant_temperature>false</store_mean_radiant_temperature>"
ElseIf (store_mean_radiant_temperature_0_false_1_true = 1) Then
Print #1, "<store_mean_radiant_temperature>true</store_mean_radiant_temperature>"
End If

If (compute_capture_index_0_false_1_true = 0) Then
Print #1, "<compute_capture_index>false</compute_capture_index>"
ElseIf (compute_capture_index_0_false_1_true = 1) Then
Print #1, "<compute_capture_index>true</compute_capture_index>"
End If

If (user_defined_subgroups_for_capture_index_0_false_1_true = 0) Then
Print #1, "<user_defined_subgroups>false</user_defined_subgroups>"
ElseIf (user_defined_subgroups_for_capture_index_0_false_1_true = 1) Then
Print #1, "<user_defined_subgroups>true</user_defined_subgroups>"
End If

If (store_LMA_0_false_1_true = 0) Then
Print #1, "<store_lma>false</store_lma>"
ElseIf (store_LMA_0_false_1_true = 1) Then
Print #1, "<store_lma>true</store_lma>"
Print #1, "<recirculation_ratio>" + CStr(LMA_recirculation_ratio) + "</recirculation_ratio>"
End If

End Sub
Sub model_modeling_concentration_setup(concentration_1_fluid_attribute, concentration_2_fluid_attribute, concentration_3_fluid_attribute, concentration_4_fluid_attribute, concentration_5_fluid_attribute, concentration_6_fluid_attribute, concentration_7_fluid_attribute, concentration_8_fluid_attribute, concentration_9_fluid_attribute, concentration_10_fluid_attribute, concentration_11_fluid_attribute, concentration_12_fluid_attribute, concentration_13_fluid_attribute, concentration_14_fluid_attribute, concentration_15_fluid_attribute)

Print #1, "<concentrations>"

If (concentration_1_fluid_attribute <> "0") Then
Print #1, "<concentration_1>"
Print #1, "<fluid>" + CStr(concentration_1_fluid_attribute) + "</fluid>"
Print #1, "</concentration_1>"
End If

If (concentration_2_fluid_attribute <> "0") Then
Print #1, "<concentration_2>"
Print #1, "<fluid>" + CStr(concentration_2_fluid_attribute) + "</fluid>"
Print #1, "</concentration_2>"
End If

If (concentration_3_fluid_attribute <> "0") Then
Print #1, "<concentration_3>"
Print #1, "<fluid>" + CStr(concentration_3_fluid_attribute) + "</fluid>"
Print #1, "</concentration_3>"
End If

If (concentration_4_fluid_attribute <> "0") Then
Print #1, "<concentration_4>"
Print #1, "<fluid>" + CStr(concentration_4_fluid_attribute) + "</fluid>"
Print #1, "</concentration_4>"
End If

If (concentration_5_fluid_attribute <> "0") Then
Print #1, "<concentration_5>"
Print #1, "<fluid>" + CStr(concentration_5_fluid_attribute) + "</fluid>"
Print #1, "</concentration_5>"
End If


If (concentration_6_fluid_attribute <> "0") Then
Print #1, "<concentration_6>"
Print #1, "<fluid>" + CStr(concentration_6_fluid_attribute) + "</fluid>"
Print #1, "</concentration_6>"
End If

If (concentration_7_fluid_attribute <> "0") Then
Print #1, "<concentration_7>"
Print #1, "<fluid>" + CStr(concentration_7_fluid_attribute) + "</fluid>"
Print #1, "</concentration_7>"
End If

If (concentration_8_fluid_attribute <> "0") Then
Print #1, "<concentration_8>"
Print #1, "<fluid>" + CStr(concentration_8_fluid_attribute) + "</fluid>"
Print #1, "</concentration_8>"
End If

If (concentration_9_fluid_attribute <> "0") Then
Print #1, "<concentration_9>"
Print #1, "<fluid>" + CStr(concentration_9_fluid_attribute) + "</fluid>"
Print #1, "</concentration_9>"
End If

If (concentration_10_fluid_attribute <> "0") Then
Print #1, "<concentration_10>"
Print #1, "<fluid>" + CStr(concentration_5_fluid_attribute) + "</fluid>"
Print #1, "</concentration_10>"
End If

If (concentration_11_fluid_attribute <> "0") Then
Print #1, "<concentration_11>"
Print #1, "<fluid>" + CStr(concentration_11_fluid_attribute) + "</fluid>"
Print #1, "</concentration_11>"
End If

If (concentration_12_fluid_attribute <> "0") Then
Print #1, "<concentration_12>"
Print #1, "<fluid>" + CStr(concentration_12_fluid_attribute) + "</fluid>"
Print #1, "</concentration_12>"
End If

If (concentration_13_fluid_attribute <> "0") Then
Print #1, "<concentration_13>"
Print #1, "<fluid>" + CStr(concentration_13_fluid_attribute) + "</fluid>"
Print #1, "</concentration_13>"
End If

If (concentration_14_fluid_attribute <> "0") Then
Print #1, "<concentration_14>"
Print #1, "<fluid>" + CStr(concentration_14_fluid_attribute) + "</fluid>"
Print #1, "</concentration_14>"
End If

If (concentration_15_fluid_attribute <> "0") Then
Print #1, "<concentration_15>"
Print #1, "<fluid>" + CStr(concentration_15_fluid_attribute) + "</fluid>"
Print #1, "</concentration_15>"
End If

Print #1, "</concentrations>"
End Sub
Sub model_modeling_visibility_setup(active_concentration_number, proportionality_constant_type_0_illuminated_signs_1_reflecting_signs_2_user_defined, user_defined_proportionality_constant, specific_extinction_coefficient_type_0_smouldering_combustion_1_flaming_combustion_2_user_defined, user_defined_specific_extinction_coefficient, maximum_visibility_distance)

Print #1, "<store_visibility>true</store_visibility>"
Print #1, "<visibility_distance_parameters>"

Print #1, "<active_concentration>concentration_" + CStr(active_concentration_number) + "</active_concentration>"

If (proportionality_constant_type_0_illuminated_signs_1_reflecting_signs_2_user_defined = 0) Then
Print #1, "<proportionality_constant_type>illuminated_signs</proportionality_constant_type>"

ElseIf (proportionality_constant_type_0_illuminated_signs_1_reflecting_signs_2_user_defined = 1) Then
Print #1, "<proportionality_constant_type>reflecting_signs</proportionality_constant_type>"

ElseIf (proportionality_constant_type_0_illuminated_signs_1_reflecting_signs_2_user_defined = 2) Then
Print #1, "<proportionality_constant_type>user_defined</proportionality_constant_type>"
Print #1, "<proportionality_constant>" + CStr(user_defined_proportionality_constant) + "</proportionality_constant>"

End If

If (specific_extinction_coefficient_type_0_smouldering_combustion_1_flaming_combustion_2_user_defined = 0) Then
Print #1, "<specific_extinction_coefficient_type>smouldering_combustion</specific_extinction_coefficient_type>"

ElseIf (specific_extinction_coefficient_type_0_smouldering_combustion_1_flaming_combustion_2_user_defined = 1) Then
Print #1, "<specific_extinction_coefficient_type>flaming_combustion</specific_extinction_coefficient_type>"

ElseIf (specific_extinction_coefficient_type_0_smouldering_combustion_1_flaming_combustion_2_user_defined = 2) Then
Print #1, "<specific_extinction_coefficient_type>user_defined</specific_extinction_coefficient_type>"
Print #1, "<specific_extinction_coefficient>" + CStr(user_defined_specific_extinction_coefficient) + "</specific_extinction_coefficient>"

End If

Print #1, "<maximum_visibility_distance>" + CStr(maximum_visibility_distance) + "</maximum_visibility_distance>"

Print #1, "</visibility_distance_parameters>"

End Sub
Sub model_modeling_solar_setup(solve_solar_0_true_1_false, angle_measured_from_0_X_1_Y_2_Z, angle, latitude, day, month, solar_time, solar_type_0_intensity_1_cloudiness, solar_intensity, cloudiness)

Print #1, "<solar_radiation>"

If (solve_solar_0_true_1_false = 0) Then
Print #1, "<solve_solar>true</solve_solar>"
ElseIf (solve_solar_0_true_1_false = 1) Then
Print #1, "<solve_solar>false</solve_solar>"
End If

If (angle_measured_from_0_X_1_Y_2_Z = 0) Then
Print #1, "<angle_measured_from>x_axis</angle_measured_from>"
ElseIf (angle_measured_from_0_X_1_Y_2_Z = 1) Then
Print #1, "<angle_measured_from>y_axis</angle_measured_from>"
Else
Print #1, "<angle_measured_from>z_axis</angle_measured_from>"
End If

Print #1, "<angle>" + CStr(angle) + "</angle>"
Print #1, "<latitude>" + CStr(latitude) + "</latitude>"
Print #1, "<day>" + CStr(day) + "</day>"
Print #1, "<month>" + CStr(month) + "</month>"
Print #1, "<solar_time>" + CStr(solar_time) + "</solar_time>"

If (solar_type_0_intensity_1_cloudiness = 0) Then
Print #1, "<solar_type>solar_intensity</solar_type>"
Print #1, "<solar_intensity>" + CStr(solar_intensity) + "</solar_intensity>"

ElseIf (solar_type_0_intensity_1_cloudiness = 1) Then
Print #1, "<solar_type>cloudiness</solar_type>"
Print #1, "<cloudiness>" + CStr(cloudiness) + "</cloudiness>"

End If

Print #1, "</solar_radiation>"

End Sub
Sub turbulence_setup(type_0_laminar_1_turbulent, turbulence_model_0_revised_algebraic_1_auto_algebraic_2_lvel_kepsilon_3_lvel_algebraic_4_capped_lvel, revised_algebraic_velocity, revised_algebraic_length_scale, lvel_kepsilon_stratification_0_false_1_true, capped_lvel_multipler)
Print #1, "<turbulence>"

If (type_0_laminar_1_turbulent = 0) Then
Print #1, "<type>laminar</type>"
Else
Print #1, "<type>turbulent</type>"
End If

If (turbulence_model_0_revised_algebraic_1_auto_algebraic_2_lvel_kepsilon_3_lvel_algebraic_4_capped_lvel = 0) Then
Print #1, "<turbulence_type>revised_algebraic</turbulence_type>"
Print #1, "<revised_algebraic><velocity>" + CStr(revised_algebraic_velocity) + "</velocity><length>" + CStr(revised_algebraic_length_scale) + "</length></revised_algebraic>"
ElseIf (turbulence_model_0_revised_algebraic_1_auto_algebraic_2_lvel_kepsilon_3_lvel_algebraic_4_capped_lvel = 1) Then
Print #1, "<turbulence_type>auto_algebraic</turbulence_type>"
ElseIf (turbulence_model_0_revised_algebraic_1_auto_algebraic_2_lvel_kepsilon_3_lvel_algebraic_4_capped_lvel = 2) Then
Print #1, "<turbulence_type>lvel_k_epsilon</turbulence_type>"

If (lvel_kepsilon_stratification_0_false_1_true = 1) Then
Print #1, "<lvel_k_epsilon_stratification>true</lvel_k_epsilon_stratification>"
End If

ElseIf (turbulence_model_0_revised_algebraic_1_auto_algebraic_2_lvel_kepsilon_3_lvel_algebraic_4_capped_lvel = 3) Then
Print #1, "<turbulence_type>lvel_algebraic</turbulence_type>"
ElseIf (turbulence_model_0_revised_algebraic_1_auto_algebraic_2_lvel_kepsilon_3_lvel_algebraic_4_capped_lvel = 4) Then
Print #1, "<turbulence_type>capped_lvel</turbulence_type>"

Print #1, "<capped_lvel_multiplier>" + CStr(capped_lvel_multipler) + "</capped_lvel_multiplier>"

End If

Print #1, "</turbulence>"
End Sub
Sub gravity_setup(type_0_off_1_normal_2_angled, normal_direction_0_negative_x_1_positive_x_2_negative_y_3_positive_y_4_negative_z_5_positive_z, angled_direction_x, angled_direction_y, angled_direction_z, gravity_value)

Print #1, "<gravity>"

If (type_0_off_1_normal_2_angled = 0) Then
Print #1, "<type>off</type>"
ElseIf (type_0_off_1_normal_2_angled = 1) Then
Print #1, "<type>normal</type>"
If (normal_direction_0_negative_x_1_positive_x_2_negative_y_3_positive_y_4_negative_z_5_positive_z = 0) Then
Print #1, "<normal_direction>neg_x</normal_direction>"
ElseIf (normal_direction_0_negative_x_1_positive_x_2_negative_y_3_positive_y_4_negative_z_5_positive_z = 1) Then
Print #1, "<normal_direction>pos_x</normal_direction>"
ElseIf (normal_direction_0_negative_x_1_positive_x_2_negative_y_3_positive_y_4_negative_z_5_positive_z = 2) Then
Print #1, "<normal_direction>neg_y</normal_direction>"
ElseIf (normal_direction_0_negative_x_1_positive_x_2_negative_y_3_positive_y_4_negative_z_5_positive_z = 3) Then
Print #1, "<normal_direction>pos_y</normal_direction>"
ElseIf (normal_direction_0_negative_x_1_positive_x_2_negative_y_3_positive_y_4_negative_z_5_positive_z = 4) Then
Print #1, "<normal_direction>neg_z</normal_direction>"
ElseIf (normal_direction_0_negative_x_1_positive_x_2_negative_y_3_positive_y_4_negative_z_5_positive_z = 5) Then
Print #1, "<normal_direction>pos_z</normal_direction>"
End If
ElseIf (type_0_off_1_normal_2_angled = 2) Then
Print #1, "<type>angled</type>"
Print #1, "<angled_direction><x>" + CStr(angled_direction_x) + "</x><y>" + CStr(angled_direction_y) + "</y><z>" + CStr(angled_direction_z) + "</z></angled_direction>"
End If

Print #1, "<value_type>user</value_type>"
Print #1, "<gravity_value>" + CStr(gravity_value) + "</gravity_value>"

Print #1, "</gravity>"

End Sub
Sub global_setup(datum_pressure, radiant_temperature, ambient_temperature, radiant_temperature_transient_attribute, ambient_temperature_transient_attribute, ambient_concentration1, ambient_concentration2, ambient_concentration3, ambient_concentration4, ambient_concentration5)

Print #1, "<global>"
Print #1, "<datum_pressure>" + CStr(datum_pressure) + "</datum_pressure>"
Print #1, "<radiant_temperature>" + CStr(radiant_temperature) + "</radiant_temperature>"
Print #1, "<ambient_temperature>" + CStr(ambient_temperature) + "</ambient_temperature>"

If (radiant_temperature_transient_attribute <> "0") Then
Print #1, "<radiant_transient>" + CStr(radiant_temperature_transient_attribute) + "</radiant_transient>"
End If

If (ambient_temperature_transient_attribute <> "0") Then
Print #1, "<ambient_transient>" + CStr(ambient_temperature_transient_temperature) + "</ambient_transient>"
End If

Print #1, "<concentration_1>" + CStr(ambient_concentration1) + "</concentration_1>"
Print #1, "<concentration_2>" + CStr(ambient_concentration2) + "</concentration_2>"
Print #1, "<concentration_3>" + CStr(ambient_concentration3) + "</concentration_3>"
Print #1, "<concentration_4>" + CStr(ambient_concentration4) + "</concentration_4>"
Print #1, "<concentration_5>" + CStr(ambient_concentration5) + "</concentration_5>"

Print #1, "</global>"


End Sub
Sub start_initial_variables_setup(initial_solution_name, initial_solution_id, use_initial_for_all_0_true_1_false)

Print #1, "<initial_variables>"

If (initial_solution_name <> "0") Then
Print #1, "<initial_solution_name>" + CStr(initial_solution_name) + "</initial_solution_name>"
Print #1, "<initial_solution_id>" + CStr(initial_solution_id) + "</initial_solution_id>"
End If

If (use_initial_for_all_0_true_1_false = 0) Then
    Print #1, "<use_initial_for_all>true</use_initial_for_all>"
Else
    Print #1, "<use_initial_for_all>false</use_initial_for_all>"
End If

End Sub
Sub set_individual_initial_variables(variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density_14_potential, type_0_automatic_1_selected_solution_set_2_user_specified, user_specified_value)
    If (variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density_14_potential = 0) Then
        Print #1, "<pressure>"
            If (type_0_automatic_1_selected_solution_set_2_user_specified = 0) Then
                Print #1, "<type>automatic</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 1) Then
                Print #1, "<type>selected_solution</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 2) Then
                Print #1, "<type>user_specified</type>"
                Print #1, "<value>" + CStr(user_specified_value) + "</value>"
            End If
            Print #1, "</pressure>"
      ElseIf (variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density_14_potential = 1) Then
            Print #1, "<x_velocity>"
            If (type_0_automatic_1_selected_solution_set_2_user_specified = 0) Then
                Print #1, "<type>automatic</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 1) Then
                Print #1, "<type>selected_solution</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 2) Then
                Print #1, "<type>user_specified</type>"
                Print #1, "<value>" + CStr(user_specified_value) + "</value>"
            End If
            Print #1, "</x_velocity>"
    ElseIf (variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density_14_potential = 2) Then
            Print #1, "<y_velocity>"
            If (type_0_automatic_1_selected_solution_set_2_user_specified = 0) Then
                Print #1, "<type>automatic</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 1) Then
                Print #1, "<type>selected_solution</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 2) Then
                Print #1, "<type>user_specified</type>"
                Print #1, "<value>" + CStr(user_specified_value) + "</value>"
            End If
            Print #1, "</y_velocity>"
    ElseIf (variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density_14_potential = 3) Then
            Print #1, "<z_velocity>"
            If (type_0_automatic_1_selected_solution_set_2_user_specified = 0) Then
                Print #1, "<type>automatic</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 1) Then
                Print #1, "<type>selected_solution</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 2) Then
                Print #1, "<type>user_specified</type>"
                Print #1, "<value>" + CStr(user_specified_value) + "</value>"
            End If
            Print #1, "</z_velocity>"
    ElseIf (variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density_14_potential = 4) Then
            Print #1, "<temperature>"
            If (type_0_automatic_1_selected_solution_set_2_user_specified = 0) Then
                Print #1, "<type>automatic</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 1) Then
                Print #1, "<type>selected_solution</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 2) Then
                Print #1, "<type>user_specified</type>"
                Print #1, "<value>" + CStr(user_specified_value) + "</value>"
            End If
            Print #1, "</temperature>"
    ElseIf (variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density_14_potential = 5) Then
            Print #1, "<ke_turb>"
            If (type_0_automatic_1_selected_solution_set_2_user_specified = 0) Then
                Print #1, "<type>automatic</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 1) Then
                Print #1, "<type>selected_solution</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 2) Then
                Print #1, "<type>user_specified</type>"
                Print #1, "<value>" + CStr(user_specified_value) + "</value>"
            End If
            Print #1, "</ke_turb>"
    ElseIf (variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density_14_potential = 6) Then
            Print #1, "<diss_turb>"
            If (type_0_automatic_1_selected_solution_set_2_user_specified = 0) Then
                Print #1, "<type>automatic</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 1) Then
                Print #1, "<type>selected_solution</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 2) Then
                Print #1, "<type>user_specified</type>"
                Print #1, "<value>" + CStr(user_specified_value) + "</value>"
            End If
            Print #1, "</diss_turb>"
    ElseIf (variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density_14_potential = 7) Then
            Print #1, "<turb_vis>"
            If (type_0_automatic_1_selected_solution_set_2_user_specified = 0) Then
                Print #1, "<type>automatic</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 1) Then
                Print #1, "<type>selected_solution</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 2) Then
                Print #1, "<type>user_specified</type>"
                Print #1, "<value>" + CStr(user_specified_value) + "</value>"
            End If
            Print #1, "</turb_vis>"
    ElseIf (variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density_14_potential = 8) Then
            Print #1, "<concentration_1>"
            If (type_0_automatic_1_selected_solution_set_2_user_specified = 0) Then
                Print #1, "<type>automatic</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 1) Then
                Print #1, "<type>selected_solution</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 2) Then
                Print #1, "<type>user_specified</type>"
                Print #1, "<value>" + CStr(user_specified_value) + "</value>"
            End If
            Print #1, "</concentration_1>"
    ElseIf (variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density_14_potential = 9) Then
            Print #1, "<concentration_2>"
            If (type_0_automatic_1_selected_solution_set_2_user_specified = 0) Then
                Print #1, "<type>automatic</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 1) Then
                Print #1, "<type>selected_solution</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 2) Then
                Print #1, "<type>user_specified</type>"
                Print #1, "<value>" + CStr(user_specified_value) + "</value>"
            End If
            Print #1, "</concentration_2>"
            
    ElseIf (variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density_14_potential = 10) Then
            Print #1, "<concentration_3>"
            If (type_0_automatic_1_selected_solution_set_2_user_specified = 0) Then
                Print #1, "<type>automatic</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 1) Then
                Print #1, "<type>selected_solution</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 2) Then
                Print #1, "<type>user_specified</type>"
                Print #1, "<value>" + CStr(user_specified_value) + "</value>"
            End If
            Print #1, "</concentration_3>"
    ElseIf (variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density_14_potential = 11) Then
            Print #1, "<concentration_4>"
            If (type_0_automatic_1_selected_solution_set_2_user_specified = 0) Then
                Print #1, "<type>automatic</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 1) Then
                Print #1, "<type>selected_solution</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 2) Then
                Print #1, "<type>user_specified</type>"
                Print #1, "<value>" + CStr(user_specified_value) + "</value>"
            End If
             Print #1, "</concentration_4>"
    ElseIf (variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density_14_potential = 12) Then
            Print #1, "<concentration_5>"
            If (type_0_automatic_1_selected_solution_set_2_user_specified = 0) Then
                Print #1, "<type>automatic</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 1) Then
                Print #1, "<type>selected_solution</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 2) Then
                Print #1, "<type>user_specified</type>"
                Print #1, "<value>" + CStr(user_specified_value) + "</value>"
            End If
            Print #1, "</concentration_5>"
    ElseIf (variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density_14_potential = 13) Then
            Print #1, "<density>"
            If (type_0_automatic_1_selected_solution_set_2_user_specified = 0) Then
                Print #1, "<type>automatic</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 1) Then
                Print #1, "<type>selected_solution</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 2) Then
                Print #1, "<type>user_specified</type>"
                Print #1, "<value>" + CStr(user_specified_value) + "</value>"
            End If
        Print #1, "</density>"
        ElseIf (variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density_14_potential = 14) Then
            Print #1, "<potential>"
            If (type_0_automatic_1_selected_solution_set_2_user_specified = 0) Then
                Print #1, "<type>automatic</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 1) Then
                Print #1, "<type>selected_solution</type>"
            ElseIf (type_0_automatic_1_selected_solution_set_2_user_specified = 2) Then
                Print #1, "<type>user_specified</type>"
                Print #1, "<value>" + CStr(user_specified_value) + "</value>"
            End If
        Print #1, "</potential>"
    End If
        
End Sub
Sub end_initial_variables_setup()
    Print #1, "</initial_variables>"
End Sub
Sub start_transient_setup(start_time, end_time, duration, keypoint_tolerance, save_time_string)
Dim points() As String
Dim k As Integer

Print #1, "<transient>"
Print #1, "<overall_transient>"
Print #1, "<start_time>" + CStr(start_time) + "</start_time>"
Print #1, "<end_time>" + CStr(end_time) + "</end_time>"
Print #1, "<duration>" + CStr(duration) + "</duration>"
Print #1, "<keypoint_tolerance>" + CStr(keypoint_tolerance) + "</keypoint_tolerance>"
Print #1, "</overall_transient>"

Print #1, "<transient_save_times>"

points() = Split(save_time_string, ",")

For k = 0 To UBound(points) Step 1
Print #1, "<save_time>" + points(k) + "</save_time>"
Next k
Print #1, "</transient_save_times>"

Print #1, "<time_patches>"
End Sub
Sub create_time_grid_patch(name, start_time, end_time, step_control_0_minimum_number_1_maximum_size, minimum_number_or_maximum_size, step_distribution_0_uniform_1_increasing_power_2_decreasing_power_3_symmetrical, distribution_index)

Print #1, "<time_patch>"
Print #1, "<name>" + CStr(name) + "</name>"
Print #1, "<start_time>" + CStr(start_time) + "</start_time>"
Print #1, "<end_time>" + CStr(end_time) + "</end_time>"

If (step_control_0_minimum_number_1_maximum_size = 0) Then
Print #1, "<step_control>minimum_number</step_control>"
Print #1, "<minimum_number>" + CStr(minimum_number_or_maximum_size) + "</minimum_number>"
Else
Print #1, "<step_control>maximum_size</step_control>"
Print #1, "<maximum_size>" + CStr(minimum_number_or_maximum_size) + "</maximum_size>"
End If

If (step_distribution_0_uniform_1_increasing_power_2_decreasing_power_3_symmetrical = 0) Then
Print #1, "<step_distribution>uniform</step_distribution>"
ElseIf (step_distribution_0_uniform_1_increasing_power_2_decreasing_power_3_symmetrical = 1) Then
Print #1, "<step_distribution>increasing_power</step_distribution>"
ElseIf (step_distribution_0_uniform_1_increasing_power_2_decreasing_power_3_symmetrical = 2) Then
Print #1, "<step_distribution>decreasing_power</step_distribution>"
Else
Print #1, "<step_distribution>symmetrical_power</step_distribution>"
End If

Print #1, "<distribution_index>" + CStr(distribution_index) + "</distribution_index>"
Print #1, "</time_patch>"

End Sub
Sub end_transient_setup()
Print #1, "</time_patches>"
Print #1, "</transient>"
End Sub
Sub start_solver_inputs()
Print #1, "<solve>"
End Sub
Sub end_solver_inputs()
Print #1, "</solve>"
End Sub
Sub overall_control_setup(number_of_outer_iterations, use_monitor_point_convergence_for_temperature_0_false_1_true, monitor_point_convergence_required_accuracy, monitor_point_convergence_num_iterations, monitor_point_convergence_residual_threshold, use_multigrid_damping_0_false_1_true, solver_option_0_multi_grid_1_segregated_conjugate_residual, fan_relaxation, active_plate_conduction_0_false_1_true, use_double_precision_0_false_1_true, network_assembly_block_correction_0_false_1_true, freeze_flow_0_false_1_true, store_error_field_0_false_1_true, error_field_variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density, estimated_free_convection_velocity, use_transient_monitor_point_termination_0_false_1_true, string_with_MP_transient_termination_criteria)
Dim points() As String
Dim k As Integer

'use_transient_monitor_point_termination_0_false_1_true,string_with_MP_transient_termination_criteria
'string_with_MP_transient_termination_criteria contains CSV name, stopping temperature points


Print #1, "<overall_control>"
Print #1, "<outer_iterations>" + CStr(number_of_outer_iterations) + "</outer_iterations>"

Print #1, "<fan_relaxation>" + CStr(fan_relaxation) + "</fan_relaxation>"
Print #1, "<estimated_free_convection_velocity>" + CStr(estimated_free_convection_velocity) + "</estimated_free_convection_velocity>"

If (use_monitor_point_convergence_for_temperature_0_false_1_true = 1) Then
Print #1, "<monitor_convergence>true</monitor_convergence>"
Print #1, "<convergence_values>"
Print #1, "<required_accuracy>" + CStr(monitor_point_convergence_required_accuracy) + "</required_accuracy>"
Print #1, "<num_iterations>" + CStr(monitor_point_convergence_num_iterations) + "</num_iterations>"
Print #1, "<residual_threshold>" + CStr(monitor_point_convergence_residual_threshold) + "</residual_threshold>"
Print #1, "</convergence_values>"
End If

If (use_multigrid_damping_0_false_1_true = 1) Then
Print #1, "<multi_grid_damping>true</multi_grid_damping>"
End If

If (solver_option_0_multi_grid_1_segregated_conjugate_residual = 0) Then
Print #1, "<solver_option>multi_grid</solver_option>"
ElseIf (solver_option_0_multi_grid_1_segregated_conjugate_residual = 1) Then
Print #1, "<solver_option>segregated_conjugate_residual</solver_option>"
End If

If (active_plate_conduction_0_false_1_true = 0) Then
Print #1, "<active_plate_conduction>false</active_plate_conduction>"
ElseIf (active_plate_conduction_0_false_1_true = 1) Then
Print #1, "<active_plate_conduction>true</active_plate_conduction>"
End If

If (use_double_precision_0_false_1_true = 0) Then
Print #1, "<use_double_precision>false</use_double_precision>"
ElseIf (use_double_precision_0_false_1_true = 1) Then
Print #1, "<use_double_precision>true</use_double_precision>"
End If

If (network_assembly_block_correction_0_false_1_true = 0) Then
Print #1, "<network_assembly_block_correction>false</network_assembly_block_correction>"
ElseIf (network_assembly_block_correction_0_false_1_true = 1) Then
Print #1, "<network_assembly_block_correction>true</network_assembly_block_correction>"
End If

If (freeze_flow_0_false_1_true = 0) Then
Print #1, "<freeze_flow>false</freeze_flow>"
ElseIf (freeze_flow_0_false_1_true = 1) Then
Print #1, "<freeze_flow>true</freeze_flow>"
End If

If (use_transient_monitor_point_termination_0_false_1_true = 0) Then

ElseIf (use_transient_monitor_point_termination_0_false_1_true = 1) Then

Print #1, "<monitor_point_transient_termination_criteria>"
Print #1, "<use_monitor_point_transient_termination_criteria>true</use_monitor_point_transient_termination_criteria>"

Print #1, "<terminating_monitor_points>"
points() = Split(string_with_MP_transient_termination_criteria, ",")

For k = 0 To UBound(points) Step 2
Print #1, "<terminating_monitor_point>"
Print #1, "<monitor_point>" + points(k) + "</monitor_point><temperature>" + points(k + 1) + "</temperature>"
Print #1, "</terminating_monitor_point>"

Next k

Print #1, "</terminating_monitor_points>"
Print #1, "</monitor_point_transient_termination_criteria>"
End If

If (store_error_field_0_false_1_true = 0) Then
Print #1, "<store_error_field>false</store_error_field>"
ElseIf (store_error_field_0_false_1_true = 1) Then
Print #1, "<store_error_field>true</store_error_field>"
    Select Case error_field_variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_turbvis_8_concentration1_9_concentration2_10_concentration3_11_concentration4_12_concentration5_13_density
        Case 0
            Print #1, "<error_field_variable>pressure</error_field_variable>"
        Case 1
            Print #1, "<error_field_variable>x_velocity</error_field_variable>"
        Case 2
            Print #1, "<error_field_variable>y_velocity</error_field_variable>"
        Case 3
            Print #1, "<error_field_variable>z_velocity</error_field_variable>"
        Case 4
            Print #1, "<error_field_variable>temperature</error_field_variable>"
        Case 5
            Print #1, "<error_field_variable>ke_turb</error_field_variable>"
        Case 6
            Print #1, "<error_field_variable>diss_turb</error_field_variable>"
        Case 7
            Print #1, "<error_field_variable>turb_vis</error_field_variable>"
        Case 8
            Print #1, "<error_field_variable>concentration_1</error_field_variable>"
        Case 9
            Print #1, "<error_field_variable>concentration_2</error_field_variable>"
        Case 10
            Print #1, "<error_field_variable>concentration_3</error_field_variable>"
        Case 11
            Print #1, "<error_field_variable>concentration_4</error_field_variable>"
        Case 12
            Print #1, "<error_field_variable>concentration_5</error_field_variable>"
        Case 13
            Print #1, "<error_field_variable>density</error_field_variable>"
    End Select
End If

Print #1, "</overall_control>"

End Sub
Sub start_solver_controls()
Print #1, "<solver_controls>"
End Sub
Sub end_solver_controls()
Print #1, "</solver_controls>"
End Sub
Sub solver_control(variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_concentration1_8_concentration2_9_concentration3_10_concentration4_11_concentration5_12_density_13_turb_vis_14_generation, linear_relaxation, error_compute_frequency)

Print #1, "<solver_control>"

Select Case variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_concentration1_8_concentration2_9_concentration3_10_concentration4_11_concentration5_12_density_13_turb_vis_14_generation
    Case 0
        Print #1, "<variable>pressure</variable>"
    Case 1
        Print #1, "<variable>x_velocity</variable>"
    Case 2
        Print #1, "<variable>y_velocity</variable>"
    Case 3
        Print #1, "<variable>z_velocity</variable>"
    Case 4
        Print #1, "<variable>temperature</variable>"
    Case 5
        Print #1, "<variable>ke_turb</variable>"
    Case 6
        Print #1, "<variable>diss_turb</variable>"
    Case 7
        Print #1, "<variable>concentration_1</variable>"
    Case 8
        Print #1, "<variable>concentration_2</variable>"
    Case 9
        Print #1, "<variable>concentration_3</variable>"
    Case 10
        Print #1, "<variable>concentration_4</variable>"
    Case 11
        Print #1, "<variable>concentration_5</variable>"
    Case 12
        Print #1, "<variable>density</variable>"
    Case 13
        Print #1, "<variable>turb_vis</variable>"
    Case 14
        Print #1, "<variable>generation</variable>"
End Select

Print #1, "<linear_relaxation>" + CStr(linear_relaxation) + "</linear_relaxation>"
Print #1, "<error_compute_frequency>" + CStr(error_compute_frequency) + "</error_compute_frequency>"

Print #1, "</solver_control>"

End Sub
Sub start_variable_controls()
Print #1, "<variable_controls>"
End Sub
Sub end_variable_controls()
Print #1, "</variable_controls>"
End Sub
Sub variable_control(variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_concentration1_8_concentration2_9_concentration3_10_concentration4_11_concentration5_12_potential, false_time_step_type_0_automatic_1_user_defined, false_time_step_multiplier, false_time_step_user_value, termination_residual_type_0_automatic_1_user_defined, termination_residual_multiplier, termination_residual_user_value, inner_iterations)

Print #1, "<variable_control>"

Select Case variable_0_pressure_1_xvelocity_2_yvelocity_3_zvelocity_4_temperature_5_keturb_6_dissturb_7_concentration1_8_concentration2_9_concentration3_10_concentration4_11_concentration5_12_potential
    Case 0
        Print #1, "<variable>pressure</variable>"
    Case 1
        Print #1, "<variable>x_velocity</variable>"
    Case 2
        Print #1, "<variable>y_velocity</variable>"
    Case 3
        Print #1, "<variable>z_velocity</variable>"
    Case 4
        Print #1, "<variable>temperature</variable>"
    Case 5
        Print #1, "<variable>ke_turb</variable>"
    Case 6
        Print #1, "<variable>diss_turb</variable>"
    Case 7
        Print #1, "<variable>concentration_1</variable>"
    Case 8
        Print #1, "<variable>concentration_2</variable>"
    Case 9
        Print #1, "<variable>concentration_3</variable>"
    Case 10
        Print #1, "<variable>concentration_4</variable>"
    Case 11
        Print #1, "<variable>concentration_5</variable>"
    Case 12
        Print #1, "<variable>potential</variable>"
End Select

Select Case false_time_step_type_0_automatic_1_user_defined
    Case 0
        Print #1, "<false_time_step>automatic</false_time_step>"
        Print #1, "<false_time_step_damping_auto_multiplier>" + CStr(false_time_step_multiplier) + "</false_time_step_damping_auto_multiplier>"
    Case 1
        Print #1, "<false_time_step>user</false_time_step>"
        Print #1, "<false_time_step_user_value>" + CStr(false_time_step_user_value) + "</false_time_step_user_value>"
End Select

Select Case termination_residual_type_0_automatic_1_user_defined
    Case 0
        Print #1, "<terminal_residual>automatic</terminal_residual>"
        Print #1, "<terminal_residual_auto_multiplier>" + CStr(termination_residual_multiplier) + "</terminal_residual_auto_multiplier>"
    Case 1
        Print #1, "<terminal_residual>user</terminal_residual>"
        Print #1, "<terminal_residual_user_value>" + CStr(termination_residual_user_value) + "</terminal_residual_user_value>"
End Select

Print #1, "<inner_iterations>" + CStr(inner_iterations) + "</inner_iterations>"

Print #1, "</variable_control>"

End Sub
Sub start_grid_inputs()
Print #1, "<grid>"
End Sub
Sub end_grid_inputs()
Print #1, "</grid>"
End Sub
Sub system_grid_setup(x_minimum_size, x_grid_type_0_minimum_number_1_maximum_size, x_min_number_or_max_size, y_minimum_size, y_grid_type_0_minimum_number_1_maximum_size, y_min_number_or_max_size, z_minimum_size, z_grid_type_0_minimum_number_1_maximum_size, z_min_number_or_max_size, use_smoothing_0_false_1_true, x_smoothing_between_0_and_50, y_smoothing_between_0_and_50, z_smoothing_between_0_and_50, smoothing_type_0_v3_1_v2, dynamic_update_0_true_1_false)

Print #1, "<system_grid>"

If (use_smoothing_0_false_1_true = 0) Then
Print #1, "<smoothing>false</smoothing>"
ElseIf (use_smoothing_0_false_1_true = 1) Then
Print #1, "<smoothing>true</smoothing>"
End If

If (smoothing_type_0_v3_1_v2 = 0) Then
Print #1, "<smoothing_type>v3</smoothing_type>"
ElseIf (smoothing_type_0_v3_1_v2 = 1) Then
Print #1, "<smoothing_type>v2</smoothing_type>"
End If

If (dynamic_update_0_true_1_false = 0) Then
Print #1, "<dynamic_update>true</dynamic_update>"
ElseIf (dynamic_update_0_true_1_false = 1) Then
Print #1, "<dynamic_update>false</dynamic_update>"
End If

Print #1, "<x_grid>"
Print #1, "<min_size>" + CStr(x_minimum_size) + "</min_size>"
If (x_grid_type_0_minimum_number_1_maximum_size = 0) Then
Print #1, "<grid_type>min_number</grid_type>"
Print #1, "<min_number>" + CStr(x_min_number_or_max_size) + "</min_number>"
ElseIf (x_grid_type_0_minimum_number_1_maximum_size = 1) Then
Print #1, "<grid_type>max_size</grid_type>"
Print #1, "<max_size>" + CStr(x_min_number_or_max_size) + "</max_size>"
End If
If (use_smoothing_0_false_1_true = 1) Then
Print #1, "<smoothing_value>" + CStr(x_smoothing_between_0_and_50) + "</smoothing_value>"
End If
Print #1, "</x_grid>"

Print #1, "<y_grid>"
Print #1, "<min_size>" + CStr(y_minimum_size) + "</min_size>"
If (y_grid_type_0_minimum_number_1_maximum_size = 0) Then
Print #1, "<grid_type>min_number</grid_type>"
Print #1, "<min_number>" + CStr(y_min_number_or_max_size) + "</min_number>"
ElseIf (y_grid_type_0_minimum_number_1_maximum_size = 1) Then
Print #1, "<grid_type>max_size</grid_type>"
Print #1, "<max_size>" + CStr(y_min_number_or_max_size) + "</max_size>"
End If
If (use_smoothing_0_false_1_true = 1) Then
Print #1, "<smoothing_value>" + CStr(y_smoothing_between_0_and_50) + "</smoothing_value>"
End If
Print #1, "</y_grid>"

Print #1, "<z_grid>"
Print #1, "<min_size>" + CStr(z_minimum_size) + "</min_size>"
If (z_grid_type_0_minimum_number_1_maximum_size = 0) Then
Print #1, "<grid_type>min_number</grid_type>"
Print #1, "<min_number>" + CStr(z_min_number_or_max_size) + "</min_number>"
ElseIf (z_grid_type_0_minimum_number_1_maximum_size = 1) Then
Print #1, "<grid_type>max_size</grid_type>"
Print #1, "<max_size>" + CStr(z_min_number_or_max_size) + "</max_size>"
End If
If (use_smoothing_0_false_1_true = 1) Then
Print #1, "<smoothing_value>" + CStr(z_smoothing_between_0_and_50) + "</smoothing_value>"
End If
Print #1, "</z_grid>"

Print #1, "</system_grid>"

End Sub
Sub start_grid_patches()
Print #1, "<patches>"

End Sub
Sub end_grid_patches()

Print #1, "</patches>"

End Sub
Sub grid_patch(name, direction_0_X_1_Y_2_Z, start_location, end_location, step_control_0_minimum_number_1_maximum_size, minimum_number_or_maximum_size, step_distribution_0_uniform_1_increasing_power_2_decreasing_power_3_symmetrical, distribution_index)

Print #1, "<grid_patch>"
Print #1, "<name>" + CStr(name) + "</name>"

Select Case direction_0_X_1_Y_2_Z
    Case 0
        Print #1, "<applies_to>x_direction</applies_to>"
    Case 1
        Print #1, "<applies_to>y_direction</applies_to>"
    Case 2
        Print #1, "<applies_to>z_direction</applies_to>"
End Select


Print #1, "<start_location>" + CStr(start_location) + "</start_location>"
Print #1, "<end_location>" + CStr(end_location) + "</end_location>"

If (step_control_0_minimum_number_1_maximum_size = 0) Then
Print #1, "<number_of_cells_control>min_number</number_of_cells_control>"
Print #1, "<min_number>" + CStr(minimum_number_or_maximum_size) + "</min_number>"
Else
Print #1, "<number_of_cells_control>max_size</number_of_cells_control>"
Print #1, "<max_size>" + CStr(minimum_number_or_maximum_size) + "</max_size>"
End If

If (step_distribution_0_uniform_1_increasing_power_2_decreasing_power_3_symmetrical = 0) Then
Print #1, "<cell_distribution>uniform</cell_distribution>"
ElseIf (step_distribution_0_uniform_1_increasing_power_2_decreasing_power_3_symmetrical = 1) Then
Print #1, "<cell_distribution>increasing</cell_distribution>"
ElseIf (step_distribution_0_uniform_1_increasing_power_2_decreasing_power_3_symmetrical = 2) Then
Print #1, "<cell_distribution>decreasing</cell_distribution>"
Else
Print #1, "<cell_distribution>symmetrical</cell_distribution>"
End If

Print #1, "<cell_distribution_index>" + CStr(distribution_index) + "</cell_distribution_index>"
Print #1, "</grid_patch>"

End Sub

