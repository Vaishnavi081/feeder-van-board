from flask import Flask, render_template, request, make_response, jsonify, redirect, url_for
from datetime import datetime
import uuid
import db
import landmarks

app = Flask(__name__)

def get_device_id():
    device_id = request.cookies.get('fvb_device_id')
    if not device_id:
        device_id = "dev_" + uuid.uuid4().hex
    return device_id

def time_to_minutes(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m

def now_minutes():
    n = datetime.now()
    return n.hour * 60 + n.minute

def format_time(t):
    h, m = map(int, t.split(":"))
    period = "AM" if h < 12 else "PM"
    h12 = 12 if h % 12 == 0 else h % 12
    return f"{h12}:{str(m).zfill(2)} {period}"

def minutes_ago(ts):
    import time
    mins = round((time.time() * 1000 - ts) / 60000)
    if mins < 1: return "just now"
    if mins < 60: return f"{mins} min ago"
    hrs = round(mins / 60)
    return f"{hrs} hr ago"

def minutes_until(trip_time):
    diff = time_to_minutes(trip_time) - now_minutes()
    if diff < 0: return None
    if diff == 0: return "now"
    if diff < 60: return f"in {diff} min"
    hrs = diff // 60
    mins = diff % 60
    return f"in {hrs} hr {mins} min" if mins > 0 else f"in {hrs} hr"

# Make helper functions available to Jinja2
app.jinja_env.globals.update(
    format_time=format_time,
    minutes_ago=minutes_ago,
    minutes_until=minutes_until,
    time_to_minutes=time_to_minutes,
    now_minutes=now_minutes,
    landmark_by_id=landmarks.LANDMARKS_BY_ID,
    ROUTES=landmarks.ROUTES,
    route_label=landmarks.route_label
)

@app.route("/")
def index():
    route_filter = request.args.get('route', 'all')
    device_id = get_device_id()
    
    trips = db.Board.list_today()
    
    # Process trips for view
    for t in trips:
        t['already_confirmed'] = db.Board.have_i_confirmed(device_id, t['id'])
        t['already_reported'] = db.Board.have_i_reported(device_id, t['id'])
        t['my_trip'] = (t.get('deviceId') == device_id)
    
    response = make_response(render_template(
        'index.html',
        current_filter=route_filter,
        trips=trips,
        today_label=datetime.now().strftime("%a, %b %d")
    ))
    
    if not request.cookies.get('fvb_device_id'):
        response.set_cookie('fvb_device_id', device_id, max_age=60*60*24*365)
        
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
        
    return response

@app.route("/trips")
def trips_partial():
    route_filter = request.args.get('route', 'all')
    device_id = get_device_id()
    trips = db.Board.list_today()
    for t in trips:
        t['already_confirmed'] = db.Board.have_i_confirmed(device_id, t['id'])
        t['already_reported'] = db.Board.have_i_reported(device_id, t['id'])
        t['my_trip'] = (t.get('deviceId') == device_id)
        
    return render_template('partials/board.html', current_filter=route_filter, trips=trips)

@app.route("/landmarks")
def search_landmarks_html():
    query = request.args.get('q', '')
    route_id = request.args.get('routeId', '')
    results = landmarks.search_landmarks(query, route_id)
    return render_template('partials/landmark_options.html', options=results, query=query.lower())

@app.route("/submit", methods=['POST'])
def submit():
    device_id = get_device_id()
    
    route_id = request.form.get('routeId')
    landmark_id = request.form.get('landmarkId')
    time = request.form.get('time')
    vehicle_number = request.form.get('vehicleNumber')
    note = request.form.get('note')
    
    if not landmark_id or not time or not route_id:
        missing = []
        if not route_id: missing.append("route")
        if not landmark_id: missing.append("pickup stop")
        if not time: missing.append("departure time")
        return f"<p class='form-msg error-banner'>⚠️ Please fill in: {', '.join(missing)}.</p>", 400
        
    try:
        # Validate time format (must be HH:MM and parseable)
        h, m = map(int, time.split(":"))
        if h < 0 or h > 23 or m < 0 or m > 59:
            raise ValueError()
        # Ensure minutes are in 5-minute increments as required by UI
        if m % 5 != 0:
            raise ValueError()

    except (ValueError, AttributeError):
        return "<p class='form-msg error-banner'>⚠️ The time format looks wrong. Please scroll the time wheel to set a valid time.</p>", 400
        
    # Validate route and landmark
    if landmark_id.startswith("custom:"):
        # Free-text stop: user typed a stop name not in the list
        custom_name = landmark_id[len("custom:"):].strip()
        if not custom_name:
            return "<p class='form-msg error-banner'>⚠️ Please type a stop name.</p>", 400
        # Use the custom name as the canonical landmark text
        landmark_id = "custom:" + custom_name
    else:
        valid_stops = [l['id'] for l in landmarks.get_stops_for_route(route_id)]
        if not valid_stops or landmark_id not in valid_stops:
            return "<p class='form-msg error-banner'>⚠️ That stop doesn't exist on this route. Please search and tap a stop from the list.</p>", 400
        
    rate = db.Board.check_rate_limit(device_id)
    if not rate['ok']:
        return f"<p class='form-msg error-banner'>⏳ {rate['reason']}</p>", 400
        
    force = request.form.get('force', 'false') == 'true'
    
    if not force:
        dup = db.Board.find_likely_duplicate(route_id, landmark_id, time)
        if dup:
            return render_template('partials/dup_dialog.html', 
                                   existing=dup, 
                                   form_data=request.form), 200

    db.Board.submit_trip(route_id, landmark_id, time, vehicle_number, note, device_id)
    db.Board.record_submit(device_id)
    
    # Send a header to trigger client-side close of modal and toast
    resp = make_response(render_template('partials/board_updater.html'))
    resp.headers['HX-Trigger'] = '{"toast": "Van logged. Thanks for helping the board!", "closeSheet": ""}'
    return resp

@app.route("/confirm/<trip_id>", methods=['POST'])
def confirm(trip_id):
    device_id = get_device_id()
    res = db.Board.confirm_trip(device_id, trip_id)
    
    if not res['ok']:
        resp = make_response("")
        resp.headers['HX-Trigger'] = f'{{"toast": "{res["reason"]}"}}'
        return resp
        
    resp = make_response(render_template('partials/trip_bottom.html', trip=res['trip'], already_confirmed=True))
    resp.headers['HX-Trigger'] = '{"toast": "Thanks - marked as confirmed."}'
    return resp

@app.route("/delete/<trip_id>", methods=['POST'])
def delete_trip(trip_id):
    device_id = get_device_id()
    res = db.Board.delete_trip(device_id, trip_id)
    if not res['ok']:
        resp = make_response("")
        resp.headers['HX-Trigger'] = f'{{"toast": "{res["reason"]}"}}'
        return resp
    # Return empty article so HTMX removes the card
    resp = make_response("")
    resp.headers['HX-Trigger'] = '{"toast": "Trip deleted.", "updateBoard": ""}'
    return resp

@app.route("/report/<trip_id>", methods=['POST'])
def report(trip_id):
    device_id = get_device_id()
    res = db.Board.report_trip(device_id, trip_id)
    
    if not res['ok']:
        resp = make_response("")
        resp.headers['HX-Trigger'] = f'{{"toast": "{res["reason"]}"}}'
        return resp
        
    resp = make_response(render_template('partials/trip_actions.html', trip=res['trip'], already_reported=True))
    resp.headers['HX-Trigger'] = '{"toast": "Reported - thanks for helping keep the board accurate."}'
    return resp

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
