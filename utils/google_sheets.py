import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime

class SheetManager:
    def __init__(self, spreadsheet_id=None, credentials_path="service_account.json"):
        self.spreadsheet_id = spreadsheet_id
        self.credentials_path = credentials_path
        self.gc = None
        self.sheet = None
        self._authenticate()

    def _authenticate(self):
        # We try to load credentials from file, or fall back to env var
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        try:
            if os.path.exists(self.credentials_path):
                creds = Credentials.from_service_account_file(self.credentials_path, scopes=scopes)
            elif os.getenv("GOOGLE_SHEETS_CREDENTIALS"):
                import json
                creds_dict = json.loads(os.getenv("GOOGLE_SHEETS_CREDENTIALS"))
                creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            else:
                print("[WARN] No Google Sheets credentials found. Service will be inactive.")
                return

            self.gc = gspread.authorize(creds)
            
            if self.spreadsheet_id:
                self.sheet = self.gc.open_by_key(self.spreadsheet_id).get_worksheet(0)
            else:
                # Try to open or create "Fastigo Leads"
                try:
                    self.sheet = self.gc.open("Fastigo Leads").get_worksheet(0)
                except gspread.SpreadsheetNotFound:
                    sp = self.gc.create("Fastigo Leads")
                    self.sheet = sp.get_worksheet(0)
                    self.sheet.append_row(["Timestamp", "Customer Name", "Service Interest", "Details/Budget", "Session ID"])
            
            print("[INFO] Google Sheets connected successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to connect to Google Sheets: {e}")

    def capture_lead(self, name: str, service: str, details: str, session_id: str):
        if not self.sheet:
            print("[WARN] Sheet not connected. Lead data:", {name, service, details})
            return False
            
        try:
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                name,
                service,
                details,
                session_id
            ]
            self.sheet.append_row(row)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to append lead to Google Sheets: {e}")
            return False
