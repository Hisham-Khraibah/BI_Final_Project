# -----------------------------------------------------------------------------
# ➕ ADD EXPENSE TAB
# -----------------------------------------------------------------------------
"""
Streamlit UI for adding transactions, managing custom categories,
and managing custom keyword rules.
"""
from __future__ import annotations
import streamlit as st
from app.core.categories import (
    auto_category,
    delete_custom_category,
    delete_custom_keyword,
    get_all_categories,
    load_custom_categories,
    load_custom_keywords,
    save_custom_category,
    save_custom_keyword,
)
from app.core.config import (
    APP_TIMEZONE,
    CSV_PATH,
    CUSTOM_CAT_PATH,
    CUSTOM_KEYWORD_PATH,
    DB_PATH,
)
from app.core.database import export_csv_append, insert_expense
from app.core.helpers import get_now_local, get_today_local
from app.ui.components import render_date_input

# -----------------------------------------------------------------------------
# SESSION STATE
# -----------------------------------------------------------------------------
def init_add_expense_state() -> None:
    """Initialize session state values used by the Add Expense tab."""
    if "manual_form_key" not in st.session_state:
        st.session_state["manual_form_key"] = 0

    if "category_key" not in st.session_state:
        st.session_state["category_key"] = 0

    if "show_kw_popup" not in st.session_state:
        st.session_state["show_kw_popup"] = False

    if "show_category_dialog" not in st.session_state:
        st.session_state["show_category_dialog"] = False

    if "category_dialog_message" not in st.session_state:
        st.session_state["category_dialog_message"] = ""

    if "keyword_dialog_message" not in st.session_state:
        st.session_state["keyword_dialog_message"] = ""

    if "category_input_version" not in st.session_state:
        st.session_state["category_input_version"] = 0

    if "keyword_input_version" not in st.session_state:
        st.session_state["keyword_input_version"] = 0

    if "pending_delete_category" not in st.session_state:
        st.session_state["pending_delete_category"] = None

    if "pending_delete_keyword" not in st.session_state:
        st.session_state["pending_delete_keyword"] = None

    if "transaction_saved_message" not in st.session_state:
        st.session_state["transaction_saved_message"] = ""

    if "last_merchant" not in st.session_state:
        st.session_state["last_merchant"] = ""

# -----------------------------------------------------------------------------
# UI STATE
# -----------------------------------------------------------------------------
def reset_add_expense_ui_state() -> None:
    """Reset dialog-related UI state after a successful save."""
    try:
        st.session_state["show_category_dialog"] = False
        st.session_state["category_dialog_message"] = ""
        st.session_state["pending_delete_category"] = None
        st.session_state["show_kw_popup"] = False
        st.session_state["keyword_dialog_message"] = ""
        st.session_state["pending_delete_keyword"] = None
    except Exception:
        pass

# -----------------------------------------------------------------------------
# CATEGORY DIALOG
# -----------------------------------------------------------------------------
@st.dialog("Create New Category", dismissible=False)
def create_category_dialog() -> None:
    """Render the dialog for creating and deleting custom categories."""
    try:
        input_key = f'dialog_new_cat_input_{st.session_state["category_input_version"]}'
        new_category = st.text_input("Category Name", key=input_key)

        if st.session_state["category_dialog_message"]:
            st.success(st.session_state["category_dialog_message"])

        if st.session_state["pending_delete_category"] is not None:
            with st.container(border=True):
                st.warning(
                    f"Are you sure you want to delete "
                    f"'{st.session_state['pending_delete_category']}'?"
                )

                confirm_col1, confirm_col2 = st.columns(2)

                with confirm_col1:
                    if st.button(
                        "Confirm Delete",
                        key="confirm_delete_category_btn",
                        use_container_width=True,
                    ):
                        target_category = st.session_state["pending_delete_category"]

                        if delete_custom_category(CUSTOM_CAT_PATH, target_category):
                            st.session_state["category_dialog_message"] = (
                                f"Deleted: {target_category}"
                            )
                        else:
                            st.session_state["category_dialog_message"] = (
                                f"Could not delete: {target_category}"
                            )

                        st.session_state["pending_delete_category"] = None
                        st.rerun()

                with confirm_col2:
                    if st.button(
                        "Cancel",
                        key="cancel_delete_category_btn",
                        use_container_width=True,
                    ):
                        st.session_state["pending_delete_category"] = None
                        st.rerun()

            st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "Save Category",
                key="dialog_save_cat_btn",
                use_container_width=True,
            ):
                if new_category.strip():
                    if save_custom_category(CUSTOM_CAT_PATH, new_category.strip()):
                        st.session_state["category_dialog_message"] = (
                            f"Category '{new_category.strip()}' added!"
                        )
                        st.session_state["category_input_version"] += 1
                        st.rerun()
                    else:
                        st.error("Could not save the category.")
                else:
                    st.error("Please enter a valid category name.")

        with col2:
            if st.button(
                "Close Category Manager",
                key="dialog_cancel_cat_btn",
                use_container_width=True,
            ):
                st.session_state["show_category_dialog"] = False
                st.session_state["pending_delete_category"] = None
                st.session_state["category_dialog_message"] = ""
                st.session_state["category_input_version"] += 1
                st.rerun()

        st.markdown("---")

        with st.expander("Existing Custom Categories", expanded=False):
            custom_categories = load_custom_categories(CUSTOM_CAT_PATH)

            if custom_categories:
                header_1, header_2 = st.columns([4, 1.8])

                with header_1:
                    st.markdown("**Category Name**")

                with header_2:
                    st.markdown("**Action**")

                st.markdown("---")

                for index, category in enumerate(
                    sorted(custom_categories, key=lambda x: x.lower())
                ):
                    row_1, row_2 = st.columns([4, 1.8])

                    with row_1:
                        st.write(category)

                    with row_2:
                        if st.button(
                            "Delete",
                            key=f"dialog_del_cat_{index}",
                            use_container_width=True,
                        ):
                            st.session_state["pending_delete_category"] = category
                            st.rerun()
            else:
                st.info("No custom categories yet.")

    except Exception as error:
        st.error(f"Error showing category dialog: {error}")

