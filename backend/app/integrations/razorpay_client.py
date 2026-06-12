"""
CareVoice AI Hospital Platform - Razorpay Integration Client.

Wrapper around the official Razorpay SDK to create orders and verify webhook/payment signatures.
"""

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
        else:
            logger.warning("Razorpay credentials not fully configured. API calls will be simulated.")

    def create_order(self, amount_paise: int, receipt_id: str) -> dict:
        """Create a new Razorpay payment order.

        Args:
            amount_paise: The payment amount in paise (1 INR = 100 paise)
            receipt_id: Internal ID (e.g. Invoice UUID) for reconciliation

        Returns:
            dict: The Razorpay order dictionary, or dummy dict if credentials missing.
        """
        if not self._client:
            logger.info("Razorpay Client simulated order creation", amount=amount_paise, receipt=receipt_id)
            import uuid
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
                "payment_capture": 1,  # Auto-capture
            }
            order = self._client.order.create(data=order_data)
            logger.info("Razorpay order created successfully", order_id=order.get("id"), receipt=receipt_id)
            return order
        except Exception as e:
            logger.error("Failed to create Razorpay order", error=str(e), receipt=receipt_id)
            raise RuntimeError(f"Razorpay order creation failed: {e}")

    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """Verify the cryptographic signature sent back from the Razorpay checkout.

        Returns:
            bool: True if signature is valid, False otherwise.
        """
        if not self._client:
            logger.info("Razorpay Client simulated signature verification (auto-verified)")
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
            logger.warning("Razorpay payment signature verification failed", error=str(e), order_id=razorpay_order_id)
            return False

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Razorpay webhook signature using the webhook secret.

        Returns:
            bool: True if valid, False otherwise.
        """
        if not settings.RAZORPAY_WEBHOOK_SECRET:
            logger.warning("RAZORPAY_WEBHOOK_SECRET is not configured, skipping webhook signature verification.")
            return True

        if not self._client:
            return True

        try:
            # We can use HMAC-SHA256 verification manually or via utility
            self._client.utility.verify_webhook_signature(
                body=payload.decode("utf-8"),
                signature=signature,
                secret=settings.RAZORPAY_WEBHOOK_SECRET
            )
            return True
        except Exception as e:
            logger.warning("Razorpay webhook signature verification failed", error=str(e))
            return False


# Singleton client instance
razorpay_client = RazorpayClient()
