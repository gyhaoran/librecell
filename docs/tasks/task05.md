# Task 05: 多 Track 支持

## 目标

参数化单元高度和布线栅格，支持同一工艺下不同 track 高度（6T/7T/9T/10T/12T 等）的标准单元生成。支持双向 track 迁移（上行如 7T→9T，下行如 9T→7T）。

## 前置条件

- Task 04 完成（LayerStack 动态化）

## 详细任务

### 5.1 参数化单元高度计算

**操作**：在 `TechConfig` 中添加 track 相关参数

```yaml
# 在 cell 配置中添加
cell:
  num_tracks: 9          # track 数（6/7/9/10/12 等）
  track_pitch: 300       # track 间距 (db_unit)
  # unit_cell_height 自动计算: num_tracks * track_pitch
  # 或者直接指定 unit_cell_height 覆盖
```

**逻辑**：
- 如果指定了 `num_tracks` 和 `track_pitch`，自动计算 `unit_cell_height`
- 如果直接指定了 `unit_cell_height`，使用指定值
- 两者都指定时以 `unit_cell_height` 优先，并发出警告
- `num_tracks` 支持范围：4~20（超出范围发出警告）

### 5.2 调整晶体管布局的 Y 坐标

**操作**：修改 `lclayout/layout/transistor.py` 和 `cell_template.py`

- `transistor_offset_y` 支持按 track 数自动计算
- Nwell/Pwell 分界线位置根据 track 数调整
- Power rail 的 Y 坐标适配新的单元高度

### 5.3 调整布线栅格

**操作**：修改布线图构建

- Y 方向的 routing grid pitch 与 track_pitch 关联
- 可用布线 track 数量随单元高度变化
- 确保布线 track 落在合法位置

**下行迁移约束**（如 9T→7T、10T→7T）：
- track 数减少意味着可用的 Y 方向布线资源减少
- 复杂单元（如 DFF、AOI）在低 track 数下可能布线失败
- 需要在布线图构建阶段计算可用 routing track 数，并在不足时发出明确警告
- 在 `lclayout/routing_graph.py` 中添加辅助函数：`estimate_min_tracks(cell_name, netlist, tech_config) -> int`，估算某个单元所需的最小 track 数（基于信号数量和布线复杂度启发式估算）

### 5.4 创建多 track 工艺配置示例

**操作**：
- `examples/dummy_tech_6t.yaml` — 6 track 配置（最紧凑，仅简单单元可行）
- `examples/dummy_tech_7t.yaml` — 7 track 配置
- `examples/dummy_tech_9t.yaml` — 9 track 配置
- `examples/dummy_tech_10t.yaml` — 10 track 配置
- `examples/dummy_tech_12t.yaml` — 12 track 配置

