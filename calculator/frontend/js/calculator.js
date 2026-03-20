/* =============================================
   Rocket Logistic — Transport Price Calculator
   calculator.js
   ============================================= */

'use strict';

// ---------------------------------------------------------------------------
// 1. Language detection
// ---------------------------------------------------------------------------
const lang = document.documentElement.lang === 'bg' ? 'bg' : 'en';

// ---------------------------------------------------------------------------
// 2. Bilingual string table
// ---------------------------------------------------------------------------
const STRINGS = {
  en: {
    calc_title:               'Get a Price Estimate',
    service_type_label:       'Service Type',
    service_ftl:              'Full Truck Load (FTL)',
    service_ltl:              'Partial Load (LTL)',
    label_origin_country:     'From (country)',
    placeholder_origin_country: 'Select country',
    label_origin:             'From (city)',
    placeholder_origin:       'Select origin city',
    placeholder_origin_text:  'Enter origin city',
    label_destination_country:'To (country)',
    placeholder_dest_country: 'Select country',
    label_destination:        'To (city)',
    placeholder_dest:         'Select destination',
    placeholder_dest_text:    'Enter destination city',
    label_pallets:            'Number of pallets',
    placeholder_pallets:      'e.g. 5',
    label_weight_ltl:         'Total weight (kg)',
    label_pallet_type:        'Pallet type',
    opt_eur_pallet:           'EUR pallet (120\u00d780 cm)',
    opt_ind_pallet:           'Industrial (120\u00d7100 cm)',
    label_non_pallet:         'Cargo is not on pallets',
    label_cargo_length:       'Cargo length (cm)',
    label_cargo_width:        'Cargo width (cm)',
    placeholder_dimension:    'e.g. 120',
    label_weight_ftl:         'Cargo weight (kg)',
    label_truck_type:         'Truck type',
    opt_curtainsider:         'Standard curtainsider',
    opt_refrigerated:         'Refrigerated',
    opt_flatbed:              'Flatbed',
    label_load_date:          'Desired load date',
    label_flexibility:        'Date flexibility',
    opt_flexible:             'Flexible',
    opt_fixed:                'Fixed date',
    estimate_label:           'Estimated price',
    estimate_secondary:       'approx.',
    fill_fields:              'Fill in details above to see estimate.',
    no_rate:                  'Contact us for a custom quote.',
    api_error:                'Unable to calculate \u2014 please contact us.',
    disclaimer:               'Indicative estimate only. Final price subject to confirmation.',
    btn_get_quote:            'Request Formal Quote',
    quote_section_title:      'Request a Quote',
    label_name:               'Name',
    placeholder_name:         'Your full name',
    label_email:              'Email',
    placeholder_email:        'your@email.com',
    label_phone:              'Phone',
    contact_hint:             'Please provide at least an email or phone number.',
    placeholder_phone:        '+359 \u2026',
    label_notes:              'Additional notes',
    placeholder_notes:        'Cargo specifics, special requirements\u2026',
    btn_submit:               'Submit Quote Request',
    submit_success:           'Thank you! We will contact you shortly.',
    submit_error:             'Something went wrong. Please try again or contact us directly.',
    btn_calculate:            'Calculate',
    opt_other_city:           'Other (specify)',
    // Validation errors
    err_service_type:         'Please select a service type.',
    err_origin_country:       'Please select an origin country.',
    err_origin_city:          'Please enter an origin city.',
    err_dest_country:         'Please select a destination country.',
    err_destination:          'Please select a destination.',
    err_num_pallets:          'Enter a number of pallets between 1 and 33.',
    err_weight_ltl:           'Enter a valid total weight in kg.',
    err_cargo_length:         'Enter a valid cargo length in cm.',
    err_cargo_width:          'Enter a valid cargo width in cm.',
    err_weight_ftl:           'Enter a valid cargo weight in kg.',
    err_name:                 'Name must be between 2 and 100 characters.',
    err_contact:              'Please enter an email address or phone number.',
    err_email_format:         'Please enter a valid email address.',
    err_notes_length:         'Notes must not exceed 500 characters.',
    quote_submitted:          'Quote submitted',
  },
  bg: {
    calc_title:               '\u041f\u043e\u043b\u0443\u0447\u0435\u0442\u0435 \u0446\u0435\u043d\u043e\u0432\u0430 \u043e\u0444\u0435\u0440\u0442\u0430',
    service_type_label:       '\u0412\u0438\u0434 \u0443\u0441\u043b\u0443\u0433\u0430',
    service_ftl:              '\u041f\u044a\u043b\u0435\u043d \u043a\u0430\u043c\u0438\u043e\u043d (FTL)',
    service_ltl:              '\u0427\u0430\u0441\u0442\u0438\u0447\u0435\u043d \u0442\u043e\u0432\u0430\u0440 (LTL)',
    label_origin_country:     '\u0414\u044a\u0440\u0436\u0430\u0432\u0430 \u043d\u0430 \u0442\u0440\u044a\u0433\u0432\u0430\u043d\u0435',
    placeholder_origin_country:'\u0418\u0437\u0431\u0435\u0440\u0435\u0442\u0435 \u0434\u044a\u0440\u0436\u0430\u0432\u0430',
    label_origin:             '\u0413\u0440\u0430\u0434 \u043d\u0430 \u0442\u0440\u044a\u0433\u0432\u0430\u043d\u0435',
    placeholder_origin:       '\u0418\u0437\u0431\u0435\u0440\u0435\u0442\u0435 \u0433\u0440\u0430\u0434 \u043d\u0430 \u0442\u0440\u044a\u0433\u0432\u0430\u043d\u0435',
    placeholder_origin_text:  '\u0412\u044a\u0432\u0435\u0434\u0435\u0442\u0435 \u0433\u0440\u0430\u0434 \u043d\u0430 \u0442\u0440\u044a\u0433\u0432\u0430\u043d\u0435',
    label_destination_country:'\u0414\u044a\u0440\u0436\u0430\u0432\u0430 \u043d\u0430 \u0434\u0435\u0441\u0442\u0438\u043d\u0430\u0446\u0438\u044f',
    placeholder_dest_country: '\u0418\u0437\u0431\u0435\u0440\u0435\u0442\u0435 \u0434\u044a\u0440\u0436\u0430\u0432\u0430',
    label_destination:        '\u0413\u0440\u0430\u0434 \u043d\u0430 \u0434\u0435\u0441\u0442\u0438\u043d\u0430\u0446\u0438\u044f',
    placeholder_dest:         '\u0418\u0437\u0431\u0435\u0440\u0435\u0442\u0435 \u0434\u0435\u0441\u0442\u0438\u043d\u0430\u0446\u0438\u044f',
    placeholder_dest_text:    '\u0412\u044a\u0432\u0435\u0434\u0435\u0442\u0435 \u0433\u0440\u0430\u0434 \u043d\u0430 \u0434\u0435\u0441\u0442\u0438\u043d\u0430\u0446\u0438\u044f',
    label_pallets:            '\u0411\u0440\u043e\u0439 \u043f\u0430\u043b\u0435\u0442\u0438',
    placeholder_pallets:      '\u043d\u0430\u043f\u0440. 5',
    label_weight_ltl:         '\u041e\u0431\u0449\u043e \u0442\u0435\u0433\u043b\u043e (\u043a\u0433)',
    label_pallet_type:        '\u0412\u0438\u0434 \u043f\u0430\u043b\u0435\u0442',
    opt_eur_pallet:           '\u0415\u0412\u0420\u041e \u043f\u0430\u043b\u0435\u0442 (120\u00d780 \u0441\u043c)',
    opt_ind_pallet:           '\u0418\u043d\u0434\u0443\u0441\u0442\u0440\u0438\u0430\u043b\u0435\u043d (120\u00d7100 \u0441\u043c)',
    label_non_pallet:         '\u0422\u043e\u0432\u0430\u0440\u044a\u0442 \u043d\u0435 \u0435 \u043d\u0430 \u043f\u0430\u043b\u0435\u0442\u0438',
    label_cargo_length:       '\u0414\u044a\u043b\u0436\u0438\u043d\u0430 \u043d\u0430 \u0442\u043e\u0432\u0430\u0440\u0430 (\u0441\u043c)',
    label_cargo_width:        '\u0428\u0438\u0440\u0438\u043d\u0430 \u043d\u0430 \u0442\u043e\u0432\u0430\u0440\u0430 (\u0441\u043c)',
    placeholder_dimension:    '\u043d\u0430\u043f\u0440. 120',
    label_weight_ftl:         '\u0422\u0435\u0433\u043b\u043e \u043d\u0430 \u0442\u043e\u0432\u0430\u0440\u0430 (\u043a\u0433)',
    label_truck_type:         '\u0422\u0438\u043f \u043a\u0430\u043c\u0438\u043e\u043d',
    opt_curtainsider:         '\u0421\u0442\u0430\u043d\u0434\u0430\u0440\u0442\u043d\u0430 \u0442\u0435\u043d\u0442\u043e\u0432\u0430',
    opt_refrigerated:         '\u0425\u043b\u0430\u0434\u0438\u043b\u043d\u0430',
    opt_flatbed:              '\u041f\u043b\u0430\u0442\u0444\u043e\u0440\u043c\u0430',
    label_load_date:          '\u0416\u0435\u043b\u0430\u043d\u0430 \u0434\u0430\u0442\u0430 \u043d\u0430 \u0442\u043e\u0432\u0430\u0440\u0435\u043d\u0435',
    label_flexibility:        '\u0413\u044a\u0432\u043a\u0430\u0432\u043e\u0441\u0442 \u043d\u0430 \u0434\u0430\u0442\u0430\u0442\u0430',
    opt_flexible:             '\u0413\u044a\u0432\u043a\u0430\u0432\u0430',
    opt_fixed:                '\u0424\u0438\u043a\u0441\u0438\u0440\u0430\u043d\u0430 \u0434\u0430\u0442\u0430',
    estimate_label:           '\u041f\u0440\u0438\u0431\u043b\u0438\u0437\u0438\u0442\u0435\u043b\u043d\u0430 \u0446\u0435\u043d\u0430',
    estimate_secondary:       '\u043f\u0440\u0438\u0431\u043b.',
    fill_fields:              '\u041f\u043e\u043f\u044a\u043b\u043d\u0435\u0442\u0435 \u0434\u0430\u043d\u043d\u0438\u0442\u0435 \u043f\u043e-\u0433\u043e\u0440\u0435, \u0437\u0430 \u0434\u0430 \u0432\u0438\u0434\u0438\u0442\u0435 \u043e\u0446\u0435\u043d\u043a\u0430\u0442\u0430.',
    no_rate:                  '\u0421\u0432\u044a\u0440\u0436\u0435\u0442\u0435 \u0441\u0435 \u0441 \u043d\u0430\u0441 \u0437\u0430 \u0438\u043d\u0434\u0438\u0432\u0438\u0434\u0443\u0430\u043b\u043d\u0430 \u043e\u0444\u0435\u0440\u0442\u0430.',
    api_error:                '\u041d\u0435 \u043c\u043e\u0436\u0435 \u0434\u0430 \u0441\u0435 \u0438\u0437\u0447\u0438\u0441\u043b\u0438 \u2014 \u043c\u043e\u043b\u044f \u0441\u0432\u044a\u0440\u0436\u0435\u0442\u0435 \u0441\u0435 \u0441 \u043d\u0430\u0441.',
    disclaimer:               '\u0421\u0430\u043c\u043e \u043f\u0440\u0438\u0431\u043b\u0438\u0437\u0438\u0442\u0435\u043b\u043d\u0430 \u043e\u0446\u0435\u043d\u043a\u0430. \u041a\u0440\u0430\u0439\u043d\u0430\u0442\u0430 \u0446\u0435\u043d\u0430 \u043f\u043e\u0434\u043b\u0435\u0436\u0438 \u043d\u0430 \u043f\u043e\u0442\u0432\u044a\u0440\u0436\u0434\u0435\u043d\u0438\u0435.',
    btn_get_quote:            '\u041f\u043e\u0438\u0441\u043a\u0430\u0439\u0442\u0435 \u043e\u0444\u0438\u0446\u0438\u0430\u043b\u043d\u0430 \u043e\u0444\u0435\u0440\u0442\u0430',
    quote_section_title:      '\u0417\u0430\u044f\u0432\u0435\u0442\u0435 \u043e\u0444\u0435\u0440\u0442\u0430',
    label_name:               '\u0418\u043c\u0435',
    placeholder_name:         '\u0412\u0430\u0448\u0435\u0442\u043e \u043f\u044a\u043b\u043d\u043e \u0438\u043c\u0435',
    label_email:              '\u0418\u043c\u0435\u0439\u043b',
    placeholder_email:        '\u0432\u0430\u0448\u0438\u044f@\u0438\u043c\u0435\u0439\u043b.com',
    label_phone:              '\u0422\u0435\u043b\u0435\u0444\u043e\u043d',
    contact_hint:             '\u041c\u043e\u043b\u044f \u0432\u044a\u0432\u0435\u0434\u0435\u0442\u0435 \u043f\u043e\u043d\u0435 \u0438\u043c\u0435\u0439\u043b \u0438\u043b\u0438 \u0442\u0435\u043b\u0435\u0444\u043e\u043d.',
    placeholder_phone:        '+359 \u2026',
    label_notes:              '\u0414\u043e\u043f\u044a\u043b\u043d\u0438\u0442\u0435\u043b\u043d\u0438 \u0431\u0435\u043b\u0435\u0436\u043a\u0438',
    placeholder_notes:        '\u0421\u043f\u0435\u0446\u0438\u0444\u0438\u043a\u0438 \u043d\u0430 \u0442\u043e\u0432\u0430\u0440\u0430, \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u043d\u0438 \u0438\u0437\u0438\u0441\u043a\u0432\u0430\u043d\u0438\u044f\u2026',
    btn_submit:               '\u0418\u0437\u043f\u0440\u0430\u0442\u0435\u0442\u0435 \u0437\u0430\u044f\u0432\u043a\u0430 \u0437\u0430 \u043e\u0444\u0435\u0440\u0442\u0430',
    submit_success:           '\u0411\u043b\u0430\u0433\u043e\u0434\u0430\u0440\u0438\u043c! \u0429\u0435 \u0441\u0435 \u0441\u0432\u044a\u0440\u0436\u0435\u043c \u0441 \u0432\u0430\u0441 \u0441\u043a\u043e\u0440\u043e.',
    submit_error:             '\u041d\u0435\u0449\u043e \u0441\u0435 \u043e\u0431\u044a\u0440\u043a\u0430. \u041c\u043e\u043b\u044f \u043e\u043f\u0438\u0442\u0430\u0439\u0442\u0435 \u043e\u0442\u043d\u043e\u0432\u043e \u0438\u043b\u0438 \u0441\u0435 \u0441\u0432\u044a\u0440\u0436\u0435\u0442\u0435 \u0441 \u043d\u0430\u0441 \u0434\u0438\u0440\u0435\u043a\u0442\u043d\u043e.',
    btn_calculate:            '\u041a\u0430\u043b\u043a\u0443\u043b\u0438\u0440\u0430\u0439',
    opt_other_city:           '\u0414\u0440\u0443\u0433\u043e (\u0443\u043a\u0430\u0436\u0435\u0442\u0435)',
    // Validation errors
    err_service_type:         '\u041c\u043e\u043b\u044f \u0438\u0437\u0431\u0435\u0440\u0435\u0442\u0435 \u0432\u0438\u0434 \u0443\u0441\u043b\u0443\u0433\u0430.',
    err_origin_country:       '\u041c\u043e\u043b\u044f \u0438\u0437\u0431\u0435\u0440\u0435\u0442\u0435 \u0434\u044a\u0440\u0436\u0430\u0432\u0430 \u043d\u0430 \u0442\u0440\u044a\u0433\u0432\u0430\u043d\u0435.',
    err_origin_city:          '\u041c\u043e\u043b\u044f \u0432\u044a\u0432\u0435\u0434\u0435\u0442\u0435 \u0433\u0440\u0430\u0434 \u043d\u0430 \u0442\u0440\u044a\u0433\u0432\u0430\u043d\u0435.',
    err_dest_country:         '\u041c\u043e\u043b\u044f \u0438\u0437\u0431\u0435\u0440\u0435\u0442\u0435 \u0434\u044a\u0440\u0436\u0430\u0432\u0430 \u043d\u0430 \u0434\u0435\u0441\u0442\u0438\u043d\u0430\u0446\u0438\u044f.',
    err_destination:          '\u041c\u043e\u043b\u044f \u0438\u0437\u0431\u0435\u0440\u0435\u0442\u0435 \u0434\u0435\u0441\u0442\u0438\u043d\u0430\u0446\u0438\u044f.',
    err_num_pallets:          '\u0412\u044a\u0432\u0435\u0434\u0435\u0442\u0435 \u0431\u0440\u043e\u0439 \u043f\u0430\u043b\u0435\u0442\u0438 \u043c\u0435\u0436\u0434\u0443 1 \u0438 33.',
    err_weight_ltl:           '\u0412\u044a\u0432\u0435\u0434\u0435\u0442\u0435 \u0432\u0430\u043b\u0438\u0434\u043d\u043e \u043e\u0431\u0449\u043e \u0442\u0435\u0433\u043b\u043e \u0432 \u043a\u0433.',
    err_cargo_length:         '\u0412\u044a\u0432\u0435\u0434\u0435\u0442\u0435 \u0432\u0430\u043b\u0438\u0434\u043d\u0430 \u0434\u044a\u043b\u0436\u0438\u043d\u0430 \u043d\u0430 \u0442\u043e\u0432\u0430\u0440\u0430 \u0432 \u0441\u043c.',
    err_cargo_width:          '\u0412\u044a\u0432\u0435\u0434\u0435\u0442\u0435 \u0432\u0430\u043b\u0438\u0434\u043d\u0430 \u0448\u0438\u0440\u0438\u043d\u0430 \u043d\u0430 \u0442\u043e\u0432\u0430\u0440\u0430 \u0432 \u0441\u043c.',
    err_weight_ftl:           '\u0412\u044a\u0432\u0435\u0434\u0435\u0442\u0435 \u0432\u0430\u043b\u0438\u0434\u043d\u043e \u0442\u0435\u0433\u043b\u043e \u043d\u0430 \u0442\u043e\u0432\u0430\u0440\u0430 \u0432 \u043a\u0433.',
    err_name:                 '\u0418\u043c\u0435\u0442\u043e \u0442\u0440\u044f\u0431\u0432\u0430 \u0434\u0430 \u0435 \u043c\u0435\u0436\u0434\u0443 2 \u0438 100 \u0437\u043d\u0430\u043a\u0430.',
    err_contact:              '\u041c\u043e\u043b\u044f \u0432\u044a\u0432\u0435\u0434\u0435\u0442\u0435 \u0438\u043c\u0435\u0439\u043b \u0430\u0434\u0440\u0435\u0441 \u0438\u043b\u0438 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0435\u043d \u043d\u043e\u043c\u0435\u0440.',
    err_email_format:         '\u041c\u043e\u043b\u044f \u0432\u044a\u0432\u0435\u0434\u0435\u0442\u0435 \u0432\u0430\u043b\u0438\u0434\u0435\u043d \u0438\u043c\u0435\u0439\u043b \u0430\u0434\u0440\u0435\u0441.',
    err_notes_length:         '\u0411\u0435\u043b\u0435\u0436\u043a\u0438\u0442\u0435 \u043d\u0435 \u0442\u0440\u044f\u0431\u0432\u0430 \u0434\u0430 \u043d\u0430\u0434\u0432\u0438\u0448\u0430\u0432\u0430\u0442 500 \u0437\u043d\u0430\u043a\u0430.',
    quote_submitted:          '\u0417\u0430\u044f\u0432\u043a\u0430\u0442\u0430 \u0435 \u0438\u0437\u043f\u0440\u0430\u0442\u0435\u043d\u0430',
  }
};

