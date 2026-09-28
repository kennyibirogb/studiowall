# The Studio Wall

A Django gallery site for an artist. Paintings hang on a wall lit by a spotlight that follows the cursor. Each painting opens in a room tinted with its own colours, with a loupe for inspecting brushwork.

## Run it

    python -m venv venv
    source venv/bin/activate        # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

Open http://127.0.0.1:8000/ for the site and http://127.0.0.1:8000/admin/ to manage it.

## Add and remove paintings

Log in at /admin/.
- Paintings: add, edit, reorder ("position"), mark Sold, or delete.
- Site profile: the artist's name, tagline, bio, WhatsApp number and email.

## Buying

Each painting can have a price (free text) and an optional payment link (Paystack, Flutterwave, PayPal). Available paintings show "Buy now" for the payment link, plus WhatsApp and email enquiry buttons that fill in the painting's name.

## Going live

Set DJANGO_SECRET_KEY, DJANGO_DEBUG=0 and DJANGO_ALLOWED_HOSTS. Run `python manage.py collectstatic`, and serve /media/ (uploaded paintings) from your web server.
