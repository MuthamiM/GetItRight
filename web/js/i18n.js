/* =============================================================
   IcapsQ — Internationalization (i18n) Engine & Israel Geo-Detection
   Supports: English (en) & Hebrew (he / עברית)
   Includes auto-detection for Israel IP / Timezone & complete RTL support
   ============================================================= */

(function (window, document) {
  'use strict';

  const translations = {
    en: {
      // Navigation
      nav_brand: 'Icaps',
      nav_brand_q: 'Q',
      nav_features: 'Features',
      nav_polls: 'Active Polls',
      nav_surveys: 'Active Surveys',
      nav_pricing: 'Pricing',
      nav_how_it_works: 'How It Works',
      nav_contact: 'Contact',
      nav_blog: 'Blog',
      nav_signin: 'Sign In',
      nav_org_signin: 'Organization Sign In',
      nav_org_signin_mobile: 'Org Sign In',
      nav_get_started: 'Get Started',
      nav_switch_lang: 'HE | עברית',
      nav_switch_lang_title: 'Switch to Hebrew',

      // Hero
      hero_headline: 'Capture <em>every</em> voice.',
      hero_sub: 'The polling platform that empowers organizations to publish targeted surveys and engage citizens through mobile voting — with live analytics.',
      hero_btn_polls: 'Vote in Live Polls',
      hero_btn_apk: 'Download IcapsQ APK',
      hero_btn_console: 'Organization Console',

      // Trusted By
      trusted_label: 'Trusted by:',
      trust_county: 'County Governments',
      trust_research: 'Research Institutes',
      trust_ngos: 'NGOs',
      trust_civic: 'Civic Organizations',
      trust_unis: 'Universities',
      trust_elections: 'Election Bodies',

      // Features
      feat_tag: 'Features',
      feat_headline: "We've solved the feedback gap.",
      feat_desc: 'IcapsQ gives organizations real participation data, without the noise. Publish, engage, analyze — all in one platform.',
      feat_target_title: 'Targeted Polling',
      feat_target_desc: 'Filter by county, audience, or topic to reach the people your research is meant for.',
      feat_sec_title: 'Sovereign Security',
      feat_sec_desc: 'Enterprise cryptographic controls ensure zero ballot tampering, with hardware-backed integrity.',
      feat_analytics_title: 'Real-Time Analytics',
      feat_analytics_desc: 'Live breakdown by geography, demographics, and trends as votes stream in.',
      feat_mobile_title: 'Mobile App Engagement',
      feat_mobile_desc: 'Android app brings your surveys directly to the pockets of citizens and team members.',
      feat_ballots_title: 'Verified Ballots',
      feat_ballots_desc: 'Anti-duplicate technology guarantees one person, one vote across every published referendum.',
      feat_export_title: 'Export & API',
      feat_export_desc: 'Export raw or aggregated CSVs, connect BI tools, or pipe live results into your CRM.',

      // Big Picture
      bp_tag: 'How It Works',
      bp_headline: 'The sovereign polling infrastructure.',
      bp_desc: 'Built from the ground up for transparency, cryptographic integrity, and sovereign organizational governance.',
      bp_step_1: 'Publish poll or survey with custom targeting & quotas',
      bp_step_2: 'Participants engage via mobile app or web portal',
      bp_step_3: 'Live cryptographic aggregation with zero tampering',
      bp_step_4: 'Export certified reports & executive analytics',

      // Pricing
      pricing_tag: 'Plans & Pricing',
      pricing_headline: 'Transparent plans for every organization.',
      pricing_desc: 'Whether you are a civic group, researcher, or large enterprise, IcapsQ scales to your audience.',
      tier_starter_name: 'Community Grassroots',
      tier_starter_desc: 'Essential public polls & citizen engagement',
      tier_pro_name: 'Professional',
      tier_pro_desc: 'Targeted research & multi-county quotas',
      tier_enterprise_name: 'Institutional',
      tier_enterprise_desc: 'National referendums & sovereign deployments',
      pricing_btn_start: 'Get Started',
      pricing_btn_contact: 'Contact Sales',

      // Discover / CTA
      cta_headline: 'Start capturing real voices today.',
      cta_desc: 'Join civic organizations, universities, and research institutes using IcapsQ across sovereign referendums.',
      cta_btn_primary: 'Create Account',
      cta_btn_secondary: 'Browse Active Polls',

      // Footer
      footer_tagline: 'Empowering organizations with verified sovereign poll and feedback management, real-time analytics, and mobile research engagement across Kenya and globally.',
      footer_nav_title: 'Navigation',
      footer_home: 'Home',
      footer_active_polls: 'Active Polls',
      footer_active_surveys: 'Active Surveys',
      footer_blog: 'Blog',
      footer_orgs_title: 'Organizations',
      footer_signin: 'Organization Sign In',
      footer_create_acc: 'Create Account',
      footer_compare: 'Plan & Quotas',
      footer_sov_title: 'Sovereignty',
      footer_download_app: 'Download Mobile App',
      footer_rights: 'All rights reserved.',
      footer_product_of: 'Product of M&F Technologies',

      // Polls (vote.html)
      polls_dir_tag: 'Public & Community Directory',
      polls_header_title: 'Active Public Polls & Referendums',
      polls_header_desc: 'Browse published community referendums, organizational polls, and civic inquiries. Vote directly to express your perspective and view verified real-time aggregate totals.',
      polls_search_ph: 'Search active polls...',
      filter_all_polls: 'All Active Polls',
      filter_community: 'Community Grassroots',
      filter_research: 'Research & Industry',
      filter_unions: 'Institutional Unions & NGOs',
      filter_civic: 'Civic Assemblies',

      // Poll Card & Donut
      total_votes: 'TOTAL VOTES',
      total_votes_mixed: 'Total Votes',
      tap_slice: 'Tap slice',
      vote_unit_singular: 'Vote',
      vote_unit_plural: 'Votes',
      turnout: 'Turnout',
      votes_cast: 'votes cast',
      time_left: 'left',
      voting_closed: 'Voting Closed',
      share_poll: 'Share Poll',
      already_voted: 'Already voted.',
      your_vote: 'YOUR VOTE',
      voted_badge: '[Voted]',
      no_polls_match: 'No active polls found matching this filter.',

      // Poll Sidebar
      sidebar_mobile_title: 'Mobile App Participation',
      sidebar_mobile_sub: 'Participate on Mobile',
      sidebar_mobile_desc: 'Download the IcapsQ Mobile App for Android to cast votes and complete surveys anywhere on the go.',
      sidebar_mobile_btn: 'Get Android Mobile App →',

      // Voter Demographics Modal
      modal_verify_title: 'Civic Verification Survey',
      modal_verify_sub: 'Kenya 47 Counties Voter Verification',
      modal_verify_desc: 'To ensure genuine regional representation and prevent ballot duplication, please confirm your verification details and County of residence.',
      lbl_voter_name: 'Full Name (as on ID / Passport)',
      ph_voter_name: 'e.g. John Kamau Mwangi',
      lbl_voter_id: 'National ID Number · 5–12 digits',
      ph_voter_id: 'e.g. 12345678',
      lbl_voter_county: 'Select County of Residence / Voting',
      ph_voter_county: '-- Select your County --',
      lbl_voter_dob: 'Date of Birth (DOB) · YYYY-MM-DD',
      ph_voter_dob: 'YYYY-MM-DD',
      btn_confirm_proceed: 'Confirm & Proceed →',
      btn_checking: 'Checking…',
      btn_cancel: 'Cancel',

      // Surveys (surveys.html)
      surveys_dir_tag: 'Public & Community Inquiries',
      surveys_header_title: 'Active Research & Public Surveys',
      surveys_header_desc: 'Explore published institutional surveys, research inquiries, and public feedback forms. Share your perspective and track verified response metrics in real-time.',
      surveys_search_ph: 'Search surveys...',
      filter_all_surveys: 'All Audiences',
      filter_public_citizens: 'Public Citizens',
      filter_enterprises: 'Enterprise & Industry',
      filter_students: 'Universities & Students',
      filter_healthcare: 'Health & Well-being',
      survey_target_label: 'Response target',
      survey_target_of: 'of',
      survey_responses_unit: 'responses',
      btn_share_survey: 'Share Link',
      btn_take_survey: 'Take Survey →',
      survey_completed: 'Completed',
      no_surveys_match: 'No active surveys found matching this filter.',

      // Survey Runner Modal
      survey_modal_title: 'Official Survey',
      survey_step_label: 'Question {curr} of {total}',
      survey_btn_prev: '← Previous',
      survey_btn_next: 'Next →',
      survey_btn_submit: 'Submit Survey',
      survey_submitting: 'Submitting…',
      survey_success_title: 'Thank you for participating!',
      survey_success_desc: 'Your feedback has been verified and recorded on the sovereign ledger.',
      survey_btn_close: 'Close',

      // Blog (blog.html)
      blog_header_title: 'Research, Methodology & Sovereign Data',
      blog_header_desc: 'Insights on sovereign polling, cryptographic verification, and civic engagement published by verified institutions across Kenya.',
      blog_read_brief: 'Read Brief →',
      blog_back_articles: '← Back to all articles',
      blog_published_on: 'Published on',
      blog_reading_time: 'min read',

      // Mobile App Page (mobile-app.html)
      app_download_title: 'Download IcapsQ Android App',
      app_eyebrow: 'MOBILE ENGAGEMENT',
      app_main_title: 'Participate anywhere on mobile.',
      app_intro: 'Download the official IcapsQ Mobile App for Android to cast votes, participate in civic referendums, and complete community surveys on the go.',
      app_btn_download: 'Download IcapsQ APK',
      app_version_label: 'Version 2.1.35 (Build 47) · Android 7.0+',

      // Auth (login.html, signup.html)
      auth_login_title: 'Organization Sign In',
      auth_login_sub: 'Enter your credentials to access your organization workspace.',
      auth_email_lbl: 'Email Address',
      auth_email_ph: 'name@organization.org',
      auth_password_lbl: 'Password',
      auth_password_ph: 'Enter your password',
      auth_btn_signin: 'Sign In →',
      auth_forgot_pwd: 'Forgot password?',
      auth_no_account: "Don't have an organization account?",
      auth_create_account_link: 'Create Account',
      auth_signup_title: 'Create Organization Account',
      auth_signup_sub: 'Start publishing sovereign polls and surveys.'
    },

    he: {
      // Navigation
      nav_brand: 'Icaps',
      nav_brand_q: 'Q',
      nav_features: 'תכונות',
      nav_polls: 'סקרים פעילים',
      nav_surveys: 'שאלונים פעילים',
      nav_pricing: 'תמחור',
      nav_how_it_works: 'איך זה עובד',
      nav_contact: 'צור קשר',
      nav_blog: 'בלוג',
      nav_signin: 'התחברות',
      nav_org_signin: 'כניסת ארגונים',
      nav_org_signin_mobile: 'כניסת ארגון',
      nav_get_started: 'התחל עכשיו',
      nav_switch_lang: 'EN | English',
      nav_switch_lang_title: 'Switch to English',

      // Hero
      hero_headline: 'לשמוע <em>כל</em> קול.',
      hero_sub: 'פלטפורמת הסקרים והמשוב המאפשרת לארגונים לפרסם שאלונים ממוקדים, לשתף אזרחים בהצבעה סלולרית ולקבל ניתוח נתונים בזמן אמת.',
      hero_btn_polls: 'הצבע בסקרים חיים',
      hero_btn_apk: 'הורד את IcapsQ ל-Android',
      hero_btn_console: 'לוח בקרה לארגונים',

      // Trusted By
      trusted_label: 'מהימן על ידי:',
      trust_county: 'רשויות מקומיות וממשל',
      trust_research: 'מכוני מחקר',
      trust_ngos: 'עמותות וארגונים',
      trust_civic: 'ארגונים אזרחיים',
      trust_unis: 'אוניברסיטאות',
      trust_elections: 'ועדות בחירות',

      // Features
      feat_tag: 'תכונות עיקריות',
      feat_headline: 'פתרנו את הפער באיסוף המשוב.',
      feat_desc: 'פלטפורמת IcapsQ מעניקה לארגונים נתוני השתתפות אמיתיים ללא רעשי רקע. פרסום, שיתוף וניתוח — הכל במקום אחד.',
      feat_target_title: 'סקרים ממוקדים',
      feat_target_desc: 'סינון לפי מחוז, קהל יעד או נושא כדי להגיע בדיוק לאנשים שהמחקר מיועד עבורם.',
      feat_sec_title: 'אבטחה ריבונית',
      feat_sec_desc: 'בקרות קריפטוגרפיות מוסדיות המבטיחות שלמות הצבעה מוחלטת ללא חשש מזיופים.',
      feat_analytics_title: 'ניתוח נתונים בזמן אמת',
      feat_analytics_desc: 'פילוח חי לפי אזור גיאוגרפי, דמוגרפיה ומגמות תוך כדי זרימת הקולות.',
      feat_mobile_title: 'מעורבות באפליקציה',
      feat_mobile_desc: 'אפליקציית Android מנגישה את השאלונים ישירות לכיסם של אזרחים ומשתתפים.',
      feat_ballots_title: 'הצבעות מאומתות',
      feat_ballots_desc: 'מנגנון למניעת כפילויות המבטיח קול אחד לכל אדם בכל משאל עם וסקר.',
      feat_export_title: 'ייצוא נתונים וממשק API',
      feat_export_desc: 'ייצוא נתונים מלא בפורמט CSV, חיבור לכלי BI והזרמת תוצאות בזמן אמת למערכות הארגון.',

      // Big Picture
      bp_tag: 'איך זה עובד',
      bp_headline: 'תשתית הסקרים הריבונית.',
      bp_desc: 'נבנה מהיסוד לשקיפות מרבית, אמינות קריפטוגרפית ושליטה ארגונית מלאה.',
      bp_step_1: 'פרסם סקר או שאלון עם הגדרות קהל ומכסות ייעודיות',
      bp_step_2: 'המשתתפים מצביעים דרך האפליקציה לנייד או פורטל האינטרנט',
      bp_step_3: 'איגום קריפטוגרפי בזמן אמת ללא אפשרות לשינוי נתונים',
      bp_step_4: 'ייצוא דוחות מוסמכים וניתוחים מעמיקים להנהלה',

      // Pricing
      pricing_tag: 'מסלולים ותמחור',
      pricing_headline: 'מסלולים שקופים ומותאמים לכל ארגון.',
      pricing_desc: 'בין אם אתם קבוצה אזרחית, מכון מחקר או ארגון ענק, IcapsQ מתאימה את עצמה לצרכים שלכם.',
      tier_starter_name: 'קהילה ושטח',
      tier_starter_desc: 'סקרים ציבוריים בסיסיים ומעורבות אזרחית',
      tier_pro_name: 'מקצועי (Pro)',
      tier_pro_desc: 'מחקר ממוקד ומכסות רב-אזוריות',
      tier_enterprise_name: 'מוסדי / ארגוני',
      tier_enterprise_desc: 'משאלי עם לאומיים ופריסות ייעודיות',
      pricing_btn_start: 'התחל עכשיו',
      pricing_btn_contact: 'צור קשר עם המכירות',

      // Discover / CTA
      cta_headline: 'התחל באיסוף קולות מאומתים עוד היום.',
      cta_desc: 'הצטרף לארגונים אזרחיים, אוניברסיטאות ומכוני מחקר המשתמשים ב-IcapsQ למשאלי עם מהימנים.',
      cta_btn_primary: 'פתח חשבון',
      cta_btn_secondary: 'עיין בסקרים פעילים',

      // Footer
      footer_tagline: 'מעצימים ארגונים עם ניהול סקרים ומשוב מאומת, ניתוח נתונים בזמן אמת ומעורבות סלולרית מתקדמת בישראל, קניה ובעולם.',
      footer_nav_title: 'ניווט',
      footer_home: 'דף הבית',
      footer_active_polls: 'סקרים פעילים',
      footer_active_surveys: 'שאלונים פעילים',
      footer_blog: 'בלוג',
      footer_orgs_title: 'לארגונים',
      footer_signin: 'כניסת ארגונים',
      footer_create_acc: 'פתיחת חשבון',
      footer_compare: 'מסלולים ומכסות',
      footer_sov_title: 'הורדות ואפליקציה',
      footer_download_app: 'הורד אפליקציה לנייד',
      footer_rights: 'כל הזכויות שמורות.',
      footer_product_of: 'מוצר מבית M&F Technologies',

      // Polls (vote.html)
      polls_dir_tag: 'מדריך קהילתי וציבורי',
      polls_header_title: 'סקרים ומשאלי עם פעילים',
      polls_header_desc: 'עיין במשאלי עם קהילתיים, סקרי ארגונים ובירורים אזרחיים. הצבע ישירות כדי להביע את עמדתך וצפה בנתונים מצטברים מאומתים בזמן אמת.',
      polls_search_ph: 'חיפוש סקרים פעילים...',
      filter_all_polls: 'כל הסקרים הפעילים',
      filter_community: 'שטח וקהילה',
      filter_research: 'מחקר ותעשייה',
      filter_unions: 'איגודים מוסדיים ועמותות',
      filter_civic: 'אספות אזרחיות',

      // Poll Card & Donut
      total_votes: 'סה״כ קולות',
      total_votes_mixed: 'סה״כ קולות',
      tap_slice: 'לחץ על פלח',
      vote_unit_singular: 'קול',
      vote_unit_plural: 'קולות',
      turnout: 'אחוז הצבעה',
      votes_cast: 'קולות נמסרו',
      time_left: 'נותרו',
      voting_closed: 'ההצבעה נסגרה',
      share_poll: 'שתף סקר',
      already_voted: 'כבר הצבעת.',
      your_vote: 'הצבעתך',
      voted_badge: '[הצבעת]',
      no_polls_match: 'לא נמצאו סקרים פעילים התואמים את הסינון הנוכחי.',

      // Poll Sidebar
      sidebar_mobile_title: 'השתתפות באפליקציה',
      sidebar_mobile_sub: 'הצבע ישירות מהנייד',
      sidebar_mobile_desc: 'הורד את אפליקציית IcapsQ ל-Android כדי להצביע ולמלא שאלונים מכל מקום ובכל עת.',
      sidebar_mobile_btn: '← הורד אפליקציה ל-Android',

      // Voter Demographics Modal
      modal_verify_title: 'אימות פרטי הצבעה אזרחיים',
      modal_verify_sub: 'אימות פרטי מצביע ומניעת כפילויות',
      modal_verify_desc: 'כדי להבטיח ייצוג אזורי מהימן ולמנוע כפילות בהצבעה, אנא אמת את פרטיך ואזור מגוריך.',
      lbl_voter_name: 'שם מלא (לפי תעודת זהות / דרכון)',
      ph_voter_name: 'לדוגמה: ישראל ישראלי',
      lbl_voter_id: 'מספר תעודת זהות · 5–12 ספרות',
      ph_voter_id: 'לדוגמה: 012345678',
      lbl_voter_county: 'בחר אזור / מחוז מגורים להצבעה',
      ph_voter_county: '-- בחר אזור מגורים / מחוז --',
      lbl_voter_dob: 'תאריך לידה · YYYY-MM-DD',
      ph_voter_dob: 'YYYY-MM-DD',
      btn_confirm_proceed: '← אישור והמשך להצבעה',
      btn_checking: 'בודק…',
      btn_cancel: 'ביטול',

      // Surveys (surveys.html)
      surveys_dir_tag: 'שאלוני משוב ומחקר ציבוריים',
      surveys_header_title: 'מחקרים ושאלוני משוב פעילים',
      surveys_header_desc: 'גלה שאלוני משוב ציבוריים, סקרי שביעות רצון ומחקרי קהילה מאומתים. הבע את דעתך ועקוב אחר תוצאות אמת.',
      surveys_search_ph: 'חיפוש שאלונים...',
      filter_all_surveys: 'כל הקהלים',
      filter_public_citizens: 'ציבור רחב',
      filter_enterprises: 'ארגונים ותעשייה',
      filter_students: 'אקדמיה וסטודנטים',
      filter_healthcare: 'בריאות ואיכות חיים',
      survey_target_label: 'יעד מענה',
      survey_target_of: 'מתוך',
      survey_responses_unit: 'מענים',
      btn_share_survey: 'שתף קישור',
      btn_take_survey: '← התחל שאלון',
      survey_completed: 'הושלם',
      no_surveys_match: 'לא נמצאו שאלונים התואמים את החיפוש הנוכחי.',

      // Survey Runner Modal
      survey_modal_title: 'שאלון רשמי',
      survey_step_label: 'שאלה {curr} מתוך {total}',
      survey_btn_prev: 'הקודם →',
      survey_btn_next: '← הבא',
      survey_btn_submit: 'שלח שאלון',
      survey_submitting: 'שולח…',
      survey_success_title: 'תודה רבה על השתתפותך!',
      survey_success_desc: 'התשובות שלך נרשמו ואומתו ברישום המאובטח של IcapsQ.',
      survey_btn_close: 'סגור',

      // Blog (blog.html)
      blog_header_title: 'מחקר, מתודולוגיה ונתונים ריבוניים',
      blog_header_desc: 'תובנות על סקרים אמינים, אימות קריפטוגרפי ומעורבות אזרחית מגופים מאומתים.',
      blog_read_brief: '← קרא תקציר',
      blog_back_articles: 'חזרה לכל המאמרים →',
      blog_published_on: 'פורסם בתאריך',
      blog_reading_time: 'דקות קריאה',

      // Mobile App Page (mobile-app.html)
      app_download_title: 'הורד את אפליקציית IcapsQ ל-Android',
      app_eyebrow: 'מעורבות סלולרית',
      app_main_title: 'השתתף מכל מקום בנייד.',
      app_intro: 'הורד את אפליקציית IcapsQ הרשמית ל-Android כדי להצביע בסקרים, להשתתף במשאלי עם אזרחיים ולמלא שאלונים בקלות בכל עת.',
      app_btn_download: 'הורד את קובץ ה-APK',
      app_version_label: 'גרסה 2.1.35 (Build 47) · אנדרואיד 7.0 ומעלה',

      // Auth (login.html, signup.html)
      auth_login_title: 'כניסת ארגונים',
      auth_login_sub: 'הזן את פרטיך כדי להתחבר לסביבת העבודה של הארגון.',
      auth_email_lbl: 'כתובת דואר אלקטרוני',
      auth_email_ph: 'name@organization.org',
      auth_password_lbl: 'Password',
      auth_password_ph: 'הזן את סיסמתך',
      auth_btn_signin: '← התחבר',
      auth_forgot_pwd: 'שכחת סיסמה?',
      auth_no_account: 'אין לך חשבון ארגון עדיין?',
      auth_create_account_link: 'פתיחת חשבון',
      auth_signup_title: 'פתיחת חשבון ארגון חדש',
      auth_signup_sub: 'התחל לפרסם סקרים ושאלונים מאומתים.'
    }
  };

  // Known dynamic item translations
  const pollOverrides = {
    'PL-KENYA-2027-01': {
      he: {
        category: 'עדיפות אזרחית',
        title: 'סדרי עדיפויות כלכליים ויוקר המחיה',
        description: 'משאל עם אזרחי מאומת על התערבויות פיסקליות וכלכליות נדרשות בכלל האזורים.',
        options: [
          'ביטחון תזונתי וסבסוד תשומות חקלאיות',
          'ייצוב מחירי הדלק והאנרגיה למשקי הבית',
          'שירותי בריאות נגישים ואספקת תרופות למרפאות',
          'תעסוקת צעירים ומרכזי משרות דיגיטליות',
          'הקלות מס ואשראי לעסקים קטנים ובינוניים'
        ]
      }
    }
  };

  const surveyOverrides = {
    'SRV-KENYA-2027-01': {
      he: {
        title: 'מדד שירותי בריאות ורפואה ציבורית 2026',
        description: 'הערכה לאומית מאומתת האוספת משוב ישיר מאזרחים על זמני המתנה במרפאות, זמינות תרופות חיוניות ומימון שירותי רפואה.',
        category: 'בריאות ושירותים ציבוריים',
        publisher: 'מכון מחקר ומודיעין ציבורי IcapsQ'
      }
    },
    'SV-CIVIC-001': {
      he: {
        title: 'שאלון הערכת איכות שירותי בריאות ציבוריים',
        description: 'משוב קהילתי על זמני המתנה, זמינות תרופות ואיכות הטיפול במרפאות אזוריות.'
      }
    },
    'SV-YOUTH-002': {
      he: {
        title: 'סקר הכשרה דיגיטלית ומוכנות לשוק העבודה',
        description: 'הערכת מיומנויות מחשוב, גישה לאינטרנט וצרכי הכשרה מקצועית בקרב צעירים.'
      }
    }
  };

  const RTL_CSS = `
    /* === IcapsQ Hebrew RTL Global Enhancements === */
    html[dir="rtl"], body.rtl-mode {
      direction: rtl !important;
      text-align: right !important;
      font-family: 'Heebo', 'Assistant', 'Rubik', 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }

    body.rtl-mode .ln-nav-links,
    body.rtl-mode .ln-nav-right,
    body.rtl-mode .ln-nav-actions,
    body.rtl-mode .card-footer-actions,
    body.rtl-mode .survey-progress-summary {
      flex-direction: row !important;
    }

    body.rtl-mode .search-box {
      direction: rtl !important;
    }

    body.rtl-mode .search-input {
      text-align: right !important;
      padding-right: 40px !important;
      padding-left: 14px !important;
    }

    body.rtl-mode .search-icon {
      right: 14px !important;
      left: auto !important;
    }

    body.rtl-mode .poll-option-content {
      flex-direction: row !important;
    }

    body.rtl-mode .poll-option-marker {
      margin-left: 10px !important;
      margin-right: 0 !important;
    }

    body.rtl-mode .poll-legend-dot {
      margin-left: 8px !important;
      margin-right: 0 !important;
    }

    body.rtl-mode .poll-feed-header {
      flex-direction: row !important;
    }

    body.rtl-mode .publisher-badge {
      flex-direction: row !important;
    }

    body.rtl-mode .publisher-avatar {
      margin-left: 12px !important;
      margin-right: 0 !important;
    }

    body.rtl-mode .modal-card,
    body.rtl-mode .survey-modal-card {
      text-align: right !important;
      direction: rtl !important;
    }

    body.rtl-mode input,
    body.rtl-mode select,
    body.rtl-mode textarea {
      text-align: right !important;
      direction: rtl !important;
    }

    /* Language Switcher Styling */
    .lang-switch-btn {
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      gap: 6px !important;
      padding: 6px 14px !important;
      border-radius: 100px !important;
      background: rgba(229, 229, 229, 0.12) !important;
      border: 1.5px solid rgba(229, 229, 229, 0.3) !important;
      color: inherit !important;
      font-family: inherit !important;
      font-size: 13px !important;
      font-weight: 700 !important;
      cursor: pointer !important;
      text-decoration: none !important;
      transition: all 0.2s ease !important;
      white-space: nowrap !important;
      user-select: none !important;
      flex-shrink: 0 !important;
      z-index: 1005 !important;
    }
    .lang-switch-btn:hover {
      background: rgba(229, 229, 229, 0.24) !important;
      border-color: rgba(229, 229, 229, 0.5) !important;
      transform: translateY(-1px) !important;
    }
    .ln-nav-mobile-lang-btn {
      display: none;
    }
    @media (max-width: 768px) {
      .ln-nav .lang-switch-btn {
        margin-left: auto !important;
        margin-right: 8px !important;
      }
      body.rtl-mode .ln-nav .lang-switch-btn,
      html[dir="rtl"] .ln-nav .lang-switch-btn {
        margin-left: 8px !important;
        margin-right: auto !important;
      }
      .lang-switch-btn {
        padding: 5px 10px !important;
        font-size: 11.5px !important;
        display: inline-flex !important;
      }
      .ln-nav-mobile-lang-btn {
        display: block !important;
        font-weight: 800 !important;
        text-align: center !important;
        padding: 11px 18px !important;
        margin-top: 10px !important;
        border-radius: 100px !important;
        border: 1.5px solid rgba(229, 229, 229, 0.35) !important;
        background: rgba(229, 229, 229, 0.08) !important;
        color: inherit !important;
        font-size: 14px !important;
        text-decoration: none !important;
        cursor: pointer !important;
      }
    }
  `;

  const I18n = {
    translations,
    currentLang: localStorage.getItem('icapsq_lang') || 'en',

    t(key) {
      const dict = this.translations[this.currentLang] || this.translations.en;
      return dict[key] || this.translations.en[key] || key;
    },

    isRTL() {
      return this.currentLang === 'he';
    },

    setLanguage(lang, persist = true) {
      if (!this.translations[lang]) lang = 'en';
      this.currentLang = lang;
      if (persist) {
        localStorage.setItem('icapsq_lang', lang);
      }

      const isHebrew = (lang === 'he');
      document.documentElement.lang = isHebrew ? 'he' : 'en';
      document.documentElement.dir = isHebrew ? 'rtl' : 'ltr';

      if (document.body) {
        document.body.classList.toggle('rtl-mode', isHebrew);
      }

      this.injectStyles();
      this.applyTranslations();
      this.updateSwitcherButtons();

      // Dispatch event for page-specific dynamic components (charts, feeds)
      window.dispatchEvent(new CustomEvent('icapsq:languageChanged', { detail: { lang, isRTL: isHebrew } }));
    },

    toggleLanguage() {
      const next = this.currentLang === 'he' ? 'en' : 'he';
      this.setLanguage(next, true);
    },

    injectStyles() {
      let styleEl = document.getElementById('icapsq-i18n-styles');
      if (!styleEl) {
        styleEl = document.createElement('style');
        styleEl.id = 'icapsq-i18n-styles';
        styleEl.textContent = RTL_CSS;
        document.head.appendChild(styleEl);
      }
    },

    updateSwitcherButtons() {
      const isHe = this.currentLang === 'he';
      const label = isHe ? 'EN | English' : 'HE | עברית';
      const title = isHe ? 'Switch to English' : 'Switch to Hebrew';

      document.querySelectorAll('.lang-switch-btn, .ln-nav-mobile-lang-btn, [data-lang-switch]').forEach(btn => {
        btn.textContent = label;
        btn.setAttribute('title', title);
        btn.setAttribute('aria-label', title);
      });
    },

    ensureSwitcherInNav() {
      const nav = document.querySelector('.ln-nav');
      const navToggle = document.getElementById('navToggle') || document.querySelector('.ln-nav-toggle');
      const navLinks = document.getElementById('navLinks') || document.querySelector('.ln-nav-links');
      const navRight = document.querySelector('.ln-nav-right');
      const navActions = document.querySelector('.ln-nav-actions');

      // 1. Landing pages with hamburger navToggle
      if (nav && navToggle) {
        if (!nav.querySelector('.lang-switch-btn')) {
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'lang-switch-btn';
          btn.onclick = () => I18n.toggleLanguage();
          if (navActions) {
            nav.insertBefore(btn, navActions);
          } else {
            nav.insertBefore(btn, navToggle);
          }
        }

        // Also add inside mobile drawer menu (.ln-nav-links)
        if (navLinks && !navLinks.querySelector('.ln-nav-mobile-lang-btn')) {
          const mobBtn = document.createElement('a');
          mobBtn.href = 'javascript:void(0)';
          mobBtn.className = 'ln-mobile-only ln-nav-mobile-lang-btn';
          mobBtn.onclick = (e) => {
            e.preventDefault();
            I18n.toggleLanguage();
          };
          navLinks.appendChild(mobBtn);
        }
      } else if (navRight) {
        // 2. vote.html / surveys.html with .ln-nav-right
        if (!navRight.querySelector('.lang-switch-btn')) {
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'lang-switch-btn';
          btn.onclick = () => I18n.toggleLanguage();
          const signin = navRight.querySelector('.ln-nav-signin');
          if (signin) {
            navRight.insertBefore(btn, signin);
          } else {
            navRight.appendChild(btn);
          }
        }
      } else if (navActions) {
        // 3. Any other pages with .ln-nav-actions
        if (!document.querySelector('.lang-switch-btn')) {
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'lang-switch-btn';
          btn.onclick = () => I18n.toggleLanguage();
          navActions.insertBefore(btn, navActions.firstChild);
        }
      } else {
        // 4. Auth pages or standalone pages without top nav
        const authContainer = document.querySelector('.auth-container');
        if (authContainer && !authContainer.querySelector('.lang-switch-btn')) {
          const wrapper = document.createElement('div');
          wrapper.className = 'auth-lang-wrap';
          wrapper.style.cssText = 'display:flex; justify-content:flex-end; margin-bottom:14px;';
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'lang-switch-btn';
          btn.onclick = () => I18n.toggleLanguage();
          wrapper.appendChild(btn);
          authContainer.insertBefore(wrapper, authContainer.firstChild);
        }
      }

      this.updateSwitcherButtons();
    },

    translatePoll(poll) {
      if (!poll) return poll;
      if (this.currentLang === 'he' && pollOverrides[poll.id] && pollOverrides[poll.id].he) {
        const ov = pollOverrides[poll.id].he;
        return {
          ...poll,
          title: ov.title || poll.title,
          description: ov.description || poll.description,
          category: ov.category || poll.category,
          options: (poll.options || []).map((opt, i) => ({
            ...opt,
            label: (ov.options && ov.options[i]) || opt.label,
            text: (ov.options && ov.options[i]) || opt.text || opt.label
          }))
        };
      }
      return poll;
    },

    translateSurvey(survey) {
      if (!survey) return survey;
      if (this.currentLang === 'he') {
        const sId = (survey.id || '').toUpperCase();
        const sCode = (survey.code || '').toUpperCase();
        const sTitle = (survey.title || '');
        if (sId.includes('KENYA') || sCode.includes('KENYA') || sTitle.includes('Kenya National Healthcare')) {
          return {
            ...survey,
            title: 'מדד שירותי בריאות ורפואה ציבורית 2026',
            description: 'הערכה לאומית מאומתת האוספת משוב ישיר מאזרחים על זמני המתנה במרפאות, זמינות תרופות חיוניות ומימון שירותי רפואה.',
            category: 'בריאות ושירותים ציבוריים',
            organization: 'מכון מחקר ומודיעין ציבורי IcapsQ'
          };
        }
        if (surveyOverrides[survey.id] && surveyOverrides[survey.id].he) {
          const ov = surveyOverrides[survey.id].he;
          return {
            ...survey,
            title: ov.title || survey.title,
            description: ov.description || survey.description,
            category: ov.category || survey.category
          };
        }
      }
      return survey;
    },

    applyTranslations() {
      // Text replacements via data-i18n
      document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const val = this.t(key);
        if (val) {
          if (el.tagName === 'INPUT' && (el.type === 'text' || el.type === 'search')) {
            el.placeholder = val;
          } else {
            el.innerHTML = val;
          }
        }
      });

      // Placeholders
      document.querySelectorAll('[data-i18n-ph]').forEach(el => {
        const key = el.getAttribute('data-i18n-ph');
        const val = this.t(key);
        if (val) el.placeholder = val;
      });

      // Titles
      document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        const val = this.t(key);
        if (val) el.title = val;
      });

      // Auto-translate common static patterns if data-i18n isn't placed yet
      this.applyKnownPatterns();
    },

    applyKnownPatterns() {
      const isHe = (this.currentLang === 'he');

      // 1. Navigation links
      const navLinks = document.querySelectorAll('.ln-nav-links a, .site-header a');
      navLinks.forEach(link => {
        const text = link.textContent.trim();
        if (text === 'Active Polls' || text === 'סקרים פעילים') {
          link.textContent = isHe ? 'סקרים פעילים' : 'Active Polls';
        } else if (text === 'Active Surveys' || text === 'שאלונים פעילים') {
          link.textContent = isHe ? 'שאלונים פעילים' : 'Active Surveys';
        } else if (text === 'Features' || text === 'תכונות') {
          link.textContent = isHe ? 'תכונות' : 'Features';
        } else if (text === 'Pricing' || text === 'תמחור') {
          link.textContent = isHe ? 'תמחור' : 'Pricing';
        } else if (text === 'How It Works' || text === 'איך זה עובד') {
          link.textContent = isHe ? 'איך זה עובד' : 'How It Works';
        } else if (text === 'Contact' || text === 'צור קשר') {
          link.textContent = isHe ? 'צור קשר' : 'Contact';
        } else if (text === 'Blog' || text === 'בלוג') {
          link.textContent = isHe ? 'בלוג' : 'Blog';
        } else if (text === 'Sign In' || text === 'התחברות') {
          link.textContent = isHe ? 'התחברות' : 'Sign In';
        }
      });

      // Sign In buttons (desktop, mobile & nav-actions)
      document.querySelectorAll('.ln-nav-signin, .ln-mobile-only').forEach(el => {
        const t = el.textContent.trim();
        if (t === 'Sign In' || t === 'כניסת ארגונים' || t === 'התחברות') {
          el.textContent = isHe ? 'כניסת ארגונים' : 'Sign In';
        }
      });
      const signinDesktop = document.querySelector('.signin-text-desktop');
      if (signinDesktop) {
        signinDesktop.textContent = isHe ? 'כניסת ארגונים' : 'Organization Sign In';
      }
      const signinMobile = document.querySelector('.signin-text-mobile');
      if (signinMobile) {
        signinMobile.textContent = isHe ? 'כניסת ארגון' : 'Org Sign In';
      }

      // Get Started CTA in Navigation
      document.querySelectorAll('.ln-nav-cta').forEach(el => {
        el.innerHTML = isHe ? '<- התחל עכשיו' : 'Get Started <span>&rarr;</span>';
      });

      // Filter pills on vote.html
      const pollFilters = document.querySelectorAll('#poll-filters-bar button');
      pollFilters.forEach(btn => {
        const plan = btn.getAttribute('data-plan');
        if (plan === 'all') btn.textContent = isHe ? 'כל הסקרים הפעילים' : 'All Active Polls';
        if (plan === 'free') btn.textContent = isHe ? 'שטח וקהילה' : 'Community Grassroots';
        if (plan === 'pro') btn.textContent = isHe ? 'מחקר ותעשייה' : 'Research & Industry';
        if (plan === 'org') btn.textContent = isHe ? 'איגודים מוסדיים ועמותות' : 'Institutional Unions & NGOs';
        if (plan === 'election') btn.textContent = isHe ? 'אספות אזרחיות' : 'Civic Assemblies';
      });

      // Filter pills on surveys.html
      const surveyFilters = document.querySelectorAll('#audience-filters-bar button, .plan-filter-btn[data-category]');
      surveyFilters.forEach(btn => {
        const cat = btn.getAttribute('data-category');
        if (cat === 'all') btn.textContent = isHe ? 'כל הקהלים' : 'All Audiences';
        if (cat === 'public') btn.textContent = isHe ? 'ציבור רחב' : 'Public Citizens';
        if (cat === 'enterprise') btn.textContent = isHe ? 'ארגונים ותעשייה' : 'Enterprise & Industry';
        if (cat === 'students') btn.textContent = isHe ? 'אקדמיה וסטודנטים' : 'Universities & Students';
        if (cat === 'healthcare') btn.textContent = isHe ? 'בריאות ואיכות חיים' : 'Health & Well-being';
      });

      // Search Inputs
      const searchInputs = document.querySelectorAll('#poll-filter-input, #survey-search-input');
      searchInputs.forEach(input => {
        if (input.id === 'poll-filter-input') {
          input.placeholder = isHe ? 'חיפוש סקרים פעילים...' : 'Search active polls...';
        } else {
          input.placeholder = isHe ? 'חיפוש שאלונים...' : 'Search surveys...';
        }
      });

      // Landing page hero
      const heroHeadline = document.querySelector('.ln-hero-headline');
      if (heroHeadline) heroHeadline.innerHTML = isHe ? 'לשמוע <em>כל</em> קול.' : 'Capture <em>every</em> voice.';
      const heroSub = document.querySelector('.ln-hero-sub');
      if (heroSub) heroSub.textContent = isHe
        ? 'פלטפורמת הסקרים והמשוב המאפשרת לארגונים לפרסם שאלונים ממוקדים, לשתף אזרחים בהצבעה סלולרית ולקבל ניתוח נתונים בזמן אמת.'
        : 'The polling platform that empowers organizations to publish targeted surveys and engage citizens through mobile voting — with live analytics.';

      // Landing hero action buttons
      const heroActions = document.querySelectorAll('.ln-hero-actions a');
      heroActions.forEach(a => {
        const t = a.textContent.trim();
        if (t === 'Vote in Live Polls' || t === 'הצבע בסקרים חיים') a.textContent = isHe ? 'הצבע בסקרים חיים' : 'Vote in Live Polls';
        if (t.includes('Download') || t.includes('הורד')) a.textContent = isHe ? 'הורד את IcapsQ ל-Android' : 'Download IcapsQ APK';
        if (t.includes('Console') || t.includes('לוח בקרה')) a.textContent = isHe ? 'לוח בקרה לארגונים' : 'Organization Console';
      });

      // Trusted-by labels (no duplicate text)
      const trustedLabel = document.querySelector('.ln-trusted-label');
      if (trustedLabel) trustedLabel.textContent = isHe ? 'מהימן על ידי:' : 'Trusted by:';
      const trustedLogos = document.querySelectorAll('.ln-trusted-logo');
      const trustMap = [
        { en: 'County Governments', he: 'רשויות מקומיות וממשל' },
        { en: 'Research Institutes', he: 'מכוני מחקר' },
        { en: 'NGOs', he: 'עמותות וארגונים' },
        { en: 'Civic Organizations', he: 'ארגונים אזרחיים' },
        { en: 'Universities', he: 'אוניברסיטאות' },
        { en: 'Election Bodies', he: 'ועדות בחירות' }
      ];
      trustedLogos.forEach((el, i) => {
        if (!trustMap[i]) return;
        const shape = el.querySelector('.ln-trusted-logo-shape');
        el.innerHTML = '';
        if (shape) el.appendChild(shape);
        el.appendChild(document.createTextNode(' ' + (isHe ? trustMap[i].he : trustMap[i].en)));
      });

      // Landing features section
      const featTag = document.querySelector('.ln-features .ln-section-tag');
      if (featTag) featTag.textContent = isHe ? 'תכונות עיקריות' : 'Features';
      const featHead = document.querySelector('.ln-features .ln-section-headline');
      if (featHead) featHead.textContent = isHe ? 'פתרנו את הפער באיסוף המשוב.' : "We've solved the feedback gap.";
      const featDescMain = document.querySelector('.ln-features-inner > div.reveal > p.ln-section-desc');
      if (featDescMain) {
        featDescMain.innerHTML = isHe
          ? 'פלטפורמת Icaps<span class="brand-q">Q</span> מעניקה לארגונים נתוני השתתפות אמיתיים, ללא רעשי רקע. פרסום, שיתוף וניתוח — הכל במקום אחד.'
          : 'Icaps<span class="brand-q">Q</span> gives organizations real participation data, without the noise. Publish, engage, analyze — all in one platform.';
      }
      const featTitles = document.querySelectorAll('.ln-feature-title');
      const featDescs = document.querySelectorAll('.ln-feature-desc');
      const featureMap = [
        { en: 'Targeted Polling', he: 'סקרים ממוקדים', de: 'Filter by county, audience, or topic to reach the people your research is meant for.', dh: 'סינון לפי מחוז, קהל יעד או נושא כדי להגיע בדיוק לאנשים שהמחקר מיועד עבורם.' },
        { en: 'Live Analytics', he: 'ניתוח נתונים בזמן אמת', de: 'Follow votes and survey responses as they arrive. Compare totals and turnout at a glance.', dh: 'עקוב אחר הקולות ותגובות השאלונים בזמן אמת. השווה תוצאות ואחוזי השתתפות במבט אחד.' },
        { en: 'Mobile-First Voting', he: 'הצבעה מובייל', de: 'Let participants respond on the web or Android app through one clear, consistent flow.', dh: 'אפשר למשתתפים להשיב באתר או באפליקציית Android בתהליך ברור ועקבי.' },
        { en: 'Export & Report', he: 'ייצוא ודוחות', de: 'Export responses as PDF or CSV for review, reporting, and sharing with your team.', dh: 'ייצוא תגובות כ-PDF או CSV לבדיקה, דיווח ושיתוף עם הצוות שלך.' }
      ];
      featTitles.forEach((el, i) => {
        if (featureMap[i]) el.textContent = isHe ? featureMap[i].he : featureMap[i].en;
      });
      featDescs.forEach((el, i) => {
        if (featureMap[i]) el.textContent = isHe ? featureMap[i].dh : featureMap[i].de;
      });

      // See the Big Picture (How-it-works)
      const bpHeadline = document.querySelector('.ln-bigpicture-headline');
      if (bpHeadline) bpHeadline.textContent = isHe ? 'לראות את התמונה המלאה' : 'See the Big Picture';
      const bpDesc = document.querySelector('.ln-bigpicture-desc');
      if (bpDesc) {
        bpDesc.innerHTML = isHe
          ? 'פלטפורמת Icaps<span class="brand-q">Q</span> הופכת נתוני השתתפות גולמיים לתובנות חזותיות ברורות המציגות בדיוק את המתרחש בכל מחוז ופילוח דמוגרפי.'
          : 'Icaps<span class="brand-q">Q</span> turns raw participation into clear, actionable visuals that show you exactly what\'s happening across every county and demographic.';
      }
      const bpSteps = document.querySelectorAll('.ln-step-text');
      const stepMap = [
        { en: '<strong>Author in Seconds:</strong> No more messy spreadsheets or paper forms.', he: '<strong>יצירה בשניות:</strong> ללא גיליונות עבודה מסובכים או טפסים מנייר.' },
        { en: '<strong>Reach Every Citizen:</strong> Push polls directly to mobile app users across all 47 counties.', he: '<strong>הגעה לכל אזרח:</strong> שליחת סקרים ישירות למשתמשי האפליקציה בכלל המחוזות.' },
        { en: '<strong>Real-Time Dashboards:</strong> Interactive charts and maps keep your stakeholders engaged.', he: '<strong>לוחות מחוונים בזמן אמת:</strong> תרשימים ומפות אינטראקטיביות לשיתוף בעלי עניין.' },
        { en: '<strong>Your Organization Snapshot:</strong> Get a quick, clear overview of every active poll and survey.', he: '<strong>תמונת מצב ארגונית:</strong> סקירה מהירה וברורה של כל סקר ושאלון פעיל.' }
      ];
      bpSteps.forEach((el, i) => {
        if (stepMap[i]) el.innerHTML = isHe ? stepMap[i].he : stepMap[i].en;
      });
      document.querySelectorAll('.ln-btn-outline').forEach(el => {
        el.innerHTML = isHe ? '<- גלה עוד' : 'Discover More <span>&rarr;</span>';
      });

      // Specs & Comparison Section
      const compTag = document.querySelector('.ln-compare .ln-section-tag');
      if (compTag) compTag.textContent = isHe ? 'מפרט' : 'Specs';
      const compHead = document.querySelector('.ln-compare-headline');
      if (compHead) compHead.innerHTML = isHe ? 'למה לבחור ב-Icaps<span class="brand-q">Q</span>?' : 'Why Choose Icaps<span class="brand-q">Q</span>?';
      const compDesc = document.querySelector('.ln-compare-desc');
      if (compDesc) {
        compDesc.innerHTML = isHe
          ? 'אתה זקוק לפתרון שעומד בקצב. בדיוק לשם כך פיתחנו את Icaps<span class="brand-q">Q</span> — גישה ייעודית לייעול איסוף המשוב של הארגון שלך.'
          : 'You need a solution that keeps up. That\'s why we developed Icaps<span class="brand-q">Q</span>. A purpose-built approach to streamline your organization\'s feedback collection.';
      }
      document.querySelectorAll('.ln-compare-cta').forEach(el => {
        el.innerHTML = isHe ? '<- גלה עוד' : 'Discover More <span>&rarr;</span>';
      });
      const tableThs = document.querySelectorAll('.ln-compare-table th');
      if (tableThs.length >= 4) {
        if (tableThs[2]) tableThs[2].textContent = isHe ? 'סקרים מסורתיים' : 'Traditional Surveys';
        if (tableThs[3]) tableThs[3].textContent = isHe ? 'טפסי נייר' : 'Paper Ballots';
      }
      const tableCells = document.querySelectorAll('.ln-compare-table td span');
      const cellTranslations = {
        'Real-time results': 'תוצאות בזמן אמת',
        'Instant live dashboards': 'לוחות בקרה חיים מיידיים',
        'Delayed processing': 'עיבוד מושהה',
        'Manual counting': 'ספירה ידנית',
        'Mobile voting': 'הצבעה סלולרית',
        'Dedicated Android app': 'אפליקציית Android ייעודית',
        'No mobile support': 'ללא תמיכה בסלולר',
        'Physical only': 'פיזי בלבד',
        'County-level targeting': 'מיקוד אזורי ומחוזי',
        'All 47 counties': 'כלל המחוזות והאזורים',
        'Limited reach': 'תפוצה מוגבלת',
        'Location-bound': 'מוגבל למיקום',
        'Duplicate vote protection': 'הגנה מכפילויות הצבעה',
        'Device-level verification': 'אימות ברמת המכשיר',
        'Basic checks': 'בדיקות בסיסיות',
        'No protection': 'ללא הגנה',
        'Live analytics dashboards': 'לוחות ניתוח בזמן אמת',
        'Charts, maps, trends': 'תרשימים, מפות, מגמות',
        'No dashboards': 'ללא לוחות בקרה',
        'PDF & CSV exports': 'ייצוא ל-PDF ו-CSV',
        'One-click export': 'ייצוא בלחיצה אחת',
        'Manual export': 'ייצוא ידני',
        'No digital records': 'ללא רשומות דיגיטליות',
        'Multi-language support': 'תמיכה בריבוי שפות',
        'English & Kiswahili': 'עברית ואנגלית',
        'Varies': 'משתנה',
        'Print-dependent': 'תלוי הדפסה'
      };
      const cellTranslationsRev = {};
      Object.entries(cellTranslations).forEach(([k, v]) => { cellTranslationsRev[v] = k; });
      tableCells.forEach(span => {
        const t = span.textContent.trim();
        if (isHe && cellTranslations[t]) {
          span.textContent = cellTranslations[t];
        } else if (!isHe && cellTranslationsRev[t]) {
          span.textContent = cellTranslationsRev[t];
        }
      });

      // Plans & Pricing Section
      const plansTag = document.querySelector('.ln-plans .ln-section-tag');
      if (plansTag) plansTag.textContent = isHe ? 'מסלולים ותמחור' : 'Plans & Pricing';
      const plansHead = document.querySelector('.ln-plans-headline');
      if (plansHead) plansHead.textContent = isHe ? 'בחר את המסלול המתאים לעבודתך.' : 'Choose the plan that fits your work.';
      const plansDesc = document.querySelector('.ln-plans-desc');
      if (plansDesc) {
        plansDesc.textContent = isHe
          ? 'אותם כלי ליבה בכל מסלול, עם מגבלות פרסום ויעדי משתתפים שמתרחבים ככל שאתה צומח.'
          : 'The same core tools on every plan, with a poll publishing limit and participant target per poll that scale as you grow.';
      }
      const planCards = document.querySelectorAll('.ln-plan-card');
      planCards.forEach(card => {
        const nameEl = card.querySelector('.ln-plan-name');
        const audEl = card.querySelector('.ln-plan-audience');
        const priceEl = card.querySelector('.ln-plan-price');
        const periodEl = card.querySelector('.ln-plan-period');
        const ribbonEl = card.querySelector('.ln-plan-ribbon');
        const ctaEl = card.querySelector('.ln-plan-cta');

        if (ribbonEl) ribbonEl.textContent = isHe ? 'הפופולרי ביותר' : 'Most popular';

        if (nameEl) {
          const n = nameEl.textContent.trim();
          if (n === 'Starter' || n === 'בסיסי (Starter)') {
            nameEl.textContent = isHe ? 'בסיסי (Starter)' : 'Starter';
            if (audEl) audEl.textContent = isHe ? 'לקבוצות קטנות שמתחילות עכשיו' : 'For small groups getting started';
            if (priceEl) priceEl.textContent = isHe ? 'חינם' : 'Free';
            if (periodEl) periodEl.textContent = isHe ? 'ללא צורך בכרטיס אשראי' : 'No card required';
            if (ctaEl) ctaEl.textContent = isHe ? 'התחל בחינם' : 'Get started free';
          } else if (n === 'Pro' || n === 'מקצועי (Pro)') {
            nameEl.textContent = isHe ? 'מקצועי (Pro)' : 'Pro';
            if (audEl) audEl.textContent = isHe ? 'לחוקרים ולאנשי מקצוע' : 'For researchers and professionals';
            if (priceEl) priceEl.textContent = isHe ? '₪15' : 'KES 499';
            if (periodEl) periodEl.textContent = isHe ? '/ 30 יום' : '/ 30 days';
            if (ctaEl) ctaEl.textContent = isHe ? 'בחר Pro' : 'Choose Pro';
          } else if (n === 'Organization' || n === 'ארגוני (Organization)') {
            nameEl.textContent = isHe ? 'ארגוני (Organization)' : 'Organization';
            if (audEl) audEl.textContent = isHe ? 'לצוותים המנהלים קמפיינים מרובים' : 'For teams managing multiple campaigns';
            if (priceEl) priceEl.textContent = isHe ? '₪29' : 'KES 899';
            if (periodEl) periodEl.textContent = isHe ? '/ 30 יום' : '/ 30 days';
            if (ctaEl) ctaEl.textContent = isHe ? 'בחר ארגוני' : 'Choose Organization';
          }
        }

        const lis = card.querySelectorAll('.ln-plan-features li');
        lis.forEach(li => {
          const text = li.textContent.trim();
          if (text.includes('polls') || text.includes('סקרים')) {
            const num = li.querySelector('span')?.textContent || '';
            li.innerHTML = isHe ? `עד <span data-plan-polls>${num}</span> סקרים` : `Up to <span data-plan-polls>${num}</span> polls`;
          } else if (text.includes('Participant target') || text.includes('יעד משתתפים')) {
            const num = li.querySelector('span')?.textContent || '';
            li.innerHTML = isHe ? `יעד משתתפים לסקר: <span data-plan-voters>${num}</span>` : `Participant target per poll: <span data-plan-voters>${num}</span>`;
          } else if (text.includes('Poll and survey') || text.includes('כלי סקרים')) {
            li.textContent = isHe ? 'כלי סקרים ושאלונים' : 'Poll and survey tools';
          } else if (text.includes('Shareable links') || text.includes('קישורים ותוצאות')) {
            li.textContent = isHe ? 'קישורים ותוצאות הניתנים לשיתוף' : 'Shareable links and results';
          }
        });
      });
      const planFootnote = document.getElementById('plan-price-note');
      if (planFootnote) {
        planFootnote.textContent = isHe
          ? 'מסלולי Pro ו-Organization משולמים מראש ל-30 יום ומתחדשים ידנית. כל המסלולים כוללים את אותם הכלים.'
          : 'Pro and Organization are prepaid for 30 days and renew manually. All plans include the same core tools.';
      }

      // Explicit Currency Overrides - Strictly NO KES in Hebrew
      document.querySelectorAll('[data-plan-price="pro"], #signup-price-pro, #price-val-pro').forEach(el => {
        el.textContent = isHe ? '₪15' : 'KES 499';
      });
      document.querySelectorAll('[data-plan-price="org"], #signup-price-org, #price-val-org').forEach(el => {
        el.textContent = isHe ? '₪29' : 'KES 899';
      });
      document.querySelectorAll('[data-plan-price="free"]').forEach(el => {
        el.textContent = isHe ? 'חינם' : 'Free';
      });

      // Discover / Unbeatable Section
      const discTag = document.querySelector('.ln-discover .ln-section-tag');
      if (discTag) discTag.textContent = isHe ? 'למה אנחנו ללא תחרות' : 'Why We Are Unbeatable';
      const discHead = document.querySelector('.ln-discover-headline');
      if (discHead) discHead.textContent = isHe ? 'נבנה לאמינות מוחלטת, מהירות חסרת תקדים והכלה מלאה.' : 'Built for Absolute Trust, Unmatched Speed & Total Inclusion.';
      const discDesc = document.querySelector('.ln-discover-desc');
      if (discDesc) {
        discDesc.innerHTML = isHe
          ? 'בין אם אתה מנהיג קהילה מקומי המנהל סקר שכונתי, אוניברסיטה המארגנת בחירות סטודנטים, איגוד עובדים או גוף פיקוח — <strong>Icaps<span class="brand-q">Q</span></strong> מעניקה לך הוכחה קריפטוגרפית, ניתוח בזמן אמת והגנה מפני זיופים ששום פלטפורמה מסורתית אינה יכולה להציע.'
          : 'Whether you are a local community leader running a neighborhood poll, a university organizing student elections, a national union surveying thousands of educators, or a sovereign election observer — <strong>Icaps<span class="brand-q">Q</span></strong> gives you cryptographic proof, real-time analytics, and fraud protection that no traditional platform can match.';
      }
      const discCards = document.querySelectorAll('.ln-discover-card');
      const discMap = [
        {
          enT: 'Cryptographic Merkle Proofs',
          heT: 'הוכחות מרקל קריפטוגרפיות',
          enD: 'Every single vote generates an immutable SHA-256 receipt stored on a tamper-proof ledger. Voters can independently verify their ballot without revealing identity.',
          heD: 'כל קול מייצר קבלה מוצפנת ב-SHA-256 שנרשמת ברישום מוגן מזיופים. המצביעים יכולים לאמת את פתק ההצבעה באופן עצמאי מבלי לחשוף את זהותם.'
        },
        {
          enT: 'IP & Location Anti-Fraud Engine',
          heT: 'מנוע למניעת הונאות מיקום ו-IP',
          enD: 'Real-time GPS validation, IP location tracking, and device hardware fingerprinting automatically block duplicate votes, bot attacks, and spoofing attempts.',
          heD: 'אימות GPS בזמן אמת, מעקב מיקום IP וטביעת אצבע של חומרת המכשיר חוסמים אוטומטית הצבעות כפולות, מתקפות בוטים וניסיונות זיוף.'
        },
        {
          enT: 'Accessible to Every Citizen',
          heT: 'נגיש לכל אזרח',
          enD: 'Seamless Flutter Mobile App (iOS/Android), Mobile Web, and SMS/Offline polling fallback ensure voters in remote rural regions or cities participate equally.',
          heD: 'אפליקציה סלולרית חלקה, אתר מותאם וגיבוי במצב לא מקוון מבטיחים שכל המשתתפים בכל אזור ייקחו חלק שווה.'
        },
        {
          enT: 'Vivid Live Analytics & Reports',
          heT: 'ניתוחים ודוחות חיים מרהיבים',
          enD: 'Watch live pie charts, bar breakdowns, and demographic maps update instantly as votes roll in. Export official signed PDF/CSV reports in one click.',
          heD: 'צפה בתרשימי עוגה, עמודות ומפות דמוגרפיות המתעדכנים מיידית עם כניסת הקולות. ייצוא דוחות רשמיים ב-PDF/CSV בלחיצה אחת.'
        }
      ];
      discCards.forEach((c, i) => {
        if (discMap[i]) {
          const tEl = c.querySelector('.ln-discover-card-title');
          const dEl = c.querySelector('.ln-discover-card-desc');
          if (tEl) tEl.textContent = isHe ? discMap[i].heT : discMap[i].enT;
          if (dEl) dEl.textContent = isHe ? discMap[i].heD : discMap[i].enD;
        }
      });
      const discCtaTitle = document.querySelector('.ln-discover-cta-title');
      if (discCtaTitle) discCtaTitle.textContent = isHe ? 'מוכנים לשדרג את קבלת ההחלטות בארגון?' : 'Ready to elevate your organization\'s decision-making?';
      const discCtaSub = document.querySelector('.ln-discover-cta-sub');
      if (discCtaSub) discCtaSub.textContent = isHe ? 'התחל בחינם עוד היום — ללא כרטיס אשראי. שדרג בכל עת ככל שהקהל גדל.' : 'Start for free today — no credit card required. Upgrade anytime as your audience grows.';
      document.querySelectorAll('.ln-discover-cta-bar .ln-btn-primary').forEach(el => {
        el.innerHTML = isHe ? '<- פתח חשבון עכשיו' : 'Create Account Now <span>&rarr;</span>';
      });

      // CTA / Contact Section
      const ctaHead = document.querySelector('.ln-cta-headline');
      if (ctaHead) ctaHead.textContent = isHe ? 'מוכנים לשמוע כל קול?' : 'Ready to capture every voice?';
      const ctaDesc = document.querySelector('.ln-cta-desc');
      if (ctaDesc) {
        ctaDesc.innerHTML = isHe
          ? 'הצטרף לארגונים שכבר משתמשים ב-Icaps<span class="brand-q">Q</span> כדי לפרסם סקרים, לשתף אזרחים ולקבל החלטות מבוססות נתונים.'
          : 'Join organizations across Kenya already using Icaps<span class="brand-q">Q</span> to publish polls, engage citizens, and make data-driven decisions.';
      }
      document.querySelectorAll('.ln-cta-buttons .ln-btn-primary').forEach(el => {
        el.innerHTML = isHe ? '<- התחל עכשיו' : 'Get Started <span>&rarr;</span>';
      });
      document.querySelectorAll('.ln-cta-buttons .ln-btn-secondary').forEach(el => {
        const t = el.textContent.trim();
        if (t.includes('Why') || t.includes('למה')) {
          el.textContent = isHe ? 'למה IcapsQ?' : 'Why IcapsQ?';
        } else if (t.includes('Mobile') || t.includes('אפליקציה')) {
          el.textContent = isHe ? 'הורד אפליקציה' : 'Get the Mobile App';
        }
      });

      // Auth / Login Page (login.html)
      const authBrandSub = document.querySelector('.auth-brand-sub');
      if (authBrandSub) {
        authBrandSub.textContent = isHe ? 'פורטל ניהול סקרים ומשוב' : 'Survey & Feedback Management Portal';
      }
      const authCardH2 = document.querySelector('.auth-card h2');
      if (authCardH2) {
        authCardH2.textContent = isHe ? 'כניסת ארגונים' : 'Sign In';
      }
      const authCardSub = document.querySelector('.auth-card .subtitle');
      if (authCardSub) {
        authCardSub.textContent = isHe ? 'גישה ללוח הבקרה וניתוח הנתונים של הארגון.' : 'Access your organization dashboard and polling analytics.';
      }
      const emailLabels = document.querySelectorAll('.form-group .form-label');
      emailLabels.forEach(lbl => {
        const txt = lbl.textContent.trim();
        if (txt === 'Email Address' || txt === 'כתובת דואר אלקטרוני') {
          lbl.textContent = isHe ? 'כתובת דואר אלקטרוני' : 'Email Address';
        } else if (txt === 'Password' || txt === 'סיסמה') {
          lbl.textContent = isHe ? 'סיסמה' : 'Password';
        }
      });
      const loginBtn = document.getElementById('login-btn');
      if (loginBtn && !loginBtn.disabled) {
        loginBtn.innerHTML = isHe ? '<- התחבר' : 'Sign In &rarr;';
      }
      const forgotLink = document.querySelector('.forgot-link');
      if (forgotLink) {
        forgotLink.textContent = isHe ? 'שכחת סיסמה?' : 'Forgot password?';
      }
      const authFooter = document.querySelector('.auth-footer');
      if (authFooter) {
        const createLink = authFooter.querySelector('a[href*="signup"]');
        if (createLink) {
          createLink.innerHTML = isHe ? '<- פתיחת חשבון' : 'Create Account &rarr;';
        }
        for (const node of authFooter.childNodes) {
          if (node.nodeType === 3 && (node.nodeValue.includes("Don't have") || node.nodeValue.includes("אין לך"))) {
            node.nodeValue = isHe ? ' אין לך חשבון עדיין? ' : " Don't have an account? ";
          }
        }
      }

      // Surveys Banner (surveys.html)
      const bannerEyebrow = document.querySelector('.page-banner-row div[style*="uppercase"]');
      if (bannerEyebrow) {
        bannerEyebrow.textContent = isHe ? 'השתתפות ציבורית ומוסדית' : 'Public & Institutional Participation';
      }
      const bannerTitle = document.querySelector('.page-banner-title');
      if (bannerTitle) {
        bannerTitle.textContent = isHe ? 'מחקרים ושאלוני משוב פעילים' : 'Active Surveys & Research Inquiries';
      }
      const bannerDesc = document.querySelector('.page-banner-desc');
      if (bannerDesc) {
        bannerDesc.textContent = isHe
          ? 'שאלוני השתתפות ישירים המפורסמים על ידי מוסדות מאומתים, איגודי עובדים, מועצות בריאות ואספות אזרחיות. שתף את נקודת מבטך והעבר קישורים ישירים לקהילה שלך.'
          : 'Direct participation surveys published by verified institutions, labor unions, healthcare boards, and civic assemblies. Share your experience and pass direct links to your community.';
      }
      const surveySearch = document.getElementById('survey-search-input');
      if (surveySearch) {
        surveySearch.placeholder = isHe ? 'חיפוש לפי נושא או מפרסם...' : 'Search by topic or publisher...';
      }

      // Global Currency Sweeper: Strictly NO KES when Hebrew is active
      if (isHe) {
        document.querySelectorAll('.ln-plan-price, .plan-price-num, #price-val-pro, #price-val-org, [data-plan-price], td, th, .plan-card').forEach(el => {
          if (el.children.length === 0 || el.classList.contains('ln-plan-price') || el.classList.contains('plan-price-num')) {
            const raw = el.textContent;
            if (raw.includes('499') || raw.includes('pro')) {
              el.textContent = '₪15';
            } else if (raw.includes('899') || raw.includes('org')) {
              el.textContent = '₪29';
            } else if (raw.includes('KES') || raw.includes('kes')) {
              el.textContent = raw.replace(/KES\s*/gi, '₪').replace(/\s*KES/gi, '₪');
            }
          }
        });
      }
      // Verification modal labels
      const vTitle = document.querySelector('.voter-modal-title');
      if (vTitle) vTitle.textContent = isHe ? 'אימות פרטי הצבעה אזרחיים' : 'Civic Verification Survey';
      const vDesc = document.querySelector('.voter-modal-desc');
      if (vDesc) {
        vDesc.textContent = isHe
          ? 'כדי להבטיח ייצוג אזורי מהימן ולמנוע כפילות בהצבעה, אנא אמת את פרטיך ואזור מגוריך.'
          : 'To ensure genuine regional representation and prevent ballot duplication, please confirm your verification details and County of residence.';
      }
      const vBtn = document.getElementById('verify-submit-btn');
      if (vBtn && !vBtn.disabled) {
        vBtn.textContent = isHe ? '<- אישור והמשך להצבעה' : 'Confirm & Proceed ->';
      }

      // Footer
      const footerDesc = document.querySelector('.ln-footer-brand-desc');
      if (footerDesc) {
        footerDesc.textContent = isHe
          ? 'מעצימים ארגונים עם ניהול סקרים ומשוב מאומת, ניתוח נתונים בזמן אמת ומעורבות סלולרית מתקדמת בישראל, קניה ובעולם.'
          : 'Empowering organizations with verified sovereign survey and feedback management, real-time analytics, and mobile research engagement across Kenya.';
      }
      const footerColTitles = document.querySelectorAll('.ln-footer-col-title');
      footerColTitles.forEach(el => {
        const t = el.textContent.trim();
        if (t === 'Navigation' || t === 'ניווט') el.textContent = isHe ? 'ניווט' : 'Navigation';
        if (t === 'Organizations' || t === 'לארגונים') el.textContent = isHe ? 'לארגונים' : 'Organizations';
        if (t === 'Sovereignty' || t === 'הורדות ואפליקציה') el.textContent = isHe ? 'הורדות ואפליקציה' : 'Sovereignty';
        if (t === 'Mobile App' || t === 'אפליקציה לנייד') el.textContent = isHe ? 'אפליקציה לנייד' : 'Mobile App';
      });
      const footerLinks = document.querySelectorAll('.ln-footer-links a');
      footerLinks.forEach(link => {
        const t = link.textContent.trim();
        if (t === 'Home' || t === 'דף הבית') link.textContent = isHe ? 'דף הבית' : 'Home';
        if (t === 'Features' || t === 'תכונות') link.textContent = isHe ? 'תכונות' : 'Features';
        if (t === 'Active Polls' || t === 'סקרים פעילים') link.textContent = isHe ? 'סקרים פעילים' : 'Active Polls';
        if (t === 'Active Surveys' || t === 'שאלונים פעילים') link.textContent = isHe ? 'שאלונים פעילים' : 'Active Surveys';
        if (t === 'Blog' || t === 'בלוג') link.textContent = isHe ? 'בלוג' : 'Blog';
        if (t === 'Organization Sign In' || t === 'כניסת ארגונים') link.textContent = isHe ? 'כניסת ארגונים' : 'Organization Sign In';
        if (t === 'Create Account' || t === 'פתיחת חשבון') link.textContent = isHe ? 'פתיחת חשבון' : 'Create Account';
        if (t.includes('Plan') || t.includes('מסלולים')) link.textContent = isHe ? 'מסלולים ומכסות' : 'Plan & Quotas';
        if (t.includes('Why We Are') || t.includes('למה אנחנו')) link.textContent = isHe ? 'למה אנחנו ייחודיים' : 'Why We Are Unique';
        if (t.includes('Download') || t.includes('הורד')) link.textContent = isHe ? 'הורד אפליקציה לנייד' : 'Download Mobile App';
        if (t.includes('Plans & Pricing') || t.includes('תמחור')) link.textContent = isHe ? 'מסלולים ותמחור' : 'Plans & Pricing';
        if (t === 'Compare' || t === 'השוואה') link.textContent = isHe ? 'השוואה' : 'Compare';
      });
      const footerBottomDivs = document.querySelectorAll('.ln-footer-bottom > div');
      if (footerBottomDivs.length >= 3) {
        footerBottomDivs[0].innerHTML = isHe ? 'כל הזכויות שמורות &copy; 2026 IcapsQ.' : 'Copyright &copy; 2026 IcapsQ. All rights reserved.';
        const prodLink = footerBottomDivs[2].querySelector('a');
        if (prodLink) {
          prodLink.textContent = isHe ? 'מוצר מבית M&F Technologies' : 'Product of M&F Technologies';
        }
      }

      // Page header (vote.html, surveys.html)
      const dirTag = document.querySelector('.page-header-row div[style*="color:#29B6F6"]');
      if (dirTag) {
        const page = window.location.pathname;
        if (page.includes('vote')) dirTag.textContent = isHe ? 'מדריך קהילתי וציבורי' : 'Public & Community Directory';
        if (page.includes('surveys')) dirTag.textContent = isHe ? 'שאלוני משוב ומחקר ציבוריים' : 'Public & Community Inquiries';
      }
      const pageTitle = document.querySelector('.page-header-title');
      if (pageTitle) {
        const page = window.location.pathname;
        if (page.includes('vote')) pageTitle.textContent = isHe ? 'סקרים ומשאלי עם פעילים' : 'Active Public Polls & Referendums';
        if (page.includes('surveys')) pageTitle.textContent = isHe ? 'מחקרים ושאלוני משוב פעילים' : 'Active Research & Public Surveys';
      }
      const pageDesc = document.querySelector('.page-header-desc');
      if (pageDesc) {
        const page = window.location.pathname;
        if (page.includes('vote')) pageDesc.textContent = isHe
          ? 'עיין במשאלי עם קהילתיים, סקרי ארגונים ובירורים אזרחיים. הצבע ישירות כדי להביע את עמדתך וצפה בנתונים מצטברים מאומתים בזמן אמת.'
          : 'Browse published community referendums, organizational polls, and civic inquiries. Vote directly to express your perspective and view verified real-time aggregate totals.';
        if (page.includes('surveys')) pageDesc.textContent = isHe
          ? 'גלה שאלוני משוב ציבוריים, סקרי שביעות רצון ומחקרי קהילה מאומתים. הבע את דעתך ועקוב אחר תוצאות אמת.'
          : 'Explore published institutional surveys, research inquiries, and public feedback forms. Share your perspective and track verified response metrics in real-time.';
      }

      // Sidebar badge & banner
      const sideBadge = document.querySelector('.sidebar-badge');
      if (sideBadge) sideBadge.textContent = isHe ? 'השתתפות באפליקציה' : 'Mobile App Participation';
      const sideHead = document.querySelector('.polls-sidebar h3');
      if (sideHead) sideHead.textContent = isHe ? 'השתתפות באפליקציה' : 'Participate on Mobile';
      const sideDesc = document.querySelector('.polls-sidebar p');
      if (sideDesc) {
        sideDesc.textContent = isHe
          ? 'הורד את אפליקציית IcapsQ ל-Android כדי להצביע ולמלא שאלונים מכל מקום ובכל עת.'
          : 'Download the IcapsQ Mobile App for Android to cast votes and complete surveys anywhere on the go.';
      }
      const sideBtn = document.querySelector('.polls-sidebar a');
      if (sideBtn) {
        sideBtn.textContent = isHe ? '<- הורד אפליקציה ל-Android' : 'Get Android Mobile App →';
      }
    },

    async detectIsrael() {
      // 1. Explicit user selection always has priority
      const saved = localStorage.getItem('icapsq_lang');
      if (saved === 'he' || saved === 'en') {
        this.setLanguage(saved, false);
        return;
      }

      // 2. Synchronous zero-latency detection: TimeZone
      try {
        const tz = (Intl.DateTimeFormat().resolvedOptions().timeZone || '').toLowerCase();
        if (tz.includes('jerusalem') || tz.includes('tel_aviv') || tz.includes('israel')) {
          this.setLanguage('he', false);
          return;
        }
      } catch (e) {}

      // 3. Synchronous browser language preferences
      try {
        const navLangs = navigator.languages || [navigator.language || ''];
        if (navLangs.some(l => l && l.toLowerCase().startsWith('he'))) {
          this.setLanguage('he', false);
          return;
        }
      } catch (e) {}

      // 4. Backend Cloudflare CF-IPCountry check
      try {
        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), 2200);
        const res = await fetch('/api/geo/detect', { signal: ctrl.signal });
        clearTimeout(tid);
        if (res.ok) {
          const data = await res.json();
          if (data && (data.isIsrael || data.countryCode === 'IL' || data.language === 'he')) {
            this.setLanguage('he', false);
            return;
          }
        }
      } catch (e) {}

      // Default to English if not in Israel
      this.setLanguage('en', false);
    },

    init() {
      this.injectStyles();
      this.ensureSwitcherInNav();

      const saved = localStorage.getItem('icapsq_lang');
      if (saved) {
        this.setLanguage(saved, false);
      } else {
        this.detectIsrael();
      }
    }
  };

  window.IcapsQ_i18n = I18n;
  window.I18n = I18n;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => I18n.init());
  } else {
    I18n.init();
  }

})(window, document);
