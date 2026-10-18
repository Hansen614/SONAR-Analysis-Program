"""Traceable local exports; null is always distinct from zero."""
import csv
import html
import io
import json
from pathlib import Path
import zipfile
from . import __version__
from .backend import sha

LIMITATIONS = [
    "RAS is the ratio of paired, signed, background-corrected linear green and red sums.",
    "RES uses AC DNA mass-equivalent units and is research-only. S7-to-S10 or external transfer is not qualified.",
    "Conditional bootstrap intervals and model-discrepancy compatibility sets are not validated 95% measurement intervals.",
    "A/B are independent transfection wells within one experiment. Event counts and technical reads are not biological n.",
    "The S7 75/90 label swap is retrospective team recollection, not independently verified preparation.",
    "Identity compensation is not validated multicolor optical compensation; detector upper limits and viability remain unresolved.",
]


def flatten(obj, prefix=""):
    out = {}
    for key, value in obj.items():
        key = prefix + key
        if isinstance(value, dict):
            out.update(flatten(value, key + "."))
        elif isinstance(value, list):
            out[key] = json.dumps(value, ensure_ascii=False, allow_nan=False)
        else:
            out[key] = value
    return out


def csv_safe(value):
    # Preserve true numeric negatives while preventing spreadsheet formula evaluation.
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


def curve_svg(model, samples):
    width, height = 840, 340
    left, top, pw, ph = 62, 25, 735, 260
    x = lambda v: left + v * pw
    y = lambda v: top + ph - (v - .4) / .9 * ph
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="840" height="340" viewBox="0 0 840 340" role="img" aria-label="Frozen RES forward curve and S7 reference wells">',
        '<rect width="840" height="340" fill="#fff"/>']
    for v in [0, .25, .5, .75, 1]:
        lines.append(f'<path d="M{x(v)} {top}V{top+ph}" stroke="#e6eceb"/><text x="{x(v)}" y="308" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#526762">{v*100:g}</text>')
    for v in [.4, .6, .8, 1, 1.2]:
        lines.append(f'<path d="M{left} {y(v)}H{left+pw}" stroke="#e6eceb"/><text x="48" y="{y(v)+4}" text-anchor="end" font-family="sans-serif" font-size="12" fill="#526762">{v:g}</text>')
    coords = ' '.join(f'{x(a)},{y(b)}' for a, b in zip(model['knots'], model['values']))
    lines.append(f'<polyline points="{coords}" fill="none" stroke="#007d72" stroke-width="3"/>')
    for s in samples:
        if s.get('series') != 'S7':
            continue
        r = next((r for r in s['RAS'] if r['population_mode'] == 'reporter'), None)
        if r and r.get('ras') is not None:
            lines.append(f'<circle cx="{x(float(s["condition_label"])/100)}" cy="{y(r["ras"])}" r="4" fill="#d89236" stroke="white"><title>{html.escape(s["sample_id"])}</title></circle>')
    lines.append('<text x="420" y="335" text-anchor="middle" font-family="sans-serif" font-size="12">Corrected AC DNA mass fraction (%) · research reference</text><text x="18" y="165" transform="rotate(-90 18 165)" font-family="sans-serif" font-size="12">RAS</text></svg>')
    return ''.join(lines)


