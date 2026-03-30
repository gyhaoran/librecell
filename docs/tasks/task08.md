# Task 08: 脚本化二次开发接口

## 目标

提供 Plugin/Hook 系统和 Python API，使 SE 工程师无需修改核心布局布线算法，仅通过配置 + Python 脚本完成工艺适配和定制化。

## 前置条件

- Task 06 完成（多电源域与 BCD 基础）

## 详细任务

### 8.1 设计 Plugin 接口

**操作**：创建 `lccommon/plugin.py`

```python
from abc import ABC, abstractmethod
from typing import List, Optional

class LayoutPlugin(ABC):
    """布局生成插件基类"""

    @property
    def name(self) -> str: ...

    @property
    def priority(self) -> int:
        """执行优先级，数字越小越先执行"""
        return 100

    def on_before_placement(self, transistors, tech_config):
        """放置前钩子：可修改晶体管列表"""
        return transistors

    def on_after_placement(self, cell, tech_config):
        """放置后钩子：可调整放置结果"""
        return cell

    def on_before_routing(self, routing_graph, tech_config):
        """布线前钩子：可修改布线图"""
        return routing_graph

    def on_after_routing(self, routes: Dict[str, List], tech_config) -> Dict[str, List]:
        """布线后钩子：可修改布线结果

        Args:
            routes: 信号名 -> 布线路径列表的映射（与 _06_route() 返回的 routing_trees 结构一致）
            tech_config: 工艺配置对象
        Returns:
            修改后的 routes 字典，结构与输入相同
        """
        return routes

    def on_before_output(self, layout, tech_config):
        """输出前钩子：可添加额外形状"""
        return layout

    def on_post_process(self, layout, tech_config):
        """后处理钩子：自定义 DRC 修正等"""
        return layout

class CharacterizationPlugin(ABC):
    """表征插件基类"""

    def on_before_simulation(self, spice_deck, tech_config):
        """仿真前钩子：可修改 SPICE 卡片"""
        return spice_deck

    def on_after_simulation(self, results, tech_config):
        """仿真后钩子：可处理仿真结果"""
        return results
```

### 8.2 实现 Plugin 注册和加载机制

**操作**：

- Plugin 通过 TechConfig 中的 `plugins` 字段指定
- 支持 Python 文件路径或模块路径
- 自动发现和加载

```yaml
# 在工艺配置中指定插件
plugins:
  - path: "./my_plugins/well_tap_inserter.py"
    class: "WellTapInserterPlugin"
    config:
      tap_interval: 10  # 每 10 个单元宽度插入一个 well tap
  - module: "my_company.plugins.drc_fixer"
    class: "CustomDrcPlugin"
```

### 8.3 实现 Plugin 管理器

**操作**：创建 `lccommon/plugin_manager.py`

```python
class PluginManager:
    def __init__(self):
        self.plugins: List[LayoutPlugin] = []

    def load_plugins(self, tech_config: TechConfig): ...

    def execute_hook(self, hook_name: str, *args, **kwargs):
        """按优先级顺序执行所有插件的指定钩子"""
```

### 8.4 在核心流水线中嵌入 Hook 点

**操作**：修改 `lclayout/standalone.py`

- 在 `create_cell_layout()` 的各步骤之间插入 hook 调用
- Hook 点与 Plugin 接口方法一一对应
- 无插件时行为完全不变

### 8.5 创建示例插件

**操作**：创建 `examples/plugins/` 目录

```python
# examples/plugins/well_tap_inserter.py
class WellTapInserterPlugin(LayoutPlugin):
    """在布局中插入 well tap"""

    def on_after_placement(self, cell, tech_config):
        # 在指定间隔插入 well tap 占位
        ...

# examples/plugins/custom_spacing_checker.py
class CustomSpacingCheckerPlugin(LayoutPlugin):
    """自定义间距检查"""

    def on_before_output(self, layout, tech_config):
        # 检查并报告自定义间距规则
        ...

# examples/plugins/power_grid_enhancer.py
class PowerGridEnhancerPlugin(LayoutPlugin):
    """增强电源网格"""

    def on_post_process(self, layout, tech_config):
        # 在空闲区域添加电源 via 和 strap
        ...
```

### 8.6 提供 Python API（非 CLI 使用）

**操作**：创建 `lclayout/api.py`