const t = STRINGS[lang];

// ---------------------------------------------------------------------------
// 3. Country / city data
// ---------------------------------------------------------------------------
const COUNTRIES = [
  { code: 'BG', name_en: 'Bulgaria',        name_bg: '\u0411\u044a\u043b\u0433\u0430\u0440\u0438\u044f' },
  { code: 'RO', name_en: 'Romania',         name_bg: '\u0420\u0443\u043c\u044a\u043d\u0438\u044f' },
  { code: 'GR', name_en: 'Greece',          name_bg: '\u0413\u044a\u0440\u0446\u0438\u044f' },
  { code: 'DE', name_en: 'Germany',         name_bg: '\u0413\u0435\u0440\u043c\u0430\u043d\u0438\u044f' },
  { code: 'AT', name_en: 'Austria',         name_bg: '\u0410\u0432\u0441\u0442\u0440\u0438\u044f' },
  { code: 'HU', name_en: 'Hungary',         name_bg: '\u0423\u043d\u0433\u0430\u0440\u0438\u044f' },
  { code: 'PL', name_en: 'Poland',          name_bg: '\u041f\u043e\u043b\u0448\u0430' },
  { code: 'CZ', name_en: 'Czech Republic',  name_bg: '\u0427\u0435\u0445\u0438\u044f' },
  { code: 'SK', name_en: 'Slovakia',        name_bg: '\u0421\u043b\u043e\u0432\u0430\u043a\u0438\u044f' },
  { code: 'IT', name_en: 'Italy',           name_bg: '\u0418\u0442\u0430\u043b\u0438\u044f' },
  { code: 'FR', name_en: 'France',          name_bg: '\u0424\u0440\u0430\u043d\u0446\u0438\u044f' },
  { code: 'ES', name_en: 'Spain',           name_bg: '\u0418\u0441\u043f\u0430\u043d\u0438\u044f' },
  { code: 'NL', name_en: 'Netherlands',     name_bg: '\u041d\u0438\u0434\u0435\u0440\u043b\u0430\u043d\u0434\u0438\u044f' },
  { code: 'BE', name_en: 'Belgium',         name_bg: '\u0411\u0435\u043b\u0433\u0438\u044f' },
  { code: 'TR', name_en: 'Turkey',          name_bg: '\u0422\u0443\u0440\u0446\u0438\u044f' },
  { code: 'RS', name_en: 'Serbia',          name_bg: '\u0421\u044a\u0440\u0431\u0438\u044f' },
  { code: 'MK', name_en: 'North Macedonia', name_bg: '\u0421\u0435\u0432\u0435\u0440\u043d\u0430 \u041c\u0430\u043a\u0435\u0434\u043e\u043d\u0438\u044f' },
];

