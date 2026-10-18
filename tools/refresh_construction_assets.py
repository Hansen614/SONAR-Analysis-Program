"""Refresh downloads and the design reference from the supplied Universal package."""
from pathlib import Path
from io import BytesIO, StringIO
from zipfile import ZipFile
import hashlib
import json
import re
import shutil
from Bio import SeqIO

PROGRAM = Path(__file__).resolve().parents[1]
ROOT = PROGRAM.parents[1]
STATIC = PROGRAM / 'sonar_app/static'
DEST = STATIC / 'downloads'
MAPS = STATIC / 'reporter-maps'
PACKAGE = ROOT / 'Reporter/序列/Universal_Reporter_Package.zip'
PREFIX = 'Universal_Reporter/'
DEST.mkdir(parents=True, exist_ok=True)
MAPS.mkdir(parents=True, exist_ok=True)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sites(sequence, circular=False):
    scan = sequence + (sequence[:5] if circular else '')
    return [(m.start() + 1, m.group()) for m in re.finditer('GGTCTC|GAGACC', scan)]


records, payloads, manifest, maps = {}, {}, [], []
with ZipFile(PACKAGE) as archive:
    provenance = json.loads(archive.read(PREFIX + 'provenance.json'))
    for name in ('Universal_Reporter_CDS', 'Universal_Reporter_EV'):
        sequences = []
        for extension, fmt in (('gb', 'genbank'), ('dna', 'snapgene'), ('fasta', 'fasta')):
            filename = name + '.' + extension
            data = archive.read(PREFIX + filename)
            assert digest(data) == provenance['outputs'][filename], filename
            stream = BytesIO(data) if extension == 'dna' else StringIO(data.decode())
            record = SeqIO.read(stream, fmt)
            sequences.append(str(record.seq).upper())
            if extension == 'gb':
                records[name] = record
            if extension in ('gb', 'dna'):
                payloads[filename] = data
                manifest.append({
                    'source': str(PACKAGE.relative_to(ROOT)),
                    'archive_member': PREFIX + filename, 'download': filename.replace('_EV.', '_Plasmid.'),
                    'source_sha256': digest(data), 'download_sha256': digest(data),
                    'method': 'byte-identical copy from user-supplied package',
                })
        assert len(set(sequences)) == 1, name
        filename = name + '.svg'
        original = archive.read(PREFIX + filename)
        assert digest(original) == provenance['outputs'][filename], filename
        # Keep the supplied vector artwork; apply the user's display-name correction only.
        artwork = original.decode()
        if name.endswith('_EV'):
            assert artwork.count('EV  •  7,498 bp') == 1
            artwork = artwork.replace('EV  •  7,498 bp', 'Plasmid  •  7,498 bp')
        filename = filename.replace('_EV.', '_Plasmid.')
        (MAPS / filename).write_text(artwork)
        maps.append({'archive_member': PREFIX + name + '.svg', 'asset': filename,
                     'source_sha256': digest(original), 'asset_sha256': digest(artwork.encode()),
                     'change': 'EV label renamed to Plasmid' if name.endswith('_EV') else 'none'})

cds = records['Universal_Reporter_CDS']
vector = records['Universal_Reporter_EV']
sequence = str(vector.seq).upper()
assert len(cds) == 2022 and cds.annotations['topology'] == 'linear'
assert len(vector) == 7498 and vector.annotations['topology'] == 'circular'
cds_features = [f for f in vector.features if f.type == 'CDS' and f.qualifiers.get('label') == ['Universal reporter CDS']]
assert len(cds_features) == 1
cds_start, cds_end = int(cds_features[0].location.start), int(cds_features[0].location.end)
assert (cds_start, cds_end) == (1118, 3140)
assert sequence[cds_start:cds_end] == str(cds.seq).upper()
protein = str(cds.seq.translate())
assert protein.endswith('*') and '*' not in protein[:-1]
assert sites(sequence, True) == [(2617, 'GAGACC'), (2648, 'GGTCTC')]
assert sites(str(cds.seq).upper()) == [(1499, 'GAGACC'), (1530, 'GGTCTC')]
left_keep, right_start = 2615, 2654
assert sequence[left_keep-6:left_keep] == sequence[right_start:right_start+6] == 'GGCAGC'
assert (left_keep-cds_start) % 3 == 0 and (right_start-left_keep) % 3 == 0

reference = {
    'name': 'Universal Reporter Plasmid',
    'source': str(PACKAGE.relative_to(ROOT)) + '!/' + PREFIX + 'Universal_Reporter_EV.gb',
    'source_sha256': digest(payloads['Universal_Reporter_EV.gb']),
    'package_sha256': digest(PACKAGE.read_bytes()),
    'cds_source': 'Universal_Reporter_CDS.gb',
    'cds_sha256': digest(payloads['Universal_Reporter_CDS.gb']),
    'status': 'computational_design', 'sequence': sequence,
    'leftKeep': left_keep, 'rightStart': right_start,
    'cdsStart': cds_start, 'cdsEnd': cds_end,
    'forwardEnd': 'CAGC', 'reverseEnd': 'TGCC',
    'protocols': ['RP01 v1.0', 'RP02 v1.0'],
}
for filename, data in payloads.items():
    (DEST / filename.replace('_EV.', '_Plasmid.')).write_bytes(data)
(STATIC / 'reporter-vector.js').write_text(
    '/* Generated from the user-supplied Universal Reporter package. */\n'
    + 'const ReporterVector = Object.freeze(' + json.dumps(reference, ensure_ascii=False) + ');\n'
    + "if(typeof module!=='undefined')module.exports=ReporterVector;\n"
)

source = ROOT / 'Protocols/RP02/RP02_Target_Reporter_Construction_by_Golden_Gate_Assembly.pdf'
target = DEST / source.name
shutil.copyfile(source, target)
manifest.append({'source': str(source.relative_to(ROOT)), 'download': target.name,
                 'source_sha256': digest(source.read_bytes()), 'download_sha256': digest(target.read_bytes()),
                 'method': 'byte-identical mirror; maintained master remains in Protocols/RP02'})
text_source = source.with_suffix('.md')
(DEST / 'construction_manifest.json').write_text(json.dumps({
    'package_source': str(PACKAGE.relative_to(ROOT)), 'package_sha256': reference['package_sha256'],
    'sequence_evidence': provenance,
    'validation': {'three_formats_identical': True, 'CDS_matches_EV': True,
                   'CDS_bp': len(cds), 'EV_bp': len(vector), 'CDS_coordinates': [cds_start+1, cds_end],
                   'BsaI_sites': sites(sequence, True), 'interface': ['CAGC', 'GGCA']},
    'protocol_source': str(text_source.relative_to(ROOT)), 'protocol_sha256': digest(text_source.read_bytes()),
    'protocol_scope': 'RP02 v1.0 describes a 4669 bp acceptor; the web page recalculates the molar ratio for the 7498 bp plasmid.',
    'files': manifest, 'maps': maps,
}, ensure_ascii=False, indent=2) + '\n')
for obsolete in ('reporter_universal.gb', 'reporter_universal_BsaI_domesticated_design.gb', 'Universal_Reporter_EV.gb', 'Universal_Reporter_EV.dna'):
    (DEST / obsolete).unlink(missing_ok=True)
print(json.dumps({'CDS_bp': len(cds), 'EV_bp': len(vector), 'files': len(manifest)}))
