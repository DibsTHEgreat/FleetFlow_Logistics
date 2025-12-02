# Note for governance: Parts of this file were created with AI assistance (ChatGPT) for sample data loading.

import sqlite3

DB_PATH = "fleetflow.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Enforce foreign key constraints
    cur.execute("PRAGMA foreign_keys = ON;")

    # 1) Clear existing data in a safe order (due to foreign keys)
    cur.execute("DELETE FROM deliveries;")
    cur.execute("DELETE FROM maintenance_logs;")
    cur.execute("DELETE FROM routes;")
    cur.execute("DELETE FROM vehicles;")
    cur.execute("DELETE FROM audit_log;")  # reset audit trail for a clean demo

    # 2) Insert vehicles
    vehicles = [
        ("V001", "van",   1200, "active",      "ABC-123",  85000),
        ("V002", "truck", 3000, "active",      "XYZ-789", 120500),
        ("V003", "van",   1000, "maintenance", "LMN-456",  60500),
        ("V004", "truck", 3500, "active",      "JKL-222", 200000),
        ("V005", "van",   1500, "retired",     "HHH-555", 180000),
    ]

    cur.executemany(
        """
        INSERT INTO vehicles (
            vehicle_id, type, capacity, status, license_plate, current_odometer
        ) VALUES (?, ?, ?, ?, ?, ?);
        """,
        vehicles,
    )

    # 3) Insert routes
    routes = [
        ("R001", "Main Depot", "Downtown",        12.5, 1),
        ("R002", "Main Depot", "Industrial Park", 18.0, 1),
        ("R003", "North Hub",  "Airport",         25.0, 0),
    ]

    cur.executemany(
        """
        INSERT INTO routes (
            route_id, origin, destination, distance_km, is_active
        ) VALUES (?, ?, ?, ?, ?);
        """,
        routes,
    )

    # 4) Insert deliveries
    deliveries = [
        ("V001", "R001", "2025-11-24", "2025-11-24T09:00", "2025-11-24T09:30",
         "Coffee Shop A", "123 Main St, Downtown", "completed"),
        ("V001", "R001", "2025-11-24", "2025-11-24T10:00", "2025-11-24T10:20",
         "Bakery B", "45 River Rd, Downtown", "completed"),
        ("V002", "R002", "2025-11-24", "2025-11-24T08:30", "2025-11-24T09:15",
         "Factory C", "10 Industry Way, Industrial Park", "completed"),
        ("V002", "R002", "2025-11-24", "2025-11-24T11:00", None,
         "Warehouse D", "20 Storage Ln, Industrial Park", "in_transit"),
        ("V004", "R001", "2025-11-25", "2025-11-25T09:00", None,
         "Office E", "200 King St, Downtown", "pending"),
        ("V001", "R001", "2025-11-25", "2025-11-25T07:30", "2025-11-25T08:05",
         "Cafe F", "78 Queen St, Downtown", "completed"),
        ("V002", "R002", "2025-11-25", "2025-11-25T13:00", "2025-11-25T13:40",
         "Plant G", "5 Steel Ave, Industrial Park", "completed"),
        ("V004", "R002", "2025-11-26", "2025-11-26T10:00", None,
         "Garage H", "90 Wrench Rd, Industrial Park", "pending"),
        ("V001", "R001", "2025-11-26", "2025-11-26T08:00", "2025-11-26T08:35",
         "Shop I", "17 Broadway, Downtown", "completed"),
        ("V002", "R002", "2025-11-26", "2025-11-26T15:00", None,
         "Client J", "300 Tech Blvd, Industrial Park", "cancelled"),
    ]

    cur.executemany(
        """
        INSERT INTO deliveries (
            vehicle_id, route_id, delivery_date,
            scheduled_time, delivery_time,
            customer_name, customer_address,
            status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        deliveries,
    )

    # 5) Insert maintenance logs
    maintenance_logs = [
        ("V001", "2025-11-20", "Oil & filter change",              "oil_change",    84000,               "QuickLube",     120.00),
        ("V002", "2025-11-18", "Front & rear brake pads replaced","brake_service", 119000,              "BrakePro",      450.00),
        ("V003", "2025-11-22", "General safety inspection",        "inspection",    60000,               "North Garage",   90.00),
        ("V004", "2025-11-15", "Engine diagnostics and repair",    "engine_repair", 198500,              "TruckCare",    1300.00),
        ("V001", "2025-11-10", "Tire rotation & balance",          "tire_service",  83000,               "TireWorks",      80.00),
        ("V002", "2025-11-05", "Transmission fluid change",        "transmission",  117500,              "AutoTransPlus", 300.00),
    ]

    cur.executemany(
        """
        INSERT INTO maintenance_logs (
            vehicle_id, service_date, description,
            service_type, odometer_at_service, vendor, cost
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        maintenance_logs,
    )

    conn.commit()
    conn.close()
    print("Sample data loaded successfully.")

if __name__ == "__main__":
    main()
