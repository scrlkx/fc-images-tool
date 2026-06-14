import base64
import json
import re
from datetime import date, timedelta

import pandas as pd
import streamlit as st

MONTHS_PT_NAME = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


def _validity_text(target: date) -> str:
    end = target + timedelta(days=7)

    return (
        f"Ofertas válidas de {target.strftime('%d/%m')} até "
        f"{end.strftime('%d/%m')} ou enquanto durarem os estoques."
    )


def render():
    if "products" not in st.session_state:
        st.session_state.products = pd.DataFrame(
            columns=[
                "Cover image",
                "Title",
                "Current price",
                "New price",
                "image_b64",
            ]
        )

    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    if "campaign_date" not in st.session_state:
        st.session_state.campaign_date = date.today() + timedelta(days=1)

    if "success_message" in st.session_state:
        st.success(st.session_state.success_message)
        del st.session_state.success_message

    if not st.session_state.products.empty:
        edited_df = st.data_editor(
            st.session_state.products.assign(Delete=False),
            hide_index=True,
            width="stretch",
            column_config={
                "Delete": st.column_config.CheckboxColumn(
                    "Delete",
                    help="Select rows to remove",
                ),
                "image_b64": None,
            },
            disabled=[
                "Cover image",
                "Title",
                "Current price",
                "New price",
                "image_b64",
            ],
        )

        if st.button("Remove selected"):
            st.session_state.products = (
                edited_df[~edited_df["Delete"]]
                .drop(columns=["Delete"])
                .reset_index(drop=True)
            )

            st.session_state.success_message = "Selected products removed!"
            st.rerun()
    else:
        st.dataframe(
            st.session_state.products,
            hide_index=True,
            width="stretch",
        )

    with st.form("product_form", clear_on_submit=True):
        uploaded_image = st.file_uploader(
            "Cover image",
            type=["png"],
            accept_multiple_files=False,
            key=f"cover_image_{st.session_state.uploader_key}",
        )

        title = st.text_input(
            "Title",
            placeholder="Body Splash Hidrabene Derma",
            key="title",
        )

        current_price = st.text_input(
            "Current price",
            placeholder="45,90",
            key="current_price",
        )

        new_price = st.text_input(
            "New price",
            placeholder="39,50",
            key="new_price",
        )

        submitted = st.form_submit_button("Add to set")

    if submitted:
        errors = []

        if uploaded_image is None:
            errors.append("Cover image is required.")

        if not title.strip():
            errors.append("Title is required.")

        if not current_price.strip():
            errors.append("Current price is required.")

        if not new_price.strip():
            errors.append("New price is required.")

        price_pattern = r"^\d+,\d{2}$"

        if current_price and not re.match(price_pattern, current_price):
            errors.append("Current price must be in the format XXX,XX.")

        if new_price and not re.match(price_pattern, new_price):
            errors.append("New price must be in the format XXX,XX.")

        if errors:
            for error in errors:
                st.error(error)
        else:
            assert uploaded_image is not None

            st.session_state.products.loc[len(st.session_state.products)] = {
                "Cover image": uploaded_image.name,
                "Title": title,
                "Current price": current_price,
                "New price": new_price,
                "image_b64": (
                    "data:image/png;base64,"
                    + base64.b64encode(uploaded_image.getvalue()).decode()
                ),
            }

            st.session_state.success_message = "Product added to the set!"
            st.session_state.uploader_key += 1
            st.rerun()

    st.divider()

    st.date_input(
        "Date",
        min_value=date.today() + timedelta(days=1),
        key="campaign_date",
    )

    result = {
        "frame_name": f"{st.session_state.campaign_date.day} de {MONTHS_PT_NAME[st.session_state.campaign_date.month]}",  # noqa: E501
        "validity_text": _validity_text(st.session_state.campaign_date),
        "products": [
            {
                "name": row["Title"],
                "prev_price": row["Current price"],
                "new_price": row["New price"],
                "image_b64": row["image_b64"],
            }
            for _, row in st.session_state.products.iterrows()
        ],
    }

    st.divider()

    st.download_button(
        label="Download schema",
        data=json.dumps(result, indent=2, ensure_ascii=False),
        file_name=f"sales-{st.session_state.campaign_date.strftime('%Y-%m-%d')}.json",
        mime="application/json",
    )
