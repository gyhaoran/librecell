# Task 08: 工艺脚本化二次开发体系

## 目标

让用户/SE 工程师能够**仅通过 YAML 配置 + Python 脚本**完成工艺适配，无需修改 LibreCell 核心代码。开放四大能力：

1. **DRC 规则扩展** — 支持自定义 DRC 检查函数（条件间距、EOL 规则、密度检查等）
2. **GDS 输出定制** — 支持输出前的层处理回调（OPC 偏移、填充层生成、标记层注入）
3. **布局流程定制** — 在核心流水线关键节点嵌入用户回调（放置后插入 guard ring、布线后添加 via strap 等）
4. **Python API** — 提供 `generate_cell()` / `generate_cell_library()` 函数式接口，方便脚本批量调用

核心原则：**YAML 描述"是什么"，Python 脚本描述"怎么做"。无脚本时行为完全不变。**

## 前置条件

- Task 06 完成（多电源域与 BCD 基础）

## 设计思路

### 工艺开发目录结构

一个典型的工艺开发项目如下：

```
my_process/
├── tech.yaml                    # 工艺配置（TechConfig）
├── cells.sp                     # 单元网表
├── scripts/                     # 用户 Python 脚本
│   ├── custom_drc.py            # 自定义 DRC 规则
│   ├── layer_postprocess.py     # 输出前层处理
│   └── guard_ring.py            # 布局定制（guard ring 插入）
└── output/                      # 生成结果
```

### 配置与脚本的关系

```yaml
# tech.yaml 中的脚本化扩展
scripts:
  # 自定义 DRC 规则 — 在标准 DRC 之后执行
  custom_drc:
    - path: "./scripts/custom_drc.py"
      function: "check_eol_spacing"       # 函数签名: (shapes, tech_config, layer_stack) -> List[DrcViolation]
    - path: "./scripts/custom_drc.py"
      function: "check_density"

  # 输出前层处理 — 在 GDS/LEF 写入之前执行
  layer_postprocess:
    - path: "./scripts/layer_postprocess.py"
      function: "bias_poly_layer"          # 函数签名: (shapes, tech_config, layer_stack) -> None (修改 shapes)
    - path: "./scripts/layer_postprocess.py"
      function: "add_fill_pattern"

  # 布局流程回调 — 在指定步骤后执行
  on_after_placement:
    - path: "./scripts/guard_ring.py"
      function: "insert_guard_ring"        # 函数签名: (cell, shapes, tech_config) -> cell
  on_after_routing:
    - path: "./scripts/guard_ring.py"
      function: "add_power_straps"         # 函数签名: (routing_trees, shapes, tech_config) -> routing_trees
```

## 详细任务

### 8.1 脚本加载与执行框架

**操作**：创建 `lccommon/script_context.py`

```python
class DrcViolation(BaseModel):
    """DRC 违规描述"""
    rule_name: str           # 规则名称，如 "EOL_SPACING_M1"
    layer: str               # 违规层
    severity: str = "error"  # "error" | "warning"
    message: str             # 可读描述
    bbox: Optional[Tuple[int, int, int, int]] = None  # 违规区域 (x1, y1, x2, y2)

class ScriptEntry(BaseModel):
    """一条脚本配置"""
    path: str                # Python 文件路径（相对于 tech.yaml 或绝对）
    function: str            # 函数名
    config: Dict[str, Any] = {}  # 传递给函数的额外配置

class ScriptConfig(BaseModel):
    """全部脚本配置"""
    custom_drc: List[ScriptEntry] = []
    layer_postprocess: List[ScriptEntry] = []
    on_after_placement: List[ScriptEntry] = []
    on_after_routing: List[ScriptEntry] = []
    on_before_output: List[ScriptEntry] = []

class ScriptContext:
    """脚本执行上下文 — 负责加载和调用用户脚本"""

    def __init__(self, script_config: ScriptConfig, base_dir: str = "."):
        """
        :param script_config: 从 TechConfig.scripts 获取
        :param base_dir: 脚本路径的基准目录（通常是 tech.yaml 所在目录）
        """

    def load_function(self, entry: ScriptEntry) -> Callable:
        """从 ScriptEntry 加载 Python 函数"""
        # 解析路径（相对 base_dir），import 模块，getattr 取函数

    def run_custom_drc(self, shapes, tech_config, layer_stack) -> List[DrcViolation]:
        """执行所有 custom_drc 脚本，汇总违规列表"""

    def run_layer_postprocess(self, shapes, tech_config, layer_stack) -> None:
        """执行所有 layer_postprocess 脚本（原地修改 shapes）"""

    def run_hook(self, hook_name: str, **kwargs) -> Any:
        """执行指定 hook 的所有脚本，链式传递第一个参数"""
```

**关键设计决策**：
- 脚本函数是**普通 Python 函数**，不要求继承基类。降低 SE 工程师的学习成本
- 函数签名明确约定（见下方 8.4 节），通过文档和示例约束
- `config` 字段允许向函数传递额外参数，函数通过 `**kwargs` 接收
- 路径解析：相对路径基于 tech.yaml 所在目录