def export_bundle(platform, dataset="reference", mode="research", sample_ids=None, population="reporter"):
    if mode not in ('research', 'routine'):
        raise ValueError('Unknown mode.')
    platform.validate_dataset(dataset)
    available = {r['sample_id'] for r in platform.metadata(dataset)}
    ids = list(available) if sample_ids is None else sample_ids
    if not ids or any(s not in available for s in ids):
        raise ValueError('Select valid sample IDs.')
    # Export raw-to-report results, including selected population and explicit provenance.
    samples = [platform.analyze(sid, dataset, population, mode, diagnostics=False) for sid in sorted(ids)]
    payload = {'app_version': __version__, 'release_id': platform.api.RELEASE, 'dataset': dataset,
        'mode': mode, 'population': population, 'missing_values': 'JSON null / CSV blank, never zero',
        'limitations': LIMITATIONS, 'samples': samples, 'sharing': 'Internal authorized research; public redistribution not established'}
    rows = []
    for s in samples:
        for ras in s['RAS']:
            rows.append(flatten({**{k: v for k, v in s.items() if k != 'RAS'}, 'RAS': ras}))
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(dict.fromkeys(k for row in rows for k in row)))
    writer.writeheader(); writer.writerows([{k: csv_safe(v) for k, v in row.items()} for row in rows])
    svg = curve_svg(platform.model, platform.frozen)
    esc = html.escape
    cells = []
    fmt = lambda v, factor=1: 'Unavailable' if v is None else f'{v*factor:.6g}'
    for s in samples:
        r = s['RAS'][0]; res = s['RES']
        cells.append('<tr>' + ''.join('<td>' + esc(str(v)) + '</td>' for v in [s['sample_id'], s['well_id'],
            s['original_source_condition_label'], s['condition_label'], r['population_mode'], fmt(r.get('ras')),
            fmt(res['res_mass_fraction'], 100), fmt(res['research_res_mass_fraction'], 100),
            res['scientific_status'], res['numerical_status']]) + '</tr>')
    report = f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>SONAR measurement report</title>
<style>body{{font:15px/1.6 system-ui;max-width:1300px;margin:48px auto;padding:0 24px;color:#193c37}}h1{{font-size:36px}}table{{border-collapse:collapse;width:100%;font-size:12px}}td,th{{border-bottom:1px solid #ddd;padding:10px;text-align:left;overflow-wrap:anywhere}}.scroll{{overflow:auto}}code{{overflow-wrap:anywhere}}@media print{{body{{margin:0}}}}</style>
<h1>SONAR measurement report</h1><p>{esc(dataset)} · {esc(mode)} · {esc(population)} · application {__version__}</p>
<p>RES is AC DNA mass-equivalent percent. Routine RES is unavailable in this release. Research RES is a separately identified exploratory estimate.</p>
{svg}<div class="scroll"><table><thead><tr>{''.join('<th>'+h+'</th>' for h in ['Sample','Independent well','Original label','Corrected condition','Population','RAS','RES (% mass eq.)','Research RES (% mass eq.)','Scientific permission','Numerical status'])}</tr></thead><tbody>{''.join(cells)}</tbody></table></div>
<h2>Interpretation and methods</h2><ul>{''.join('<li>'+esc(v)+'</li>' for v in LIMITATIONS)}</ul>
<h2>Reproduction</h2><p>JSON and CSV retain input hashes, counts, signed sums, both uncertainty outputs, model/context IDs, optical audit and reproduction commands for each sample. Run from the application directory with the same workspace.</p>
<pre>{esc(samples[0]['provenance']['reproduction_command'])}</pre><p>Reference manifest SHA-256: <code>{platform.release_hash}</code></p>
<p>Machine-readable provenance and dependency lock are included. This export does not contain raw acquisitions; retain the original experiment workspace with matching hashes.</p></html>'''
    provenance = {'app_version': __version__, 'release_id': platform.api.RELEASE,
        'reference_manifest_sha256': platform.release_hash, 'context_sha256': sha(platform.root/'models/context_profiles/context_v1.json'),
        'model_sha256': sha(platform.root/'models/res_primary/model.json'), 'samples': [s['provenance'] | {'sample_id':s['sample_id'], 'input_sha256':s['input_sha256']} for s in samples],
        'dependencies': platform.dependency_status()}
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('measurements.json', json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False))
        z.writestr('measurements.csv', '\ufeff' + stream.getvalue())
        z.writestr('report.html', report)
        z.writestr('calibration.svg', svg)
        z.writestr('provenance.json', json.dumps(provenance, indent=2))
        z.write(platform.root/'environment/requirements.lock.txt', 'requirements.lock.txt')
        z.writestr('METHODS.txt', '\n\n'.join(LIMITATIONS))
    return data.getvalue()
