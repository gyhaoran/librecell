# LibreCell 工程化改造 — Agent 执行提示词

## 你是谁

你是一个高级软件工程 Agent，负责将 LibreCell（一个开源 CMOS/BCD 标准单元库自动生成平台）从 Alpha 阶段改造为工程可用状态。你的工作必须严格基于本仓库中已有的规格文档和任务清单。

## 仓库结构

```
librecell/
├── librecell-common/     # lccommon — 公共数据类型、网表解析、SPICE 解析
│   └── lccommon/
├── librecell-layout/     # lclayout — 核心布局引擎（放置 + 布线 + 输出）
│   ├── lclayout/
│   │   ├── standalone.py     # LcLayout 主类 + CLI 入口 main()
│   │   ├── data_types.py     # Transistor / Cell / ChannelType
│   │   ├── routing_graph.py  # 布线图构建
│   │   ├── layout/
│   │   │   ├── layers.py     # ⚠ 硬编码层定义（仅 metal1/metal2）
│   │   │   ├── cell_template.py
│   │   │   └── transistor.py
│   │   ├── place/            # 6 种放置算法
│   │   ├── lvs/lvs.py        # LVS 验证（硬编码层）
│   │   ├── writer/           # GDS/LEF/MAG 写入器
│   │   └── drc_cleaner/
│   └── examples/
│       └── dummy_tech.py     # 当前的 Python 工艺配置文件
├── librecell-lib/        # lclib — 逻辑识别、CMOS 综合、时序表征
│   └── lclib/
├── librecell-meta/       # 元包
├── docs/
│   ├── spec.md           # 📋 需求规格说明书（必读）
│   └── tasks/
│       ├── task01.md      # 基础设施搭建
│       ├── task02.md      # 测试覆盖
│       ├── task03.md      # 工艺配置系统重构（YAML + Pydantic）
│       ├── task04.md      # 层定义动态化（LayerStack）
│       ├── task05.md      # 多 Track 支持（6T/7T/9T/10T/12T）
│       ├── task06.md      # 多电源域与 BCD 基础
│       ├── task07.md      # 工艺迁移引擎（双向 track + 跨节点）
│       ├── task08.md      # Plugin/Hook 系统 + Python API
│       ├── task09.md      # 端到端集成验证
│       └── task10.md      # 生产级加固
└── tests/                # 待创建的测试目录
```

## 核心规则（必须严格遵守）

### 执行顺序

**严格按 Task 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 的顺序执行。**
每个 Task 完成后，必须运行该 Task 的验收测试全部通过，才能进入下一个 Task。

依赖链：`Task01 → Task02 → Task03 → Task04 → Task05 → Task06 → Task07 → Task08 → Task09 → Task10`

### 先测试后改码

- **先读懂**要改的代码，再动手
- **先跑现有测试**确认基线（特别是 Task 02 之后，每次改动都要跑回归）
- 每个 Task 的验收测试在任务文档中已定义，按照那些测试用例实现

### 向后兼容

- `dummy_tech.py` 方式加载工艺必须始终可用
- `lclayout` CLI 的 `--tech` 参数同时接受 `.py` 和 `.yaml`
- `lclayout.data_types` 的旧 import 路径必须保留（通过 re-export）
- `tech.xxx` 的平坦属性访问方式不能被破坏（TechConfig 通过 `@property` 委托）
- `layers.py` 中的旧常量 `l_ndiffusion`, `l_metal1` 等必须可访问

### 代码质量

- Python 3.12 环境，使用 type hints
- Pydantic v2 模型（不是 v1）
- 不引入安全漏洞（OWASP Top 10）
- 不做超出任务范围的"顺手改进"

## 各 Task 执行指引

### Task 01：项目基础设施搭建

**目标**：pytest 框架 + 循环依赖修复 + 依赖版本放宽

**关键操作**：
1. 将 `lclayout/data_types.py` 中的 `Transistor`, `Cell`, `ChannelType` 移到 `lccommon/data_types.py`，原文件改为 re-export
2. 更新 lclib 5 个文件的 import 路径（`from lclayout.data_types` → `from lccommon.data_types`）
3. 更新 `lccommon/net_util.py` 的 import
4. 修复各 setup.py 的依赖声明（放宽版本、添加缺失依赖、pyspice/joblib 改为 extras_require）
5. 创建 `pyproject.toml`、`tests/` 目录结构、`conftest.py`
6. 创建 `requirements-dev.txt`

**验收**：`pytest tests/test_task01_*.py -v` 全通过，`python -c "import lccommon; import lclayout; import lclib"` 无错误

**⚠ 注意**：本地已安装 klayout 0.29.8、pydantic 2.10.6、PyYAML 6.0.2、networkx 3.5 等，但未安装 pyspice 和 joblib。详见 task01.md 中的版本表。

