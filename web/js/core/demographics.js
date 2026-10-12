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

  const Demographics = {
    counties: KENYA_COUNTIES,
    pendingVoteCallback: null,
    currentLocation: {
      lat: null,
      lng: null,
      accuracy: null,
      status: 'pending' // 'pending', 'acquired', 'denied', 'ip_fallback'
    },

    init() {
      // 1. Immediately request high-precision location on session start
      this.acquireLocation();

      // 2. Inject Modal Styles and Modal Container into DOM
      this.injectStyles();
      this.injectModal();

      // 3. If first-time visitor, show mandatory onboarding survey modal
      if (!this.hasCompletedDemographics()) {
        setTimeout(() => {
          this.openSurveyModal({
            title: "Welcome to Getitright — Civic Verification",
            subtitle: "Mandatory First-Time Visitor Survey",
            notice: "To prevent electoral manipulation and ensure accurate regional representation across Kenya's 47 counties, all citizens must declare their County and Date of Birth (DOB)."
          });
        }, 600);
      }
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
      return {
        lat: lat ? parseFloat(lat) : this.currentLocation.lat,
        lng: lng ? parseFloat(lng) : this.currentLocation.lng,
        accuracy: acc ? parseFloat(acc) : this.currentLocation.accuracy
      };
    },

    acquireLocation(forcePrompt = false) {
      if (!navigator.geolocation) {
        this.fallbackIpLocation();
        return;
      }

      const options = {
        enableHighAccuracy: true,
        timeout: 12000,
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
          this.currentLocation.status = error.code === 1 ? 'denied' : 'error';
          this.fallbackIpLocation();
        },
        options
      );
    },

    fallbackIpLocation() {
      fetch('https://ipapi.co/json/')
        .then(res => res.json())
        .then(data => {
          if (data && data.latitude && data.longitude) {
            this.currentLocation = {
              lat: data.latitude,
              lng: data.longitude,
              accuracy: 2500,
              status: 'ip_fallback'
            };
            if (!localStorage.getItem('gir_precise_lat')) {
              localStorage.setItem('gir_precise_lat', data.latitude);
              localStorage.setItem('gir_precise_lng', data.longitude);
              localStorage.setItem('gir_location_accuracy', 2500);
            }
            if (data.region && !localStorage.getItem('gir_county')) {
              const matched = KENYA_COUNTIES.find(c => data.region.toLowerCase().includes(c.toLowerCase()));
              if (matched) {
                const sel = document.getElementById('gir-survey-county');
                if (sel && !sel.value) sel.value = matched;
              }
            }
          }
          this.updateLocationBadge();
        })
        .catch(() => {
          // Default to Nairobi Central if all offline
          if (!this.currentLocation.lat) {
            this.currentLocation.lat = -1.286389;
            this.currentLocation.lng = 36.817223;
            this.currentLocation.accuracy = 5000;
            this.currentLocation.status = 'ip_fallback';
            this.updateLocationBadge();
          }
        });
    },

    updateLocationBadge() {
      const badge = document.getElementById('gir-geo-status-badge');
      if (!badge) return;

      if (this.currentLocation.status === 'acquired' && this.currentLocation.lat) {
        badge.innerHTML = `
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#303030;margin-right:6px;"></span>
          <strong>Precise GPS Verified:</strong> ${this.currentLocation.lat.toFixed(5)}, ${this.currentLocation.lng.toFixed(5)} (&plusmn;${Math.round(this.currentLocation.accuracy)}m)
        `;
        badge.style.borderColor = '#303030';
        badge.style.color = '#303030';
      } else if (this.currentLocation.status === 'ip_fallback' && this.currentLocation.lat) {
        badge.innerHTML = `
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#666;margin-right:6px;"></span>
          <strong>Network Location Captured:</strong> ${this.currentLocation.lat.toFixed(4)}, ${this.currentLocation.lng.toFixed(4)}
          <button type="button" onclick="window.Demographics.acquireLocation(true)" style="background:none;border:none;color:#303030;font-weight:700;text-decoration:underline;cursor:pointer;margin-left:6px;">Request GPS</button>
        `;
      } else if (this.currentLocation.status === 'denied') {
        badge.innerHTML = `
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#888;margin-right:6px;"></span>
          <strong>Location Permission Pending:</strong> Click allow to enable verified voter GPS.
          <button type="button" onclick="window.Demographics.acquireLocation(true)" style="background:none;border:none;color:#303030;font-weight:700;text-decoration:underline;cursor:pointer;margin-left:6px;">Enable GPS</button>
        `;
      } else {
        badge.innerHTML = `
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#888;margin-right:6px;"></span>
          Acquiring precise satellite location...
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
          padding: 32px;
          box-sizing: border-box;
          transform: translateY(20px) scale(0.98);
          transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
          font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }
        .gir-modal-overlay.active .gir-modal-box {
          transform: translateY(0) scale(1);
        }
        .gir-modal-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          margin-bottom: 16px;
        }
        .gir-modal-title {
          font-family: 'Outfit', sans-serif;
          font-size: 22px;
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
          padding: 12px 14px;
          margin-bottom: 20px;
        }
        .gir-form-group {
          margin-bottom: 18px;
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
          padding: 12px 14px;
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

          <div class="gir-modal-desc" id="gir-modal-desc-text">
            To prevent unfair manipulation and ensure genuine regional participation across Kenya's 47 counties, please verify your County and Date of Birth (DOB).
          </div>

          <form id="gir-demographics-form" onsubmit="window.Demographics.handleSubmit(event)">
            <div class="gir-form-group">
              <label class="gir-form-label" for="gir-survey-county">Select County of Residence / Voting</label>
              <select id="gir-survey-county" class="gir-form-select" required>
                <option value="" disabled selected>-- Select your County --</option>
                ${countiesOptions}
              </select>
            </div>

            <div class="gir-form-group">
              <label class="gir-form-label" for="gir-survey-dob">Date of Birth (DOB)</label>
              <input type="date" id="gir-survey-dob" class="gir-form-input" required max="2008-12-31">
              <div style="font-size:11px;color:#666;margin-top:4px;">Must be 18 years or older for official voting eligibility.</div>
            </div>

            <button type="submit" class="gir-submit-btn" id="gir-survey-submit-btn">
              Confirm &amp; Proceed &rarr;
            </button>
          </form>
        </div>
      `;

      document.body.appendChild(overlay);
      this.updateLocationBadge();

      // Pre-fill if already known
      const savedCounty = localStorage.getItem('gir_county');
      const savedDob = localStorage.getItem('gir_dob');
      if (savedCounty) {
        const cEl = document.getElementById('gir-survey-county');
        if (cEl) cEl.value = savedCounty;
      }
      if (savedDob) {
        const dEl = document.getElementById('gir-survey-dob');
        if (dEl) dEl.value = savedDob;
      }
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
      const county = document.getElementById('gir-survey-county').value;
      const dob = document.getElementById('gir-survey-dob').value;
      const submitBtn = document.getElementById('gir-survey-submit-btn');

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
      localStorage.setItem('gir_county', county);
      localStorage.setItem('gir_dob', dob);
      localStorage.setItem('gir_demographics_completed', 'true');
      localStorage.setItem('gir_voter_verified', 'true');

      const loc = this.getLocation();

      // Submit to Backend API
      try {
        const voterKey = localStorage.getItem('gir_voter_key') || ('Voter-' + Math.floor(Math.random() * 90000 + 10000));
        localStorage.setItem('gir_voter_key', voterKey);

        let userId = null;
        try {
          const uStr = localStorage.getItem('gir_user');
          if (uStr) userId = JSON.parse(uStr).id;
        } catch (_) {}

        await fetch('/api/visitor-demographics', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            county: county,
            dob: dob,
            latitude: loc.lat,
            longitude: loc.lng,
            accuracy: loc.accuracy,
            voterKey: voterKey,
            userId: userId,
            platform: 'web'
          })
        });
      } catch (err) {
        console.warn('[Demographics] Demographic API sync:', err);
      }

      submitBtn.disabled = false;
      submitBtn.textContent = 'Confirm & Proceed \u2192';
      this.closeSurveyModal();

      if (window.App && typeof window.App.showToast === 'function') {
        window.App.showToast(`Verified: ${county} County. Demographics secured!`, 'success');
      }

      // If a vote was waiting for this verification, resume the vote immediately!
      if (typeof this.pendingVoteCallback === 'function') {
        const cb = this.pendingVoteCallback;
        this.pendingVoteCallback = null;
        cb({ county, dob, lat: loc.lat, lng: loc.lng });
      }
    },

    // Guard called before taking any poll:
    // ALWAYS asks for County and DOB as a survey if not yet completed!
    ensureVoterSurveyBeforePoll(onVerifiedCallback) {
      if (this.hasCompletedDemographics()) {
        const loc = this.getLocation();
        onVerifiedCallback({
          county: this.getCounty(),
          dob: this.getDob(),
          lat: loc.lat,
          lng: loc.lng
        });
        return;
      }

      // Not yet verified -> open mandatory pre-poll survey modal
      this.pendingVoteCallback = onVerifiedCallback;
      this.openSurveyModal({
        title: "Voter Survey Required Before Voting",
        subtitle: "County & Date of Birth (DOB) Verification",
        notice: "Before casting your vote, Kenyan civic verification requires confirming your County and Date of Birth (DOB) for ledger inclusion."
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
