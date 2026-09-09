"""Hardcoded surf-shop catalog used by the public Product Listing pages."""

SURF_PRODUCTS = [
    {
        "id": 1,
        "name": "Tiki Wave Rider Board",
        "category": "Boards",
        "price": 649.00,
        "in_stock": True,
        "emoji": "🏄",
        "description": "A mid-length board built for clean morning sets and mellow reef breaks.",
    },
    {
        "id": 2,
        "name": "Reef Break Shortboard",
        "category": "Boards",
        "price": 529.00,
        "in_stock": True,
        "emoji": "🌊",
        "description": "A high-performance shortboard for steep faces and quick bottom turns.",
    },
    {
        "id": 3,
        "name": "Palm Wax (Tropical)",
        "category": "Accessories",
        "price": 8.50,
        "in_stock": True,
        "emoji": "🕯️",
        "description": "Warm-water surf wax with a coconut scent that stays grippy in the sun.",
    },
    {
        "id": 4,
        "name": "Leash 7ft Coil",
        "category": "Accessories",
        "price": 29.00,
        "in_stock": True,
        "emoji": "🪢",
        "description": "A durable 7-foot leash with a padded ankle cuff and double swivels.",
    },
    {
        "id": 5,
        "name": "Tiki Rash Guard",
        "category": "Apparel",
        "price": 42.00,
        "in_stock": True,
        "emoji": "👕",
        "description": "UPF 50+ long-sleeve rash guard with a faded tiki print.",
    },
    {
        "id": 6,
        "name": "Sunset Board Shorts",
        "category": "Apparel",
        "price": 55.00,
        "in_stock": False,
        "emoji": "🩳",
        "description": "Quick-dry board shorts with a sunset stripe. Currently restocking.",
    },
    {
        "id": 7,
        "name": "Bamboo Surf Fins (Thruster)",
        "category": "Accessories",
        "price": 89.00,
        "in_stock": True,
        "emoji": "🪵",
        "description": "A lightweight bamboo thruster set with a lively, snappy feel.",
    },
    {
        "id": 8,
        "name": "Island Soft-Top",
        "category": "Boards",
        "price": 319.00,
        "in_stock": True,
        "emoji": "🌴",
        "description": "A friendly soft-top for learners and long, lazy summer days.",
    },
]


def get_all_products():
    return list(SURF_PRODUCTS)


def get_categories():
    return sorted({product["category"] for product in SURF_PRODUCTS})


def get_products_by_category(category):
    if not category:
        return get_all_products()
    return [product for product in SURF_PRODUCTS if product["category"] == category]


def get_product_by_id(product_id):
    for product in SURF_PRODUCTS:
        if product["id"] == product_id:
            return product
    return None
