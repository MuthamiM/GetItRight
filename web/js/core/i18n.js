/* =============================================================
   POLLTRACK — Internationalization (i18n) Engine
   Externalized Strings: English (en) & Kiswahili (sw)
   Zero emojis.
   ============================================================= */

const I18n = {
  currentLang: localStorage.getItem('pt_lang') || 'en',

  translations: {
    en: {
      brand: "PollTrack",
      tagline: "Polls you can prove.",
      subtagline: "Tamper-evident polling, station capture, and append-only cryptographic verification.",
      
      // Navigation
      nav_features: "Features",
      nav_pricing: "Pricing",
      nav_verify: "Public Verifier",
      nav_docs: "Docs",
      nav_login: "Sign In",
      nav_start_free: "Create Free Poll",
      nav_console: "Console",

      // Hero
      hero_title_1: "Polls you can",
      hero_title_accent: "prove.",
      hero_desc: "Observers capture polling-station results tied to hardware keys, photos, and GPS. Cryptographically committed to an append-only hash chain with published Merkle roots.",
      hero_cta_primary: "Create Free Poll",
      hero_cta_secondary: "See Live Verifier",
      hero_trust_strip_1: "Published Merkle Roots",
      hero_trust_strip_2: "In-Browser SHA-256 Verifier",
      hero_trust_strip_3: "External Timestamp Anchors",

      // Tiers
      tier_free: "Free",
      tier_pro: "Pro",
      tier_org: "Organisation",
      tier_election: "Election / Enterprise",
      tier_free_price: "KES 0",
      tier_pro_price: "KES 1,500/mo",
      tier_pro_price_usd: "(~$12/mo)",
      tier_org_price: "KES 6,500/mo",
      tier_org_price_usd: "(~$49/mo)",
      tier_election_price: "Custom / per station",
      tier_election_sub: "Starts KES 150-400 / station",
      upgrade_to_pro: "Available on Pro",
      upgrade_to_org: "Available on Organisation",
      upgrade_to_election: "Available on Election Tier",

      // Status Vocabulary (Section 4)
      status_draft: "Draft",
      status_open: "Open",
      status_live: "Live",
      status_closed: "Closed",
      status_pending_sync: "Pending sync",
      status_provisional: "Provisional",
      status_verified: "Verified",
      status_flagged: "Flagged",
      status_frozen: "Frozen",
      status_superseded: "Superseded",
      status_certified: "Certified",

      // Verifier
      verifier_title: "Public Ledger Verifier",
      verifier_sub: "Verify any result photo or hash receipt independently without logging in. All hashing happens client-side in your browser.",
      verifier_dropzone: "Drop result photo here or click to browse",
      verifier_hash_input: "Or paste SHA-256 hash or Entry receipt",
      verifier_btn: "Verify Against Ledger",
      verifier_match: "MATCH VERIFIED",
      verifier_not_found: "HASH NOT FOUND",
      verifier_mismatch: "MISMATCH DETECTED",
      verifier_explanation: "This entry was cryptographically anchored in Merkle Checkpoint #142 at 2026-09-30 02:15 UTC. The computed leaf matches the published root.",

      // Console
      sidebar_dashboard: "Dashboard",
      sidebar_polls: "Polls",
      sidebar_stations: "Stations",
      sidebar_observers: "Observers & Devices",
      sidebar_ledger: "Ledger Explorer",
      sidebar_anomalies: "Anomaly Engine",
      sidebar_disputes: "Disputes & Review",
      sidebar_checkpoints: "Checkpoints",
      sidebar_audit_log: "Audit Log",
      sidebar_operations: "System Operations",
      sidebar_billing: "Billing & Plans",
      sidebar_settings: "Settings",

      // Dispute & Reconciliation
      dispute_title: "Station Dispute & Reviewer Reconciliation",
      dispute_status_frozen: "STATION FROZEN: Observers report differing tally counts",
      dispute_accept_a: "Accept Observer A",
      dispute_accept_b: "Accept Observer B",
      dispute_order_recount: "Order Official Recount",
      dispute_escalate: "Escalate to Tribunal",

      // Mobile Observer
      mobile_capture_title: "Capture Station Form",
      mobile_enter_counts: "Enter Structured Counts",
      mobile_sign_submit: "Sign with Hardware Key",
      mobile_duress_alert: "Silent Duress Alert",
      mobile_offline_banner: "Offline mode: Submissions encrypted in outbox",
    },

    sw: {
      brand: "PollTrack",
      tagline: "Kura unazoweza kuthibitisha.",
      subtagline: "Mfumo wa kura usiobadilika, unasa picha za vituo, na uthibitisho wa kihasibu wa Merkle.",
      
      // Navigation
      nav_features: "Sifa Kuu",
      nav_pricing: "Bei na Vifurushi",
      nav_verify: "Kithibitishaji cha Umma",
      nav_docs: "Nyaraka",
      nav_login: "Ingia",
      nav_start_free: "Anzisha Kura Bure",
      nav_console: "Dashibodi Kuu",

      // Hero
      hero_title_1: "Kura unazoweza",
      hero_title_accent: "kuthibitisha.",
      hero_desc: "Waangalizi wanarekodi matokeo ya vituo yakifungwa na funguo za kifaa, picha na GPS. Kila matokeo yanalindwa kwenye mnyororo wa hesabu na mizizi ya Merkle iliyochapishwa.",
      hero_cta_primary: "Anzisha Kura Bure",
      hero_cta_secondary: "Tazama Kithibitishaji",
      hero_trust_strip_1: "Mizizi ya Merkle Iliyochapishwa",
      hero_trust_strip_2: "Uthibitisho wa SHA-256 Kivinjari",
      hero_trust_strip_3: "Nukuu za Muda Zisizobadilika",

      // Tiers
      tier_free: "Bure",
      tier_pro: "Pro",
      tier_org: "Shirika",
      tier_election: "Uchaguzi / Biashara",
      tier_free_price: "KES 0",
      tier_pro_price: "KES 1,500/mwezi",
      tier_pro_price_usd: "(~$12/mwezi)",
      tier_org_price: "KES 6,500/mwezi",
      tier_org_price_usd: "(~$49/mwezi)",
      tier_election_price: "Maalum / kwa kituo",
      tier_election_sub: "Huanzia KES 150-400 / kituo",
      upgrade_to_pro: "Inapatikana kwenye Pro",
      upgrade_to_org: "Inapatikana kwenye Shirika",
      upgrade_to_election: "Inapatikana kwenye Uchaguzi",

      // Status Vocabulary
      status_draft: "Rasimu",
      status_open: "Wazi",
      status_live: "Mbashara",
      status_closed: "Imefungwa",
      status_pending_sync: "Inasubiri kuoanishwa",
      status_provisional: "Ya mpito",
      status_verified: "Imethibitishwa",
      status_flagged: "Imewekewa alama",
      status_frozen: "Imegandishwa",
      status_superseded: "Imebadilishwa",
      status_certified: "Imeidhinishwa Rasmi",

      // Verifier
      verifier_title: "Kithibitishaji cha Umma",
      verifier_sub: "Thibitisha picha ya matokeo au risiti ya hesabu bila kuingia. Ukokotoaji wote unafanyika ndani ya kivinjari chako.",
      verifier_dropzone: "Weka picha ya fomu hapa au bofya kuchagua",
      verifier_hash_input: "Au weka nambari ya SHA-256 au nambari ya risiti",
      verifier_btn: "Thibitisha Kwenye Leja",
      verifier_match: "IMETHIBITISHWA: INALINGANA",
      verifier_not_found: "NAMBARI HAIJAPATIKANA",
      verifier_mismatch: "TOFAUTI IMETAMBULIKA",
      verifier_explanation: "Taarifa hii ilifungwa kwenye Merkle Checkpoint #142 tarehe 2026-09-30 02:15 UTC. Hesabu inalingana na mzizi uliochapishwa.",

      // Console
      sidebar_dashboard: "Dashibodi",
      sidebar_polls: "Kura",
      sidebar_stations: "Vituo vya Kura",
      sidebar_observers: "Waangalizi na Vifaa",
      sidebar_ledger: "Mchunguzi wa Leja",
      sidebar_anomalies: "Hitilafu za Takwimu",
      sidebar_disputes: "Migogoro na Mapitio",
      sidebar_checkpoints: "Vituo vya Merkle",
      sidebar_audit_log: "Kumbukumbu ya Vitendo",
      sidebar_operations: "Uendeshaji wa Mifumo",
      sidebar_billing: "Malipo na Vifurushi",
      sidebar_settings: "Mipangilio",

      // Dispute & Reconciliation
      dispute_title: "Mapitio ya Mgogoro wa Kituo",
      dispute_status_frozen: "KITUO KIMEGANDISHWA: Waangalizi wamewasilisha matokeo yanayotofautiana",
      dispute_accept_a: "Kubali Mwangalizi A",
      dispute_accept_b: "Kubali Mwangalizi B",
      dispute_order_recount: "Agiza Hesabu Upya",
      dispute_escalate: "Peleka kwenye Mahakama",

      // Mobile Observer
      mobile_capture_title: "Piga Picha ya Fomu ya Kituo",
      mobile_enter_counts: "Ingiza Matokeo ya Kura",
      mobile_sign_submit: "Saini kwa Ufunguo wa Kifaa",
      mobile_duress_alert: "Tahadhari ya Siri ya Shambulio",
      mobile_offline_banner: "Hali ya bila mtandao: Taarifa zimelindwa kwenye kifaa",
    }
  },

  t(key) {
    const lang = this.translations[this.currentLang] || this.translations.en;
    return lang[key] || this.translations.en[key] || key;
  },

  setLanguage(lang) {
    if (this.translations[lang]) {
      this.currentLang = lang;
      localStorage.setItem('pt_lang', lang);
      this.applyTranslations();
      document.documentElement.lang = lang;
    }
  },

  applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const val = this.t(key);
      if (el.tagName === 'INPUT' && (el.type === 'text' || el.type === 'search')) {
        el.placeholder = val;
      } else {
        el.textContent = val;
      }
    });

    // Update active lang button UI if exists
    document.querySelectorAll('.lang-selector-btn').forEach(btn => {
      if (btn.getAttribute('data-lang') === this.currentLang) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }
};

document.addEventListener('DOMContentLoaded', () => {
  I18n.applyTranslations();
});

if (typeof module !== 'undefined' && module.exports) {
  module.exports = I18n;
}
