.PHONY: run-ui install-desktop uninstall-desktop lint install-hooks

run-ui:
	.venv/bin/streamlit run app.py

install-desktop:
	@bash create-desktop-shortcut.sh "$(CURDIR)"

uninstall-desktop:
	rm -f $(HOME)/.local/share/applications/fc-images-tool.desktop
	@echo "Shortcut removed."

lint:
	.venv/bin/ruff check app.py app
	.venv/bin/ruff format --check app.py app
	.venv/bin/pyright

install-hooks:
	.venv/bin/lefthook install
