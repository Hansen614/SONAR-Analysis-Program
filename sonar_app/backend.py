"""GUI-independent application services around the immutable SONAR engine."""
from __future__ import annotations

import csv
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import sys
import tempfile
import uuid
import zipfile

from . import __version__
from .scope import measurement_data

MAX_IMPORT_BYTES = 600 * 1024 * 1024
MAX_IMPORT_FILES = 256
POPULATIONS = ("reporter", "blue_positive_reporter", "blue_negative_reporter")


def safe_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", value):
        raise ValueError("ID must use 1–80 letters, numbers, underscores, dots or hyphens.")
    return value


def contained(root, relative):
    root = Path(root).resolve()
    if Path(relative).is_absolute():
        raise ValueError("Path must stay relative to the experiment directory.")
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError("Path must stay within the experiment directory.")
    return path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


class Platform:
    def __init__(self, reference=None, workspace=None, verify=True):
        self.root = Path(reference or os.environ.get("SONAR_REFERENCE_ROOT") or
                         Path(__file__).resolve().parents[1] / "scientific_reference").resolve()
        self.workspace = Path(workspace or os.environ.get("SONAR_WORKSPACE") or Path.cwd() / "workspace").resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        # Legacy imports stay untouched so their hashed numerical semantics remain intact.
        # One explicitly selected reference root per process; never silently mix roots.
        loaded = sys.modules.get("science_api")
        if loaded and Path(loaded.ROOT).resolve() != self.root:
            raise ValueError("A different scientific root is already loaded. Start a separate process.")
        if verify:
            self.verify_release()
        os.environ.setdefault("MPLCONFIGDIR", str(self.workspace / ".matplotlib"))
        sys.path.insert(0, str(self.root / "src"))
        self.api = importlib.import_module("science_api")
        self.np = importlib.import_module("numpy")
        self.pd = importlib.import_module("pandas")
        self.context = self.api.load_context()
        self.model = self.api.load_res_model()
        self.manifest = self.api.load_experiment(verify_hashes=False)
        self.frozen = read_json(self.root / "results/integrated/SONAR_Sample_Reports.json")["samples"]
        self.release_hash = sha(self.root / "RELEASE_MANIFEST.json")
        self.model_hash = sha(self.root / "models/res_primary/model.json")
        self.context_hash = sha(self.root / "models/context_profiles/context_v1.json")

    def _ensure_current_identity(self):
        if (sha(self.root / "RELEASE_MANIFEST.json") != self.release_hash or
            sha(self.root / "models/res_primary/model.json") != self.model_hash or
            sha(self.root / "models/context_profiles/context_v1.json") != self.context_hash):
            raise ValueError("Scientific identity changed; cached downstream results invalidated. Restart after scientific review.")
        self.api.load_res_model()

    def verify_release(self):
        manifest = read_json(self.root / "RELEASE_MANIFEST.json")
        for record in manifest["files"]:
            p = contained(self.root, record["path"])
            if not p.is_file() or sha(p) != record["sha256"]:
                raise ValueError("Frozen file integrity failure: " + record["path"])
        return {"status": "PASS", "files": len(manifest["files"]), "release_id": manifest["release_id"]}

    def dependency_status(self):
        import importlib.metadata as metadata
        result = []
        for line in (self.root / "environment/requirements.lock.txt").read_text().splitlines():
            name, expected = line.split("==")
            try:
                actual = metadata.version(name)
            except metadata.PackageNotFoundError:
                actual = None
            result.append({"package": name, "expected": expected, "actual": actual, "matches": actual == expected})
        return result

    def datasets(self):
        values = [{"id": "reference", "name": "S7 / S10 · frozen reference", "samples": len(self.frozen), "kind": "frozen"}]
        for path in sorted((self.workspace / "imports").glob("*/experiment.json")):
            d = read_json(path)
            values.append({"id": path.parent.name, "name": d["name"], "samples": len(d["samples"]), "kind": "imported"})
        return values

    def metadata(self, dataset="reference"):
        if dataset == "reference":
            rows = self.api.clean(self.manifest[self.manifest.sample_role != "Mock"].to_dict("records"))
            for r in rows:
                r["sample_id"] = r["acquisition_id"]
                r["linked_editor_present"] = r["series"] == "S10" and r["condition_label"] > 0
            return rows
        return read_json(self.workspace / "imports" / safe_id(dataset) / "experiment.json")["samples"]

    def _metadata(self, dataset, sample_id):
        matches = [r for r in self.metadata(dataset) if r["sample_id"] == sample_id]
        if len(matches) != 1:
            raise ValueError("Unknown sample ID.")
        return matches[0]

    def sample_list(self, dataset="reference", mode="research"):
        if mode not in ("research", "routine"):
            raise ValueError("Unknown mode.")
        if dataset == "reference":
            reports = json.loads(json.dumps(self.frozen))
        else:
            self._check_import_identity(dataset)
            base = self.workspace / "imports" / safe_id(dataset) / "reports"
            reports = [read_json(p) for p in sorted(base.glob("*.json"))]
        for sample in reports:
            if mode == "routine":
                sample["RES"]["res_mass_fraction"] = None
                sample["RES"]["mode"] = mode
        return measurement_data(reports)

    def overview(self, dataset="reference", mode="research"):
        self._ensure_current_identity()
        return {"app_version": __version__, "release_id": self.api.RELEASE,
                "manifest_sha256": self.release_hash, "datasets": self.datasets(),
                "samples": self.sample_list(dataset, mode), "metadata": self.metadata(dataset),
                "reference_samples": measurement_data(self.frozen),
                "model": self.model, "context": self.context, "workspace": str(self.workspace),
                "dependency_status": self.dependency_status()}

    def analyze(self, sample_id, dataset="reference", population="reporter", mode="research", bootstrap=0, diagnostics=True):
        self._ensure_current_identity()
        if population not in POPULATIONS or mode not in ("research", "routine"):
            raise ValueError("Unknown population or mode.")
        if not isinstance(bootstrap, int) or not 0 <= bootstrap <= 2000:
            raise ValueError("Bootstrap repeats must be 0–2000.")
        if dataset != "reference":
            self._check_import_identity(dataset)
        md = self._metadata(dataset, sample_id)
        base = self.root if dataset == "reference" else self.workspace / "imports" / safe_id(dataset)
        path = contained(base, md["file_path"])
        if sha(path) != md["sha256"]:
            raise ValueError("Input changed since registration; import it as a new experiment.")
        self.api.load_res_model()  # invalidate dependencies changed since startup
        self.api.load_context()
        processed = self.api.process_fcs(path, self.context, md)
        return self._report(processed, md, dataset, population, mode, bootstrap, diagnostics)

    def _report(self, processed, md, dataset, population, mode, bootstrap, diagnostics):
        old = next((s for s in self.frozen if s["sample_id"] == md["sample_id"]), None) if dataset == "reference" else None
        frozen_ras = next((r for r in old["RAS"] if r["population_mode"] == population), None) if old else None
        uncertainty = frozen_ras["uncertainty"] if frozen_ras else None
        ras = self.api.calculate_ras(processed, population, uncertainty=uncertainty, bootstrap_repeats=bootstrap)
        u = ras.get("uncertainty", {})
        interval = [u.get("event_control_ci_low"), u.get("event_control_ci_high")]
        if any(v is None for v in interval):
            interval = None
        compatible = dataset == "reference" and md["series"] == "S7" and population == "reporter"
        res = self.api.calculate_res(ras.get("ras"), context_id=self.context["context_id"],
            population_mode=population, calibration_domain_id=self.model["calibration_domain_id"] if compatible else "TRANSFER_NOT_QUALIFIED",
            mode=mode, sample_id=md["sample_id"] if compatible else None, ras_interval=interval, model=self.model)
        result = {"sample_id": md["sample_id"], "well_id": md["well_id"], "series": md.get("series", "Imported"),
            "condition_label": md["condition_label"], "original_source_condition_label": md.get("source_condition_label", md.get("original_label")),
            "metadata": md, "input_sha256": processed["input_sha256"], "qc": processed["qc"], "optical": processed["optical"],
            "RAS": [ras], "RES": res,
            "provenance": {"app_version": __version__, "release_id": self.api.RELEASE, "reference_manifest_sha256": self.release_hash,
                "context_sha256": sha(self.root / "models/context_profiles/context_v1.json"),
                "model_sha256": sha(self.root / "models/res_primary/model.json"), "dataset": dataset,
                "population": population, "mode": mode, "bootstrap_repeats_requested": bootstrap,
                "reproduction_command": shlex.join(['python', '-m', 'sonar_app', '--reference', str(self.root),
                    '--workspace', str(self.workspace), 'analyze', '--dataset', dataset, '--sample', md['sample_id'],
                    '--population', population, '--mode', mode, '--bootstrap', str(bootstrap), '--output', 'report.json']),
                "reproduction_path_note": "Paths identify this run; use relocated --reference/--workspace after moving the self-contained package."}}
        if diagnostics:
            x = processed["array"]
            ix = self.np.linspace(0, len(x) - 1, min(1800, len(x)), dtype=int)
            result["diagnostic_points"] = {"representation": "asinh(raw/150); display only; full signed linear sums used for RAS",
                "total_events": len(x), "display_events": len(ix), "points": self.np.column_stack([
                    self.np.arcsinh(x[ix, 9] / 150), self.np.arcsinh(x[ix, 5] / 150), processed["masks"][population][ix]]).tolist()}
        return self.api.clean(result)

    def inverse(self, ras, mode="research", interval=None):
        # A standalone calculator is hypothetical; it cannot assert sample compatibility.
        self._ensure_current_identity()
        value = float(ras)
        if not self.np.isfinite(value):
            raise ValueError("RAS must be finite.")
        if interval is not None and (len(interval) != 2 or not all(self.np.isfinite(interval)) or not interval[0] <= value <= interval[1]):
            raise ValueError("RAS interval must bracket the input.")
        self.api.load_res_model()
        return self.api.calculate_res(value, context_id=self.context["context_id"], population_mode="reporter",
            calibration_domain_id="UNREGISTERED_CALCULATOR_INPUT", mode=mode, ras_interval=interval, model=self.model)

    def validate_import_rows(self, rows, source):
        if not rows or len(rows) > 128:
            raise ValueError("Provide 1–128 samples.")
        required = {"sample_id", "well_id", "file_path", "condition_label", "original_label", "cell_type", "reporter_construct", "linked_editor_present"}
        seen_ids, seen_wells, seen_hashes = set(), set(), set()
        normalized = []
        for row in rows:
            if not required.issubset(row) or any(row[k] is None or str(row[k]).strip() == "" for k in required):
                raise ValueError("Missing metadata: " + ", ".join(sorted(required)))
            sid, well = safe_id(row["sample_id"]), safe_id(row["well_id"])
            if sid in seen_ids or well in seen_wells:
                raise ValueError("Sample IDs and independent well IDs must be unique.")
            flag = str(row["linked_editor_present"]).lower()
            if flag not in ("true", "false"):
                raise ValueError("linked_editor_present must be true or false; unknown linkage uses false.")
            if row["cell_type"] != self.context["cell_type"]:
                raise ValueError("This context is limited to HEK293T. A separate context requires scientific qualification.")
            path = contained(source, row["file_path"])
            if path.suffix.lower() != ".fcs" or not path.is_file():
                raise ValueError("Every file_path must identify an existing FCS file inside the import.")
            digest = sha(path)
            if digest in seen_hashes:
                raise ValueError("Duplicate FCS acquisition cannot represent an additional independent well.")
            if row.get("sha256") and row["sha256"] != digest:
                raise ValueError("Input changed: declared hash mismatch.")
            seen_ids.add(sid); seen_wells.add(well); seen_hashes.add(digest)
            normalized.append({**row, "sample_id": sid, "acquisition_id": sid, "well_id": well, "sha256": digest,
                "linked_editor_present": flag == "true", "series": "Imported", "source_condition_label": row["original_label"],
                "profile_id": self.context["acquisition_profile_id"], "calibration_permission": "NO_S7_TRANSFER_QUALIFICATION"})
        return normalized

    def import_directory(self, source, name="Imported experiment"):
        source = Path(source).resolve()
        with (source / "metadata.csv").open(encoding="utf-8-sig", newline="") as f:
            rows = self.validate_import_rows(list(csv.DictReader(f)), source)
        identifier = "experiment-" + uuid.uuid4().hex[:12]
        imports = self.workspace / "imports"
        imports.mkdir(exist_ok=True)
        temp = Path(tempfile.mkdtemp(prefix=".pending-", dir=imports))
        try:
            for row in rows:
                src = contained(source, row["file_path"])
                dest = temp / "inputs" / (row["sample_id"] + ".fcs")
                dest.parent.mkdir(exist_ok=True)
                shutil.copyfile(src, dest)
                row["original_filename"] = row["file_path"]
                row["file_path"] = dest.relative_to(temp).as_posix()
                p = self.api.process_fcs(dest, self.context, row)
                report = self._report(p, row, identifier, "reporter", "research", 0, False)
                write_json(temp / "reports" / (row["sample_id"] + ".json"), report)
            write_json(temp / "experiment.json", {"schema_version": 1, "name": str(name)[:120], "samples": rows,
                "context_id": self.context["context_id"], "context_sha256": sha(self.root / "models/context_profiles/context_v1.json"),
                "reference_manifest_sha256": self.release_hash, "calibration_permission": "NO_S7_TRANSFER_QUALIFICATION"})
            with (temp / "metadata.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in rows for k in r)))
                writer.writeheader(); writer.writerows(rows)
            temp.rename(imports / identifier)
        except Exception:
            shutil.rmtree(temp)
            raise
        return {"dataset": identifier, "samples": len(rows), "status": "IMPORTED_RAS_AVAILABLE_RES_TRANSFER_NOT_QUALIFIED"}

    def import_zip(self, payload, name):
        if len(payload) > MAX_IMPORT_BYTES:
            raise ValueError("Archive exceeds 600 MiB.")
        with tempfile.TemporaryDirectory(dir=self.workspace, prefix="import-") as tmp:
            with zipfile.ZipFile(io.BytesIO(payload)) as z:
                infos = z.infolist()
                if len(infos) > MAX_IMPORT_FILES or sum(i.file_size for i in infos) > MAX_IMPORT_BYTES:
                    raise ValueError("Expanded archive exceeds the 256-file / 600 MiB limit.")
                names = set()
                for info in infos:
                    p = contained(tmp, info.filename)
                    if p in names or (info.external_attr >> 16) & 0o170000 == 0o120000:
                        raise ValueError("Duplicate archive paths and symlinks are not supported.")
                    names.add(p)
                    if info.is_dir():
                        p.mkdir(parents=True, exist_ok=True)
                    else:
                        if p.suffix.lower() not in (".csv", ".fcs", ".json", ".txt"):
                            raise ValueError("Import supports metadata.csv and FCS files only (optional JSON/TXT notes).")
                        p.parent.mkdir(parents=True, exist_ok=True)
                        with z.open(info) as source, p.open("wb") as target:
                            shutil.copyfileobj(source, target)
            return self.import_directory(tmp, name)

    def validate_dataset(self, dataset):
        if dataset == "reference":
            return {**self.verify_release(), **self.api.validate_metadata(self.manifest)}
        base, experiment = self._check_import_identity(dataset)
        for row in experiment["samples"]:
            self.api.process_fcs(contained(base, row["file_path"]), self.context, row)
        return {"status": "PASS", "samples": len(experiment["samples"]), "RES": "TRANSFER_NOT_QUALIFIED"}

    def _check_import_identity(self, dataset):
        base = self.workspace / "imports" / safe_id(dataset)
        experiment = read_json(base / "experiment.json")
        if experiment["context_sha256"] != sha(self.root / "models/context_profiles/context_v1.json") or experiment["reference_manifest_sha256"] != self.release_hash:
            raise ValueError("Context/reference version changed; downstream artifacts invalidated.")
        self.validate_import_rows(experiment["samples"], base)
        return base, experiment

    def fit_references(self, csv_text, name="User reference fit"):
        rows = list(csv.DictReader(io.StringIO(csv_text)))
        required = {"well_id", "fraction", "ras", "context_id", "reporter_construct", "fraction_basis", "population_mode"}
        if not rows or not required.issubset(rows[0]):
            raise ValueError("Required reference columns: " + ", ".join(sorted(required)))
        wells = [safe_id(r["well_id"]) for r in rows]
        if len(set(wells)) != len(wells):
            raise ValueError("References require unique independent well IDs.")
        for key, expected in [("context_id", self.context["context_id"]), ("fraction_basis", "AC_DNA_mass_fraction"), ("population_mode", "reporter")]:
            if any(r[key] != expected for r in rows):
                raise ValueError("Reference " + key + " is incompatible with this research workflow.")
        if len({r["reporter_construct"] for r in rows}) != 1 or not rows[0]["reporter_construct"].strip():
            raise ValueError("One explicit reporter construct per calibration.")
        x = self.np.array([float(r["fraction"]) for r in rows]); y = self.np.array([float(r["ras"]) for r in rows])
        levels, counts = self.np.unique(x, return_counts=True)
        if len(levels) < 3 or min(counts) < 2:
            raise ValueError("Use at least 3 reference levels and 2 independent wells per level.")
        m = self.api.fit_reporter_calibration(x, y)
        inverse = importlib.import_module("inverse_calibration").inverse
        predict = importlib.import_module("reporter_calibration").predict
        validation = []
        for level in levels:
            train = x != level
            fitted = self.api.fit_reporter_calibration(x[train], y[train])
            for i in self.np.flatnonzero(~train):
                inv = inverse(fitted, y[i])
                validation.append({"well_id": wells[i], "held_fraction": float(level), "observed_ras": float(y[i]),
                    "predicted_ras": float(predict(fitted, [level])[0]) if fitted["x_min"] <= level <= fitted["x_max"] else None,
                    "inverse": inv, "error_pp": None if inv["point"] is None else 100 * (inv["point"] - level)})
        rng = self.np.random.default_rng(20261013)
        grid = self.np.linspace(m["x_min"], m["x_max"], 101)
        curves = []
        for _ in range(200):
            ix = self.np.concatenate([rng.choice(self.np.flatnonzero(x == v), int((x == v).sum()), replace=True) for v in levels])
            fitted = self.api.fit_reporter_calibration(x[ix], y[ix])
            curves.append(predict(fitted, grid))
        identifier = "research-" + uuid.uuid4().hex[:12]
        m.update(model_id=identifier, app_version=__version__, name=str(name)[:120], context_id=self.context["context_id"],
            context_sha256=sha(self.root / "models/context_profiles/context_v1.json"), population_mode="reporter",
            reference_rows=rows, independent_wells=len(wells), validation=validation,
            uncertainty={"grid": grid.tolist(), "lower": self.np.quantile(curves, .025, axis=0).tolist(),
                "upper": self.np.quantile(curves, .975, axis=0).tolist(), "draws": 200,
                "scope": "within-level well resampling only; no event or shared-control uncertainty; not validated coverage"},
            qualification="UNQUALIFIED_USER_RESEARCH_FIT_REQUIRES_SCIENTIFIC_REVIEW", routine_allowed=False,
            sample_application="NOT_IMPLEMENTED_UNTIL_SEPARATE_CONTEXT_DOMAIN_AND_MODEL_REVIEW")
        m = self.api.clean(m)
        write_json(self.workspace / "user_models" / (identifier + ".json"), m)
        return m
