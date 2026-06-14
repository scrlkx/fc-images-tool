import io
import zipfile
from datetime import datetime

import streamlit as st
from PIL import Image


def render():
    uploaded = st.file_uploader(
        "Images", type=["png"], accept_multiple_files=True, key="crop_images"
    )

    if uploaded and not (2 <= len(uploaded)):
        st.error("Please select more them 1 PNG images.")
        return

    files_bytes = [file.getvalue() for file in uploaded]
    images = [Image.open(io.BytesIO(bytes)).convert("RGBA") for bytes in files_bytes]

    result = []

    for image in images:
        bbox = image.getbbox()

        if bbox is None or bbox == (0, 0, image.width, image.height):
            continue

        result.append(image.crop(bbox))

    if not result:
        return

    target_file = None

    if len(result) == 1:
        target_file = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"

        image_buffer = io.BytesIO()
        result[0].save(image_buffer, format="PNG")

        st.download_button(
            label="Download cropped image",
            data=image_buffer.getvalue(),
            file_name=target_file,
            mime="image/png",
        )
    else:
        target_file = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.zip"

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip:
            for index, image in enumerate(result):
                image_buffer = io.BytesIO()
                image.save(image_buffer, format="PNG")

                zip.writestr(f"{index + 1}.png", image_buffer.getvalue())

        st.download_button(
            label="Download cropped images",
            data=zip_buffer.getvalue(),
            file_name=target_file,
            mime="application/zip",
        )