### 8.2 TechConfig 集成

**操作**：修改 `lccommon/tech_config.py`

- 新增字段：`scripts: ScriptConfig = ScriptConfig()`
- YAML 中 `scripts:` 段可选，缺省时所有回调列表为空
- 新增属性：`has_scripts -> bool`（任意回调列表非空时为 True）

### 8.3 流水线嵌入回调点

**操作**：修改 `lclayout/standalone.py`

在 `LcLayout.__init__` 中构造 `ScriptContext`（如果 `tech.has_scripts`，否则为 None）。

在 `create_cell_layout()` 的关键节点插入条件调用：

```python
# _03_place_transistors 之后:
if self._script_ctx:
    self._abstract_cell = self._script_ctx.run_hook(
        'on_after_placement',
        cell=self._abstract_cell, shapes=self.shapes, tech_config=self.tech
    ) or self._abstract_cell

# _06_route 之后:
if self._script_ctx:
    self._routing_trees = self._script_ctx.run_hook(
        'on_after_routing',
        routing_trees=self._routing_trees, shapes=self.shapes, tech_config=self.tech
    ) or self._routing_trees

# _09_post_process 之后、writer 之前:
if self._script_ctx:
    self._script_ctx.run_layer_postprocess(self.shapes, self.tech, self.layer_stack)
    violations = self._script_ctx.run_custom_drc(self.shapes, self.tech, self.layer_stack)
    for v in violations:
        if v.severity == 'error':
            logger.error("DRC violation: %s — %s", v.rule_name, v.message)
        else:
            logger.warning("DRC warning: %s — %s", v.rule_name, v.message)
```

**无脚本时**：`self._script_ctx` 为 None，所有 `if` 短路，行为零变化。

### 8.4 用户脚本函数签名约定

| 回调类型 | 函数签名 | 说明 |
|---------|----------|------|
| `custom_drc` | `(shapes, tech_config, layer_stack, **kwargs) -> List[DrcViolation]` | 返回违规列表 |
| `layer_postprocess` | `(shapes, tech_config, layer_stack, **kwargs) -> None` | 原地修改 shapes |
| `on_after_placement` | `(cell, shapes, tech_config, **kwargs) -> cell` | 可返回修改后的 Cell |
| `on_after_routing` | `(routing_trees, shapes, tech_config, **kwargs) -> routing_trees` | 可返回修改后的路由树 |
| `on_before_output` | `(layout, shapes, tech_config, **kwargs) -> None` | 输出前的最终修改 |

其中：
- `shapes: Dict[str, pya.Shapes]` — 层名→形状的可修改字典
- `tech_config: TechConfig` — 完整工艺配置
- `layer_stack: LayerStack` — 层信息（layermap、via_layers 等）
- `**kwargs` — 接收 ScriptEntry 中的 `config` 字段

### 8.5 示例脚本

**操作**：创建 `examples/scripts/` 目录

```python
# examples/scripts/custom_drc.py
"""示例：自定义 DRC 规则 — EOL 间距检查"""

def check_eol_spacing(shapes, tech_config, layer_stack, min_eol_spacing=100, **kwargs):
    """检查 metal1 层的 End-of-Line 间距"""
    from lccommon.script_context import DrcViolation
    violations = []
    # ... 遍历 shapes['metal1'] 检查线端间距 ...
    return violations


def check_density(shapes, tech_config, layer_stack, max_density=0.8, **kwargs):
    """检查金属层密度是否超标"""
    from lccommon.script_context import DrcViolation
    violations = []
    # ... 计算每层面积占比 ...
    return violations
```

```python
# examples/scripts/layer_postprocess.py
"""示例：输出前层处理 — poly 偏移、填充层"""

def bias_poly_layer(shapes, tech_config, layer_stack, bias_amount=5, **kwargs):
    """对 poly 层做 OPC 偏移（示例：各边外扩 bias_amount）"""
    # ... 遍历 shapes['poly']，对每个 polygon 做 sized(bias_amount) ...
    pass


def add_fill_pattern(shapes, tech_config, layer_stack, fill_layer='metal1_fill', **kwargs):
    """在空白区域添加金属填充图案"""
    # ... 计算空白区域，插入填充 shapes ...
    pass
```

```python
# examples/scripts/guard_ring.py
"""示例：guard ring 插入"""

def insert_guard_ring(cell, shapes, tech_config, ring_width=200, **kwargs):
    """在单元周围插入 guard ring"""
    # ... 在 shapes['ndiffusion'] 和 shapes['pdiff_contact'] 中插入环形结构 ...
    return cell
```

### 8.6 Python API

**操作**：创建 `lclayout/api.py`

