# Task 07: 工艺迁移引擎

## 目标

实现工艺迁移工具，支持：
1. **同工艺双向 track 迁移**（如 6T↔7T↔9T↔10T↔12T，任意方向）
2. **跨工艺节点迁移**（如 90nm → 55nm）
3. 自动生成目标工艺配置，并提供参数缩放规则和可行性检查

## 前置条件

- Task 05 完成（多 Track 支持）
- Task 06 完成（多电源域基础）

## 详细任务

### 7.1 设计工艺迁移规则模型

**操作**：创建 `lccommon/tech_migration.py`

```python
class MigrationRule(BaseModel):
    """工艺迁移规则"""
    source_node: str       # e.g., "90nm"
    target_node: str       # e.g., "55nm"
    scale_factor: float    # 总体缩放比例 (e.g., 55/90 = 0.611)

    # 各参数的独立缩放（覆盖总体比例）
    overrides: Dict[str, float] = {}  # 参数路径 -> 缩放因子
    # e.g., {"cell.gate_length": 0.5, "routing.grid_pitch_x": 0.7}

    # 固定值覆盖（不缩放，直接指定目标值）
    fixed_values: Dict[str, Any] = {}
    # e.g., {"cell.num_tracks": 7, "db_unit": 1e-9}

class TechMigrator:
    """工艺迁移执行器"""

    def __init__(self, rule: MigrationRule): ...

    def migrate(self, source: TechConfig) -> TechConfig:
        """应用迁移规则，生成新的工艺配置"""

    def validate_feasibility(self, source: TechConfig, target: TechConfig,
                              cell_names: List[str] = None) -> MigrationReport:
        """验证迁移可行性，特别是下行 track 迁移时的布线资源是否充足"""

    def generate_migration_report(self, source: TechConfig, target: TechConfig) -> str:
        """生成迁移报告，列出所有参数变化"""

class MigrationReport(BaseModel):
    """迁移可行性报告"""
    feasible: bool
    warnings: List[str] = []  # 非致命警告
    errors: List[str] = []    # 致命问题
    param_changes: Dict[str, Tuple[Any, Any]] = {}  # 参数变化 {路径: (旧值, 新值)}
```

### 7.2 实现缩放引擎

**操作**：在 `TechMigrator.migrate()` 中实现

- 几何参数（width, spacing, pitch 等）按 `scale_factor` 缩放
- 离散值（层数、track 数）不缩放，需显式指定
- 缩放后的值圆整到 `db_unit` 的整数倍
- 间距规则自动缩放但保持最小值约束
- 生成可审核的 YAML 配置文件（带注释标注每个参数的来源）

**overrides/fixed_values 的点路径（dot-path）解析**：

`overrides` 和 `fixed_values` 中的 key 使用点分路径（如 `"cell.gate_length"`, `"routing.grid_pitch_x"`），需要递归访问 Pydantic v2 嵌套模型。实现注意事项：
- Pydantic v2 模型使用 `model_fields` 获取字段定义，使用 `model_copy(update=...)` 创建修改后的副本
- 递归解析示例：`"cell.gate_length"` → 先取 `source.cell`，再修改其 `gate_length` 字段
- 对于嵌套 Dict 类型（如 `min_spacing.metal1.metal2`），需要区分 Pydantic 子模型属性和 Dict key
- 建议实现 `_resolve_dot_path(config, path) -> (parent_obj, field_name)` 辅助函数
- 对不存在的路径抛出明确的 `ValueError`，列出可用字段

### 7.3 同工艺双向 Track 迁移

**操作**：提供任意方向 track 迁移的支持

**上行迁移**（如 7T → 9T、7T → 10T）：
- 仅改变 `num_tracks` 和相关 Y 方向参数
- 不改变 X 方向参数（gate_length, grid_pitch_x, 间距规则等）
- 自动调整 transistor_offset_y, routing grid 等
- 相对简单，布线资源增加

**下行迁移**（如 9T → 7T、10T → 7T、9T → 6T）：
- 同样仅改变 Y 方向参数
- **关键风险**：布线 track 数减少可能导致部分复杂单元无法布线
- 迁移引擎必须调用 `validate_feasibility()` 进行可行性检查
- 对每个目标单元，使用 Task 05 的 `estimate_min_tracks()` 估算最小 track 需求
- 生成明确的可行性报告：
  - 可行的单元列表
  - 不可行的单元列表（附原因：如 "DFF 需要至少 8 tracks，目标仅 6 tracks"）
  - 建议操作（如 "建议保持 7T 或更高"）

```yaml
# migration_9t_to_7t.yaml
source_node: "180nm_9t"
target_node: "180nm_7t"
scale_factor: 1.0  # 同工艺不缩放
fixed_values:
  cell.num_tracks: 7
overrides:
  cell.unit_cell_height: 0.778  # 7/9
```

```yaml
# migration_7t_to_9t.yaml
source_node: "180nm_7t"
target_node: "180nm_9t"
scale_factor: 1.0  # 同工艺不缩放
fixed_values:
  cell.num_tracks: 9
overrides:
  cell.unit_cell_height: 1.286  # 9/7
```

### 7.4 跨节点迁移示例

**操作**：创建迁移规则示例

- `examples/migration/90nm_to_55nm.yaml`
- `examples/migration/180nm_to_90nm.yaml`
- `examples/migration/7t_to_9t.yaml`（上行 track 迁移）
- `examples/migration/9t_to_7t.yaml`（下行 track 迁移）
- `examples/migration/10t_to_7t.yaml`（下行 track 迁移）
- `examples/migration/7t_to_6t.yaml`（下行 track 迁移，极端情况）

