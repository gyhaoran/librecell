# Task 03: 工艺配置系统重构

## 目标

用 YAML + Pydantic 配置体系替代当前的裸 Python 模块工艺配置。实现 schema 校验、默认值、继承机制和向后兼容。

## 前置条件

- Task 01 完成（包结构修复）
- Task 02 完成（测试安全网就绪）

## 详细任务

### 3.1 设计 Pydantic 工艺配置模型

**操作**：创建 `lccommon/tech_config.py`

**核心数据模型**：
```python
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Tuple
from enum import Enum

class LayerDefinition(BaseModel):
    """单个工艺层定义"""
    name: str
    gds_layer: int
    gds_purpose: int = 0
    material: Optional[str] = None  # e.g., "metal", "via", "diffusion"
    direction: Optional[str] = None  # "horizontal", "vertical", "hv", ""
    min_width: Optional[float] = None
    min_spacing: Optional[float] = None
    min_area: Optional[float] = None
    min_notch: Optional[float] = None

class ViaDefinition(BaseModel):
    """Via 层定义"""
    name: str
    gds_layer: int
    gds_purpose: int = 0
    bottom_layer: str
    top_layer: str
    size: float  # via 尺寸 (db_unit)
    min_enclosure_bottom: float = 0
    min_enclosure_top: float = 0

class PowerDomain(BaseModel):
    """电源域定义"""
    name: str
    supply_net: str  # e.g., "VDD"
    ground_net: str  # e.g., "VSS"
    voltage: Optional[float] = None

class RoutingConfig(BaseModel):
    """布线配置"""
    grid_pitch_x: float
    grid_pitch_y: float
    grid_offset_x: float = 0
    grid_offset_y: float = 0
    layers: Dict[str, str]  # layer_name -> direction ("h"/"v"/"hv")
    wire_width: Dict[str, float]
    wire_width_horizontal: Optional[Dict[str, float]] = None
    via_weights: Dict[str, float] = {}
    weights_horizontal: Dict[str, float] = {}
    weights_vertical: Dict[str, float] = {}
    orientation_change_penalty: float = 100

class CellConfig(BaseModel):
    """单元尺寸配置"""
    unit_cell_width: float
    unit_cell_height: float
    gate_length: float
    gate_extension: float
    transistor_offset_y: float
    power_rail_width: float
    minimum_gate_width_nfet: float
    minimum_gate_width_pfet: float
    minimum_pin_width: float
    transistor_channel_width_sizing: float = 1.0  # 沟道宽度缩放因子，1.0 表示不缩放

class TechConfig(BaseModel):
    """完整工艺配置"""
    name: str
    node: str  # e.g., "180nm", "55nm"
    db_unit: float = 1e-9

    # 层定义
    layers: List[LayerDefinition]
    vias: List[ViaDefinition]

    # 电源域
    power_domains: List[PowerDomain]

    # 设计规则
    min_spacing: Dict[str, Dict[str, float]]  # layer -> layer -> spacing
    min_enclosure: Dict[str, Dict[str, float]]  # outer -> inner -> enclosure

    # 单元配置
    cell: CellConfig

    # 布线配置
    routing: RoutingConfig

    # 输出配置
    output_map: Dict[str, Union[Tuple[int,int], List[Tuple[int,int]]]]
    # 注意：output_map 支持一对多映射，如 nwell: [[1,0], [1,1]]
    output_writers: List[WriterConfig]

    # 可选：工艺特定扩展
    extensions: Dict = {}

class WriterConfig(BaseModel):
    """输出写入器配置（YAML 可序列化替代 Python Writer 对象实例）"""
    type: str  # "gds", "lef", "mag"
    enabled: bool = True
    db_unit: Optional[float] = None  # 覆盖全局 db_unit
    output_map: Optional[Dict[str, Union[Tuple[int,int], List[Tuple[int,int]]]]] = None
    # 覆盖全局 output_map（MagWriter 有独立 output_map）
    # 特定写入器参数
    params: Dict[str, Any] = {}
    # e.g., {"tech_name": "scmos", "scale_factor": 0.1, "site": "CORE"}
```

**关于 output_writers 的 YAML 化设计**：

