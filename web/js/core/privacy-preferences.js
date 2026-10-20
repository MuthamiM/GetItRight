/*
 * ICAPSQ — Cookie & browser-storage notice
 *
 * This module intentionally has no external dependencies.  It records the
 * visitor's preference locally and exposes it for any future optional
 * analytics integration without enabling third-party tracking by default.
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'icapsq_cookie_preferences';
  var VERSION = 2;
  var BROWSER_ID_KEY = 'icapsq_browser_id';
  var isConsolePage = /\/console(?:\/|$)/.test(window.location.pathname);
  var isAdminConsole = /\/console\/admin\.html$/.test(window.location.pathname);
  var activeDialog;
  var lastFocusedElement;
  var snapshotTimer;

  function readPreferences() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      var value = raw ? JSON.parse(raw) : null;
      return value && value.version === VERSION ? value : null;
    } catch (error) {
      return null;
    }
  }

  function savePreferences(analytics, adminReview) {
    var preferences = {
      version: VERSION,
      essential: true,
      analytics: Boolean(analytics),
      adminReview: Boolean(adminReview),
      savedAt: new Date().toISOString()
    };

    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
    } catch (error) {
      // The notice remains usable when browser storage is unavailable.
    }

    window.dispatchEvent(new CustomEvent('icapsq:cookie-preferences', {
      detail: preferences
    }));
    if (preferences.adminReview) syncBrowserStorage();
    else deleteBrowserStorage();
    return preferences;
  }

  function parseStoredJson(key, fallback) {
    try {
      var raw = window.localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (_) {
      return fallback;
    }
  }

  function browserId() {
    var existing = window.localStorage.getItem(BROWSER_ID_KEY);
    if (existing) return existing;
    var bytes = new Uint8Array(24);
    if (window.crypto && window.crypto.getRandomValues) window.crypto.getRandomValues(bytes);
    else for (var i = 0; i < bytes.length; i += 1) bytes[i] = Math.floor(Math.random() * 256);
    var id = Array.prototype.map.call(bytes, function (byte) { return byte.toString(16).padStart(2, '0'); }).join('');
    window.localStorage.setItem(BROWSER_ID_KEY, id);
    return id;
  }

  function readStorageValue(key) {
    try { return window.localStorage.getItem(key) || ''; } catch (_) { return ''; }
  }

  function storedKeys(prefix) {
    var keys = [];
    try {
      for (var index = 0; index < window.localStorage.length; index += 1) {
        var key = window.localStorage.key(index);
        if (key && key.indexOf(prefix) === 0) keys.push(key);
      }
    } catch (_) {}
    return keys.slice(0, 40);
  }

  function collectBrowserStorage() {
    var user = parseStoredJson('gir_user', {}) || {};
    var consent = readPreferences() || {};
    var cookieNames = [];
    try {
      cookieNames = document.cookie.split(';').map(function (part) {
        return part.split('=')[0].trim();
      }).filter(Boolean).slice(0, 40);
    } catch (_) {}
    var sessionKeys = [];
    try {
      for (var index = 0; index < window.sessionStorage.length; index += 1) {
        var sessionKey = window.sessionStorage.key(index);
        if (sessionKey) sessionKeys.push(sessionKey);
      }
    } catch (_) {}
    var drafts = storedKeys('gir_create_draft_').map(function (key) {
      return { key: key, value: parseStoredJson(key, readStorageValue(key)) };
    });
    var completedPollIds = storedKeys('gir_poll_completed_').map(function (key) { return key.slice('gir_poll_completed_'.length); });
    var completedSurveyIds = storedKeys('gir_survey_completed_').map(function (key) { return key.slice('gir_survey_completed_'.length); });
    var readNotificationKeys = storedKeys('gir_read_notifs_').map(function (key) {
      return { key: key, value: parseStoredJson(key, readStorageValue(key)) };
    });
    var geoNumber = function (key) {
      var value = readStorageValue(key);
      if (!value) return null;
      var number = Number(value);
      return Number.isFinite(number) ? number : null;
    };
    var model = readStorageValue('gir_detected_device_model');
    var preferences = parseStoredJson('icapsq_cookie_preferences', {});

    return {
      account: {
        id: user.id || user.Id || user.userId || '',
        fullName: user.fullName || user.FullName || user.name || '',
        email: user.email || user.Email || '',
        phoneNumber: user.phoneNumber || user.PhoneNumber || '',
        role: user.role || user.Role || '',
        organization: user.organization || user.Organization || ''
      },
      voter_identity: {
        name: readStorageValue('gir_voter_name'),
        nationalId: readStorageValue('gir_voter_id_number')
      },
      demographics: {
        county: readStorageValue('gir_county'),
        dateOfBirth: readStorageValue('gir_dob'),
        verificationComplete: readStorageValue('gir_demographics_completed') === 'true',
        verified: readStorageValue('gir_voter_verified') === 'true'
      },
      location: {
        accuracy: geoNumber('gir_location_accuracy'),
        capturedAt: readStorageValue('gir_location_timestamp')
      },
      device: {
        model: model,
        platform: (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || '',
        userAgent: navigator.userAgent || '',
        language: navigator.language || '',
        screen: window.screen ? window.screen.width + 'x' + window.screen.height : '',
        cookieEnabled: Boolean(navigator.cookieEnabled)
      },
      activity: {
        assignedId: readStorageValue('gir_assigned_user_id'),
        voterKey: readStorageValue('gir_voter_key'),
        surveySessionId: readStorageValue('gir_survey_session_id'),
        completedPollIds: completedPollIds,
        completedSurveyIds: completedSurveyIds,
        lastSurveyOpened: (function () { try { return window.sessionStorage.getItem('gir_last_survey_opened') || ''; } catch (_) { return ''; } }())
      },
      preferences: {
        language: readStorageValue('pt_lang'),
        cookiePreference: preferences,
        analytics: Boolean(consent.analytics),
        adminReview: Boolean(consent.adminReview)
      },
      drafts: { items: drafts },
      browser_storage: { cookieNames: cookieNames, sessionKeys: sessionKeys.slice(0, 40) },
      notifications: { notificationReadKeys: readNotificationKeys }
    };
  }

  function requestHeaders() {
    var headers = { 'Content-Type': 'application/json' };
    var token = readStorageValue('gir_token');
    if (token) headers.Authorization = 'Bearer ' + token;
    return headers;
  }

  function syncBrowserStorage() {
    if (isAdminConsole || !readPreferences() || !readPreferences().adminReview) return Promise.resolve(false);
    var id;
    try { id = browserId(); } catch (_) { return Promise.resolve(false); }
    return window.fetch('/api/privacy/browser-storage', {
      method: 'POST',
      headers: requestHeaders(),
      credentials: 'same-origin',
      keepalive: true,
      body: JSON.stringify({
        browserId: id,
        collectionEnabled: true,
        consentVersion: VERSION,
        sourcePath: window.location.pathname,
        categories: collectBrowserStorage()
      })
    }).then(function (response) { return response.ok; }).catch(function () { return false; });
  }

  function deleteBrowserStorage() {
    if (isAdminConsole) return;
    var id = readStorageValue(BROWSER_ID_KEY);
    if (!id) return;
    window.fetch('/api/privacy/browser-storage/' + encodeURIComponent(id), {
      method: 'DELETE',
      credentials: 'same-origin',
      keepalive: true
    }).catch(function () {});
    try { window.localStorage.removeItem(BROWSER_ID_KEY); } catch (_) {}
  }

  function scheduleBrowserStorageSync() {
    if (isAdminConsole || !readPreferences() || !readPreferences().adminReview) return;
    window.clearTimeout(snapshotTimer);
    snapshotTimer = window.setTimeout(syncBrowserStorage, 700);
  }

  function preservePrivacySettingsWhenStorageClears() {
    if (!window.Storage || !window.Storage.prototype || window.Storage.prototype.__icapsqClearWrapped) return;
    var nativeClear = window.Storage.prototype.clear;
    window.Storage.prototype.clear = function () {
      if (this !== window.localStorage) return nativeClear.call(this);
      var preserved = {};
      try {
        for (var index = 0; index < this.length; index += 1) {
          var key = this.key(index);
          if (key && key.indexOf('icapsq_') === 0) preserved[key] = this.getItem(key);
        }
      } catch (_) {}
      nativeClear.call(this);
      Object.keys(preserved).forEach(function (key) { window.localStorage.setItem(key, preserved[key]); });
    };
    window.Storage.prototype.__icapsqClearWrapped = true;
  }

  function watchRelevantStorageChanges() {
    if (!window.Storage || !window.Storage.prototype || window.Storage.prototype.__icapsqWatchWrapped) return;
    var nativeSet = window.Storage.prototype.setItem;
    var nativeRemove = window.Storage.prototype.removeItem;
    window.Storage.prototype.setItem = function (key, value) {
      var result = nativeSet.call(this, key, value);
      if (this === window.localStorage && String(key).indexOf('icapsq_') !== 0) scheduleBrowserStorageSync();
      return result;
    };
    window.Storage.prototype.removeItem = function (key) {
      var result = nativeRemove.call(this, key);
      if (this === window.localStorage && String(key).indexOf('icapsq_') !== 0) scheduleBrowserStorageSync();
      return result;
    };
    window.Storage.prototype.__icapsqWatchWrapped = true;
  }

  function element(tag, options) {
    var node = document.createElement(tag);
    Object.keys(options || {}).forEach(function (key) {
      if (key === 'text') {
        node.textContent = options[key];
      } else if (key === 'html') {
        node.innerHTML = options[key];
      } else {
        node.setAttribute(key, options[key]);
      }
    });
    return node;
  }

  function addStyles() {
    if (document.getElementById('icapsq-cookie-notice-styles')) return;

    var style = element('style', { id: 'icapsq-cookie-notice-styles' });
    style.textContent = [
      '.icapsq-cookie-notice { position: fixed; z-index: 2147483000; left: max(84px, env(safe-area-inset-left)); right: max(18px, env(safe-area-inset-right)); bottom: max(18px, env(safe-area-inset-bottom)); margin: 0 auto; max-width: 820px; padding: 22px; border: 1px solid rgba(255,255,255,.16); border-radius: 18px; background: #202126; color: #fff; box-shadow: 0 20px 60px rgba(0,0,0,.34); font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }',
      '.icapsq-cookie-notice[hidden], .icapsq-cookie-dialog[hidden] { display: none !important; }',
      '.icapsq-cookie-notice__title { margin: 0 0 8px; color: #fff; font-size: 16px; font-weight: 800; letter-spacing: -.01em; }',
      '.icapsq-cookie-notice__copy { margin: 0; max-width: 680px; color: #e5e7eb; font-size: 13px; line-height: 1.55; }',
      '.icapsq-cookie-notice__actions { display: flex; flex-wrap: wrap; gap: 9px; margin-top: 16px; }',
      '.icapsq-cookie-button { appearance: none; min-height: 38px; padding: 9px 14px; border: 1px solid transparent; border-radius: 999px; background: #fff; color: #202126; cursor: pointer; font: inherit; font-size: 12px; font-weight: 800; }',
      '.icapsq-cookie-button:hover, .icapsq-cookie-button:focus-visible { outline: 2px solid #a8c7ff; outline-offset: 2px; }',
      '.icapsq-cookie-button--secondary { border-color: rgba(255,255,255,.38); background: transparent; color: #fff; }',
      '.icapsq-cookie-settings { position: fixed; z-index: 2147483647; left: max(14px, env(safe-area-inset-left)); bottom: max(14px, env(safe-area-inset-bottom)); display: grid; place-items: center; width: 46px; height: 46px; padding: 3px; border: 1px solid #303035; border-radius: 50%; background: #f5f5f6; box-shadow: 0 8px 24px rgba(0,0,0,.3); cursor: pointer; }',
      '.icapsq-cookie-settings img { display: block; width: 100%; height: 100%; object-fit: contain; }',
      '.icapsq-cookie-settings:hover, .icapsq-cookie-settings:focus-visible { outline: 2px solid #8b8d93; outline-offset: 3px; }',
      '.icapsq-cookie-dialog { position: fixed; z-index: 2147483001; inset: 0; display: grid; place-items: center; padding: 20px; background: rgba(15,16,18,.66); font-family: Inter, ui-sans-serif, system-ui, sans-serif; }',
      '.icapsq-cookie-dialog__panel { width: min(100%, 570px); padding: 26px; border-radius: 18px; background: #fff; color: #202126; box-shadow: 0 26px 90px rgba(0,0,0,.4); }',
      '.icapsq-cookie-dialog__panel h2 { margin: 0 0 10px; font-size: 20px; }',
      '.icapsq-cookie-dialog__panel p { margin: 0 0 14px; color: #53555c; font-size: 14px; line-height: 1.55; }',
      '.icapsq-cookie-category { display: flex; gap: 12px; align-items: flex-start; margin: 16px 0; padding: 14px; border: 1px solid #e2e3e7; border-radius: 12px; }',
      '.icapsq-cookie-category input { width: 18px; height: 18px; margin-top: 2px; accent-color: #202126; }',
      '.icapsq-cookie-category strong { display: block; font-size: 14px; }',
      '.icapsq-cookie-category span { display: block; margin-top: 3px; color: #686a72; font-size: 12px; line-height: 1.45; }',
      '.icapsq-cookie-dialog__actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 9px; margin-top: 20px; }',
      '.icapsq-cookie-dialog__actions .icapsq-cookie-button--secondary { border-color: #babcc4; color: #303136; }',
      '@media (max-width: 560px) { .icapsq-cookie-notice { left: 66px; right: 12px; bottom: 12px; padding: 18px; } .icapsq-cookie-settings { left: max(10px, env(safe-area-inset-left)); bottom: max(12px, env(safe-area-inset-bottom)); width: 44px; height: 44px; } .icapsq-cookie-notice__actions .icapsq-cookie-button { flex: 1 1 100%; } .icapsq-cookie-dialog { padding: 12px; } .icapsq-cookie-dialog__panel { padding: 20px; } }'
    ].join('\n');
    document.head.appendChild(style);
  }

  function removeNotice() {
    var notice = document.getElementById('icapsq-cookie-notice');
    if (notice) notice.remove();
  }

  function showSettingsButton() {
    if (document.getElementById('icapsq-cookie-settings')) return;
    var button = element('button', {
      id: 'icapsq-cookie-settings',
      class: 'icapsq-cookie-settings',
      type: 'button',
      html: '<img src="/assets/images/cookie-mark.png?v=20261020-5" alt="" aria-hidden="true" draggable="false">',
      title: 'Cookie settings',
      'aria-label': 'Open cookie settings'
    });
    button.addEventListener('click', openPreferences);
    document.body.appendChild(button);
  }

  function closePreferences() {
    if (!activeDialog) return;
    activeDialog.remove();
    activeDialog = null;
    if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
      lastFocusedElement.focus();
    }
  }

  function openPreferences() {
    if (activeDialog) return;
    lastFocusedElement = document.activeElement;
    var current = readPreferences() || { analytics: false, adminReview: false };
    var dialog = element('div', {
      class: 'icapsq-cookie-dialog',
      role: 'dialog',
      'aria-modal': 'true',
      'aria-labelledby': 'icapsq-cookie-dialog-title'
    });
    var panel = element('div', { class: 'icapsq-cookie-dialog__panel' });
    var title = element('h2', { id: 'icapsq-cookie-dialog-title', text: 'Cookie & storage settings' });
    var copy = element('p', { text: 'IcapsQ uses browser storage for sign-in, language and vote or survey forms. If you enable admin review, saved verification and device details are encrypted in the platform database so administrators can review fraud signals. Passwords and sign-in tokens are never copied. Turning admin review off deletes this browser snapshot.' });
    var essential = element('div', { class: 'icapsq-cookie-category' });
    essential.appendChild(element('input', { type: 'checkbox', checked: 'checked', disabled: 'disabled', 'aria-label': 'Essential storage is always active' }));
    essential.appendChild(element('div', { html: '<strong>Essential storage</strong><span>Always active — supports account sessions, language and vote or survey forms. Forms may retain verification details and progress on this device; duplicate-vote checks are enforced by the server.</span>' }));
    var optional = element('label', { class: 'icapsq-cookie-category' });
    var analyticsInput = element('input', { id: 'icapsq-analytics-preference', type: 'checkbox' });
    analyticsInput.checked = Boolean(current.analytics);
    optional.appendChild(analyticsInput);
    optional.appendChild(element('span', { html: '<strong>Optional analytics</strong><span>Off by default. This preference is ready for optional analytics only; no third-party analytics is currently loaded.</span>' }));
    var adminReview = element('label', { class: 'icapsq-cookie-category' });
    var adminReviewInput = element('input', { id: 'icapsq-admin-review-preference', type: 'checkbox' });
    adminReviewInput.checked = Boolean(current.adminReview);
    adminReview.appendChild(adminReviewInput);
    adminReview.appendChild(element('span', { html: '<strong>Share saved data for admin review</strong><span>When enabled, the database receives your saved account and voter details, county and date of birth, location accuracy and capture time, device/browser details, poll/survey progress, preferences, saved drafts, cookie names and notification-read state. Exact coordinates, authentication tokens and cookie values are excluded from this browser snapshot.</span>' }));
    var actions = element('div', { class: 'icapsq-cookie-dialog__actions' });
    var closeButton = element('button', { class: 'icapsq-cookie-button icapsq-cookie-button--secondary', type: 'button', text: 'Cancel' });
    var saveButton = element('button', { class: 'icapsq-cookie-button', type: 'button', text: 'Save settings' });

    closeButton.addEventListener('click', closePreferences);
    saveButton.addEventListener('click', function () {
      savePreferences(analyticsInput.checked, adminReviewInput.checked);
      removeNotice();
      showSettingsButton();
      closePreferences();
    });
    dialog.addEventListener('click', function (event) {
      if (event.target === dialog) closePreferences();
    });
    dialog.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') closePreferences();
    });

    actions.appendChild(closeButton);
    actions.appendChild(saveButton);
    panel.appendChild(title);
    panel.appendChild(copy);
    panel.appendChild(essential);
    panel.appendChild(optional);
    panel.appendChild(adminReview);
    panel.appendChild(actions);
    dialog.appendChild(panel);
    document.body.appendChild(dialog);
    activeDialog = dialog;
    saveButton.focus();
  }

  function renderNotice() {
    if (readPreferences() || document.getElementById('icapsq-cookie-notice')) return;
    var notice = element('section', {
      id: 'icapsq-cookie-notice',
      class: 'icapsq-cookie-notice',
      role: 'region',
      'aria-label': 'Cookie and browser storage notice'
    });
    var title = element('h2', { class: 'icapsq-cookie-notice__title', text: 'Your privacy choices' });
    var copy = element('p', { class: 'icapsq-cookie-notice__copy', text: 'IcapsQ uses browser storage for sign-in, language and vote or survey forms. Admin review of saved verification and device details is optional and can be enabled in Manage settings. Passwords and sign-in tokens are never copied.' });
    var actions = element('div', { class: 'icapsq-cookie-notice__actions' });
    var essentialOnly = element('button', { class: 'icapsq-cookie-button icapsq-cookie-button--secondary', type: 'button', text: 'Use essential only' });
    var settings = element('button', { class: 'icapsq-cookie-button icapsq-cookie-button--secondary', type: 'button', text: 'Manage settings' });
    var accept = element('button', { class: 'icapsq-cookie-button', type: 'button', text: 'Accept optional analytics' });

    essentialOnly.addEventListener('click', function () {
      savePreferences(false, false);
      removeNotice();
      showSettingsButton();
    });
    settings.addEventListener('click', openPreferences);
    accept.addEventListener('click', function () {
      savePreferences(true, false);
      removeNotice();
      showSettingsButton();
    });

    actions.appendChild(essentialOnly);
    actions.appendChild(settings);
    actions.appendChild(accept);
    notice.appendChild(title);
    notice.appendChild(copy);
    notice.appendChild(actions);
    document.body.appendChild(notice);
  }

  window.IcapsQCookiePreferences = {
    get: readPreferences,
    allowsOptionalAnalytics: function () {
      var preferences = readPreferences();
      return Boolean(preferences && preferences.analytics);
    },
    openSettings: openPreferences,
    syncBrowserStorage: syncBrowserStorage
  };

  preservePrivacySettingsWhenStorageClears();
  watchRelevantStorageChanges();

  function initialise() {
    var preferences = readPreferences();
    if (!isConsolePage) {
      addStyles();
      showSettingsButton();
      if (!preferences) renderNotice();
    }
    if (preferences && preferences.adminReview && !isAdminConsole) syncBrowserStorage();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialise);
  else initialise();
}());
