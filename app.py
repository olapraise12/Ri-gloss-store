import os, sqlite3, uuid
from pathlib import Path
from flask import Flask, request, redirect, url_for, session, render_template_string, flash, send_from_directory
import requests

APP = Flask(__name__)
APP.secret_key = os.environ.get("RI_GLOSS_SECRET", "change-this-secret-key")
BASE = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("RI_GLOSS_DATA_DIR", str(BASE / "data")))
UPLOADS = DATA_DIR / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)
DB = DATA_DIR / "ri_gloss.db"
PAYSTACK_SECRET = os.environ.get("PAYSTACK_SECRET_KEY", "")
PAYSTACK_PUBLIC = os.environ.get("PAYSTACK_PUBLIC_KEY", "")
OWNER_PASSWORD = os.environ.get("RI_GLOSS_OWNER_PASSWORD", "change-me-123")

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reference TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        amount INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT "pending",
        items TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price INTEGER NOT NULL,
        description TEXT DEFAULT '',
        image TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    con.commit(); con.close()

HTML = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title or "Ri Gloss" }}</title>
<style>
:root{--pink:#f58db2;--hot:#d94d82;--light:#fff7fa;--cream:#fffaf5;--gold:#d7a548;--dark:#3b2730}
*{box-sizing:border-box}body{margin:0;font-family:Inter,Arial,sans-serif;color:var(--dark);background:var(--cream)}
a{text-decoration:none;color:inherit}.top{background:#fff;border-bottom:1px solid #f2dbe3;position:sticky;top:0;z-index:20}
.nav{max-width:1180px;margin:auto;padding:15px 20px;display:flex;align-items:center;gap:20px}.logo{font-size:30px;font-weight:900;color:var(--hot);margin-right:auto}.logo b{color:var(--gold)}
.navlinks{display:flex;gap:20px;font-weight:700}.navlinks a:hover{color:var(--hot)}
.cartbtn,.primary{border:0;background:var(--hot);color:white;border-radius:24px;padding:11px 18px;font-weight:800;cursor:pointer}
.hero{max-width:1180px;margin:28px auto;padding:65px 35px;border-radius:32px;background:linear-gradient(135deg,#ffd5e4,#fff 58%,#f7dfad);display:grid;grid-template-columns:1.2fr .8fr;gap:30px;align-items:center}
.hero h1{font-size:clamp(44px,7vw,78px);line-height:.92;margin:0 0 20px}.hero p{font-size:18px;line-height:1.7;max-width:620px}.hero .primary{display:inline-block;margin-top:15px}
.art{height:310px;display:flex;align-items:center;justify-content:center}.bottle{height:235px;width:120px;border-radius:24px 24px 38px 38px;background:linear-gradient(90deg,#d84c82,#ffd0df,#e8689a);position:relative;box-shadow:0 25px 45px #b9436b40;transform:rotate(5deg)}.bottle:before{content:"";position:absolute;top:-60px;left:20px;width:80px;height:65px;border-radius:13px 13px 4px 4px;background:#392a30}.bottle:after{content:"RI GLOSS";position:absolute;top:105px;left:18px;width:84px;text-align:center;background:#fff;border-radius:9px;padding:9px 0;font-weight:900;font-size:12px}
.wrap{max-width:1180px;margin:55px auto;padding:0 20px}.title{text-align:center;font-size:34px;margin-bottom:26px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.card{background:#fff;border:1px solid #f0dce3;border-radius:22px;overflow:hidden;box-shadow:0 10px 30px #653a4812}.pic{height:270px;background:#fce0e9;display:flex;align-items:center;justify-content:center}.pic img{width:100%;height:100%;object-fit:cover}.sample{width:75px;height:165px;border-radius:15px 15px 25px 25px;background:linear-gradient(90deg,#d94d82,#ffd0df,#e96b9b);position:relative}.sample:before{content:"";position:absolute;top:-35px;left:16px;width:43px;height:40px;background:#392a30;border-radius:7px}.info{padding:18px}.info h3{margin:0 0 7px}.price{font-size:19px;font-weight:900;color:var(--hot)}.buy{width:100%;margin-top:12px;padding:12px;border:0;border-radius:13px;background:#f9d8e3;color:#96355e;font-weight:900;cursor:pointer}
.about,.contact{background:#fff;padding:32px;border-radius:24px;line-height:1.75}.contact{background:#f7b4ca}.wa{display:inline-block;background:#fff;color:#9b315d;padding:12px 17px;border-radius:13px;font-weight:900;margin-top:10px}
footer{text-align:center;background:#fff;padding:35px;margin-top:60px;border-top:1px solid #f1dbe3}
.admin{max-width:1000px;margin:35px auto;padding:0 20px}.panel{background:#fff;border-radius:22px;padding:25px;margin-bottom:20px;border:1px solid #f0dce3}.form{display:grid;gap:12px}.form input,.form textarea{padding:12px;border:1px solid #e7ccd6;border-radius:10px;font:inherit}.products-admin{display:grid;gap:12px}.row{display:flex;gap:15px;align-items:center;padding:12px;background:#fff7fa;border-radius:13px}.row img{width:70px;height:70px;object-fit:cover;border-radius:10px}.danger{background:#b92e55;color:white;border:0;padding:9px 13px;border-radius:9px;cursor:pointer;margin-left:auto}
.notice{padding:12px 15px;background:#fff0b8;border-radius:10px;margin-bottom:15px}
@media(max-width:800px){.hero{grid-template-columns:1fr;padding:45px 22px}.grid{grid-template-columns:1fr}.navlinks{display:none}.nav{padding:13px}.hero h1{font-size:50px}.row{flex-wrap:wrap}}
</style></head><body>
<header class="top"><div class="nav"><a class="logo" href="/">Ri <b>Gloss</b></a>
<nav class="navlinks"><a href="/#shop">Shop</a><a href="/#about">About</a><a href="/#contact">Contact</a></nav>
<a class="cartbtn" href="/cart">Cart ({{ cart_count }})</a></div></header>
{% with messages=get_flashed_messages() %}{% if messages %}<div class="wrap"><div class="notice">{{ messages[0] }}</div></div>{% endif %}{% endwith %}
{{ body|safe }}
<footer>© 2026 Ri Gloss · Lip Gloss Store</footer></body></html>"""

HOME = r"""<section class="hero"><div><h1>Gloss that<br><span style="color:#d94d82">speaks for you.</span></h1><p>Welcome to Ri Gloss — your dedicated lip-gloss store. Discover beautiful glosses, add your favourites to your cart and order directly.</p><a class="primary" href="#shop">Shop Lip Gloss</a></div><div class="art"><div class="bottle"></div></div></section>
<section class="wrap" id="shop"><h2 class="title">Shop Our Lip Gloss</h2><div class="grid">
{% for p in products %}<article class="card"><div class="pic">{% if p.image %}<img src="{{url_for('uploaded_file',filename=p.image)}}" alt="{{p.name}}">{% else %}<div class="sample"></div>{% endif %}</div><div class="info"><h3>{{p.name}}</h3><p>{{p.description}}</p><div class="price">₦{{"{:,}".format(p.price)}}</div><form method="post" action="/cart/add"><input type="hidden" name="id" value="{{p.id}}"><button class="buy">Add to cart</button></form></div></article>{% else %}<p>No products yet. The owner can add products from the owner dashboard.</p>{% endfor %}
</div></section>
<section class="wrap" id="about"><h2 class="title">About Ri Gloss</h2><div class="about">Ri Gloss is a lip-gloss-only online store. The owner can add products, prices, descriptions and real product photos from the private owner dashboard.</div></section>
<section class="wrap" id="contact"><h2 class="title">Contact Ri Gloss</h2><div class="contact"><h3>Need help with an order?</h3><p>Contact the store owner directly on WhatsApp.</p><a class="wa" href="https://wa.me/2348032191299" target="_blank">Chat on WhatsApp</a></div></section>"""

CART = r"""<section class="admin"><div class="panel"><h1>Your Cart</h1>{% if items %}{% for x in items %}<p><strong>{{x.name}}</strong> — ₦{{"{:,}".format(x.price)}}</p>{% endfor %}<hr><h2>Total: ₦{{"{:,}".format(total)}}</h2><a class="primary" href="/checkout">Pay securely with Paystack</a> <a class="wa" href="{{wa}}">Order on WhatsApp</a>{% else %}<p>Your cart is empty.</p><a class="primary" href="/">Continue shopping</a>{% endif %}</div></section>"""

CHECKOUT = r"""<section class="admin"><div class="panel"><h1>Secure Checkout</h1><p>Pay securely with Paystack. Your card or bank-payment details are entered on Paystack's secure checkout.</p><form class="form" method="post"><input type="email" name="email" placeholder="Customer email address" required><button class="primary">Pay ₦{{"{:,}".format(total)}}</button></form></div></section>"""

PAYMENT = r"""<section class="admin"><div class="panel" style="text-align:center"><h1>Payment Started</h1><p>You are being redirected to secure Paystack checkout.</p><p>If nothing happens, <a class="primary" href="{{url}}">click here to continue</a>.</p><script>window.location.href={{url|tojson}};</script></div></section>"""

LOGIN = r"""<section class="admin"><div class="panel"><h1>Ri Gloss Owner Login</h1><p>Private dashboard for adding and managing lip gloss products.</p><form class="form" method="post"><input type="password" name="password" placeholder="Owner password" required><button class="primary">Sign in</button></form></div></section>"""

DASH = r"""<section class="admin"><div class="panel"><h1>Owner Dashboard</h1><p>Add your real lip-gloss products here. You can upload the product photo yourself.</p>
<form class="form" method="post" action="/admin/add" enctype="multipart/form-data"><input name="name" placeholder="Product name" required><input name="price" type="number" min="0" placeholder="Price in Naira" required><textarea name="description" placeholder="Product description"></textarea><input name="image" type="file" accept="image/*"><button class="primary">Add Product</button></form></div>
<div class="panel"><h2>Orders</h2><div class="products-admin">{% for o in orders %}<div class="row"><div><strong>{{o.reference}}</strong><br>{{o.email}}<br>₦{{"{:,}".format(o.amount)}} · {{o.status}}<br><small>{{o.items}}</small></div></div>{% else %}<p>No orders yet.</p>{% endfor %}</div></div><div class="panel"><h2>Products</h2><div class="products-admin">{% for p in products %}<div class="row">{% if p.image %}<img src="{{url_for('uploaded_file',filename=p.image)}}">{% else %}<div style="width:70px;height:70px;border-radius:10px;background:#ffd5e4"></div>{% endif %}<div><strong>{{p.name}}</strong><br>₦{{"{:,}".format(p.price)}}<br><small>{{p.description}}</small></div><form method="post" action="/admin/delete/{{p.id}}"><button class="danger">Delete</button></form></div>{% else %}<p>No products yet.</p>{% endfor %}</div></div>
<div class="panel"><a href="/" class="primary">View Store</a> <a href="/admin/logout">Log out</a></div></section>"""

def page(body, title="Ri Gloss"):
    con=db(); count=sum(session.get("cart",[]).__len__() for _ in [0])
    return render_template_string(HTML, body=render_template_string(body, **page_data()), title=title, cart_count=count)

def page_data():
    con=db(); products=con.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    orders=con.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 100").fetchall(); con.close()
    return {"products":products,"orders":orders}

@APP.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOADS, filename)

@APP.route("/")
def home(): return page(HOME)

@APP.post("/cart/add")
def cart_add():
    cid=int(request.form["id"]); cart=session.get("cart",[]); cart.append(cid); session["cart"]=cart; flash("Product added to your cart."); return redirect(request.referrer or "/")

@APP.route("/cart")
def cart():
    ids=session.get("cart",[]); items=[]; con=db()
    for i in ids:
        p=con.execute("SELECT * FROM products WHERE id=?",(i,)).fetchone()
        if p: items.append(p)
    con.close(); total=sum(x["price"] for x in items)
    msg="Hello Ri Gloss! I would like to order:%0A"+"%0A".join("- "+x["name"]+" (₦"+format(x["price"],",")+")" for x in items)+"%0ATotal: ₦"+format(total,",")
    return render_template_string(HTML,body=render_template_string(CART,items=items,total=total,wa="https://wa.me/2348032191299?text="+msg),title="Cart | Ri Gloss",cart_count=len(ids))


@APP.route("/checkout", methods=["GET","POST"])
def checkout():
    ids=session.get("cart",[])
    items=[]; con=db()
    for i in ids:
        p=con.execute("SELECT * FROM products WHERE id=?",(i,)).fetchone()
        if p: items.append(p)
    con.close()
    total=sum(x["price"] for x in items)
    if not items:
        flash("Your cart is empty.")
        return redirect("/")
    if request.method=="GET":
        return render_template_string(HTML,body=render_template_string(CHECKOUT,items=items,total=total),title="Checkout | Ri Gloss",cart_count=len(ids))
    email=request.form["email"].strip()
    if not PAYSTACK_SECRET:
        flash("Paystack is not configured yet. Add PAYSTACK_SECRET_KEY in Render.")
        return redirect("/checkout")
    reference="RIGLOSS-"+uuid.uuid4().hex[:16].upper()
    item_text="; ".join(x["name"] for x in items)
    con=db()
    con.execute("INSERT INTO orders(reference,email,amount,status,items) VALUES(?,?,?,?,?)",(reference,email,total,"pending",item_text))
    con.commit(); con.close()
    try:
        r=requests.post("https://api.paystack.co/transaction/initialize",
            headers={"Authorization":"Bearer "+PAYSTACK_SECRET,"Content-Type":"application/json"},
            json={"email":email,"amount":total*100,"currency":"NGN","reference":reference,
                  "callback_url":url_for("payment_callback",_external=True)})
        data=r.json()
    except Exception:
        flash("Unable to contact Paystack. Please try again.")
        return redirect("/checkout")
    if not data.get("status"):
        flash("Paystack could not initialize this payment.")
        return redirect("/checkout")
    return render_template_string(HTML,body=render_template_string(PAYMENT,url=data["data"]["authorization_url"]),title="Paystack | Ri Gloss",cart_count=len(ids))

@APP.route("/payment/callback")
def payment_callback():
    reference=request.args.get("reference","")
    if not reference or not PAYSTACK_SECRET:
        flash("Payment could not be verified.")
        return redirect("/")
    try:
        r=requests.get("https://api.paystack.co/transaction/verify/"+reference,
            headers={"Authorization":"Bearer "+PAYSTACK_SECRET})
        data=r.json()
    except Exception:
        flash("Could not verify payment. Please contact the store.")
        return redirect("/")
    status=data.get("data",{}).get("status")
    con=db()
    if status=="success":
        con.execute("UPDATE orders SET status='paid' WHERE reference=?",(reference,))
        con.commit()
        session["cart"]=[]
        flash("Payment successful. Your order has been received.")
    else:
        con.execute("UPDATE orders SET status='failed' WHERE reference=?",(reference,))
        con.commit()
        flash("Payment was not completed.")
    con.close()
    return redirect("/")

@APP.route("/admin",methods=["GET","POST"])
def admin():
    if request.method=="POST":
        if request.form.get("password")==OWNER_PASSWORD: session["owner"]=True; return redirect("/admin")
        flash("Incorrect owner password.")
    if not session.get("owner"): return page(LOGIN,"Owner Login | Ri Gloss")
    return page(DASH,"Owner Dashboard | Ri Gloss")

@APP.post("/admin/add")
def admin_add():
    if not session.get("owner"): return redirect("/admin")
    name=request.form["name"].strip(); price=int(request.form["price"]); desc=request.form.get("description","").strip(); image=""
    f=request.files.get("image")
    if f and f.filename:
        ext=Path(f.filename).suffix.lower()
        if ext not in {".jpg",".jpeg",".png",".webp",".gif"}: flash("Use a JPG, PNG, WEBP or GIF image."); return redirect("/admin")
        image=uuid.uuid4().hex+ext; f.save(UPLOADS/image)
    con=db(); con.execute("INSERT INTO products(name,price,description,image) VALUES(?,?,?,?)",(name,price,desc,image)); con.commit(); con.close()
    flash("Product added successfully."); return redirect("/admin")

@APP.post("/admin/delete/<int:pid>")
def admin_delete(pid):
    if not session.get("owner"): return redirect("/admin")
    con=db(); p=con.execute("SELECT image FROM products WHERE id=?",(pid,)).fetchone(); con.execute("DELETE FROM products WHERE id=?",(pid,)); con.commit(); con.close()
    if p and p["image"]:
        try:(UPLOADS/p["image"]).unlink()
        except FileNotFoundError: pass
    flash("Product deleted."); return redirect("/admin")

@APP.route("/admin/logout")
def logout(): session.pop("owner",None); return redirect("/")

init_db()
if __name__=="__main__":
    APP.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
