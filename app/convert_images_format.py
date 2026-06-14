import io
import zipfile
from datetime import datetime

import streamlit as st
from PIL import Image


def render():
    uploaded = st.file_uploader(
        "Images",
        type=["jpg", "jpeg", "webp", "avif"],
        accept_multiple_files=True,
        key="convert_images",
    )

    if not uploaded:
        return

    images = [Image.open(io.BytesIO(f.getvalue())).convert("RGBA") for f in uploaded]

    result = []

    for image, file in zip(images, uploaded):
        buf = io.BytesIO()
        image.save(buf, format="PNG")

        stem = file.name.rsplit(".", 1)[0]
        result.append((stem, buf.getvalue()))

    if len(result) == 1:
        stem, data = result[0]
        st.download_button(
            label="Download converted image",
            data=data,
            file_name=f"{stem}.png",
            mime="image/png",
        )
    else:
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as file:
            for stem, data in result:
                file.writestr(f"{stem}.png", data)

        st.download_button(
            label="Download converted images",
            data=zip_buffer.getvalue(),
            file_name=f"converted_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.zip",
            mime="application/zip",
        )
