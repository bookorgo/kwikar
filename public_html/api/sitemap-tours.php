<?php
// Sitemap of tour pages, built from the saved tours feed (api/cache/tours-list.json).
header('Content-Type: application/xml; charset=utf-8');
header('Cache-Control: public, max-age=3600');
$file = __DIR__ . '/cache/tours-list.json';
$items = [];
if (is_file($file)) {
    $data = json_decode((string)file_get_contents($file), true);
    if (is_array($data) && time() - (int)($data['savedAt'] ?? 0) < 7 * 24 * 3600) $items = $data['payload']['items'] ?? [];
}
echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n" . '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n";
foreach ($items as $t) {
    $id = $t['id'] ?? null;
    if (is_int($id) && $id > 0 && !empty($t['name'])) echo '  <url><loc>https://kwikar.com/tour/' . $id . "</loc></url>\n";
}
echo "</urlset>\n";
