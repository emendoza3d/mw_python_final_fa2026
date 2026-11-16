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

In the sidebar, enter a sample name and email to create a demo profile or use
an existing email to look it up. Choose ring details and save the design; use
**Order history** to review previous designs for that profile.

## Demo data only

This app has no authentication; an email address is only used to look up a
profile. Do not enter real customer information. Profiles and orders are saved
to `customers.csv` and `orders.csv`, which are excluded from Git. On
Streamlit Community Cloud, local files are not durable and may be reset when
the app restarts. Use a properly secured persistent database and authentication
before adapting this demo for real customer data.

## Customize the choices

Edit `menu.txt` using one `CATEGORY : comma-separated options` entry per line.
The app reads the `SHAPE`, `STYLE`, `METAL`, and `DIAMOND` categories.
