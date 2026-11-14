<?php
/**
 * KWIKAR — online payment for activities (Nomod Hosted Checkout)
 *
 *   GET  /api/pay.php?action=ready           → {"ok":true,"enabled":bool}  (is "Pay now" switched on?)
 *   POST /api/pay.php?action=create  (JSON)  → {"ok":true,"url":"https://...nomod..."}  (redirect the customer there)
 *   GET  /api/pay.php?action=status&ref=KW-… → order status for the payment result page
 *
 * The price is NEVER taken from the browser: it is recalculated here from the live TravelDesk
 * tour data (the same /api/tours.php feed the site uses). Keys live only in kwikar-config.php
 * outside public_html:  'NOMOD_API_KEY' => 'sk_live_…', 'NOMOD_WEBHOOK_SECRET' => 'whsec_…'.
 * Without NOMOD_API_KEY (or with 'PAYMENTS_ENABLED' => false) online payment stays off.
 * Orders are saved as JSON outside public_html (kwikar-orders/), never in the website folder.
 */
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');

require __DIR__ . '/pay-lib.php';

$action = (string)($_GET['action'] ?? '');

if ($action === 'ready') {
    out(['ok' => true, 'enabled' => kw_pay_enabled()]);
}

if ($action === 'status') {
    $ref = (string)($_GET['ref'] ?? '');
    $order = kw_order_load($ref);
    if (!$order) out(['ok' => false, 'error' => 'Order not found'], 404);
    $order = kw_order_refresh($order);   // asks Nomod for the real status (paid / cancelled / expired)
    out(['ok' => true, 'order' => kw_order_public($order)]);
}

if ($action !== 'create' || ($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') out(['ok' => false, 'error' => 'Bad request'], 400);
if (!kw_pay_enabled()) out(['ok' => false, 'error' => 'Online payment is not available. Please book on WhatsApp.'], 503);
if (!kw_rate_ok('create', 20, 3600)) out(['ok' => false, 'error' => 'Too many attempts. Please try again later or book on WhatsApp.'], 429);

$raw = file_get_contents('php://input', false, null, 0, 20000);
$in = json_decode((string)$raw, true);
if (!is_array($in)) out(['ok' => false, 'error' => 'Bad request'], 400);

/* ---------- input ---------- */
$tourId   = (string)($in['tour_id'] ?? '');
$offerId  = (string)($in['offer_id'] ?? '');
$date     = (string)($in['date'] ?? '');
$adults   = (int)($in['adults'] ?? 0);
$children = (int)($in['children'] ?? 0);
$infants  = (int)($in['infants'] ?? 0);
$ages     = array_values(array_map('intval', is_array($in['ages'] ?? null) ? $in['ages'] : []));
$c        = is_array($in['customer'] ?? null) ? $in['customer'] : [];
$name     = clean_text($c['name'] ?? '', 80);
$phone    = clean_text($c['phone'] ?? '', 30);
$email    = clean_text($c['email'] ?? '', 120);
$res      = clean_text($c['residence'] ?? '', 60);
$pickup   = clean_text($c['pickup'] ?? '', 200);
$special  = clean_text($c['special'] ?? '', 500);
$src      = preg_match('/^[GFMSRD]$/', (string)($in['src'] ?? '')) ? (string)$in['src'] : 'D';

if (!preg_match('/^[1-9]\d{0,8}$/', $tourId)) fail('Invalid activity.');
if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $date)) fail('Please choose a date.');
if ($adults < 1 || $adults > 50 || $children < 0 || $children > 50 || $infants < 0 || $infants > 20) fail('Please check the number of guests.');
if (count($ages) !== $children) fail('Please add the age of each child.');
if (mb_strlen($name) < 2) fail('Please enter your full name.');
if (!preg_match('/^\+?[0-9 ()-]{7,30}$/', $phone)) fail('Please enter a valid mobile number.');
if ($email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) fail('Please check your email address.');

/* ---------- live tour data and price ---------- */
$tour = kw_tour($tourId);
if (!$tour) fail('This activity could not be loaded. Please book on WhatsApp.', 502);
$offer = null;
foreach (($tour['offers'] ?? []) as $o) { if ((string)($o['id'] ?? '') === $offerId) { $offer = $o; break; } }
if (!$offer) fail('Please choose an option again.');

$check = kw_check_offer($offer, $date, $adults, $children, $infants);
if ($check !== null) fail($check);
$total = kw_total($offer, $date, $adults, $children);
if ($total === null || $total <= 0) fail('This option has no online price. Please book on WhatsApp.');

/* ---------- order + Nomod checkout ---------- */
$ref = kw_new_ref();
$order = [
    'ref' => $ref, 'status' => 'created', 'created' => gmdate('c'), 'src' => $src,
    'tour' => ['id' => (int)$tourId, 'name' => (string)($tour['name'] ?? ''), 'url' => 'https://kwikar.com' . (string)($in['path'] ?? '')],
    'offer' => ['id' => $offerId, 'name' => (string)($offer['name'] ?? '')],
    'date' => $date, 'adults' => $adults, 'children' => $children, 'infants' => $infants, 'ages' => $ages,
    'total' => $total, 'currency' => 'AED',
    'customer' => ['name' => $name, 'phone' => $phone, 'email' => $email, 'residence' => $res, 'pickup' => $pickup, 'special' => $special],
    'cancellation' => array_slice(array_map('strval', $tour['cancellation'] ?? []), 0, 6),
];
if (!preg_match('#^/activities/[a-z0-9/-]{3,200}$#', (string)($in['path'] ?? ''))) $order['tour']['url'] = 'https://kwikar.com/activities';

$parts = preg_split('/\s+/', $name, 2);
$items = [];
$period = kw_period($offer, $date);
if ((float)($period['adult'] ?? 0) > 0) $items[] = kw_item('adult', 'Adult', $adults, (float)$period['adult']);
if ($children > 0 && (float)($period['child'] ?? 0) > 0) $items[] = kw_item('child', 'Child', $children, (float)$period['child']);
if ((float)($period['trip'] ?? 0) > 0) $items[] = kw_item('trip', 'Per booking', 1, (float)$period['trip']);
foreach ($items as &$it) { $it['name'] = mb_substr($order['tour']['name'] . ' – ' . $order['offer']['name'] . ' (' . $it['name'] . ')', 0, 250); }
unset($it);

$base = 'https://kwikar.com/payment';
$session = kw_nomod('POST', '/checkout', [
    'reference_id' => $ref,
    'amount' => number_format($total, 2, '.', ''),
    'currency' => 'AED',
    'items' => $items,
    'customer' => array_filter(['first_name' => $parts[0] ?? $name, 'last_name' => $parts[1] ?? '', 'email' => $email, 'phone_number' => preg_replace('/[^0-9+]/', '', $phone)]),
    'success_url' => $base . '/success?ref=' . $ref,
    'failure_url' => $base . '/failed?ref=' . $ref,
    'cancelled_url' => $base . '/failed?ref=' . $ref . '&cancelled=1',
    'metadata' => ['kwref' => $ref, 'tour' => (string)$tourId, 'date' => $date, 'src' => $src],
]);
if (!$session || empty($session['url']) || empty($session['id'])) {
    kw_log('nomod create failed for ' . $ref);
    fail('Payment could not be started. Please try again or book on WhatsApp.', 502);
}
$order['checkout_id'] = (string)$session['id'];
kw_order_save($order);
out(['ok' => true, 'ref' => $ref, 'url' => (string)$session['url']]);
