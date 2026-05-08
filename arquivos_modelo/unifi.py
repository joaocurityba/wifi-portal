import requests
import urllib3
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
from dotenv import load_dotenv

load_dotenv()

# Suppress SSL warnings
urllib3.disable_warnings(InsecureRequestWarning)

class UnifiController:
    """
    UniFi Controller API client using username/password authentication (no 2FA)
    Supports guest authorization, client retrieval, and basic health checks.
    """
    def __init__(self):
        self.UNIFI_BASE_URL = os.getenv("UNIFI_BASE_URL")
        self.UNIFI_USERNAME = os.getenv("UNIFI_USERNAME")
        self.UNIFI_PASSWORD = os.getenv("UNIFI_PASSWORD")
        self.UNIFI_SITE = os.getenv("UNIFI_SITE")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Spotipo-Captive-Portal/1.0"
        })
        
    def login(self):
        """
        Log in to UniFi controller using username/password.
        Returns True if successful, False otherwise.
        """
        if not self.UNIFI_USERNAME or not self.UNIFI_PASSWORD:
            print("UNIFI_USERNAME or UNIFI_PASSWORD not set")
            return False
        
        payload = {
            "username": self.UNIFI_USERNAME,
            "password": self.UNIFI_PASSWORD,
            "remember": True
        }
        
        endpoints = ["/api/auth/login", "/api/login"]
        
        for ep in endpoints:
            url = f"{self.UNIFI_BASE_URL}{ep}"
            try:
                resp = self.session.post(url, json=payload, verify=False, allow_redirects=False, timeout=10)
                print(f"Login attempt to {url}: Status {resp.status_code}")
                
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        if data.get("meta", {}).get("rc") == "ok":
                            print("Login successful!")
                            return True
                    except json.JSONDecodeError:
                        print("Login successful (non-JSON response)")
                        return True
                elif resp.status_code in [302, 303, 307]:
                    location = resp.headers.get("Location", "")
                    if "login" not in location.lower():
                        print("Login successful (redirect)!")
                        return True
            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
        
        print("Login failed")
        return False
    
    def authorize_guest(self, mac, minutes=60):
        """
        Authorize a guest by MAC address.
        Returns True if successful, False otherwise.
        """
        if not mac:
            print("MAC address is required")
            return False
        
        mac = mac.lower().replace("-", ":").replace(".", ":")
        url = f"{self.UNIFI_BASE_URL}/api/s/{self.UNIFI_SITE}/cmd/stamgr"
        payload = {"cmd": "authorize-guest", "mac": mac, "minutes": int(minutes)}
        
        try:
            resp = self.session.post(url, json=payload, verify=False, timeout=10)
            print(f"Authorize guest {mac}: Status {resp.status_code}")
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if data.get("meta", {}).get("rc") == "ok":
                        print(f"Guest {mac} authorized")
                        return True
                    else:
                        print(f"Authorization failed: {data}")
                except json.JSONDecodeError:
                    print(f"Guest {mac} authorized (non-JSON response)")
                    return True
            elif resp.status_code in [401, 403]:
                print(f"Authorization failed: {resp.status_code}")
            else:
                print(f"Authorization error {resp.status_code}: {resp.text[:200]}")
        except requests.exceptions.RequestException as e:
            print(f"Authorization request error: {e}")
        
        return False
    
    def get_clients(self):
        """
        Get all connected clients.
        Returns a list of clients.
        """
        url = f"{self.UNIFI_BASE_URL}/api/s/{self.UNIFI_SITE}/stat/sta"
        try:
            resp = self.session.get(url, verify=False, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("meta", {}).get("rc") == "ok":
                    clients = data.get("data", [])
                    print(f"Found {len(clients)} clients")
                    return clients
            print(f"Failed to get clients: Status {resp.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Get clients error: {e}")
        return []
    
    def health(self):
        """
        Get controller health status.
        """
        url = f"{self.UNIFI_BASE_URL}/api/s/{self.UNIFI_SITE}/stat/health"
        try:
            resp = self.session.get(url, verify=False, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("meta", {}).get("rc") == "ok":
                    print("Controller health OK")
                    return data.get("data", {})
            print(f"Health check failed: Status {resp.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Health check error: {e}")
        return {}
    
    def test_connection(self):
        """
        Test if the controller is reachable.
        """
        try:
            resp = self.session.get(f"{self.UNIFI_BASE_URL}/", verify=False, timeout=5)
            print(f"Connection test: Status {resp.status_code}")
            return resp.status_code < 500
        except requests.exceptions.RequestException as e:
            print(f"Connection test failed: {e}")
            return False

# Example usage
if __name__ == "__main__":
    uc = UnifiController()
    
    if uc.test_connection():
        print("Controller reachable")
        
        if uc.login():
            print("Logged in successfully")
            
            print("Fetching clients...")
            clients = uc.get_clients()
            
            print("Controller health...")
            uc.health()
            
           
        else:
            print("Login failed")
    else:
        print("Cannot reach controller")
