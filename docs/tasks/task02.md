# Task 02: 现有功能测试覆盖

## 目标

为 LibreCell 现有核心功能补充全面的单元测试（UT）和功能测试（FT），建立回归测试安全网。后续所有重构都依赖这个测试网保障不引入回归。

## 前置条件

- Task 01 完成（pytest 框架可用，包可正常导入）

## 详细任务

### 2.1 数据类型与工具函数测试

**测试对象**：`lccommon/data_types.py`, `lccommon/net_util.py`, `lccommon/spice_parser.py`

**测试用例**：
```python
# tests/unit/common/test_data_types.py

def test_transistor_creation():
    """Transistor namedtuple 正确创建"""

def test_channel_type_enum():
    """ChannelType 包含 NMOS 和 PMOS"""

def test_cell_structure():
    """Cell 包含 upper 和 lower 行"""

# tests/unit/common/test_net_util.py

def test_is_ground_net():
    """识别 gnd/vss/vgnd 等接地网络"""
    assert is_ground_net('gnd') == True
    assert is_ground_net('vss') == True
    assert is_ground_net('signal_a') == False

def test_is_supply_net():
    """识别 vdd/vcc/vpwr 等电源网络"""

def test_get_io_pins():
    """从 pin 列表中过滤出 I/O pin（排除电源）"""

def test_load_transistor_netlist_inverter():
    """从 SPICE 文件加载反相器网表"""

def test_load_transistor_netlist_nand2():
    """从 SPICE 文件加载 NAND2 网表"""

# tests/unit/common/test_spice_parser.py

def test_parse_mosfet():
    """解析 MOSFET 实例"""

def test_parse_subcircuit():
    """解析 .subckt 定义"""

def test_parse_include():
    """解析 .include 指令"""

def test_parse_full_netlist():
    """解析完整的标准单元网表"""
```

### 2.2 放置算法测试

**测试对象**：`lclayout/place/` 下所有放置器

**测试用例**：
```python
# tests/unit/layout/test_placers.py

import pytest
from lccommon.data_types import Transistor, ChannelType

@pytest.fixture
def inverter_netlist():
    """INV 晶体管列表"""

@pytest.fixture
def nand2_netlist():
    """NAND2 晶体管列表"""

class TestEulerPlacer:
    def test_place_inverter(self, inverter_netlist):
        """EulerPlacer 能放置反相器"""

    def test_place_nand2(self, nand2_netlist):
        """EulerPlacer 能放置 NAND2"""

    def test_placement_has_two_rows(self, inverter_netlist):
        """放置结果包含 upper 和 lower 两行"""

    def test_pmos_in_upper_nmos_in_lower(self, nand2_netlist):
        """PMOS 在上行，NMOS 在下行"""

class TestHierarchicalPlacer:
    def test_place_inverter(self, inverter_netlist):
        """HierarchicalPlacer 能放置反相器"""

    def test_place_complex_cell(self):
        """HierarchicalPlacer 能处理复杂单元（如 FAX1）"""

class TestMetaTransistorPlacer:
    def test_auto_selects_euler_for_simple(self, inverter_netlist):
        """MetaTransistorPlacer 对简单单元选择 EulerPlacer"""

    def test_auto_selects_hierarchical_for_complex(self):
        """MetaTransistorPlacer 对复杂单元选择 HierarchicalPlacer"""

class TestSMTPlacer:
    @pytest.mark.slow
    def test_place_nand2(self, nand2_netlist):
        """SMTPlacer 能放置 NAND2"""

# tests/unit/layout/test_euler_tours.py

def test_construct_even_degree_graphs():
    """构建偶度数图"""

def test_find_euler_tours_simple():
    """简单图找到 Euler 回路"""

def test_wiring_length_bbox():
    """线长包围盒计算正确"""
```

### 2.3 布线算法测试

**测试对象**：`lclayout/graphrouter/`

