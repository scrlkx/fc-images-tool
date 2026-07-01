import io
from datetime import datetime

import requests
import streamlit as st
from PIL import Image
from rembg import new_session, remove


def render():
    if "dh_url_input_key" not in st.session_state:
        st.session_state.dh_url_input_key = 0

    def _reset():
        for key in ["dh_image", "dh_bg_removed", "dh_cropped"]:
            st.session_state.pop(key, None)
        st.session_state.dh_url_input_key += 1

    if "dh_image" not in st.session_state:
        url = st.text_input(
            "Image URL",
            key=f"dh_url_{st.session_state.dh_url_input_key}",
        )
        if st.button("Download and Save", disabled=not url, key="dh_download_save"):
            try:
                with st.spinner("Downloading..."):
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    image_bytes = response.content

                    img = Image.open(io.BytesIO(image_bytes))
                    if img.format != "PNG":
                        img = img.convert("RGBA")
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        image_bytes = buf.getvalue()

                st.session_state.dh_image = image_bytes
                st.session_state.dh_bg_removed = False
                st.session_state.dh_cropped = False
                st.rerun()
            except Exception as e:
                st.error(f"Failed to download image: {e}")
    else:
        image_bytes = st.session_state.dh_image

        st.image(image_bytes)

        if not st.session_state.dh_cropped:
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(
                    "Remove Background",
                    disabled=st.session_state.dh_bg_removed,
                    key="dh_remove_bg",
                ):
                    with st.spinner("Removing background..."):
                        session = new_session("birefnet-general-lite")
                        result = remove(image_bytes, session=session)
                    st.session_state.dh_image = result
                    st.session_state.dh_bg_removed = True
                    st.rerun()
            with col2:
                if st.button("Crop", key="dh_crop"):
                    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
                    bbox = img.getbbox()
                    if bbox and bbox != (0, 0, img.width, img.height):
                        buf = io.BytesIO()
                        img.crop(bbox).save(buf, format="PNG")
                        st.session_state.dh_image = buf.getvalue()
                    st.session_state.dh_cropped = True
                    st.rerun()
            with col3:
                if st.button(
                    "Remove Background and Crop",
                    disabled=st.session_state.dh_bg_removed,
                    key="dh_remove_bg_and_crop",
                ):
                    with st.spinner("Removing background..."):
                        session = new_session("birefnet-general-lite")
                        result = remove(image_bytes, session=session)
                    img = Image.open(io.BytesIO(result)).convert("RGBA")
                    bbox = img.getbbox()
                    if bbox and bbox != (0, 0, img.width, img.height):
                        buf = io.BytesIO()
                        img.crop(bbox).save(buf, format="PNG")
                        result = buf.getvalue()
                    st.session_state.dh_image = result
                    st.session_state.dh_bg_removed = True
                    st.session_state.dh_cropped = True
                    st.rerun()

        col_dl, col_reset = st.columns(2)
        with col_dl:
            st.download_button(
                label="Download",
                data=st.session_state.dh_image,
                file_name=f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png",
                mime="image/png",
                key="dh_download",
            )
        with col_reset:
            st.button("Reset", on_click=_reset, key="dh_reset")
