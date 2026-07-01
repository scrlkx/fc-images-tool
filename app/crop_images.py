import io
import zipfile
from datetime import datetime

import streamlit as st
from PIL import Image


def render():
    if "crop_uploader_key" not in st.session_state:
        st.session_state.crop_uploader_key = 0

    uploaded = st.file_uploader(
        "Images",
        type=["png"],
        accept_multiple_files=True,
        key=f"crop_images_{st.session_state.crop_uploader_key}",
    )

    if "crop_results" in st.session_state:
        result = st.session_state.crop_results

        def _clear():
            del st.session_state.crop_results
            st.session_state.crop_uploader_key += 1

        if len(result) == 1:
            st.download_button(
                label="Download",
                data=result[0],
                file_name=f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png",
                mime="image/png",
                on_click=_clear,
            )
        else:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for index, data in enumerate(result):
                    zf.writestr(f"{index + 1}.png", data)

            st.download_button(
                label="Download",
                data=zip_buffer.getvalue(),
                file_name=f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.zip",
                mime="application/zip",
                on_click=_clear,
            )
    else:
        if not uploaded:
            st.error("Please select at least 1 PNG image.")

        if uploaded and st.button("Crop"):
            with st.spinner("Cropping..."):
                result = []
                for file in uploaded:
                    image = Image.open(io.BytesIO(file.getvalue())).convert("RGBA")
                    bbox = image.getbbox()

                    if bbox is None or bbox == (0, 0, image.width, image.height):
                        continue

                    buf = io.BytesIO()
                    image.crop(bbox).save(buf, format="PNG")
                    result.append(buf.getvalue())

            if result:
                st.session_state.crop_results = result
                st.rerun()
            else:
                st.warning("No images needed cropping.")
