#!/usr/bin/env python3
"""Generate work handover PPT for floxml_tools module."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

# ── Color palette ──
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x00, 0x00, 0x00)
DARK_BLUE = RGBColor(0x1B, 0x3A, 0x5C)
ACCENT_BLUE = RGBColor(0x2E, 0x75, 0xB6)
LIGHT_BLUE = RGBColor(0xD6, 0xE4, 0xF0)
MID_BLUE = RGBColor(0x5B, 0x9B, 0xD5)
DARK_GRAY = RGBColor(0x33, 0x33, 0x33)
MED_GRAY = RGBColor(0x66, 0x66, 0x66)
LIGHT_GRAY = RGBColor(0xF2, 0xF2, 0xF2)
ORANGE = RGBColor(0xED, 0x7D, 0x31)
GREEN = RGBColor(0x70, 0xAD, 0x47)

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)


def set_slide_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_shape(slide, left, top, width, height, fill_color=None, border_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.line.fill.background()
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1)
    return shape


def add_text_box(slide, left, top, width, height, text, font_size=18,
                 color=DARK_GRAY, bold=False, alignment=PP_ALIGN.LEFT,
                 font_name="Microsoft YaHei"):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    return txBox


def add_bullet_list(slide, left, top, width, height, items, font_size=14,
                    color=DARK_GRAY, spacing=Pt(6), bold_items=None):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = item
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.font.name = "Microsoft YaHei"
        p.space_after = spacing
        p.level = 0
        if bold_items and i in bold_items:
            p.font.bold = True
    return txBox


def add_footer(slide, text="floxml_tools 工作交接"):
    add_text_box(slide, Inches(0.5), Inches(7.0), Inches(12), Inches(0.4),
                 text, font_size=9, color=MED_GRAY, alignment=PP_ALIGN.LEFT)


def make_title_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    set_slide_bg(slide, WHITE)

    # Top accent bar
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.08), ACCENT_BLUE)

    # Center block
    add_shape(slide, Inches(1.5), Inches(1.8), Inches(10.3), Inches(3.6), LIGHT_BLUE)

    add_text_box(slide, Inches(2), Inches(2.0), Inches(9.3), Inches(1.2),
                 "floxml_tools", font_size=48, color=DARK_BLUE, bold=True)
    add_text_box(slide, Inches(2), Inches(3.0), Inches(9.3), Inches(0.8),
                 "FloTHERM FloXML 自动化工具集", font_size=28, color=ACCENT_BLUE)
    add_text_box(slide, Inches(2), Inches(3.8), Inches(9.3), Inches(0.6),
                 "工作交接文档", font_size=22, color=MED_GRAY)

    add_text_box(slide, Inches(2), Inches(5.5), Inches(9.3), Inches(0.4),
                 "日期: 2026-06-01", font_size=14, color=MED_GRAY)
    add_text_box(slide, Inches(2), Inches(5.9), Inches(9.3), Inches(0.4),
                 "代码规模: 16 个 Python 模块 / 约 10,800 行代码", font_size=14, color=MED_GRAY)


def make_overview_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.08), ACCENT_BLUE)

    add_text_box(slide, Inches(0.6), Inches(0.3), Inches(12), Inches(0.7),
                 "模块总览", font_size=32, color=DARK_BLUE, bold=True)

    add_text_box(slide, Inches(0.6), Inches(1.1), Inches(12), Inches(0.5),
                 "floxml_tools 是一套完整的 FloTHERM FloXML 项目自动化工具，覆盖从模型创建到求解配置的全流程。",
                 font_size=16, color=MED_GRAY)

    # 4 category boxes
    categories = [
        ("模型构建", "floxml_builder.py\nfloxml_boundary_conditions.py\nfloxml_nonlinear_source.py",
         "程序化构建完整的\nFloXML 项目文件", ACCENT_BLUE),
        ("格式转换", "ecxml_to_floxml_converter.py\nwrap_geometry_floxml_as_project.py",
         "ECXML → FloXML\n几何 → 完整项目", MID_BLUE),
        ("配置注入", "config_injector.py\nfloxml_add_volume_regions.py\nfloxml_add_solve_settings.py\n"
         "grid_config.py\nfloxml_grid_parser.py",
         "网格/区域/求解/边界\nJSON 配置注入", GREEN),
        ("流程编排", "floxml_pipeline.py\ninject_grid_from_floxml.py\ninject_config.py\n"
         "floxml_inject_grid.py\nfloxml_inject_model_solve.py",
         "一键式流水线\n组合多个步骤", ORANGE),
    ]

    box_w = Inches(2.9)
    box_h = Inches(4.8)
    gap = Inches(0.25)
    start_x = Inches(0.5)
    start_y = Inches(1.7)

    for i, (title, modules, desc, color) in enumerate(categories):
        x = start_x + i * (box_w + gap)
        # Header bar
        add_shape(slide, x, start_y, box_w, Inches(0.5), color)
        add_text_box(slide, x + Inches(0.15), start_y + Inches(0.05), box_w - Inches(0.3), Inches(0.4),
                     title, font_size=18, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
        # Body
        body_shape = add_shape(slide, x, start_y + Inches(0.5), box_w, box_h - Inches(0.5),
                               fill_color=LIGHT_GRAY)
        add_text_box(slide, x + Inches(0.15), start_y + Inches(0.6), box_w - Inches(0.3), Inches(1.0),
                     desc, font_size=13, color=ACCENT_BLUE, bold=True)
        add_text_box(slide, x + Inches(0.15), start_y + Inches(1.5), box_w - Inches(0.3), box_h - Inches(1.5),
                     modules, font_size=11, color=MED_GRAY)

    add_footer(slide)


def make_dataflow_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.08), ACCENT_BLUE)

    add_text_box(slide, Inches(0.6), Inches(0.3), Inches(12), Inches(0.7),
                 "数据处理流程", font_size=32, color=DARK_BLUE, bold=True)

    # Flow: boxes with arrows
    flow_items = [
        ("ECXML / 几何文件\n(ECXML / geometry XML)", ACCENT_BLUE),
        ("格式转换\necxml_to_floxml_converter\nwrap_geometry_floxml_as_project", MID_BLUE),
        ("FloXML 基础项目\n(xml_case)", GREEN),
        ("配置注入\nvolume_regions / solve\ngrid / boundary / nonlinear", ORANGE),
        ("完整 FloXML 项目\n可直接导入 FloTHERM", RGBColor(0xC0, 0x39, 0x2B)),
    ]

    box_w = Inches(2.1)
    box_h = Inches(1.6)
    start_x = Inches(0.4)
    arrow_w = Inches(0.35)
    start_y = Inches(1.5)

    for i, (text, color) in enumerate(flow_items):
        x = start_x + i * (box_w + arrow_w)
        shape = add_shape(slide, x, start_y, box_w, box_h, color)
        add_text_box(slide, x + Inches(0.1), start_y + Inches(0.15),
                     box_w - Inches(0.2), box_h - Inches(0.3),
                     text, font_size=12, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

        if i < len(flow_items) - 1:
            # Arrow text
            arrow_x = x + box_w + Inches(0.05)
            add_text_box(slide, arrow_x, start_y + Inches(0.5),
                         arrow_w - Inches(0.1), Inches(0.5),
                         "→", font_size=24, color=MED_GRAY, alignment=PP_ALIGN.CENTER)

    # Pipeline shortcut
    add_text_box(slide, Inches(0.6), Inches(3.5), Inches(12), Inches(0.5),
                 "快捷方式: floxml_pipeline.py 可一步完成上述所有步骤", font_size=14, color=ORANGE, bold=True)

    # JSON config section
    add_shape(slide, Inches(0.5), Inches(4.2), Inches(5.8), Inches(2.8), LIGHT_GRAY)
    add_text_box(slide, Inches(0.7), Inches(4.3), Inches(5.4), Inches(0.4),
                 "JSON 配置文件 (输入)", font_size=16, color=DARK_BLUE, bold=True)
    configs = [
        "• solve_settings.example.json — 求解器配置",
        "• floxml_volume_regions.example.json — 体积区域定义",
        "• transient_only.example.json — 瞬态设置",
        "• floxml_converter_config.example.json — 转换配置",
        "• floxml_template.example.json — 模板配置",
    ]
    add_bullet_list(slide, Inches(0.7), Inches(4.8), Inches(5.4), Inches(2.0),
                    configs, font_size=12, color=DARK_GRAY, spacing=Pt(4))

    # Module dependency
    add_shape(slide, Inches(6.8), Inches(4.2), Inches(5.8), Inches(2.8), LIGHT_GRAY)
    add_text_box(slide, Inches(7.0), Inches(4.3), Inches(5.4), Inches(0.4),
                 "模块调用关系 (核心)", font_size=16, color=DARK_BLUE, bold=True)
    deps = [
        "• floxml_pipeline → floxml_builder + inject_*",
        "• config_injector → floxml_add_volume_regions",
        "• floxml_inject_model_solve → pdml_tools",
        "• floxml_inject_grid → pdml_tools",
        "• ecxml_to_floxml_converter → (独立)",
        "• floxml_builder → (独立, 基础模块)",
    ]
    add_bullet_list(slide, Inches(7.0), Inches(4.8), Inches(5.4), Inches(2.0),
                    deps, font_size=12, color=DARK_GRAY, spacing=Pt(4))

    add_footer(slide)


def make_module_detail_slides(prs):
    """Create individual slides for each major module."""

    modules = [
        {
            "title": "ecxml_to_floxml_converter.py",
            "subtitle": "ECXML → FloXML 核心转换器",
            "lines": "1,851 行",
            "desc": "将 JEDEC JEP181 ECXML 器件热模型转换为 FloTHERM FloXML 项目格式。",
            "details": [
                "ECXML 是器件级热模型交换标准格式",
                "ECXML 缺少: 网格(grid)、求解器(solve)、模型设置(model)、求解域(solution_domain)",
                "本工具自动补充这些配置，生成完整可导入的 FloXML 项目",
                "支持命令行: python -m floxml_tools.ecxml_to_floxml_converter model.ecxml -o output.xml",
                "支持 JSON 配置文件自定义转换参数",
            ],
            "key_classes": "ECXMLToFloXMLConverter (核心转换类)\n支持多种 ECXML 元素映射",
            "color": MID_BLUE,
        },
        {
            "title": "floxml_builder.py",
            "subtitle": "FloXML 项目生成器",
            "lines": "1,554 行",
            "desc": "程序化构建完整的 FloXML 项目文件，覆盖 FloTHERM V10.1 Schema 全部对象。",
            "details": [
                "从 Siemens 官方 VBA 代码 (7196 行) 转换而来",
                "使用 xml.etree.ElementTree 构建 XML",
                "支持: model/solve/grid/attributes/geometry/solution_domain 全部节",
                "提供 Pythonic 的上下文管理器 API (with b.model_section(): ...)",
                "命令行也可直接生成: python -m floxml_tools.floxml_builder -o output.xml",
            ],
            "key_classes": "FloXMLBuilder — 主构建类\n链式 API 设计",
            "color": ACCENT_BLUE,
        },
        {
            "title": "floxml_add_solve_settings.py",
            "subtitle": "求解设置注入器",
            "lines": "1,187 行",
            "desc": "往 FloXML 注入求解设置和瞬态设置，支持 JSON 和 Excel 两种配置方式。",
            "details": [
                "<solve>: overall_control / variable_controls / solver_controls",
                "<model>: modeling / turbulence / gravity / global / initial_variables / transient",
                "支持 JSON 配置: python -m ... model.xml --config solve.json",
                "支持 Excel 配置: python -m ... model.xml --config solve.xlsx",
                "可生成配置模板: python -m ... --create-template template.xlsx",
            ],
            "key_classes": "支持迭代次数、求解器类型、收敛判据、松弛因子等完整求解参数",
            "color": ORANGE,
        },
        {
            "title": "floxml_add_volume_regions.py",
            "subtitle": "体积区域注入器",
            "lines": "1,225 行",
            "desc": "通过 JSON 配置向 FloXML 项目添加体积区域 (region) 和网格约束。",
            "details": [
                "支持显式定义: position + size",
                "支持从已有几何体 bounding box 自动推导 (bbox_from)",
                "支持通配符匹配几何体名称",
                "可创建 grid_constraint_att 定义并分配到几何体",
                "区域可插入到根 geometry 或指定 assembly 下",
            ],
            "key_classes": "支持 include_names / include_patterns / include_tags 多模式匹配",
            "color": GREEN,
        },
        {
            "title": "floxml_boundary_conditions.py",
            "subtitle": "边界条件注入器",
            "lines": "921 行",
            "desc": "通过 JSON 配置向 FloXML 添加/修改边界条件。",
            "details": [
                "Ambient (环境): 温度、压力、换热系数、速度、辐射",
                "Solution Domain (求解域): 各面边界类型",
                "Surface Property (表面属性): 发射率、粗糙度等",
                "Radiation (辐射): 表面类型、面积阈值",
                "Source (热源): 总功率/定温/体积热源",
                "Surface Exchange (表面交换): 对流换热方法",
                "Thermal Model (热模型): 导热/对流模型",
            ],
            "key_classes": "7 种边界条件类型，完整覆盖 FloTHERM 边界设置",
            "color": RGBColor(0x8E, 0x44, 0xAD),
        },
        {
            "title": "config_injector.py",
            "subtitle": "统一 JSON 配置注入器",
            "lines": "548 行",
            "desc": "读取单个 JSON 配置文件，统一注入 FloXML 所需的全部属性。",
            "details": [
                "属性定义: surfaces, surface_exchanges, radiations, resistances, fans, thermals",
                "属性分配: 将引用设置到 geometry 元素 (cuboid, assembly, source 等)",
                "Volume regions / grid constraints: 委托 floxml_add_volume_regions",
                "支持 standalone 使用或被 converter 调用",
                "设计为 ConfigInjector 类，inject(root) 方法就地修改",
            ],
            "key_classes": "ConfigInjector — 统一注入入口",
            "color": ACCENT_BLUE,
        },
        {
            "title": "grid 相关模块 (3个)",
            "subtitle": "grid_config + floxml_grid_parser + inject_grid",
            "lines": "1,599 行 (合计)",
            "desc": "网格配置读取、解析和注入的完整工具链。",
            "details": [
                "grid_config.py (794行): 从 Excel 读取网格配置 (system_grid / patches / constraints)",
                "floxml_grid_parser.py (679行): 解析/修改 FloXML 中的网格设置",
                "floxml_inject_grid.py (126行): 将网格 XML 注入到 FloXML 项目",
                "inject_grid_from_floxml.py (277行): 从已有 FloXML 提取网格注入到新项目",
                "支持 PDML 二进制文件输入 (自动转换为 FloXML)",
            ],
            "key_classes": "SystemGridDirection / GridAxis 数据类",
            "color": MID_BLUE,
        },
        {
            "title": "流程编排模块 (3个)",
            "subtitle": "pipeline + inject_config + inject_model_solve",
            "lines": "730 行 (合计)",
            "desc": "一键式流水线，组合多个注入步骤为单一操作。",
            "details": [
                "floxml_pipeline.py (278行): 组合 wrap + grid/regions + solve 为一次执行",
                "inject_config.py (170行): ECXML→FloXML + 属性注入一步到位",
                "floxml_inject_model_solve.py (282行): model/solve 设置注入",
                "支持: --grid / --solve 分步执行或 -c config.json 统一执行",
                "支持 --wrap 自动包装几何文件为完整项目",
            ],
            "key_classes": "命令行工具，通过 argparse 串联流程",
            "color": ORANGE,
        },
        {
            "title": "辅助模块",
            "subtitle": "floxml_nonlinear_source + wrap_geometry",
            "lines": "871 行 (合计)",
            "desc": "非线性热源和几何包装等辅助功能。",
            "details": [
                "floxml_nonlinear_source.py (498行): 功率-温度曲线注入",
                "  - 支持 JSON 查找表和 CSV 数据",
                "  - 支持数学公式定义曲线",
                "  - 生成 power_temp_curve_point 节点",
                "wrap_geometry_floxml_as_project.py (373行): 包装几何文件",
                "  - 将仅含 attributes + geometry 的文件包装为完整项目",
                "  - 自动补充 model/solve/grid/solution_domain",
            ],
            "key_classes": "适用于表格生成的紧凑模型 XML 文件",
            "color": GREEN,
        },
    ]

    for mod in modules:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        set_slide_bg(slide, WHITE)
        add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.08), mod["color"])

        # Title area
        add_text_box(slide, Inches(0.6), Inches(0.3), Inches(9), Inches(0.5),
                     mod["title"], font_size=28, color=DARK_BLUE, bold=True)
        add_text_box(slide, Inches(0.6), Inches(0.8), Inches(9), Inches(0.4),
                     f"{mod['subtitle']}  |  {mod['lines']}", font_size=16, color=mod["color"])

        # Line separator
        add_shape(slide, Inches(0.6), Inches(1.2), Inches(12), Inches(0.02), mod["color"])

        # Description
        add_text_box(slide, Inches(0.6), Inches(1.4), Inches(12), Inches(0.5),
                     mod["desc"], font_size=15, color=DARK_GRAY, bold=True)

        # Details - left column
        add_shape(slide, Inches(0.5), Inches(2.0), Inches(7.2), Inches(4.5), LIGHT_GRAY)
        add_text_box(slide, Inches(0.7), Inches(2.1), Inches(6.8), Inches(0.4),
                     "功能要点", font_size=16, color=DARK_BLUE, bold=True)
        detail_items = [f"• {d}" for d in mod["details"]]
        add_bullet_list(slide, Inches(0.7), Inches(2.5), Inches(6.8), Inches(3.8),
                        detail_items, font_size=13, color=DARK_GRAY, spacing=Pt(5))

        # Key info - right column
        add_shape(slide, Inches(8.0), Inches(2.0), Inches(4.8), Inches(2.2), LIGHT_BLUE)
        add_text_box(slide, Inches(8.2), Inches(2.1), Inches(4.4), Inches(0.4),
                     "关键类 / 特性", font_size=16, color=DARK_BLUE, bold=True)
        add_text_box(slide, Inches(8.2), Inches(2.5), Inches(4.4), Inches(1.5),
                     mod["key_classes"], font_size=13, color=DARK_GRAY)

        add_footer(slide)


def make_usage_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.08), ACCENT_BLUE)

    add_text_box(slide, Inches(0.6), Inches(0.3), Inches(12), Inches(0.7),
                 "典型使用场景", font_size=32, color=DARK_BLUE, bold=True)

    scenarios = [
        ("场景 1: ECXML 转换 + 求解",
         "python -m floxml_tools.ecxml_to_floxml_converter model.ecxml \\\n"
         "  --config config.json -o project.xml\n"
         "# config.json 中可指定 grid、solve、volume_regions 等全部设置",
         ACCENT_BLUE),
        ("场景 2: 一键流水线",
         "python -m floxml_tools.floxml_pipeline geometry.xml \\\n"
         "  -c config.json --wrap -o project.xml\n"
         "# 自动: 包装为项目 + 注入网格 + 注入求解设置",
         MID_BLUE),
        ("场景 3: 网格复用",
         "python -m floxml_tools.inject_grid_from_floxml \\\n"
         "  project.floxml --ecxml model.ecxml -o output.xml\n"
         "# 从已有项目提取网格应用到新模型",
         GREEN),
        ("场景 4: 非线性热源",
         "python -m floxml_tools.floxml_nonlinear_source \\\n"
         "  input.xml --csv curve.csv --source \"Chip\" -o out.xml\n"
         "# 注入功率-温度曲线",
         ORANGE),
    ]

    start_y = Inches(1.2)
    for i, (title, code, color) in enumerate(scenarios):
        y = start_y + i * Inches(1.5)
        add_shape(slide, Inches(0.5), y, Inches(3.0), Inches(1.3), color)
        add_text_box(slide, Inches(0.7), y + Inches(0.2), Inches(2.6), Inches(0.9),
                     title, font_size=14, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
        add_shape(slide, Inches(3.7), y, Inches(9.1), Inches(1.3), LIGHT_GRAY)
        add_text_box(slide, Inches(3.9), y + Inches(0.15), Inches(8.7), Inches(1.0),
                     code, font_size=11, color=DARK_GRAY, font_name="Menlo")

    add_footer(slide)


def make_config_example_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.08), ACCENT_BLUE)

    add_text_box(slide, Inches(0.6), Inches(0.3), Inches(12), Inches(0.7),
                 "配置文件示例", font_size=32, color=DARK_BLUE, bold=True)

    # Left: solve settings example
    add_shape(slide, Inches(0.5), Inches(1.2), Inches(6.0), Inches(5.5), LIGHT_GRAY)
    add_text_box(slide, Inches(0.7), Inches(1.3), Inches(5.6), Inches(0.4),
                 "solve_settings.example.json", font_size=14, color=ACCENT_BLUE, bold=True)
    solve_json = """{
  "overall_control": {
    "max_iterations": 1500,
    "solver_type": "coupled",
    "convergence_criteria": 1e-4
  },
  "modeling": {
    "solution": "flow_heat",
    "radiation": "on"
  },
  "transient": {
    "time_steps": [0, 60, 300],
    "save_times": [60, 300]
  }
}"""
    add_text_box(slide, Inches(0.7), Inches(1.8), Inches(5.6), Inches(4.5),
                 solve_json, font_size=11, color=DARK_GRAY, font_name="Menlo")

    # Right: volume regions example
    add_shape(slide, Inches(6.8), Inches(1.2), Inches(6.0), Inches(5.5), LIGHT_GRAY)
    add_text_box(slide, Inches(7.0), Inches(1.3), Inches(5.6), Inches(0.4),
                 "floxml_volume_regions.example.json", font_size=14, color=GREEN, bold=True)
    vr_json = """{
  "grid_constraint_atts": [
    {
      "name": "fine_grid",
      "max_size": 0.001
    }
  ],
  "volume_regions": [
    {
      "name": "chip_region",
      "bbox_from": {
        "include_names": ["U1"],
        "padding": 0.002
      },
      "grid_constraint": "fine_grid"
    }
  ]
}"""
    add_text_box(slide, Inches(7.0), Inches(1.8), Inches(5.6), Inches(4.5),
                 vr_json, font_size=11, color=DARK_GRAY, font_name="Menlo")

    add_footer(slide)


def make_test_status_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.08), ACCENT_BLUE)

    add_text_box(slide, Inches(0.6), Inches(0.3), Inches(12), Inches(0.7),
                 "测试 & 文档状态", font_size=32, color=DARK_BLUE, bold=True)

    # Test status
    add_shape(slide, Inches(0.5), Inches(1.3), Inches(5.8), Inches(2.5), LIGHT_GRAY)
    add_text_box(slide, Inches(0.7), Inches(1.4), Inches(5.4), Inches(0.4),
                 "单元测试", font_size=18, color=DARK_BLUE, bold=True)
    tests = [
        "• test_ecxml_to_floxml_converter_pytest.py — pytest 格式",
        "• test_ecxml_to_floxml_converter_unittest.py — unittest 格式",
        "• 测试覆盖: ECXML 转换器核心功能",
        "• 建议: 其他模块仍需补充单元测试",
    ]
    add_bullet_list(slide, Inches(0.7), Inches(1.9), Inches(5.4), Inches(1.8),
                    tests, font_size=13, color=DARK_GRAY, spacing=Pt(4))

    # Documentation
    add_shape(slide, Inches(6.8), Inches(1.3), Inches(5.8), Inches(2.5), LIGHT_GRAY)
    add_text_box(slide, Inches(7.0), Inches(1.4), Inches(5.4), Inches(0.4),
                 "文档", font_size=18, color=DARK_BLUE, bold=True)
    docs = [
        "• 每个模块有完整的 docstring (含用法示例)",
        "• floxml_add_volume_regions.md — 体积区域详细说明",
        "• GAP_ANALYSIS.md — 功能差距分析",
        "• README.md — 项目整体说明",
    ]
    add_bullet_list(slide, Inches(7.0), Inches(1.9), Inches(5.4), Inches(1.8),
                    docs, font_size=13, color=DARK_GRAY, spacing=Pt(4))

    # TODO / suggestions
    add_shape(slide, Inches(0.5), Inches(4.2), Inches(12.1), Inches(2.8), LIGHT_BLUE)
    add_text_box(slide, Inches(0.7), Inches(4.3), Inches(11.7), Inches(0.4),
                 "后续改进建议", font_size=18, color=DARK_BLUE, bold=True)
    suggestions = [
        "• 补充单元测试: 目前仅 ecxml_to_floxml_converter 有完整测试，其他模块建议按优先级逐步补充",
        "• 统一配置格式: 各模块配置 JSON schema 略有差异，可考虑统一规范",
        "• 错误处理增强: 部分模块对异常输入处理不够完善",
        "• 性能优化: 大型 ECXML 文件转换时可考虑流式解析",
        "• 日志系统: 建议引入 logging 模块替代 print 输出",
    ]
    add_bullet_list(slide, Inches(0.7), Inches(4.8), Inches(11.7), Inches(2.0),
                    suggestions, font_size=13, color=DARK_GRAY, spacing=Pt(4))

    add_footer(slide)


def make_summary_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.08), ACCENT_BLUE)

    add_text_box(slide, Inches(0.6), Inches(0.3), Inches(12), Inches(0.7),
                 "交接总结", font_size=32, color=DARK_BLUE, bold=True)

    # Summary stats
    add_shape(slide, Inches(0.5), Inches(1.3), Inches(12.1), Inches(1.8), LIGHT_BLUE)
    stats = [
        ("16", "Python 模块"),
        ("~10,800", "行代码"),
        ("1", "核心转换器 (ECXML→FloXML)"),
        ("7", "边界条件类型"),
    ]
    for i, (num, label) in enumerate(stats):
        x = Inches(0.7) + i * Inches(3.0)
        add_text_box(slide, x, Inches(1.4), Inches(2.8), Inches(0.8),
                     num, font_size=36, color=ACCENT_BLUE, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide, x, Inches(2.1), Inches(2.8), Inches(0.5),
                     label, font_size=13, color=MED_GRAY, alignment=PP_ALIGN.CENTER)

    # Key takeaways
    add_text_box(slide, Inches(0.6), Inches(3.5), Inches(12), Inches(0.4),
                 "核心要点", font_size=20, color=DARK_BLUE, bold=True)

    takeaways = [
        "1. floxml_tools 是一套完整的 FloTHERM 自动化工具，核心能力是 ECXML → FloXML 转换",
        "2. 采用 JSON/XLSX 配置驱动，无需手动编辑 XML，降低使用门槛",
        "3. 模块化设计: 每个功能独立可用，也可通过 pipeline 一键组合",
        "4. 覆盖全流程: 模型构建 → 格式转换 → 网格配置 → 求解设置 → 边界条件 → 非线性热源",
        "5. 所有模块均有命令行入口，支持 -h 查看帮助",
        "6. 注意: 部分注入模块依赖项目根目录下的 pdml_tools 包",
    ]
    add_bullet_list(slide, Inches(0.6), Inches(4.0), Inches(12), Inches(3.0),
                    takeaways, font_size=14, color=DARK_GRAY, spacing=Pt(6))

    add_footer(slide)


def make_thankyou_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, DARK_BLUE)

    add_text_box(slide, Inches(2), Inches(2.5), Inches(9.3), Inches(1.5),
                 "谢谢", font_size=56, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(slide, Inches(2), Inches(4.0), Inches(9.3), Inches(0.8),
                 "如有疑问请参考各模块 docstring 或 README.md",
                 font_size=18, color=MID_BLUE, alignment=PP_ALIGN.CENTER)
    add_text_box(slide, Inches(2), Inches(5.0), Inches(9.3), Inches(0.6),
                 "python -m floxml_tools.<module_name> -h  # 查看任何模块的帮助",
                 font_size=14, color=LIGHT_BLUE, alignment=PP_ALIGN.CENTER, font_name="Menlo")


def main():
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    make_title_slide(prs)
    make_overview_slide(prs)
    make_dataflow_slide(prs)
    make_usage_slide(prs)
    make_module_detail_slides(prs)
    make_config_example_slide(prs)
    make_test_status_slide(prs)
    make_summary_slide(prs)
    make_thankyou_slide(prs)

    out_path = os.path.join(os.path.dirname(__file__), "floxml_tools_工作交接.pptx")
    prs.save(out_path)
    print(f"PPT saved to: {out_path}")
    print(f"Total slides: {len(prs.slides)}")


if __name__ == "__main__":
    main()