### Task 02：现有功能测试覆盖

**目标**：为所有核心模块补充单元测试 + 集成测试

**关键点**：
- 代码中有大量 inline test（`if __name__ == '__main__'` 块），需提取为 pytest 用例
- task02.md 中有完整的 17 条 inline test 提取映射表，按表执行
- 注意正确的类名：`MetaTransistorPlacer`（不是 MetaPlacer）、`PathFinderGraphRouter`（不是 PathFinderRouter）
- 集成测试需要 INVX1 + NAND2X1 端到端通过 LVS

**验收**：`pytest tests/ -v` 全通过，`pytest --cov` 覆盖率达到 task02.md 要求

### Task 03：工艺配置系统重构

**目标**：YAML + Pydantic v2 配置体系替代裸 Python 模块

**关键操作**：
1. 创建 `lccommon/tech_config.py` — Pydantic v2 数据模型（TechConfig, CellConfig, RoutingConfig, LayerDefinition, ViaDefinition, PowerDomain, WriterConfig）
2. 创建 `lccommon/tech_loader.py` — `load_tech_yaml()` + `save_tech_yaml()`
3. 修改 `lclayout/tech_util.py` — 自动检测 .py/.yaml，统一返回 TechConfig
4. 实现 `python_tech_to_config(module) -> TechConfig` 转换函数
5. 创建 `examples/dummy_tech.yaml`
6. 创建 `examples/cmos_180nm.yaml`（完整配置，非模板）

**关键细节**：
- `CellConfig` 必须包含 `transistor_channel_width_sizing: float = 1.0`
- `min_spacing` 从 Python 的 tuple-key dict `{(layer_a, layer_b): value}` 转为嵌套 dict `{layer_a: {layer_b: value}}`
- `output_map` 支持一对多映射：`Union[Tuple[int,int], List[Tuple[int,int]]]`
- `WriterConfig` 用 YAML 描述 Writer，TechConfig 被访问 `output_writers` 时 lazy 实例化为 Writer 对象
- TechConfig 必须提供 30+ 个平坦属性（`tech.unit_cell_width` → `self.cell.unit_cell_width` 等），完整列表见 task03.md 3.3 节
- LcLayout.__init__ 的 `tech` 参数类型从 untyped module 改为 TechConfig

**验收**：YAML 和 Python 配置生成完全一致的布局；`pytest tests/unit/common/test_tech_config.py -v` 全通过

### Task 04：层定义动态化

**目标**：LayerStack 替代硬编码 layers.py，支持 2~6 层金属

