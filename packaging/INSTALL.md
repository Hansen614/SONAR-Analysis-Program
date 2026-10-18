# SAP desktop candidate — 1.4.0rc1

This is a local test build, not yet a signed public release.

## macOS (Apple Silicon)

Open the DMG, drag SAP.app to Applications, then open SAP. The app includes Python and its scientific dependencies. It opens its own window; no terminal is needed. The current candidate is ad-hoc signed, not Developer ID signed or notarized. Distribution to other Macs is pending signing and clean-machine verification. Do not disable system security to run an untrusted copy.

## Windows

After a Windows build is available, fully extract the portable ZIP and open SAP.exe inside the SAP directory. Keep the entire directory together. The offline build must include the Microsoft WebView2 Fixed Runtime. No Windows binary is produced by a Mac build.

## Data and examples

Choose Design or Analysis on the home page. Example buttons appear on input stages. Complete the control upload, review Theta, upload samples, then compute results. Existing scientific qualification and uncertainty labels apply.

Your saved experiments are separate from the application. Default data and logs:

- macOS: ~/Library/Application Support/SAP/
- Windows: %LOCALAPPDATA%/SAP/

Experiments saved to a custom location remain there. Replacing the application does not delete them. The desktop workspace starts separately from the existing browser-development workspace; that workspace is not deleted or included in the app.

Wait for calculations or exports to finish before closing. SAP prevents a second desktop instance from writing to the same workspace. Startup errors point to logs/SAP.log.
