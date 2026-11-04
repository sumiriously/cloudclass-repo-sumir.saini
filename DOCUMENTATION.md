# Tiki Surf Shop — Features, Configuration, and Challenges

This document describes the Flask e-commerce application in `ecommerce_app` and the local load-balancing simulation in `load_balancing`. It is the course submission for documentation of features, challenges, and configuration.

Repository: https://github.com/sumiriously/cloudclass-repo-sumir.saini

## 1. What the application is

Tiki Surf Shop is a small storefront for boards, apparel, and accessories. Anyone can browse the catalog, keep a cart, and place an order. Registered users can manage inventory. One staff account, chosen with `ADMIN_EMAIL`, can see every order and update its status.

The shop and the load balancer are separate programs. The shop is the real application. The load balancer is a local simulation that shows how traffic can be spread across several copies of a page. Both want port 5000, so only one of them should be running at a time.

## 2. Features

### Accounts and inventory

Visitors can register, log in, and log out from the browser. The same actions exist as JSON endpoints (`/register`, `/login`, `/logout`) for API clients. Passwords are stored as hashes. A signed-in user can add products through the Inventory page. The product API supports list, create, update, and delete. Create, update, and delete require a login.

### Public shop and cart

The public catalog lives in `ecommerce_app/app/catalog.py`. It does not depend on the inventory database, so the storefront still has products on a fresh database. `/ui/shop` lists the catalog as cards and can filter by category. Each product has a detail page.

The cart is stored in the Flask session. A shopper can add an item with a quantity, change the quantity, remove one item, or clear the cart. The quantity for one product is limited to 20. Out-of-stock catalog items cannot be added. The navigation bar shows the cart count on every page.

### Orders

Checkout asks for a name and email, then saves an order with its line items, total, and a status of `placed`. The cart is cleared and the shopper is sent to a confirmation page with an order number and a receipt download. Refreshing that page does not create a second order.

A customer who logs in with the same email can open Orders and see only those orders. Another account cannot open them. The staff account sees every order and can set the status to placed, processing, shipped, delivered, or cancelled. Orders can also be filtered by status.

### Receipt storage

Each order writes a text receipt. When DigitalOcean Spaces credentials are set, the file is uploaded to a private object in a Spaces bucket. The application reads it back only for someone who is allowed to see the order. When those credentials are blank, or the upload fails, the same receipt is saved under `ecommerce_app/instance/receipts/`. The order page says which place holds the file.

### Security basics

Responses include `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and a `Content-Security-Policy` of `default-src 'self'`. Session cookies are HTTP-only and use `SameSite=Lax`. `SESSION_COOKIE_SECURE` turns on the secure flag when the site is served over HTTPS. Request bodies are limited to 16 MB. Product and account input is validated before it is saved.

### Load balancer and simulated scaling

`load_balancing/` runs four copies of a small shop page and one balancer.

| Process | Port | Role |
| --- | --- | --- |
| `app1` | 5000 | Backend |
| `app2` | 5001 | Backend |
| `app3` | 5002 | Extra capacity |
| `app4` | 5003 | Extra capacity |
| `load_balancer.py` | 8000 | Round-robin entry point |

Each request to http://127.0.0.1:8000 is forwarded to the next target. A down target is skipped. http://127.0.0.1:8000/pool lists the targets and whether each health check passed. Screenshots of a two-instance pool and a four-instance pool are in `load_balancing/screenshots/`.

This is a local stand-in for auto-scaling. The extra processes are started by hand. A cloud platform would start them from a metric such as CPU or request rate. The lesson is the same: the balancer spreads traffic across whatever is in the pool.

## 3. Configuration

Copy `ecommerce_app/.env.example` to `ecommerce_app/.env`. The application reads it on startup.

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Signs the session cookie. Use a long random value outside local development. |
| `DATABASE_URL` | SQLAlchemy database URL. The default is SQLite at `sqlite:///ecommerce.db`. A Postgres URL works with the installed `psycopg2` driver, including a DigitalOcean managed database. |
| `PORT` | Port for `python run.py`. Default `5000`. |
| `SESSION_COOKIE_SECURE` | `true` only when the site is on HTTPS. Leave `false` for local HTTP. |
| `ADMIN_EMAIL` | Account that can see every order and change status. Register that email, then log in again after changing this value. |
| `SPACES_KEY` | DigitalOcean Spaces access key. Leave blank to store receipts on the app server. |
| `SPACES_SECRET` | Spaces secret key. |
| `SPACES_BUCKET` | Bucket name. |
| `SPACES_REGION` | Region, such as `nyc3`. The client uses `https://<region>.digitaloceanspaces.com`. |
| `SPACES_ENDPOINT` | Optional full endpoint. Overrides the region URL. |
| `RECEIPT_DIR` | Optional folder for local receipts. Default is `ecommerce_app/instance/receipts`. |

