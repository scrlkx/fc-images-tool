# fc-images-tool

Streamlit webapp for product image processing: converts formats, removes backgrounds with AI, crops objects, builds horizontal product sets, and exports metadata for the Figma plugin.

**Tabs:**

| Tab | Function |
|-----|----------|
| Convert Images Format | WebP, AVIF, JPEG → PNG (RGBA) |
| Remove Background | Removes backgrounds using the BiRefNet model via `rembg` |
| Crop Images | Trims transparent padding around objects |
| Draw Product Set | Aligns 2–6 images side by side as a set |
| Generate Figma Schema | Generates the JSON for the sales slides Figma plugin |

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/scrlkx/fc-images-tool/main/install.sh | bash
```

Requirements: Python 3.10+ and git.

> **First run** downloads the birefnet-general-lite model (~1 GB) to `~/.u2net/`. One-time only.

## Usage

Open the **FC Images Tool** shortcut from the launcher.

## Figma Sales Plugin

Weekly sales slides can be generated directly in Figma using the plugin in `figma_plugin/`.

### Workflow

1. Open the webapp and go to the **Generate Figma Schema** tab.

2. Fill in the sales date, then add products one by one (name, prices, cover image). Download the generated `sales.json`.

3. Open Figma, load the plugin (`figma_plugin/`), select the target page and the generated JSON, and click **Generate Slides**. The plugin duplicates the Slide 1 / Slide 2 templates and fills in each product.

## Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/scrlkx/fc-images-tool/main/install.sh | bash -s -- --uninstall
```

This removes the desktop shortcut and `~/.local/share/fc-images-tool/`. The model cache at `~/.u2net/` is left in place — delete it manually if you no longer need it.

## Development

```bash
git clone git@github.com:scrlkx/fc-images-tool.git
cd fc-images-tool
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
make run-ui
```