const CITIES_BY_COUNTRY = {
  BG: [
    { en: 'Sofia',              bg: 'София' },
    { en: 'Plovdiv',            bg: 'Пловдив' },
    { en: 'Varna',              bg: 'Варна' },
    { en: 'Burgas',             bg: 'Бургас' },
    { en: 'Ruse',               bg: 'Русе' },
    { en: 'Stara Zagora',       bg: 'Стара Загора' },
    { en: 'Pleven',             bg: 'Плевен' },
    { en: 'Sliven',             bg: 'Сливен' },
    { en: 'Dobrich',            bg: 'Добрич' },
    { en: 'Shumen',             bg: 'Шумен' },
    { en: 'Pernik',             bg: 'Перник' },
    { en: 'Haskovo',            bg: 'Хасково' },
    { en: 'Yambol',             bg: 'Ямбол' },
    { en: 'Pazardzhik',         bg: 'Пазарджик' },
    { en: 'Blagoevgrad',        bg: 'Благоевград' },
    { en: 'Veliko Tarnovo',     bg: 'Велико Търново' },
    { en: 'Vratsa',             bg: 'Враца' },
    { en: 'Gabrovo',            bg: 'Габрово' },
    { en: 'Asenovgrad',         bg: 'Асеновград' },
    { en: 'Vidin',              bg: 'Видин' },
    { en: 'Kazanlak',           bg: 'Казанлък' },
    { en: 'Kyustendil',         bg: 'Кюстендил' },
    { en: 'Montana',            bg: 'Монтана' },
    { en: 'Dimitrovgrad',       bg: 'Димитровград' },
    { en: 'Lovech',             bg: 'Ловеч' },
    { en: 'Silistra',           bg: 'Силистра' },
    { en: 'Targovishte',        bg: 'Търговище' },
    { en: 'Dupnitsa',           bg: 'Дупница' },
    { en: 'Razgrad',            bg: 'Разград' },
    { en: 'Gorna Oryahovitsa',  bg: 'Горна Оряховица' },
    { en: 'Petrich',            bg: 'Петрич' },
    { en: 'Gotse Delchev',      bg: 'Гоце Делчев' },
    { en: 'Karlovo',            bg: 'Карлово' },
    { en: 'Smolyan',            bg: 'Смолян' },
    { en: 'Sandanski',          bg: 'Сандански' },
    { en: 'Sevlievo',           bg: 'Севлиево' },
    { en: 'Samokov',            bg: 'Самоков' },
    { en: 'Lom',                bg: 'Лом' },
    { en: 'Nova Zagora',        bg: 'Нова Загора' },
    { en: 'Troyan',             bg: 'Троян' },
    { en: 'Aytos',              bg: 'Айтос' },
    { en: 'Botevgrad',          bg: 'Ботевград' },
    { en: 'Velingrad',          bg: 'Велинград' },
    { en: 'Svilengrad',         bg: 'Свиленград' },
    { en: 'Kardzhali',          bg: 'Кърджали' },
    { en: 'Harmanli',           bg: 'Харманли' },
    { en: 'Panagyurishte',      bg: 'Панагюрище' },
    { en: 'Chirpan',            bg: 'Чирпан' },
    { en: 'Pomorie',            bg: 'Поморие' },
    { en: 'Popovo',             bg: 'Попово' },
  ],
  RO: [
    { en: 'Bucharest',    bg: 'Букурещ' },
    { en: 'Cluj-Napoca',  bg: 'Клуж-Напока' },
    { en: 'Timisoara',    bg: 'Тимишоара' },
    { en: 'Constanta',    bg: 'Констанца' },
    { en: 'Iasi',         bg: 'Яш' },
    { en: 'Brasov',       bg: 'Брашов' },
    { en: 'Craiova',      bg: 'Крайова' },
    { en: 'Galati',       bg: 'Галац' },
    { en: 'Ploiesti',     bg: 'Плоещ' },
    { en: 'Oradea',       bg: 'Орадя' },
    { en: 'Arad',         bg: 'Арад' },
    { en: 'Sibiu',        bg: 'Сибиу' },
    { en: 'Pitesti',      bg: 'Питещ' },
    { en: 'Bacau',        bg: 'Бакъу' },
    { en: 'Giurgiu',      bg: 'Гюргево' },
  ],
  GR: [
    { en: 'Athens',          bg: 'Атина' },
    { en: 'Thessaloniki',    bg: 'Солун' },
    { en: 'Patras',          bg: 'Патра' },
    { en: 'Heraklion',       bg: 'Ираклион' },
    { en: 'Larissa',         bg: 'Лариса' },
    { en: 'Volos',           bg: 'Волос' },
    { en: 'Ioannina',        bg: 'Янина' },
    { en: 'Kavala',          bg: 'Кавала' },
    { en: 'Alexandroupoli',  bg: 'Александруполи' },
    { en: 'Serres',          bg: 'Сяр' },
  ],
  DE: [
    { en: 'Berlin',      bg: 'Берлин' },
    { en: 'Munich',      bg: 'Мюнхен' },
    { en: 'Hamburg',      bg: 'Хамбург' },
    { en: 'Frankfurt',   bg: 'Франкфурт' },
    { en: 'Cologne',     bg: 'Кьолн' },
    { en: 'Stuttgart',   bg: 'Щутгарт' },
    { en: 'Dusseldorf',  bg: 'Дюселдорф' },
    { en: 'Dortmund',    bg: 'Дортмунд' },
    { en: 'Essen',       bg: 'Есен' },
    { en: 'Leipzig',     bg: 'Лайпциг' },
    { en: 'Bremen',      bg: 'Бремен' },
    { en: 'Dresden',     bg: 'Дрезден' },
    { en: 'Hannover',    bg: 'Хановер' },
    { en: 'Nuremberg',   bg: 'Нюрнберг' },
  ],
  AT: [
    { en: 'Vienna',       bg: 'Виена' },
    { en: 'Graz',         bg: 'Грац' },
    { en: 'Linz',         bg: 'Линц' },
    { en: 'Salzburg',     bg: 'Залцбург' },
    { en: 'Innsbruck',    bg: 'Инсбрук' },
    { en: 'Klagenfurt',   bg: 'Клагенфурт' },
    { en: 'Villach',      bg: 'Филах' },
    { en: 'Wels',         bg: 'Велс' },
    { en: 'Sankt Polten', bg: 'Санкт Пьолтен' },
    { en: 'Dornbirn',     bg: 'Дорнбирн' },
  ],
  HU: [
    { en: 'Budapest',       bg: 'Будапеща' },
    { en: 'Debrecen',       bg: 'Дебрецен' },
    { en: 'Szeged',         bg: 'Сегед' },
    { en: 'Miskolc',        bg: 'Мишколц' },
    { en: 'Pecs',           bg: 'Печ' },
    { en: 'Gyor',           bg: 'Дьор' },
    { en: 'Nyiregyhaza',    bg: 'Ниредхаза' },
    { en: 'Kecskemet',      bg: 'Кечкемет' },
    { en: 'Szekesfehervar', bg: 'Секешфехервар' },
    { en: 'Szombathely',    bg: 'Сомбатхей' },
  ],
  PL: [
    { en: 'Warsaw',    bg: 'Варшава' },
    { en: 'Krakow',    bg: 'Краков' },
    { en: 'Lodz',      bg: 'Лодз' },
    { en: 'Wroclaw',   bg: 'Вроцлав' },
    { en: 'Poznan',    bg: 'Познан' },
    { en: 'Gdansk',    bg: 'Гданск' },
    { en: 'Szczecin',  bg: 'Шчечин' },
    { en: 'Katowice',  bg: 'Катовице' },
    { en: 'Lublin',    bg: 'Люблин' },
    { en: 'Bialystok', bg: 'Бялисток' },
    { en: 'Rzeszow',   bg: 'Жешув' },
  ],
  CZ: [
    { en: 'Prague',             bg: 'Прага' },
    { en: 'Brno',               bg: 'Бърно' },
    { en: 'Ostrava',            bg: 'Острава' },
    { en: 'Plzen',              bg: 'Плзен' },
    { en: 'Liberec',            bg: 'Либерец' },
    { en: 'Olomouc',            bg: 'Оломоуц' },
    { en: 'Ceske Budejovice',   bg: 'Ческе Будейовице' },
    { en: 'Hradec Kralove',     bg: 'Храдец Кралове' },
    { en: 'Pardubice',          bg: 'Пардубице' },
    { en: 'Zlin',               bg: 'Злин' },
  ],
  SK: [
    { en: 'Bratislava',       bg: 'Братислава' },
    { en: 'Kosice',           bg: 'Кошице' },
    { en: 'Presov',           bg: 'Прешов' },
    { en: 'Zilina',           bg: 'Жилина' },
    { en: 'Banska Bystrica',  bg: 'Банска Бистрица' },
    { en: 'Nitra',            bg: 'Нитра' },
    { en: 'Trnava',           bg: 'Търнава' },
    { en: 'Trencin',          bg: 'Тренчин' },
    { en: 'Martin',           bg: 'Мартин' },
    { en: 'Poprad',           bg: 'Попрад' },
  ],
  IT: [
    { en: 'Rome',      bg: 'Рим' },
    { en: 'Milan',     bg: 'Милано' },
    { en: 'Naples',    bg: 'Неапол' },
    { en: 'Turin',     bg: 'Торино' },
    { en: 'Palermo',   bg: 'Палермо' },
    { en: 'Genoa',     bg: 'Генуа' },
    { en: 'Bologna',   bg: 'Болоня' },
    { en: 'Florence',  bg: 'Флоренция' },
    { en: 'Bari',      bg: 'Бари' },
    { en: 'Venice',    bg: 'Венеция' },
    { en: 'Verona',    bg: 'Верона' },
    { en: 'Trieste',   bg: 'Триест' },
  ],
  FR: [
    { en: 'Paris',        bg: 'Париж' },
    { en: 'Marseille',    bg: 'Марсилия' },
    { en: 'Lyon',         bg: 'Лион' },
    { en: 'Toulouse',     bg: 'Тулуза' },
    { en: 'Nice',         bg: 'Ница' },
    { en: 'Nantes',       bg: 'Нант' },
    { en: 'Strasbourg',   bg: 'Страсбург' },
    { en: 'Montpellier',  bg: 'Монпелие' },
    { en: 'Bordeaux',     bg: 'Бордо' },
    { en: 'Lille',        bg: 'Лил' },
    { en: 'Rennes',       bg: 'Рен' },
  ],
  ES: [
    { en: 'Madrid',      bg: 'Мадрид' },
    { en: 'Barcelona',   bg: 'Барселона' },
    { en: 'Valencia',    bg: 'Валенсия' },
    { en: 'Seville',     bg: 'Севиля' },
    { en: 'Zaragoza',    bg: 'Сарагоса' },
    { en: 'Malaga',      bg: 'Малага' },
    { en: 'Bilbao',      bg: 'Билбао' },
    { en: 'Alicante',    bg: 'Аликанте' },
    { en: 'Murcia',      bg: 'Мурсия' },
    { en: 'Valladolid',  bg: 'Валядолид' },
  ],
  NL: [
    { en: 'Amsterdam',   bg: 'Амстердам' },
    { en: 'Rotterdam',   bg: 'Ротердам' },
    { en: 'The Hague',   bg: 'Хага' },
    { en: 'Utrecht',     bg: 'Утрехт' },
    { en: 'Eindhoven',   bg: 'Айндховен' },
    { en: 'Groningen',   bg: 'Гронинген' },
    { en: 'Tilburg',     bg: 'Тилбург' },
    { en: 'Breda',       bg: 'Бреда' },
    { en: 'Nijmegen',    bg: 'Наймеген' },
    { en: 'Maastricht',  bg: 'Маастрихт' },
  ],
  BE: [
    { en: 'Brussels',   bg: 'Брюксел' },
    { en: 'Antwerp',    bg: 'Антверпен' },
    { en: 'Ghent',      bg: 'Гент' },
    { en: 'Charleroi',  bg: 'Шарлероа' },
    { en: 'Liege',      bg: 'Лиеж' },
    { en: 'Bruges',     bg: 'Брюж' },
    { en: 'Namur',      bg: 'Намюр' },
    { en: 'Leuven',     bg: 'Льовен' },
    { en: 'Mons',       bg: 'Монс' },
    { en: 'Mechelen',   bg: 'Мехелен' },
  ],
  TR: [
    { en: 'Istanbul',    bg: 'Истанбул' },
    { en: 'Ankara',      bg: 'Анкара' },
    { en: 'Izmir',       bg: 'Измир' },
    { en: 'Bursa',       bg: 'Бурса' },
    { en: 'Antalya',     bg: 'Анталия' },
    { en: 'Adana',       bg: 'Адана' },
    { en: 'Gaziantep',   bg: 'Газиантеп' },
    { en: 'Konya',       bg: 'Коня' },
    { en: 'Mersin',      bg: 'Мерсин' },
    { en: 'Edirne',      bg: 'Одрин' },
    { en: 'Tekirdag',    bg: 'Текирдаг' },
    { en: 'Kirklareli',  bg: 'Къркларели' },
  ],
  RS: [
    { en: 'Belgrade',    bg: 'Белград' },
    { en: 'Novi Sad',    bg: 'Нови Сад' },
    { en: 'Nis',         bg: 'Ниш' },
    { en: 'Kragujevac',  bg: 'Крагуевац' },
    { en: 'Subotica',    bg: 'Суботица' },
    { en: 'Zrenjanin',   bg: 'Зренянин' },
    { en: 'Pancevo',     bg: 'Панчево' },
    { en: 'Cacak',       bg: 'Чачак' },
    { en: 'Novi Pazar',  bg: 'Нови Пазар' },
    { en: 'Kraljevo',    bg: 'Кралево' },
  ],
  MK: [
    { en: 'Skopje',     bg: 'Скопие' },
    { en: 'Bitola',     bg: 'Битоля' },
    { en: 'Kumanovo',   bg: 'Куманово' },
    { en: 'Prilep',     bg: 'Прилеп' },
    { en: 'Tetovo',     bg: 'Тетово' },
    { en: 'Ohrid',      bg: 'Охрид' },
    { en: 'Veles',      bg: 'Велес' },
    { en: 'Stip',       bg: 'Щип' },
    { en: 'Strumica',   bg: 'Струмица' },
    { en: 'Gevgelija',  bg: 'Гевгелия' },
  ],
};

