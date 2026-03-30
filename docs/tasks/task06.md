# Task 06: 多电源域与 BCD 基础

## 目标

支持多电源域（多 VDD/GND），为 BCD 工艺奠定基础。支持高压/低压混合单元的布局生成。

## 前置条件

- Task 05 完成（多 Track 支持）

## 详细任务

### 6.1 移除单电源域断言

**操作**：修改 `lclayout/standalone.py` 中的 `_01_load_netlist()`

- 当前代码 `assert len(ground_nets) == 1` 和 `assert len(supply_nets) == 1`（第 275-276 行）
- 改为从 `TechConfig.power_domains` 获取电源网络列表
- 支持多个 VDD（如 VDD_HV, VDD_LV）和多个 GND（如 GND, GNDA）
- 保持默认情况（单 VDD/GND）的行为不变

**关键重构**：`self.SUPPLY_VOLTAGE_NET` 和 `self.GND_NET`（第 278-279 行）当前是**单个字符串**，需要改为支持多电源域的数据结构：

```python
# 当前（单电源域）
self.SUPPLY_VOLTAGE_NET = supply_nets.pop()   # str
self.GND_NET = ground_nets.pop()               # str

# 改造后（多电源域）
self.power_nets = {}  # Dict[str, PowerDomain]
# e.g., {"VDD": PowerDomain(name="core", supply_net="VDD", ground_net="VSS"), ...}
self.supply_nets = supply_nets    # Set[str]，如 {"VDD", "VDDH"}
self.ground_nets = ground_nets    # Set[str]，如 {"VSS"}
# 向后兼容：默认电源域
self.SUPPLY_VOLTAGE_NET = config.power_domains[0].supply_net  # 主电源域
self.GND_NET = config.power_domains[0].ground_net              # 主接地
```

**波及范围**：`standalone.py` 中所有使用 `self.SUPPLY_VOLTAGE_NET` 和 `self.GND_NET` 的位置都需要检查，确保多电源域场景正确工作。主要涉及：
- `_05_draw_cell_template()`：power rail 绘制
- `_06_route()`：电源网络作为 reserved nodes
- `_08_draw_routes()`：电源网络标签

### 6.2 扩展 Power Rail 绘制

**操作**：修改 `lclayout/layout/cell_template.py`

- 支持多条 power rail（不仅是顶部 VDD + 底部 GND）
- BCD 模式下，高压电源 rail 可在不同 Y 位置
- Power rail 宽度可按电源域独立配置

### 6.3 扩展网表加载

**操作**：修改 `lccommon/net_util.py`

- `is_ground_net()` 和 `is_supply_net()` 支持自定义电源名称
- 网表加载时根据 TechConfig 识别电源网络

### 6.4 BCD 工艺层支持

**操作**：在 TechConfig 和 LayerStack 中支持 BCD 特有层

- 高压 N-well（HV_NWELL）
- 高压 P-well（HV_PWELL）
- Drain extension 层
- 深 N-well（DNW）（可选）
- 高压晶体管的 gate oxide 标记层

```yaml
# BCD 工艺配置示例
layers:
  - name: ndiffusion
    gds_layer: 1
    material: diffusion
  - name: pdiffusion
    gds_layer: 2
    material: diffusion
  - name: nwell
    gds_layer: 3
    material: well
  - name: hv_nwell
    gds_layer: 13
    material: well
    description: "High-voltage N-well"
  - name: thick_oxide
    gds_layer: 14
    material: marker
    description: "Thick gate oxide marker for HV transistors"
  # ...

power_domains:
  - name: core
    supply_net: VDD
    ground_net: VSS
    voltage: 1.8
  - name: io_hv
    supply_net: VDDH
    ground_net: VSS
    voltage: 5.0
```

### 6.5 高压晶体管支持

**操作**：扩展 `lccommon/data_types.py` 中的晶体管模型

