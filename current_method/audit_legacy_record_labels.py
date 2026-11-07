"""Reinterpret archived labels without rerunning or changing any old result."""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

from atlas_new.core import calibrated_quantile
from atlas_new.operational_metadata import operational_condition_labels


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    started = perf_counter()
    base = Path(__file__).resolve().parent
    cfg = json.loads((base / 'configs/full.json').read_text(encoding='utf-8'))
    old = base / 'results/full'
    sources = [old / f'operational_{name}.csv' for name in ('records', 'summary', 'frontier', 'audits')]
    sources += [base / 'results/full_plus/plus_assumption_boundaries.csv']
    before = {str(p.relative_to(base)): sha256(p) for p in sources}
    records = pd.read_csv(sources[0])
    corrected = []
    for i, row in records.iterrows():
        corrected.append(dict(source_row=int(i), scenario=row['scenario'], replicate=int(row['replicate']),
                              method=row['method'], archived_assumption_valid=bool(row['assumption_valid']),
                              **operational_condition_labels(row['scenario'], row['method'], cfg['eta'], cfg['zeta'])))
    labels = pd.DataFrame(corrected)
    by_cell = []
    for (scenario, method), group in labels.groupby(['scenario', 'method'], sort=True):
        by_cell.append(dict(scenario=scenario, method=method, n=len(group),
                            archived_valid_count=int(group['archived_assumption_valid'].sum()),
                            corrected_status=group['certificate_status'].iloc[0],
                            certificate_guarantee_applicable=bool(group['certificate_guarantee_applicable'].iloc[0]),
                            outer_guarantee_applicable=bool(group['outer_guarantee_applicable'].iloc[0]),
                            reasons=group['certificate_unsupported_reasons'].iloc[0]))
    old_frontier = pd.read_csv(sources[2])
    frontier_labels = []
    for i, row in old_frontier.iterrows():
        new = operational_condition_labels(row['scenario'], row['method'], cfg['eta'], cfg['zeta'])
        frontier_labels.append(dict(source_row=int(i), scenario=row['scenario'], method=row['method'],
                                    tolerance=row['tolerance'], archived_bound_if_valid=row['bound_if_valid'],
                                    corrected_bound_if_valid=new['nominal_certificate_failure_bound']))
    q = calibrated_quantile(np.arange(10), .05)
    archived_boundary = pd.read_csv(sources[4]).set_index('case').loc['small_calibration']
    after = {str(p.relative_to(base)): sha256(p) for p in sources}
    if before != after:
        raise AssertionError('Archived source bytes changed during read-only audit')
    counts = dict(records=len(labels),
                  archived_true=int(labels['archived_assumption_valid'].sum()),
                  corrected_certificate_valid=int(labels['certificate_guarantee_applicable'].sum()),
                  unsupported_certificate=int((labels['certificate_status'] == 'unsupported_conditions').sum()),
                  point_only_not_applicable=int((labels['certificate_status'] == 'not_applicable_point_only').sum()),
                  archived_true_but_unsupported=int((labels['archived_assumption_valid'] &
                      (labels['certificate_status'] == 'unsupported_conditions')).sum()),
                  archived_true_but_point_only=int((labels['archived_assumption_valid'] &
                      (labels['certificate_status'] == 'not_applicable_point_only')).sum()),
                  frontier_rows=len(frontier_labels),
                  frontier_rows_without_applicable_bound=sum(x['corrected_bound_if_valid'] is None for x in frontier_labels))
    if not np.isposinf(q):
        raise AssertionError('Expected infinite conformal order statistic')
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    labels.to_csv(out / 'corrected_operational_labels.csv', index=False)
    pd.DataFrame(by_cell).to_csv(out / 'method_scenario_label_summary.csv', index=False)
    pd.DataFrame(frontier_labels).to_csv(out / 'corrected_frontier_labels.csv', index=False)
    summary = dict(counts=counts, calibration_boundary=dict(
        n=10, eta=.05, requested_rank=11,
        archived_observed=str(archived_boundary['observed']), corrected_observed='infinite',
        quantile_representation='positive_infinity'),
        archive_hashes_before=before, archive_hashes_after=after, archived_bytes_unchanged=True,
        code_hashes={str(p.relative_to(base)): sha256(p) for p in
                     [Path(__file__).resolve(), base/'atlas_new/operational_metadata.py',
                      base/'atlas_new/experiments.py', base/'atlas_new/audit_plus.py']},
        audit_seconds=perf_counter()-started,
        scope='Deterministic metadata reinterpretation only; no optimizer, fit, outcome sampling, new simulation, or old file writes.')
    (out/'audit_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    lines = [
        '# 旧结果记录标签的确定性纠正', '',
        '本次只修输出记录与审计身份。没有重算权重、区间、误差、覆盖或发布策略，没有新抽样；所有旧 CSV 字节哈希保持一致。', '',
        '## 1. 小校准样本状态', '',
        '`calibrated_quantile(arange(10), .05)` 请求第 11 个次序统计量，因此原核心函数一直正确返回 +inf。',
        '`audit_plus.assumptions_and_boundaries` 旧版忽略返回值、硬写 finite；现按实际返回值写 infinite。旧 full_plus 边界表保留，其纠正在本目录 JSON 中。', '',
        '## 2. 原 operational 结果的前提标签', '',
        '旧 assumption_valid 只按 scenario 设置。nominal 等四个设定下，非法适应性 R2、未校准 singleton_U、删除曲率的 no_curvature 都继承 True；无区间的两个点预测基线也继承 True。',
        f"共 {counts['records']} 条记录；旧 True={counts['archived_true']}；新合法证书条件={counts['corrected_certificate_valid']}，条件不受支持的证书={counts['unsupported_certificate']}，无证书点基线={counts['point_only_not_applicable']}。",
        f"旧 True 中 {counts['archived_true_but_unsupported']} 条实为负控制；另 {counts['archived_true_but_point_only']} 条只是点基线，前提布尔值应为 NA。",
        f"旧 frontier 的 {counts['frontier_rows']} 行都写 .10；其中 {counts['frontier_rows_without_applicable_bound']} 行没有适用的证书概率界，新 writer 及对照表改为 null/空值。", '',
        '此处方法身份为早期一维二次曲面的 box-supremum Bbar 实验，不是后来的 min(Bbar,BLip) 工作流。no_curvature 没有 BLip 回退，故整套 Bbar 声明不受支持；这仍不等于每个实际数值区间都不覆盖或每个权重一定违反几何界。',
        '原 outer 列使用原校准盒与 L，独立于候选证书方法。因而 nominal 的三个负控制和两个点基线，其另行计算的 outer 仍有适用条件；proxy_shift 和 understated_LH 的 outer 则没有该统一保证。新增标签明确区分证书与外包。',
        'joint_set_covered 仍表示原校准盒的实际覆盖事件，不表示该方法完整假设成立，更不表示 singleton_U 的集合覆盖。未知方法/设定会抛错，不被静默标为合法。', '',
        '## 3. 文件和验证范围', '',
        '- corrected_operational_labels.csv：原行号、世界和方法对应的新旧条件标签，不重复输出或改变数值结果。',
        '- corrected_frontier_labels.csv：原行号和阈值对应的概率界可用性。',
        '- method_scenario_label_summary.csv：全部 48 个方法 × 设定组合。',
        '- audit_summary.json：前后档案哈希、代码哈希、记录计数与耗时。', '',
        f"确定性审计耗时 {summary['audit_seconds']:.3f} 秒；不属于一次新实验。相关单元测试另记录于提交说明。", '',
        '该纠正不解决真实 U/L/H 来源、被遗漏的机制或适应性选择的实际价值；也未开展新的重尾/等方差实验。',
    ]
    (out/'RECORD_LABEL_CORRECTION.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps(dict(counts=counts, audit_seconds=summary['audit_seconds'], archive_unchanged=True)))


if __name__ == '__main__':
    main()