// ---------------------------------------------------------------------------
// 4. State
// ---------------------------------------------------------------------------
let currentServiceType = 'ftl';
let lastEstimate = null;

// Tracks whether each city field is in "select" mode or "text" mode
// and whether "Other" was chosen in a select
let originCityMode = 'select'; // 'select' | 'text'
let destCityMode   = 'select'; // 'select' | 'text'

// ---------------------------------------------------------------------------
// 5. DOM references (populated after DOMContentLoaded)
// ---------------------------------------------------------------------------
let calcForm, estimateCard, quotePanel, quoteSummary, quoteForm, quoteSuccess;
let originCountrySelect, originCitySelect, originCityText;
let destCountrySelect,   destCitySelect,   destCityText;
let ftlFields, ltlFields;
let palletTypeGroup, dimFields;
let btnCalculate, btnGetQuote, btnGetQuoteNorate, btnSubmit;

// Estimate card state elements
let stateEmpty, stateLoading, statePrice, stateNoRate, stateError;
let priceMainEl, priceEurEl, estimateNoteEl;

// Quote form fields
let qfName, qfEmail, qfPhone, qfNotes;
let qfLang, qfMinPrice, qfMaxPrice;

// ---------------------------------------------------------------------------
// 6. Initialisation
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  bindDOMRefs();
  applyStrings();
  populateCountries();
  attachEventListeners();
  showEstimateState('empty');
});

