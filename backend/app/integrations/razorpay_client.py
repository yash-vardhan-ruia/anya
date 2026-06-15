"""
CareVoice AI Hospital Platform - Razorpay Integration Client.

Wrapper around the official Razorpay SDK to create orders, payment links,
and verify webhook/payment signatures.
"""

import uuid
import razorpay
import structlog
from app.config import settings

logger = structlog.get_logger(__name__)


class RazorpayClient:
    """Client wrapper for handling Razorpay payment operations."""

    def __init__(self) -> None:
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self._client = None

        if self.key_id and self.key_secret:
            self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
            logger.info("Razorpay client configured successfully")
        else:
            logger.warning("Razorpay credentials not fully configured. API calls will be simulated.")

    def create_order(self, amount_paise: int, receipt_id: str) -> dict:
        if not self._client:
            logger.info("Razorpay simulated order creation", amount=amount_paise, receipt=receipt_id)
            return {
                "id": f"order_sim_{uuid.uuid4().hex[:14]}",
                "amount": amount_paise,
                "currency": "INR",
                "receipt": receipt_id,
                "status": "created",
            }

        try:
            order_data = {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": receipt_id,
                "payment_capture": 1,
            }
            order = self._client.order.create(data=order_data)
            logger.info("Razorpay order created successfully", order_id=order.get("id"))
            return order
        except Exception as e:
            logger.error("Failed to create Razorpay order", error=str(e), receipt=receipt_id)
            raise RuntimeError(f"Razorpay order creation failed: {e}")

    def create_payment_link(
        self,
        amount_paise: int,
        customer_name: str,
        customer_phone: str,
        description: str,
        reference_id: str,
        notes: dict | None = None,
        expire_by: int | None = None,
    ) -> dict:
        """
        Create a Razorpay Payment Link and optionally send SMS.

        amount_paise: amount in paise, e.g. INR 590 = 59000
        customer_phone: Indian mobile number with country code, e.g. +917453888015
        expire_by: Unix timestamp when link expires
        """

        if not self._client:
            link_id = f"plink_sim_{uuid.uuid4().hex[:14]}"
            logger.info(
                "Razorpay simulated payment link creation",
                payment_link_id=link_id,
                amount=amount_paise,
                phone=customer_phone,
            )
            return {
                "id": link_id,
                "short_url": f"https://rzp.io/i/{link_id}",
                "status": "created",
                "amount": amount_paise,
                "currency": "INR",
                "reference_id": reference_id,
                "notes": notes or {},
            }

        try:
            data = {
                "amount": amount_paise,
                "currency": "INR",
                "accept_partial": False,
                "description": description,
                "reference_id": reference_id,
                "customer": {
                    "name": customer_name,
                    "contact": customer_phone,
                },
                "notify": {
                    "sms": True,
                    "email": False,
                },
                "reminder_enable": False,
                "notes": notes or {},
            }

            if expire_by:
                data["expire_by"] = expire_by

            payment_link = self._client.payment_link.create(data)
            logger.info(
                "Razorpay payment link created successfully",
                payment_link_id=payment_link.get("id"),
                short_url=payment_link.get("short_url"),
                amount=amount_paise,
                phone=customer_phone,
            )
            return payment_link

        except Exception as e:
            logger.error("Failed to create Razorpay payment link", error=str(e), phone=customer_phone)
            raise RuntimeError(f"Razorpay payment link creation failed: {e}")

    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        if not self._client:
            logger.info("Razorpay simulated signature verification")
            return True

        try:
            params_dict = {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
            self._client.utility.verify_payment_signature(params_dict)
            logger.info("Razorpay payment signature verified", order_id=razorpay_order_id)
            return True
        except Exception as e:
            logger.warning("Razorpay payment signature verification failed", error=str(e))
            return False

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        if not settings.RAZORPAY_WEBHOOK_SECRET:
            logger.warning("RAZORPAY_WEBHOOK_SECRET is not configured, skipping webhook signature verification.")
            return True

        if not self._client:
            return True

        try:
            self._client.utility.verify_webhook_signature(
                body=payload.decode("utf-8"),
                signature=signature,
                secret=settings.RAZORPAY_WEBHOOK_SECRET,
            )
            return True
        except Exception as e:
            logger.warning("Razorpay webhook signature verification failed", error=str(e))
            return False


razorpay_client = RazorpayClient()