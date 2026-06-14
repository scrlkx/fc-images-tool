import io
from datetime import datetime

import streamlit as st
from PIL import Image

GAP_MIN = 10
GAP_MAX = 60
GAP_RATIO = 0.05


def _compute_auto_gap(file_bytes_list: list[bytes]) -> int:
    images = [Image.open(io.BytesIO(bytes)) for bytes in file_bytes_list]
    min_height = min(img.height for img in images)
    widths = []

    for image in images:
        if image.height != min_height:
            widths.append(round(image.width * min_height / image.height))
        else:
            widths.append(image.width)

    avg_width = sum(widths) / len(widths)

    return max(GAP_MIN, min(GAP_MAX, round(avg_width * GAP_RATIO)))


def _build_set_bytes(file_bytes: list[bytes], gap: int) -> bytes:
    images = [Image.open(io.BytesIO(bytes)).convert("RGBA") for bytes in file_bytes]
    min_height = min(image.height for image in images)
    resized = []

    for image in images:
        if image.height != min_height:
            new_width = round(image.width * min_height / image.height)
            image = image.resize((new_width, min_height), Image.Resampling.LANCZOS)

        resized.append(image)

    total_width = sum(img.width for img in resized) + gap * (len(resized) - 1)
    canvas = Image.new("RGBA", (total_width, min_height), (0, 0, 0, 0))
    x = 0

    for image in resized:
        canvas.paste(image, (x, 0))
        x += image.width + gap

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")

    return buf.getvalue()


def render():
    uploaded = st.file_uploader(
        "Images",
        type=["png"],
        accept_multiple_files=True,
    )

    if uploaded and not (2 <= len(uploaded) <= 6):
        st.error("Please select between 2 and 6 PNG images.")
        return

    if uploaded and 2 <= len(uploaded) <= 6:
        files_bytes = [file.getvalue() for file in uploaded]
        auto_gap = _compute_auto_gap(files_bytes)
        gap = st.number_input("Gap (px)", min_value=0, value=auto_gap, step=1)

        set_bytes = _build_set_bytes(files_bytes, int(gap))
        st.image(set_bytes, caption="Preview")

        st.download_button(
            label="Download set",
            data=set_bytes,
            file_name=f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png",
            mime="image/png",
        )
