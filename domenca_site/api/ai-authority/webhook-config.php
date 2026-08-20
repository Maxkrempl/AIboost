/**
 * AI Authority — Stripe Webhook Configuration
 * 
 * Add this webhook URL to your Stripe Dashboard:
 * https://hd-webdesign.si/api/ai-authority/webhook.php
 * 
 * Events to listen for:
 * - checkout.session.completed
 * - customer.subscription.deleted
 * - invoice.payment_failed
 * 
 * Or, as a simpler approach, the success page redirect captures the order.
 */

// This file documents the webhook setup needed in Stripe Dashboard.
// Go to: https://dashboard.stripe.com/webhooks
// Add endpoint: https://hd-webdesign.si/api/ai-authority/webhook.php
// Select events:
//   - checkout.session.completed
//   - customer.subscription.deleted  
//   - invoice.payment_failed

echo "This is a config file, not an endpoint.\n";
