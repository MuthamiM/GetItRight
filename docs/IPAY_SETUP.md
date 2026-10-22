# iPay plan payments

IcapsQ uses iPay's hosted C2B checkout for plan purchases. Card details, PINs, and CVVs stay on iPay; the API activates a plan only after a server-side iPay transaction search validates the order, amount, and response signature.

## Merchant setup

1. Register through iPay's [merchant application](https://www.ipayafrica.com/merchant-register/?rc=RC000000#/registration).
2. In the merchant dashboard, get the vendor ID and configure the hash key. Keep both values private.
3. Set these variables in the server's untracked `.env` file:

   ```dotenv
   PAYMENT_PROVIDER=ipay
   IPAY_VENDOR_ID=your_vendor_id
   IPAY_HASH_KEY=your_private_hash_key
   IPAY_LIVE=1
   APP_PUBLIC_URL=https://icapsq.mftechnologies.org
   ```

4. Configure the callback URL with iPay as `https://icapsq.mftechnologies.org/api/payments/ipay/callback`.
5. Restart both API services so they load the same credentials. Leave `IPAY_LIVE=0` in non-production environments and use iPay's test setup there.

The app leaves paid checkout disabled until the vendor ID and hash key are present. Production checkout also requires `IPAY_LIVE=1`. Never put merchant credentials in source control, browser code, or chat.

## Verification

The browser posts a short-lived, API-signed checkout form to iPay. On return, the API checks iPay's IPN response and searches for the order server-to-server. It checks the signed response, exact order reference, and exact expected amount before activating the plan. Repeated callbacks are idempotent.

The integration follows iPay's [C2B developer guide](https://dev.ipayafrica.com/C2B.html).