### 7.5 迁移 CLI 命令

**操作**：添加 CLI 命令

```bash
lclayout-migrate --source examples/cmos_90nm.yaml \
                 --rule examples/migration/90nm_to_55nm.yaml \
                 --output examples/cmos_55nm_generated.yaml
```

**验收测试**：
```python
# tests/unit/common/test_tech_migration.py

class TestMigrationRule:
    def test_load_migration_rule(self):
        """加载迁移规则 YAML"""

    def test_scale_factor_applied(self):
        """总体缩放因子正确应用"""
        rule = MigrationRule(source_node="90nm", target_node="55nm", scale_factor=55/90)
        source = load_tech_yaml("examples/cmos_90nm.yaml")
        target = TechMigrator(rule).migrate(source)
        # 间距缩放
        assert target.cell.gate_length == round(source.cell.gate_length * 55/90)

    def test_overrides_precedence(self):
        """独立缩放覆盖总体缩放"""

    def test_fixed_values(self):
        """固定值覆盖不受缩放影响"""

    def test_discrete_params_not_scaled(self):
        """层数等离散参数不被意外缩放"""

    def test_rounding_to_db_unit(self):
        """缩放后值圆整到 db_unit 整数倍"""

class TestTrackMigration:
    def test_7t_to_9t_height_change(self):
        """7T → 9T 仅改变高度"""
        source = load_tech_yaml("examples/dummy_tech_7t.yaml")
        rule = load_migration_rule("examples/migration/7t_to_9t.yaml")
        target = TechMigrator(rule).migrate(source)
        assert target.cell.num_tracks == 9
        # X 方向参数不变
        assert target.cell.gate_length == source.cell.gate_length

    def test_7t_to_9t_x_params_unchanged(self):
        """上行 Track 迁移不影响 X 方向参数"""

    def test_9t_to_7t_downward(self):
        """9T → 7T 下行迁移生成合法配置"""
        source = load_tech_yaml("examples/dummy_tech_9t.yaml")
        rule = load_migration_rule("examples/migration/9t_to_7t.yaml")
        target = TechMigrator(rule).migrate(source)
        assert target.cell.num_tracks == 7
        assert target.cell.unit_cell_height < source.cell.unit_cell_height

    def test_10t_to_7t_downward(self):
        """10T → 7T 下行迁移"""

    def test_downward_feasibility_warning(self):
        """下行迁移可行性检查对复杂单元发出警告"""
        source = load_tech_yaml("examples/dummy_tech_9t.yaml")
        rule = load_migration_rule("examples/migration/9t_to_7t.yaml")
        migrator = TechMigrator(rule)
        target = migrator.migrate(source)
        report = migrator.validate_feasibility(source, target, cell_names=["DFFPOSX1"])
        # DFF 可能在 7T 下布线困难，至少应有 warning
        assert len(report.warnings) > 0 or not report.feasible

    def test_extreme_downward_7t_to_6t(self):
        """7T → 6T 极端下行迁移，复杂单元应标记不可行"""

class TestCrossNodeMigration:
    def test_90nm_to_55nm(self):
        """90nm → 55nm 迁移"""
        source = load_tech_yaml("examples/cmos_90nm.yaml")
        rule = load_migration_rule("examples/migration/90nm_to_55nm.yaml")
        target = TechMigrator(rule).migrate(source)
        assert target.node == "55nm"
        assert target.cell.gate_length < source.cell.gate_length

    def test_migration_report(self):
        """迁移报告列出所有变化"""

    def test_migrated_config_validates(self):
        """迁移后的配置通过 schema 校验"""

# tests/integration/test_migration_pipeline.py

@pytest.mark.integration
class TestMigrationPipeline:
    def test_migrated_config_generates_layout(self, tmp_output_dir):
        """迁移后的配置能成功生成布局"""

    def test_7t_to_9t_both_pass_lvs(self, tmp_output_dir):
        """7T 和 9T 迁移后都通过 LVS"""

    def test_cli_migration_command(self, tmp_output_dir):
        """CLI 迁移命令正常工作"""
```

## 完成标准

- [ ] `MigrationRule` 模型和 `TechMigrator` 类实现完成
- [ ] 7T → 9T 上行 track 迁移正确（X 方向不变，Y 方向调整）
- [ ] 9T → 7T 下行 track 迁移生成合法配置
- [ ] 10T → 7T 下行 track 迁移生成合法配置
- [ ] 下行迁移可行性检查对复杂单元产生合理警告
- [ ] 90nm → 55nm 跨节点迁移产生合法配置
- [ ] 迁移后的配置通过 Pydantic schema 校验
- [ ] 迁移后的配置能成功生成布局
- [ ] 迁移报告包含所有参数变化
- [ ] CLI 命令可用
- [ ] `pytest tests/unit/common/test_tech_migration.py -v` 全部通过
- [ ] `pytest tests/integration/test_migration_pipeline.py -v` 全部通过

## 预计影响范围

- `lccommon/tech_migration.py`（新文件）
- `lclayout/standalone.py`（添加 migrate 子命令或新入口）
- `examples/migration/`（新目录，迁移规则示例）
- `examples/cmos_90nm.yaml`（新文件，90nm 工艺完整配置——从 cmos_180nm.yaml 手动调整或迁移生成）
- `setup.py`（注册新 CLI 命令）

**注意**：`examples/cmos_55nm.yaml` 不在本 task 创建——它由 Task 09 通过运行迁移引擎自动生成并验证。
