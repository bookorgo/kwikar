<?php
/**
 * KWIKAR — Nomod webhook (Hosted Checkout events: charge.completed, charge.failed, charge.refunded).
 * URL to register in Nomod: https://kwikar.com/api/nomod-webhook.php
 * The signature is checked with NOMOD_WEBHOOK_SECRET from kwikar-config.php. The order status is
 * always re-read from the Nomod API, so a webhook body alone can never mark an order as paid.
 */
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
require __DIR__ . '/pay-lib.php';

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') out(['ok' => false], 405);
if (!kw_rate_ok('webhook', 300, 3600)) out(['ok' => false], 429);
$raw = (string)file_get_contents('php://input', false, null, 0, 200000);
$h = [];
foreach (['svix-id', 'svix-timestamp', 'svix-signature'] as $k) $h[$k] = (string)($_SERVER['HTTP_' . strtoupper(str_replace('-', '_', $k))] ?? '');
if (!kw_verify_webhook($raw, $h, trim((string)cfg('NOMOD_WEBHOOK_SECRET')))) { kw_log('webhook: bad signature'); out(['ok' => false], 400); }

$seen = kw_data_dir() . '/webhook-seen.txt';
if (strpos((string)@file_get_contents($seen), $h['svix-id'] . "\n") !== false) out(['ok' => true]);   // same delivery twice: ignore
@file_put_contents($seen, $h['svix-id'] . "\n", FILE_APPEND | LOCK_EX);
if (@filesize($seen) > 200000) @file_put_contents($seen, substr((string)file_get_contents($seen), -100000), LOCK_EX);
$ev = json_decode($raw, true);
$type = is_array($ev) ? (string)($ev['type'] ?? '') : '';
if (!preg_match('/KW-\d{6}-[A-Z2-9]{8}/', $raw, $m)) { kw_log('webhook ' . $type . ': no KWIKAR ref'); out(['ok' => true]); }
$order = kw_order_load($m[0]);
if (!$order) { kw_log('webhook ' . $type . ': unknown ' . $m[0]); out(['ok' => true]); }

if ($type === 'charge.refunded' || $type === 'charge.partially_refunded') {
    $order['status'] = $type === 'charge.refunded' ? 'refunded' : 'partially_refunded';
    $order['refunded_at'] = gmdate('c');
    kw_order_save($order);
    kw_mail(KW_NOTIFY_TO, 'REFUND ' . $order['ref'] . ' – ' . $order['tour']['name'], 'Nomod reports a ' . str_replace('charge.', '', $type) . ' for ' . $order['ref'] . ' (AED ' . $order['total'] . ').');
    kw_whatsapp_alert('*' . strtoupper(str_replace('charge.', '', $type)) . ' ' . $order['ref'] . '* · AED ' . $order['total'] . "\n" . $order['tour']['name'] . ' · ' . $order['date']);
    kw_log('webhook refund ' . $order['ref']);
} elseif ($type === 'charge.failed') {
    kw_log('webhook failed charge for ' . $order['ref']);
} else {
    kw_order_refresh($order);   // charge.completed etc: confirm with the API, then email once
}
out(['ok' => true]);
