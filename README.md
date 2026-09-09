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
  Added add-to-cart, cart totals, and out-of-stock handling to practice forms, sessions, and page flow.

