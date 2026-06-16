import os
import json
import threading
from datetime import datetime

from flask import Flask, request, jsonify

# ----------------------------
# Configuration
# ----------------------------
# JSON file used as storage (no database)
DATA_FILE = "courses.json"

# Simple in-process lock to make reads/writes safer in this tutorial
LOCK = threading.Lock()

# Allowed statuses for a course
ALLOWED_STATUSES = {"Not Started", "In Progress", "Completed"}


# ----------------------------
# Helper utilities (beginner-friendly)
# ----------------------------
def ensure_data_store():
    """
    Ensure the JSON storage file exists.
    If it doesn't, create it and initialize with an empty list.
    """
    if not os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
        except OSError as e:
            # Fail fast with a clear message (useful during learning)
            raise RuntimeError(f"Failed to create data store '{DATA_FILE}': {e}")


def load_courses():
    """
    Load all courses from the JSON file.
    Returns a list of course dicts.
    """
    with LOCK:
        try:
            if not os.path.exists(DATA_FILE):
                return []
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
                if isinstance(data, list):
                    return data
                else:
                    # Safety: reset to empty if data is not a list
                    return []
        except json.JSONDecodeError:
            # Corrupted or empty file treated as empty
            return []
        except IOError as e:
            # Propagate I/O errors to the caller for proper error handling
            raise e


def save_courses(courses):
    """
    Persist the list of courses to the JSON file.
    Uses a lock to ensure exclusive write access.
    """
    with LOCK:
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(courses, f, indent=2)
        except IOError as e:
            raise e


def next_id(courses):
    """
    Compute the next auto-incremented ID for a new course.
    """
    if not courses:
        return 1
    return max(course.get("id", 0) for course in courses) + 1


