import io
import zipfile
from datetime import datetime

import streamlit as st
from PIL import Image


def render():
    if "convert_uploader_key" not in st.session_state:
        st.session_state.convert_uploader_key = 0

    uploaded = st.file_uploader(
        "Images",
        type=["jpg", "jpeg", "webp", "avif"],
        accept_multiple_files=True,
        key=f"convert_images_{st.session_state.convert_uploader_key}",
    )

    if "convert_results" in st.session_state:
        result = st.session_state.convert_results

        def _clear():
            del st.session_state.convert_results
            st.session_state.convert_uploader_key += 1

        if len(result) == 1:
            stem, data = result[0]
            st.download_button(
                label="Download",
                data=data,
                file_name=f"{stem}.png",
                mime="image/png",
                on_click=_clear,
            )
        else:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for stem, data in result:
                    zf.writestr(f"{stem}.png", data)

            st.download_button(
                label="Download",
                data=zip_buffer.getvalue(),
                file_name=f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.zip",
                mime="application/zip",
                on_click=_clear,
            )
    else:
        if st.button("Convert", disabled=not uploaded):
            with st.spinner("Converting..."):
                result = []
                for file in uploaded:
                    image = Image.open(io.BytesIO(file.getvalue())).convert("RGBA")
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                    stem = file.name.rsplit(".", 1)[0]
                    result.append((stem, buf.getvalue()))

            st.session_state.convert_results = result
            st.rerun()
