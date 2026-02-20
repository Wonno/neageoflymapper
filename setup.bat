@echo off
python --version && python -m venv env && CALL env\Scripts\activate && python -m pip install --upgrade pip && python -m pip install -r requirements.txt && (
	echo DONE
) || (
	echo FAILED
)
echo Press ENTER to exit.
pause >nul
