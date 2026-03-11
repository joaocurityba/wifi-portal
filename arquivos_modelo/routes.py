from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app import db
from app.models import Guest
from app.unifi import UnifiController
from app.util import validate_email
import os

bp = Blueprint("routes", __name__)

def get_unifi_controller():
    """
    Create a fresh UnifiController instance for each request.
    This ensures we always have a valid connection and authentication.
    """
    try:
        controller = UnifiController()
        
        # Test basic connectivity first
        if not controller.test_connection():
            current_app.logger.error("Cannot connect to UniFi controller")
            return None
            
        # Authenticate with the controller
        if not controller.login():
            current_app.logger.error("Failed to authenticate with UniFi controller")
            return None
            
        return controller
        
    except Exception as e:
        current_app.logger.error(f"Error creating UniFi controller: {e}")
        return None

@bp.route("/", methods=["GET"])
def portal_login():
    """
    Display the captive portal login page.
    UniFi typically passes parameters via GET for initial load.
    """
    # Get UniFi parameters from query string (typical captive portal flow)
    mac = request.args.get('id', '')  # UniFi passes MAC as 'id'
    ip = request.args.get('ip', '')
    ap_mac = request.args.get('ap', '')
    ssid = request.args.get('ssid', '')
    
    # Log the captive portal access
    current_app.logger.info(f"Portal access - MAC: {mac}, IP: {ip}, SSID: {ssid}")
    
    return render_template("login.html", 
                         mac=mac, 
                         ip=ip, 
                         ap_mac=ap_mac, 
                         ssid=ssid)

@bp.route("/authenticate", methods=["POST"])
def authenticate():
    """
    Handle email submission and authorize guest with UniFi controller.
    """
    # Retrieve form data
    email = request.form.get("email")
    mac = request.form.get("mac") 
    ip = request.form.get("ip")
    ap_mac = request.form.get("ap_mac")
    ssid = request.form.get("ssid")
    
    # Log the authentication attempt
    current_app.logger.info(f"Authentication attempt - Email: {email}, MAC: {mac}")
    
    # Basic validation
    if not email or not validate_email(email):
        flash("Please enter a valid email address.")
        return redirect(url_for("routes.portal_login", 
                              id=mac, ip=ip, ap=ap_mac, ssid=ssid))
    
    if not mac:
        flash("Device MAC address is required.")
        return redirect(url_for("routes.portal_login"))
    
    # Create guest record
    guest = Guest(email=email, mac=mac, ip=ip, ap_mac=ap_mac, ssid=ssid)
    
    try:
        # Get a fresh UniFi controller instance
        unifi_controller = get_unifi_controller()
        
        if not unifi_controller:
            current_app.logger.error("Could not initialize UniFi controller")
            flash("System temporarily unavailable. Please try again later.")
            return redirect(url_for("routes.portal_login", 
                                  id=mac, ip=ip, ap=ap_mac, ssid=ssid))

        # Authorize the guest using their MAC address
        current_app.logger.info(f"Attempting to authorize MAC: {mac}")
        
        if not unifi_controller.authorize_guest(mac, minutes=60):
            current_app.logger.error(f"Failed to authorize guest MAC: {mac}")
            flash("Authorization failed. Please try again or contact support.")
            return redirect(url_for("routes.portal_login", 
                                  id=mac, ip=ip, ap=ap_mac, ssid=ssid))
        
        # If authorization successful, save guest record
        guest.authorized = True
        db.session.add(guest)
        db.session.commit()
        
        current_app.logger.info(f"Successfully authorized guest: {email} ({mac})")
        
        # Redirect to success page with UniFi continue URL if available
        continue_url = request.form.get('url') or request.args.get('url')
        return redirect(url_for("routes.success", url=continue_url))
        
    except Exception as e:
        # Catch any unexpected errors
        current_app.logger.error(f"Unexpected error during authentication: {e}")
        flash("An unexpected error occurred. Please try again.")
        
        # Rollback any database changes
        db.session.rollback()
        
        return redirect(url_for("routes.portal_login", 
                              id=mac, ip=ip, ap=ap_mac, ssid=ssid))

@bp.route("/success")
def success():
    """
    Display success page after authorization.
    """
    # Get continue URL for redirecting user back to internet
    continue_url = request.args.get('url')
    
    return render_template("success.html", continue_url=continue_url)

@bp.route("/admin")
def admin():
    """
    Simple admin panel to view guest records.
    In production, you should add proper authentication here.
    """
    try:
        # Fetch all guests and order by creation date
        guests = Guest.query.order_by(Guest.created_at.desc()).limit(100).all()
        
        # Get some basic stats
        total_guests = Guest.query.count()
        authorized_guests = Guest.query.filter_by(authorized=True).count()
        
        return render_template("admin.html", 
                             guests=guests,
                             total_guests=total_guests,
                             authorized_guests=authorized_guests)
                             
    except Exception as e:
        current_app.logger.error(f"Error in admin panel: {e}")
        flash("Error loading admin data.")
        return render_template("admin.html", guests=[], total_guests=0, authorized_guests=0)

@bp.route("/health")
def health_check():
    """
    Health check endpoint to verify system status.
    """
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = "OK"
    except:
        db_status = "ERROR"
    
    # Test UniFi controller connection
    try:
        controller = UnifiController()
        if controller.test_connection():
            unifi_status = "OK"
        else:
            unifi_status = "CONNECTION_ERROR"
    except:
        unifi_status = "ERROR"
    
    status = {
        "database": db_status,
        "unifi_controller": unifi_status,
        "overall": "OK" if db_status == "OK" and unifi_status == "OK" else "ERROR"
    }
    
    return status, 200 if status["overall"] == "OK" else 503

@bp.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors gracefully"""
    return render_template('404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors gracefully"""
    db.session.rollback()
    current_app.logger.error(f"Internal server error: {error}")
    return render_template('500.html'), 500