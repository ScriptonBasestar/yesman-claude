

dev-install:
	pip install -e . --config-settings editable_mode=compat

dev-run-yesman:
	uv run ./yesman.py
