# Next application requirements
Product: SONAR — RNA Editing Reporter Measurement Toolkit. Scientificbackend must remain GUI-independent. A lightweight Streamlit UI is an acceptable first application; no GUI has been built here.

Priority 1 reproduce the frozen engine; priority2 installablePythonpackage without changingmath; priority3 CLI/import/reporting; priority4 accessibleGUI; priority5 versionedmodel loading and user-referencefitting; priority6 validation/errors/export; priority7 docs/examples/releasepackaging. The fuller instructions are in CODEX_IMPLEMENTATION_PROMPT.md.

Workflow: import FCS+controls+requiredwell metadata; inspectContext/QC; calculateRASwith declaredpopulation; loadcompatiblemodel or fit reviewable user reference; inspectRESforward/inverse/uncertainty/domains; evaluate qualifiedmolecular data; export table+report+provenance bundle. RESmust be prominent and understandable. Show source and correctedlabels together. KeepQC,numericalavailability andinterpretationpermissions separate. Never substitute a percentage editing label for RESorrelative chromatogram index. Missing data are notzero; error states must be informative.

New panel/instrument support is a versionedcontext extension; no silent channel guess, automatic unverified compensation or arbitrary reuse ofS7 calibration. A supplied absolutemolecular model requires a reviewed qualification adapter; v1 always returns PER null. Preserve all frozen tests and add meaningful import/export/error-flow integrationtests.
