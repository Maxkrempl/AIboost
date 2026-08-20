<?php
/**
 * AI Authority — Orders API
 * GET /api/ai-authority/orders.php — list all orders
 * GET /api/ai-authority/orders.php?id=1 — get single order with audits
 * PATCH /api/ai-authority/orders.php — update order (url, status, notes)
 */

require_once '/home/hdwebd88/public_html/data/db.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: https://hd-webdesign.si');
header('Access-Control-Allow-Methods: GET, PATCH, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

$db = getDb();

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $id = $_GET['id'] ?? null;
    
    if ($id) {
        // Single order with audits
        $stmt = $db->prepare('SELECT * FROM orders WHERE id = ?');
        $stmt->execute([$id]);
        $order = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if (!$order) {
            http_response_code(404);
            echo json_encode(['error' => 'Order not found']);
            exit;
        }
        
        // Get audits
        $stmt = $db->prepare('SELECT * FROM audits WHERE order_id = ? ORDER BY created_at DESC');
        $stmt->execute([$id]);
        $audits = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        // Get generated files
        $stmt = $db->prepare('SELECT * FROM generated_files WHERE order_id = ? ORDER BY created_at DESC');
        $stmt->execute([$id]);
        $files = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        echo json_encode([
            'order' => $order,
            'audits' => $audits,
            'files' => $files,
        ], JSON_PRETTY_PRINT);
    } else {
        // List all orders
        $status = $_GET['status'] ?? null;
        $sql = 'SELECT * FROM orders';
        $params = [];
        
        if ($status) {
            $sql .= ' WHERE status = ?';
            $params[] = $status;
        }
        
        $sql .= ' ORDER BY created_at DESC';
        $stmt = $db->prepare($sql);
        $stmt->execute($params);
        $orders = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        // Add summary stats
        $stats = $db->query('SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = "active" THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN status = "pending" THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN product = "ai_authority" THEN amount ELSE 0 END) as total_onetime,
            SUM(CASE WHEN product = "ai_authority_monthly" THEN amount ELSE 0 END) as total_monthly
        FROM orders')->fetch(PDO::FETCH_ASSOC);
        
        echo json_encode([
            'orders' => $orders,
            'stats' => $stats,
        ], JSON_PRETTY_PRINT);
    }
} elseif ($_SERVER['REQUEST_METHOD'] === 'PATCH') {
    $input = json_decode(file_get_contents('php://input'), true);
    $id = $input['id'] ?? null;
    
    if (!$id) {
        http_response_code(400);
        echo json_encode(['error' => 'Order ID required']);
        exit;
    }
    
    $updates = [];
    $params = [];
    
    foreach (['customer_url', 'customer_notes', 'status', 'customer_name'] as $field) {
        if (isset($input[$field])) {
            $updates[] = "$field = ?";
            $params[] = $input[$field];
        }
    }
    
    if (empty($updates)) {
        http_response_code(400);
        echo json_encode(['error' => 'No fields to update']);
        exit;
    }
    
    $updates[] = "updated_at = datetime('now')";
    $params[] = $id;
    
    $sql = 'UPDATE orders SET ' . implode(', ', $updates) . ' WHERE id = ?';
    $db->prepare($sql)->execute($params);
    
    echo json_encode(['success' => true]);
}
