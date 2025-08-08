#!/usr/bin/env python3
"""
StrandsFlow package entry point.

This allows the package to be run as a module:
python -m strandsflow
"""

from .cli import app

if __name__ == "__main__":
    app()