**测试用例**：
```python
# tests/unit/layout/test_routers.py

class TestDijkstraRouter:
    def test_route_two_terminals(self):
        """两点之间找到最短路径（DijkstraRouter 是 SignalRouter，处理单信号路径）"""

    def test_no_path_raises(self):
        """无路径时抛出异常"""

class TestApproxSteinerTreeRouter:
    def test_route_three_terminals(self):
        """三端口 Steiner 树（ApproxSteinerTreeRouter 处理多端口信号）"""

class TestPathFinderGraphRouter:
    def test_route_single_net(self):
        """单信号布线"""

    def test_route_two_nets_no_conflict(self):
        """两信号无冲突布线"""

    def test_route_two_nets_with_conflict(self):
        """两信号有冲突时协商解决"""

    def test_convergence(self):
        """PathFinderGraphRouter 在合理迭代次数内收敛"""

class TestHVGraphRouter:
    def test_penalizes_direction_change(self):
        """HVGraphRouter 方向改变产生额外代价"""
```

### 2.4 布局流水线测试（集成测试）

**测试对象**：`lclayout/standalone.py` 的 `LcLayout` 类

**测试用例**：
```python
# tests/integration/test_layout_pipeline.py

@pytest.mark.integration
class TestLayoutPipeline:
    def test_generate_inverter_gds(self, dummy_tech, tmp_output_dir):
        """生成 INVX1 的 GDS 文件"""
        # 验证 GDS 文件存在且非空

    def test_generate_nand2_gds(self, dummy_tech, tmp_output_dir):
        """生成 NAND2X1 的 GDS 文件"""

    def test_generate_lef(self, dummy_tech, tmp_output_dir):
        """生成 LEF 文件且包含 MACRO 定义"""

    def test_lvs_pass(self, dummy_tech, tmp_output_dir):
        """生成的布局通过 LVS 验证"""

    def test_placement_save_load(self, dummy_tech, tmp_output_dir):
        """放置结果可保存为 JSON 并重新加载"""
```

### 2.5 Logic 模块测试

**测试对象**：`lclib/logic/`

**策略：提取现有 inline test 函数**

代码库中散落着大量 inline test 函数（在源文件中定义但非 pytest 可发现的）。应优先提取这些函数为 pytest 测试，而不是从零编写，以降低工作量并复用已验证的逻辑。

需提取的 inline test 函数清单：

| 源文件 | 函数名 | 提取为 |
|-------|-------|-------|
| `lclib/logic/functional_abstraction.py` | `test_find_input_gates` | `test_functional_abstraction.py::test_find_input_gates` |
| 同上 | `test_complex_cmos_graph_to_formula` | 同上 |
| 同上 | `test_resolve_intermediate_variables` | 同上 |
| 同上 | `test_analyze_circuit_graph` | 同上 |
| 同上 | `test_analyze_circuit_graph_transmission_gate_xor` | 同上 |
| 同上 | `test_analyze_circuit_graph_mux2` | 同上 |
| 同上 | `test_analyze_circuit_graph_latch` | 同上 |
| 同上 | `test_analyze_circuit_graph_set_reset_nand` | 同上 |
| 同上 | `test_analyze_circuit_graph_dff_pos` | 同上 |
| 同上 | `test_analyze_circuit_graph_dff_pos_sync_reset` | 同上 |
| 同上 | `test_analyze_circuit_graph_dff_pos_scan` | 同上 |
| `lclib/logic/seq_recognition.py` | `test_find_boolean_isomorphism` | `test_seq_recognition.py::test_find_boolean_isomorphism` |
| `lclayout/place/euler_placer.py` | `test_wiring_length_bbox1` | `test_placers.py::test_wiring_length_bbox` |
| `lclayout/place/smt_placer.py` | `test()` | `test_placers.py::test_smt_placer_standalone` |
| `lclayout/graphrouter/pathfinder.py` | `test()` | `test_routers.py::test_pathfinder_standalone` |
| `lclayout/graphrouter/signal_router.py` | `test_dijkstra_router` | `test_routers.py::test_dijkstra_router_standalone` |
| `lccommon/spice_parser.py` | `test_spice_parser` | `test_spice_parser.py::test_spice_parser_legacy` |

提取步骤：
1. 将 inline test 函数原封不动复制到对应 pytest 文件中
2. 去除函数中的 `plt.show()` 等阻塞调用（如有）
3. 添加 pytest 断言替代原有的 print 验证
4. 原文件中的 inline test 保留不删（避免破坏 `if __name__ == '__main__'` 入口）