# -----------------------------------------------------------------------------
# KEYWORD RULES DIALOG
# -----------------------------------------------------------------------------
@st.dialog("Custom Keyword Rules", dismissible=False)
def custom_keyword_rules_dialog() -> None:
    """Render the dialog for managing custom keyword rules."""
    try:
        keyword_input_key = f'new_kw_input_{st.session_state["keyword_input_version"]}'
        keyword_cat_key = f'new_kw_category_{st.session_state["keyword_input_version"]}'

        keyword_input = st.text_input(
            "Keyword",
            placeholder="Enter keyword(s)",
            key=keyword_input_key,
        )
        keyword_category = st.selectbox(
            "Choose the Category",
            get_all_categories(CUSTOM_CAT_PATH),
            key=keyword_cat_key,
        )

        if st.session_state["keyword_dialog_message"]:
            st.success(st.session_state["keyword_dialog_message"])

        if st.session_state["pending_delete_keyword"] is not None:
            with st.container(border=True):
                st.warning(
                    f"Are you sure you want to delete "
                    f"'{st.session_state['pending_delete_keyword']}'?"
                )

                confirm_col1, confirm_col2 = st.columns(2)

                with confirm_col1:
                    if st.button(
                        "Confirm Delete",
                        key="confirm_delete_keyword_btn",
                        use_container_width=True,
                    ):
                        target_keyword = st.session_state["pending_delete_keyword"]

                        if delete_custom_keyword(CUSTOM_KEYWORD_PATH, target_keyword):
                            st.session_state["keyword_dialog_message"] = (
                                f"Deleted keyword: {target_keyword}"
                            )
                        else:
                            st.session_state["keyword_dialog_message"] = (
                                f"Could not delete keyword: {target_keyword}"
                            )

                        st.session_state["pending_delete_keyword"] = None
                        st.rerun()

                with confirm_col2:
                    if st.button(
                        "Cancel",
                        key="cancel_delete_keyword_btn",
                        use_container_width=True,
                    ):
                        st.session_state["pending_delete_keyword"] = None
                        st.rerun()

            st.markdown("---")

        col_kw1, col_kw2 = st.columns(2)

        with col_kw1:
            if st.button(
                "Save Keyword Rule",
                key="save_kw_btn",
                use_container_width=True,
            ):
                if keyword_input.strip():
                    if save_custom_keyword(
                        CUSTOM_KEYWORD_PATH,
                        keyword_input.strip(),
                        keyword_category,
                    ):
                        st.session_state["keyword_dialog_message"] = (
                            f"Rule added: {keyword_input.strip()} -> {keyword_category}"
                        )
                        st.session_state["keyword_input_version"] += 1
                        st.rerun()
                    else:
                        st.error("Could not save keyword rule.")
                else:
                    st.error("Please enter a keyword.")

        with col_kw2:
            if st.button(
                "Close",
                key="cancel_kw_btn",
                use_container_width=True,
            ):
                st.session_state["show_kw_popup"] = False
                st.session_state["pending_delete_keyword"] = None
                st.session_state["keyword_dialog_message"] = ""
                st.session_state["keyword_input_version"] += 1
                st.rerun()

        st.markdown("---")

        with st.expander("Existing Custom Keyword Rules", expanded=False):
            rules = load_custom_keywords(CUSTOM_KEYWORD_PATH)

            if rules:
                header_1, header_2, header_3 = st.columns([3, 3, 1.8])

                with header_1:
                    st.markdown("**Keyword**")

                with header_2:
                    st.markdown("**Category**")

                with header_3:
                    st.markdown("**Action**")

                st.markdown("---")

                for index, (keyword, category) in enumerate(
                    sorted(rules.items(), key=lambda x: x[0].lower())
                ):
                    row_1, row_2, row_3 = st.columns([3, 3, 1.8])

                    with row_1:
                        st.write(keyword)

                    with row_2:
                        st.write(category)

                    with row_3:
                        if st.button(
                            "Delete",
                            key=f"dialog_del_kw_{index}",
                            use_container_width=True,
                        ):
                            st.session_state["pending_delete_keyword"] = keyword
                            st.rerun()
            else:
                st.info("No custom keyword rules yet.")

    except Exception as error:
        st.error(f"Error showing keyword dialog: {error}")

