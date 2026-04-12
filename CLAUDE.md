# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FloTHERM automation tools for batch simulation, parameter modification, and FloXML generation. Compatible with FloTHERM 2020.2 and Simcenter Flotherm 2504.

## Common Commands

### Batch ECXML Solving
```bash
# Single file
flotherm -b model.ecxml -z output.pack -r report.html

# Batch solve folder
python batch_ecxml_solver.py ./input_folder -o ./output_folder

# Dry-run to preview
python batch_ecxml_solver.py ./input -o ./output --dry-run
```

### Excel Batch Simulation
```bash
python excel_batch_simulation.py template.ecxml config.xlsx -o ./output
python excel_batch_simulation.py template.pdml config.xlsx -o ./output --no-solve
python excel_batch_simulation.py template.ecxml config.xlsx -o ./output --sheet "配置1"
```

### ECXML/FloXML Operations
```bash
# ECXML analysis and modification
python ecxml_editor.py model.ecxml --analyze
python ecxml_editor.py model.ecxml --set-power U1_CPU 15.0 -o modified.ecxml
python ecxml_editor.py model.ecxml --power-config power_config.json -o modified.ecxml

# ECXML to FloXML conversion
python -m floxml_tools.ecxml_to_floxml_converter input.ecxml -o output.xml
python -m floxml_tools.ecxml_to_floxml_converter input.ecxml -o output.xml --padding-ratio 0.15

# ECXML to FloXML with grid from PDML (binary #FFFB or FloXML)
python -m floxml_tools.ecxml_to_floxml_converter input.ecxml -o output.xml --pdml project.pdml
python -m floxml_tools.ecxml_to_floxml_converter input.ecxml -o output.xml --pdml project.floxml

# Wrap geometry FloXML as project FloXML
python -m floxml_tools.wrap_geometry_floxml_as_project geometry.xml -o project.xml
```

### Pack File Operations
```bash
python pack_editor.py model.pack --list
python pack_editor.py model.pack --extract ./extracted
python pack_editor.py model.pack --set-power U1_CPU 15.0 -o modified.pack
```

### FloXML Generation (Excel-based)
```bash
python excel_floxml_generator.py materials --data materials.json -o output.xml
```

### FloXML Generation (Python Builder)
```bash
# Generate example model
python -m floxml_tools.floxml_builder --example -o output.xml
```

```python
from floxml_tools.floxml_builder import FloXMLBuilder

b = FloXMLBuilder("My Model")
with b.model_section():
    b.modeling_setup(solution="flow_heat", radiation="on")
    b.gravity_setup(gravity_type="normal", direction="neg_z", value=9.81)
    b.global_setup(ambient_temperature=300)
with b.solve_section():
    b.overall_control(outer_iterations=500)
with b.grid_section():
    b.system_grid(x_min_size=0.001, x_control=("max_size", 0.01))
with b.attributes_section():
    with b.materials_section():
        b.create_material("Aluminum", k=160, rho=2300, cp=455)
    with b.ambients_section():
        b.create_ambient("Ambient", temperature=300)
with b.geometry_section():
    b.build_cuboid("Block", size=(1, 2, 3), material="Aluminum")
b.build_solution_domain(size=(5, 5, 5), ambient="Ambient", fluid="Air")
b.write("output.xml")
```

## File Formats

| Format | Description | Parser |
|--------|-------------|--------|
| `.ecxml` | JEDEC JEP181 device thermal model (component-level) | `ECXMLParser` |
| `.pdml` | FloTHERM native project format (full model) | `PDMLParser` |
| `.floxml` / `.xml` | FloTHERM XML format (project or assembly) | `PDMLParser` |
| `.pack` | FloTHERM compressed project archive | `pack_editor.py` |

### FloXML Types
- **Assembly FloXML**: Contains only `<attributes>` + `<geometry>` - for import as subassembly
- **Project FloXML**: Full project with `<model>`, `<solve>`, `<grid>`, `<solution_domain>` - for direct opening

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Input Files                               │
│  .ecxml (JEDEC)  │  .pdml (Native)  │  .pack  │  Excel (.xlsx)  │
└────────┬─────────┴────────┬──────────┴────┬───┴───────┬─────────┘
         │                  │               │           │
         ▼                  ▼               ▼           ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────────┐
