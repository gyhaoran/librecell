# Task 04: 层定义动态化

## 目标

用运行时构建的 `LayerStack` 替代硬编码的 `layers.py`，支持任意金属层数（2~6层），消除当前仅支持 metal1/metal2 的限制。

## 前置条件

- Task 03 完成（TechConfig 系统可用）

## 详细任务

### 4.1 设计 LayerStack 数据结构

**操作**：创建 `lccommon/layer_stack.py`

```python
class Layer:
    """运行时层对象，替代 layers.py 中的硬编码常量"""
    name: str
    index: int  # 唯一索引，用于 KLayout
    material: str  # "diffusion", "well", "poly", "metal", "via", "contact"

class LayerStack:
    """动态层栈，从 TechConfig 构建"""

    def __init__(self, tech_config: TechConfig): ...

    # 按名称访问
    def get_layer(self, name: str) -> Layer: ...

    # 按类型批量获取
    def get_metal_layers(self) -> List[Layer]: ...
    def get_via_layers(self) -> List[Layer]: ...

    # Via 连接关系
    def get_via_between(self, bottom: Layer, top: Layer) -> Optional[Layer]: ...
    def get_layers_above(self, layer: Layer) -> List[Layer]: ...
    def get_layers_below(self, layer: Layer) -> List[Layer]: ...

    # 兼容性：提供与旧 layers.py 相同的属性
    @property
    def l_ndiffusion(self) -> Layer: ...
    @property
    def l_metal1(self) -> Layer: ...
    # ... 等等
```

### 4.2 重构 layers.py 为兼容适配器

**操作**：修改 `lclayout/layout/layers.py`

- 保留所有原有的全局常量（`l_ndiffusion`, `l_metal1` 等）作为默认值
- 添加 `LayerStack.from_legacy()` 类方法，从旧的硬编码层创建 LayerStack
- 所有引用 `layers.py` 常量的代码逐步迁移到通过 LayerStack 访问

### 4.3 修改布线图构建

**操作**：修改 `lclayout/routing_graph.py`

当前 `routing_graph.py` 有两处关键的硬编码依赖：

1. **`via_layers` 图**（第 52 行）：`for l1, l2, data in via_layers.edges(data=True):` — 直接使用 `layers.py` 导出的 `via_layers` networkx Graph。这个图编码了 ndiff↔metal1、pdiff↔metal1、poly↔metal1、metal1↔metal2 的连接关系。
   - **改为**：从 LayerStack 获取 via connectivity（`layer_stack.get_via_definitions()` 或类似接口）

2. **`layermap` 未直接使用**，但通过 `from .layout.layers import *` 引入了所有层常量。

**改造后**：
- `create_routing_graph_base(grid, tech, layer_stack)` — 增加 `layer_stack` 参数
- Via 边的创建循环遍历 `layer_stack.get_via_definitions()` 而非 `via_layers.edges()`
- 支持 3+ 层金属的布线图（自动根据 LayerStack 中的金属层数量创建节点和边）

### 4.3.1 修改 `_02_setup_layout`

`standalone.py:307` 的 `_02_setup_layout()` 使用 `layermap` 字典来设置 KLayout 层：
```python
# 当前（硬编码）
for name, (num, purpose) in layermap.items():
    layer = self.layout.layer(num, purpose)
    self.shapes[name] = self.top_cell.shapes(layer)
```

**改为**：从 LayerStack 获取所有层的 GDS 编号：
```python
# 改造后
for layer_def in self.layer_stack.all_layers():
    klayout_layer = self.layout.layer(layer_def.gds_layer, layer_def.gds_purpose)
    self.shapes[layer_def.name] = self.top_cell.shapes(klayout_layer)
```

### 4.3.2 修改 DRC cleaner

`drc_cleaner/drc_cleaner.py:32` 同样 `from ..layout.layers import *`，使用层常量进行 DRC 修正。需同步改为从 LayerStack 获取。

### 4.4 修改单元模板

**操作**：修改 `lclayout/layout/cell_template.py`

- Well 层从 LayerStack 获取（而非硬编码 nwell/pwell）
- Power rail 层从 TechConfig 获取

### 4.5 修改晶体管绘制

**操作**：修改 `lclayout/layout/transistor.py`

- Diffusion、gate、contact 层从 LayerStack 获取
- 移除对 `layers.py` 全局常量的直接引用

### 4.6 修改输出写入器

**操作**：修改 `lclayout/writer/` 下的写入器

- GDS output_map 从 TechConfig 动态构建
- LEF 层名称从 LayerStack 获取
- MAG 层映射从配置获取