- 添加 `voltage_domain` 属性（属于哪个电源域）
- 添加 `is_high_voltage` 标志
- 高压晶体管绘制时额外添加 thick_oxide / HV marker 层

### 6.6 BCD 单元模板

**操作**：创建 BCD 工艺的单元模板和示例

- `examples/bcd_tech.yaml` — BCD 工艺配置
- `examples/bcd_cells.sp` — 简单的 BCD 单元网表（HV 反相器、Level Shifter）

**验收测试**：
```python
# tests/unit/layout/test_multi_power.py

class TestMultiPower:
    def test_single_power_domain_default(self):
        """默认单电源域行为不变"""
        config = load_tech_yaml("examples/dummy_tech.yaml")
        assert len(config.power_domains) == 1

    def test_dual_power_domain(self):
        """双电源域配置正确加载"""
        config = load_tech_yaml("examples/bcd_tech.yaml")
        assert len(config.power_domains) == 2

    def test_custom_power_net_names(self):
        """自定义电源网络名称被正确识别"""
        assert is_supply_net("VDDH", config=bcd_config) == True
        assert is_supply_net("VDD", config=bcd_config) == True

    def test_power_rail_positions_bcd(self):
        """BCD 模式下 power rail 位置正确"""

# tests/unit/layout/test_bcd_layers.py

class TestBCDLayers:
    def test_hv_nwell_layer(self):
        """高压 N-well 层存在于 LayerStack"""

    def test_thick_oxide_layer(self):
        """Thick oxide 标记层存在"""

    def test_hv_transistor_markers(self):
        """高压晶体管绘制时包含 thick_oxide 标记"""

# tests/unit/common/test_transistor_model.py

def test_transistor_voltage_domain():
    """晶体管包含电源域属性"""

def test_transistor_is_hv():
    """可标记为高压晶体管"""

# tests/integration/test_bcd_pipeline.py

@pytest.mark.integration
class TestBCDPipeline:
    def test_generate_hv_inverter(self, tmp_output_dir):
        """生成高压反相器布局"""
        # 验证 GDS 包含 thick_oxide 层

    def test_generate_cmos_with_bcd_config(self, tmp_output_dir):
        """BCD 配置下仍能生成普通 CMOS 单元"""

    def test_single_domain_regression(self, tmp_output_dir):
        """单电源域配置回归测试"""

    def test_gds_contains_hv_layers(self, tmp_output_dir):
        """GDS 输出包含高压工艺层"""
```

## 完成标准

- [ ] 单电源域配置（现有 dummy_tech）行为完全不变
- [ ] 双电源域配置能正确加载和校验
- [ ] BCD 工艺层（HV_NWELL, thick_oxide 等）在 LayerStack 中可用
- [ ] 高压晶体管绘制时生成正确的标记层
- [ ] 简单 HV 反相器能生成 GDS（包含 HV 标记层）
- [ ] `pytest tests/unit/layout/test_multi_power.py -v` 全部通过
- [ ] `pytest tests/unit/layout/test_bcd_layers.py -v` 全部通过
- [ ] `pytest tests/integration/test_bcd_pipeline.py -v` 全部通过
- [ ] 所有之前的回归测试通过

## 预计影响范围

- `lccommon/data_types.py`（扩展 Transistor 类，添加 voltage_domain / is_high_voltage 属性）
- `lccommon/net_util.py`（自定义电源名称）
- `lccommon/tech_config.py`（PowerDomain, BCD 层）
- `lccommon/layer_stack.py`（支持 BCD 特有层：HV_NWELL, thick_oxide 等）
- `lclayout/standalone.py`（移除单电源断言，重构 SUPPLY_VOLTAGE_NET/GND_NET 为多值）
- `lclayout/layout/cell_template.py`（多 power rail）
- `lclayout/layout/transistor.py`（HV 晶体管标记）
- `examples/bcd_tech.yaml`（新文件）
- `examples/bcd_cells.sp`（新文件）
