from django.contrib.messages import get_messages
from django.core.files.base import ContentFile

from salitaaco.defaults.plans import PENDING, PLUS
from salitaaco.models.payment import Payment
from salitaaco.models.plan import Plan
from salitaaco.models.site_setting import SiteSetting
from salitaaco.tests.users_base import image_bytes


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


def make_payment(guardian, status=PENDING, plan_key=PLUS, **fields):
    """A payment with a picture, as a guardian's upload makes it."""
    plan = Plan.objects.get(key=plan_key)
    payment = Payment(guardian=guardian, plan=plan, amount=plan.price, proof_mime="image/png", status=status, **fields)
    payment.proof.save("bayad.png", ContentFile(image_bytes()), save=False)
    payment.save()
    return payment


def set_gcash_qr():
    """Give the site a GCash QR code, as an admin does on System Settings > General."""
    setting = SiteSetting.load()
    setting.set_gcash_qr("qr.png", ContentFile(image_bytes()), "image/png")
    return setting
