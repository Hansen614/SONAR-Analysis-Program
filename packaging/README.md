# Desktop build

The existing local HTTP API and UI run in pywebview. The server binds to loopback only. PyInstaller onedir embeds Python, native libraries, UI assets and all 883 manifest-registered scientific files. Scientific code is collected as source to preserve the existing file identity checks. No analysis formula is changed.

## Build (maintainers only)

Use an isolated Python 3.13 environment with system-site-packages disabled.

macOS arm64 (tested dependency lock):

```sh
python3.13 -m venv .desktop-venv
.desktop-venv/bin/python -m pip install -r packaging/requirements-macos-arm64.lock.txt
.desktop-venv/bin/python packaging/build_desktop.py
```

Windows x64 (native Windows build; dependency lock captured from the successful candidate):

```powershell
py -3.13 -m venv .desktop-venv
.desktop-venv\Scripts\python -m pip install -r packaging/requirements-windows-x64.lock.txt
$env:SAP_WEBVIEW2_RUNTIME = "C:\build\WebView2"
.desktop-venv\Scripts\python packaging/build_desktop.py
```

Obtain the x64 Fixed Version WebView2 Runtime from Microsoft, verify its downloaded SHA256 against your recorded release input, and extract it before building. Set SAP_WEBVIEW2_RUNTIME to the directory directly containing msedgewebview2.exe. The build refuses to silently omit it. The committed Windows lock records the dependencies from the successful native build. macOS Intel also requires its own native build and QA.

Outputs: desktop-dist/SAP.app or desktop-dist/SAP/, architecture-specific DMG/ZIP, BUILD_MANIFEST.json, SHA256SUMS.txt. A frozen self-test runs real Mock and sample FCS through Theta/RAS/RES, checks the manifest, downloads, source identity and dependency metadata. Test data goes into _work/frozen-self-test, never the user's experiment workspace.

The workflow in .github/workflows/desktop-build.yml prepares candidate artifacts only; it does not publish Releases. Windows requires a verified Fixed Runtime URL and hash supplied at dispatch. Before a public release: select a project license, review redistribution permissions, collect dependency notices, sign binaries, notarize/staple macOS, and pass clean-system/offline GUI acceptance tests. Code signing secrets must not be committed.

## Public preview packaging

The build collects original third-party notices, includes the SAP MIT license, and excludes unused HEIC codec binaries while retaining scientific environment metadata. Both platforms run the frozen real-FCS test and a native GUI self-test. Windows asks users to acknowledge Microsoft Runtime terms once, before opening the analysis UI; diagnostic CI modes are noninteractive. Set SAP_DIST_DIR to an alternate output directory to preserve older candidates. Public release assets are built from the release commit, with per-platform manifests and combined SHA256 checksums.
