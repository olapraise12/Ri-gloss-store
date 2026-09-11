RI GLOSS — REAL ONLINE STORE
============================

What this version includes
- Real Flask ecommerce website
- Lip-gloss-only product catalogue
- Owner dashboard at /admin
- Owner can add product name, price, description and upload YOUR OWN product photo
- Shopping cart
- WhatsApp ordering
- Paystack checkout
- Paystack payment verification
- Orders shown in the owner dashboard
- Persistent data/uploads when RI_GLOSS_DATA_DIR points to a Render persistent disk

LOCAL TEST
----------
1. Open PowerShell in this project folder.
2. Run:
   py -3.13 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe app.py
3. Open:
   http://127.0.0.1:5000
4. Owner dashboard:
   http://127.0.0.1:5000/admin
5. Default local owner password:
   change-me-123

IMPORTANT: change the owner password before going live.

GITHUB
------
Create a new GitHub repository, then from this folder run:
   git init
   git add .
   git commit -m "Initial Ri Gloss store"
   git branch -M main
   git remote add origin YOUR_GITHUB_REPOSITORY_URL
   git push -u origin main

RENDER
------
Create a Render Web Service from the GitHub repository.

Build Command:
   pip install -r requirements.txt

Start Command:
   gunicorn --bind 0.0.0.0:$PORT app:APP

Environment variables:
   RI_GLOSS_SECRET = a long random secret
   RI_GLOSS_OWNER_PASSWORD = your private owner password
   PAYSTACK_SECRET_KEY = your LIVE Paystack secret key
   PAYSTACK_PUBLIC_KEY = your LIVE Paystack public key
   RI_GLOSS_DATA_DIR = /var/data

PERSISTENT STORAGE
------------------
Add a Render Persistent Disk and mount it at:
   /var/data

This is important because the SQLite database and uploaded product pictures are stored there.

PAYSTACK
--------
Use LIVE keys for real customer payments.
Never put the Paystack secret key in GitHub or inside frontend JavaScript.

CUSTOM DOMAIN
-------------
After the Render service is live:
1. Open the Render service.
2. Go to Settings > Custom Domains.
3. Add:
   rigloss.com
4. Render will show the DNS record(s) you need.
5. Add those DNS records at the company where rigloss.com was purchased.
6. Wait for DNS propagation.
7. Render should issue HTTPS automatically after the domain verifies.

OWNER PRODUCT PHOTOS
--------------------
Log in at:
   https://YOUR-RENDER-URL/admin

Add each lip gloss with its real name, price, description and your own image.
Uploaded images are stored outside the Git repository and served from /uploads.

SECURITY
--------
Before launch, set RI_GLOSS_SECRET and RI_GLOSS_OWNER_PASSWORD in Render.
Do not commit secrets or the local data folder to GitHub.
