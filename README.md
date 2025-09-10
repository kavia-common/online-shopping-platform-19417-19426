# online-shopping-platform-19417-19426

Backend: Online Kart (Django + DRF)

How to run locally:
- Install dependencies: pip install -r online_kart_backend/requirements.txt
- Apply migrations: python online_kart_backend/manage.py migrate
- Create superuser (optional): python online_kart_backend/manage.py createsuperuser
- Run dev server: python online_kart_backend/manage.py runserver 0.0.0.0:8000

API:
- Swagger UI: /docs
- Redoc: /redoc
- Health: /api/health/
- Auth: /api/auth/register/ (POST), /api/auth/login/ (POST), /api/auth/logout/ (POST)
- Catalog: /api/categories/, /api/products/
- Cart: /api/cart/ (GET), /api/cart/add_item/ (POST), /api/cart/remove_item/ (POST), /api/cart/clear/ (POST), /api/cart/checkout/ (POST)
- Orders: /api/orders/
