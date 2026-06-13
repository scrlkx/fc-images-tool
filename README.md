# fc-images

Batch-converts WebP, AVIF, and JPEG images to PNG, removes backgrounds using the [birefnet-general-lite](https://github.com/ZhengPeng7/BiRefNet) AI model, and crops the transparent padding around each object.

Installs as:

- **`fc-images`** — CLI command available system-wide
- **Nautilus right-click menu** — four actions on any directory, plus sales metadata generation on CSV files (if Nautilus is installed)

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/scrlkx/fc-images/main/install.sh | bash
```

Requirements: Linux, Python 3.10+, git.

> **First run** downloads the birefnet-general model (~1 GB) to `~/.u2net/`. One-time only.

### Nautilus extension

Installed automatically if Nautilus and `nautilus-python` are present. If `nautilus-python` is missing, the installer prints the install command for your distro and asks you to re-run.

## Usage

```bash
# Full pipeline: convert formats + remove backgrounds + crop objects
fc-images /path/to/directory

# Convert formats only (WebP/AVIF/JPEG → PNG, keep backgrounds)
fc-images /path/to/directory --keep-background

# Remove backgrounds only (operates on existing PNGs)
fc-images /path/to/directory --backgrounds-only

# Crop only: trim transparent padding from existing PNGs
fc-images /path/to/directory --crop-only
```

Original files are deleted after conversion. Background removal and cropping overwrite PNGs in place.

The crop step detects the bounding box of non-transparent pixels and removes the surrounding empty area. It only processes RGBA PNGs and skips images with no transparency.

## Figma Sales Plugin

Weekly sales slides can be generated directly in Figma using the plugin in `figma_plugin/`.

### Workflow

1. Prepare a semicolon-delimited CSV with one product per line:

   ```
   image_filename;product_name;previous_price;new_price
   ```

   Images must live in the same directory as the CSV.

2. Generate the metadata JSON (right-click the CSV in Nautilus → **Generate Sales Metadata**, then pick the sales date from the calendar — or run it directly):

   ```bash
   python generate_figma_metadata.py /path/to/sales.csv --data 2026-06-14
   ```

   This produces a `sales.json` alongside the CSV containing product names, prices, base64-encoded images, the frame name, and the validity period in Portuguese.

3. Open Figma, load the plugin (`figma_plugin/`), select the target page and the generated JSON, and click **Generate Slides**. The plugin duplicates the Slide 1 / Slide 2 templates and fills in each product.

## Update

Re-run the install command. Dependencies are only reinstalled if `requirements.txt` changed.

## Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/scrlkx/fc-images/main/install.sh | bash -s -- --uninstall
```

This removes `~/.local/bin/fc-images`, the Nautilus extension, and `~/.local/share/fc-images/`. The model cache at `~/.u2net/` is left in place — delete it manually if you no longer need it.

## Development

```bash
git clone https://github.com/scrlkx/fc-images
cd fc-images
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
make install-extension && make restart-nautilus
```
