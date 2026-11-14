<?php
/**
 * Shared helpers for KWIKAR online payment (pay.php and nomod-webhook.php). Not a public endpoint.
 */
declare(strict_types=1);

if (basename($_SERVER['SCRIPT_FILENAME'] ?? '') === 'pay-lib.php') { http_response_code(404); exit; }

date_default_timezone_set('Asia/Dubai');
const KW_NOMOD_API   = 'https://api.nomod.com/v1';
const KW_NOTIFY_TO   = 'info@kwikar.com';
const KW_MIN_HOURS   = 12;     // online payment only when the activity starts at least 12 hours from now
const KW_DEFAULT_START = '09:00';  // assumed start time when the supplier gives no time slot

$KW_CONFIG = [];
foreach ([dirname(__DIR__, 4) . '/kwikar-config.php', dirname(__DIR__, 2) . '/kwikar-config.php', __DIR__ . '/config.php'] as $f) {
    if (@is_file($f)) { $c = require $f; if (is_array($c)) $KW_CONFIG = $c; break; }
}

function cfg(string $k, $default = '') { global $KW_CONFIG; return $KW_CONFIG[$k] ?? $default; }

function kw_pay_enabled(): bool {
    return trim((string)cfg('NOMOD_API_KEY')) !== '' && cfg('PAYMENTS_ENABLED', true) !== false;
}

function out(array $p, int $code = 200): void { http_response_code($code); echo json_encode($p, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES); exit; }
function fail(string $msg, int $code = 400): void { out(['ok' => false, 'error' => $msg], $code); }

function clean_text($v, int $max): string {
    $s = trim(preg_replace('/[\x00-\x1F\x7F]+/u', ' ', (string)$v) ?? '');
    return mb_substr($s, 0, $max);
}

function kw_data_dir(): string {
    static $dir = null;
    if ($dir !== null) return $dir;
    foreach ([dirname(__DIR__, 4) . '/kwikar-orders', __DIR__ . '/cache/orders'] as $d) {
        if (is_dir($d) || @mkdir($d, 0700, true)) { if (is_writable($d)) { $dir = $d; return $dir; } }
    }
    $dir = __DIR__ . '/cache';
    return $dir;
}

function kw_log(string $line): void {
    @file_put_contents(kw_data_dir() . '/payments.log', gmdate('c') . ' ' . $line . "\n", FILE_APPEND | LOCK_EX);
}

function kw_rate_ok(string $bucket, int $max, int $window): bool {
    $ip = preg_replace('/[^0-9a-f:.]/i', '', (string)($_SERVER['REMOTE_ADDR'] ?? 'x'));
    $f = kw_data_dir() . '/rate-' . $bucket . '-' . md5($ip) . '.json';
    $now = time();
    $hits = array_values(array_filter((array)json_decode((string)@file_get_contents($f), true), fn($t) => is_int($t) && $t > $now - $window));
    if (count($hits) >= $max) return false;
    $hits[] = $now;
    @file_put_contents($f, json_encode($hits), LOCK_EX);
    return true;
}

/* ---------- tour data (same feed as the website) ---------- */
function kw_tour(string $id): ?array {
    $cache = __DIR__ . '/cache/tour-' . $id . '.json';
    $c = @json_decode((string)@file_get_contents($cache), true);
    if (is_array($c) && isset($c['savedAt'], $c['payload']['ok']) && time() - (int)$c['savedAt'] < 600 && $c['payload']['ok']) return $c['payload'];
    $ch = curl_init('https://kwikar.com/api/tours.php?id=' . $id);
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 25, CURLOPT_HTTPHEADER => ['Accept: application/json']]);
    $body = curl_exec($ch);
    curl_close($ch);
    $d = $body ? json_decode((string)$body, true) : null;
    if (is_array($d) && !empty($d['ok']) && empty($d['stale'])) return $d;
    return null;   // never charge from old (stale) supplier data
}

function kw_period(array $o, string $date): ?array {
    $pp = $o['pricingPeriods'] ?? [];
    if (!$pp) return ['adult' => (float)($o['adultBase'] ?? 0), 'child' => (float)($o['child'] ?? 0), 'trip' => (float)($o['tripFee'] ?? 0)];
    foreach ($pp as $p) { if (($p['dateStart'] ?? '') <= $date && $date <= ($p['dateEnd'] ?? '')) return $p; }
    return null;
}