def is_valid_date(date_str):
    """
    Validate that a date string is in YYYY-MM-DD format.
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def current_timestamp():
    """
    Return an ISO-like UTC timestamp for created_at.
    Example: 2024-07-01T12:34:56Z
    """
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def error_response(message, status_code=400):
    """
    Convenience wrapper to return a JSON error response with an HTTP status.
    """
    return jsonify({"error": message}), status_code


# ----------------------------
# Flask app initialization
# ----------------------------
app = Flask(__name__)

# Ensure the data store exists on startup
ensure_data_store()


# ----------------------------
# API Endpoints (REST)
# ----------------------------
# Notes:
# - POST /api/courses: add a new course
# - GET /api/courses: get all courses
# - GET /api/courses/ with ?id=<id>: get a specific course
# - PUT /api/courses/: update a course (payload must include id)
# - DELETE /api/courses/: delete a course (payload must include id)

# GET /api/courses and POST /api/courses
# Also support trailing slash variant
@app.route("/api/courses", methods=["GET", "POST"])
@app.route("/api/courses/", methods=["GET", "POST"])
def courses_root():
    """
    - GET: If query param 'id' is provided, return that course.
           Otherwise, return all courses.
    - POST: Create a new course (requires name, description, target_date, status)
    """
    if request.method == "GET":
        course_id_param = request.args.get("id")
        if course_id_param:
            # Get a specific course by id (from query string)
            try:
                cid = int(course_id_param)
            except ValueError:
                return error_response("Invalid course id", 400)

            try:
                courses = load_courses()
            except Exception:
                return error_response("Failed to read data file.", 500)

            course = next((c for c in courses if c.get("id") == cid), None)
            if not course:
                return error_response("Course not found", 404)
            return jsonify(course), 200

        # No id provided -> return all courses
        try:
            courses = load_courses()
        except Exception:
            return error_response("Failed to read data file.", 500)
        return jsonify(courses), 200

    else:  # POST
        payload = request.get_json(force=True) if request.data else None
        if not isinstance(payload, dict):
            return error_response("Invalid payload. Expecting a JSON object.", 400)

        name = payload.get("name")
        description = payload.get("description")
        target_date = payload.get("target_date")
        status = payload.get("status")

        # Validate required fields
        if not name:
            return error_response("Missing required field: name", 400)
        if not description:
            return error_response("Missing required field: description", 400)
        if not target_date:
            return error_response("Missing required field: target_date", 400)
        if not is_valid_date(target_date):
            return error_response("target_date must be in YYYY-MM-DD format", 400)
        if not status:
            return error_response("Missing required field: status", 400)
        if status not in ALLOWED_STATUSES:
            return error_response(
                "status must be one of: Not Started, In Progress, Completed", 400
            )

        # Load existing data
        try:
            courses = load_courses()
        except Exception:
            return error_response("Failed to read data file.", 500)

        # Create new course object
        course = {
            "id": next_id(courses),
            "name": name,
            "description": description,
            "target_date": target_date,
            "status": status,
            "created_at": current_timestamp()
        }

        # Persist
        courses.append(course)
        try:
            save_courses(courses)
        except Exception:
            return error_response("Failed to write data file.", 500)

        return jsonify(course), 201


# PUT /api/courses/ and DELETE /api/courses/
@app.route("/api/courses/", methods=["PUT", "DELETE"])
def update_or_delete_course():
    """
    - PUT: Update an existing course.
           Payload must include id and at least one updatable field
    - DELETE: Delete a course by id (provided in payload)
    """
    # Expect a JSON body with at least an 'id'
    payload = request.get_json(force=True) if request.data else None
    if not isinstance(payload, dict) or "id" not in payload:
        return error_response("Missing required field: id (in JSON body)", 400)

    course_id = payload.get("id")

    try:
        courses = load_courses()
    except Exception:
        return error_response("Failed to read data file.", 500)

    course = next((c for c in courses if c.get("id") == course_id), None)
    if not course:
        return error_response("Course not found", 404)

    if request.method == "PUT":
        updated = False

        if "name" in payload:
            if not payload["name"]:
                return error_response("Invalid value for name.", 400)
            course["name"] = payload["name"]
            updated = True

        if "description" in payload:
            if not payload["description"]:
                return error_response("Invalid value for description.", 400)
            course["description"] = payload["description"]
            updated = True

        if "target_date" in payload:
            if not payload["target_date"] or not is_valid_date(payload["target_date"]):
                return error_response("Invalid target_date. Use YYYY-MM-DD", 400)
            course["target_date"] = payload["target_date"]
            updated = True

        if "status" in payload:
            if payload["status"] not in ALLOWED_STATUSES:
                return error_response(
                    "Invalid status. Must be: Not Started, In Progress, Completed", 400
                )
            course["status"] = payload["status"]
            updated = True

        if not updated:
            return error_response("No valid fields provided to update.", 400)

        try:
            save_courses(courses)
        except Exception:
            return error_response("Failed to write data file.", 500)

        return jsonify(course), 200

    else:  # DELETE
        index = next((i for i, c in enumerate(courses) if c.get("id") == course_id), None)
        if index is None:
            return error_response("Course not found", 404)

        removed = courses.pop(index)

        try:
            save_courses(courses)
        except Exception:
            return error_response("Failed to write data file.", 500)

        return jsonify({"message": "Deleted", "deleted": removed}), 200

# GET /api/courses/stats
# GET /api/courses/stats/
@app.route("/api/courses/stats", methods=["GET"])
@app.route("/api/courses/stats/", methods=["GET"])
def courses_stats():
    """
    Return simple statistics about the courses:
    - total: total number of courses
    - by_status: counts per status
        - Not Started
        - In Progress
        - Completed
    """
    try:
        courses = load_courses()
    except Exception:
        return error_response("Failed to read data file.", 500)

    total = len(courses)

    by_status = {
        "Not Started": 0,
        "In Progress": 0,
        "Completed": 0
    }

    # Count courses by their status
    for c in courses:
        status = c.get("status")
        if status in by_status:
            by_status[status] += 1
        # If a course has an unknown status, we ignore it in this simple stats view

    stats = {
        "total": total,
        "by_status": by_status
    }

    return jsonify(stats), 200

# Optional: root health check
@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "CodeCraftHub API - Flask + JSON storage"}), 200


# ----------------------------
# Run the app
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)