当前 `dummy_tech.py` 中 `output_writers` 是 Python 对象实例列表：
```python
output_writers = [
    MagWriter(tech_name='scmos', scale_factor=0.1, output_map={...}),
    LefWriter(db_unit=1e-6, output_map=output_map, site="CORE"),
    GdsWriter(db_unit=db_unit, output_map=output_map)
]
```

每个 Writer 有独立的 `output_map`（MagWriter 的映射使用字符串层名而非 GDS 数字）。
YAML 中需要用 `WriterConfig` 描述，由引擎负责实例化对应 Writer 类：

```yaml
output_writers:
  - type: mag
    enabled: true
    params:
      tech_name: scmos
      scale_factor: 0.1
    output_map:  # MagWriter 专用映射（字符串层名）
      via1: m2contact
      poly: polysilicon
      abutment_box: [border, fence]
      # ...
  - type: lef
    db_unit: 1e-6
    params:
      site: CORE
    # 使用全局 output_map
  - type: gds
    # 使用全局 db_unit 和 output_map
```

**关于 output_map 一对多映射**：

当前代码支持将一个内部层映射到多个输出层：
```python
l_nwell: [my_nwell, my_nwell2],  # Map l_nwell to two output layers
```

Pydantic 模型中使用 `Union[Tuple[int,int], List[Tuple[int,int]]]` 类型处理，
YAML 中表示为：
```yaml
output_map:
  nwell: [[1, 0], [1, 1]]    # 一对多
  ndiffusion: [3, 0]          # 一对一
```

### 3.2 实现 YAML 加载器

**操作**：创建 `lccommon/tech_loader.py`

- 实现 `load_tech_yaml(path: str) -> TechConfig`
- 实现 `save_tech_yaml(config: TechConfig, path: str) -> None`（将 TechConfig 序列化为 YAML，Task 09 SE 工作流需要）
- 支持 `!include` 指令（引用其他 YAML 文件）
- 支持变量引用 `${node_name}` 替换
- 加载后执行 Pydantic 校验
- 友好的错误消息（指出具体哪个字段缺失或类型错误）

### 3.3 实现向后兼容层

**操作**：修改 `lclayout/tech_util.py`

- 保留 `load_tech_file()` 函数，自动检测文件类型：
  - `.py` 文件 → 使用现有 Python 加载逻辑
  - `.yaml` / `.yml` 文件 → 使用新的 YAML 加载器
- 两种方式加载后，统一转换为 `TechConfig` 对象
- 实现 `python_tech_to_config(module) -> TechConfig` 转换函数
- `TechConfig` 对象**必须**提供与原 Python 模块相同的**平坦属性访问接口**

**平坦属性兼容列表**（从 `dummy_tech.py` 和 `standalone.py` 的实际使用中提取）：

TechConfig 必须直接提供以下属性（通过 `@property` 委托到内部子模型），确保 `tech.xxx` 的现有访问方式不被破坏：

```python
# 来自 cell 子模型
tech.unit_cell_width        # → self.cell.unit_cell_width
tech.unit_cell_height       # → self.cell.unit_cell_height
tech.gate_length            # → self.cell.gate_length
tech.power_rail_width       # → self.cell.power_rail_width
tech.minimum_gate_width_nfet  # → self.cell.minimum_gate_width_nfet
tech.minimum_gate_width_pfet  # → self.cell.minimum_gate_width_pfet
tech.minimum_pin_width      # → self.cell.minimum_pin_width
tech.transistor_channel_width_sizing  # → self.cell.transistor_channel_width_sizing

# 来自 routing 子模型
tech.routing_grid_pitch_x   # → self.routing.grid_pitch_x
tech.routing_grid_pitch_y   # → self.routing.grid_pitch_y
tech.grid_offset_x          # → self.routing.grid_offset_x
tech.grid_offset_y          # → self.routing.grid_offset_y
tech.routing_layers         # → self.routing.layers
tech.wire_width             # → self.routing.wire_width
tech.wire_width_horizontal  # → self.routing.wire_width_horizontal
tech.via_weights            # → self.routing.via_weights
tech.weights_horizontal     # → self.routing.weights_horizontal
tech.weights_vertical       # → self.routing.weights_vertical
tech.orientation_change_penalty  # → self.routing.orientation_change_penalty

# 来自顶层 / 设计规则
tech.db_unit                # 顶层属性
tech.min_spacing            # 顶层属性（Dict[Tuple, float]）
tech.minimum_width          # 顶层属性
tech.minimum_enclosure      # 顶层属性
tech.minimum_notch          # 顶层属性
tech.min_area               # 顶层属性
tech.connectable_layers     # 顶层属性
tech.via_size               # 顶层属性
tech.multi_via              # 顶层属性
tech.pin_layer              # 顶层属性
tech.power_layer            # 顶层属性

# 来自输出配置
tech.output_map             # 全局层映射
tech.output_writers         # Writer 实例列表（由 WriterConfig 实例化）
```