### 4.7 修改 LVS 验证

**操作**：修改 `lclayout/lvs/lvs.py`

当前 `lvs.py` 的 `extract_netlist()` 函数（约 100 行）是**最重度硬编码**的位置，需要重点改造。

**当前硬编码问题**：
1. 所有层名直接引用 `layers.py` 常量：`l_nwell`, `l_ndiffusion`, `l_metal1`, `l_metal2`, `l_via1` 等
2. Active region 定义硬编码：`rpactive = rpdiff & rnwell`，`rnactive = rndiff - rnwell`
3. 仅处理 metal1/metal2 两层金属的 connectivity（代码中已有 `# TODO: what if more than 2 metal layers?` 注释）
4. 只有 3 端子 MOS 设备提取（无 4 端子、无 HV 器件）

**改造步骤**：

**步骤 1：层获取动态化**
```python
# 之前（硬编码）
rnwell = make_layer(l_nwell)
rmetal1 = make_layer(l_metal1)
rmetal2 = make_layer(l_metal2)
rvia1 = make_layer(l_via1)

# 之后（从 LayerStack 动态获取）
def extract_netlist(layout, top_cell, layer_stack):
    rnwell = make_layer(layer_stack.get_layer("nwell"))
    for metal in layer_stack.get_metal_layers():
        metal_regions[metal.name] = make_layer(metal)
    for via in layer_stack.get_via_layers():
        via_regions[via.name] = make_layer(via)
```

**步骤 2：Inter-layer connectivity 动态生成**
```python
# 之前（硬编码 2 层金属）
l2n.connect(rmetal1, rvia1)
l2n.connect(rvia1, rmetal2)

# 之后（循环处理任意层数）
for via_def in layer_stack.get_via_definitions():
    bottom_region = metal_regions[via_def.bottom_layer]
    top_region = metal_regions[via_def.top_layer]
    via_region = via_regions[via_def.name]
    l2n.connect(bottom_region, via_region)
    l2n.connect(via_region, top_region)
```

**步骤 3：Label connectivity 动态生成**
```python
# 之前
l2n.connect(rmetal1, rmetal1_lbl)
l2n.connect(rmetal2, rmetal2_lbl)

# 之后
for metal in layer_stack.get_metal_layers():
    label_layer = layer_stack.get_label_layer(metal)
    if label_layer:
        l2n.connect(metal_regions[metal.name], make_layer(label_layer))
```

**步骤 4：设备提取规则参数化**
- PMOS/NMOS 的 active region 推导公式从 TechConfig 获取（而非硬编码 `pdiff & nwell`）
- 预留 4 端子 MOS 提取接口（Task 06 BCD 需要）

**注意**：`MOS4To3NetlistSpiceReader` 类也使用硬编码的 `['S', 'G', 'D']` 端口顺序，需与 TechConfig 的设备模型定义对齐。