function kw_start_time(array $o): string {
    $best = null;
    foreach (($o['timeSlots'] ?? []) as $slot) {
        if (preg_match('/\b(\d{1,2})[:.](\d{2})\s*(am|pm)?/i', (string)$slot, $m)) {
            $h = (int)$m[1]; $min = (int)$m[2]; $ap = strtolower($m[3] ?? '');
            if ($ap === 'pm' && $h < 12) $h += 12; if ($ap === 'am' && $h === 12) $h = 0;
            if ($h < 24 && $min < 60) { $t = sprintf('%02d:%02d', $h, $min); if ($best === null || $t < $best) $best = $t; }
        }
    }
    return $best ?? KW_DEFAULT_START;
}

/** Same rules as the booking sheet (kw.js), plus the 12-hour rule. Returns an error message or null. */
function kw_check_offer(array $o, string $date, int $adults, int $children, int $infants): ?string {
    $start = strtotime($date . ' ' . kw_start_time($o));
    if (!$start) return 'Please choose a date.';
    if ($start - time() < KW_MIN_HOURS * 3600) return 'Online payment closes ' . KW_MIN_HOURS . ' hours before the activity. Please send your request on WhatsApp and our team will confirm.';
    if ($start - time() > 400 * 86400) return 'Please choose a date within the next year.';
    $days = array_map('strtolower', array_map('strval', $o['daysOffered'] ?? []));
    if ($days && !in_array(strtolower(date('l', $start)), $days, true)) return 'This option is not offered on that day of the week.';
    $party = $adults + $children + $infants;
    if (isset($o['minPeople']) && $o['minPeople'] !== null && $party < (int)$o['minPeople']) return 'Minimum ' . (int)$o['minPeople'] . ' guests for this option.';
    if (isset($o['maxPeople']) && $o['maxPeople'] !== null && $party > (int)$o['maxPeople']) return 'Maximum ' . (int)$o['maxPeople'] . ' guests for this option.';
    if ($children > 0 && ($o['childrenAllowed'] ?? null) === false) return 'Children are not allowed on this option.';
    $p = kw_period($o, $date);
    if (!$p) return 'This option has no price for that date.';
    $tripOnly = !(float)($p['adult'] ?? 0) && !(float)($p['child'] ?? 0) && (float)($p['trip'] ?? 0) > 0;
    if (!$tripOnly && !((float)($p['adult'] ?? 0) > 0)) return 'Adult price on request for this option. Please book on WhatsApp.';
    if (!$tripOnly && $children > 0 && !((float)($p['child'] ?? 0) > 0)) return 'Child price on request for this option. Please book on WhatsApp.';
    return null;
}

function kw_total(array $o, string $date, int $adults, int $children): ?float {
    $p = kw_period($o, $date);
    if (!$p) return null;
    return round((float)($p['adult'] ?? 0) * $adults + (float)($p['child'] ?? 0) * $children + (float)($p['trip'] ?? 0), 2);
}

function kw_item(string $id, string $name, int $qty, float $unit): array {
    $tot = number_format($unit * $qty, 2, '.', '');
    return ['item_id' => $id, 'name' => $name, 'quantity' => $qty, 'unit_amount' => number_format($unit, 2, '.', ''),
            'discount_type' => 'flat', 'discount_amount' => '0.00', 'total_amount' => $tot, 'net_amount' => $tot];
}

/* ---------- orders ---------- */
function kw_new_ref(): string {
    $chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    $s = '';
    for ($i = 0; $i < 8; $i++) $s .= $chars[random_int(0, strlen($chars) - 1)];
    return 'KW-' . date('ymd') . '-' . $s;
}
function kw_valid_ref(string $ref): bool { return (bool)preg_match('/^KW-\d{6}-[A-Z2-9]{8}$/', $ref); }
function kw_order_file(string $ref): string { return kw_data_dir() . '/order-' . $ref . '.json'; }
function kw_order_load(string $ref): ?array {
    if (!kw_valid_ref($ref)) return null;
    $d = @json_decode((string)@file_get_contents(kw_order_file($ref)), true);
    return is_array($d) ? $d : null;
}
function kw_order_save(array $o): void {
    $f = kw_order_file($o['ref']);
    @file_put_contents($f, json_encode($o, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), LOCK_EX);
    @chmod($f, 0600);
}

