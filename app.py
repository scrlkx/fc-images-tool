import streamlit as st

from app.convert_images_format import render as render_convert_images_format
from app.crop_images import render as render_crop_images
from app.draw_product_set import render as render_draw_product_set
from app.generate_figma_schema import render as render_generate_figma_schema
from app.remove_images_background import render as render_remove_images_background

st.set_page_config(page_title="FC Images Tool", layout="wide")
st.title("FC Images Tool")

(
    convert_images_format,
    remove_images_background,
    crop_images,
    draw_product_set,
    generate_figma_schema,
) = st.tabs(
    [
        "Convert Images Format",
        "Remove Images Background",
        "Crop Images",
        "Draw Product Set",
        "Generate Figma Schema",
    ]
)

with convert_images_format:
    render_convert_images_format()

with remove_images_background:
    render_remove_images_background()

with crop_images:
    render_crop_images()

with draw_product_set:
    render_draw_product_set()

with generate_figma_schema:
    render_generate_figma_schema()
