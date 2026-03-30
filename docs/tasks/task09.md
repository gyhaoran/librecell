# Task 09: 端到端集成验证

## 目标

对多个工艺节点（180nm, 90nm, 55nm）执行完整的端到端验证流程：工艺配置 → 单元库生成 → LVS 通过 → LEF/GDS 输出正确。验证工艺迁移和 BCD 流程。

## 前置条件

- Task 01 ~ Task 08 全部完成

## 详细任务

### 9.1 创建标准验证单元集

**操作**：定义每个工艺节点必须通过的最小单元集

| 类别 | 单元 | 最小集（必须通过） |
|------|------|-------------------|
| 反相器 | INVX1, INVX2, INVX4 | INVX1, INVX2 |
| 与非门 | NAND2X1, NAND3X1 | NAND2X1 |
| 或非门 | NOR2X1, NOR3X1 | NOR2X1 |
| 与门 | AND2X1 | AND2X1 |
| 或门 | OR2X1 | OR2X1 |
| 缓冲器 | BUFX2 | BUFX2 |
| 触发器 | DFFPOSX1 | DFFPOSX1 |
| AOI/OAI | AOI21X1, OAI21X1 | AOI21X1 |

### 9.2 CMOS 180nm 端到端验证

**操作**：
- 使用 `cmos_180nm.yaml` 配置
- 生成最小单元集的所有单元
- 验证每个单元 LVS 通过
- 验证 GDS 文件有效
- 验证 LEF 文件包含正确的 MACRO 定义

### 9.3 CMOS 90nm 端到端验证

**操作**：
- 使用 `cmos_90nm.yaml` 配置（或从 180nm 迁移生成）
- 执行与 9.2 相同的验证

### 9.4 CMOS 55nm 端到端验证

**操作**：
- 使用 `cmos_55nm.yaml` 配置（或从 90nm 迁移生成）
- 执行与 9.2 相同的验证

### 9.5 Track 迁移验证

**操作**：

**上行迁移**（7T → 9T）：
- 迁移前后分别生成 INVX1, NAND2X1
- 验证两者都通过 LVS
- 验证 9T 单元高度大于 7T

**下行迁移**（9T → 7T）：
- 迁移后生成 INVX1, NAND2X1
- 验证简单单元（INVX1）通过 LVS
- 验证迁移报告正确标识了不可行的复杂单元（如有）

**极端下行迁移**（9T → 6T）：
- 验证迁移引擎对复杂单元产生明确警告/错误
- 验证简单单元（INVX1）仍可尝试生成

### 9.6 BCD 工艺验证

**操作**：
- 使用 `bcd_tech.yaml` 配置
- 生成普通 CMOS 单元（应正常工作）
- 生成 HV 反相器
- 验证 GDS 包含 HV 标记层

### 9.7 脚本化适配验证

**操作**：
- 模拟 SE 工程师工作流：
  1. 复制一个现有 YAML 配置
  2. 修改关键参数（gate_length, spacing 等）
  3. 编写一个简单插件（如 well tap 插件）
  4. 使用 Python API 生成单元库
  5. 验证生成结果