```python
def generate_cell(
    cell_name: str,
    netlist_path: str,
    tech_config: Union[str, TechConfig],
    output_dir: str,
    placer: str = "meta",
    router: str = "dijkstra",
) -> dict:
    """
    生成单个标准单元。

    Returns:
        {
            "cell_name": str,
            "gds_path": str,    # 生成的 GDS 路径（如 writer 包含 GDS）
            "lef_path": str,    # LEF 路径（如有）
            "lvs_passed": bool, # LVS 结果
            "drc_violations": list,  # 自定义 DRC 违规（如有脚本）
        }
    """

def generate_cell_library(
    cell_list: List[str],
    netlist_path: str,
    tech_config: Union[str, TechConfig],
    output_dir: str,
    continue_on_error: bool = False,
    **kwargs,
) -> dict:
    """
    批量生成标准单元库。

    Returns:
        {
            "success_count": int,
            "failure_count": int,
            "results": {cell_name: generate_cell_result, ...},
            "failures": {cell_name: error_message, ...},
        }
    """
```

## 验收测试

```python
# tests/unit/common/test_script_context.py

class TestScriptConfig:
    def test_empty_scripts_default(self):
        """无脚本配置时所有列表为空"""

    def test_has_scripts_false_by_default(self):
        """默认 tech 无脚本"""

    def test_load_scripts_from_yaml(self):
        """从 YAML 加载脚本配置"""

class TestScriptContext:
    def test_load_function_from_file(self):
        """从 Python 文件加载函数"""

    def test_load_function_not_found_raises(self):
        """函数不存在时抛出明确错误"""

    def test_run_custom_drc_empty(self):
        """无 DRC 脚本时返回空列表"""

    def test_run_custom_drc_collects_violations(self):
        """DRC 脚本返回的违规被正确收集"""

    def test_run_layer_postprocess(self):
        """layer_postprocess 脚本被调用"""

    def test_run_hook_chain(self):
        """多个同名 hook 链式执行"""

    def test_config_passed_to_function(self):
        """ScriptEntry.config 作为 kwargs 传递给函数"""

    def test_no_scripts_no_effect(self):
        """无脚本时流水线行为完全不变"""

# tests/unit/layout/test_python_api.py

class TestPythonAPI:
    def test_generate_cell_basic(self, tmp_output_dir):
        """Python API 生成 INVX1"""

    def test_generate_cell_returns_dict(self, tmp_output_dir):
        """返回值包含必要字段"""

    def test_generate_cell_library_basic(self, tmp_output_dir):
        """批量生成多个单元"""

    def test_generate_cell_library_continue_on_error(self, tmp_output_dir):
        """continue_on_error=True 时不因单个失败中断"""

# tests/integration/test_script_pipeline.py

@pytest.mark.integration
class TestScriptPipeline:
    def test_custom_drc_script_runs(self, tmp_output_dir):
        """自定义 DRC 脚本在流水线中被调用"""

    def test_layer_postprocess_modifies_shapes(self, tmp_output_dir):
        """layer_postprocess 脚本实际修改了输出"""

    def test_no_scripts_regression(self, tmp_output_dir):
        """无脚本配置时完整流水线回归通过"""

    def test_script_error_reported_clearly(self, tmp_output_dir):
        """脚本抛出异常时报告清晰的错误信息"""
```

## 完成标准

- [ ] `ScriptContext` 可从 YAML 配置加载并执行用户 Python 函数
- [ ] `TechConfig.scripts` 字段可选，缺省时零影响
- [ ] `custom_drc` 脚本在后处理阶段被调用，违规被收集和报告
- [ ] `layer_postprocess` 脚本在 writer 之前被调用
- [ ] `on_after_placement` / `on_after_routing` 回调在流水线对应位置被调用
- [ ] 无脚本时所有现有测试仍通过
- [ ] 3 个示例脚本可加载运行
- [ ] Python API (`generate_cell`, `generate_cell_library`) 可用
- [ ] `pytest tests/unit/common/test_script_context.py -v` 全部通过
- [ ] `pytest tests/unit/layout/test_python_api.py -v` 全部通过
- [ ] `pytest tests/integration/test_script_pipeline.py -v` 全部通过

## 预计影响范围

- `lccommon/script_context.py`（新文件 — 脚本加载与执行框架）
- `lccommon/tech_config.py`（添加 `scripts: ScriptConfig` 字段）
- `lclayout/standalone.py`（嵌入回调点）
- `lclayout/api.py`（新文件 — Python API）
- `examples/scripts/`（新目录 — 3 个示例脚本）
- `librecell-layout/setup.py`（无变化）

## 与原 task08 的区别

| 维度 | 原方案（Plugin 系统） | 新方案（工艺脚本化） |
|------|----------------------|---------------------|
| 用户写什么 | 继承 `LayoutPlugin` 基类 | 普通 Python 函数 |
| 配置方式 | YAML 指定类路径 + class | YAML 指定文件路径 + function |
| 学习成本 | 需理解 OOP 继承、ABC | 只需写函数，签名有约定 |
| 扩展重点 | 通用 hook 系统 | DRC/GDS/布局/布线四大工艺开发场景 |
| DRC 扩展 | 无专门支持 | `custom_drc` 回调 + `DrcViolation` 模型 |
| GDS 输出 | 无专门支持 | `layer_postprocess` 回调 |
| API | `generate_cell()` | `generate_cell()` + `generate_cell_library()` |
