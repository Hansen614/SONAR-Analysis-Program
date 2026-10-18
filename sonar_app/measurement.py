"""Measurement-only records around the unchanged numerical adapter.

Keeping pipeline.py intact preserves the scientific identity of already reviewed
Theta objects. Old records are projected on read; new runs save the current schema.
"""
import hashlib
import html
import io
import json
import zipfile

from .backend import read_json, write_json, sha
from .pipeline import UserPipeline
from .scope import measurement_data
from .localization import english_message


class MeasurementPipeline(UserPipeline):
    def run(self, specification):
        report = measurement_data(super().run(specification))
        if 'experiment_notes' in specification:
            report['experiment_notes'] = specification['experiment_notes']
        base = self.p.workspace / 'analyses' / report['run_id']
        write_json(base / 'results.json', report)
        manifest = read_json(base / 'artifact_manifest.json')
        manifest['results.json'] = sha(base / 'results.json')
        write_json(base / 'artifact_manifest.json', manifest)
        return report

    def load(self, run_id):
        return measurement_data(super().load(run_id))

    def export(self, run_id):
        # Preserve input/mask bytes and portable rerun configuration. Older saved
        # runs stay untouched; the exported result and its manifest agree.
        original = super().export(run_id)
        output = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(original)) as source:
            report = measurement_data(json.loads(source.read('results.json')))
            result_bytes = (json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()
            manifest = json.loads(source.read('artifact_manifest.json'))
            manifest['results.json'] = hashlib.sha256(result_bytes).hexdigest()
            rendered = source.read('report.html').decode().replace(
                'S7 模型用于新批次时是明确标记的未验证转移估计；本批次参考拟合是研究校准，均非 RNA 编辑百分比。',
                '内置标尺用于新批次时是明确标记的未验证转移估计；本批次参考拟合是研究校准。')
            # Translate report boilerplate only, before inserting user metadata.
            for message in (
                'RES 单位为 AC DNA 质量参考等效 %。',
                '内置标尺用于新批次时是明确标记的未验证转移估计；本批次参考拟合是研究校准。',
                '完整 Θ、signed sums、bootstrap 分母、兼容范围、模型、输入和版本哈希见 JSON/CSV。区间未经名义 95% 覆盖率验证。',
                '解压本报告后，在相同锁定 Python 环境运行：',
                '报告包含此次上传的原始 FCS，仅用于本地内部研究。',
            ):
                rendered = rendered.replace(message, english_message(message))
            rendered = rendered.replace('lang="zh-CN"', 'lang="en"')
            if 'experiment_notes' in report:
                fields = [('Cell type', report.get('cell_type', 'Not specified')),
                          ('Reporter construct', report.get('reporter_construct', 'Not specified')),
                          ('Experiment notes', report['experiment_notes'] or 'None')]
                info = '<section><h2>Experiment details</h2><dl>' + ''.join(
                    '<dt>'+html.escape(label)+'</dt><dd style="white-space:pre-wrap">'+html.escape(str(value))+'</dd>'
                    for label, value in fields) + '</dl></section>'
                rendered = rendered.replace('</h1>', '</h1>'+info, 1)
            replacements = {'results.json': result_bytes, 'artifact_manifest.json': json.dumps(manifest, indent=2).encode(),
                            'report.html': rendered.encode()}
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as target:
                for name in source.namelist():
                    target.writestr(name, replacements[name] if name in replacements else source.read(name))
        return output.getvalue()