**验收测试**：
```python
# tests/unit/layout/test_layer_stack.py

class TestLayerStack:
    def test_create_from_tech_config(self):
        """从 TechConfig 创建 LayerStack"""
        config = load_tech_yaml("examples/dummy_tech.yaml")
        stack = LayerStack(config)
        assert stack.get_layer("metal1") is not None
        assert stack.get_layer("metal2") is not None

    def test_get_metal_layers(self):
        """获取所有金属层"""
        stack = LayerStack(config_2metal)
        assert len(stack.get_metal_layers()) == 2

        stack = LayerStack(config_4metal)
        assert len(stack.get_metal_layers()) == 4

    def test_via_connectivity(self):
        """Via 连接关系正确"""
        stack = LayerStack(config)
        via = stack.get_via_between(
            stack.get_layer("metal1"),
            stack.get_layer("metal2")
        )
        assert via is not None
        assert via.name == "via1"

    def test_legacy_compatibility(self):
        """兼容旧的属性访问方式"""
        stack = LayerStack(config)
        assert stack.l_ndiffusion == stack.get_layer("ndiffusion")
        assert stack.l_metal1 == stack.get_layer("metal1")

    def test_legacy_compatibility_complete(self):
        """所有 layers.py 遗留属性在 LayerStack 上可访问"""
        stack = LayerStack(config)
        # layers.py 中定义的全部 17 个层常量
        legacy_attrs = [
            'l_ndiffusion', 'l_pdiffusion', 'l_nwell', 'l_pwell',
            'l_poly', 'l_poly_label',
            'l_pdiff_contact', 'l_ndiff_contact', 'l_poly_contact',
            'l_metal1', 'l_metal1_label', 'l_metal1_pin',
            'l_via1',
            'l_metal2', 'l_metal2_label', 'l_metal2_pin',
            'l_abutment_box',
        ]
        for attr in legacy_attrs:
            assert hasattr(stack, attr), f"LayerStack missing legacy attr: {attr}"
            assert getattr(stack, attr) == stack.get_layer(attr[2:])  # strip 'l_' prefix

    def test_3_metal_layers(self):
        """支持 3 层金属"""
        config_3m = make_config(metals=["metal1", "metal2", "metal3"])
        stack = LayerStack(config_3m)
        assert len(stack.get_metal_layers()) == 3
        assert stack.get_via_between(
            stack.get_layer("metal2"),
            stack.get_layer("metal3")
        ) is not None

    def test_4_metal_layers(self):
        """支持 4 层金属"""

# tests/unit/layout/test_routing_graph_dynamic.py

def test_routing_graph_2_metals():
    """2 层金属布线图结构正确"""

def test_routing_graph_3_metals():
    """3 层金属布线图包含额外的层和 via"""

def test_routing_graph_layer_directions():
    """每层的布线方向正确"""

# tests/integration/test_dynamic_layers_pipeline.py

@pytest.mark.integration
class TestDynamicLayersPipeline:
    def test_2metal_generates_same_as_before(self, tmp_output_dir):
        """2 层金属配置生成结果与重构前一致"""

    def test_3metal_config_accepted(self, tmp_output_dir):
        """3 层金属配置能通过校验并生成布局"""

    def test_gds_layer_mapping_dynamic(self, tmp_output_dir):
        """GDS 输出的层映射与配置一致"""

    def test_lef_layer_names_dynamic(self, tmp_output_dir):
        """LEF 输出的层名称与配置一致"""

    def test_lvs_with_dynamic_layers(self, tmp_output_dir):
        """动态层定义下 LVS 仍然通过"""
```

## 完成标准

- [ ] `LayerStack` 能从 `TechConfig` 动态构建
- [ ] 2 层金属配置生成结果与重构前 bit-exact 一致
- [ ] 3 层金属配置能正确构建布线图（节点和边数量正确）
- [ ] `layers.py` 中的旧常量仍可访问（向后兼容）
- [ ] 所有引用层的模块（routing_graph, cell_template, transistor, writers, lvs）使用 LayerStack
- [ ] `pytest tests/unit/layout/test_layer_stack.py -v` 全部通过
- [ ] `pytest tests/integration/test_dynamic_layers_pipeline.py -v` 全部通过
- [ ] Task 02 中的所有回归测试仍然通过

## 预计影响范围

- `lccommon/layer_stack.py`（新文件）
- `lclayout/layout/layers.py`（重构为适配器）
- `lclayout/routing_graph.py`（使用 LayerStack）
- `lclayout/layout/cell_template.py`（使用 LayerStack）
- `lclayout/layout/transistor.py`（使用 LayerStack）
- `lclayout/writer/*.py`（使用 LayerStack）
- `lclayout/lvs/lvs.py`（使用 LayerStack）
- `lclayout/standalone.py`（传递 LayerStack）
- `lclayout/drc_cleaner/drc_cleaner.py`（使用 LayerStack）

## LcLayout 接口契约（Task 04 完成后）

```python
# Task 04 完成后的 LcLayout 签名
class LcLayout:
    def __init__(self,
                 tech: TechConfig,
                 layout: pya.Layout,
                 placer: TransistorPlacer,
                 router: GraphRouter,
                 debug_routing_graph: bool = False,
                 debug_smt_solver: bool = False):
        self.tech = tech
        self.layer_stack = LayerStack(tech)   # 从 TechConfig 构建 LayerStack
        # ... 其余不变

    def _02_setup_layout(self):
        # 使用 self.layer_stack 替代 layermap
        for layer_def in self.layer_stack.all_layers():
            klayout_layer = self.layout.layer(layer_def.gds_layer, layer_def.gds_purpose)
            self.shapes[layer_def.name] = self.top_cell.shapes(klayout_layer)
```

**关键约束**：
- `LayerStack` 在 `__init__` 中从 `TechConfig` 自动构建，无需作为额外参数传入
- `main()` 函数调用方式不变：`LcLayout(tech=tech, layout=layout, placer=placer, router=router)`
- 所有内部方法（`_02_setup_layout`, `_04_draw_transistors`, `_06_route` 等）通过 `self.layer_stack` 访问层信息
- `routing_graph.py` 的函数增加 `layer_stack` 参数，由 LcLayout 传入