**验收测试**：
```python
# tests/unit/layout/test_multi_track.py

class TestMultiTrack:
    def test_6t_cell_height(self):
        """6T 单元高度 = 6 * track_pitch"""
        config = load_tech_yaml("examples/dummy_tech_6t.yaml")
        assert config.cell.unit_cell_height == 6 * config.cell.track_pitch

    def test_7t_cell_height(self):
        """7T 单元高度 = 7 * track_pitch"""
        config = load_tech_yaml("examples/dummy_tech_7t.yaml")
        assert config.cell.unit_cell_height == 7 * config.cell.track_pitch

    def test_9t_cell_height(self):
        """9T 单元高度 = 9 * track_pitch"""

    def test_10t_cell_height(self):
        """10T 单元高度 = 10 * track_pitch"""

    def test_12t_cell_height(self):
        """12T 单元高度 = 12 * track_pitch"""

    def test_explicit_height_overrides(self):
        """显式指定 unit_cell_height 覆盖自动计算"""

    def test_transistor_offset_scales(self):
        """晶体管偏移随 track 数调整"""

    def test_routing_tracks_count(self):
        """可用布线 track 数随单元高度变化"""
        config_7t = load_tech_yaml("examples/dummy_tech_7t.yaml")
        config_9t = load_tech_yaml("examples/dummy_tech_9t.yaml")
        # 9T 比 7T 多 2 个可用布线 track
        tracks_7t = count_routing_tracks(config_7t)
        tracks_9t = count_routing_tracks(config_9t)
        assert tracks_9t > tracks_7t

    def test_power_rail_position_7t(self):
        """7T 下电源轨道位于正确的 Y 坐标"""

    def test_power_rail_position_9t(self):
        """9T 下电源轨道位于正确的 Y 坐标"""

    def test_active_region_on_routing_grid(self):
        """各 track 高度下，有源区域（扩散区）不与布线 track 冲突"""
        for yaml_file in ["dummy_tech_6t.yaml", "dummy_tech_7t.yaml",
                          "dummy_tech_9t.yaml", "dummy_tech_10t.yaml",
                          "dummy_tech_12t.yaml"]:
            config = load_tech_yaml(f"examples/{yaml_file}")
            # 布线 track 的 Y 坐标应落在合法栅格上（不与 diffusion/gate 区域重叠）
            track_ys = compute_routing_track_ys(config)
            active_y_range = compute_active_region_y_range(config)
            for y in track_ys:
                assert y not in active_y_range, \
                    f"{yaml_file}: routing track y={y} overlaps active region"

    def test_min_tracks_estimate_inv(self):
        """反相器估算最小 track 数较小（如 <=6）"""

    def test_min_tracks_estimate_dff(self):
        """DFF 估算最小 track 数较大（如 >=7）"""

# tests/integration/test_multi_track_pipeline.py

@pytest.mark.integration
class TestMultiTrackPipeline:
    def test_generate_inv_6t(self, tmp_output_dir):
        """6T 配置下生成 INVX1（简单单元应能在最紧凑 track 下工作）"""

    def test_generate_inv_7t(self, tmp_output_dir):
        """7T 配置下生成 INVX1"""
        # 验证 GDS 非空且单元高度正确

    def test_generate_inv_9t(self, tmp_output_dir):
        """9T 配置下生成 INVX1"""

    def test_generate_inv_10t(self, tmp_output_dir):
        """10T 配置下生成 INVX1"""

    def test_generate_nand2_7t(self, tmp_output_dir):
        """7T 配置下生成 NAND2X1"""

    def test_generate_nand2_9t(self, tmp_output_dir):
        """9T 配置下生成 NAND2X1"""

    def test_9t_cell_taller_than_7t(self, tmp_output_dir):
        """9T 单元的高度大于 7T 单元"""

    def test_7t_cell_taller_than_6t(self, tmp_output_dir):
        """7T 单元的高度大于 6T 单元"""

    def test_lvs_pass_7t(self, tmp_output_dir):
        """7T 布局通过 LVS"""

    def test_lvs_pass_9t(self, tmp_output_dir):
        """9T 布局通过 LVS"""

    def test_7t_to_9t_same_netlist(self, tmp_output_dir):
        """7T 和 9T 生成的布局对应相同的逻辑网表"""

    def test_downward_migration_warning(self, tmp_output_dir):
        """当 track 数不足以布线时，产生明确警告"""
```

## 完成标准

- [ ] `num_tracks` 参数在 TechConfig 中可用
- [ ] 6T / 7T / 9T / 10T / 12T 配置文件分别生成正确高度的单元
- [ ] 7T 配置下 INVX1 和 NAND2X1 通过 LVS
- [ ] 9T 配置下 INVX1 和 NAND2X1 通过 LVS
- [ ] 6T 配置下 INVX1 通过 LVS（简单单元在最紧凑 track 下可行）
- [ ] 布线栅格随 track 数正确调整
- [ ] 布线 track 不足时产生明确警告（支持下行迁移场景）
- [ ] `pytest tests/unit/layout/test_multi_track.py -v` 全部通过
- [ ] `pytest tests/integration/test_multi_track_pipeline.py -v` 全部通过
- [ ] 所有 Task 02 回归测试通过

## 预计影响范围

- `lccommon/tech_config.py`（添加 track 参数）
- `lclayout/layout/cell_template.py`（参数化高度）
- `lclayout/layout/transistor.py`（调整 Y 坐标）
- `lclayout/routing_graph.py`（布线栅格调整，track 不足警告）
- `lclayout/standalone.py`（传递 track 参数）
- `examples/dummy_tech_6t.yaml`（新文件）
- `examples/dummy_tech_7t.yaml`（新文件）
- `examples/dummy_tech_9t.yaml`（新文件）
- `examples/dummy_tech_10t.yaml`（新文件）
- `examples/dummy_tech_12t.yaml`（新文件）