function bindDOMRefs() {
  calcForm           = document.getElementById('calc-form');
  estimateCard       = document.getElementById('estimate-card');
  quotePanel         = document.getElementById('quote-panel');
  quoteSummary       = document.getElementById('quote-summary');
  quoteForm          = document.getElementById('quote-form');
  quoteSuccess       = document.getElementById('quote-success');

  originCountrySelect = document.getElementById('origin_country');
  originCitySelect    = document.getElementById('origin_city_select');
  originCityText      = document.getElementById('origin_city_text');

  destCountrySelect   = document.getElementById('destination_country');
  destCitySelect      = document.getElementById('destination_select');
  destCityText        = document.getElementById('destination_text');

  ftlFields          = document.getElementById('ftl-fields');
  ltlFields          = document.getElementById('ltl-fields');

  palletTypeGroup    = document.getElementById('pallet-type-group');
  dimFields          = document.getElementById('dim-fields');

  btnCalculate       = document.getElementById('btn-calculate');
  btnGetQuote        = document.getElementById('btn-get-quote');
  btnGetQuoteNorate  = document.getElementById('btn-get-quote-norate');
  btnSubmit          = document.getElementById('btn-submit');

  stateEmpty         = document.getElementById('state-empty');
  stateLoading       = document.getElementById('state-loading');
  statePrice         = document.getElementById('state-price');
  stateNoRate        = document.getElementById('state-norate');
  stateError         = document.getElementById('state-error');

  priceMainEl        = document.getElementById('price-main');
  priceEurEl         = document.getElementById('price-eur');
  estimateNoteEl     = document.getElementById('estimate-note');

  qfName             = document.getElementById('qf-name');
  qfEmail            = document.getElementById('qf-email');
  qfPhone            = document.getElementById('qf-phone');
  qfNotes            = document.getElementById('qf-notes');
  qfLang             = document.getElementById('qf-lang');
  qfMinPrice         = document.getElementById('qf-min-price');
  qfMaxPrice         = document.getElementById('qf-max-price');
}

