import os
import sys
import json
import requests
import urllib3
import xml.etree.ElementTree as ET

urllib3.disable_warnings()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.repositories.base import SessionLocal
from app.models.entities import AuditEvent

SPLUNK_URL = "https://127.0.0.1:8089"
SPLUNK_USER = "admin"
SPLUNK_PASS = "rajkushal"
INDEX_NAME = "warehouse_security"

def setup_splunk():
    print("[1/4] Authenticating with Splunk REST API...")
    r = requests.post(
        f"{SPLUNK_URL}/services/auth/login",
        data={"username": SPLUNK_USER, "password": SPLUNK_PASS},
        verify=False,
        timeout=10
    )
    if r.status_code != 200:
        print(f"Failed to authenticate: {r.status_code} {r.text}")
        return False

    token = ET.fromstring(r.text).findtext("sessionKey")
    headers = {"Authorization": f"Splunk {token}"}
    print("      -> Successfully authenticated as admin!")

    print(f"[2/4] Ensuring index '{INDEX_NAME}' exists...")
    r_idx = requests.post(
        f"{SPLUNK_URL}/services/data/indexes",
        data={"name": INDEX_NAME},
        headers=headers,
        verify=False
    )
    if r_idx.status_code in [201, 409]:
        print(f"      -> Index '{INDEX_NAME}' is ready.")
    else:
        print(f"      -> Index status: {r_idx.status_code}")

    print("[3/4] Ingesting all AWMS Warehouse Audit Events into Splunk...")
    db = SessionLocal()
    events = db.query(AuditEvent).order_by(AuditEvent.timestamp.asc()).all()
    print(f"      -> Found {len(events)} database audit events to ingest.")

    count = 0
    for e in events:
        meta_dict = {}
        try:
            if e.metadata_json:
                meta_dict = json.loads(e.metadata_json)
        except Exception:
            pass

        meta_str = " ".join([f"{k}=\"{v}\"" for k, v in meta_dict.items() if isinstance(v, (str, int, float, bool))])
        
        # Standard Key-Value format for automatic Splunk field extraction
        payload = (
            f"{e.timestamp.strftime('%Y-%m-%d %H:%M:%S')} "
            f"system=\"AWMS\" project=\"System 23\" "
            f"event_id=\"{e.id}\" "
            f"actor_id=\"{e.actor_id}\" "
            f"actor_type=\"{e.actor_type}\" "
            f"action=\"{e.action}\" "
            f"target_entity=\"{e.target_entity}\" "
            f"target_id=\"{e.target_id or 'NONE'}\" "
            f"outcome=\"{e.outcome}\" "
            f"reason_code=\"{e.reason_code}\" "
            f"ip_address=\"{e.ip_address or '127.0.0.1'}\" "
            f"{meta_str}\n"
        )

        # Ingest into warehouse_security index
        r_post = requests.post(
            f"{SPLUNK_URL}/services/receivers/simple?index={INDEX_NAME}&sourcetype=awms:audit",
            data=payload,
            headers=headers,
            verify=False
        )
        # Also ingest into main index for general discovery
        requests.post(
            f"{SPLUNK_URL}/services/receivers/simple?index=main&sourcetype=awms:audit",
            data=payload,
            headers=headers,
            verify=False
        )
        if r_post.status_code == 200:
            count += 1

    db.close()
    print(f"      -> Successfully ingested {count} events into Splunk index '{INDEX_NAME}' and 'main'!")

    print("[4/4] Creating dedicated Splunk Dashboard 'awms_security_dashboard'...")
    dashboard_xml = """<dashboard version="1.1" theme="dark">
  <label>System 23: Autonomous Warehouse Management System (AWMS) - Security Operations</label>
  <description>24CYS401 Secure Software Engineering - Cyber-Physical Security, Fleet Telemetry &amp; Cryptographic Audit Trail</description>
  <row>
    <panel>
      <single>
        <title>Total Security Audit Events</title>
        <search>
          <query>index=warehouse_security OR index=main sourcetype="awms:audit" | stats count</query>
          <earliest>0</earliest>
          <latest>now</latest>
        </search>
        <option name="colorMode">block</option>
        <option name="rangeColors">["0x53a051","0x006d9c"]</option>
        <option name="useColors">1</option>
      </single>
    </panel>
    <panel>
      <single>
        <title>Successful Operations</title>
        <search>
          <query>index=warehouse_security OR index=main sourcetype="awms:audit" outcome="SUCCESS" | stats count</query>
          <earliest>0</earliest>
          <latest>now</latest>
        </search>
        <option name="colorMode">block</option>
        <option name="rangeColors">["0x53a051","0x53a051"]</option>
        <option name="useColors">1</option>
      </single>
    </panel>
    <panel>
      <single>
        <title>Security Alerts &amp; Denials</title>
        <search>
          <query>index=warehouse_security OR index=main sourcetype="awms:audit" outcome!="SUCCESS" | stats count</query>
          <earliest>0</earliest>
          <latest>now</latest>
        </search>
        <option name="colorMode">block</option>
        <option name="rangeColors">["0xdc4e41","0xdc4e41"]</option>
        <option name="useColors">1</option>
      </single>
    </panel>
    <panel>
      <single>
        <title>Active AGVs &amp; Actors</title>
        <search>
          <query>index=warehouse_security OR index=main sourcetype="awms:audit" | stats dc(actor_id) as count</query>
          <earliest>0</earliest>
          <latest>now</latest>
        </search>
        <option name="colorMode">block</option>
        <option name="rangeColors">["0xf8be34","0xf1813f"]</option>
        <option name="useColors">1</option>
      </single>
    </panel>
  </row>
  <row>
    <panel>
      <chart>
        <title>Security &amp; Operational Events Breakdown by Action</title>
        <search>
          <query>index=warehouse_security OR index=main sourcetype="awms:audit" | stats count by action</query>
          <earliest>0</earliest>
          <latest>now</latest>
        </search>
        <option name="charting.chart">pie</option>
        <option name="charting.drilldown">none</option>
      </chart>
    </panel>
    <panel>
      <chart>
        <title>Audit Outcome Distribution</title>
        <search>
          <query>index=warehouse_security OR index=main sourcetype="awms:audit" | stats count by outcome</query>
          <earliest>0</earliest>
          <latest>now</latest>
        </search>
        <option name="charting.chart">column</option>
        <option name="charting.drilldown">none</option>
      </chart>
    </panel>
  </row>
  <row>
    <panel>
      <table>
        <title>Real-Time Immutable Audit Log Trail</title>
        <search>
          <query>index=warehouse_security OR index=main sourcetype="awms:audit" | table _time actor_id actor_type action target_entity outcome reason_code ip_address</query>
          <earliest>0</earliest>
          <latest>now</latest>
        </search>
        <option name="count">10</option>
        <option name="drilldown">none</option>
      </table>
    </panel>
  </row>
  <row>
    <panel>
      <table>
        <title>Autonomous AGV Fleet Missions &amp; Dispatches</title>
        <search>
          <query>index=warehouse_security OR index=main sourcetype="awms:audit" action IN ("TASK_DISPATCH", "MISSION_COMPLETED", "EMERGENCY_STOP", "COLLISION_RECOVERY", "STOCK_RESERVE") | table _time actor_id action target_entity reason_code</query>
          <earliest>0</earliest>
          <latest>now</latest>
        </search>
        <option name="count">10</option>
        <option name="drilldown">none</option>
      </table>
    </panel>
  </row>
</dashboard>"""

    # Delete existing view if present, then recreate
    requests.delete(
        f"{SPLUNK_URL}/servicesNS/admin/search/data/ui/views/awms_security_dashboard",
        headers=headers,
        verify=False
    )
    
    r_dash = requests.post(
        f"{SPLUNK_URL}/servicesNS/admin/search/data/ui/views",
        data={"name": "awms_security_dashboard", "eai:data": dashboard_xml},
        headers=headers,
        verify=False
    )

    if r_dash.status_code in [200, 201]:
        print("      -> Dashboard 'awms_security_dashboard' created successfully!")
    else:
        print(f"      -> Dashboard creation response: {r_dash.status_code} {r_dash.text[:200]}")

    print("================================================================================")
    print("SPLUNK CONFIGURATION COMPLETE FOR SYSTEM 23 (AWMS)!")
    print("Direct Dashboard URL: http://127.0.0.1:8000/en-US/app/search/awms_security_dashboard")
    print("Search Query: index=warehouse_security")
    print("================================================================================")
    return True

if __name__ == "__main__":
    setup_splunk()
