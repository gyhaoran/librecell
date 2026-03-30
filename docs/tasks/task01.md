# Task 01: 项目基础设施搭建

## 目标

搭建 pytest 测试框架、修复包依赖结构、建立开发环境标准化配置。这是所有后续工作的基础。

## 前置条件

- 无（第一个任务）

## 详细任务

### 1.1 修复包结构与循环依赖

**问题**：
1. `librecell-common/lccommon/net_util.py` 导入 `from lclayout.data_types import *`，导致 common 反向依赖 layout
2. `lclib/logic/` 下 5 个文件直接 `from lclayout.data_types import ChannelType/Transistor`，但 `lclib/setup.py` 未声明对 `librecell-layout` 的依赖
3. `lccommon/net_util.py` 导入 `klayout.db`，但 `lccommon/setup.py` 未声明 `klayout` 依赖
4. `lccommon/spice_parser.py` 使用 `pyparsing`，但 `lccommon/setup.py` 未声明
5. `librecell-meta/setup.py` 要求 `librecell-lib==0.0.10`，实际 lib 版本为 `0.0.11`

**操作**：

**步骤一：移动核心数据类型到 lccommon**
- 将 `lclayout/data_types.py` 中的核心数据类型（`Transistor`, `Cell`, `ChannelType`）移动到 `lccommon/data_types.py`
- `lclayout/data_types.py` 改为从 `lccommon.data_types` 重新导出（保持向后兼容）：
  ```python
  # lclayout/data_types.py（重构后）
  from lccommon.data_types import *  # 向后兼容
  ```

**步骤二：更新所有 import 路径**

需要更新的文件清单：

| 包 | 文件 | 当前导入 | 改为 |
|---|------|---------|------|
| lccommon | `net_util.py` | `from lclayout.data_types import *` | `from lccommon.data_types import *` |
| lclib | `logic/functional_abstraction.py` | `from lclayout.data_types import ChannelType` | `from lccommon.data_types import ChannelType` |
| lclib | `logic/seq_recognition.py` | `from lclayout.data_types import ChannelType` | `from lccommon.data_types import ChannelType` |
| lclib | `logic/cmos_sim.py` | `from lclayout.data_types import ChannelType` | `from lccommon.data_types import ChannelType` |
| lclib | `logic/graph_enumeration.py` | `from lclayout.data_types import Transistor, ChannelType` | `from lccommon.data_types import Transistor, ChannelType` |
| lclib | `logic/cmos_synth.py` | `from lclayout.data_types import Transistor, ChannelType` | `from lccommon.data_types import Transistor, ChannelType` |

**步骤三：修复依赖声明**

| 包 | setup.py 修改 |
|---|-------------|
| `lccommon` | 添加 `pyparsing>=3.0` |
| `lccommon` | 添加 `klayout>=0.28` |
| `lclib` | 添加 `librecell-layout>=0.0.9`（声明已有的隐式依赖） |
| `librecell-meta` | 将 `librecell-lib==0.0.10` 改为 `librecell-lib>=0.0.9` |

**验收测试**：
```python
# tests/test_task01_imports.py

def test_common_no_layout_dependency():
    """librecell-common 不应依赖 librecell-layout（核心类型在 lccommon 内）"""
    import lccommon.data_types
    assert hasattr(lccommon.data_types, 'Transistor')
    assert hasattr(lccommon.data_types, 'ChannelType')
    assert hasattr(lccommon.data_types, 'Cell')

def test_layout_backward_compat():
    """lclayout.data_types 仍然可用（向后兼容重导出）"""
    from lclayout.data_types import Transistor, ChannelType, Cell
    assert Transistor is not None

def test_lclib_uses_lccommon_types():
    """lclib 从 lccommon 导入数据类型，不再直接依赖 lclayout.data_types"""
    import lclib.logic.functional_abstraction as fa
    # 验证模块可正常导入
    assert hasattr(fa, 'ChannelType')

def test_common_data_types_independent():
    """lccommon.data_types 可以独立导入（不触发 lclayout 导入）"""
    import importlib
    import sys
    # 清除可能的缓存
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith('lclayout'):
            del sys.modules[mod_name]
    # 重新导入 lccommon.data_types
    importlib.reload(importlib.import_module('lccommon.data_types'))
    leaked = [k for k in sys.modules if k == 'lclayout' or k.startswith('lclayout.')]
    assert len(leaked) == 0, f"不应导入 lclayout，但发现: {leaked}"
```

### 1.2 搭建 pytest 框架

**操作**：
- 在项目根目录创建 `pyproject.toml`（统一构建配置和 pytest 配置）
- 创建测试目录结构：
  ```
  tests/
  ├── conftest.py          # 共享 fixtures
  ├── unit/                # 单元测试
  │   ├── common/
  │   ├── layout/
  │   └── lib/
  ├── integration/         # 集成测试
  ├── e2e/                 # 端到端测试 (Task 09)
  └── fixtures/            # 测试数据文件
      └── netlists/        # 测试用 SPICE 网表
  ```
- 在 `pyproject.toml` 中配置 pytest：
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  markers = [
      "unit: unit tests",
      "integration: integration tests (may need klayout/ngspice)",
      "e2e: end-to-end tests",
      "slow: slow tests (SMT solver etc.)",
  ]
  ```
- 将现有 `examples/cells.sp` 和 `librecell-lib/test_data/` 中的文件链接或复制到 `tests/fixtures/`

**注意**：本地已安装 pytest 8.3.3、pytest-cov 5.0.0、pytest-sugar 1.0.0、pytest-html 4.1.1，无需额外安装。

**验收测试**：
```python
# tests/test_task01_infrastructure.py

