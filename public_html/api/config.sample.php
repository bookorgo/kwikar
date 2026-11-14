<?php
// KWIKAR server keys. Save a copy of this file as  kwikar-config.php  in your Hostinger HOME folder
// (the top folder in File Manager, above "domains"), then paste the keys below.
// Keeping it outside public_html means Git deployments never touch it. Never send these keys by chat or email.
return [
    // TravelDesk API key (tours and prices)
    'KWIKAR_API_KEY' => '',

    // Nomod Hosted Checkout (online payment for activities). Leave empty to keep "Pay now" switched off.
    'NOMOD_API_KEY' => '',          // Nomod > Settings > Apps & APIs > Nomod Hosted Checkout > API key
    'NOMOD_WEBHOOK_SECRET' => '',   // Nomod > Webhooks > your webhook > signing secret (starts with whsec_)
    // 'PAYMENTS_ENABLED' => false,  // uncomment to switch "Pay now" off without removing the key
];