// ---------------------------------------------------------------------------
// 7. Apply bilingual strings to DOM elements
// ---------------------------------------------------------------------------
function applyStrings() {
  // Section title
  const sectionTitle = document.getElementById('calc-section-title');
  if (sectionTitle) sectionTitle.textContent = t.calc_title;

  // Service tabs
  const spanFtl = document.getElementById('label-ftl');
  const spanLtl = document.getElementById('label-ltl');
  if (spanFtl) spanFtl.textContent = t.service_ftl;
  if (spanLtl) spanLtl.textContent = t.service_ltl;

  // Route labels / placeholders
  setLabelAndPlaceholder('origin_country',      'label-origin-country',      t.label_origin_country,      t.placeholder_origin_country);
  setLabelAndPlaceholder('origin_city_select',  'label-origin-city',         t.label_origin,              t.placeholder_origin);
  setLabelAndPlaceholder('destination_country', 'label-dest-country',        t.label_destination_country, t.placeholder_dest_country);
  setLabelAndPlaceholder('destination_select',  'label-destination',         t.label_destination,         t.placeholder_dest);

  // Text fallbacks
  if (originCityText) originCityText.placeholder = t.placeholder_origin_text;
  if (destCityText)   destCityText.placeholder   = t.placeholder_dest_text;

  // LTL fields
  setLabel('label-pallets',      t.label_pallets);
  setPlaceholder('num_pallets',  t.placeholder_pallets);
  setLabel('label-weight-ltl',   t.label_weight_ltl);
  setLabel('label-pallet-type',  t.label_pallet_type);
  setOption('opt-eur-pallet',    t.opt_eur_pallet);
  setOption('opt-ind-pallet',    t.opt_ind_pallet);
  const nonPalletSpan = document.getElementById('label-non-pallet-span');
  if (nonPalletSpan) nonPalletSpan.textContent = t.label_non_pallet;
  setLabel('label-cargo-length', t.label_cargo_length);
  setPlaceholder('cargo_length_cm', t.placeholder_dimension);
  setLabel('label-cargo-width',  t.label_cargo_width);
  setPlaceholder('cargo_width_cm',  t.placeholder_dimension);

  // FTL fields
  setLabel('label-weight-ftl',   t.label_weight_ftl);
  setLabel('label-truck-type',   t.label_truck_type);
  setOption('opt-curtainsider',  t.opt_curtainsider);
  setOption('opt-refrigerated',  t.opt_refrigerated);
  setOption('opt-flatbed',       t.opt_flatbed);

  // Date fields
  setLabel('label-load-date',    t.label_load_date);
  setLabel('label-flexibility',  t.label_flexibility);
  setOption('opt-flexible',      t.opt_flexible);
  setOption('opt-fixed',         t.opt_fixed);

  // Estimate card
  const estimateLabel = document.getElementById('estimate-label');
  if (estimateLabel) estimateLabel.textContent = t.estimate_label;
  if (stateEmpty)    stateEmpty.textContent    = t.fill_fields;
  if (estimateNoteEl) estimateNoteEl.textContent = t.disclaimer;
  const noRateMsg = document.getElementById('norate-msg');
  if (noRateMsg) noRateMsg.textContent = t.no_rate;
  const errorMsg  = document.getElementById('error-msg');
  if (errorMsg)  errorMsg.textContent  = t.api_error;
  if (btnCalculate)      btnCalculate.textContent      = t.btn_calculate;
  if (btnGetQuote)       btnGetQuote.textContent       = t.btn_get_quote;
  if (btnGetQuoteNorate) btnGetQuoteNorate.textContent = t.btn_get_quote;

  // Optional toggle
  const toggleOptBtn = document.getElementById('toggle-optional-btn');
  if (toggleOptBtn) toggleOptBtn.textContent = t.toggle_optional;

  // Quote panel
  const quotePanelTitle = document.getElementById('quote-panel-title');
  if (quotePanelTitle) quotePanelTitle.textContent = t.quote_section_title;
  setLabel('label-qf-name',  t.label_name);
  setPlaceholder('qf-name',  t.placeholder_name);
  setLabel('label-qf-email', t.label_email);
  setPlaceholder('qf-email', t.placeholder_email);
  setLabel('label-qf-phone', t.label_phone);
  setPlaceholder('qf-phone', t.placeholder_phone);
  const contactHint = document.getElementById('contact-hint');
  if (contactHint) contactHint.textContent = t.contact_hint;
  setLabel('label-qf-notes', t.label_notes);
  setPlaceholder('qf-notes', t.placeholder_notes);
  if (btnSubmit) btnSubmit.textContent = t.btn_submit;
}

function setLabel(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setPlaceholder(id, text) {
  const el = document.getElementById(id);
  if (el) el.placeholder = text;
}

function setOption(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setLabelAndPlaceholder(inputId, labelId, labelText, placeholderText) {
  const labelEl = document.getElementById(labelId);
  const inputEl = document.getElementById(inputId);
  if (labelEl) labelEl.textContent = labelText;
  if (inputEl && placeholderText !== undefined) inputEl.querySelector && (inputEl.options[0].text = placeholderText);
  // For select elements the placeholder is the first disabled option
  if (inputEl && inputEl.tagName === 'SELECT' && inputEl.options[0]) {
    inputEl.options[0].text = placeholderText;
  }
}

// ---------------------------------------------------------------------------
// 8. Populate country dropdowns
// ---------------------------------------------------------------------------
function populateCountries() {
  [originCountrySelect, destCountrySelect].forEach(select => {
    if (!select) return;
    // Keep the first placeholder option
    while (select.options.length > 1) select.remove(1);
    COUNTRIES.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.code;
      opt.textContent = lang === 'bg' ? c.name_bg : c.name_en;
      select.appendChild(opt);
    });
  });
}

// ---------------------------------------------------------------------------
// 9. Populate city dropdown for a given country code
//    Returns mode: 'select' | 'text'
// ---------------------------------------------------------------------------
function populateCities(countryCode, citySelect, cityText, labelId) {
  const cities = CITIES_BY_COUNTRY[countryCode];

  if (cities && cities.length > 0) {
    // Show select, hide text
    citySelect.hidden = false;
    cityText.hidden   = true;
    cityText.value    = '';
    cityText.removeAttribute('required');
    citySelect.setAttribute('required', '');

    // Repopulate
    while (citySelect.options.length > 1) citySelect.remove(1);
    cities.forEach(city => {
      const opt = document.createElement('option');
      opt.value = city.en;
      opt.textContent = lang === 'bg' ? city.bg : city.en;
      citySelect.appendChild(opt);
    });

    // Add "Other (specify)" option
    const otherOpt = document.createElement('option');
    otherOpt.value = '__other__';
    otherOpt.textContent = t.opt_other_city;
    citySelect.appendChild(otherOpt);

    citySelect.value = '';
    return 'select';
  } else {
    // No preset cities — show free-text
    citySelect.hidden = true;
    citySelect.value  = '';
    citySelect.removeAttribute('required');
    cityText.hidden   = false;
    cityText.setAttribute('required', '');
    cityText.value    = '';
    return 'text';
  }
}

// ---------------------------------------------------------------------------
// 10. Attach event listeners
// ---------------------------------------------------------------------------
function attachEventListeners() {
  // Service type tabs
  document.querySelectorAll('input[name="service_type"]').forEach(radio => {
    radio.addEventListener('change', onServiceTypeChange);
  });

  // Country change
  if (originCountrySelect) originCountrySelect.addEventListener('change', onOriginCountryChange);
  if (destCountrySelect)   destCountrySelect.addEventListener('change', onDestCountryChange);

  // City selects (including "Other" detection)
  if (originCitySelect) {
    originCitySelect.addEventListener('change', e => {
      if (e.target.value === '__other__') {
        originCitySelect.hidden = true;
        originCitySelect.value = '';
        originCityText.hidden = false;
        originCityText.setAttribute('required', '');
        originCitySelect.removeAttribute('required');
        originCityText.focus();
        originCityMode = 'text';
      }
      onInputChange();
    });
  }

  if (destCitySelect) {
    destCitySelect.addEventListener('change', e => {
      if (e.target.value === '__other__') {
        destCitySelect.hidden = true;
        destCitySelect.value = '';
        destCityText.hidden = false;
        destCityText.setAttribute('required', '');
        destCitySelect.removeAttribute('required');
        destCityText.focus();
        destCityMode = 'text';
      }
      onInputChange();
    });
  }

  // All form inputs — debounced calculation
  if (calcForm) {
    calcForm.addEventListener('input', onInputChange);
    calcForm.addEventListener('change', onInputChange);
  }

  // Pallet type radios
  document.querySelectorAll('input[name="pallet_type"]').forEach(r => r.addEventListener('change', onNonPalletChange));

  // Optional toggle
  // Calculate button
  if (btnCalculate) btnCalculate.addEventListener('click', onCalculateClick);

  // Quote CTA buttons
  if (btnGetQuote)       btnGetQuote.addEventListener('click', openQuotePanel);
  if (btnGetQuoteNorate) btnGetQuoteNorate.addEventListener('click', openQuotePanel);

  // Quote form submit
  if (quoteForm) quoteForm.addEventListener('submit', onQuoteSubmit);

  // Clear errors on input for quote fields
  ['qf-name', 'qf-email', 'qf-phone', 'qf-notes'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', () => clearFieldError(id));
  });
}

// ---------------------------------------------------------------------------
// 11. Service type change
// ---------------------------------------------------------------------------
function onServiceTypeChange(e) {
  currentServiceType = e.target.value;

  // Update active tab class
  document.querySelectorAll('.service-tabs__option').forEach(label => {
    label.classList.remove('service-tabs__option--active');
  });
  e.target.closest('.service-tabs__option').classList.add('service-tabs__option--active');

  // Show/hide field groups
  if (currentServiceType === 'ftl') {
    ftlFields.hidden = false;
    ltlFields.hidden = true;
  } else {
    ftlFields.hidden = true;
    ltlFields.hidden = false;
  }

  // Reset estimate if switching
  showEstimateState('empty');
  onInputChange();
}

// ---------------------------------------------------------------------------
// 12. Country change handlers
// ---------------------------------------------------------------------------
function onOriginCountryChange() {
  const code = originCountrySelect.value;
  if (code) {
    originCityMode = populateCities(code, originCitySelect, originCityText, 'label-origin-city');
  } else {
    originCitySelect.hidden = false;
    originCityText.hidden   = true;
    while (originCitySelect.options.length > 1) originCitySelect.remove(1);
    originCitySelect.value  = '';
  }
  onInputChange();
}

function onDestCountryChange() {
  const code = destCountrySelect.value;
  if (code) {
    destCityMode = populateCities(code, destCitySelect, destCityText, 'label-destination');
  } else {
    destCitySelect.hidden = false;
    destCityText.hidden   = true;
    while (destCitySelect.options.length > 1) destCitySelect.remove(1);
    destCitySelect.value  = '';
  }
  onInputChange();
}

