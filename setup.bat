@echo off
python --version && python -m venv .venv && CALL .venv\Scripts\activate && python -m pip install --upgrade pip && python -m pip install -r requirements.txt && (
	echo DONE
) || (
	echo FAILED
)
echo Press ENTER to exit.
pause >nul
