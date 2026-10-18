# SAP v1.4.0rc1 — installation and examples

This public desktop preview is not a signed stable release. Download only from:
https://github.com/Hansen614/SONAR-Analysis-Program/releases/tag/v1.4.0rc1

## Windows x64

Download `SAP-1.4.0rc1-windows-x64-portable.zip`. Fully extract it, then open `SAP/SAP.exe`. Keep the entire SAP directory together, including `_internal`. Python and Microsoft WebView2 Fixed Runtime are included; no separate Python installation or terminal is required.

On first Windows launch, review the separate Microsoft WebView2 terms. Choose Yes to agree and continue, No to exit, or Cancel to read the full terms. WebView2 includes Microsoft Defender SmartScreen and may collect and send information to Microsoft; see https://aka.ms/privacy and https://learn.microsoft.com/en-us/microsoft-edge/privacy-whitepaper#smartscreen. SAP does not upload your experiment files for analysis.

Windows Server 2022 x64 is the automated test platform. Clean-machine manual Windows 11 acceptance remains pending. This executable is unsigned and may trigger security warnings. Do not disable security or bypass malware warnings; report startup problems through GitHub Issues.

## macOS Apple Silicon

Download `SAP-1.4.0rc1-macos-arm64.dmg`, open it, drag SAP.app to Applications, then open SAP. The app contains Python and its scientific dependencies. It is ad-hoc signed, not Developer ID signed or notarized; macOS may block opening a downloaded copy. Do not disable Gatekeeper or remove security protections to work around this preview's signing limitation.

The build targets macOS 14 or later on Apple Silicon, with local testing on macOS 26.5.2. Intel Macs are not supported by this package.

## Try the examples

1. Open **Design** and load the example on the input page. Review the selected editing site and highlighted regions, confirm the sequence conversion and inspect/export oligos.
2. Open **Analysis** and start an experiment. Load the example during input stages, review Theta, continue to sample upload and compute the result.
3. Inspect results and export a report. Example inputs and the reference data are bundled; an internet connection is not needed for scientific computation.

Examples demonstrate the workflow. RES estimates retain their model/transfer qualification; they are not direct RNA editing percentages.

## Your data

The application stores experiments separately from its installation folder:

- macOS: `~/Library/Application Support/SAP/`
- Windows: `%LOCALAPPDATA%/SAP/`

Experiments saved to a custom location remain there. Replacing the application does not delete them. Never save personal experiments inside the installation folder. Wait for calculations and exports to finish before closing. Only one SAP instance may write to the same desktop workspace. Startup logs are in `logs/SAP.log` under the default data directory.

## Licenses and updates

MIT applies to original SAP code. Read LICENSE and THIRD_PARTY_NOTICES for third-party terms. The Windows fixed browser runtime updates with SAP releases. Obtain updates from this repository's Releases page; there is no automatic SAP updater.