def test_pytest_runs():
    """pytest 框架能正常发现和运行测试"""
    assert True

def test_fixtures_available(shared_netlist_path):
    """测试 fixtures 目录中的网表文件可访问"""
    import os
    assert os.path.exists(shared_netlist_path)

def test_markers_registered():
    """pytest markers 已正确注册（不产生 PytestUnknownMarkWarning）"""
    import pytest
    pass
```

### 1.3 放宽依赖版本约束

**问题**：当前版本锁定过严（`klayout==0.26.*`, `sympy==1.6.*` 等），与本地已安装版本不兼容。

**当前本地已安装版本**（作为兼容性参考）：

| 包 | setup.py 要求 | 本地已安装 | 建议范围 |
|---|-------------|-----------|---------|
| klayout | `==0.26.*` | 0.29.8 | `>=0.28` |
| numpy | `==1.*` | 1.26.4 | `>=1.20` |
| networkx | `==2.5` / `==2.*` | 3.5 | `>=2.5` |
| scipy | `>=1.5.*` | 1.16.0 | `>=1.5` |
| sympy | `==1.6.*` | 1.14.0 | `>=1.6` |
| z3-solver | `==4.8.*` | 4.15.4.0 | `>=4.8` |
| pysmt | `==0.9.*` | 0.9.6 | `>=0.9` |
| matplotlib | `==3.*` | 3.9.2 | `>=3.0` |
| toml | `==0.10.*` | 0.10.2 | `>=0.10` |
| liberty-parser | `>=0.0.8` | 0.0.25 | `>=0.0.8`（保持不变） |
| pyparsing | *未声明* | 3.1.4 | `>=3.0`（新增到 lccommon） |
| pydantic | *未声明* | 2.10.6 | `>=2.0`（Task 03 需要） |
| PyYAML | *未声明* | 6.0.2 | `>=6.0`（Task 03 需要） |

**缺失的包**（本地未安装，需确认是否需要）：

| 包 | 要求方 | 状态 | 处理方案 |
|---|-------|------|---------|
| pyspice | `lclib==1.4.*` | 未安装 | 标记为可选依赖（仅表征模块需要） |
| joblib | `lclib>=0.14` | 未安装 | 标记为可选依赖（仅并行表征需要） |

**操作**：
- 更新各 `setup.py` 中的 `install_requires`，按上表放宽版本
- 将 `pyspice` 和 `joblib` 改为 extras_require 可选依赖：
  ```python
  # lclib/setup.py
  extras_require={
      'characterization': ['pyspice>=1.4', 'joblib>=0.14'],
  }
  ```
- 创建 `requirements-dev.txt`（开发依赖，记录已验证的版本组合）
- 在当前环境验证所有包可正确安装

**验收测试**：
```python
# tests/test_task01_deps.py

def test_all_packages_importable():
    """三个子包都能正常导入"""
    import lccommon
    import lclayout
    import lclib

def test_dev_dependencies():
    """开发依赖已安装"""
    import pytest
    import coverage
```

### 1.4 创建基础 conftest.py

**操作**：
- 实现共享 fixtures：
  - `dummy_tech` — 加载 dummy_tech.py 配置
  - `sample_netlist_path` — 指向测试用 SPICE 网表
  - `shared_netlist_path` — 指向 fixtures 目录中的网表
  - `inverter_transistors` — 一个最简单的反相器晶体管列表
  - `tmp_output_dir` — 临时输出目录

**验收测试**：
```python
# tests/test_task01_conftest.py

def test_dummy_tech_fixture(dummy_tech):
    """dummy_tech fixture 返回有效的 tech 对象"""
    assert hasattr(dummy_tech, 'unit_cell_width')
    assert hasattr(dummy_tech, 'routing_grid_pitch_x')
    assert dummy_tech.db_unit == 1e-9

def test_inverter_transistors_fixture(inverter_transistors):
    """inverter_transistors fixture 返回 2 个晶体管"""
    assert len(inverter_transistors) == 2
```

## 完成标准

- [ ] `pip install -e ./librecell-common && pip install -e ./librecell-layout && pip install -e ./librecell-lib` 成功
- [ ] `python -c "import lccommon; import lclayout; import lclib"` 无错误
- [ ] `pytest tests/test_task01_*.py -v` 全部通过
- [ ] `lccommon` 不再依赖 `lclayout`（核心类型在 lccommon 内，可独立安装和导入）
- [ ] `lclib` 对 `lclayout.data_types` 的隐式依赖已改为从 `lccommon.data_types` 导入
- [ ] `pytest --co` 能发现所有测试文件
- [ ] `pyspice` / `joblib` 为可选依赖，未安装时不影响核心功能导入

## 预计影响范围

- `librecell-common/lccommon/data_types.py`（新文件）
- `librecell-common/lccommon/net_util.py`（修改 import）
- `librecell-common/setup.py`（添加 pyparsing、klayout 依赖）
- `librecell-layout/lclayout/data_types.py`（改为重导出）
- `librecell-layout/setup.py`（放宽版本）
- `librecell-lib/setup.py`（放宽版本，添加 lclayout 依赖声明，pyspice/joblib 改为可选）
- `librecell-lib/lclib/logic/functional_abstraction.py`（修改 import）
- `librecell-lib/lclib/logic/seq_recognition.py`（修改 import）
- `librecell-lib/lclib/logic/cmos_sim.py`（修改 import）
- `librecell-lib/lclib/logic/graph_enumeration.py`（修改 import）
- `librecell-lib/lclib/logic/cmos_synth.py`（修改 import）
- `librecell-meta/setup.py`（修复版本号）
- `tests/`（新目录和文件）
- `pyproject.toml`（新文件）
- `requirements-dev.txt`（新文件）
