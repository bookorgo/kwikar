<?php
/**
 * KWIKAR — live tours feed (TravelDesk proxy)
 *
 *   /api/tours.php          → list of tours with "from" prices
 *   /api/tours.php?id=123   → one tour with options, itinerary, FAQ
 *
 * The TravelDesk API key stays on the server (api/config.php) and is never
 * sent to the browser. Responses are cached in api/cache/ for 10 minutes;
 * if TravelDesk is down, the last saved copy (up to 7 days old) is served.
 * No booking or payment happens here — bookings go to WhatsApp.
 */
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');

const API_BASE   = 'https://api.traveldesk.me/public/b2b/v1';
const FRESH_SECS = 600;            // 10 minutes
const STALE_SECS = 7 * 24 * 3600;  // 7 days

$config = [];
if (is_file(__DIR__ . '/config.php')) {
    $config = require __DIR__ . '/config.php';
}
$apiKey = is_array($config) ? trim((string)($config['KWIKAR_API_KEY'] ?? '')) : '';
$apiBase = is_array($config) && !empty($config['API_BASE']) ? (string)$config['API_BASE'] : API_BASE;

$cacheDir = __DIR__ . '/cache';
if (!is_dir($cacheDir)) { @mkdir($cacheDir, 0755, true); }

function respond(array $payload, int $status = 200, int $maxAge = 300): void {
    http_response_code($status);
    header('Cache-Control: public, max-age=' . $maxAge);
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function cache_read(string $file): ?array {
    if (!is_file($file)) return null;
    $raw = @file_get_contents($file);
    $data = $raw ? json_decode($raw, true) : null;
    return is_array($data) && isset($data['savedAt'], $data['payload']) ? $data : null;
}

function cache_write(string $file, array $payload): void {
    @file_put_contents($file, json_encode(['savedAt' => time(), 'payload' => $payload], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), LOCK_EX);
}

function vendor_get(string $path, string $key): array {
    global $apiBase;
    $ch = curl_init($apiBase . $path);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 25,
        CURLOPT_HTTPHEADER     => ['Authorization: Bearer ' . $key, 'Accept: application/json'],
    ]);
    $body = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    if ($body === false || $code < 200 || $code >= 300) throw new RuntimeException('Vendor unavailable');
    $json = json_decode((string)$body, true);
    if (!is_array($json)) throw new RuntimeException('Invalid vendor response');
    return $json;
}

/* ---------- helpers mirrored from the previous site ---------- */

function num($v): ?float {
    if (is_int($v) || is_float($v)) return is_finite((float)$v) ? (float)$v : null;
    if (is_string($v) && trim($v) !== '' && is_numeric($v)) return (float)$v;
    return null;
}
function amount($v): float { $n = num($v); return $n !== null && $n > 0 ? round($n, 2) : 0.0; }

function photo_src($p, string $size): ?string {
    $sets = is_array($p) ? ($p['srcSet'] ?? null) : null;
    if (!is_array($sets) || !$sets) return null;
    $set = $sets[0];
    foreach ($sets as $s) { if (($s['type'] ?? '') === 'image/webp') { $set = $s; break; } }
    $sizes = $set['sizes'] ?? [];
    foreach ($sizes as $s) { if (isset($s['src']) && preg_match('/-' . preg_quote($size, '/') . '\.\w+$/', $s['src'])) return $s['src']; }
    return $sizes[0]['src'] ?? null;
}

function active_period(array $periods): ?array {
    $today = gmdate('Y-m-d');
    foreach ($periods as $p) {
        $start = substr((string)($p['dateStart'] ?? '0000'), 0, 10) ?: '0000';
        $end   = substr((string)($p['dateEnd'] ?? '9999'), 0, 10) ?: '9999';
        if ($start <= $today && $today <= $end) return $p;
    }
    return null;
}

