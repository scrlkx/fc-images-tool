import io
import zipfile
from datetime import datetime

import streamlit as st
from rembg import new_session, remove


def render():
    uploaded = st.file_uploader(
        "Images",
        type=["png", "jpg", "jpeg", "webp", "avif"],
        accept_multiple_files=True,
        key="remove_background_images",
    )

    if not uploaded:
        st.session_state.pop("remove_background_results", None)
        return

    if st.button("Remove backgrounds", key="remove_background"):
        session = new_session("birefnet-general-lite")
        results = []
        progress = st.progress(0)

        with st.status("Removing backgrounds...", expanded=True) as status:
            for index, file in enumerate(uploaded):
                st.write(f"Processing {file.name}...")

                result_bytes = remove(file.getvalue(), session=session)
                stem = file.name.rsplit(".", 1)[0]
                results.append((stem, result_bytes))
                progress.progress((index + 1) / len(uploaded))

            status.update(label="Done!", state="complete")

        st.session_state.remove_background_results = results

    if not st.session_state.get("remove_background_results"):
        return

    results = st.session_state.remove_background_results

    if len(results) == 1:
        stem, data = results[0]
        st.download_button(
            label="Download image",
            data=data,
            file_name=f"{stem}.png",
            mime="image/png",
        )
    else:
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as file:
            for stem, data in results:
                file.writestr(f"{stem}.png", data)

        st.download_button(
            label="Download images",
            data=zip_buffer.getvalue(),
            file_name=f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.zip",
            mime="application/zip",
        )