**注意**：`output_writers` 在 YAML 模式下由 `WriterConfig` 描述，TechConfig 在被访问时自动实例化为 `MagWriter`/`LefWriter`/`GdsWriter` 对象（lazy instantiation），确保 `tech.output_writers` 返回的仍然是 `Writer` 实例列表。

### 3.3.1 LcLayout 接口契约（Task 03 完成后）

Task 03 完成后，`LcLayout.__init__` 的签名变为：

```python
# Task 03 完成后的 LcLayout 签名
class LcLayout:
    def __init__(self,
                 tech: TechConfig,           # 从 untyped module 改为 TechConfig
                 layout: pya.Layout,
                 placer: TransistorPlacer,
                 router: GraphRouter,
                 debug_routing_graph: bool = False,
                 debug_smt_solver: bool = False):
        self.tech = tech                     # TechConfig 对象
        self.layer_stack = None              # Task 04 填充
        # ... 其余不变
```

**关键约束**：
- `tech` 参数类型从 untyped Python module 变为 `TechConfig`
- 由于 TechConfig 提供平坦属性兼容接口，`LcLayout` 内部代码（如 `tech.routing_grid_pitch_x`）无需修改
- `main()` 函数中 `tech_util.load_tech_file()` 的返回类型从 module 变为 `TechConfig`
- `layer_stack` 属性预留为 `None`，Task 04 填充

### 3.4 创建 YAML 版 dummy_tech

**操作**：创建 `examples/dummy_tech.yaml`

- 将 `dummy_tech.py` 中的所有参数翻译为 YAML 格式
- 添加注释说明每个参数的含义和单位
- 确保 YAML 版本和 Python 版本生成完全相同的结果

### 3.5 创建工艺配置模板

**操作**：创建 `examples/` 目录下的工艺配置文件

- `examples/cmos_180nm.yaml` — 180nm CMOS 工艺完整配置（Task 09 端到端测试使用）
- `examples/templates/cmos_55nm_template.yaml` — 55nm CMOS 工艺模板（参数可为占位符，Task 07 迁移生成）
- 每个配置/模板包含详细注释，指导 SE 工程师如何填写
- `cmos_180nm.yaml` 必须是**可直接使用**的完整配置（不是模板），基于 `dummy_tech.yaml` 调整为合理的 180nm 参数

### 3.6 适配核心引擎使用 TechConfig

**操作**：修改 `lclayout/standalone.py`

- `LcLayout.__init__` 接受 `TechConfig` 对象
- 所有原来通过 `tech.xxx` 访问 Python 模块属性的地方，改为通过 `TechConfig` 对象访问
- 保持 CLI 接口不变（`--tech` 参数同时接受 .py 和 .yaml）

