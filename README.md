# Atelier Ring Studio

A Streamlit class/demo app for designing custom rings and viewing a sample
customer's order history. Ring choices are read from `menu.txt`.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Create a profile with an email address, name, and password (at least 8
characters), or sign in with the email and password for an existing account.
Passwords are stored as salted PBKDF2 hashes, not plaintext. Review the
displayed selection summary and select **Save design**. Use **View order
history** or the **Order history** page to review and edit saved designs.

## Demo data only

This is still a class demo. Do not enter real customer information or reuse a
real password. It does not verify email addresses, provide password recovery,
or protect local CSV files as a production database should. Profiles and orders
are saved to `customers.csv` and `orders.csv`, which are excluded from Git. The
existing password-free demo profile records are preserved but cannot be used to
sign in, and their existing orders cannot be opened through the new accounts;
create an account with a new email address. On Streamlit Community Cloud, local
files are not durable and may be reset when the app restarts. Use a properly
secured persistent database and production-ready authentication before adapting
this demo for real customer data.

## Customize the choices

Edit `menu.txt` using one `CATEGORY : comma-separated options` entry per line.
The app reads the `SHAPE`, `STYLE`, `METAL`, and `DIAMOND` categories.
