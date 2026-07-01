import io
import zipfile
from datetime import datetime

import streamlit as st
from rembg import new_session, remove


def render():
    if "remove_bg_uploader_key" not in st.session_state:
        st.session_state.remove_bg_uploader_key = 0

    uploaded = st.file_uploader(
        "Images",
        type=["png", "jpg", "jpeg", "webp", "avif"],
        accept_multiple_files=True,
        key=f"remove_background_images_{st.session_state.remove_bg_uploader_key}",
    )

    if not uploaded:
        st.session_state.pop("remove_background_results", None)
        return

    if "remove_background_results" in st.session_state:
        results = st.session_state.remove_background_results

        def _clear():
            del st.session_state.remove_background_results
            st.session_state.remove_bg_uploader_key += 1

        if len(results) == 1:
            stem, data = results[0]
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
                for stem, data in results:
                    zf.writestr(f"{stem}.png", data)

            st.download_button(
                label="Download",
                data=zip_buffer.getvalue(),
                file_name=f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.zip",
                mime="application/zip",
                on_click=_clear,
            )
    else:
        if st.button("Remove Background", key="remove_background"):
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
            st.rerun()