# -----------------------------------------------------------------------------
# MAIN RENDERER
# -----------------------------------------------------------------------------
def render_add_expense_tab() -> None:
    """Render the Add Expense tab UI."""
    try:
        init_add_expense_state()

        st.subheader("New Transaction")

        if st.session_state["transaction_saved_message"]:
            st.success(st.session_state["transaction_saved_message"])
            st.session_state["transaction_saved_message"] = ""

        form_key = st.session_state["manual_form_key"]

        col1, col2 = st.columns([1, 1], gap="small")

        with col1:
            tx_date = render_date_input(
                label="Transaction Date",
                value=get_today_local(APP_TIMEZONE),
                max_value=get_today_local(APP_TIMEZONE),
                key=f"manual_date_{form_key}",
                app_timezone=APP_TIMEZONE,
            )

            merchant = st.text_input(
                "Vendor",
                placeholder="Company Name",
                key=f"manual_merchant_{form_key}",
            )

            amount = st.number_input(
                "Amount",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key=f"manual_amount_{form_key}",
            )

            note = st.text_input(
                "Description",
                key=f"manual_note_{form_key}",
            )

        with col2:
            all_categories = get_all_categories(CUSTOM_CAT_PATH)
            category_widget_key = f"manual_category_{form_key}"

            suggested_category = auto_category(
                merchant,
                note,
                CUSTOM_KEYWORD_PATH,
            )

            if category_widget_key not in st.session_state:
                st.session_state[category_widget_key] = (
                    suggested_category
                    if suggested_category in all_categories
                    else all_categories[0]
                )
            else:
                previous_merchant = st.session_state["last_merchant"]
                previous_auto = auto_category(
                    previous_merchant,
                    note,
                    CUSTOM_KEYWORD_PATH,
                )
                current_value = st.session_state[category_widget_key]

                if merchant != previous_merchant:
                    if current_value == previous_auto or current_value not in all_categories:
                        if suggested_category in all_categories:
                            st.session_state[category_widget_key] = suggested_category
                        elif current_value not in all_categories:
                            st.session_state[category_widget_key] = all_categories[0]

            st.session_state["last_merchant"] = merchant

            category = st.selectbox(
                "Category",
                all_categories,
                key=category_widget_key,
            )

            col_cat1, col_cat2 = st.columns(2)

            with col_cat1:
                add_category_btn = st.button(
                    "Create Category",
                    key="open_cat_popup_btn",
                    use_container_width=True,
                )

            with col_cat2:
                add_keyword_btn = st.button(
                    "Add Keyword Rule",
                    key="open_kw_popup_btn",
                    use_container_width=True,
                )

        save_clicked = st.button(
            "Save",
            key=f"manual_save_btn_{form_key}",
        )

        if save_clicked:
            if merchant and amount > 0:
                saved_ok = insert_expense(
                    db_path=DB_PATH,
                    tx_date=tx_date.isoformat(),
                    merchant=merchant.strip(),
                    amount=amount,
                    category=category,
                    note=note,
                    app_timezone=APP_TIMEZONE,
                )

                now = get_now_local(APP_TIMEZONE)

                csv_ok = export_csv_append(
                    csv_path=CSV_PATH,
                    row={
                        "tx_date": tx_date.isoformat(),
                        "merchant": merchant.strip(),
                        "amount": amount,
                        "category": category,
                        "note": note,
                        "created_date": now.strftime("%Y-%m-%d"),
                        "created_time": now.strftime("%I:%M:%S %p"),
                    },
                )

                if saved_ok and csv_ok:
                    reset_add_expense_ui_state()
                    st.session_state["transaction_saved_message"] = "Saved"
                    st.session_state["manual_form_key"] += 1
                    st.session_state["category_key"] += 1
                    st.rerun()
                else:
                    st.error("Transaction could not be fully saved.")
            else:
                st.error("Please provide a vendor and a positive amount.")

        if add_category_btn:
            st.session_state["show_category_dialog"] = True
            st.session_state["show_kw_popup"] = False
            st.session_state["pending_delete_category"] = None
            st.session_state["pending_delete_keyword"] = None
            st.session_state["category_dialog_message"] = ""

        if add_keyword_btn:
            st.session_state["show_kw_popup"] = True
            st.session_state["show_category_dialog"] = False
            st.session_state["pending_delete_category"] = None
            st.session_state["pending_delete_keyword"] = None
            st.session_state["keyword_dialog_message"] = ""

        if st.session_state.get("show_category_dialog", False):
            create_category_dialog()
        elif st.session_state.get("show_kw_popup", False):
            custom_keyword_rules_dialog()

    except Exception as error:
        st.error(f"Error in Add Expense tab: {error}")