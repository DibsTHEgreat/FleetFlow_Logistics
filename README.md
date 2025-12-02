# 🧭 FleetFlow Logistics Operations System

A lightweight, auditable logistics management system built with **Flask** and **SQLite3**.  
FleetFlow allows small or medium-sized delivery companies to track vehicles, routes, deliveries, and maintenance logs in one place — replacing spreadsheets with a dependable, low-cost pilot system.

---

## 🚀 Project Overview

FleetFlow is designed for **FleetFlow Logistics**, a regional delivery firm that needs a unified system to manage fleet operations and maintain data integrity.  
This system demonstrates how a small team can build a dependable operational database with a web interface that supports:

- **CRUD operations** (Create, Read, Update, Delete) for vehicles and deliveries  
- **Audit logging** for every change made to operational data  
- **Two business-ready reports:**
  - Vehicle utilization  
  - Deliveries per route  
- **Data integrity enforcement** using foreign keys and constraints  
- **Simple web interface** using Flask and Bootstrap  

This prototype is intended as a **pilot solution**—low cost, easy to maintain, and scalable in the future to larger databases (e.g., PostgreSQL).

---

## ⚙️ Setup Instructions

### 1. Create & Activate a Virtual Environment

```bash
    python -m venv venv
    source venv/bin/activate        # macOS / Linux
    venv\Scripts\activate           # Windows
```

### 2. Install Dependencies
```bash 
pip install flask
```

### 3. Initialize the Database
```bash 
python fleet_setup.py
```

### 4. Load Sample Data
```bash 
python load_sample_data.py
```

### 5. Run the Flask App
```bash 
python app.py
```

Visit your app in a browser at:
👉 http://127.0.0.1:5000/


## 🧩 Schema Overview

| Table | Purpose | Key Fields |
|--------|----------|------------|
| **vehicles** | Tracks all fleet units | `vehicle_id`, `type`, `capacity`, `status`, `license_plate`, `current_odometer` |
| **routes** | Delivery routes and regions | `route_id`, `origin`, `destination`, `distance_km`, `is_active` |
| **deliveries** | Individual delivery records | `delivery_id`, `vehicle_id`, `route_id`, `delivery_date`, `scheduled_time`, `delivery_time`, `status`, `customer_name`, `customer_address` |
| **maintenance_logs** | Vehicle service and repair history | `log_id`, `vehicle_id`, `service_date`, `service_type`, `description`, `vendor`, `cost` |
| **audit_log** | Tracks all CRUD changes across tables | `audit_id`, `timestamp`, `action`, `table_name`, `record_id`, `details`, `user` |

**Relationships**
- `deliveries.vehicle_id → vehicles.vehicle_id`
- `deliveries.route_id → routes.route_id`
- `maintenance_logs.vehicle_id → vehicles.vehicle_id`

All foreign keys are **enforced via SQLite PRAGMA**, ensuring that invalid or orphaned records (e.g., a delivery for a deleted vehicle) are prevented.

---

## 💻 Usage Guide

After running the app:

| Feature | URL | Description |
|----------|-----|-------------|
| **Dashboard** | `/` | Central hub linking to all sections |
| **Vehicles CRUD** | `/vehicles` | Add, view, edit, or delete vehicles |
| **Deliveries CRUD** | `/deliveries` | Manage deliveries by vehicle and route |
| **Maintenance Logs CRUD** | `/maintenance` | Manage maintenance logs |
| **Reports** | `/reports/vehicle_utilization` <br> `/reports/deliveries_per_route` | Generate summary insights |
| **Audit Log** | `/audit` | Review recorded database changes |

---

## 🧾 Example Workflow

1. Add a new vehicle (`/vehicles/new`)  
2. Add a route (`/routes/new`, optional if preloaded)  
3. Create a delivery (`/deliveries/new`)  
4. Update delivery status to “Completed”  
5. Check `/audit` to confirm changes are logged  
6. View performance in `/reports/vehicle_utilization`

---

## 📈 Design & Integrity Highlights

- **ACID-compliant transactions** – Each operation runs within a transaction to maintain data consistency.  
- **Audit logging** – Every insert, update, or delete creates a traceable record in `audit_log`.  
- **Indexes** – Applied on `vehicle_id`, `route_id`, and `delivery_date` to optimize report queries.  
- **Foreign key constraints** – Guarantee referential integrity between entities.  
- **Bootstrap 5 UI** – Responsive, minimal interface designed for ease of use by non-technical staff.

---

## 💰 Assumptions & Limitations

- Single-depot, single-user deployment (internal prototype)  
- No authentication or role-based access (trusted internal staff)  
- SQLite concurrency limits apply (safe for low-traffic operations)  
- Minimal front-end design; focus on backend reliability  
- No external APIs — all operations are fully local and offline-compatible  

---

## 🧠 AI Usage Disclosure

AI tools (ChatGPT and Copilot) were used responsibly for:
- Drafting and refining Flask CRUD boilerplate  
- Structuring HTML templates and Bootstrap layouts  
- Writing schema documentation and code comments  
- Improving readability and clarity of explanations  

All schema logic, database relationships, and business rules were designed, reviewed, and tested manually by **Divya Pateliya**.

---

**Author:** Divya Pateliya  
**Course:** MGT 4850 – Data Management & Business Analytics  
**Institution:** University of Lethbridge  
**Year:** 2025  