Do not commit `.env`. The example file has empty Spaces values and no staff password. Staff sign in with the password they chose at registration.

Tables are created on startup when the app is not in test mode. Tests use an in-memory SQLite database and do not touch the development file.

### Run the shop

From the repository root, with the project virtual environment:

```bash
cd ecommerce_app
../venv/bin/python run.py
```

Open http://127.0.0.1:5000. The home page is http://127.0.0.1:5000/ui. Health is http://127.0.0.1:5000/health.

Dependencies are listed in `ecommerce_app/requirements.txt`. Create the environment with `python3 -m venv ../venv` from `ecommerce_app`, activate it, and run `pip install -r requirements.txt` if it does not exist yet.

### Run the shop in Docker

The image is built from `ecommerce_app/Dockerfile` (Python 3.11, port 5000, `python run.py`).

```bash
docker build -t tiki-surf-shop ./ecommerce_app
docker run --rm -p 5000:5000 --env-file ecommerce_app/.env tiki-surf-shop
```

Pass `ADMIN_EMAIL` and the Spaces variables in that env file or with `-e` if those features should be on inside the container. The SQLite file inside the container disappears when the container is removed unless a volume is mounted.

### Run the load balancer

From `load_balancing`, in four terminals for the backends and a fifth for the balancer:

```bash
../venv/bin/python app1/app1.py
../venv/bin/python app2/app2.py
../venv/bin/python app3/app3.py
../venv/bin/python app4/app4.py
../venv/bin/python load_balancer.py
```

`load_balancing/requirements.txt` needs Flask and `requests`. The balancer targets are the list named `targets` in `load_balancing/load_balancer.py`. Remove a URL from that list and restart the balancer to scale the pool back down. Stop these processes before starting the main shop, because `app1` also binds port 5000.

### Tests and CI

```bash
cd ecommerce_app
../venv/bin/python -m pytest -q tests/
```

GitHub Actions (`.github/workflows/test.yml`) installs `ecommerce_app/requirements.txt` on Python 3.11 and runs that test suite on every push and pull request to `main`. `.github/workflows/docker-build.yml` builds the image and does not push it.

## 4. Challenges

**Checkout used to forget the order.** The first checkout only cleared the cart and showed a confirmation. There was nothing to look up later. Saving `Order` and `OrderItem` rows fixed that, and the confirmation is now a redirect so a refresh does not place a second order.

**Two product lists.** The public shop uses the hardcoded catalog. Inventory uses the database. That keeps the storefront working before anyone adds database products, but the cart does not sell inventory items. A later version would use one catalog.

**Guest orders and accounts.** A shopper does not have to log in to check out. The order is tied to the email they type. Logging in with that email later shows the order. Logging in as someone else does not. The browser session can still reopen an order it just placed, which is what the confirmation page needs.

**Spaces is optional.** The course asked for a DigitalOcean cloud service. Spaces is the right fit for a receipt file, but a local run often has no Spaces keys. The storage code tries Spaces when the four settings are present and otherwise writes the file locally. A failed upload also falls back to local storage so the order is still saved. The tradeoff is that a missing key does not fail loudly. The order page has to say “local storage” or “DigitalOcean Spaces” so it is obvious which one ran.

**GitHub Pages cannot host this app.** Pages serves static files. Login, the session cart, checkout, and the database need a running Python process. A live site needs a host that runs Flask, such as a DigitalOcean Droplet or App Platform, with the same environment variables as `.env`.

**The load balancer is not the cloud.** Round-robin in one Python process shows the idea, and skipping a dead target keeps a stopped app from breaking the page. It does not add machines, check CPU, or share a database. Four processes also cannot share one SQLite file safely, which is why the demo page does not use the shop database. Real scaling would put the shop behind a managed load balancer and a shared database such as managed Postgres.

**Port 5000 is shared.** The shop, Docker, and `app1` all default to port 5000. Starting the demo while the shop is running makes http://127.0.0.1:5000 show the demo page instead of the themed store. Stop one before starting the other.

**Staff access is easy to misconfigure.** Only `ADMIN_EMAIL` marks an account as staff, and it is applied at registration or login. Setting it in `.env` does nothing until the process is restarted and that user logs in. There is no separate admin password in the application.

## 5. Layout

```text
ecommerce_app/
  run.py                 starts the shop
  config.py              environment settings
  app/catalog.py         public product list
  app/models.py          users, products, orders
  app/orders.py          place an order and enforce who can see it
  app/spaces.py          DigitalOcean Spaces or local receipt files
  app/routes/            auth, product API, and browser pages
  app/templates/         Tiki Surf Shop pages
  tests/                 auth, products, shop, and orders
load_balancing/
  load_balancer.py       round-robin proxy on port 8000
  app1/ … app4/          backend copies
  screenshots/           pool and request captures
```
