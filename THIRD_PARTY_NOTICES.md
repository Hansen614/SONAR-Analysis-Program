# Third-party notices

SAP's original source code is licensed under MIT (see LICENSE). This does not relicense third-party software, fonts, logos/trademarks or externally sourced materials. Scientific reference files retain their provenance and are included for reproducibility; their integrity manifest is unchanged.

Desktop distributions contain a THIRD_PARTY_NOTICES directory with original license texts collected from the exact build environment, dependency versions, upstream references, Python's license and supplementary notices. The inventory includes build/test dependencies as well as runtime dependencies; listing a package does not imply all its code is included.

- Python: Python Software Foundation license and bundled notices.
- NumPy, SciPy, pandas, scikit-learn, Matplotlib and other scientific dependencies: retain their respective original notices, including bundled native-library notices and applicable runtime exceptions.
- pywebview, pythonnet, PyObjC and related components: original notices in the inventory.
- PyInstaller: GPL with its bootloader exception; the exception allows distribution of the generated application under its own license. See the complete COPYING text in the inventory.
- Manrope font: SIL Open Font License; original OFL and attribution are included in sonar_app/static/fonts.
- Microsoft WebView2 Fixed Runtime (Windows only): proprietary Microsoft redistributable, separate from SAP's MIT license. It is distributed unchanged from Microsoft's signed download. The original terms are included in `supplemental/Microsoft-WebView2-Fixed-Runtime.html`; Windows users must acknowledge them on first launch. Microsoft Defender SmartScreen is included and may collect and send information to Microsoft (https://aka.ms/privacy). See https://developer.microsoft.com/en-us/microsoft-edge/webview2 and https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution. Third-party notices shipped inside the Runtime are retained; its show_third_party_software_licenses.bat is Microsoft's notice viewer. Runtime updates are delivered with SAP updates, not automatically by this fixed-runtime package.

The unused pillow-heif decoder, libheif, libde265 and x265 binaries are explicitly excluded from SAP desktop distributions. Only pillow-heif distribution metadata is retained to document the frozen reference environment; SAP does not import this optional decoder. This exclusion does not change sequence design or FCS analysis.

SAP is a research tool. The license does not change the scientific scope or validate a model estimate as a direct RNA editing measurement. No trademark or endorsement rights are granted.
