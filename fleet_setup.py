import sqlite3

DB_PATH = "fleetflow.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Enable foreign key enforcement for SQLite (ensure referential integrity)
cur.execute("PRAGMA foreign_keys = ON;")

DDL = """
-- Schema definition for FleetFlow operations database
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id TEXT PRIMARY KEY, -- Internal unique identifier
    -- Added Checks for data integrity
    type TEXT NOT NULL,
    capacity INTEGER CHECK(capacity >= 0), -- in kilograms
    status TEXT NOT NULL CHECK (status IN ('active', 'maintenance', 'retired')),  -- To limit scope I am only enforcing these three statuses
    -- Additional vehicle attributes I added for better tracking
    license_plate TEXT UNIQUE NOT NULL, -- This is a real-world identifier
    current_odometer INTEGER -- in kilometers
);

CREATE TABLE IF NOT EXISTS routes (
    route_id TEXT PRIMARY KEY,
    -- Added Checks for data integrity
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    distance_km REAL CHECK(distance_km >= 0),
    -- Additional routes attribute I added for better tracking
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)) -- 1 for active route, 0 for inactive route
);

CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id TEXT NOT NULL,
    route_id   TEXT NOT NULL,
    delivery_date TEXT NOT NULL, -- YYYY-MM-DD
    -- Additional deliveries attributes I added for better tracking
    scheduled_time TEXT, -- ISO datetime string
    delivery_time TEXT,  -- ISO datetime string
    customer_name TEXT,
    customer_address TEXT,
    -- Added Checks for data integrity
    status TEXT NOT NULL CHECK (status IN ('pending', 'in_transit', 'completed', 'cancelled')),
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(vehicle_id),
    FOREIGN KEY(route_id) REFERENCES routes(route_id)
);

CREATE TABLE IF NOT EXISTS maintenance_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id TEXT NOT NULL,
    service_date TEXT NOT NULL, -- YYYY-MM-DD
    description TEXT NOT NULL,
    -- Additional maintenance attributes I added for better tracking
    service_type TEXT NOT NULL,
    odometer_at_service INTEGER,
    vendor TEXT,
    cost NUMERIC CHECK(cost >= 0),
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(vehicle_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL, -- ISO datetime string
    action TEXT NOT NULL,     -- e.g., 'INSERT', 'UPDATE', 'DELETE'
    table_name TEXT NOT NULL,
    record_id TEXT,           -- could store the ID of the affected record
    details TEXT,              -- JSON or text describing changes
    user TEXT NOT NULL -- Track who made the change
);

-- Utilizing ChatGPT I was able enchance my database schema with the addition of indexes for performance optimization.
-- The main reason I have done this is to speed up queries that will likely be run frequently in a fleet management system.
CREATE INDEX IF NOT EXISTS idx_deliveries_vehicle_id ON deliveries(vehicle_id); 
CREATE INDEX IF NOT EXISTS idx_deliveries_route_id ON deliveries(route_id); 
CREATE INDEX IF NOT EXISTS idx_deliveries_date ON deliveries(delivery_date); 

CREATE INDEX IF NOT EXISTS idx_maint_vehicle_id ON maintenance_logs(vehicle_id); 
CREATE INDEX IF NOT EXISTS idx_maint_service_date ON maintenance_logs(service_date);

"""
cur.executescript(DDL)
conn.commit()
conn.close()