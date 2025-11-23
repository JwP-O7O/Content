"""Stripe API integration for payment processing."""

import stripe
from typing import Dict, Optional
from datetime import datetime
from loguru import logger

from config.config import settings


class StripeAPI:
    """
    Stripe API client for handling subscriptions and payments.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Stripe API client.

        Args:
            api_key: Stripe API key (defaults to settings)
        """
        self.api_key = api_key or getattr(settings, 'stripe_api_key', None)

        if self.api_key:
            stripe.api_key = self.api_key
            logger.info("Stripe API initialized")
        else:
            logger.warning("Stripe API key not configured")

    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Create a new Stripe customer.

        Args:
            email: Customer email
            name: Customer name
            metadata: Additional metadata

        Returns:
            Customer object or None
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )

            logger.info(f"Stripe customer created: {customer.id}")

            return {
                "id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "created": customer.created
            }

        except Exception as e:
            logger.error(f"Error creating Stripe customer: {e}")
            return None

    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: int = 0,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Create a subscription for a customer.

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            trial_days: Number of trial days
            metadata: Additional metadata

        Returns:
            Subscription object or None
        """
        try:
            subscription_data = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "metadata": metadata or {}
            }

            if trial_days > 0:
                subscription_data["trial_period_days"] = trial_days

            subscription = stripe.Subscription.create(**subscription_data)

            logger.info(f"Stripe subscription created: {subscription.id}")

            return {
                "id": subscription.id,
                "customer": subscription.customer,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(
                    subscription.current_period_start
                ),
                "current_period_end": datetime.fromtimestamp(
                    subscription.current_period_end
                ),
                "trial_end": datetime.fromtimestamp(subscription.trial_end)
                if subscription.trial_end else None
            }

        except Exception as e:
            logger.error(f"Error creating Stripe subscription: {e}")
            return None

    def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ) -> Optional[Dict]:
        """
        Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID
            at_period_end: Whether to cancel at period end or immediately

        Returns:
            Updated subscription object or None
        """
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)

            logger.info(f"Stripe subscription cancelled: {subscription_id}")

            return {
                "id": subscription.id,
                "status": subscription.status,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "cancelled_at": datetime.fromtimestamp(subscription.cancelled_at)
                if subscription.cancelled_at else None
            }

        except Exception as e:
            logger.error(f"Error cancelling Stripe subscription: {e}")
            return None

    def create_payment_link(
        self,
        price_id: str,
        metadata: Optional[Dict] = None,
        discount_code: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a payment link for a product.

        Args:
            price_id: Stripe price ID
            metadata: Additional metadata
            discount_code: Optional discount/promo code

        Returns:
            Payment link URL or None
        """
        try:
            link_data = {
                "line_items": [{"price": price_id, "quantity": 1}],
                "metadata": metadata or {}
            }

            if discount_code:
                link_data["discounts"] = [{"coupon": discount_code}]

            payment_link = stripe.PaymentLink.create(**link_data)

            logger.info(f"Stripe payment link created: {payment_link.id}")

            return payment_link.url

        except Exception as e:
            logger.error(f"Error creating payment link: {e}")
            return None

    def create_discount_code(
        self,
        percent_off: int,
        duration: str = "once",
        duration_in_months: Optional[int] = None,
        max_redemptions: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Create a discount/promo code.

        Args:
            percent_off: Percentage off (0-100)
            duration: 'once', 'repeating', or 'forever'
            duration_in_months: Required if duration is 'repeating'
            max_redemptions: Maximum number of times this can be used

        Returns:
            Coupon object or None
        """
        try:
            coupon_data = {
                "percent_off": percent_off,
                "duration": duration
            }

            if duration == "repeating" and duration_in_months:
                coupon_data["duration_in_months"] = duration_in_months

            if max_redemptions:
                coupon_data["max_redemptions"] = max_redemptions

            coupon = stripe.Coupon.create(**coupon_data)

            logger.info(f"Stripe coupon created: {coupon.id} ({percent_off}% off)")

            return {
                "id": coupon.id,
                "percent_off": coupon.percent_off,
                "duration": coupon.duration,
                "valid": coupon.valid
            }

        except Exception as e:
            logger.error(f"Error creating discount code: {e}")
            return None

    def get_subscription(self, subscription_id: str) -> Optional[Dict]:
        """
        Get subscription details.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Subscription object or None
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)

            return {
                "id": subscription.id,
                "customer": subscription.customer,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(
                    subscription.current_period_start
                ),
                "current_period_end": datetime.fromtimestamp(
                    subscription.current_period_end
                ),
                "cancel_at_period_end": subscription.cancel_at_period_end
            }

        except Exception as e:
            logger.error(f"Error retrieving subscription: {e}")
            return None

    def webhook_construct_event(
        self,
        payload: bytes,
        sig_header: str,
        webhook_secret: str
    ) -> Optional[Dict]:
        """
        Construct and verify a webhook event.

        Args:
            payload: Request body
            sig_header: Stripe signature header
            webhook_secret: Webhook secret

        Returns:
            Event object or None
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )

            return event

        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return None