**验收测试**：
```python
# tests/e2e/test_cmos_180nm.py

@pytest.mark.e2e
class TestCMOS180nm:
    CELL_LIST = ["INVX1", "INVX2", "NAND2X1", "NOR2X1", "AND2X1",
                 "OR2X1", "BUFX2", "DFFPOSX1", "AOI21X1"]

    @pytest.fixture(scope="class")
    def tech_config(self):
        return load_tech_yaml("examples/cmos_180nm.yaml")

    @pytest.mark.parametrize("cell_name", CELL_LIST)
    def test_generate_cell(self, cell_name, tech_config, tmp_output_dir):
        """生成单元 GDS"""
        result = generate_cell(
            cell_name=cell_name,
            netlist_path="examples/cells.sp",
            tech_config=tech_config,
            output_dir=tmp_output_dir,
        )
        assert os.path.exists(result['gds_path'])
        assert os.path.getsize(result['gds_path']) > 0

    @pytest.mark.parametrize("cell_name", CELL_LIST)
    def test_lvs_pass(self, cell_name, tech_config, tmp_output_dir):
        """单元通过 LVS"""
        result = generate_cell(
            cell_name=cell_name,
            netlist_path="examples/cells.sp",
            tech_config=tech_config,
            output_dir=tmp_output_dir,
        )
        assert result['lvs_passed'] == True

    @pytest.mark.parametrize("cell_name", CELL_LIST)
    def test_lef_valid(self, cell_name, tech_config, tmp_output_dir):
        """LEF 文件包含 MACRO 定义"""

    def test_library_generation(self, tech_config, tmp_output_dir):
        """批量生成完整单元库"""
        result = generate_cell_library(
            cell_list=self.CELL_LIST,
            netlist_path="examples/cells.sp",
            tech_config=tech_config,
            output_dir=tmp_output_dir,
            parallel=1,
            continue_on_error=False,
        )
        assert result['success_count'] == len(self.CELL_LIST)
        assert result['failure_count'] == 0

# tests/e2e/test_cmos_90nm.py
# (类似 180nm 的结构)

# tests/e2e/test_cmos_55nm.py
# (类似 180nm 的结构)

# tests/e2e/test_track_migration.py

@pytest.mark.e2e
class TestTrackMigration:
    def test_7t_to_9t_both_generate(self, tmp_output_dir):
        """7T 和 9T 都能生成 INVX1"""

    def test_7t_to_9t_both_lvs(self, tmp_output_dir):
        """7T 和 9T 的 INVX1 都通过 LVS"""

    def test_9t_taller_than_7t(self, tmp_output_dir):
        """9T 单元高度 > 7T"""

    def test_migrated_config_generates(self, tmp_output_dir):
        """迁移生成的配置也能正确工作"""

    def test_9t_to_7t_downward_inv(self, tmp_output_dir):
        """9T → 7T 下行迁移后 INVX1 通过 LVS"""

    def test_9t_to_7t_downward_nand2(self, tmp_output_dir):
        """9T → 7T 下行迁移后 NAND2X1 通过 LVS"""

    def test_9t_to_7t_feasibility_report(self, tmp_output_dir):
        """9T → 7T 迁移报告正确标识可行/不可行单元"""

    def test_9t_to_6t_extreme_warning(self, tmp_output_dir):
        """9T → 6T 极端下行迁移对复杂单元产生警告"""

# tests/e2e/test_bcd.py

@pytest.mark.e2e
class TestBCD:
    def test_cmos_cells_with_bcd_config(self, tmp_output_dir):
        """BCD 配置下的普通 CMOS 单元"""

    def test_hv_inverter(self, tmp_output_dir):
        """HV 反相器生成"""

    def test_hv_layers_in_gds(self, tmp_output_dir):
        """GDS 包含 HV 工艺层"""

# tests/e2e/test_se_workflow.py

@pytest.mark.e2e
class TestSEWorkflow:
    def test_copy_and_modify_config(self, tmp_path):
        """SE 复制配置并修改参数"""
        import shutil
        shutil.copy("examples/cmos_180nm.yaml", tmp_path / "my_tech.yaml")
        # 修改 gate_length
        config = load_tech_yaml(str(tmp_path / "my_tech.yaml"))
        config.cell.gate_length = 60  # 修改
        save_tech_yaml(config, str(tmp_path / "my_tech_modified.yaml"))
        # 验证修改后的配置能工作
        result = generate_cell("INVX1", tech_config=str(tmp_path / "my_tech_modified.yaml"),
                               netlist_path="examples/cells.sp",
                               output_dir=str(tmp_path / "output"))
        assert result['lvs_passed']

    def test_plugin_based_customization(self, tmp_output_dir):
        """SE 通过插件定制布局"""

    def test_python_api_workflow(self, tmp_output_dir):
        """SE 使用 Python API 的完整工作流"""
```

## 完成标准

- [ ] 180nm CMOS：至少 9 个单元全部生成成功且 LVS 通过
- [ ] 90nm CMOS：至少 5 个核心单元（INV, NAND2, NOR2, AND2, BUF）通过
- [ ] 55nm CMOS：至少 5 个核心单元通过
- [ ] 7T → 9T 上行 Track 迁移验证通过
- [ ] 9T → 7T 下行 Track 迁移验证通过（简单单元 LVS 通过，复杂单元有合理报告）
- [ ] BCD HV 反相器验证通过
- [ ] SE 工程师工作流验证通过（配置修改 + 插件 + API）
- [ ] `pytest tests/e2e/ -v` 全部通过
- [ ] 所有之前的单元测试和集成测试仍通过

## 预计影响范围

- `tests/e2e/`（新目录，端到端测试）
- `examples/cmos_180nm.yaml`（完善或新建）
- `examples/cmos_90nm.yaml`（完善或新建）
- `examples/cmos_55nm.yaml`（完善或新建）
- 可能需要微调核心代码以修复端到端测试中暴露的 bug

## 注意事项

- 端到端测试较慢（SMT 求解 + LVS），标记为 `@pytest.mark.e2e`
- 如果某个单元生成失败，应深入分析原因并修复（可能是 Task 04/05/06 中的遗漏）
- 55nm 的设计规则更严格，可能暴露布线算法的局限性——记录但不阻塞
