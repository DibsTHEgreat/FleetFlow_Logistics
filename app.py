import datetime
import sqlite3
from flask import Flask, g, render_template, request, redirect, url_for

app = Flask(__name__)
DATABASE = "fleetflow.db"

def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        g.db = conn
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def log_audit(db, action, table_name, record_id, user="system", details=""):
    """
    Write a simple audit entry for any INSERT/UPDATE/DELETE.
    """
    timestamp = datetime.datetime.utcnow().isoformat()
    db.execute(
        """
        INSERT INTO audit_log (timestamp, action, table_name, record_id, details, user)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (timestamp, action, table_name, str(record_id), details, user),
    )

@app.route("/")
def index():
    return render_template("index.html")

# ---------- VEHICLES CRUD ----------
@app.route("/vehicles")
def list_vehicles():
    """
    List all vehicles in a simple table.
    """
    db = get_db()
    vehicles = db.execute(
        "SELECT * FROM vehicles ORDER BY vehicle_id"
    ).fetchall()
    return render_template("vehicles.html", vehicles=vehicles)

@app.route("/vehicles/new", methods=["GET", "POST"])
def create_vehicle():
    """
    Create a new vehicle.
    GET: show form
    POST: insert into vehicles, then redirect to /vehicles
    """
    if request.method == "POST":
        vehicle_id = request.form.get("vehicle_id").strip()
        v_type = request.form.get("type").strip()
        status = request.form.get("status").strip()
        license_plate = request.form.get("license_plate").strip()

        capacity_raw = request.form.get("capacity")
        odometer_raw = request.form.get("current_odometer")

        capacity = int(capacity_raw) if capacity_raw else None
        current_odometer = int(odometer_raw) if odometer_raw else None

        db = get_db()
        try:
            db.execute(
                """
                INSERT INTO vehicles (
                    vehicle_id, type, capacity, status, license_plate, current_odometer
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (vehicle_id, v_type, capacity, status, license_plate, current_odometer),
            )
            log_audit(
                db,
                action="INSERT",
                table_name="vehicles",
                record_id=vehicle_id,
                user="demo_user",
                details="Created new vehicle",
            )
            db.commit()
            return redirect(url_for("list_vehicles"))
        except sqlite3.IntegrityError as e:
            error = f"Error creating vehicle: {e}"
            return render_template(
                "vehicle_form.html",
                vehicle=None,
                form_action=url_for("create_vehicle"),
                is_edit=False,
                error=error,
            )

    return render_template(
        "vehicle_form.html",
        vehicle=None,
        form_action=url_for("create_vehicle"),
        is_edit=False,
        error=None,
    )

@app.route("/vehicles/<vehicle_id>/edit", methods=["GET", "POST"])
def edit_vehicle(vehicle_id):
    """
    Edit an existing vehicle.
    GET: show form pre-filled
    POST: update row
    """
    db = get_db()
    if request.method == "POST":
        v_type = request.form.get("type").strip()
        status = request.form.get("status").strip()
        license_plate = request.form.get("license_plate").strip()

        capacity_raw = request.form.get("capacity")
        odometer_raw = request.form.get("current_odometer")

        capacity = int(capacity_raw) if capacity_raw else None
        current_odometer = int(odometer_raw) if odometer_raw else None

        try:
            db.execute(
                """
                UPDATE vehicles
                SET type = ?, capacity = ?, status = ?, license_plate = ?, current_odometer = ?
                WHERE vehicle_id = ?
                """,
                (v_type, capacity, status, license_plate, current_odometer, vehicle_id),
            )
            log_audit(
                db,
                action="UPDATE",
                table_name="vehicles",
                record_id=vehicle_id,
                user="demo_user",
                details="Updated vehicle",
            )
            db.commit()
            return redirect(url_for("list_vehicles"))
        except sqlite3.IntegrityError as e:
            error = f"Error updating vehicle: {e}"
            vehicle = db.execute(
                "SELECT * FROM vehicles WHERE vehicle_id = ?",
                (vehicle_id,),
            ).fetchone()
            return render_template(
                "vehicle_form.html",
                vehicle=vehicle,
                form_action=url_for("edit_vehicle", vehicle_id=vehicle_id),
                is_edit=True,
                error=error,
            )

    vehicle = db.execute(
        "SELECT * FROM vehicles WHERE vehicle_id = ?",
        (vehicle_id,),
    ).fetchone()
    if vehicle is None:
        return "Vehicle not found", 404

    return render_template(
        "vehicle_form.html",
        vehicle=vehicle,
        form_action=url_for("edit_vehicle", vehicle_id=vehicle_id),
        is_edit=True,
        error=None,
    )

@app.route("/vehicles/<vehicle_id>/delete", methods=["POST"])
def delete_vehicle(vehicle_id):
    """
    Delete a vehicle.
    We will prevent deletion if the vehicle has deliveries (to avoid FK errors).
    """
    db = get_db()

    count_row = db.execute(
        "SELECT COUNT(*) AS cnt FROM deliveries WHERE vehicle_id = ?",
        (vehicle_id,),
    ).fetchone()
    if count_row["cnt"] > 0:
        return (
            "Cannot delete vehicle with existing deliveries. "
            "Reassign or delete deliveries first.",
            400,
        )

    db.execute(
        "DELETE FROM vehicles WHERE vehicle_id = ?",
        (vehicle_id,),
    )
    log_audit(
        db,
        action="DELETE",
        table_name="vehicles",
        record_id=vehicle_id,
        user="demo_user",
        details="Deleted vehicle",
    )
    db.commit()
    return redirect(url_for("list_vehicles"))

# ---------- DELIVERIES CRUD ----------
@app.route("/deliveries")
def list_deliveries():
    """
    List all deliveries, joined with vehicle and route info.
    """
    db = get_db()
    deliveries = db.execute(
        """
        SELECT d.delivery_id,
               d.delivery_date,
               d.status,
               d.customer_name,
               d.customer_address,
               d.scheduled_time,
               d.delivery_time,
               v.vehicle_id,
               v.type AS vehicle_type,
               r.route_id,
               r.origin,
               r.destination
        FROM deliveries d
        JOIN vehicles v ON d.vehicle_id = v.vehicle_id
        JOIN routes r   ON d.route_id   = r.route_id
        ORDER BY d.delivery_date DESC, d.delivery_id DESC
        """
    ).fetchall()
    return render_template("deliveries.html", deliveries=deliveries)

@app.route("/deliveries/new", methods=["GET", "POST"])
def create_delivery():
    """
    Create a new delivery record.
    """
    db = get_db()

    if request.method == "POST":
        vehicle_id = request.form.get("vehicle_id")
        route_id = request.form.get("route_id")
        delivery_date = request.form.get("delivery_date")
        scheduled_time = request.form.get("scheduled_time") or None
        delivery_time = request.form.get("delivery_time") or None
        customer_name = request.form.get("customer_name") or None
        customer_address = request.form.get("customer_address") or None
        status = request.form.get("status")

        db.execute(
            """
            INSERT INTO deliveries (
                vehicle_id, route_id, delivery_date,
                scheduled_time, delivery_time,
                customer_name, customer_address,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vehicle_id,
                route_id,
                delivery_date,
                scheduled_time,
                delivery_time,
                customer_name,
                customer_address,
                status,
            ),
        )
        log_audit(
            db,
            action="INSERT",
            table_name="deliveries",
            record_id="(auto)",  # delivery_id is autoincrement; you can fetch it if you want
            user="demo_user",
            details=f"Created delivery for {customer_name or 'unknown customer'}",
        )
        db.commit()
        return redirect(url_for("list_deliveries"))

    # GET: need vehicles and routes for dropdowns
    vehicles = db.execute(
        "SELECT vehicle_id, type FROM vehicles WHERE status != 'retired' ORDER BY vehicle_id"
    ).fetchall()
    routes = db.execute(
        "SELECT route_id, origin, destination FROM routes WHERE is_active = 1 ORDER BY route_id"
    ).fetchall()

    return render_template(
        "delivery_form.html",
        delivery=None,
        vehicles=vehicles,
        routes=routes,
        form_action=url_for("create_delivery"),
        is_edit=False,
        error=None,
    )

@app.route("/deliveries/<int:delivery_id>/edit", methods=["GET", "POST"])
def edit_delivery(delivery_id):
    """
    Edit an existing delivery record.
    """
    db = get_db()
    delivery = db.execute(
        "SELECT * FROM deliveries WHERE delivery_id = ?",
        (delivery_id,),
    ).fetchone()

    if delivery is None:
        return "Delivery not found", 404

    if request.method == "POST":
        vehicle_id = request.form.get("vehicle_id")
        route_id = request.form.get("route_id")
        delivery_date = request.form.get("delivery_date")
        scheduled_time = request.form.get("scheduled_time") or None
        delivery_time = request.form.get("delivery_time") or None
        customer_name = request.form.get("customer_name") or None
        customer_address = request.form.get("customer_address") or None
        status = request.form.get("status")

        db.execute(
            """
            UPDATE deliveries
            SET vehicle_id = ?,
                route_id = ?,
                delivery_date = ?,
                scheduled_time = ?,
                delivery_time = ?,
                customer_name = ?,
                customer_address = ?,
                status = ?
            WHERE delivery_id = ?
            """,
            (
                vehicle_id,
                route_id,
                delivery_date,
                scheduled_time,
                delivery_time,
                customer_name,
                customer_address,
                status,
                delivery_id,
            ),
        )
        log_audit(
            db,
            action="UPDATE",
            table_name="deliveries",
            record_id=delivery_id,
            user="demo_user",
            details="Updated delivery",
        )
        db.commit()
        return redirect(url_for("list_deliveries"))

    # GET: dropdown data
    vehicles = db.execute(
        "SELECT vehicle_id, type FROM vehicles WHERE status != 'retired' ORDER BY vehicle_id"
    ).fetchall()
    routes = db.execute(
        "SELECT route_id, origin, destination FROM routes WHERE is_active = 1 ORDER BY route_id"
    ).fetchall()

    return render_template(
        "delivery_form.html",
        delivery=delivery,
        vehicles=vehicles,
        routes=routes,
        form_action=url_for("edit_delivery", delivery_id=delivery_id),
        is_edit=True,
        error=None,
    )

@app.route("/deliveries/<int:delivery_id>/delete", methods=["POST"])
def delete_delivery(delivery_id):
    """
    Delete a delivery record.
    """
    db = get_db()
    db.execute(
        "DELETE FROM deliveries WHERE delivery_id = ?",
        (delivery_id,),
    )
    log_audit(
        db,
        action="DELETE",
        table_name="deliveries",
        record_id=delivery_id,
        user="demo_user",
        details="Deleted delivery",
    )
    db.commit()
    return redirect(url_for("list_deliveries"))

# ---------- REPORTS ----------
@app.route("/reports/vehicle_utilization")
def vehicle_utilization_report():
    """
    Show how many deliveries each vehicle has handled.
    """
    db = get_db()
    rows = db.execute(
        """
        SELECT v.vehicle_id,
               v.type AS vehicle_type,
               v.status AS vehicle_status,
               COUNT(d.delivery_id) AS total_deliveries,
               SUM(CASE WHEN d.status = 'completed' THEN 1 ELSE 0 END) AS completed_deliveries
        FROM vehicles v
        LEFT JOIN deliveries d ON v.vehicle_id = d.vehicle_id
        GROUP BY v.vehicle_id, v.type, v.status
        ORDER BY completed_deliveries DESC, total_deliveries DESC;
        """
    ).fetchall()
    return render_template("report_vehicle_utilization.html", rows=rows)

@app.route("/reports/deliveries_per_route")
def deliveries_per_route_report():
    """
    Show how many deliveries are associated with each route.
    """
    db = get_db()
    rows = db.execute(
        """
        SELECT r.route_id,
               r.origin,
               r.destination,
               COUNT(d.delivery_id) AS total_deliveries,
               SUM(CASE WHEN d.status = 'completed' THEN 1 ELSE 0 END) AS completed_deliveries
        FROM routes r
        LEFT JOIN deliveries d ON r.route_id = d.route_id
        GROUP BY r.route_id, r.origin, r.destination
        ORDER BY total_deliveries DESC, completed_deliveries DESC;
        """
    ).fetchall()
    return render_template("report_deliveries_per_route.html", rows=rows)

# ---------- MAINTENANCE LOGS CRUD ----------
@app.route("/maintenance")
def list_maintenance():
    """
    List all maintenance logs, joined with vehicle info.
    """
    db = get_db()
    logs = db.execute(
        """
        SELECT m.log_id,
               m.service_date,
               m.service_type,
               m.description,
               m.vendor,
               m.cost,
               m.odometer_at_service,
               v.vehicle_id,
               v.type AS vehicle_type
        FROM maintenance_logs m
        JOIN vehicles v ON m.vehicle_id = v.vehicle_id
        ORDER BY m.service_date DESC, m.log_id DESC
        """
    ).fetchall()
    return render_template("maintenance_logs.html", logs=logs)

@app.route("/maintenance/new", methods=["GET", "POST"])
def create_maintenance():
    """
    Create a new maintenance log entry.
    """
    db = get_db()

    if request.method == "POST":
        vehicle_id = request.form.get("vehicle_id")
        service_date = request.form.get("service_date")
        service_type = request.form.get("service_type")
        description = request.form.get("description")
        odometer_raw = request.form.get("odometer_at_service")
        vendor = request.form.get("vendor") or None
        cost_raw = request.form.get("cost")

        odometer_at_service = int(odometer_raw) if odometer_raw else None
        cost = float(cost_raw) if cost_raw else None

        db.execute(
            """
            INSERT INTO maintenance_logs (
                vehicle_id, service_date, description,
                service_type, odometer_at_service, vendor, cost
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vehicle_id,
                service_date,
                description,
                service_type,
                odometer_at_service,
                vendor,
                cost,
            ),
        )
        log_audit(
            db,
            action="INSERT",
            table_name="maintenance_logs",
            record_id="(auto)",
            user="demo_user",
            details=f"Created maintenance log for vehicle {vehicle_id}",
        )
        db.commit()
        return redirect(url_for("list_maintenance"))

    # GET: load active vehicles for dropdown
    vehicles = db.execute(
        "SELECT vehicle_id, type FROM vehicles WHERE status != 'retired' ORDER BY vehicle_id"
    ).fetchall()

    return render_template(
        "maintenance_form.html",
        log=None,
        vehicles=vehicles,
        form_action=url_for("create_maintenance"),
        is_edit=False,
        error=None,
    )

@app.route("/maintenance/<int:log_id>/edit", methods=["GET", "POST"])
def edit_maintenance(log_id):
    """
    Edit an existing maintenance log.
    """
    db = get_db()
    log = db.execute(
        "SELECT * FROM maintenance_logs WHERE log_id = ?",
        (log_id,),
    ).fetchone()

    if log is None:
        return "Maintenance log not found", 404

    if request.method == "POST":
        vehicle_id = request.form.get("vehicle_id")
        service_date = request.form.get("service_date")
        service_type = request.form.get("service_type")
        description = request.form.get("description")
        odometer_raw = request.form.get("odometer_at_service")
        vendor = request.form.get("vendor") or None
        cost_raw = request.form.get("cost")

        odometer_at_service = int(odometer_raw) if odometer_raw else None
        cost = float(cost_raw) if cost_raw else None

        db.execute(
            """
            UPDATE maintenance_logs
            SET vehicle_id = ?,
                service_date = ?,
                service_type = ?,
                description = ?,
                odometer_at_service = ?,
                vendor = ?,
                cost = ?
            WHERE log_id = ?
            """,
            (
                vehicle_id,
                service_date,
                service_type,
                description,
                odometer_at_service,
                vendor,
                cost,
                log_id,
            ),
        )
        log_audit(
            db,
            action="UPDATE",
            table_name="maintenance_logs",
            record_id=log_id,
            user="demo_user",
            details=f"Updated maintenance log {log_id}",
        )
        db.commit()
        return redirect(url_for("list_maintenance"))

    vehicles = db.execute(
        "SELECT vehicle_id, type FROM vehicles WHERE status != 'retired' ORDER BY vehicle_id"
    ).fetchall()

    return render_template(
        "maintenance_form.html",
        log=log,
        vehicles=vehicles,
        form_action=url_for("edit_maintenance", log_id=log_id),
        is_edit=True,
        error=None,
    )

@app.route("/maintenance/<int:log_id>/delete", methods=["POST"])
def delete_maintenance(log_id):
    """
    Delete a maintenance log entry.
    """
    db = get_db()
    db.execute(
        "DELETE FROM maintenance_logs WHERE log_id = ?",
        (log_id,),
    )
    log_audit(
        db,
        action="DELETE",
        table_name="maintenance_logs",
        record_id=log_id,
        user="demo_user",
        details=f"Deleted maintenance log {log_id}",
    )
    db.commit()
    return redirect(url_for("list_maintenance"))

# ---------- AUDITS ----------
@app.route("/audit")
def view_audit_log():
    """
    Show recent audit log entries (most recent first).
    """
    db = get_db()
    rows = db.execute(
        """
        SELECT audit_id,
               timestamp,
               action,
               table_name,
               record_id,
               user,
               details
        FROM audit_log
        ORDER BY timestamp DESC
        LIMIT 200
        """
    ).fetchall()
    return render_template("audit_log.html", rows=rows)

if __name__ == "__main__":
    app.run(debug=True)