function price_of(?array $p): array {
    if (!$p) return ['price' => null, 'unit' => null, 'child' => null, 'tripFee' => null, 'adultBase' => null];
    $adult = amount($p['recPricePerAdult'] ?? null);
    $child = amount($p['recPricePerChild'] ?? null);
    $trip  = amount($p['recPricePerTrip'] ?? null);
    if ($adult > 0) return ['price' => $adult, 'unit' => 'person', 'child' => $child > 0 ? $child : null, 'tripFee' => $trip, 'adultBase' => $adult];
    if ($trip > 0)  return ['price' => $trip, 'unit' => 'trip', 'child' => null, 'tripFee' => $trip, 'adultBase' => 0];
    return ['price' => null, 'unit' => null, 'child' => null, 'tripFee' => null, 'adultBase' => null];
}

const NO_PROMISE = 'KWIKAR will confirm your booking on WhatsApp after checking availability with the supplier.';
function promise_re(): string {
    return '/\b(?:instant(?:ly)?|immediate(?:ly)?|automatic(?:ally)?)\s+(?:booking\s+)?confirm(?:ation|ed)\b|\bconfirm(?:ation|ed)\s+(?:instantly|immediately|automatically)\b|\b(?:tickets?|vouchers?)\b[^.!?]{0,150}\b(?:immediately|instantly|automatically)\b/i';
}
function customer_text($v): string {
    if (!is_string($v)) return '';
    $out = [];
    foreach (preg_split('/(?<=[.!?])\s+/', $v) as $s) {
        $s = preg_match(promise_re(), $s) ? NO_PROMISE : $s;
        if ($s === NO_PROMISE && end($out) === NO_PROMISE) continue;
        $out[] = $s;
    }
    return trim(implode(' ', $out));
}
/** Keep only simple formatting tags, no attributes, no scripts. */
function customer_html($v): string {
    if (!is_string($v)) return '';
    $safe = preg_replace('/<(script|style|iframe)\b[^>]*>[\s\S]*?<\/\1>/i', '', $v);
    $safe = preg_replace_callback('/<\/?[^>]+>/', function ($m) {
        return preg_match('/^<(\/)?(p|ul|ol|li|strong|b|em|i|br|h2|h3|h4)\b[^>]*>$/i', $m[0], $t)
            ? '<' . ($t[1] ?? '') . strtolower($t[2]) . '>' : '';
    }, (string)$safe);
    $safe = preg_replace_callback('/<(p|li|h2|h3|h4)>([\s\S]*?)<\/\1>/i', function ($m) {
        $text = str_replace(['&nbsp;', '&#160;'], ' ', strip_tags($m[2]));
        return preg_match(promise_re(), $text) ? '<' . $m[1] . '>' . htmlspecialchars(customer_text($text)) . '</' . $m[1] . '>' : $m[0];
    }, (string)$safe);
    return preg_match('/<(p|li|h2|h3|h4)>/i', (string)$safe) ? (string)$safe : htmlspecialchars(customer_text(strip_tags((string)$safe)));
}

function operating_days($v): array {
    $names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
    if (is_int($v) && $v >= 0 && $v <= 127) {
        if ($v === 0) return $names;
        return array_values(array_filter($names, fn($n, $i) => ($v & (1 << $i)) !== 0, ARRAY_FILTER_USE_BOTH));
    }
    if (!is_array($v)) return [];
    $out = [];
    foreach ($v as $x) { if (is_string($x) && in_array(strtolower(trim($x)), $names, true)) $out[] = strtolower(trim($x)); }
    return array_values(array_unique($out));
}

