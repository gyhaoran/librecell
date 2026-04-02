# Task 10: 生产级加固

## 目标

提升系统的生产可用性：性能优化、错误处理完善、日志体系、用户文档、以及架构扩展点预留（FinFET）。

## 前置条件

- Task 09 完成（端到端验证通过）

## 详细任务

### 10.1 性能优化

**操作**：

1. **布线图冲突计算优化**
   - 当前 `standalone.py:494` 的间距冲突检测是 O(N^2)
   - 使用空间索引（R-tree 或网格分区）降低到 O(N log N)

2. **配置解析缓存**
   - TechConfig 对象创建后缓存，避免重复解析
   - LayerStack 构建结果缓存

3. **并行单元生成**
   - `generate_cell_library()` 支持多进程并行
   - 使用 `multiprocessing` 或 `joblib`

4. **Profiling 基准**
   - 为 INVX1, NAND2X1, DFFPOSX1 建立性能基准
   - 记录放置时间、布线时间、DRC 修正时间

### 10.2 错误处理完善

**操作**：

1. **自定义异常类**
   ```python
   class TechConfigError(Exception): ...
   class PlacementError(Exception): ...
   class RoutingError(Exception): ...
   class LVSError(Exception): ...
   class DRCError(Exception): ...
   ```

2. **错误消息人性化**
   - 网表解析失败时指出具体行号和原因
   - 布线失败时指出是哪个信号无法布线
   - LVS 失败时指出不匹配的网络/器件
   - 配置错误时指出具体字段和期望值

3. **优雅的降级处理**
   - SMT 求解超时时回退到启发式方法
   - 单个单元失败不阻断整个库生成
   - 提供 `--continue-on-error` 选项

### 10.3 日志体系

**操作**：

1. 统一使用 Python `logging` 模块
2. 日志级别：
   - DEBUG：详细的算法步骤
   - INFO：单元生成进度、LVS 结果
   - WARNING：非致命问题（如 DRC 修正近似）
   - ERROR：生成失败
3. 支持日志输出到文件（`--log` 参数增强）
4. 结构化日志（可选 JSON 格式）

### 10.4 FinFET 架构扩展点

**操作**：在关键位置预留扩展点，但不实现

1. `TechConfig` 中预留 `process_type` 字段（`planar` / `finfet`）
2. `TransistorLayout` 预留 fin 相关参数接口
3. `LayerStack` 支持 FinFET 特有层的声明（但不处理）
4. 文档中记录 FinFET 扩展的设计思路

```python
class TechConfig(BaseModel):
    process_type: str = "planar"  # "planar" | "finfet" (future)
    # FinFET specific (reserved)
    fin_pitch: Optional[float] = None
    fin_width: Optional[float] = None
    num_fins_per_device: Optional[int] = None
```

### 10.5 用户文档

**操作**：创建 `docs/` 目录下的用户指南

1. `docs/getting_started.md` — 快速入门
2. `docs/tech_config_guide.md` — 工艺配置编写指南（含所有字段说明）
3. `docs/migration_guide.md` — 工艺迁移指南
4. `docs/scripting_guide.md` — 脚本开发指南
5. `docs/api_reference.md` — Python API 参考
6. `docs/faq.md` — 常见问题

### 10.6 代码质量

**操作**：

1. 添加 type hints 到所有公共 API
2. 修复已知 bug：
   - `layers.py` 中 `layer()` 函数引用未定义 `material`，且 `AbstractLayer.__init__` 不接受 `material` 参数
   - `layers.py` 中 `eval_op_tree()` 函数引用未定义变量 `layout` 和 `selection_box`
   - `anneal_placer.py` 中 `_evaluate()` upper_row 循环缺少 `enumerate`，变量 `x` 为上一循环残留值
   - `Mask.__sub__` 引用不存在的 `self.material`
3. 移除死代码（如 `transistor_sizing/width_opt.py` 整个注释掉的文件）

**验收测试**：
```python
# tests/unit/test_error_handling.py

class TestErrorHandling:
    def test_invalid_tech_config_message(self):
        """无效配置产生清晰错误消息"""
        with pytest.raises(TechConfigError, match="missing required field"):
            load_tech_yaml("tests/fixtures/invalid_tech.yaml")

    def test_routing_failure_message(self):
        """布线失败消息指出具体信号"""

    def test_lvs_failure_details(self):
        """LVS 失败提供详细不匹配信息"""

    def test_continue_on_error(self):
        """--continue-on-error 下单个失败不阻断"""

# tests/unit/test_logging.py

def test_log_levels():
    """日志级别正确控制输出量"""

def test_log_to_file(tmp_path):
    """日志可输出到文件"""

# tests/unit/test_performance.py

@pytest.mark.benchmark
class TestPerformance:
    def test_inv_generation_time(self, benchmark):
        """INVX1 生成时间基准"""
        # 使用 pytest-benchmark

    def test_nand2_generation_time(self, benchmark):
        """NAND2X1 生成时间基准"""

    def test_config_loading_cached(self):
        """配置加载有缓存"""
        import time
        t1 = time.time()
        load_tech_yaml("examples/cmos_180nm.yaml")
        t2 = time.time()
        load_tech_yaml("examples/cmos_180nm.yaml")  # cached
        t3 = time.time()
        assert (t3 - t2) < (t2 - t1) * 0.5

# tests/unit/test_finfet_extensibility.py

def test_process_type_field():
    """TechConfig 包含 process_type 字段"""
    config = load_tech_yaml("examples/dummy_tech.yaml")
    assert config.process_type == "planar"

def test_finfet_params_optional():
    """FinFET 参数为可选"""
    config = load_tech_yaml("examples/dummy_tech.yaml")
    assert config.fin_pitch is None

def test_finfet_config_validates():
    """FinFET 配置可以声明但不执行"""

# tests/unit/test_bug_fixes.py

def test_layers_layer_function():
    """layers.py layer() 函数不再引用未定义变量"""

def test_layers_eval_op_tree():
    """layers.py eval_op_tree() 函数不再引用未定义的 layout 和 selection_box"""

def test_anneal_placer_evaluate():
    """anneal_placer _evaluate() upper_row 循环使用正确的 enumerate"""

def test_mask_subtraction():
    """Mask.__sub__ 正常工作"""
```

## 完成标准

- [ ] 布线冲突计算性能提升（使用 pytest-benchmark 建立 INVX1/NAND2X1/DFFPOSX1 基准线，优化后 regression 测试确保无性能退化）
- [ ] 自定义异常类覆盖所有主要失败场景
- [ ] 已知 bug（4 个）全部修复
- [ ] 错误消息对用户友好（指出具体问题和建议）
- [ ] 日志体系统一且可配置
- [ ] FinFET 扩展点已预留（字段存在，文档说明）
- [ ] 5 份用户文档完成
- [ ] 已知 bug（4 个）全部修复
- [ ] `pytest tests/ -v` 全部通过（包括所有之前的测试）
- [ ] `pytest --cov --cov-report=term` 整体覆盖率 > 70%

## 预计影响范围

- `lccommon/exceptions.py`（新文件）
- `lclayout/standalone.py`（错误处理、日志、性能优化）
- `lclayout/routing_graph.py`（空间索引优化）
- `lclayout/layout/layers.py`（bug 修复）
- `lclayout/place/anneal_placer.py`（bug 修复）
- `lccommon/tech_config.py`（FinFET 扩展字段）
- `lclayout/api.py`（并行支持、错误处理）
- `docs/*.md`（新文档文件）
- `tests/`（新测试文件）
