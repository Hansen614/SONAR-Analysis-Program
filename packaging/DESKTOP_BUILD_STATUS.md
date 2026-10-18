# SAP desktop candidate — 1.4.0rc1

Built and verified locally on 2026-10-18, macOS 26.5.2 / Apple Silicon / Python 3.13.7.

## Delivered

- `desktop-dist/SAP.app`: self-contained arm64 application, approximately 429 MiB on disk.
- `desktop-dist/SAP-1.4.0rc1-macos-arm64.dmg`: approximately 273 MiB, with SAP.app and Applications shortcut.
- `desktop-dist/BUILD_MANIFEST.json` and `SHA256SUMS.txt`: inputs, versions, source/asset hashes and package checksum.
- `packaging/SAP.spec`, `build_desktop.py`, locked Mac dependencies, Windows build instructions and `.github/workflows/desktop-build.yml`.

The graphical interface, Logo and scientific formulas are retained. The application uses pywebview/WKWebView and embeds Python through PyInstaller. It starts on Home in a dedicated window without a terminal. Experiment data and logs are stored under `~/Library/Application Support/SAP/`, or the experiment directory chosen by the user. The existing development workspace is untouched.

## Verification

- Existing application suite: 46 passed in the new isolated environment.
- New desktop lifecycle checks: 2 passed, including concurrent-process lock exclusion and release.
- Sequence design: 117 checks passed; fixed control oligos: 26 checks passed.
- Frozen application: all 883 scientific files verified; all 27 declared scientific dependency versions match; 10 API/static/download routes verified.
- Actual bundled FCS: RAS 0.9562602659677871; RES model estimate 0.7454898213131972, matching existing expected values within 1e-12 relative tolerance. Qualified RES remains null. Theta reused without refitting.
- Native GUI: design example through oligo output; CSV save dialog and saved file; actual FCS selection/upload; Theta preview; sample computation; report ZIP save; close terminates server; restart restores active experiment.
- Exported CSV parses into 3 rows; exported report ZIP passes integrity check with 14 files.
- Isolated relocated bundle: PASS with original project and system Python paths denied, non-loopback networking denied, and Chinese/space-containing output path. The sandbox was separately checked to actually reject access to original source. This is not a clean-machine certification or a universal macOS compatibility claim.
- Local ad-hoc code signature verifies. No Developer ID identity or notarization is present.

Evidence is saved in `verification/SAP_desktop_self_test.json`, `SAP_desktop_isolation_test.json`, the isolation profile and native GUI screenshots. The scientific pipeline source hash is unchanged.

## Remaining release work

This is a working local candidate, not a public signed release. Windows and Intel Mac binaries have not been built or tested. The workflow is prepared locally but has not been pushed or run on GitHub; no download release has been published.

Before external publication: Windows native build with a verified WebView2 Fixed Runtime; clean-system GUI and offline tests on supported targets; Developer ID signing, hardened runtime/notarization/stapling for macOS; Windows signing plan; project license and distribution permission review; third-party notices; publish verified artifacts to GitHub Releases. macOS 14 is the configured build floor based on dependencies, but only macOS 26.5.2 has been tested here.