function transfer_info($name, float $trip, $direct): array {
    $l = is_string($name) ? strtolower($name) : '';
    $kind = preg_match('/direct reporting|meet at|no transfer|without transfer/', $l) ? 'meet_at_location'
        : (preg_match('/private[\s-]+transfer|transfer[\s-]+private/', $l) ? 'private'
        : (preg_match('/(?:sharing|shared)[\s-]+transfer|transfer[\s-]+(?:sharing|shared)|\bsic\b/', $l) ? 'sharing' : 'unspecified'));
    if ($direct === true) $kind = 'meet_at_location';
    return [
        'transferKind' => $kind,
        'transferPricingMode' => $trip > 0 ? 'per_booking' : ($kind === 'sharing' ? 'per_person' : 'included'),
        'pickupRequired' => $kind === 'private' || $kind === 'sharing',
    ];
}

function names_of($v): array {
    if (!is_array($v)) return [];
    $out = [];
    foreach ($v as $item) {
        $s = is_array($item) ? (string)($item['name'] ?? $item['value'] ?? $item['day'] ?? '') : (string)$item;
        if ($s !== '') $out[] = $s;
    }
    return $out;
}

function policy_lines($v): array {
    if (is_string($v)) return trim($v) !== '' ? [trim(strip_tags($v))] : [];
    if (is_array($v)) {
        $out = [];
        $isList = array_keys($v) === range(0, count($v) - 1);
        if ($isList) { foreach ($v as $x) $out = array_merge($out, policy_lines($x)); return $out; }
        foreach (['name', 'description', 'text', 'policy', 'cancellationPolicy'] as $k) if (isset($v[$k])) $out = array_merge($out, policy_lines($v[$k]));
        return $out;
    }
    return [];
}

/** Which destination a tour belongs to (same rules as before). */
function tour_location(array $t): string {
    static $overrides = null;
    if ($overrides === null) {
        $file = __DIR__ . '/locations.json';
        $overrides = is_file($file) ? (json_decode((string)file_get_contents($file), true) ?: []) : [];
    }
    $valid = ['dubai','abu-dhabi','sharjah','ras-al-khaimah','fujairah','ajman','oman','singapore','malaysia','thailand','bali','vietnam','japan','south-korea','australia','turkiye','greece','italy','spain','portugal','france','germany','austria','belgium','uk','croatia','poland','usa','canada'];
    $id = (string)($t['id'] ?? '');
    if (isset($overrides[$id]) && in_array($overrides[$id], $valid, true)) return $overrides[$id];
    $rules = [
        ['abu-dhabi', '/abu ?-?dhabi|\byas\b|ferrari world|warner|seaworld|louvre abu|sheikh zayed|saadiyat|al ain|qasr al|liwa|emirates park zoo/iu'],
        ['sharjah', '/sharjah|mleiha|khor ?fakkan/iu'], ['ras-al-khaimah', '/ras al|\brak\b|jebel jais|jais /iu'],
        ['fujairah', '/fujairah|dibba|snoopy/iu'], ['ajman', '/ajman/iu'], ['oman', '/musandam|oman\b/iu'],
        ['dubai', '/dubai|burj|dhow|desert safari|atlantis|aquaventure|img worlds|motion gate|global village|miracle garden|house of hype|aya universe|cabrio|alexandra|lotus royale|lost world|ain dubai|la perle|museum of the future|jumeirah/iu'],
        ['singapore', '/singapore|sentosa|gardens by the bay|jewel changi|mandai/iu'], ['bali', '/bali|batur|ubud|nusa |uluwatu/iu'],
        ['thailand', '/phuket|phi phi|krabi|pattaya|bangkok|thailand|andamanda/iu'], ['malaysia', '/malaysia|kuala|desaru|malacca|melaka|menara|langkawi|genting|berjaya|penang|sunway/iu'],
        ['vietnam', '/vietnam|da nang|danang|hanoi|ho chi minh|saigon|mekong|ha long|halong|ba na|hoi an|nha trang|phu quoc/iu'],
        ['turkiye', '/istanbul|antalya|aspendos|miniat|cappadocia|basilica cistern|bosphorus|turkey|türkiye|hagia sophia|topkapi/iu'],
        ['greece', '/athens|acropolis|lindos|greece|rhodes|santorini|mykonos|agora|thessaloniki/iu'],
        ['spain', '/barcelona|madrid|montju|mallorca|sagrada|seville|spain|valencia|g[uü]ell|batll|cordoba|canaria|tenerife/iu'],
        ['portugal', '/lisbon|monserrate|sintra|\bpena\b|\bporto\b|portugal|jer[oó]nimos/iu'],
        ['italy', '/\brome\b|\broma\b|vatican|colosseum|florence|venice|milan|italy|pompeii/iu'],
        ['france', '/paris|eiffel|versailles|france/iu'], ['usa', '/los angeles|hollywood|academy museum|battleship iowa|new york|las vegas|san francisco|miami|orlando/iu'],
        ['japan', '/tokyo|osaka|kyoto|japan|moomin/iu'], ['australia', '/sydney|melbourne|australia|gold coast/iu'],
        ['belgium', '/atomium|brussels|belgium/iu'], ['uk', '/london|westminster|thames|england|edinburgh/iu'],
        ['south-korea', '/seoul|korea|incheon/iu'], ['germany', '/berlin|cologne|munich|germany/iu'],
        ['austria', '/vienna|schonbrunn|sch[oö]nbrunn|austria/iu'],
    ];
    $name = (string)($t['name'] ?? '');
    foreach ($rules as [$loc, $re]) { if (preg_match($re, $name)) return $loc; }
    return 'other';
}

