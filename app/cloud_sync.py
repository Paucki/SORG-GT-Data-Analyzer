from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone

SUPABASE_URL = "https://cdhfmhxhhtqqoetlferj.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_r9xkC56K3zezl30297f1qQ_fsz6ztfl"


def _stamp(value):
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    text = str(value).strip().replace(" ", "T")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class CloudSync:
    """Synchronisiert die für PC und Mobile gemeinsam benötigten Kerndaten."""

    def __init__(self, database, user_session):
        self.db = database
        self.session = user_session
        self.team_id = getattr(user_session, "team_id", "") or ""
        self.token = getattr(user_session, "token", "") or ""
        self.enabled = bool(self.team_id and self.token)
        self._busy = False

    def _request(self, table, *, method="GET", query="", body=None, prefer=""):
        url = f"{SUPABASE_URL}/rest/v1/{table}"
        if query:
            url += "?" + query
        headers = {
            "apikey": SUPABASE_PUBLISHABLE_KEY,
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        data = None if body is None else json.dumps(body, default=str).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")
            raise RuntimeError(f"Cloud {table}: {detail or error}") from error

    def _uuid(self, table: str, legacy_id: int) -> str:
        return str(uuid.uuid5(uuid.UUID(self.team_id), f"{table}:{int(legacy_id)}"))

    def _rows(self, table):
        return list(self.db.all(f"SELECT * FROM {table}"))

    @staticmethod
    def _get(row, key, default=None):
        try:
            return row[key]
        except Exception:
            return default

    def _remote_legacy_ids(self, table):
        rows = self._request(
            table,
            query=urllib.parse.urlencode({
                "team_id": f"eq.{self.team_id}",
                "select": "id,legacy_id",
            }),
        ) or []
        result = {}
        for row in rows:
            legacy = row.get("legacy_id")
            if legacy is not None:
                result[int(legacy)] = str(row["id"])
        return result

    def _remote_meta(self, table):
        rows = self._request(
            table,
            query=urllib.parse.urlencode({
                "team_id": f"eq.{self.team_id}",
                "select": "id,legacy_id,created_at,updated_at",
            }),
        ) or []
        return {str(r["id"]): r for r in rows}

    def _upsert(self, table, records):
        if not records:
            return

        # PostgreSQL/Supabase setzt created_at/updated_at selbst per Default.
        # Lokale SQLite-Bestandsdaten haben updated_at häufig noch NULL.
        # Ein explizites JSON-null überschreibt den DB-Default und verletzt
        # die NOT-NULL-Constraints. Fehlende Zeitstempel daher nicht senden.
        cleaned = []
        for record in records:
            item = dict(record)
            if item.get("created_at") in (None, ""):
                item.pop("created_at", None)
            if item.get("updated_at") in (None, ""):
                item.pop("updated_at", None)
            cleaned.append(item)

        self._request(
            table,
            method="POST",
            query="on_conflict=id",
            body=cleaned,
            prefer="resolution=merge-duplicates,return=minimal",
        )

    def sync(self):
        if not self.enabled or self._busy:
            return
        self._busy = True
        try:
            self._pull_core()
            self._pull_measurements()
            self._push_core()
        finally:
            self._busy = False

    def _patch_legacy_id(self, table: str, remote_id: str, legacy_id: int) -> None:
        query = urllib.parse.urlencode({"id": f"eq.{remote_id}"})
        self._request(
            table,
            method="PATCH",
            query=query,
            body={"legacy_id": int(legacy_id)},
            prefer="return=minimal",
        )

    def _pull_core(self):
        """Zieht Mobile-/Cloud-Stammdaten in die lokale PC-Datenbank."""
        def remote(table):
            return self._request(
                table,
                query=urllib.parse.urlencode({
                    "team_id": f"eq.{self.team_id}",
                    "select": "*",
                }),
            ) or []

        tracks = remote("tracks")
        vehicles = remote("vehicles")
        drivers = remote("drivers")
        weekends = remote("race_weekends")
        sessions = remote("sessions")
        tyre_sets = remote("tyre_sets")

        track_map = {}
        for row in tracks:
            legacy = row.get("legacy_id")
            local = self.db.get_track(int(legacy)) if legacy is not None else None
            remote_time = _stamp(row.get("updated_at") or row.get("created_at"))
            local_time = _stamp((local["updated_at"] or local["created_at"]) if local else None)
            if local is None or remote_time > local_time:
                local_id = self.db.save_track(
                    int(legacy) if local is not None else None,
                    row.get("name") or "",
                    row.get("country") or "",
                    float(row.get("length_km") or 0),
                    int(row.get("corners") or 0),
                    row.get("address") or "",
                    row.get("latitude"),
                    row.get("longitude"),
                    row.get("notes") or "",
                )
            else:
                local_id = int(local["id"])
            track_map[str(row["id"])] = local_id
            if row.get("legacy_id") is None:
                self._patch_legacy_id("tracks", str(row["id"]), local_id)

        car_map = {}
        for row in vehicles:
            legacy = row.get("legacy_id")
            local = self.db.get_car(int(legacy)) if legacy is not None else None
            remote_time = _stamp(row.get("updated_at") or row.get("created_at"))
            local_time = _stamp((local["updated_at"] or local["created_at"]) if local else None)
            if local is None or remote_time > local_time:
                local_id = self.db.save_car(
                    int(legacy) if local is not None else None,
                    row.get("manufacturer") or "",
                    row.get("model") or row.get("name") or "",
                    row.get("vehicle_class") or "",
                    int(row.get("year") or 0),
                    float(row.get("weight_kg") or 0),
                    float(row.get("horsepower") or 0),
                    row.get("drive_type") or "",
                    row.get("notes") or "",
                    str(row.get("start_number") or ""),
                )
            else:
                local_id = int(local["id"])
            car_map[str(row["id"])] = local_id
            if row.get("legacy_id") is None:
                self._patch_legacy_id("vehicles", str(row["id"]), local_id)

        driver_map = {}
        for row in drivers:
            legacy = row.get("legacy_id")
            local = self.db.get_driver(int(legacy)) if legacy is not None else None
            remote_time = _stamp(row.get("updated_at") or row.get("created_at"))
            local_time = _stamp((local["updated_at"] or local["created_at"]) if local else None)
            if local is None or remote_time > local_time:
                first = row.get("first_name") or ""
                last = row.get("last_name") or ""
                if not first and not last:
                    parts = str(row.get("name") or "").split(" ", 1)
                    first = parts[0] if parts else ""
                    last = parts[1] if len(parts) > 1 else ""
                local_id = self.db.save_driver(
                    int(legacy) if local is not None else None,
                    first,
                    last,
                    row.get("nickname") or "",
                    str(row.get("race_number") or row.get("number") or ""),
                    row.get("licence_class") or "",
                    row.get("notes") or "",
                )
            else:
                local_id = int(local["id"])
            driver_map[str(row["id"])] = local_id
            if row.get("legacy_id") is None:
                self._patch_legacy_id("drivers", str(row["id"]), local_id)

        event_map = {}
        for row in weekends:
            remote_track = str(row.get("track_id") or "")
            track_id = track_map.get(remote_track)
            if track_id is None:
                continue
            legacy = row.get("legacy_id")
            local = self.db.get_event(int(legacy)) if legacy is not None else None
            remote_time = _stamp(row.get("updated_at") or row.get("created_at"))
            local_time = _stamp((local["updated_at"] or local["created_at"]) if local else None)
            if local is None or remote_time > local_time:
                local_id = self.db.save_event(
                    int(legacy) if local is not None else None,
                    row.get("name") or "",
                    track_id,
                    row.get("start_date") or "",
                    row.get("end_date") or "",
                    row.get("championship") or "",
                    row.get("event_type") or "",
                    row.get("notes") or "",
                )
            else:
                local_id = int(local["id"])
            event_map[str(row["id"])] = local_id
            if row.get("legacy_id") is None:
                self._patch_legacy_id("race_weekends", str(row["id"]), local_id)

        session_map = {}
        remote_session_by_id = {}
        for row in sessions:
            remote_session_by_id[str(row["id"])] = row
            event_id = event_map.get(str(row.get("race_weekend_id") or ""))
            car_id = car_map.get(str(row.get("vehicle_id") or ""))
            driver_id = driver_map.get(str(row.get("driver_id") or "")) if row.get("driver_id") else None
            if event_id is None or car_id is None:
                continue
            legacy = row.get("legacy_id")
            local = self.db.get_session(int(legacy)) if legacy is not None else None
            remote_time = _stamp(row.get("updated_at") or row.get("created_at"))
            local_time = _stamp((local["updated_at"] or local["created_at"]) if local else None)
            if local is None or remote_time > local_time:
                local_id = self.db.save_session(
                    int(legacy) if local is not None else None,
                    event_id,
                    car_id,
                    driver_id,
                    row.get("session_type") or "Session",
                    row.get("session_date") or row.get("measured_at") or "",
                    row.get("weather") or "",
                    float(row.get("air_temperature") or 0),
                    float(row.get("track_temperature") or 0),
                    float(row.get("rim_temp_c") or 0),
                    float(row.get("humidity_percent") or 0),
                    row.get("notes") or "",
                )
            else:
                local_id = int(local["id"])
            session_map[str(row["id"])] = local_id
            if row.get("legacy_id") is None:
                self._patch_legacy_id("sessions", str(row["id"]), local_id)

        # Cloud-Reifensätze werden einer Session über sessions.tyre_set_id zugeordnet.
        set_session = {}
        for row in sessions:
            remote_set = row.get("tyre_set_id")
            if remote_set:
                local_session_id = session_map.get(str(row["id"]))
                if local_session_id is not None:
                    set_session[str(remote_set)] = local_session_id

        for row in tyre_sets:
            session_id = set_session.get(str(row["id"]))
            if session_id is None:
                continue
            legacy = row.get("legacy_id")
            local = self.db.get_tyre_set(int(legacy)) if legacy is not None else None
            remote_time = _stamp(row.get("updated_at") or row.get("created_at"))
            local_time = _stamp((local["updated_at"] or local["created_at"]) if local else None)
            if local is None or remote_time > local_time:
                local_id = self.db.save_tyre_set(
                    int(legacy) if local is not None else None,
                    session_id,
                    str(row.get("set_number") or ""),
                    row.get("manufacturer") or "",
                    row.get("compound") or "",
                    int(row.get("laps") or 0),
                    int(row.get("heat_cycles") or 0),
                    row.get("notes") or "",
                    row.get("tyre_type") or "Slick",
                    row.get("condition") or "gebraucht",
                )
            else:
                local_id = int(local["id"])
            if row.get("legacy_id") is None:
                self._patch_legacy_id("tyre_sets", str(row["id"]), local_id)

    def _push_core(self):
        cars = self._rows("cars")
        drivers = self._rows("drivers")
        tracks = self._rows("tracks")
        events = self._rows("events")
        sessions = self._rows("sessions")
        tyre_sets = self._rows("tyre_sets")
        measurements = self._rows("tyre_measurements")

        remote_ids = {
            "vehicles": self._remote_legacy_ids("vehicles"),
            "drivers": self._remote_legacy_ids("drivers"),
            "tracks": self._remote_legacy_ids("tracks"),
            "race_weekends": self._remote_legacy_ids("race_weekends"),
            "sessions": self._remote_legacy_ids("sessions"),
            "tyre_sets": self._remote_legacy_ids("tyre_sets"),
        }
        car_map = {int(r["id"]): remote_ids["vehicles"].get(int(r["id"]), self._uuid("vehicles", r["id"])) for r in cars}
        driver_map = {int(r["id"]): remote_ids["drivers"].get(int(r["id"]), self._uuid("drivers", r["id"])) for r in drivers}
        track_map = {int(r["id"]): remote_ids["tracks"].get(int(r["id"]), self._uuid("tracks", r["id"])) for r in tracks}
        event_map = {int(r["id"]): remote_ids["race_weekends"].get(int(r["id"]), self._uuid("race_weekends", r["id"])) for r in events}
        session_map = {int(r["id"]): remote_ids["sessions"].get(int(r["id"]), self._uuid("sessions", r["id"])) for r in sessions}
        set_map = {int(r["id"]): remote_ids["tyre_sets"].get(int(r["id"]), self._uuid("tyre_sets", r["id"])) for r in tyre_sets}

        event_track = {int(r["id"]): int(r["track_id"]) for r in events}
        session_by_id = {int(r["id"]): r for r in sessions}
        set_by_id = {int(r["id"]): r for r in tyre_sets}

        payloads = {
            "vehicles": [],
            "drivers": [],
            "tracks": [],
            "race_weekends": [],
            "tyre_sets": [],
            "sessions": [],
            "tyre_measurements": [],
        }

        for r in cars:
            rid = int(r["id"])
            payloads["vehicles"].append({
                "id": car_map[rid], "legacy_id": rid, "team_id": self.team_id,
                "name": f'{self._get(r,"manufacturer","")} {self._get(r,"model","")}'.strip() or f"Fahrzeug {rid}",
                "manufacturer": self._get(r,"manufacturer",""), "model": self._get(r,"model",""),
                "vehicle_class": self._get(r,"car_class"), "start_number": self._get(r,"start_number"),
                "year": self._get(r,"year",0), "weight_kg": self._get(r,"weight_kg",0),
                "horsepower": self._get(r,"horsepower",0), "drive_type": self._get(r,"drive_type"),
                "target_hot_front_bar": self._get(r,"target_hot_front_bar",0),
                "target_hot_rear_bar": self._get(r,"target_hot_rear_bar",0),
                "notes": self._get(r,"notes"), "created_at": self._get(r,"created_at"),
                "updated_at": self._get(r,"updated_at"),
            })

        for r in drivers:
            rid = int(r["id"])
            first, last = self._get(r,"first_name",""), self._get(r,"last_name","")
            name = f"{first} {last}".strip() or self._get(r,"nickname") or f"Fahrer {rid}"
            payloads["drivers"].append({
                "id": driver_map[rid], "legacy_id": rid, "team_id": self.team_id,
                "name": name, "number": self._get(r,"race_number"),
                "first_name": first, "last_name": last, "nickname": self._get(r,"nickname"),
                "race_number": self._get(r,"race_number"), "licence_class": self._get(r,"licence_class"),
                "notes": self._get(r,"notes"), "created_at": self._get(r,"created_at"),
                "updated_at": self._get(r,"updated_at"),
            })

        for r in tracks:
            rid = int(r["id"])
            payloads["tracks"].append({
                "id": track_map[rid], "legacy_id": rid, "team_id": self.team_id,
                "name": self._get(r,"name","") or f"Strecke {rid}",
                "country": self._get(r,"country"), "length_km": self._get(r,"length_km"),
                "corners": self._get(r,"corners",0), "address": self._get(r,"address"),
                "latitude": self._get(r,"latitude"), "longitude": self._get(r,"longitude"),
                "notes": self._get(r,"notes"), "created_at": self._get(r,"created_at"),
                "updated_at": self._get(r,"updated_at"),
            })

        for r in events:
            rid = int(r["id"])
            track_id = int(r["track_id"])
            payloads["race_weekends"].append({
                "id": event_map[rid], "legacy_id": rid, "team_id": self.team_id,
                "track_id": track_map.get(track_id), "name": self._get(r,"name","") or f"Event {rid}",
                "start_date": self._get(r,"start_date"), "end_date": self._get(r,"end_date"),
                "championship": self._get(r,"championship"), "event_type": self._get(r,"event_type"),
                "notes": self._get(r,"notes"), "created_at": self._get(r,"created_at"),
                "updated_at": self._get(r,"updated_at"),
            })

        for r in tyre_sets:
            rid = int(r["id"])
            local_session = session_by_id.get(int(r["session_id"]))
            if local_session is None:
                continue
            event_id = int(local_session["event_id"])
            car_id = int(local_session["car_id"])
            raw_number = str(self._get(r,"set_number","") or rid)
            digits = "".join(ch for ch in raw_number if ch.isdigit())
            set_number = int(digits or rid)
            payloads["tyre_sets"].append({
                "id": set_map[rid], "legacy_id": rid, "team_id": self.team_id,
                "vehicle_id": car_map.get(car_id), "race_weekend_id": event_map.get(event_id),
                "set_number": set_number, "compound": self._get(r,"compound") or "Unbekannt",
                "manufacturer": self._get(r,"manufacturer"), "condition": self._get(r,"condition") or "gebraucht",
                "tyre_type": self._get(r,"tyre_type") or "Slick", "laps": self._get(r,"laps",0) or 0,
                "heat_cycles": self._get(r,"heat_cycles",0) or 0, "notes": self._get(r,"notes"),
                "created_at": self._get(r,"created_at"), "updated_at": self._get(r,"updated_at"),
            })

        # Sessions werden nach Reifensätzen geschrieben, damit tyre_set_id gesetzt werden kann.
        first_set_by_session = {}
        for r in tyre_sets:
            first_set_by_session.setdefault(int(r["session_id"]), int(r["id"]))

        for r in sessions:
            rid = int(r["id"])
            event_id, car_id = int(r["event_id"]), int(r["car_id"])
            driver_id = self._get(r,"driver_id")
            set_id = first_set_by_session.get(rid)
            payloads["sessions"].append({
                "id": session_map[rid], "legacy_id": rid, "team_id": self.team_id,
                "race_weekend_id": event_map.get(event_id),
                "driver_id": driver_map.get(int(driver_id)) if driver_id is not None else None,
                "vehicle_id": car_map.get(car_id),
                "track_id": track_map.get(event_track.get(event_id)),
                "tyre_set_id": set_map.get(set_id) if set_id else None,
                "session_type": self._get(r,"session_type"),
                "air_temperature": self._get(r,"air_temp_c",0),
                "track_temperature": self._get(r,"track_temp_c",0),
                "weather": self._get(r,"weather"),
                "measured_at": self._get(r,"session_date") or self._get(r,"created_at"),
                "session_date": self._get(r,"session_date"),
                "humidity_percent": self._get(r,"humidity_percent",0),
                "rim_temp_c": self._get(r,"rim_temp_c",0),
                "notes": self._get(r,"notes"),
                "created_at": self._get(r,"created_at"), "updated_at": self._get(r,"updated_at"),
            })

        pos = {"FL":"vl","FR":"vr","RL":"hl","RR":"hr"}
        for r in measurements:
            rid = int(r["id"])
            set_id = int(r["tyre_set_id"])
            local_set = set_by_id.get(set_id)
            if local_set is None:
                continue
            sess_id = int(local_set["session_id"])
            payloads["tyre_measurements"].append({
                "id": self._uuid("tyre_measurements", rid), "legacy_id": rid,
                "team_id": self.team_id, "session_id": session_map.get(sess_id),
                "tyre_set_id": set_map.get(set_id),
                "position": pos.get(str(r["position"]).upper(), str(r["position"]).lower()),
                "measured_cold_pressure": self._get(r,"cold_pressure_bar"),
                "measured_hot_pressure": self._get(r,"hot_pressure_bar"),
                "target_hot_pressure": self._get(r,"target_pressure_bar"),
                "temperature_inner": self._get(r,"temp_inside_c"),
                "temperature_middle": self._get(r,"temp_middle_c"),
                "temperature_outer": self._get(r,"temp_outside_c"),
                "wear_percent": self._get(r,"wear_percent"),
                "notes": self._get(r,"notes"),
                "cold_tyre_temp_c": self._get(r,"cold_tyre_temp_c"),
                "expected_hot_tyre_temp_c": self._get(r,"expected_hot_tyre_temp_c"),
                "ambient_pressure_bar": self._get(r,"ambient_pressure_bar",1.01325),
                "calculated_cold_pressure_bar": self._get(r,"calculated_cold_pressure_bar"),
                "calibration_offset_bar": self._get(r,"calibration_offset_bar",0),
                "calculation_model": self._get(r,"calculation_model"),
                "driven_cold_pressure_bar": self._get(r,"driven_cold_pressure_bar"),
                "hot_pressure_difference": self._get(r,"pressure_difference_bar"),
                "reference_cold_pressure": self._get(r,"reference_cold_pressure_bar"),
                "recommended_cold_pressure": self._get(r,"recommended_next_cold_pressure_bar"),
                "created_at": self._get(r,"created_at"), "updated_at": self._get(r,"updated_at"),
            })

        # Eltern zuerst, danach abhängige Datensätze.
        for table in ("vehicles","drivers","tracks","race_weekends","tyre_sets","sessions","tyre_measurements"):
            remote = self._remote_meta(table)
            send = []
            for rec in payloads[table]:
                old = remote.get(str(rec["id"]))
                local_time = _stamp(rec.get("updated_at") or rec.get("created_at"))
                remote_time = _stamp((old or {}).get("updated_at") or (old or {}).get("created_at"))
                if old is None or local_time >= remote_time:
                    send.append(rec)
            self._upsert(table, send)

    def _pull_measurements(self):
        cloud_sets = self._request(
            "tyre_sets",
            query=urllib.parse.urlencode({
                "team_id": f"eq.{self.team_id}",
                "select": "id,legacy_id",
            }),
        ) or []
        set_map = {str(r["id"]): int(r["legacy_id"]) for r in cloud_sets if r.get("legacy_id") is not None}
        if not set_map:
            return

        rows = self._request(
            "tyre_measurements",
            query=urllib.parse.urlencode({
                "team_id": f"eq.{self.team_id}",
                "select": "*",
            }),
        ) or []
        reverse_pos = {"vl":"FL","vr":"FR","hl":"RL","hr":"RR"}

        for row in rows:
            local_set_id = set_map.get(str(row.get("tyre_set_id")))
            if local_set_id is None:
                continue
            position = reverse_pos.get(str(row.get("position","")).lower())
            if not position:
                continue

            existing = self.db.one(
                "SELECT * FROM tyre_measurements WHERE tyre_set_id=? AND position=?",
                (local_set_id, position),
            )
            local_time = _stamp(
                (existing["updated_at"] or existing["created_at"]) if existing else None
            )
            remote_time = _stamp(row.get("updated_at") or row.get("created_at"))
            if existing is not None and local_time >= remote_time:
                continue

            self.db.save_tyre_measurement(
                local_set_id,
                position,
                row.get("measured_cold_pressure"),
                row.get("measured_hot_pressure"),
                row.get("target_hot_pressure"),
                row.get("temperature_inner"),
                row.get("temperature_middle"),
                row.get("temperature_outer"),
                row.get("wear_percent"),
                row.get("notes") or "",
                cold_tyre_temp_c=row.get("cold_tyre_temp_c"),
                expected_hot_tyre_temp_c=row.get("expected_hot_tyre_temp_c"),
                ambient_pressure_bar=row.get("ambient_pressure_bar") or 1.01325,
                calculated_cold_pressure_bar=row.get("calculated_cold_pressure_bar"),
                calibration_offset_bar=row.get("calibration_offset_bar") or 0,
                calculation_model=row.get("calculation_model") or "cloud-sync",
                driven_cold_pressure_bar=row.get("driven_cold_pressure_bar"),
                reference_cold_pressure_bar=row.get("reference_cold_pressure"),
                recommended_next_cold_pressure_bar=row.get("recommended_cold_pressure"),
            )

            saved = self.db.one(
                "SELECT id FROM tyre_measurements WHERE tyre_set_id=? AND position=?",
                (local_set_id, position),
            )
            if saved and row.get("legacy_id") is None:
                q = urllib.parse.urlencode({"id": f"eq.{row['id']}"})
                self._request(
                    "tyre_measurements",
                    method="PATCH",
                    query=q,
                    body={"legacy_id": int(saved["id"])},
                    prefer="return=minimal",
                )