```python
def generate_cell(
    cell_name: str,
    netlist_path: str,
    tech_config: Union[str, TechConfig],
    output_dir: str,
    placer: str = "meta",
    router: str = "dijkstra",
    plugins: Optional[List[LayoutPlugin]] = None,
) -> dict:
    """
    Python API：生成单个标准单元

    Returns:
        dict with keys:
        - gds_path: str — 生成的 GDS 文件路径
        - lef_path: str — 生成的 LEF 文件路径
        - mag_path: str — 生成的 MAG 文件路径（如有）
        - lvs_passed: bool — LVS 是否通过
        - cell_name: str — 单元名称
    """

def generate_cell_library(
    cell_list: List[str],
    netlist_path: str,
    tech_config: Union[str, TechConfig],
    output_dir: str,
    parallel: int = 1,
    continue_on_error: bool = False,
    **kwargs,
) -> dict:
    """
    Python API：批量生成标准单元库

    Returns:
        dict with keys:
        - success_count: int — 成功生成的单元数
        - failure_count: int — 失败的单元数
        - results: Dict[str, dict] — 每个单元的 generate_cell 返回值
        - failures: Dict[str, str] — 失败单元名 -> 错误消息
    """
```

**验收测试**：
```python
# tests/unit/test_plugin_system.py

class TestPluginInterface:
    def test_plugin_base_class(self):
        """Plugin 基类方法可被继承"""

    def test_plugin_default_hooks_passthrough(self):
        """默认 hook 实现直接传递参数"""

    def test_plugin_priority_ordering(self):
        """Plugin 按优先级排序"""

class TestPluginManager:
    def test_load_plugin_from_path(self):
        """从文件路径加载插件"""

    def test_load_plugin_from_module(self):
        """从模块路径加载插件"""

    def test_execute_hooks_in_order(self):
        """按优先级执行 hooks"""

    def test_no_plugins_no_effect(self):
        """无插件时行为不变"""

    def test_plugin_config_passed(self):
        """插件配置正确传递"""

class TestPluginExamples:
    def test_well_tap_plugin_loads(self):
        """well tap 插件可加载"""

    def test_spacing_checker_plugin_loads(self):
        """间距检查插件可加载"""

# tests/unit/layout/test_python_api.py

class TestPythonAPI:
    def test_generate_cell_basic(self, tmp_output_dir):
        """Python API 生成单个单元"""
        result = generate_cell(
            cell_name="INVX1",
            netlist_path="examples/cells.sp",
            tech_config="examples/dummy_tech.yaml",
            output_dir=tmp_output_dir,
        )
        assert result['gds_path'].endswith('.gds')
        assert os.path.exists(result['gds_path'])

    def test_generate_cell_with_plugin(self, tmp_output_dir):
        """Python API 配合插件使用"""

    def test_generate_cell_library(self, tmp_output_dir):
        """批量生成单元库"""

# tests/integration/test_plugin_pipeline.py

@pytest.mark.integration
class TestPluginPipeline:
    def test_plugin_hook_called(self, tmp_output_dir):
        """插件 hook 在流水线中被调用"""

    def test_well_tap_plugin_effect(self, tmp_output_dir):
        """well tap 插件实际插入了 tap"""

    def test_plugin_does_not_break_lvs(self, tmp_output_dir):
        """使用插件后 LVS 仍通过"""
```

## 完成标准

- [ ] `LayoutPlugin` 和 `CharacterizationPlugin` 基类定义完成
- [ ] Plugin 从 YAML 配置自动加载
- [ ] 无插件时所有现有测试仍通过（零影响）
- [ ] 至少 3 个示例插件可正常加载和运行
- [ ] Python API (`generate_cell`, `generate_cell_library`) 可用
- [ ] SE 工程师仅通过 YAML + Plugin 脚本完成定制（有文档示例）
- [ ] `pytest tests/unit/test_plugin_system.py -v` 全部通过
- [ ] `pytest tests/unit/layout/test_python_api.py -v` 全部通过
- [ ] `pytest tests/integration/test_plugin_pipeline.py -v` 全部通过

## 预计影响范围

- `lccommon/plugin.py`（新文件）
- `lccommon/plugin_manager.py`（新文件）
- `lclayout/api.py`（新文件）
- `lclayout/standalone.py`（嵌入 hook 点）
- `examples/plugins/`（新目录，示例插件）
- `lccommon/tech_config.py`（添加 plugins 字段）