// ---------------------------------------------------------------------------
// 13. Pallet type radio change
// ---------------------------------------------------------------------------
function onNonPalletChange() {
  const selected = document.querySelector('input[name="pallet_type"]:checked');
  const isNonPallet = selected && selected.value === 'non_pallet';
  if (dimFields) dimFields.hidden = !isNonPallet;

  // Lock/unlock number of pallets field
  const numPalletsEl = document.getElementById('num_pallets');
  if (numPalletsEl) {
    numPalletsEl.disabled = isNonPallet;
    if (isNonPallet) numPalletsEl.value = '';
  }

  // Toggle required on dimension fields
  const lenEl = document.getElementById('cargo_length_cm');
  const widEl = document.getElementById('cargo_width_cm');
  if (lenEl) { isNonPallet ? lenEl.setAttribute('required', '') : lenEl.removeAttribute('required'); }
  if (widEl) { isNonPallet ? widEl.setAttribute('required', '') : widEl.removeAttribute('required'); }

  onInputChange();
}

// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// 14. Input change — reset estimate so stale results don't persist
// ---------------------------------------------------------------------------
function onInputChange() {
  clearCalcFieldErrors();
  if (lastEstimate !== null) {
    showEstimateState('empty');
  }
}

// ---------------------------------------------------------------------------
// 16. Collect form data
// ---------------------------------------------------------------------------
function getOriginCity() {
  if (!originCitySelect.hidden && originCitySelect.value && originCitySelect.value !== '__other__') {
    return originCitySelect.value;
  }
  return originCityText.value.trim();
}

function getDestCity() {
  if (!destCitySelect.hidden && destCitySelect.value && destCitySelect.value !== '__other__') {
    return destCitySelect.value;
  }
  return destCityText.value.trim();
}

function getCityDisplayName(countryCode, cityEnValue) {
  const cities = CITIES_BY_COUNTRY[countryCode];
  if (!cities) return cityEnValue;
  const found = cities.find(c => c.en === cityEnValue);
  if (!found) return cityEnValue;
  return lang === 'bg' ? found.bg : found.en;
}

function collectFormData() {
  const isLtl = currentServiceType === 'ltl';
  const palletRadio    = document.querySelector('input[name="pallet_type"]:checked');
  const palletRadioVal = palletRadio ? palletRadio.value : 'eur';
  const isNonPallet    = palletRadioVal === 'non_pallet';

  const truckTypeEl    = document.getElementById('truck_type');
  const numPalletsEl   = document.getElementById('num_pallets');
  const weightLtlEl   = document.getElementById('total_weight_kg');
  const cargoLengthEl  = document.getElementById('cargo_length_cm');
  const cargoWidthEl   = document.getElementById('cargo_width_cm');
  const cargoWeightEl  = document.getElementById('cargo_weight_kg');
  const loadDateEl     = document.getElementById('load_date');
  const flexibilityEl  = document.querySelector('input[name="date_flexibility"]:checked');

  return {
    service_type:         currentServiceType,
    origin_country:       originCountrySelect ? originCountrySelect.value : '',
    origin_city:          getOriginCity(),
    destination_country:  destCountrySelect  ? destCountrySelect.value  : '',
    destination:          getDestCity(),
    num_pallets:          isLtl && !isNonPallet && numPalletsEl  ? (parseInt(numPalletsEl.value, 10)  || null) : null,
    total_weight_kg:      isLtl && weightLtlEl  ? (parseFloat(weightLtlEl.value)  || null) : null,
    pallet_type:          isLtl && !isNonPallet ? palletRadioVal : null,
    non_pallet_cargo:     isLtl ? isNonPallet : false,
    cargo_length_cm:      isLtl && isNonPallet && cargoLengthEl  ? (parseInt(cargoLengthEl.value, 10) || null) : null,
    cargo_width_cm:       isLtl && isNonPallet && cargoWidthEl   ? (parseInt(cargoWidthEl.value, 10)  || null) : null,
    cargo_weight_kg:      !isLtl && cargoWeightEl ? (parseFloat(cargoWeightEl.value) || null) : null,
    truck_type:           !isLtl && truckTypeEl   ? (truckTypeEl.value || 'standard')         : null,
    load_date:            loadDateEl   ? (loadDateEl.value || null) : null,
    date_flexibility:     flexibilityEl ? flexibilityEl.value : null,
    language:             lang,
  };
}

// ---------------------------------------------------------------------------
// 17. Silent form validation (no error display)
// ---------------------------------------------------------------------------
function isFormValid() {
  const d = collectFormData();

  if (!d.service_type) return false;
  if (!d.origin_country || !d.origin_city) return false;
  if (!d.destination_country || !d.destination) return false;

  if (d.service_type === 'ltl') {
    if (!d.total_weight_kg || d.total_weight_kg <= 0) return false;
    if (d.non_pallet_cargo) {
      if (!d.cargo_length_cm || d.cargo_length_cm <= 0) return false;
      if (!d.cargo_width_cm  || d.cargo_width_cm  <= 0) return false;
    } else {
      if (!d.num_pallets || d.num_pallets < 1 || d.num_pallets > 33) return false;
    }
  } else {
    if (!d.cargo_weight_kg || d.cargo_weight_kg <= 0) return false;
  }

  return true;
}

// ---------------------------------------------------------------------------
// 18. Backend API calculation
// ---------------------------------------------------------------------------
async function calculateViaBackend(data) {
  const response = await fetch('/api/calculate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      service_type:        data.service_type,
      origin_country:      data.origin_country,
      origin_city:         data.origin_city,
      destination_country: data.destination_country,
      destination:         data.destination,
      num_pallets:         data.num_pallets,
      total_weight_kg:     data.total_weight_kg,
      pallet_type:         data.pallet_type,
      non_pallet_cargo:    data.non_pallet_cargo,
      cargo_length_cm:     data.cargo_length_cm,
      cargo_width_cm:      data.cargo_width_cm,
      cargo_weight_kg:     data.cargo_weight_kg,
      truck_type:          data.truck_type,
      date_flexibility:    data.date_flexibility,
      language:            data.language,
    }),
  });

  if (!response.ok) {
    throw new Error(`Backend returned ${response.status}`);
  }

  return await response.json();
}

// ---------------------------------------------------------------------------
// 18b. Calculate button handler
// ---------------------------------------------------------------------------
async function onCalculateClick() {
  if (!isFormValid()) {
    showValidationErrors();
    showEstimateState('empty');
    return;
  }

  showEstimateState('loading');
  btnCalculate.disabled = true;

  try {
    const data = collectFormData();
    const result = await calculateViaBackend(data);

    if (result.no_rate) {
      showEstimateState('no-rate');
      return;
    }

    if (result.success && result.min_price != null) {
      lastEstimate = {
        min: result.min_price,
        max: result.max_price,
      };
      showEstimateState('price', result);
    } else {
      showEstimateState('no-rate');
    }
  } catch (err) {
    console.error('Backend calculation failed:', err);
    showEstimateState('error');
  } finally {
    btnCalculate.disabled = false;
  }
}

function showValidationErrors() {
  const d = collectFormData();
  clearCalcFieldErrors();

  if (!d.origin_country)       showFieldError('origin_country', t.err_origin_country);
  if (!d.origin_city)          showFieldError(originCitySelect.hidden ? 'origin_city_text' : 'origin_city_select', t.err_origin_city);
  if (!d.destination_country)  showFieldError('destination_country', t.err_dest_country);
  if (!d.destination)          showFieldError(destCitySelect.hidden ? 'destination_text' : 'destination_select', t.err_destination);

  if (d.service_type === 'ltl') {
    if (!d.total_weight_kg || d.total_weight_kg <= 0) showFieldError('total_weight_kg', t.err_weight_ltl);
    if (d.non_pallet_cargo) {
      if (!d.cargo_length_cm || d.cargo_length_cm <= 0) showFieldError('cargo_length_cm', t.err_cargo_length);
      if (!d.cargo_width_cm  || d.cargo_width_cm  <= 0) showFieldError('cargo_width_cm',  t.err_cargo_width);
    } else {
      if (!d.num_pallets || d.num_pallets < 1 || d.num_pallets > 33) showFieldError('num_pallets', t.err_num_pallets);
    }
  } else {
    if (!d.cargo_weight_kg || d.cargo_weight_kg <= 0) showFieldError('cargo_weight_kg', t.err_weight_ftl);
  }
}

