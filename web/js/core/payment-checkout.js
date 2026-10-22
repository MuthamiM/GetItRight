(() => {
  const IPAY_ACTION = 'https://payments.ipayafrica.com/v3/ke';
  const FLUTTERWAVE_HOST = 'checkout.flutterwave.com';
  const IPAY_FIELDS = new Set([
    'live', 'oid', 'inv', 'ttl', 'tel', 'eml', 'vid', 'curr',
    'p1', 'p2', 'p3', 'p4', 'cbk', 'cst', 'crl', 'hsh',
  ]);

  window.IcapsPaymentCheckout = {
    launch(data) {
      if (data?.provider === 'ipay') {
        const action = new URL(data.checkout_url || '');
        if (action.protocol !== 'https:' || action.href !== IPAY_ACTION) {
          throw new Error('The payment provider returned an invalid checkout destination.');
        }
        const fields = data.checkout_fields;
        if (!fields || typeof fields !== 'object' || Array.isArray(fields)) {
          throw new Error('Secure checkout could not be prepared.');
        }
        const oid = String(fields.oid || '');
        const signature = String(fields.hsh || '');
        if (!/^IC[A-F0-9]{24}$/.test(oid) || !/^[a-f0-9]{40}$/i.test(signature)) {
          throw new Error('Secure checkout returned invalid payment details.');
        }

        const form = document.createElement('form');
        form.method = 'POST';
        form.action = IPAY_ACTION;
        form.hidden = true;
        for (const [name, value] of Object.entries(fields)) {
          if (!IPAY_FIELDS.has(name) || typeof value !== 'string') continue;
          const input = document.createElement('input');
          input.type = 'hidden';
          input.name = name;
          input.value = value;
          form.appendChild(input);
        }
        document.body.appendChild(form);
        form.submit();
        return;
      }

      if (data?.provider === 'flutterwave') {
        const checkout = new URL(data.checkout_url || '');
        if (checkout.protocol !== 'https:' || checkout.hostname !== FLUTTERWAVE_HOST) {
          throw new Error('The payment provider returned an invalid checkout destination.');
        }
        window.location.assign(checkout.href);
        return;
      }

      throw new Error('No supported payment provider is configured.');
    },
  };
})();
