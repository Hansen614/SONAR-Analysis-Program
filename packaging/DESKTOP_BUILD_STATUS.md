# SAP v1.4.0rc1 — public desktop preview

Published on 2026-10-18 (Asia/Shanghai).

- Public MIT-licensed source: https://github.com/Hansen614/SONAR-Analysis-Program
- Release and downloads: https://github.com/Hansen614/SONAR-Analysis-Program/releases/tag/v1.4.0rc1
- Tagged application/build source: `18587af088848e05c061ffccec35c53fff360e6f`
- Windows build: https://github.com/Hansen614/SONAR-Analysis-Program/actions/runs/39102672849
- Windows archive validation and delivery: https://github.com/Hansen614/SONAR-Analysis-Program/actions/runs/39110537992

## Released packages

| Package | Bytes | SHA256 |
| --- | ---: | --- |
| SAP-1.4.0rc1-windows-x64-portable.zip | 602824153 | `0a6cc37a87c03e7e64dd6b8f6647643cd142801da7213f372885a726ee6a66ca` |
| SAP-1.4.0rc1-macos-arm64.dmg | 282796862 | `337e777018138ff643802a280a8b3eb9b50db853beea1b52c099bf35463d8834` |

Both are self-contained desktop packages with Python, existing SAP UI/assets, licenses and all 883 frozen scientific reference files. Windows also includes Microsoft's fixed WebView2 Runtime and a first-launch terms acknowledgement. The unused HEIC codec binaries are excluded. Scientific algorithms, reference file bytes and graphical analysis/design pages are unchanged.

## Completed verification

- Windows: 49 Python tests passed; sequence and control-oligo checks passed; frozen real-FCS/API/export tests passed; native Home/Design/Construction/Analysis GUI checks passed and verified use of the bundled WebView2 process.
- macOS: frozen real-FCS/API/export and native GUI tests passed; DMG CRC check passed; the actual DMG was mounted read-only, and its ad-hoc signature, packaged source hashes, license inventory and all 883 reference hashes were verified.
- Both frozen pipelines produced RAS `0.9562602659677871`, RES model estimate `0.7454898213131972`, and null qualified RES for the bundled acceptance example. Theta was reused without refitting.
- Windows portable ZIP CRC, x64 GUI subsystem (no console), embedded Python/browser, source hashes and all reference hashes passed archive checks.
- GitHub upload digests match the verified package digests. Unauthenticated requests confirmed the public MIT repository, published pre-release and HTTP 200 downloads for both packages, with matching byte lengths.
- Per-platform build manifests, verification JSON, dependency locks and combined SHA256SUMS.txt are attached to the Release.

The macOS build began at the tagged source. A delivery/documentation-only commit was added while it ran; the manifest records both that later checkout head and the verified build-source commit. Every packaged application source hash and packaging input was checked against the tag.

## Remaining work before a signed stable release

Windows signing and manual clean Windows 11 acceptance; macOS Developer ID signing/notarization/stapling and additional supported-version clean-system acceptance. The configured macOS floor is 14; local native tests used macOS 26.5.2 Apple Silicon. Intel Mac and Windows ARM64 packages have not been built. This is a public **pre-release**, not a signed stable release; OS security can block first launch.

The earlier local candidates and Actions artifacts are superseded by the two release packages above. Use the fixed Release links in `docs/WIKI_CONTRIBUTION.md` for Wiki download buttons. That file supplies copy/links; it does not itself deploy the Wiki.