**验收测试**：
```python
# tests/unit/common/test_tech_config.py

class TestTechConfig:
    def test_load_yaml(self):
        """从 YAML 文件加载工艺配置"""
        config = load_tech_yaml("examples/dummy_tech.yaml")
        assert config.db_unit == 1e-9
        assert config.cell.unit_cell_width == 400

    def test_schema_validation_missing_field(self):
        """缺少必要字段时抛出 ValidationError"""

    def test_schema_validation_wrong_type(self):
        """字段类型错误时抛出 ValidationError"""

    def test_default_values(self):
        """可选字段有合理的默认值"""

    def test_python_compat_conversion(self):
        """Python tech 文件可转换为 TechConfig"""
        from lclayout.tech_util import load_tech_file_raw  # 加载原始 Python 模块
        py_module = load_tech_file_raw("examples/dummy_tech.py")
        py_config = python_tech_to_config(py_module)
        yaml_config = load_tech_yaml("examples/dummy_tech.yaml")
        assert py_config.cell.unit_cell_width == yaml_config.cell.unit_cell_width

    def test_layer_definitions(self):
        """层定义包含所有必要层"""
        config = load_tech_yaml("examples/dummy_tech.yaml")
        layer_names = [l.name for l in config.layers]
        assert 'ndiffusion' in layer_names
        assert 'metal1' in layer_names
        assert 'metal2' in layer_names

    def test_spacing_rules(self):
        """间距规则正确加载（YAML 嵌套 dict 格式）"""
        config = load_tech_yaml("examples/dummy_tech.yaml")
        assert config.min_spacing["ndiffusion"]["ndiffusion"] == 50
        assert config.min_spacing["metal1"]["metal1"] == 50
        assert config.min_spacing["metal2"]["metal2"] == 100

    def test_spacing_rules_python_to_yaml_conversion(self):
        """Python tuple-key dict 正确转换为嵌套 dict"""
        # dummy_tech.py 使用 (layer_a, layer_b): value 格式
        # TechConfig 使用 {layer_a: {layer_b: value}} 嵌套格式
        from lclayout.tech_util import load_tech_file_raw
        py_module = load_tech_file_raw("examples/dummy_tech.py")
        py_config = python_tech_to_config(py_module)
        assert py_config.min_spacing["ndiffusion"]["ndiffusion"] == 50
        assert py_config.min_spacing["pdiffusion"]["ndiffusion"] == 50
        # 注意：原始 (pdiff, ndiff) 是否自动填充 (ndiff, pdiff) 需在实现时决定并在此断言

    def test_power_domains(self):
        """电源域配置正确"""
        config = load_tech_yaml("examples/dummy_tech.yaml")
        assert len(config.power_domains) >= 1
        assert config.power_domains[0].supply_net == "VDD"

    def test_save_and_reload_yaml(self, tmp_path):
        """TechConfig 可序列化为 YAML 并重新加载"""
        config = load_tech_yaml("examples/dummy_tech.yaml")
        save_path = str(tmp_path / "saved_tech.yaml")
        save_tech_yaml(config, save_path)
        reloaded = load_tech_yaml(save_path)
        assert reloaded.db_unit == config.db_unit
        assert reloaded.cell.unit_cell_width == config.cell.unit_cell_width

    def test_flat_property_compat(self):
        """TechConfig 平坦属性兼容接口可用"""
        config = load_tech_yaml("examples/dummy_tech.yaml")
        # 通过平坦属性访问（向后兼容 Python tech module 风格）
        assert config.unit_cell_width == config.cell.unit_cell_width
        assert config.routing_grid_pitch_x == config.routing.grid_pitch_x

# tests/integration/test_yaml_tech_pipeline.py

@pytest.mark.integration
class TestYamlTechPipeline:
    def test_generate_inv_with_yaml_tech(self, tmp_output_dir):
        """使用 YAML 工艺配置生成 INVX1"""

    def test_generate_nand2_with_yaml_tech(self, tmp_output_dir):
        """使用 YAML 工艺配置生成 NAND2"""

    def test_yaml_and_python_produce_same_gds(self, tmp_output_dir):
        """YAML 和 Python 配置生成的 GDS 完全一致"""

    def test_cli_accepts_yaml(self, tmp_output_dir):
        """CLI --tech 参数接受 .yaml 文件"""
```

## 完成标准

- [ ] `TechConfig` Pydantic 模型定义完成，包含所有必要字段
- [ ] `load_tech_yaml()` 能正确加载 `dummy_tech.yaml`
- [ ] `python_tech_to_config()` 能将 `dummy_tech.py` 转为 `TechConfig`
- [ ] YAML 和 Python 配置生成的布局结果完全一致
- [ ] 缺失字段/类型错误时产生清晰的错误消息
- [ ] `pytest tests/unit/common/test_tech_config.py -v` 全部通过
- [ ] `pytest tests/integration/test_yaml_tech_pipeline.py -v` 全部通过
- [ ] 现有 `lclayout --tech examples/dummy_tech.py` 仍然正常工作

## 预计影响范围

- `lccommon/tech_config.py`（新文件）
- `lccommon/tech_loader.py`（新文件）
- `lclayout/tech_util.py`（修改）
- `lclayout/standalone.py`（修改，使用 TechConfig）
- `examples/dummy_tech.yaml`（新文件）
- `examples/templates/`（新目录）
- `setup.py`（添加 pydantic, pyyaml 依赖）