│ ECXMLParser     │ │ PDMLParser   │ │PackEditor│ │ExcelConfig   │
│ ecxml_editor.py │ │ pdml_parser  │ │          │ │Reader        │
└────────┬────────┘ └──────┬───────┘ └────┬─────┘ └──────┬───────┘
         │                 │              │              │
         └────────────────┬┴──────────────┴──────────────┘
                          ▼
         ┌────────────────────────────────────────────┐
         │              Processing Layer               │
         ├────────────────────────────────────────────┤
         │ excel_batch_simulation.py  (multi-config)  │
         │ floxml_tools/              (format conv)   │
         │ batch_ecxml_solver.py      (batch solve)   │
         │ excel_floxml_generator.py  (FloXML gen)    │
         └────────────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────────────────┐
         │              Output Files                   │
         │  .ecxml │ .floxml │ .pack │ reports        │
         └────────────────────────────────────────────┘
```

## Key Modules

| File | Purpose |
|------|---------|
| `ecxml_editor.py` | Parse/modify ECXML (JEDEC JEP181) - components, powers, materials |
| `pdml_tools/pdml_parser.py` | Parse PDML/FloXML - full model with grid, solve, geometry |
| `pack_editor.py` | Extract/modify .pack archives (ZIP format) |
| `floxml_tools/ecxml_to_floxml_converter.py` | Convert ECXML to complete FloXML project; `--pdml` injects grid from PDML/FloXML |
| `pdml_tools/pdml_to_floxml_converter.py` | Parse binary PDML (#FFFB) and convert to FloXML |
| `floxml_tools/floxml_add_volume_regions.py` | Inject volume regions and grid constraints into FloXML |
| `floxml_tools/floxml_grid_parser.py` | Parse grid settings from FloXML |
| `floxml_tools/grid_config.py` | Grid configuration from Excel (system_grid, patches, constraints) |
| `floxml_tools/wrap_geometry_floxml_as_project.py` | Wrap Assembly FloXML as Project FloXML |
| `floxml_tools/floxml_builder.py` | **FloXML 项目生成器** — 用 Python 程序化构建完整 FloXML（VBA Class_XML_Subs_FCv11 的 Python 版） |
| `excel_batch_simulation.py` | Multi-config batch simulation from Excel |
| `batch_ecxml_solver.py` | Batch solve ECXML files using `flotherm -z` |
| `excel_floxml_generator.py` | Generate FloXML via Excel COM automation |

## FloTHERM 2020.2 Automation Capabilities

| Method | Status | Notes |
|--------|--------|-------|
| `-z` batch parameter | Works | `flotherm -b model.ecxml -z output.pack` |
| FloSCRIPT macros | Partial | Requires GUI, manual click to run |
| COM API | Not available | 2020.2 doesn't support |
| Python API | Not available | 2020.2 doesn't support |

## Excel Config Format

Simple format for batch simulation:

| config_name | U1_CPU | U2_GPU | Ambient |
|-------------|--------|--------|---------|
| case1       | 10     | 5      | 25      |
| case2       | 15     | 8      | 35      |

- First column must be `config_name`
- Other columns match component names or boundary condition names
- Numeric values auto-detected: power (W) or temperature (°C)

## Schema and Examples

```
examples/
├── FloXML/
│   ├── FloXML Files/
│   │   ├── Project FloXML Examples/    # Full project examples
│   │   └── Assembly FloXML Examples/   # Subassembly examples
│   └── Spreadsheets/                   # Excel templates (.xlsm)
├── FloSCRIPT/
│   └── Schema/                         # FloSCRIPT XSD schemas
├── DCIM Development Toolkit/
│   └── Schema Files/FloXML/            # FloXML XSD schemas
```

## Dependencies

```bash
pip install openpyxl pandas
```

## Notes

- FloXML is import-only format; FloTHERM cannot export FloXML directly
- `solution_domain` must be at root level, not inside `<geometry>`
- Assembly FloXML needs wrapping to become a standalone project
- Excel templates use VBA macros - macro names are auto-detected from `.xlsm` internals
- FloXMLBuilder 生成的 XML 已通过 Simcenter Flotherm 2504 验证可正常导入
- FloTHERM Schema 要求 `<modeling>` 包含 store_options，`<global>` 包含 concentration_1-5，`<solve>` 用 `outer_iterations`（非 `max_iterations`）
