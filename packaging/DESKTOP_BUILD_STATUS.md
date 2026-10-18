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

macOS arm64 and Windows x64 candidates have been built and tested as recorded here. Intel Mac remains unbuilt. The repository and Actions artifacts are private; no public signed release has been published.

Before external publication: clean-system GUI and offline tests on supported targets; Developer ID signing, hardened runtime/notarization/stapling for macOS; Windows signing plan; project license and distribution permission review; third-party notices; publish verified artifacts to GitHub Releases. macOS 14 is the configured build floor based on dependencies, but only macOS 26.5.2 has been tested here.

## Windows build completed — 2026-10-18

Source and all 883 frozen scientific reference files were uploaded to the user's private repository with explicit authorization. User workspaces, caches, local QA exports and build environments were excluded.

- Repository: https://github.com/Hansen614/SONAR-Analysis-Program
- Successful run: https://github.com/Hansen614/SONAR-Analysis-Program/actions/runs/39100443668
- Built source: b59fa6d9184a0317fcfb29f01863ed524814a6e8
- Artifact: SAP-windows-x64-candidate / SAP-1.4.0rc1-windows-x64-portable.zip
- Python tests: 48 passed; design checks: 117 passed; control oligos: 26 passed.
- Frozen executable: actual FCS self-test, reference hashes, dependency metadata, API and export checks passed.
- Native WebView: Home, Design, Construction and Analysis pages load; oligo engine produces expected sequences; process path confirms use of the bundled WebView2 Fixed Runtime.
- Microsoft runtime: 155.0.4283.62 x64; CAB SHA256 pinned in packaging/webview2-windows-x64.json; Microsoft executable signature validated in CI.
- First CI run exposed a missing test-output directory on a clean checkout; the test now creates that directory. No scientific algorithm was changed.

The repository remains private. This is an unsigned candidate artifact, not a public GitHub Release. Manual Windows 11 user acceptance and signing remain pending.

Local download verification passed: ZIP integrity, Windows x64 GUI executable, bundled Python/WebView2 and all 883 scientific file hashes. Portable ZIP size: 608898510 bytes; SHA256: `8411361a14952f2d1959d4b3a1b38e1531bafa5049cf106a3931f37c0d1fd215`. The exact resolved Windows dependency lock is retained in `packaging/requirements-windows-x64.lock.txt`.
