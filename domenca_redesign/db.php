<?php
/**
 * AI Authority — Database helper
 * Creates/connects to SQLite database
 */

define('DB_PATH', '/home/hdwebd88/data/ai-authority.db');

function getDb() {
    static $db = null;
    if ($db) return $db;
    
    $dir = dirname(DB_PATH);
    if (!is_dir($dir)) {
        mkdir($dir, 0755, true);
    }
    
    $db = new PDO('sqlite:' . DB_PATH);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->exec('PRAGMA journal_mode=WAL');
    $db->exec('PRAGMA foreign_keys=ON');
    
    // Initialize tables if needed
    $schema = file_get_contents(__DIR__ . '/db-schema.sql');
    $db->exec($schema);
    
    return $db;
}