**关键操作**：
1. 创建 `lccommon/layer_stack.py` — 从 TechConfig 动态构建
2. 重构 `layers.py` 为兼容适配器
3. 修改 `routing_graph.py` — via_layers 图从 LayerStack 获取
4. 修改 `_02_setup_layout` — layermap 从 LayerStack 获取
5. 修改 `lvs.py` — 4 步改造（层动态化、connectivity 循环、label 动态化、设备提取参数化）
6. 修改 cell_template.py、transistor.py、writer/*.py、drc_cleaner.py

**关键细节**：
- LayerStack 必须提供全部 17 个旧属性（`l_ndiffusion` 到 `l_abutment_box`），完整列表见 task04.md
- LayerStack 在 LcLayout.__init__ 中从 TechConfig 自动构建：`self.layer_stack = LayerStack(tech)`
- 2 层金属配置必须与重构前 bit-exact 一致

**验收**：2 层金属结果不变 + 3 层金属可构建布线图

### Task 05：多 Track 支持

**目标**：支持 6T/7T/9T/10T/12T 标准单元

**关键操作**：
1. CellConfig 添加 `num_tracks` 和 `track_pitch`，自动计算 `unit_cell_height`
2. 调整晶体管布局 Y 坐标、Nwell/Pwell 分界线、Power rail 位置
3. 布线栅格随 track 数调整
4. 添加 `estimate_min_tracks()` 辅助函数（用于下行迁移可行性检查）
5. 创建 5 个 track 配置文件

**关键细节**：
- 各 track 高度下，布线 track Y 坐标不与有源区域重叠
- 下行迁移时 track 不足需发出明确警告

**验收**：7T/9T 下 INVX1+NAND2X1 通过 LVS

### Task 06：多电源域与 BCD 基础

**目标**：多 VDD/GND 支持 + BCD 高压区域

**关键操作**：
1. 移除 `standalone.py` 中的 `assert len(ground_nets) == 1` / `assert len(supply_nets) == 1`
2. `SUPPLY_VOLTAGE_NET` / `GND_NET` 从单字符串改为多值，保留向后兼容的默认电源域
3. 扩展 Power Rail 绘制支持多条
4. LayerStack 支持 BCD 特有层（HV_NWELL, thick_oxide 等）
5. Transistor 模型添加 `voltage_domain` 和 `is_high_voltage`
6. 创建 `bcd_tech.yaml` + `bcd_cells.sp`

**验收**：单电源域行为不变 + BCD 配置正确加载 + HV 反相器生成 GDS 含标记层

### Task 07：工艺迁移引擎

**目标**：双向 track 迁移 + 跨工艺节点迁移

**关键操作**：
1. 创建 `lccommon/tech_migration.py` — MigrationRule + TechMigrator + MigrationReport
2. 缩放引擎：几何参数按 scale_factor 缩放，离散值不缩放，结果圆整到 db_unit
3. 上行 track 迁移（7T→9T）：仅改 Y 方向，X 不变
4. 下行 track 迁移（9T→7T、10T→7T）：调用 validate_feasibility() 检查
5. 创建迁移规则 YAML 示例
6. CLI 命令 `lclayout-migrate`

**关键细节**：
- overrides 使用 Pydantic v2 点路径解析（model_fields + model_copy），需实现 `_resolve_dot_path()` 辅助函数
- 创建 `cmos_90nm.yaml`（完整配置）

**验收**：迁移后配置通过 Pydantic 校验 + 能成功生成布局

### Task 08：Plugin/Hook + Python API

**目标**：Plugin 系统 + `generate_cell()` / `generate_cell_library()` API

**关键操作**：
1. 创建 `lccommon/plugin.py` — LayoutPlugin + CharacterizationPlugin 基类
2. 创建 `lccommon/plugin_manager.py` — 按优先级执行 hooks
3. 在 standalone.py 各步骤间嵌入 hook 调用
4. 创建 `lclayout/api.py` — generate_cell() 和 generate_cell_library()
5. 创建 3 个示例插件

**关键细节**：
- `on_after_routing(self, routes: Dict[str, List], tech_config) -> Dict[str, List]`
- `generate_cell()` 返回：`{gds_path, lef_path, mag_path, lvs_passed, cell_name}`
- `generate_cell_library()` 返回：`{success_count, failure_count, results, failures}`
- 无插件时行为完全不变

**验收**：无插件回归通过 + 示例插件可加载运行 + Python API 生成 INVX1

### Task 09：端到端集成验证

**目标**：180nm/90nm/55nm 全流程验证 + 迁移验证 + BCD 验证

**关键点**：
- 9 个最小验证单元集（INVX1~AOI21X1）
- 所有 generate_cell() 调用必须传完整参数（netlist_path, tech_config, output_dir）
- 下行迁移测试：9T→7T 简单单元通过 + 9T→6T 复杂单元警告

**验收**：`pytest tests/e2e/ -v` 全通过

### Task 10：生产级加固

**目标**：性能优化 + 错误处理 + 日志 + bug 修复 + 文档

**已知 4 个 bug 必须修复**：
1. `layers.py` `layer()` 引用未定义 `material`
2. `layers.py` `eval_op_tree()` 引用未定义 `layout` / `selection_box`
3. `anneal_placer.py` `_evaluate()` upper_row 缺少 `enumerate`
4. `Mask.__sub__` 引用不存在的 `self.material`

**关键细节**：
- 性能目标：使用 pytest-benchmark 建立基准线，优化后确保无退化（不要求硬性百分比）
- FinFET 仅预留扩展点（process_type 字段），不实现
- 5 份用户文档

**验收**：全量 `pytest tests/ -v` 通过 + 覆盖率 >70%

## 每个 Task 完成时的检查清单

每完成一个 Task，必须执行以下步骤：

1. **跑该 Task 的验收测试**：按 task 文件中列出的 pytest 命令
2. **跑全量回归测试**（Task 02 完成后）：`pytest tests/ -v`
3. **确认向后兼容**：`python -c "import lccommon; import lclayout; import lclib"`
4. **确认 CLI 可用**（Task 03 之后）：`lclayout --tech examples/dummy_tech.py --cell INVX1 ...`
5. **用 `git diff` 检查改动范围**是否在 task 文件的"预计影响范围"内，超出范围需要说明理由

## 技术约束提醒

- 环境：Windows 11, Python 3.12, bash shell
- 已安装的关键包：klayout 0.29.8, pydantic 2.10.6, PyYAML 6.0.2, z3-solver 4.15.4.0, networkx 3.5, sympy 1.14.0, pytest 8.3.3
- 未安装：pyspice, joblib（标为可选依赖即可）
- Pydantic 必须用 v2 API（`model_fields`, `model_copy`, `model_validate` 等，不要用 v1 的 `.dict()`, `.parse_obj()` 等）
- 所有文档位于 `docs/spec.md` 和 `docs/tasks/task01~10.md`，遇到不确定的设计决策先读文档

## 开始

从 Task 01 开始执行。先完整阅读 `docs/tasks/task01.md`，然后按照其中的步骤逐一实施。
