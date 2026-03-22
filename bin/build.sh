#!/bin/bash
echo "My Voice Build Helper"
echo "Installing deps if needed..."
python -m pip install --user pygobject
echo "To run: python -m src.agents.gui"
echo "For packaging: pyinstaller --onefile --windowed src/agents/gui.py"
