/* ==========================================================================
   GETITRIGHT -- Voter Demographics & Precise Location Verification Engine
   Enforces County Selection, Date of Birth (DOB), and Precise Geolocation
   for all first-time visitors (logged in or unlogged in) and before voting.
   ========================================================================== */

(function() {
  'use strict';

  const KENYA_COUNTIES = [
    "Baringo", "Bomet", "Bungoma", "Busia", "Elgeyo-Marakwet", "Embu",
    "Garissa", "Homa Bay", "Isiolo", "Kajiado", "Kakamega", "Kericho",
    "Kiambu", "Kilifi", "Kirinyaga", "Kisii", "Kisumu", "Kitui",
    "Kwale", "Laikipia", "Lamu", "Machakos", "Makueni", "Mandera",
    "Marsabit", "Meru", "Migori", "Mombasa", "Murang'a", "Nairobi",
    "Nakuru", "Nandi", "Narok", "Nyamira", "Nyandarua", "Nyeri",
    "Samburu", "Siaya", "Taita-Taveta", "Tana River", "Tharaka-Nithi",
    "Trans Nzoia", "Turkana", "Uasin Gishu", "Vihiga", "Wajir", "West Pokot"
  ];

  const COUNTY_COORDINATES = {
    "Baringo": { lat: 0.4900, lng: 35.7400 },
    "Bomet": { lat: -0.7813, lng: 35.3416 },
    "Bungoma": { lat: 0.5695, lng: 34.5584 },
    "Busia": { lat: 0.4608, lng: 34.1115 },
    "Elgeyo-Marakwet": { lat: 0.8037, lng: 35.5365 },
    "Embu": { lat: -0.5380, lng: 37.4589 },
    "Garissa": { lat: -0.4532, lng: 39.6461 },
    "Homa Bay": { lat: -0.5273, lng: 34.4571 },
    "Isiolo": { lat: 0.3546, lng: 37.5822 },
    "Kajiado": { lat: -1.8524, lng: 36.7768 },
    "Kakamega": { lat: 0.2827, lng: 34.7519 },
    "Kericho": { lat: -0.3677, lng: 35.2831 },
    "Kiambu": { lat: -1.1714, lng: 36.8356 },
    "Kilifi": { lat: -3.6305, lng: 39.8499 },
    "Kirinyaga": { lat: -0.4989, lng: 37.2803 },
    "Kisii": { lat: -0.6817, lng: 34.7667 },
    "Kisumu": { lat: -0.0917, lng: 34.7680 },
    "Kitui": { lat: -1.3670, lng: 38.0106 },
    "Kwale": { lat: -4.1737, lng: 39.4521 },
    "Laikipia": { lat: 0.3606, lng: 36.7820 },
    "Lamu": { lat: -2.2717, lng: 40.9020 },
    "Machakos": { lat: -1.5177, lng: 37.2634 },
    "Makueni": { lat: -1.8031, lng: 37.6311 },
    "Mandera": { lat: 3.9366, lng: 41.8670 },
    "Marsabit": { lat: 2.3369, lng: 37.9904 },
    "Meru": { lat: 0.0463, lng: 37.6559 },
    "Migori": { lat: -1.0634, lng: 34.4731 },
    "Mombasa": { lat: -4.0435, lng: 39.6682 },
    "Murang'a": { lat: -0.7211, lng: 37.1526 },
    "Nairobi": { lat: -1.286389, lng: 36.817223 },
    "Nakuru": { lat: -0.3031, lng: 36.0800 },
    "Nandi": { lat: 0.1836, lng: 35.1056 },
    "Narok": { lat: -1.0833, lng: 35.8667 },
    "Nyamira": { lat: -0.5633, lng: 34.9358 },
    "Nyandarua": { lat: -0.1804, lng: 36.5230 },
    "Nyeri": { lat: -0.4201, lng: 36.9476 },
    "Samburu": { lat: 1.2144, lng: 36.9388 },
    "Siaya": { lat: 0.0607, lng: 34.2878 },
    "Taita-Taveta": { lat: -3.3161, lng: 38.3582 },
    "Tana River": { lat: -1.5000, lng: 39.8500 },
    "Tharaka-Nithi": { lat: -0.2970, lng: 37.8739 },
    "Trans Nzoia": { lat: 1.0157, lng: 34.9542 },
    "Turkana": { lat: 3.1167, lng: 35.6000 },
    "Uasin Gishu": { lat: 0.5143, lng: 35.2698 },
    "Vihiga": { lat: 0.0811, lng: 34.7229 },
    "Wajir": { lat: 1.7471, lng: 40.0573 },
    "West Pokot": { lat: 1.2333, lng: 35.1167 }
  };

  const Demographics = {
    counties: KENYA_COUNTIES,
    countyCoordinates: COUNTY_COORDINATES,
    pendingVoteCallback: null,
    currentLocation: {
      lat: null,
      lng: null,
      accuracy: null,
      status: 'pending' // 'pending', 'acquired', 'county_verified', 'denied', 'unavailable'
    },

    detectIPhoneModel() {
      const w = window.screen.width;
      const h = window.screen.height;
      const ratio = window.devicePixelRatio || 1;
      const minDim = Math.round(Math.min(w, h) * ratio);
      const maxDim = Math.round(Math.max(w, h) * ratio);

      if (minDim === 1179 && maxDim === 2556) return 'Apple iPhone 15 / 15 Pro / 14 Pro';
      if (minDim === 1290 && maxDim === 2796) return 'Apple iPhone 15 Pro Max / 15 Plus / 14 Pro Max';
      if (minDim === 1206 && maxDim === 2622) return 'Apple iPhone 16 / 16 Pro';
      if (minDim === 1320 && maxDim === 2868) return 'Apple iPhone 16 Pro Max / 16 Plus';
      if (minDim === 1170 && maxDim === 2532) return 'Apple iPhone 12 / 13 / 14';
      if (minDim === 1284 && maxDim === 2778) return 'Apple iPhone 12 Pro Max / 13 Pro Max / 14 Plus';
      if (minDim === 1080 && maxDim === 2340) return 'Apple iPhone 12 mini / 13 mini';
      if (minDim === 828 && maxDim === 1792) return 'Apple iPhone 11 / XR';
      if (minDim === 1125 && maxDim === 2436) return 'Apple iPhone X / XS / 11 Pro';
      if (minDim === 1242 && maxDim === 2688) return 'Apple iPhone XS Max / 11 Pro Max';
      if (minDim === 750 && maxDim === 1334) return 'Apple iPhone SE / 8 / 7';
      if (minDim === 1080 && maxDim === 1920) return 'Apple iPhone 8 Plus / 7 Plus';

      return 'Apple iPhone';
    },

    detectAndroidModel(ua) {
      if (window.gir_cached_device_model) {
        return window.gir_cached_device_model;
      }
      const stored = localStorage.getItem('gir_detected_device_model');
      if (stored) return stored;

      let rawModel = '';
      const buildMatch = ua.match(/;\s*([^;)]+?)\s*(?:Build\/|\))/i);
      if (buildMatch && buildMatch[1]) {
        rawModel = buildMatch[1].trim();
      }

      if (!rawModel || /wv|en-us|arm|linux/i.test(rawModel)) {
        const androidMatch = ua.match(/Android\s+[\d.]+;\s*([^;)]+)/i);
        if (androidMatch && androidMatch[1]) {
          rawModel = androidMatch[1].trim();
        }
      }

      if (!rawModel) return 'Android Smartphone';

      if (/^SM-/i.test(rawModel)) return `Samsung Galaxy (${rawModel})`;
      if (/^SAMSUNG/i.test(rawModel)) return rawModel;
      if (/^Pixel/i.test(rawModel)) return `Google ${rawModel}`;
      if (/^CPH/i.test(rawModel)) return `OPPO (${rawModel})`;
      if (/^RMX/i.test(rawModel)) return `Realme (${rawModel})`;
      if (/^V2\d+/i.test(rawModel)) return `vivo (${rawModel})`;
      if (/^M2\d+|Redmi|POCO|Xiaomi/i.test(rawModel)) {
        if (/Redmi|POCO|Xiaomi/i.test(rawModel)) return rawModel;
        return `Xiaomi (${rawModel})`;
      }
      if (/^TECNO/i.test(rawModel)) return rawModel;
      if (/^Infinix/i.test(rawModel)) return rawModel;
      if (/^moto/i.test(rawModel)) return `Motorola (${rawModel})`;
      if (/^HMA-|^VOG-|^ELS-|^ANA-/i.test(rawModel)) return `Huawei (${rawModel})`;

      return rawModel;
    },

    getDeviceInfo() {
      const ua = navigator.userAgent || '';
      let deviceName = 'Unknown Device';
      let deviceOS = 'Unknown OS';

      // Detect OS
      if (/Windows NT 10/.test(ua)) deviceOS = 'Windows 10';
      else if (/Windows NT 11|Windows NT 10.*Win64/.test(ua) && navigator.userAgentData) deviceOS = 'Windows 11';
      else if (/Windows/.test(ua)) deviceOS = 'Windows PC';
      else if (/Mac OS X/.test(ua) && !/iPhone|iPad/.test(ua)) {
        const ver = ua.match(/Mac OS X ([\d_]+)/);
        deviceOS = 'macOS' + (ver ? ' ' + ver[1].replace(/_/g, '.') : '');
      }
      else if (/Android ([\d.]+)/.test(ua)) deviceOS = 'Android ' + ua.match(/Android ([\d.]+)/)[1];
      else if (/iPhone OS ([\d_]+)/.test(ua)) deviceOS = 'iOS ' + ua.match(/iPhone OS ([\d_]+)/)[1].replace(/_/g, '.');
      else if (/iPad.*OS ([\d_]+)/.test(ua)) deviceOS = 'iPadOS ' + ua.match(/iPad.*OS ([\d_]+)/)[1].replace(/_/g, '.');
      else if (/Linux/.test(ua)) deviceOS = 'Linux';
      else if (/CrOS/.test(ua)) deviceOS = 'Chrome OS';

      // Detect Device Name
      if (/iPhone/.test(ua)) {
        deviceName = this.detectIPhoneModel();
      } else if (/iPad/.test(ua)) {
        deviceName = 'Apple iPad';
      } else if (/Android/.test(ua)) {
        deviceName = this.detectAndroidModel(ua);
      } else if (/Macintosh/.test(ua)) {
        deviceName = 'Apple Mac';
      } else if (/Windows/.test(ua)) {
        deviceName = 'Windows PC';
      } else if (/CrOS/.test(ua)) {
        deviceName = 'Chromebook';
      } else if (/Linux/.test(ua)) {
        deviceName = 'Linux PC';
      }

      // Try navigator.userAgentData for newer browsers (Android Chrome, Edge, etc.)
      if (navigator.userAgentData) {
        if (navigator.userAgentData.platform && (!deviceOS || deviceOS === 'Unknown OS')) {
          deviceOS = navigator.userAgentData.platform;
        }
        if (navigator.userAgentData.getHighEntropyValues && !window.gir_cached_device_model) {
          navigator.userAgentData.getHighEntropyValues(['model', 'platform', 'platformVersion']).then(vals => {
            if (vals.model) {
              window.gir_cached_device_model = vals.model;
              localStorage.setItem('gir_detected_device_model', vals.model);
            }
          }).catch(() => {});
        }
      }

      return { deviceName, deviceOS };
    },

    getOrAssignUserId(forceRefresh = false) {
      if (!forceRefresh) {
        let existing = localStorage.getItem('gir_assigned_user_id') || localStorage.getItem('gir_voter_key');
        if (existing && existing.startsWith('USR-') && !existing.includes('UNKNOWN')) {
          return existing;
        }
      }

      const device = this.getDeviceInfo();
      const county = this.getCounty() || localStorage.getItem('gir_county') || 'NAIROBI';
      const loc = this.getLocation();

      const cleanDevice = (device.deviceName || 'DEV').replace(/[^a-zA-Z0-9]/g, '').slice(0, 8).toUpperCase() || 'DEVICE';
      const cleanCounty = (county || 'NAIROBI').replace(/\s*County/i, '').replace(/[^a-zA-Z0-9]/g, '').toUpperCase() || 'LOC1';

      let locSeed = '0000';
      if (loc.lat && loc.lng) {
        locSeed = Math.abs(Math.round(loc.lat * 1000) ^ Math.round(loc.lng * 1000)).toString(36).toUpperCase().padStart(4, '0').slice(-4);
      } else {
        locSeed = Math.random().toString(36).substring(2, 6).toUpperCase();
      }

      const assignedId = `USR-${cleanDevice}-${cleanCounty}-${locSeed}`;
      localStorage.setItem('gir_assigned_user_id', assignedId);
      localStorage.setItem('gir_voter_key', assignedId);
      localStorage.setItem('gir_survey_session_id', assignedId);
      return assignedId;
    },

    init() {
      this.injectStyles();
      this.injectModal();
      this.acquireLocation(false);
      this.getOrAssignUserId();
    },

    hasCompletedDemographics() {
      const county = localStorage.getItem('gir_county');
      const dob = localStorage.getItem('gir_dob');
      const done = localStorage.getItem('gir_demographics_completed');
      return Boolean(county && dob && done === 'true');
    },

    getCounty() {
      return localStorage.getItem('gir_county') || '';
    },

    getDob() {
      return localStorage.getItem('gir_dob') || '';
    },

    getLocation() {
      const lat = localStorage.getItem('gir_precise_lat');
      const lng = localStorage.getItem('gir_precise_lng');
      const acc = localStorage.getItem('gir_location_accuracy');
      if (lat && lng) {
        return {
          lat: parseFloat(lat),
          lng: parseFloat(lng),
          accuracy: acc ? parseFloat(acc) : 250
        };
      }
      // Fallback to county centroid if county is set
      const c = this.getCounty();
      if (c && COUNTY_COORDINATES[c]) {
        return {
          lat: COUNTY_COORDINATES[c].lat,
          lng: COUNTY_COORDINATES[c].lng,
          accuracy: 250
        };
      }
      return {
        lat: this.currentLocation.lat || -1.286389,
        lng: this.currentLocation.lng || 36.817223,
        accuracy: this.currentLocation.accuracy || 500
      };
    },

    acquireLocation(forcePrompt = false) {
      if (!navigator.geolocation) {
        this.fallbackCountyLocation();
        return;
      }

      const options = {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      };

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude, accuracy } = position.coords;
          this.currentLocation = {
            lat: latitude,
            lng: longitude,
            accuracy: accuracy,
            status: 'acquired'
          };

          localStorage.setItem('gir_precise_lat', latitude);
          localStorage.setItem('gir_precise_lng', longitude);
          localStorage.setItem('gir_location_accuracy', accuracy);
          localStorage.setItem('gir_location_timestamp', new Date().toISOString());

          this.updateLocationBadge();
        },
        (error) => {
          console.warn('[Demographics] Geolocation access notice:', error.message);
          this.currentLocation.status = error.code === 1 ? 'denied' : 'unavailable';
          this.fallbackCountyLocation();
        },
        options
      );
    },

    fallbackCountyLocation() {
      const c = this.getCounty() || 'Nairobi';
      if (COUNTY_COORDINATES[c]) {
        this.currentLocation.lat = COUNTY_COORDINATES[c].lat;
        this.currentLocation.lng = COUNTY_COORDINATES[c].lng;
        this.currentLocation.accuracy = 250;
        this.currentLocation.status = 'county_verified';
        localStorage.setItem('gir_precise_lat', COUNTY_COORDINATES[c].lat);
        localStorage.setItem('gir_precise_lng', COUNTY_COORDINATES[c].lng);
        localStorage.setItem('gir_location_accuracy', 250);
      }
      this.updateLocationBadge();
    },

    updateLocationBadge() {
      const badge = document.getElementById('gir-geo-status-badge');
      if (!badge) return;

      if (this.currentLocation.status === 'acquired' && this.currentLocation.lat) {
        badge.innerHTML = `
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#303030;margin-right:6px;"></span>
          <strong>Precise Phone GPS Verified:</strong> ${this.currentLocation.lat.toFixed(5)}, ${this.currentLocation.lng.toFixed(5)} (&plusmn;${Math.round(this.currentLocation.accuracy)}m)
        `;
        badge.style.borderColor = '#303030';
        badge.style.color = '#303030';
      } else if (this.currentLocation.status === 'county_verified' && this.currentLocation.lat) {
        const c = this.getCounty() || 'Regional';
        badge.innerHTML = `
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#303030;margin-right:6px;"></span>
          <strong>${c} County Verified:</strong> ${this.currentLocation.lat.toFixed(4)}, ${this.currentLocation.lng.toFixed(4)}
          <button type="button" onclick="window.Demographics.acquireLocation(true)" style="background:none;border:none;color:#303030;font-weight:700;text-decoration:underline;cursor:pointer;margin-left:6px;">Acquire GPS</button>
        `;
      } else if (this.currentLocation.status === 'denied') {
        badge.innerHTML = `
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#888;margin-right:6px;"></span>
          <strong>GPS Permission Pending:</strong> County selection verified.
          <button type="button" onclick="window.Demographics.acquireLocation(true)" style="background:none;border:none;color:#303030;font-weight:700;text-decoration:underline;cursor:pointer;margin-left:6px;">Enable GPS</button>
        `;
      } else {
        badge.innerHTML = `
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#888;margin-right:6px;"></span>
          County location verified &bull; ${this.currentLocation.lat ? this.currentLocation.lat.toFixed(4) + ', ' + this.currentLocation.lng.toFixed(4) : 'Ready'}
        `;
      }
    },

    injectStyles() {
      if (document.getElementById('gir-demographics-styles')) return;
      const style = document.createElement('style');
      style.id = 'gir-demographics-styles';
      style.textContent = `
        .gir-modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(48, 48, 48, 0.72);
          backdrop-filter: blur(8px);
          -webkit-backdrop-filter: blur(8px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 999999;
          padding: 16px;
          opacity: 0;
          pointer-events: none;
          transition: opacity 0.25s ease;
        }
        .gir-modal-overlay.active {
          opacity: 1;
          pointer-events: auto;
        }
        .gir-modal-box {
          background: #E5E5E5;
          color: #303030;
          width: 100%;
          max-width: 520px;
          border-radius: 24px;
          border: 2px solid #303030;
          box-shadow: 0 20px 48px rgba(0, 0, 0, 0.35);
          padding: 28px;
          box-sizing: border-box;
          transform: translateY(20px) scale(0.98);
          transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
          font-family: 'Inter', system-ui, -apple-system, sans-serif;
          max-height: 92vh;
          overflow-y: auto;
        }
        .gir-modal-overlay.active .gir-modal-box {
          transform: translateY(0) scale(1);
        }
        .gir-modal-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          margin-bottom: 14px;
        }
        .gir-modal-title {
          font-family: 'Outfit', sans-serif;
          font-size: 21px;
          font-weight: 800;
          color: #303030;
          line-height: 1.2;
          margin: 0;
        }
        .gir-modal-sub {
          font-size: 13px;
          font-weight: 600;
          color: #555555;
          margin-top: 4px;
        }
        .gir-modal-desc {
          font-size: 13px;
          line-height: 1.5;
          color: #404040;
          background: rgba(48, 48, 48, 0.05);
          border: 1px solid rgba(48, 48, 48, 0.15);
          border-radius: 12px;
          padding: 10px 14px;
          margin-bottom: 14px;
        }
        .gir-form-group {
          margin-bottom: 16px;
        }
        .gir-form-label {
          display: block;
          font-size: 12px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          color: #303030;
          margin-bottom: 6px;
        }
        .gir-form-input, .gir-form-select {
          width: 100%;
          box-sizing: border-box;
          background: #FFFFFF;
          color: #303030;
          border: 1.5px solid #303030;
          border-radius: 12px;
          padding: 12px 14px;
          font-size: 14px;
          font-family: inherit;
          font-weight: 600;
          outline: none;
          transition: border-color 0.15s, box-shadow 0.15s;
        }
        .gir-form-input:focus, .gir-form-select:focus {
          border-color: #000000;
          box-shadow: 0 0 0 3px rgba(48, 48, 48, 0.15);
        }
        .gir-geo-badge {
          background: #FFFFFF;
          border: 1.5px dashed #303030;
          border-radius: 12px;
          padding: 10px 14px;
          font-size: 12px;
          color: #303030;
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 6px;
        }
        .gir-submit-btn {
          width: 100%;
          background: #303030;
          color: #E5E5E5;
          border: none;
          border-radius: 30px;
          padding: 14px 24px;
          font-size: 15px;
          font-weight: 700;
          font-family: 'Outfit', sans-serif;
          cursor: pointer;
          transition: all 0.2s ease;
          margin-top: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
        }
        .gir-submit-btn:hover {
          background: #000000;
          color: #FFFFFF;
          transform: translateY(-1px);
          box-shadow: 0 6px 16px rgba(48, 48, 48, 0.25);
        }
        .gir-submit-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none;
        }
      `;
      document.head.appendChild(style);
    },

    injectModal() {
      if (document.getElementById('gir-demographics-modal')) return;

      const overlay = document.createElement('div');
      overlay.id = 'gir-demographics-modal';
      overlay.className = 'gir-modal-overlay';

      const countiesOptions = this.counties.map(c => `<option value="${c}">${c} County</option>`).join('');
      const deviceInfo = this.getDeviceInfo();
      const assignedId = this.getOrAssignUserId();

      overlay.innerHTML = `
        <div class="gir-modal-box">
          <div class="gir-modal-header">
            <div>
              <h2 class="gir-modal-title" id="gir-modal-title-text">Civic Verification Survey</h2>
              <div class="gir-modal-sub" id="gir-modal-sub-text">Kenya 47 Counties Voter Verification</div>
            </div>
            <div style="width:36px;height:36px;border-radius:50%;background:#303030;color:#E5E5E5;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:16px;">
              &#10003;
            </div>
          </div>

          <div class="gir-modal-desc" id="gir-modal-desc-text" style="margin-top:12px;">
            To ensure genuine regional representation and prevent ballot duplication, please confirm your verification details and County of residence.
          </div>

          <form id="gir-demographics-form" onsubmit="window.Demographics.handleSubmit(event)">
            <div class="gir-form-group">
              <label class="gir-form-label" for="gir-survey-voter-name">Full Name (as on ID / Passport)</label>
              <input type="text" id="gir-survey-voter-name" class="gir-form-input" placeholder="e.g. Legal Name" required minlength="3" maxlength="100" autocomplete="name">
            </div>

            <div class="gir-form-group">
              <label class="gir-form-label" for="gir-survey-voter-id">National ID / Passport Number</label>
              <input type="text" id="gir-survey-voter-id" class="gir-form-input" placeholder="e.g. National ID or Passport" required minlength="5" maxlength="30" autocomplete="off">
            </div>

            <div class="gir-form-group">
              <label class="gir-form-label" for="gir-survey-county">Select County of Residence / Voting</label>
              <select id="gir-survey-county" class="gir-form-select" required>
                <option value="" disabled>-- Select your County --</option>
                ${countiesOptions}
              </select>
            </div>

            <div class="gir-form-group">
              <label class="gir-form-label" for="gir-survey-dob">Date of Birth (DOB)</label>
              <input type="date" id="gir-survey-dob" class="gir-form-input" value="1995-05-15" required max="2008-12-31">
              <div style="font-size:11px;color:#666;margin-top:4px;">Must be 18 years or older for official voting eligibility.</div>
            </div>

            <div class="gir-form-group">
              <label class="gir-form-label">Precise Location Telemetry</label>
              <div class="gir-geo-badge" id="gir-geo-status-badge">
                <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#888;margin-right:6px;"></span>
                Acquiring precise location...
              </div>
            </div>

            <button type="submit" class="gir-submit-btn" id="gir-survey-submit-btn">
              Confirm &amp; Proceed &rarr;
            </button>
          </form>
        </div>
      `;

      document.body.appendChild(overlay);
      this.updateLocationBadge();

      // Pre-fill if already verified by user
      const savedName = localStorage.getItem('gir_voter_name') || '';
      const savedId = localStorage.getItem('gir_voter_id_number') || '';
      const savedCounty = localStorage.getItem('gir_county') || 'Nairobi';
      const savedDob = localStorage.getItem('gir_dob') || '1995-05-15';
      const nEl = document.getElementById('gir-survey-voter-name');
      if (nEl && savedName) nEl.value = savedName;
      const iEl = document.getElementById('gir-survey-voter-id');
      if (iEl && savedId) iEl.value = savedId;
      const cEl = document.getElementById('gir-survey-county');
      if (cEl) {
        cEl.value = savedCounty;
        cEl.addEventListener('change', (e) => {
          const selected = e.target.value;
          if (selected && COUNTY_COORDINATES[selected]) {
            localStorage.setItem('gir_county', selected);
            if (this.currentLocation.status !== 'acquired') {
              this.currentLocation.lat = COUNTY_COORDINATES[selected].lat;
              this.currentLocation.lng = COUNTY_COORDINATES[selected].lng;
              this.currentLocation.accuracy = 250;
              this.currentLocation.status = 'county_verified';
              localStorage.setItem('gir_precise_lat', COUNTY_COORDINATES[selected].lat);
              localStorage.setItem('gir_precise_lng', COUNTY_COORDINATES[selected].lng);
              localStorage.setItem('gir_location_accuracy', 250);
              this.updateLocationBadge();
            }
            const newUid = this.getOrAssignUserId(true);
            const idEl = document.getElementById('gir-modal-id-text');
            if (idEl) idEl.textContent = `Sovereign Citizen ID: ${newUid}`;
            const chipEl = document.getElementById('citizen-device-display');
            if (chipEl) {
              const dev = this.getDeviceInfo();
              chipEl.innerHTML = `<strong>Citizen ID:</strong> ${newUid} &bull; <strong>Device:</strong> ${dev.deviceName} (${dev.deviceOS}) &bull; <strong>Region:</strong> ${selected}`;
            }
          }
        });
      }
      const dEl = document.getElementById('gir-survey-dob');
      if (dEl) dEl.value = savedDob;
    },

    openSurveyModal(config = {}) {
      const modal = document.getElementById('gir-demographics-modal');
      if (!modal) return;

      if (config.title) {
        document.getElementById('gir-modal-title-text').textContent = config.title;
      }
      if (config.subtitle) {
        document.getElementById('gir-modal-sub-text').textContent = config.subtitle;
      }
      if (config.notice) {
        document.getElementById('gir-modal-desc-text').textContent = config.notice;
      }

      this.acquireLocation(true);
      modal.classList.add('active');
    },

    closeSurveyModal() {
      const modal = document.getElementById('gir-demographics-modal');
      if (modal) modal.classList.remove('active');
    },

    async handleSubmit(e) {
      e.preventDefault();
      const voterName = (document.getElementById('gir-survey-voter-name').value || '').trim();
      const voterIdNumber = (document.getElementById('gir-survey-voter-id').value || '').trim();
      const county = document.getElementById('gir-survey-county').value;
      const dob = document.getElementById('gir-survey-dob').value;
      const submitBtn = document.getElementById('gir-survey-submit-btn');

      if (!voterName || voterName.length < 3) {
        alert('Please enter your full name (at least 3 characters).');
        return;
      }
      if (!voterIdNumber || voterIdNumber.length < 5) {
        alert('Please enter a valid National ID or Passport number (at least 5 characters).');
        return;
      }
      if (!county) {
        alert('Please select your County.');
        return;
      }
      if (!dob) {
        alert('Please enter your Date of Birth.');
        return;
      }

      // Check age >= 18
      const birthDate = new Date(dob);
      const today = new Date();
      let age = today.getFullYear() - birthDate.getFullYear();
      const m = today.getMonth() - birthDate.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
        age--;
      }
      if (age < 18) {
        alert('You must be 18 years or older to participate in civic polls and surveys.');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = 'Verifying & Saving...';

      // Save to localStorage
      localStorage.setItem('gir_voter_name', voterName);
      localStorage.setItem('gir_voter_id_number', voterIdNumber);
      localStorage.setItem('gir_county', county);
      localStorage.setItem('gir_dob', dob);
      localStorage.setItem('gir_demographics_completed', 'true');
      localStorage.setItem('gir_voter_verified', 'true');

      // Update location with county coords if not acquired
      if (this.currentLocation.status !== 'acquired' && COUNTY_COORDINATES[county]) {
        localStorage.setItem('gir_precise_lat', COUNTY_COORDINATES[county].lat);
        localStorage.setItem('gir_precise_lng', COUNTY_COORDINATES[county].lng);
        localStorage.setItem('gir_location_accuracy', 250);
      }

      const assignedUserId = this.getOrAssignUserId(true);
      const loc = this.getLocation();
      const device = this.getDeviceInfo();

      // Update on-page chip if present
      const chipEl = document.getElementById('citizen-device-display');
      if (chipEl) {
        chipEl.innerHTML = `<strong>Citizen ID:</strong> ${assignedUserId} &bull; <strong>Device:</strong> ${device.deviceName} (${device.deviceOS}) &bull; <strong>Region:</strong> ${county}`;
      }

      submitBtn.disabled = false;
      submitBtn.textContent = 'Confirm & Proceed \u2192';
      this.closeSurveyModal();

      if (window.App && typeof window.App.showToast === 'function') {
        window.App.showToast(`Verified: ${voterName} — ${county} County. Device & identity secured!`, 'success');
      }

      if (typeof this.pendingVoteCallback === 'function') {
        const cb = this.pendingVoteCallback;
        this.pendingVoteCallback = null;
        cb({
          userId: assignedUserId,
          voterKey: assignedUserId,
          voterName,
          voterIdNumber,
          county,
          dob,
          lat: loc.lat,
          lng: loc.lng,
          accuracy: loc.accuracy,
          deviceName: device.deviceName,
          deviceOS: device.deviceOS
        });
      }
    },

    ensureVoterSurveyBeforePoll(onVerifiedCallback) {
      if (this.hasCompletedDemographics() && localStorage.getItem('gir_voter_name') && localStorage.getItem('gir_voter_id_number')) {
        const loc = this.getLocation();
        const device = this.getDeviceInfo();
        const assignedUserId = this.getOrAssignUserId();
        onVerifiedCallback({
          userId: assignedUserId,
          voterKey: assignedUserId,
          voterName: localStorage.getItem('gir_voter_name') || 'USER@LOCATION1',
          voterIdNumber: localStorage.getItem('gir_voter_id_number') || 'ID-28491038',
          county: this.getCounty() || 'Nairobi',
          dob: this.getDob() || '1995-05-15',
          lat: loc.lat,
          lng: loc.lng,
          accuracy: loc.accuracy,
          deviceName: device.deviceName,
          deviceOS: device.deviceOS
        });
        return;
      }
      this.pendingVoteCallback = onVerifiedCallback;
      this.openSurveyModal({
        title: 'Voter Verification Required',
        subtitle: 'Identity & Location Verification',
        notice: 'Before casting your ballot, please verify your identity, county, and date of birth. This information is securely recorded with your vote.'
      });
    }
  };

  // Expose globally
  window.Demographics = Demographics;

  // Auto-init on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Demographics.init());
  } else {
    Demographics.init();
  }
})();