function kw_nomod(string $method, string $path, ?array $body = null): ?array {
    $ch = curl_init(rtrim((string)cfg('NOMOD_API_BASE', KW_NOMOD_API), '/') . $path);
    $opt = [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 25, CURLOPT_CUSTOMREQUEST => $method,
            CURLOPT_HTTPHEADER => ['X-API-KEY: ' . trim((string)cfg('NOMOD_API_KEY')), 'Content-Type: application/json', 'Accept: application/json']];
    if ($body !== null) $opt[CURLOPT_POSTFIELDS] = json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    curl_setopt_array($ch, $opt);
    $res = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    if ($res === false || $code < 200 || $code >= 300) { kw_log("nomod $method $path -> HTTP $code " . substr((string)$res, 0, 300)); return null; }
    $d = json_decode((string)$res, true);
    return is_array($d) ? $d : null;
}

/** Ask Nomod for the checkout status; on first "paid" send the emails. */
function kw_order_refresh(array $o): array {
    if (empty($o['checkout_id']) || in_array($o['status'], ['refunded'], true)) return $o;
    if ($o['status'] === 'paid' && !empty($o['notified'])) return $o;
    $s = kw_nomod('GET', '/checkout/' . rawurlencode($o['checkout_id']));
    if (!$s) return $o;
    $st = (string)($s['status'] ?? '');
    if ($st === 'paid' && (float)($s['amount'] ?? 0) + 0.01 >= (float)$o['total']) {
        if ($o['status'] !== 'paid') { $o['status'] = 'paid'; $o['paid_at'] = gmdate('c'); }
        if (empty($o['notified'])) { kw_notify($o); $o['notified'] = gmdate('c'); }
        kw_order_save($o);
    } elseif (in_array($st, ['cancelled', 'expired'], true) && $o['status'] === 'created') {
        $o['status'] = $st; kw_order_save($o);
    }
    return $o;
}

function kw_guests(array $o): string {
    $g = $o['adults'] . ' adult' . ($o['adults'] == 1 ? '' : 's');
    if ($o['children']) $g .= ', ' . $o['children'] . ' child' . ($o['children'] == 1 ? '' : 'ren') . ' (ages ' . implode(', ', $o['ages']) . ')';
    if ($o['infants']) $g .= ', ' . $o['infants'] . ' infant' . ($o['infants'] == 1 ? '' : 's');
    return $g;
}

function kw_order_public(array $o): array {
    return ['ref' => $o['ref'], 'status' => $o['status'], 'tour' => $o['tour']['name'], 'url' => $o['tour']['url'], 'option' => $o['offer']['name'],
            'date' => $o['date'], 'date_text' => date('D j M Y', strtotime($o['date'])), 'guests' => kw_guests($o), 'total' => $o['total'], 'currency' => 'AED',
            'first_name' => preg_split('/\s+/', $o['customer']['name'])[0] ?? '', 'pickup' => $o['customer']['pickup'] !== '' ? $o['customer']['pickup'] : null,
            'cancellation' => $o['cancellation'] ?? []];
}

function kw_mail(string $to, string $subject, string $text): void {
    $headers = "From: KWIKAR <info@kwikar.com>\r\nReply-To: info@kwikar.com\r\nContent-Type: text/plain; charset=UTF-8";
    @mail($to, '=?UTF-8?B?' . base64_encode($subject) . '?=', $text, $headers);
}

