# SAP desktop candidate — 1.4.0rc1

These are test candidates, not yet signed public releases.

## macOS (Apple Silicon)

Open the DMG, drag SAP.app to Applications, then open SAP. The app includes Python and its scientific dependencies. It opens its own window; no terminal is needed. The current candidate is ad-hoc signed, not Developer ID signed or notarized. Distribution to other Macs is pending signing and clean-machine verification. Do not disable system security to run an untrusted copy.

## Windows

Download **SAP-windows-x64-candidate** from the [successful GitHub Actions run](https://github.com/Hansen614/SONAR-Analysis-Program/actions/runs/39100443668). Sign in with an account that has access to the private repository. Extract that artifact, then fully extract SAP-1.4.0rc1-windows-x64-portable.zip. Open SAP/SAP.exe. Keep the entire SAP directory together, including _internal. Python and the Microsoft WebView2 Fixed Runtime are included; no command line or Python installation is required.

The candidate is built and automatically tested on GitHub's Windows Server 2022 x64 runner. Manual clean-machine Windows 11 acceptance and Windows code signing remain pending. Do not disable system security to run an untrusted copy.

## Data and examples

Choose Design or Analysis on the home page. Example buttons appear on input stages. Complete the control upload, review Theta, upload samples, then compute results. Existing scientific qualification and uncertainty labels apply.

Your saved experiments are separate from the application. Default data and logs:

- macOS: ~/Library/Application Support/SAP/
- Windows: %LOCALAPPDATA%/SAP/

Experiments saved to a custom location remain there. Replacing the application does not delete them. The desktop workspace starts separately from the existing browser-development workspace; that workspace is not deleted or included in the app.

Wait for calculations or exports to finish before closing. SAP prevents a second desktop instance from writing to the same workspace. Startup errors point to logs/SAP.log.
