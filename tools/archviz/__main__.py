"""Allow running archviz with `python -m tools.archviz`."""

from tools.archviz.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