function kw_notify(array $o): void {
    $c = $o['customer'];
    $lines = ['New PAID activity booking — book with the supplier now.', '',
        'Booking ref: ' . $o['ref'], 'Paid: AED ' . number_format((float)$o['total'], 2), 'Lead source: ' . $o['src'], '',
        'Activity: ' . $o['tour']['name'] . ' (TravelDesk tour ' . $o['tour']['id'] . ')', 'Option: ' . $o['offer']['name'] . ' (offer ' . $o['offer']['id'] . ')',
        'Date: ' . date('D j M Y', strtotime($o['date'])), 'Guests: ' . kw_guests($o), '',
        'Name: ' . $c['name'], 'Mobile / WhatsApp: ' . $c['phone'], 'Email: ' . ($c['email'] ?: '-'), 'Country of residence: ' . ($c['residence'] ?: '-'),
        'Pickup: ' . ($c['pickup'] ?: '-'), 'Requests: ' . ($c['special'] ?: '-'), '', 'Page: ' . $o['tour']['url'], 'Nomod checkout: ' . ($o['checkout_id'] ?? '-')];
    kw_mail(KW_NOTIFY_TO, 'PAID ' . $o['ref'] . ' – ' . $o['tour']['name'] . ' – ' . date('j M', strtotime($o['date'])), implode("\n", $lines));
    if ($c['email'] !== '') {
        $cust = ['Hi ' . (preg_split('/\s+/', $c['name'])[0] ?? '') . ',', '', 'Thank you for booking with KWIKAR. We have received your payment and your booking is confirmed.', '',
            'Booking ref: ' . $o['ref'], 'Activity: ' . $o['tour']['name'], 'Option: ' . $o['offer']['name'], 'Date: ' . date('D j M Y', strtotime($o['date'])),
            'Guests: ' . kw_guests($o), 'Paid: AED ' . number_format((float)$o['total'], 2), '',
            'Our team will send your tickets or meeting details on WhatsApp (+971 50 559 9243). If the supplier cannot confirm your date, you receive a full refund.', '',
            'Cancellation terms: ' . (implode(' ', $o['cancellation'] ?? []) ?: 'as shown on the activity page.'), 'Refunds go back to the same card within 7–10 working days.', '',
            'KWIKAR · Kwikar L.L.C-FZ · info@kwikar.com · +971 50 559 9243'];
        kw_mail($c['email'], 'Your KWIKAR booking ' . $o['ref'] . ' is confirmed', implode("\n", $cust));
    }
    kw_whatsapp_alert(implode("\n", [
        '*PAID ' . $o['ref'] . '* · AED ' . number_format((float)$o['total'], 2),
        $o['tour']['name'] . ' – ' . $o['offer']['name'],
        date('D j M Y', strtotime($o['date'])) . ' · ' . kw_guests($o),
        $c['name'] . ' · ' . $c['phone'],
        'Pickup: ' . ($c['pickup'] ?: '-'),
        'Requests: ' . ($c['special'] ?: '-'),
        'Source: ' . $o['src'] . ' · Book with TravelDesk now (tour ' . $o['tour']['id'] . ', offer ' . $o['offer']['id'] . ')',
    ]));
    kw_log('paid ' . $o['ref'] . ' AED ' . $o['total']);
}

/**
 * WhatsApp alert to the team (CallMeBot: free, sends to numbers that activated it).
 * kwikar-config.php: 'WHATSAPP_ALERTS' => ['+971XXXXXXXXX' => 'callmebot-apikey', ...]
 * Off when not set. A failed alert never stops the order (the email is already sent).
 */
function kw_whatsapp_alert(string $text): void {
    $list = cfg('WHATSAPP_ALERTS', []);
    if (!is_array($list)) return;
    foreach ($list as $phone => $key) {
        $phone = preg_replace('/[^0-9+]/', '', (string)$phone); $key = trim((string)$key);
        if ($phone === '' || $key === '') continue;
        $url = (string)cfg('WHATSAPP_ALERT_URL', 'https://api.callmebot.com/whatsapp.php') . '?' . http_build_query(['phone' => $phone, 'apikey' => $key, 'text' => mb_substr($text, 0, 1500)]);
        $ch = curl_init($url);
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 12]);
        $res = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
        if ($res === false || $code >= 400) kw_log('whatsapp alert failed for ' . substr($phone, 0, 6) . '… HTTP ' . $code);
    }
}

/** Svix-style signature check used by Nomod webhooks. */
function kw_verify_webhook(string $raw, array $h, string $secret): bool {
    $id = $h['svix-id'] ?? ''; $ts = $h['svix-timestamp'] ?? ''; $sig = $h['svix-signature'] ?? '';
    if ($id === '' || $ts === '' || $sig === '' || $secret === '') return false;
    if (abs(time() - (int)$ts) > 300) return false;
    $key = base64_decode(preg_replace('/^whsec_/', '', $secret), true);
    if ($key === false) return false;
    $expected = base64_encode(hash_hmac('sha256', $id . '.' . $ts . '.' . $raw, $key, true));
    foreach (preg_split('/\s+/', trim($sig)) as $part) {
        $v = explode(',', $part, 2);
        if (count($v) === 2 && $v[0] === 'v1' && hash_equals($expected, $v[1])) return true;
    }
    return false;
}