**测试用例**：
```python
# tests/unit/lib/test_functional_abstraction.py

def test_analyze_inverter():
    """从反相器晶体管网络提取布尔函数 Y = ~A"""

def test_analyze_nand2():
    """从 NAND2 提取 Y = ~(A & B)"""

def test_analyze_nor2():
    """从 NOR2 提取 Y = ~(A | B)"""

def test_analyze_mux():
    """从 MUX 提取正确的选择逻辑"""

def test_analyze_latch():
    """识别锁存器中的反馈环路"""

def test_analyze_dff():
    """识别 D 触发器结构"""

# tests/unit/lib/test_cmos_sim.py

def test_evaluate_inverter():
    """开关级仿真反相器"""

def test_evaluate_nand2():
    """开关级仿真 NAND2"""

# tests/unit/lib/test_cmos_synth.py

def test_synthesize_inverter():
    """从 ~A 合成反相器电路"""

def test_synthesize_nand2():
    """从 ~(A&B) 合成 NAND2 电路"""

def test_synthesize_minimal():
    """minimal 合成选择晶体管数更少的方案"""
```

### 2.6 表征模块测试（需 ngspice）

**测试对象**：`lclib/characterization/`

**测试用例**：
```python
# tests/unit/lib/test_piece_wise_linear.py

def test_pwl_interpolation():
    """分段线性波形插值"""

def test_step_wave():
    """阶跃波形生成"""

def test_pulse_wave():
    """脉冲波形生成"""

def test_pwl_arithmetic():
    """PWL 加法和标量乘法"""

# tests/unit/lib/test_timing_util.py

def test_transition_time():
    """测量信号翻转时间"""

def test_slew_time():
    """测量 slew 时间"""

def test_input_to_output_delay():
    """测量输入到输出延迟"""

# tests/integration/test_characterization.py
@pytest.mark.integration
@pytest.mark.slow
class TestCharacterization:
    def test_ngspice_subprocess_basic(self):
        """ngspice 子进程能执行简单仿真"""

    def test_input_capacitance(self):
        """测量输入电容"""

    def test_combinational_timing(self):
        """组合逻辑时序表征"""
```

### 2.7 输出格式测试

**测试对象**：`lclayout/writer/`

**测试用例**：
```python
# tests/unit/layout/test_writers.py

def test_gds_writer_creates_file(tmp_path):
    """GdsWriter 创建有效的 GDS 文件"""

def test_lef_writer_creates_file(tmp_path):
    """LefWriter 创建包含 MACRO 的 LEF 文件"""

def test_lef_writer_pin_geometry(tmp_path):
    """LEF 文件包含正确的 pin 几何信息"""

def test_mag_writer_creates_file(tmp_path):
    """MagWriter 创建有效的 Magic 文件"""
```

## 完成标准

- [ ] `pytest tests/unit/ -v` 全部通过（预计 60+ 个测试用例）
- [ ] `pytest tests/integration/ -v` 全部通过（预计 10+ 个测试用例）
- [ ] `pytest --cov=lccommon --cov=lclayout --cov=lclib --cov-report=term` 显示：
  - `lccommon` 覆盖率 > 60%
  - `lclayout` 核心模块（data_types, place, graphrouter）覆盖率 > 50%
  - `lclib/logic` 覆盖率 > 60%
- [ ] 现有 17 个内联 `test_*` 函数全部提取到 `tests/` 目录（见 2.5 中的清单）
- [ ] 所有测试可在无 ngspice 环境下跳过 integration 测试正常运行：`pytest tests/unit/ -v`

## 预计影响范围

- `tests/` 目录下所有新文件
- `tests/conftest.py`（扩展 fixtures）
- 不修改任何生产代码（仅增加测试）

## 注意事项

- 集成测试（需要 ngspice/klayout）标记为 `@pytest.mark.integration`
- 慢速测试（SMT 求解器等）标记为 `@pytest.mark.slow`
- 测试用 SPICE 网表从 `examples/cells.sp` 和 `test_data/` 中获取
- 将现有代码中的 17 个内联测试函数（见 2.5 中的清单）**提取**到 pytest 测试文件中，保持原逻辑不变，去除 `plt.show()` 等阻塞调用
- 部分 inline test 函数使用了 `lclib/logic/functional_abstraction.py` 中的 `NetlistGen` 类来生成测试网表，提取时需将其作为 pytest fixture
