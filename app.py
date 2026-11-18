"""Streamlit app for the sample custom-ring ordering experience."""

import re
from pathlib import Path

import streamlit as st

import storage
from readmenu import read_menu


def _is_valid_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()))


def _load_menu() -> dict[str, list[str]]:
    menu_path = Path(__file__).resolve().with_name("menu.txt")
    raw_menu = read_menu(menu_path)
    expected_categories = ("SHAPE", "STYLE", "METAL", "DIAMOND")
    options: dict[str, list[str]] = {}
    for category in expected_categories:
        values = [
            value.strip()
            for value in raw_menu.get(category, "").split(",")
            if value.strip()
        ]
        if not values:
            raise ValueError(
                f"Add at least one {category.lower()} option to {menu_path.name}."
            )
        options[category] = values
    return options


def _apply_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #30251f;
            --muted: #75685d;
            --gold: #a97936;
            --paper: #fbf8f2;
        }
        .stApp { background: var(--paper); color: var(--ink); }
        [data-testid="stSidebar"] { background: #f1e9dc; }
        h1, h2, h3 { color: var(--ink); font-family: Georgia, serif; }
        div.stButton > button[kind="primary"] {
            background: var(--gold);
            border-color: var(--gold);
            color: white;
        }
        .atelier-kicker {
            color: var(--gold);
            font-size: .78rem;
            font-weight: 700;
            letter-spacing: .16em;
            text-transform: uppercase;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _customer_access() -> None:
    st.sidebar.markdown("### Your studio")
    st.sidebar.caption(
        "Use sample details only. Sign in with your email and password, or create "
        "a new profile."
    )
    active_email = st.session_state.get("customer_email")
    if active_email:
        st.sidebar.info(
            f"Current profile: {st.session_state.get('customer_name', active_email)}"
        )
        if st.sidebar.button("Sign out", key="sign_out"):
            st.session_state.pop("customer_email", None)
            st.session_state.pop("customer_name", None)
            st.rerun()
        return

    sign_in_tab, create_tab = st.sidebar.tabs(("Sign in", "Create profile"))
    with sign_in_tab:
        with st.form("customer_sign_in"):
            sign_in_email = st.text_input("Email", key="sign_in_email")
            sign_in_password = st.text_input(
                "Password", type="password", key="sign_in_password"
            )
            sign_in_submitted = st.form_submit_button("Sign in", type="primary")

        if sign_in_submitted:
            if not _is_valid_email(sign_in_email):
                st.error("Enter a valid email address.")
            else:
                customer = storage.authenticate_customer(
                    sign_in_email, sign_in_password
                )
                if customer is None:
                    st.error("Invalid email or password.")
                else:
                    st.session_state["customer_email"] = customer["email"]
                    st.session_state["customer_name"] = customer["name"]
                    st.rerun()

    with create_tab:
        with st.form("customer_registration"):
            register_email = st.text_input("Email", key="register_email")
            register_name = st.text_input("Name", key="register_name")
            register_password = st.text_input(
                "Password (at least 8 characters)",
                type="password",
                key="register_password",
            )
            register_submitted = st.form_submit_button(
                "Create account", type="primary"
            )

        if register_submitted:
            if not _is_valid_email(register_email):
                st.error("Enter a valid email address.")
            else:
                try:
                    customer = storage.register_customer(
                        register_email, register_name, register_password
                    )
                except ValueError as error:
                    st.error(str(error))
                else:
                    st.session_state["customer_email"] = customer["email"]
                    st.session_state["customer_name"] = customer["name"]
                    st.success("Profile created.")
                    st.rerun()


def _show_menu(options: dict[str, list[str]]) -> None:
    with st.sidebar.expander("Explore ring options"):
        for category, values in options.items():
            st.markdown(f"**{category.title()}**")
            st.write(", ".join(values))


def _open_ring_concepts() -> None:
    st.session_state["studio_section"] = "Ring concepts"


def _create_order(options: dict[str, list[str]]) -> None:
    email = st.session_state.get("customer_email")
    if not email:
        st.info(
            "To try the demo, open a profile in the sidebar, choose your ring "
            "details, and save your design. Use sample information only."
        )
        return

    st.markdown('<p class="atelier-kicker">Made for you</p>', unsafe_allow_html=True)
    st.header("Design your ring")
    st.write("Choose the details that bring your idea to life.")

    first, second = st.columns(2)
    with first:
        shape = st.selectbox("Stone shape", options["SHAPE"])
        metal = st.selectbox("Metal", options["METAL"])
    with second:
        style = st.selectbox("Setting style", options["STYLE"])
        diamond = st.selectbox("Diamond", options["DIAMOND"])

    with st.container(border=True):
        st.subheader("Your selections")
        st.write(
            f"{shape.title()} shape · {style.title()} setting · "
            f"{metal.title()} · {diamond.title()} diamond"
        )
        submitted = st.button("Save design", type="primary", key="save_design")

    if submitted:
        order = storage.create_order(
            email,
            {"shape": shape, "style": style, "metal": metal, "diamond": diamond},
        )
        st.session_state["last_order"] = order
        st.success(
            "Ring concept saved. Find and update it under Ring concepts."
        )

    last_order = st.session_state.get("last_order")
    if last_order and last_order["customer_email"] == email:
        with st.container(border=True):
            st.subheader("Your latest design")
            st.write(storage.get_order_summary(last_order))
            st.caption(f"Concept #{last_order['order_id']}")
            st.button(
                "View ring concepts",
                on_click=_open_ring_concepts,
                key="view_order_history",
            )


def _show_ring_concepts(options: dict[str, list[str]]) -> None:
    email = st.session_state.get("customer_email")
    if not email:
        st.info("Sign in or create a profile in the sidebar to view ring concepts.")
        return

    st.markdown('<p class="atelier-kicker">Your collection</p>', unsafe_allow_html=True)
    st.header("Ring concepts")
    orders = storage.get_customer_orders(email)
    if not orders:
        st.write("No ring concepts yet. Your first design will appear here.")
        return

    for order in orders:
        with st.container(border=True):
            st.markdown(f"**{storage.get_order_summary(order)}**")
            st.caption(
                f"Concept #{order['order_id']} · "
                f"{order['created_at'].replace('T', ' ').replace('+00:00', ' UTC')}"
            )
            if order["status"] == "finalized":
                st.success(
                    "Concept finalized. It is marked ready to discuss a purchase."
                )
                st.caption(
                    "This demo records your confirmation only; it does not place "
                    "an order or process payment."
                )
                continue

            st.info("Concept — you can still make changes.")
            with st.form(f"edit_order_{order['order_id']}"):
                shape_options = options["SHAPE"]
                style_options = options["STYLE"]
                metal_options = options["METAL"]
                diamond_options = options["DIAMOND"]
                first, second = st.columns(2)
                with first:
                    shape = st.selectbox(
                        "Stone shape",
                        shape_options,
                        index=(
                            shape_options.index(order["shape"])
                            if order["shape"] in shape_options
                            else 0
                        ),
                        key=f"edit_shape_{order['order_id']}",
                    )
                    metal = st.selectbox(
                        "Metal",
                        metal_options,
                        index=(
                            metal_options.index(order["metal"])
                            if order["metal"] in metal_options
                            else 0
                        ),
                        key=f"edit_metal_{order['order_id']}",
                    )
                with second:
                    style = st.selectbox(
                        "Setting style",
                        style_options,
                        index=(
                            style_options.index(order["style"])
                            if order["style"] in style_options
                            else 0
                        ),
                        key=f"edit_style_{order['order_id']}",
                    )
                    diamond = st.selectbox(
                        "Diamond",
                        diamond_options,
                        index=(
                            diamond_options.index(order["diamond"])
                            if order["diamond"] in diamond_options
                            else 0
                        ),
                        key=f"edit_diamond_{order['order_id']}",
                    )
                updated = st.form_submit_button("Save changes")
            if updated:
                selections = {
                    "shape": shape,
                    "style": style,
                    "metal": metal,
                    "diamond": diamond,
                }
                if storage.update_order(order["order_id"], email, selections):
                    order.update(selections)
                    st.success("Ring concept updated.")
                    st.markdown(f"**Updated concept: {storage.get_order_summary(order)}**")
                else:
                    st.error("Could not update this concept for the signed-in profile.")

            with st.form(f"finalize_order_{order['order_id']}"):
                confirmed = st.checkbox(
                    "I confirm this concept is ready to proceed toward purchase.",
                    key=f"confirm_order_{order['order_id']}",
                )
                finalize = st.form_submit_button(
                    "Confirm and finalize concept",
                    type="primary",
                )
            if finalize:
                if not confirmed:
                    st.error("Confirm the concept before finalizing it.")
                elif storage.finalize_order(order["order_id"], email):
                    st.rerun()
                else:
                    st.error("Could not finalize this concept for the signed-in profile.")


def main() -> None:
    st.set_page_config(
        page_title="Atelier | Custom Ring Studio",
        page_icon="💍",
        layout="wide",
    )
    _apply_styles()
    st.markdown('<p class="atelier-kicker">A little more personal</p>', unsafe_allow_html=True)
    st.title("Atelier Ring Studio")
    st.write("Create and refine a ring concept, one thoughtful detail at a time.")
    st.warning(
        "Class demo only: use sample names and email addresses, not real customer "
        "information. Passwords are stored as salted hashes, but this demo has no "
        "email verification or password recovery. CSV data on Streamlit Community "
        "Cloud may be lost when the app restarts."
    )

    try:
        options = _load_menu()
    except (OSError, ValueError) as error:
        st.error(f"Could not load ring options: {error}")
        st.stop()

    _customer_access()
    _show_menu(options)

    page = st.sidebar.radio(
        "Studio",
        ("Design a ring", "Ring concepts"),
        key="studio_section",
    )
    if page == "Design a ring":
        if st.session_state.get("customer_email"):
            _create_order(options)
        else:
            st.info("Sign in or create a profile in the sidebar to design a ring.")
    else:
        _show_ring_concepts(options)


if __name__ == "__main__":
    main()