function clearCalcFieldErrors() {
  const ids = [
    'origin_country', 'origin_city_select', 'origin_city_text',
    'destination_country', 'destination_select', 'destination_text',
    'num_pallets', 'total_weight_kg', 'cargo_length_cm', 'cargo_width_cm',
    'cargo_weight_kg',
  ];
  ids.forEach(id => clearFieldError(id));
}

// ---------------------------------------------------------------------------
// 19. Estimate card state management
// ---------------------------------------------------------------------------
function showEstimateState(state, data) {
  // Hide all state panels
  stateEmpty.hidden   = true;
  stateLoading.hidden = true;
  statePrice.hidden   = true;
  stateNoRate.hidden  = true;
  stateError.hidden   = true;

  // Remove modifier classes
  estimateCard.classList.remove(
    'estimate-card--empty',
    'estimate-card--loading',
    'estimate-card--price',
    'estimate-card--norate',
    'estimate-card--error'
  );

  switch (state) {
    case 'empty':
      stateEmpty.hidden = false;
      estimateCard.classList.add('estimate-card--empty');
      lastEstimate = null;
      // Hide quote panel when resetting
      if (quotePanel) quotePanel.hidden = true;
      break;

    case 'loading':
      stateLoading.hidden = false;
      estimateCard.classList.add('estimate-card--loading');
      break;

    case 'price':
      statePrice.hidden = false;
      estimateCard.classList.add('estimate-card--price');
      if (data && priceMainEl) {
        priceMainEl.textContent = formatPriceRange(data.min_price, data.max_price, 'EUR');
      }
      if (priceEurEl) {
        priceEurEl.textContent = '';
      }
      if (estimateNoteEl) estimateNoteEl.textContent = t.disclaimer;
      break;

    case 'no-rate':
      stateNoRate.hidden = false;
      estimateCard.classList.add('estimate-card--norate');
      break;

    case 'error':
      stateError.hidden = false;
      estimateCard.classList.add('estimate-card--error');
      break;
  }
}

function formatPriceRange(min, max, currency) {
  const fmt = n => n.toLocaleString('bg-BG', { maximumFractionDigits: 0 });
  return `${fmt(min)} \u2013 ${fmt(max)} ${currency}`;
}

// ---------------------------------------------------------------------------
// 20. Quote panel
// ---------------------------------------------------------------------------
function openQuotePanel() {
  if (!quotePanel) return;

  // Update hidden fields
  if (qfLang)     qfLang.value     = lang;
  if (qfMinPrice) qfMinPrice.value = lastEstimate ? lastEstimate.min : '';
  if (qfMaxPrice) qfMaxPrice.value = lastEstimate ? lastEstimate.max : '';

  // Build cargo summary
  buildQuoteSummary();

  // Show panel
  quotePanel.hidden = false;

  // Update aria-expanded on both CTA buttons
  if (btnGetQuote)       btnGetQuote.setAttribute('aria-expanded', 'true');
  if (btnGetQuoteNorate) btnGetQuoteNorate.setAttribute('aria-expanded', 'true');

  // Scroll to panel
  quotePanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function buildQuoteSummary() {
  if (!quoteSummary) return;

  const d = collectFormData();
  const parts = [];

  // Service type
  parts.push(d.service_type.toUpperCase());

  // Route — show localized city name if available
  const originDisplay = getCityDisplayName(d.origin_country, d.origin_city);
  const destDisplay   = getCityDisplayName(d.destination_country, d.destination);
  const originLabel = `${d.origin_country} ${originDisplay}`;
  const destLabel   = `${d.destination_country} ${destDisplay}`;
  parts.push(`${originLabel} \u2192 ${destLabel}`);

  // Cargo details
  if (d.service_type === 'ltl') {
    if (d.non_pallet_cargo) {
      parts.push(`non-pallet ${d.cargo_length_cm || '?'}\u00d7${d.cargo_width_cm || '?'} cm`);
    } else {
      parts.push(`${d.num_pallets || '?'} pallets`);
    }
    if (d.total_weight_kg) parts.push(`${d.total_weight_kg.toLocaleString()} kg`);
  } else {
    if (d.cargo_weight_kg) parts.push(`${d.cargo_weight_kg.toLocaleString()} kg`);
    if (d.truck_type) {
      const truckLabels = { standard: t.opt_curtainsider, refrigerated: t.opt_refrigerated, flatbed: t.opt_flatbed };
      parts.push(truckLabels[d.truck_type] || d.truck_type);
    }
  }

  quoteSummary.textContent = parts.join(' | ');
}

// ---------------------------------------------------------------------------
// 21. Quote form submission
// ---------------------------------------------------------------------------
async function onQuoteSubmit(e) {
  e.preventDefault();

  const name  = qfName  ? qfName.value.trim()  : '';
  const email = qfEmail ? qfEmail.value.trim()  : '';
  const phone = qfPhone ? qfPhone.value.trim()  : '';
  const notes = qfNotes ? qfNotes.value.trim()  : '';

  let valid = true;

  // Validate name
  if (name.length < 2 || name.length > 100) {
    showFieldError('qf-name', t.err_name);
    valid = false;
  }

  // Validate at least one contact
  if (!email && !phone) {
    showFieldError('qf-email', t.err_contact);
    showFieldError('qf-phone', t.err_contact);
    valid = false;
  } else {
    // Validate email format if provided
    if (email && !isValidEmail(email)) {
      showFieldError('qf-email', t.err_email_format);
      valid = false;
    }
  }

  // Validate notes length
  if (notes.length > 500) {
    showFieldError('qf-notes', t.err_notes_length);
    valid = false;
  }

  if (!valid) return;

  // Disable submit button during request
  if (btnSubmit) {
    btnSubmit.disabled = true;
    btnSubmit.textContent = lang === 'bg' ? '\u0418\u0437\u043f\u0440\u0430\u0449\u0430...' : 'Submitting...';
  }

  const payload = {
    ...collectFormData(),
    name,
    email,
    phone,
    notes,
    language:         lang,
    shown_min_price:  lastEstimate ? lastEstimate.min : null,
    shown_max_price:  lastEstimate ? lastEstimate.max : null,
  };

  try {
    const response = await fetch('/api/quote', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (response.ok && data.success) {
      // Success
      if (quoteForm)    quoteForm.hidden    = true;
      if (quoteSuccess) {
        quoteSuccess.hidden = false;
        const successP = quoteSuccess.querySelector('p');
        if (successP) successP.textContent = t.submit_success;
      }
      // Update CTA buttons
      if (btnGetQuote) {
        btnGetQuote.textContent = t.quote_submitted;
        btnGetQuote.disabled    = true;
      }
      if (btnGetQuoteNorate) {
        btnGetQuoteNorate.textContent = t.quote_submitted;
        btnGetQuoteNorate.disabled    = true;
      }
    } else {
      // Server-side error
      showSubmitError(t.submit_error);
      if (btnSubmit) {
        btnSubmit.disabled    = false;
        btnSubmit.textContent = t.btn_submit;
      }
    }

  } catch (err) {
    showSubmitError(t.submit_error);
    if (btnSubmit) {
      btnSubmit.disabled    = false;
      btnSubmit.textContent = t.btn_submit;
    }
  }
}

function showSubmitError(message) {
  let errEl = document.getElementById('quote-submit-error');
  if (!errEl) {
    errEl = document.createElement('p');
    errEl.id = 'quote-submit-error';
    errEl.setAttribute('role', 'alert');
    errEl.className = 'form-error quote-submit-error';
    if (btnSubmit) btnSubmit.parentNode.insertBefore(errEl, btnSubmit);
  }
  errEl.textContent = message;
}

// ---------------------------------------------------------------------------
// 22. Field-level validation helpers
// ---------------------------------------------------------------------------
function showFieldError(fieldId, message) {
  const field = document.getElementById(fieldId);
  if (!field) return;

  field.setAttribute('aria-invalid', 'true');
  field.classList.add('field--error');

  let errorEl = document.getElementById(`${fieldId}-error`);
  if (!errorEl) {
    errorEl = document.createElement('span');
    errorEl.id = `${fieldId}-error`;
    errorEl.setAttribute('role', 'alert');
    errorEl.className = 'form-error';
    field.parentNode.appendChild(errorEl);
  }
  errorEl.textContent = message;
}

function clearFieldError(fieldId) {
  const field = document.getElementById(fieldId);
  if (!field) return;

  field.removeAttribute('aria-invalid');
  field.classList.remove('field--error');

  const errorEl = document.getElementById(`${fieldId}-error`);
  if (errorEl) errorEl.textContent = '';
}

// ---------------------------------------------------------------------------
// 23. Email validation helper
// ---------------------------------------------------------------------------
function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