/* ---------- request ---------- */

$id = $_GET['id'] ?? null;
if ($id !== null && !preg_match('/^[1-9]\d{0,8}$/', (string)$id)) respond(['ok' => false, 'error' => 'Invalid tour'], 400, 60);

$cacheFile = $cacheDir . '/' . ($id ? 'tour-' . $id : 'tours-list') . '.json';
$cached = cache_read($cacheFile);
$age = $cached ? time() - (int)$cached['savedAt'] : PHP_INT_MAX;

if ($cached && $age < FRESH_SECS) respond($cached['payload']);

$serveStale = function () use ($cached, $age) {
    if ($cached && $age < STALE_SECS && !empty($cached['payload']['ok'])) {
        respond($cached['payload'] + ['stale' => true, 'updated' => gmdate('c', (int)$cached['savedAt'])], 200, 60);
    }
    respond(['ok' => false, 'error' => 'Tours feed unavailable'], 502, 30);
};

if ($apiKey === '') $serveStale();

try {
    if ($id) {
        $d = vendor_get('/tours/' . $id . '?CurrencyCode=AED', $apiKey);
        $offers = [];
        foreach (($d['offers'] ?? []) as $o) {
            $periods = is_array($o['pricingPeriods'] ?? null) ? $o['pricingPeriods'] : [];
            $active = null;
            $today = gmdate('Y-m-d');
            foreach ($periods as $p) {
                if (!empty($p['dateStart']) && !empty($p['dateEnd']) && substr($p['dateStart'], 0, 10) <= $today && $today <= substr($p['dateEnd'], 0, 10)) { $active = $p; break; }
            }
            $pp = [];
            foreach ($periods as $p) {
                $s = substr((string)($p['dateStart'] ?? ''), 0, 10); $e = substr((string)($p['dateEnd'] ?? ''), 0, 10);
                if ($s && $e) $pp[] = ['dateStart' => $s, 'dateEnd' => $e, 'adult' => num($p['recPricePerAdult'] ?? null), 'child' => num($p['recPricePerChild'] ?? null), 'trip' => num($p['recPricePerTrip'] ?? null)];
            }
            $tripNow = $active ? amount($active['recPricePerTrip'] ?? null) : 0.0;
            $offers[] = array_merge([
                'id' => $o['id'] ?? null,
                'name' => (string)($o['name'] ?? ''),
                'hours' => num($o['numberOfHours'] ?? null),
            ], price_of($active), [
                'childrenAllowed' => $o['childrenAllowed'] ?? null,
                'minPeople' => num($o['minNumOfPeople'] ?? null),
                'maxPeople' => num($o['maxNumOfPeople'] ?? null),
                'daysOffered' => operating_days($o['daysOffered'] ?? ($d['daysOffered'] ?? null)),
                'timeSlots' => names_of($o['timeSlots'] ?? ($o['timeslots'] ?? null)),
                'pricingPeriods' => $pp,
                'desc' => customer_html($o['description'] ?? ''),
            ], transfer_info($o['name'] ?? '', $tripNow, $o['isDirectReporting'] ?? null));
        }
        usort($offers, fn($a, $b) => ($a['price'] ?? 1e9) <=> ($b['price'] ?? 1e9));
        $itinerary = [];
        foreach (($d['itineraries'] ?? []) as $it) foreach (($it['stops'] ?? []) as $s) {
            $itinerary[] = ['name' => (string)($s['name'] ?? ''), 'desc' => customer_text(strip_tags((string)($s['description'] ?? ''))), 'time' => $s['time'] ?? null];
        }
        $faq = [];
        foreach (($d['faqList'] ?? []) as $f) $faq[] = ['q' => trim((string)($f['question'] ?? '')), 'a' => trim(customer_text(strip_tags((string)($f['answer'] ?? ''))))];
        $photos = [];
        foreach (($d['photos'] ?? []) as $p) { $src = photo_src($p, 'hd'); if ($src) $photos[] = $src; }
        $payload = [
            'ok' => true,
            'id' => $d['id'] ?? (int)$id,
            'name' => (string)($d['name'] ?? ''),
            'location' => tour_location($d),
            'rating' => num($d['totalRating'] ?? null),
            'reviews' => num($d['totalRatingsCount'] ?? null),
            'img' => photo_src($d['heroImage'] ?? null, 'fhd'),
            'photos' => $photos,
            'categories' => names_of($d['categories'] ?? []),
            'description' => customer_html($d['salesDescription'] ?? ''),
            'terms' => customer_html($d['termsAndConditions'] ?? ''),
            'cancellation' => policy_lines($d['cancellationPolicy'] ?? []),
            'faq' => $faq,
            'itinerary' => $itinerary,
            'offers' => $offers,
        ];
    } else {
        $tours  = vendor_get('/tours?CurrencyCode=AED', $apiKey);
        $offers = vendor_get('/offers?IncludePrices=true', $apiKey);
        if (!$tours || array_keys($tours) !== range(0, count($tours) - 1)) throw new RuntimeException('Invalid vendor feed');
        $min = [];
        foreach ($offers as $o) {
            $p = price_of(active_period(is_array($o['prices'] ?? null) ? $o['prices'] : []));
            if (!$p['price']) continue;
            $k = (string)($o['tourId'] ?? '');
            $prev = $min[$k] ?? null;
            if (!$prev || ($p['unit'] === 'person' && $prev['unit'] !== 'person') || ($p['unit'] === $prev['unit'] && $p['price'] < $prev['price'])) $min[$k] = $p;
        }
        $items = [];
        foreach ($tours as $t) {
            $k = (string)($t['id'] ?? '');
            $items[] = [
                'id' => $t['id'] ?? null,
                'name' => trim((string)($t['name'] ?? '')),
                'img' => photo_src($t['heroImage'] ?? null, 'sd'),
                'cats' => names_of($t['categories'] ?? []),
                'rating' => num($t['totalRating'] ?? null),
                'reviews' => num($t['totalRatingsCount'] ?? null),
                'price' => $min[$k]['price'] ?? null,
                'unit' => $min[$k]['unit'] ?? null,
                'loc' => tour_location($t),
            ];
        }
        $payload = ['ok' => true, 'updated' => gmdate('c'), 'items' => $items];
    }
    cache_write($cacheFile, $payload);
    respond($payload);
} catch (Throwable $e) {
    $serveStale();
}
