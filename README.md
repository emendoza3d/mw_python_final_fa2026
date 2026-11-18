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

In the sidebar, select **Try with a sample profile** to start without entering
an email, or use sample details to create or look up a demo profile. A name is
required only when creating a new profile. Review the displayed selection
summary and select **Save design**; after saving, use **View order history** or
the **Order history** page to review designs for that profile.

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
