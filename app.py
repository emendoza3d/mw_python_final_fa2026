"""Streamlit app for the sample custom-ring ordering experience."""

import re
from pathlib import Path
from uuid import uuid4

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
        "Use sample details only. Email is only used to look up a demo profile; "
        "no password is required. You can also try the app without entering an email."
    )
    with st.sidebar.form("customer_access"):
        email = st.text_input("Email")
        name = st.text_input(
            "Name",
            help="Required only when creating a new profile; leave blank to open an existing one.",
        )
        submitted = st.form_submit_button("Open my studio", type="primary")

    if submitted:
        normalized_email = email.strip()
        if not _is_valid_email(normalized_email):
            st.sidebar.error("Enter a valid email address.")
        else:
            existing = storage.get_customer(normalized_email)
            if existing is None and not name.strip():
                st.sidebar.error("Enter a name to create a demo profile.")
            else:
                customer, created = storage.get_or_create_customer(
                    normalized_email, name
                )
                st.session_state["customer_email"] = customer["email"]
                st.session_state["customer_name"] = customer["name"]
                if created:
                    st.sidebar.success("Demo profile created.")
                else:
                    st.sidebar.success(f"Welcome back, {customer['name']}.")

    if st.sidebar.button("Try with a sample profile", key="sample_profile"):
        sample_email = f"guest-{uuid4().hex}@example.test"
        customer, _ = storage.get_or_create_customer(sample_email, "Sample Guest")
        st.session_state["customer_email"] = customer["email"]
        st.session_state["customer_name"] = customer["name"]
        st.sidebar.success("Sample profile ready. No personal information needed.")

    active_email = st.session_state.get("customer_email")
    if active_email:
        st.sidebar.info(
            f"Current profile: {st.session_state.get('customer_name', active_email)}"
        )


def _show_menu(options: dict[str, list[str]]) -> None:
    with st.sidebar.expander("Explore ring options"):
        for category, values in options.items():
            st.markdown(f"**{category.title()}**")
            st.write(", ".join(values))


def _open_order_history() -> None:
    st.session_state["studio_page"] = "Order history"


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
            "Design saved in this demo profile. Find it anytime under Order history."
        )

    last_order = st.session_state.get("last_order")
    if last_order and last_order["customer_email"] == email:
        with st.container(border=True):
            st.subheader("Your latest design")
            st.write(storage.get_order_summary(last_order))
            st.caption(f"Demo order #{last_order['order_id']}")
            st.button(
                "View order history",
                on_click=_open_order_history,
                key="view_order_history",
            )


def _show_order_history() -> None:
    email = st.session_state.get("customer_email")
    if not email:
        st.info("Open a demo profile in the sidebar to view its order history.")
        return

    st.markdown('<p class="atelier-kicker">Your collection</p>', unsafe_allow_html=True)
    st.header("Order history")
    orders = storage.get_customer_orders(email)
    if not orders:
        st.write("No designs yet. Your first ring design will appear here.")
        return

    for order in orders:
        with st.container(border=True):
            st.markdown(f"**{storage.get_order_summary(order)}**")
            st.caption(
                f"Order #{order['order_id']} · "
                f"{order['created_at'].replace('T', ' ').replace('+00:00', ' UTC')}"
            )


def main() -> None:
    st.set_page_config(
        page_title="Atelier | Custom Ring Studio",
        page_icon="💍",
        layout="wide",
    )
    _apply_styles()
    st.markdown('<p class="atelier-kicker">A little more personal</p>', unsafe_allow_html=True)
    st.title("Atelier Ring Studio")
    st.write("Create a one-of-a-kind ring, one thoughtful detail at a time.")
    st.warning(
        "Class demo only: use sample names and email addresses, not real customer "
        "information. This demo has no password protection, and CSV data on "
        "Streamlit Community Cloud may be lost when the app restarts."
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
        ("Create a ring", "Order history"),
        key="studio_page",
    )
    if page == "Create a ring":
        _create_order(options)
    else:
        _show_order_history()


if __name__ == "__main__":
    main()
