# Paid plan checkout

Paid plans use Flutterwave hosted checkout for KES card and M-Pesa payments. IcapsQ sends customers to Flutterwave; it does not collect card numbers, CVVs, or M-Pesa PINs. Self-service prices match the public pricing page: Pro is KES 1,500 and Organisation is KES 6,500 for 30 days. Election deployments remain custom-quoted and are not charged through self-service checkout.

## Server configuration

1. Create and complete business verification for the Flutterwave merchant account. Test with the provider's test environment before enabling live payments.
2. Add `FLW_SECRET_KEY` and a random `FLW_SECRET_HASH` to the deployment secret store or the private `.env` file on the server. Never add their values to this repository or send them in chat.
3. Set `APP_PUBLIC_URL` to the canonical HTTPS site origin.
4. Configure the Flutterwave webhook URL as `https://icapsq.mftechnologies.org/api/payments/webhook/flutterwave` and use the same secret hash configured on the server.
5. Restart both API instances. `GET /api/payments/plans` reports whether checkout is enabled.

The backend owns the plan prices and amounts. Customers cannot submit a custom amount. It activates a paid plan only after a server-side transaction lookup confirms the transaction reference, successful status, KES currency, and exact expected amount. The webhook and return page share the same idempotent activation path.

Paid access is prepaid for 30 days and renews manually. Pro, Organization, and Election prices are KES 499, KES 899, and KES 1,399 per 30 days. Customer plan changes through the user-plan API are blocked; administrators retain the protected manual plan grant.

The web signup and account upgrade screens stay unavailable for paid checkout until both server-side Flutterwave secrets are configured. Free signup remains available.
