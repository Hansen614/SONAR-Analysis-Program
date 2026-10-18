"""Frozen GUI entry point; no external Python interpreter is required."""
import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()
    from sonar_app.desktop import main
    raise SystemExit(main())
