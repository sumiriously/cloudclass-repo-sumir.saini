# Managing Web Applications Course

This repository is used by Sumir Saini for exercises for the Managing Web Applications Course

## Feature Added: Tiki Surf Shop Ecommerce App

Implemented a simple ecommerce web application with authentication and a themed UI under `ecommerce_app`.

### What was added and why

- **User authentication (register/login/logout)**  
  Added secure user account flows so only authenticated users can manage store data.

- **Product management API (list/create/update/delete)**  
  Added core ecommerce product operations to support inventory management.

- **Application factory structure and blueprints**  
  Organized the app into `app/`, `routes/`, and config modules to keep the code scalable and maintainable.

- **Simple Tiki Surf Shop UI**  
  Added browser pages for authentication and product management so the app is usable without API tools.

- **Validation, error handling, and security headers**  
  Added safeguards to reduce invalid input, improve reliability, and apply basic web security best practices.

- **Docker support and CI test workflow**  
  Added containerization and automated tests to make local setup and verification consistent.

## Feature Added: Public Product Listing

Added a public Product Listing page that renders a hardcoded Python product list with basic HTML.

### What was added and why

- **In-code product catalog (`app/catalog.py`)**  
  Defined boards, apparel, and accessories directly in Python so the listing does not depend on the database.

- **Public Product Listing page (`/ui/shop`)**  
  Displayed the catalog as HTML cards so anyone can browse without logging in.

- **Category filter and product detail pages**  
  Added simple extra shop features for filtering by category and viewing one product at a time.

- **Session shopping cart**  
  Added add-to-cart with quantity, update/remove items, a cart count in the nav, and a simple checkout that confirms the order and clears the cart.

## Feature Added: Order Management and DigitalOcean Spaces

Checkout used to confirm an order and then forget it. Orders are now saved, and each receipt is stored in DigitalOcean Spaces when that service is configured.

### What was added and why

- **Saved orders**  
  Placing an order writes the customer, line items, total, and status to the database so the shop can track what was purchased after the cart is cleared.

- **Order list and detail**  
  A customer can review orders placed with their account email. Shop staff (the account in `ADMIN_EMAIL`) can see every order and move it through placed, processing, shipped, delivered, or cancelled.

- **DigitalOcean Spaces receipts**  
  Each order writes a text receipt to a Spaces bucket so the record is backed by object storage. If Spaces credentials are not set, the same receipt is saved on the app server, which keeps local development and tests working.

## Feature Added: Simulated Load Balancer and Scaling

A single Flask process is a single point of failure and a single capacity limit. `load_balancing/` runs several copies of a small shop page and a round-robin balancer in front of them.

### What was added and why

- **Two application instances (`app1`, `app2`)**  
  The same page runs on ports 5000 and 5001 so traffic can be spread instead of landing on one process.

- **Round-robin load balancer (`load_balancer.py`, port 8000)**  
  Each request is forwarded to the next healthy instance. Refreshing the balancer URL shows which app answered.

- **Scale-out copies (`app3`, `app4`)**  
  Starting another app and uncommenting its URL in `targets` adds it to the pool. That simulates auto-scaling locally, where new servers are started by hand instead of by a cloud platform.

