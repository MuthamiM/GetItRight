(function () {
  'use strict';

  var panels = document.querySelectorAll('[data-google-profile-sharing]');
  if (!panels.length) return;

  function browserId() {
    var key = 'icapsq_google_profile_browser_id';
    var id = window.localStorage.getItem(key);
    if (id) return id;
    var bytes = new Uint8Array(24);
    window.crypto.getRandomValues(bytes);
    id = Array.prototype.map.call(bytes, function (byte) {
      return byte.toString(16).padStart(2, '0');
    }).join('');
    window.localStorage.setItem(key, id);
    return id;
  }

  function setStatus(element, message, isError) {
    element.textContent = message;
    element.style.color = isError ? '#ffb4ab' : 'inherit';
  }

  panels.forEach(function (panel) {
    var checkbox = panel.querySelector('[data-google-profile-consent]');
    var button = panel.querySelector('[data-google-profile-button]');
    var status = panel.querySelector('[data-google-profile-status]');
    var clientConfig;
    var initialized = false;
    var loading = false;

    function loadGoogleScript(onReady) {
      if (window.google && window.google.accounts && window.google.accounts.id) {
        onReady();
        return;
      }
      if (loading) return;
      loading = true;
      var script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = onReady;
      script.onerror = function () {
        loading = false;
        setStatus(status, 'Google sign-in could not load. Try again.', true);
      };
      document.head.appendChild(script);
    }

    function initializeButton() {
      if (!checkbox.checked || initialized || !window.google || !clientConfig.enabled) return;
      initialized = true;
      window.google.accounts.id.initialize({
        client_id: clientConfig.clientId,
        auto_select: false,
        callback: async function (response) {
          if (!checkbox.checked || !response || !response.credential) {
            setStatus(status, 'Select the consent box before sharing your profile.', true);
            return;
          }
          setStatus(status, 'Saving your approved profile fields…', false);
          try {
            var headers = { 'Content-Type': 'application/json' };
            var appToken = window.localStorage.getItem('gir_token');
            if (appToken) headers.Authorization = 'Bearer ' + appToken;
            var result = await window.fetch('/api/privacy/google-profile', {
              method: 'POST',
              headers: headers,
              credentials: 'same-origin',
              body: JSON.stringify({
                credential: response.credential,
                consent: true,
                sourcePath: window.location.pathname
              })
            });
            var payload = await result.json().catch(function () { return {}; });
            if (!result.ok) throw new Error(payload.detail || 'Could not save your Google profile.');
            setStatus(status, 'Profile shared with IcapsQ admin for review.', false);
          } catch (error) {
            setStatus(status, error.message || 'Could not save your Google profile.', true);
          }
        }
      });
      button.replaceChildren();
      window.google.accounts.id.renderButton(button, {
        type: 'standard',
        theme: 'outline',
        size: 'large',
        shape: 'pill',
        text: 'continue_with',
        width: 280
      });
      setStatus(status, 'Google is ready. Select Continue with Google to share the listed fields.', false);
    }

    checkbox.addEventListener('change', function () {
      button.replaceChildren();
      initialized = false;
      if (!checkbox.checked) {
        setStatus(status, 'Profile sharing is off.', false);
        return;
      }
      setStatus(status, 'Checking Google sign-in…', false);
      window.fetch('/api/privacy/google-profile/config', { credentials: 'same-origin', cache: 'no-store' })
        .then(function (response) {
          if (!response.ok) throw new Error('Google sign-in setup is unavailable.');
          return response.json();
        })
        .then(function (config) {
          clientConfig = config;
          if (!config.enabled || !config.clientId) {
            setStatus(status, 'Google sign-in setup is required before profiles can be shared.', true);
            return;
          }
          loadGoogleScript(initializeButton);
        })
        .catch(function (error) {
          setStatus(status, error.message || 'Google sign-in setup is unavailable.', true);
        });
    });
  });
}());
