from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable


class Database:
    def __init__(self, path: str | Path = "sorg_gt_v2.db") -> None:
        self.path = Path(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._create_base_schema()
        self.migrate()


    def _create_base_schema(self) -> None:
        """Creates the base database for a fresh installation. Existing DBs stay intact."""
        with self.connection:
            self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS cars (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    manufacturer TEXT NOT NULL DEFAULT '',
                    model TEXT NOT NULL DEFAULT '',
                    car_class TEXT,
                    year INTEGER DEFAULT 0,
                    weight_kg REAL DEFAULT 0,
                    horsepower REAL DEFAULT 0,
                    drive_type TEXT,
                    target_hot_front_bar REAL DEFAULT 0,
                    target_hot_rear_bar REAL DEFAULT 0,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT
                );

                CREATE TABLE IF NOT EXISTS drivers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL DEFAULT '',
                    last_name TEXT NOT NULL DEFAULT '',
                    nickname TEXT,
                    race_number TEXT,
                    licence_class TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT
                );

                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL DEFAULT '',
                    country TEXT,
                    length_km REAL DEFAULT 0,
                    corners INTEGER DEFAULT 0,
                    address TEXT,
                    latitude REAL,
                    longitude REAL,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL DEFAULT '',
                    track_id INTEGER NOT NULL,
                    start_date TEXT,
                    end_date TEXT,
                    championship TEXT,
                    event_type TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT,
                    FOREIGN KEY(track_id) REFERENCES tracks(id) ON DELETE RESTRICT
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    car_id INTEGER NOT NULL,
                    driver_id INTEGER,
                    session_type TEXT,
                    session_date TEXT,
                    weather TEXT,
                    air_temp_c REAL DEFAULT 0,
                    track_temp_c REAL DEFAULT 0,
                    rim_temp_c REAL DEFAULT 0,
                    humidity_percent REAL DEFAULT 0,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT,
                    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
                    FOREIGN KEY(car_id) REFERENCES cars(id) ON DELETE RESTRICT,
                    FOREIGN KEY(driver_id) REFERENCES drivers(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS tyre_sets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    set_number TEXT NOT NULL DEFAULT '',
                    manufacturer TEXT,
                    compound TEXT,
                    laps INTEGER DEFAULT 0,
                    heat_cycles INTEGER DEFAULT 0,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS tyre_measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tyre_set_id INTEGER NOT NULL,
                    position TEXT NOT NULL,
                    cold_pressure_bar REAL,
                    hot_pressure_bar REAL,
                    target_pressure_bar REAL,
                    temp_inside_c REAL,
                    temp_middle_c REAL,
                    temp_outside_c REAL,
                    wear_percent REAL,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT,
                    UNIQUE(tyre_set_id, position),
                    FOREIGN KEY(tyre_set_id) REFERENCES tyre_sets(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS session_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    category TEXT,
                    title TEXT,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                """
            )

    def migrate(self) -> None:
        """
        Ergänzt die Phase-3-Tabelle bei vorhandenen Datenbanken.
        Bestehende Daten bleiben erhalten.
        """
        with self.connection:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS session_setup_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    parameter_name TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    unit TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT,
                    FOREIGN KEY(session_id)
                        REFERENCES sessions(id)
                        ON DELETE CASCADE
                )
                """
            )

            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS session_media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    media_type TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id)
                        REFERENCES sessions(id)
                        ON DELETE CASCADE
                )
                """
            )

            # Automatische Kaltdruckberechnung.
            self._ensure_column(
                "tyre_measurements",
                "cold_tyre_temp_c",
                "REAL",
            )
            self._ensure_column(
                "tyre_measurements",
                "expected_hot_tyre_temp_c",
                "REAL",
            )
            self._ensure_column(
                "tyre_measurements",
                "ambient_pressure_bar",
                "REAL DEFAULT 1.01325",
            )
            self._ensure_column(
                "tyre_measurements",
                "calculated_cold_pressure_bar",
                "REAL",
            )
            self._ensure_column(
                "tyre_measurements",
                "calibration_offset_bar",
                "REAL DEFAULT 0",
            )
            self._ensure_column(
                "tyre_measurements",
                "calculation_model",
                "TEXT",
            )
            self._ensure_column(
                "tyre_measurements",
                "driven_cold_pressure_bar",
                "REAL",
            )
            self._ensure_column(
                "tyre_measurements",
                "pressure_difference_bar",
                "REAL",
            )

            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS driver_track_pressure_targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_id INTEGER NOT NULL,
                    track_id INTEGER NOT NULL,
                    car_id INTEGER NOT NULL,
                    target_hot_front_bar REAL NOT NULL,
                    target_hot_rear_bar REAL NOT NULL,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT,
                    UNIQUE(driver_id, track_id, car_id),
                    FOREIGN KEY(driver_id)
                        REFERENCES drivers(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY(track_id)
                        REFERENCES tracks(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY(car_id)
                        REFERENCES cars(id)
                        ON DELETE CASCADE
                )
                """
            )

            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS pressure_recommendation_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tyre_set_id INTEGER NOT NULL,
                    position TEXT NOT NULL,
                    target_hot_pressure_bar REAL,
                    cold_tyre_temp_c REAL,
                    expected_hot_tyre_temp_c REAL,
                    ambient_pressure_bar REAL,
                    history_correction_bar REAL,
                    recommended_cold_pressure_bar REAL,
                    model_version TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(tyre_set_id)
                        REFERENCES tyre_sets(id)
                        ON DELETE CASCADE
                )
                """
            )

            # Phase 8: Rennwochenende / Reifenlogik für den Boxenbetrieb.
            self._ensure_column("sessions", "rim_temp_c", "REAL DEFAULT 0")
            self._ensure_column("cars", "start_number", "TEXT")
            self._ensure_column("tyre_sets", "tyre_type", "TEXT DEFAULT 'Slick'")
            self._ensure_column("tyre_sets", "condition", "TEXT DEFAULT 'gebraucht'")
            self._ensure_column("tyre_measurements", "reference_cold_pressure_bar", "REAL")
            self._ensure_column("tyre_measurements", "recommended_next_cold_pressure_bar", "REAL")

            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS session_drivers (
                    session_id INTEGER NOT NULL,
                    driver_id INTEGER NOT NULL,
                    PRIMARY KEY(session_id, driver_id),
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY(driver_id) REFERENCES drivers(id) ON DELETE CASCADE
                )
                """
            )

            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tyre_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tyre_set_id INTEGER NOT NULL,
                    note_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    action TEXT,
                    tyre_type TEXT,
                    manufacturer TEXT,
                    condition_before TEXT,
                    condition_after TEXT,
                    notes TEXT,
                    FOREIGN KEY(tyre_set_id) REFERENCES tyre_sets(id) ON DELETE CASCADE
                )
                """
            )

            # Lösch-Synchronisation: Jede lokale Löschung wird vorgemerkt,
            # damit CloudSync sie auf allen Geräten entfernen kann.
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_deletions (
                    local_table TEXT NOT NULL,
                    local_id INTEGER NOT NULL,
                    deleted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(local_table, local_id)
                )
                """
            )

            sync_tables = (
                "cars",
                "drivers",
                "tracks",
                "events",
                "sessions",
                "tyre_sets",
                "tyre_measurements",
                "session_changes",
                "session_setup_entries",
                "session_media",
                "driver_track_pressure_targets",
                "pressure_recommendation_log",
                "tyre_notes",
            )
            for table in sync_tables:
                trigger = "trg_sync_delete_" + table
                self.connection.execute(
                    f"""
                    CREATE TRIGGER IF NOT EXISTS {trigger}
                    AFTER DELETE ON {table}
                    BEGIN
                        INSERT OR REPLACE INTO sync_deletions(
                            local_table, local_id, deleted_at
                        )
                        VALUES ('{table}', OLD.id, CURRENT_TIMESTAMP);
                    END
                    """
                )

    def _ensure_column(
        self,
        table: str,
        column: str,
        definition: str,
    ) -> None:
        columns = {
            row["name"]
            for row in self.all(
                f"PRAGMA table_info({table})"
            )
        }

        if column not in columns:
            self.connection.execute(
                f"ALTER TABLE {table} "
                f"ADD COLUMN {column} {definition}"
            )

    def close(self) -> None:
        self.connection.close()

    def all(self, sql: str, parameters: Iterable[Any] = ()) -> list[sqlite3.Row]:
        cursor = self.connection.execute(sql, tuple(parameters))
        return cursor.fetchall()

    def one(self, sql: str, parameters: Iterable[Any] = ()) -> sqlite3.Row | None:
        cursor = self.connection.execute(sql, tuple(parameters))
        return cursor.fetchone()

    def execute(self, sql: str, parameters: Iterable[Any] = ()) -> int:
        with self.connection:
            cursor = self.connection.execute(sql, tuple(parameters))
            return int(cursor.lastrowid)

    def statistics(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for table in (
            "cars",
            "drivers",
            "tracks",
            "events",
            "sessions",
            "tyre_sets",
            "session_changes",
            "session_setup_entries",
            "session_media",
            "pressure_recommendation_log",
            "driver_track_pressure_targets",
            "session_drivers",
            "tyre_notes",
        ):
            row = self.one(f"SELECT COUNT(*) AS total FROM {table}")
            result[table] = int(row["total"]) if row else 0
        return result

    # -----------------------------------------------------------------
    # Cars
    # -----------------------------------------------------------------

    def get_cars(self) -> list[sqlite3.Row]:
        return self.all(
            """
            SELECT *
            FROM cars
            ORDER BY manufacturer, model
            """
        )

    def get_car(self, car_id: int) -> sqlite3.Row | None:
        return self.one("SELECT * FROM cars WHERE id = ?", (car_id,))

    def save_car(
        self,
        car_id: int | None,
        manufacturer: str,
        model: str,
        car_class: str,
        year: int,
        weight_kg: float,
        horsepower: float,
        drive_type: str,
        notes: str,
        start_number: str = "",
    ) -> int:
        """
        Speichert nur Fahrzeug-Stammdaten.

        Die Ziel-Heißdrücke werden fahrer-, strecken- und
        fahrzeugspezifisch in driver_track_pressure_targets gepflegt.
        Vorhandene alte Fahrzeug-Zielwerte bleiben als Rückfallwert erhalten.
        """
        if car_id is None:
            return self.execute(
                """
                INSERT INTO cars (
                    manufacturer, model, car_class, year,
                    weight_kg, horsepower, drive_type,
                    target_hot_front_bar, target_hot_rear_bar,
                    notes, start_number
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
                """,
                (
                    manufacturer,
                    model,
                    car_class,
                    year,
                    weight_kg,
                    horsepower,
                    drive_type,
                    notes,
                    start_number,
                ),
            )

        self.execute(
            """
            UPDATE cars
            SET
                manufacturer = ?,
                model = ?,
                car_class = ?,
                year = ?,
                weight_kg = ?,
                horsepower = ?,
                drive_type = ?,
                notes = ?,
                start_number = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                manufacturer,
                model,
                car_class,
                year,
                weight_kg,
                horsepower,
                drive_type,
                notes,
                start_number,
                car_id,
            ),
        )
        return car_id

    def delete_car(self, car_id: int) -> None:
        self.execute("DELETE FROM cars WHERE id = ?", (car_id,))

    # -----------------------------------------------------------------
    # Drivers
    # -----------------------------------------------------------------

    def get_drivers(self) -> list[sqlite3.Row]:
        return self.all(
            """
            SELECT *
            FROM drivers
            ORDER BY first_name, last_name
            """
        )

    def get_driver(self, driver_id: int) -> sqlite3.Row | None:
        return self.one("SELECT * FROM drivers WHERE id = ?", (driver_id,))

    def save_driver(
        self,
        driver_id: int | None,
        first_name: str,
        last_name: str,
        nickname: str,
        race_number: str,
        licence_class: str,
        notes: str,
    ) -> int:
        if driver_id is None:
            return self.execute(
                """
                INSERT INTO drivers (
                    first_name, last_name, nickname,
                    race_number, licence_class, notes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    first_name,
                    last_name,
                    nickname,
                    race_number,
                    licence_class,
                    notes,
                ),
            )

        self.execute(
            """
            UPDATE drivers
            SET
                first_name = ?,
                last_name = ?,
                nickname = ?,
                race_number = ?,
                licence_class = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                first_name,
                last_name,
                nickname,
                race_number,
                licence_class,
                notes,
                driver_id,
            ),
        )
        return driver_id

    def delete_driver(self, driver_id: int) -> None:
        self.execute("DELETE FROM drivers WHERE id = ?", (driver_id,))

    # -----------------------------------------------------------------
    # Tracks
    # -----------------------------------------------------------------

    def get_tracks(self) -> list[sqlite3.Row]:
        return self.all(
            """
            SELECT *
            FROM tracks
            ORDER BY name
            """
        )

    def get_track(self, track_id: int) -> sqlite3.Row | None:
        return self.one("SELECT * FROM tracks WHERE id = ?", (track_id,))

    def save_track(
        self,
        track_id: int | None,
        name: str,
        country: str,
        length_km: float,
        corners: int,
        address: str,
        latitude: float | None,
        longitude: float | None,
        notes: str,
    ) -> int:
        if track_id is None:
            return self.execute(
                """
                INSERT INTO tracks (
                    name, country, length_km, corners,
                    address, latitude, longitude, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    country,
                    length_km,
                    corners,
                    address,
                    latitude,
                    longitude,
                    notes,
                ),
            )

        self.execute(
            """
            UPDATE tracks
            SET
                name = ?,
                country = ?,
                length_km = ?,
                corners = ?,
                address = ?,
                latitude = ?,
                longitude = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                name,
                country,
                length_km,
                corners,
                address,
                latitude,
                longitude,
                notes,
                track_id,
            ),
        )
        return track_id

    def delete_track(self, track_id: int) -> None:
        self.execute("DELETE FROM tracks WHERE id = ?", (track_id,))

    # -----------------------------------------------------------------
    # Fahrer-/Strecken-/Fahrzeug-Ziel-Heißdrücke
    # -----------------------------------------------------------------

    def get_driver_track_pressure_target(
        self,
        driver_id: int,
        track_id: int,
        car_id: int,
    ) -> sqlite3.Row | None:
        return self.one(
            """
            SELECT *
            FROM driver_track_pressure_targets
            WHERE driver_id = ?
              AND track_id = ?
              AND car_id = ?
            """,
            (driver_id, track_id, car_id),
        )

    def get_pressure_targets_for_track(
        self,
        track_id: int,
    ) -> list[sqlite3.Row]:
        return self.all(
            """
            SELECT
                p.*,
                d.first_name,
                d.last_name,
                d.nickname,
                c.manufacturer,
                c.model
            FROM driver_track_pressure_targets AS p
            INNER JOIN drivers AS d ON p.driver_id = d.id
            INNER JOIN cars AS c ON p.car_id = c.id
            WHERE p.track_id = ?
            ORDER BY
                d.first_name,
                d.last_name,
                c.manufacturer,
                c.model
            """,
            (track_id,),
        )

    def save_driver_track_pressure_target(
        self,
        driver_id: int,
        track_id: int,
        car_id: int,
        target_hot_front_bar: float,
        target_hot_rear_bar: float,
        notes: str = "",
    ) -> int:
        if target_hot_front_bar <= 0 or target_hot_rear_bar <= 0:
            raise ValueError(
                "Die Ziel-Heißdrücke müssen größer als 0 bar sein."
            )

        self.execute(
            """
            INSERT INTO driver_track_pressure_targets (
                driver_id,
                track_id,
                car_id,
                target_hot_front_bar,
                target_hot_rear_bar,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(driver_id, track_id, car_id)
            DO UPDATE SET
                target_hot_front_bar =
                    excluded.target_hot_front_bar,
                target_hot_rear_bar =
                    excluded.target_hot_rear_bar,
                notes = excluded.notes,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                driver_id,
                track_id,
                car_id,
                target_hot_front_bar,
                target_hot_rear_bar,
                notes,
            ),
        )

        row = self.get_driver_track_pressure_target(
            driver_id,
            track_id,
            car_id,
        )
        return int(row["id"]) if row else 0

    def delete_driver_track_pressure_target(
        self,
        driver_id: int,
        track_id: int,
        car_id: int,
    ) -> None:
        self.execute(
            """
            DELETE FROM driver_track_pressure_targets
            WHERE driver_id = ?
              AND track_id = ?
              AND car_id = ?
            """,
            (driver_id, track_id, car_id),
        )

    def get_pressure_target_for_session(
        self,
        session_id: int,
    ) -> sqlite3.Row | None:
        """
        Liefert zuerst den persönlichen Zielwert für
        Fahrer + Strecke + Fahrzeug.

        Falls noch kein persönlicher Wert vorhanden ist, werden die alten
        Fahrzeug-Zielwerte als Übergangs-/Rückfallwert geliefert.
        """
        return self.one(
            """
            SELECT
                COALESCE(
                    p.target_hot_front_bar,
                    c.target_hot_front_bar
                ) AS target_hot_front_bar,
                COALESCE(
                    p.target_hot_rear_bar,
                    c.target_hot_rear_bar
                ) AS target_hot_rear_bar,
                CASE WHEN p.id IS NULL THEN 0 ELSE 1 END
                    AS personal_target_found
            FROM sessions AS s
            INNER JOIN events AS e
                ON s.event_id = e.id
            INNER JOIN cars AS c
                ON s.car_id = c.id
            LEFT JOIN driver_track_pressure_targets AS p
                ON p.driver_id = s.driver_id
               AND p.track_id = e.track_id
               AND p.car_id = s.car_id
            WHERE s.id = ?
            """,
            (session_id,),
        )


    # -----------------------------------------------------------------
    # Events / Sessions / Tyres
    # -----------------------------------------------------------------

    def get_events(self) -> list[sqlite3.Row]:
        return self.all(
            """
            SELECT
                e.*,
                t.name AS track_name,
                t.country AS track_country
            FROM events AS e
            INNER JOIN tracks AS t
                ON e.track_id = t.id
            ORDER BY e.start_date DESC, e.id DESC
            """
        )

    def get_event(self, event_id: int) -> sqlite3.Row | None:
        return self.one(
            """
            SELECT
                e.*,
                t.name AS track_name
            FROM events AS e
            INNER JOIN tracks AS t
                ON e.track_id = t.id
            WHERE e.id = ?
            """,
            (event_id,),
        )

    def save_event(
        self,
        event_id: int | None,
        name: str,
        track_id: int,
        start_date: str,
        end_date: str,
        championship: str,
        event_type: str,
        notes: str,
    ) -> int:
        if event_id is None:
            return self.execute(
                """
                INSERT INTO events (
                    name, track_id, start_date, end_date,
                    championship, event_type, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    track_id,
                    start_date,
                    end_date,
                    championship,
                    event_type,
                    notes,
                ),
            )

        self.execute(
            """
            UPDATE events
            SET
                name = ?,
                track_id = ?,
                start_date = ?,
                end_date = ?,
                championship = ?,
                event_type = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                name,
                track_id,
                start_date,
                end_date,
                championship,
                event_type,
                notes,
                event_id,
            ),
        )
        return event_id

    def delete_event(self, event_id: int) -> None:
        self.execute("DELETE FROM events WHERE id = ?", (event_id,))

    def get_sessions_for_event(self, event_id: int) -> list[sqlite3.Row]:
        return self.all(
            """
            SELECT
                s.*,
                e.name AS event_name,
                t.name AS track_name,
                c.manufacturer,
                c.model,
                c.start_number,
                d.first_name AS driver_first_name,
                d.last_name AS driver_last_name,
                d.nickname AS driver_nickname,
                COALESCE((
                    SELECT GROUP_CONCAT(TRIM(sd_d.first_name || ' ' || COALESCE(sd_d.last_name, '')), ', ')
                    FROM session_drivers sd
                    JOIN drivers sd_d ON sd_d.id = sd.driver_id
                    WHERE sd.session_id = s.id
                ), TRIM(COALESCE(d.first_name, '') || ' ' || COALESCE(d.last_name, ''))) AS driver_names
            FROM sessions AS s
            INNER JOIN events AS e
                ON s.event_id = e.id
            INNER JOIN tracks AS t
                ON e.track_id = t.id
            INNER JOIN cars AS c
                ON s.car_id = c.id
            LEFT JOIN drivers AS d
                ON s.driver_id = d.id
            WHERE s.event_id = ?
            ORDER BY s.session_date, s.id
            """,
            (event_id,),
        )

    def get_session(self, session_id: int) -> sqlite3.Row | None:
        return self.one(
            """
            SELECT
                s.*,
                e.name AS event_name,
                t.name AS track_name,
                c.manufacturer,
                c.model,
                c.start_number,
                d.first_name AS driver_first_name,
                d.last_name AS driver_last_name,
                d.nickname AS driver_nickname,
                COALESCE((
                    SELECT GROUP_CONCAT(TRIM(sd_d.first_name || ' ' || COALESCE(sd_d.last_name, '')), ', ')
                    FROM session_drivers sd
                    JOIN drivers sd_d ON sd_d.id = sd.driver_id
                    WHERE sd.session_id = s.id
                ), TRIM(COALESCE(d.first_name, '') || ' ' || COALESCE(d.last_name, ''))) AS driver_names
            FROM sessions AS s
            INNER JOIN events AS e
                ON s.event_id = e.id
            INNER JOIN tracks AS t
                ON e.track_id = t.id
            INNER JOIN cars AS c
                ON s.car_id = c.id
            LEFT JOIN drivers AS d
                ON s.driver_id = d.id
            WHERE s.id = ?
            """,
            (session_id,),
        )

    def save_session(
        self,
        session_id: int | None,
        event_id: int,
        car_id: int,
        driver_id: int | None,
        session_type: str,
        session_date: str,
        weather: str,
        air_temp_c: float,
        track_temp_c: float,
        rim_temp_c: float,
        humidity_percent: float,
        notes: str,
    ) -> int:
        if session_id is None:
            return self.execute(
                """
                INSERT INTO sessions (
                    event_id, car_id, driver_id,
                    session_type, session_date, weather,
                    air_temp_c, track_temp_c, rim_temp_c,
                    humidity_percent, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    car_id,
                    driver_id,
                    session_type,
                    session_date,
                    weather,
                    air_temp_c,
                    track_temp_c,
                    rim_temp_c,
                    humidity_percent,
                    notes,
                ),
            )

        self.execute(
            """
            UPDATE sessions
            SET
                event_id = ?,
                car_id = ?,
                driver_id = ?,
                session_type = ?,
                session_date = ?,
                weather = ?,
                air_temp_c = ?,
                track_temp_c = ?,
                rim_temp_c = ?,
                humidity_percent = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                event_id,
                car_id,
                driver_id,
                session_type,
                session_date,
                weather,
                air_temp_c,
                track_temp_c,
                rim_temp_c,
                humidity_percent,
                notes,
                session_id,
            ),
        )
        return session_id

    def get_session_driver_ids(self, session_id: int) -> list[int]:
        rows = self.all(
            "SELECT driver_id FROM session_drivers WHERE session_id = ? ORDER BY driver_id",
            (session_id,),
        )
        if rows:
            return [int(row["driver_id"]) for row in rows]
        row = self.one("SELECT driver_id FROM sessions WHERE id = ?", (session_id,))
        return [int(row["driver_id"])] if row and row["driver_id"] is not None else []

    def set_session_drivers(self, session_id: int, driver_ids: list[int]) -> None:
        cleaned = []
        for driver_id in driver_ids:
            value = int(driver_id)
            if value not in cleaned:
                cleaned.append(value)
        with self.connection:
            self.connection.execute("DELETE FROM session_drivers WHERE session_id = ?", (session_id,))
            for driver_id in cleaned:
                self.connection.execute(
                    "INSERT OR IGNORE INTO session_drivers (session_id, driver_id) VALUES (?, ?)",
                    (session_id, driver_id),
                )
            self.connection.execute(
                "UPDATE sessions SET driver_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (cleaned[0] if cleaned else None, session_id),
            )

    def get_session_driver_names(self, session_id: int) -> str:
        rows = self.all(
            """
            SELECT d.first_name, d.last_name, d.nickname
            FROM session_drivers sd
            JOIN drivers d ON d.id = sd.driver_id
            WHERE sd.session_id = ?
            ORDER BY d.last_name, d.first_name
            """,
            (session_id,),
        )
        if not rows:
            row = self.get_session(session_id)
            if not row or row["driver_id"] is None:
                return "Ohne Fahrer"
            rows = [row]
        names = []
        for row in rows:
            first = row["first_name"] if "first_name" in row.keys() else row["driver_first_name"]
            last = row["last_name"] if "last_name" in row.keys() else row["driver_last_name"]
            nick = row["nickname"] if "nickname" in row.keys() else row["driver_nickname"]
            name = f"{first or ''} {last or ''}".strip()
            if nick:
                name = f'{name} "{nick}"'.strip()
            if name:
                names.append(name)
        return ", ".join(names) if names else "Ohne Fahrer"

    def delete_session(self, session_id: int) -> None:
        self.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def get_tyre_sets_for_session(self, session_id: int) -> list[sqlite3.Row]:
        return self.all(
            """
            SELECT *
            FROM tyre_sets
            WHERE session_id = ?
            ORDER BY id
            """,
            (session_id,),
        )

    def get_tyre_set(self, tyre_set_id: int) -> sqlite3.Row | None:
        return self.one(
            """
            SELECT *
            FROM tyre_sets
            WHERE id = ?
            """,
            (tyre_set_id,),
        )

    def save_tyre_set(
        self,
        tyre_set_id: int | None,
        session_id: int,
        set_number: str,
        manufacturer: str,
        compound: str,
        laps: int,
        heat_cycles: int,
        notes: str,
        tyre_type: str = "Slick",
        condition: str = "gebraucht",
    ) -> int:
        if tyre_set_id is None:
            with self.connection:
                cursor = self.connection.execute(
                    """
                    INSERT INTO tyre_sets (
                        session_id, set_number, manufacturer,
                        compound, laps, heat_cycles, notes, tyre_type, condition
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        set_number,
                        manufacturer,
                        compound,
                        laps,
                        heat_cycles,
                        notes,
                        tyre_type,
                        condition,
                    ),
                )
                new_id = int(cursor.lastrowid)

                session = self.get_pressure_target_for_session(
                    session_id
                )

                front_target = (
                    session["target_hot_front_bar"]
                    if session else None
                )
                rear_target = (
                    session["target_hot_rear_bar"]
                    if session else None
                )

                for position in ("FL", "FR", "RL", "RR"):
                    target = (
                        front_target
                        if position in ("FL", "FR")
                        else rear_target
                    )
                    self.connection.execute(
                        """
                        INSERT INTO tyre_measurements (
                            tyre_set_id, position,
                            target_pressure_bar
                        )
                        VALUES (?, ?, ?)
                        """,
                        (new_id, position, target),
                    )

                return new_id

        self.execute(
            """
            UPDATE tyre_sets
            SET
                session_id = ?,
                set_number = ?,
                manufacturer = ?,
                compound = ?,
                laps = ?,
                heat_cycles = ?,
                notes = ?,
                tyre_type = ?,
                condition = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                session_id,
                set_number,
                manufacturer,
                compound,
                laps,
                heat_cycles,
                notes,
                tyre_type,
                condition,
                tyre_set_id,
            ),
        )
        return tyre_set_id

    def add_tyre_note(
        self,
        tyre_set_id: int,
        action: str,
        tyre_type: str,
        manufacturer: str,
        condition_before: str,
        condition_after: str,
        notes: str,
    ) -> int:
        return self.execute(
            """
            INSERT INTO tyre_notes (
                tyre_set_id, action, tyre_type, manufacturer,
                condition_before, condition_after, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tyre_set_id, action, tyre_type, manufacturer,
                condition_before, condition_after, notes,
            ),
        )

    def get_tyre_notes(self, tyre_set_id: int) -> list[sqlite3.Row]:
        return self.all(
            "SELECT * FROM tyre_notes WHERE tyre_set_id = ? ORDER BY id DESC",
            (tyre_set_id,),
        )

    @staticmethod
    def calculate_next_cold_pressure(
        reference_cold_pressure_bar: float,
        measured_hot_pressure_bar: float,
        target_hot_pressure_bar: float,
    ) -> tuple[float, float]:
        """Boxen-Korrektur: Referenz kalt - (gemessen heiß - Ziel heiß)."""
        difference = measured_hot_pressure_bar - target_hot_pressure_bar
        recommended = reference_cold_pressure_bar - difference
        return round(difference, 3), max(0.0, round(recommended, 3))

    def delete_tyre_set(self, tyre_set_id: int) -> None:
        self.execute("DELETE FROM tyre_sets WHERE id = ?", (tyre_set_id,))

    def get_tyre_measurements(self, tyre_set_id: int) -> list[sqlite3.Row]:
        return self.all(
            """
            SELECT *
            FROM tyre_measurements
            WHERE tyre_set_id = ?
            ORDER BY CASE position
                WHEN 'FL' THEN 1
                WHEN 'FR' THEN 2
                WHEN 'RL' THEN 3
                WHEN 'RR' THEN 4
                ELSE 5
            END
            """,
            (tyre_set_id,),
        )

    def get_tyre_measurement(
        self,
        tyre_set_id: int,
        position: str,
    ) -> sqlite3.Row | None:
        return self.one(
            """
            SELECT *
            FROM tyre_measurements
            WHERE tyre_set_id = ? AND position = ?
            """,
            (tyre_set_id, position),
        )

    @staticmethod
    def calculate_cold_pressure(
        target_hot_pressure_bar: float,
        cold_tyre_temp_c: float,
        expected_hot_tyre_temp_c: float,
        ambient_pressure_bar: float = 1.01325,
        calibration_offset_bar: float = 0.0,
    ) -> float:
        """
        Näherung über das ideale Gasgesetz.

        Es wird mit Absolutdruck gerechnet:
        P_kalt_abs / T_kalt = P_heiss_abs / T_heiss

        Die Korrektur aus historischen Daten kann zusätzlich
        aufgeschlagen werden.
        """
        cold_kelvin = cold_tyre_temp_c + 273.15
        hot_kelvin = expected_hot_tyre_temp_c + 273.15

        if cold_kelvin <= 0 or hot_kelvin <= 0:
            raise ValueError(
                "Reifentemperaturen müssen über -273,15 °C liegen."
            )

        if target_hot_pressure_bar <= 0:
            raise ValueError(
                "Der Ziel-Heißdruck muss größer als 0 bar sein."
            )

        if ambient_pressure_bar <= 0:
            raise ValueError(
                "Der Umgebungsdruck muss größer als 0 bar sein."
            )

        hot_absolute = (
            target_hot_pressure_bar
            + ambient_pressure_bar
        )
        cold_absolute = (
            hot_absolute
            * cold_kelvin
            / hot_kelvin
        )
        cold_gauge = (
            cold_absolute
            - ambient_pressure_bar
            + calibration_offset_bar
        )

        return max(0.0, round(cold_gauge, 3))

    def get_historical_pressure_correction(
        self,
        tyre_set_id: int,
        position: str,
        minimum_samples: int = 2,
    ) -> dict[str, float | int]:
        """
        Ermittelt eine Korrektur aus vergleichbaren Datensätzen.

        Priorität:
        gleiches Fahrzeug + gleiche Strecke + gleiche Reifenposition.
        Es werden nur Datensätze genutzt, bei denen Ziel-Heißdruck,
        Kalttemperatur, erwartete Heißtemperatur und der tatsächlich
        verwendete Kaltdruck vorhanden sind.
        """
        context = self.one(
            """
            SELECT
                s.car_id,
                s.driver_id,
                e.track_id
            FROM tyre_sets AS ts
            INNER JOIN sessions AS s
                ON ts.session_id = s.id
            INNER JOIN events AS e
                ON s.event_id = e.id
            WHERE ts.id = ?
            """,
            (tyre_set_id,),
        )

        if not context:
            return {
                "correction_bar": 0.0,
                "samples": 0,
            }

        rows = self.all(
            """
            SELECT
                COALESCE(
                    tm.driven_cold_pressure_bar,
                    tm.cold_pressure_bar
                ) AS driven_cold_pressure_bar,
                tm.target_pressure_bar,
                tm.cold_tyre_temp_c,
                tm.expected_hot_tyre_temp_c,
                COALESCE(
                    tm.ambient_pressure_bar,
                    1.01325
                ) AS ambient_pressure_bar
            FROM tyre_measurements AS tm
            INNER JOIN tyre_sets AS ts
                ON tm.tyre_set_id = ts.id
            INNER JOIN sessions AS s
                ON ts.session_id = s.id
            INNER JOIN events AS e
                ON s.event_id = e.id
            WHERE tm.tyre_set_id <> ?
              AND tm.position = ?
              AND s.car_id = ?
              AND e.track_id = ?
              AND (
                    s.driver_id = ?
                    OR (? IS NULL AND s.driver_id IS NULL)
                  )
              AND COALESCE(
                    tm.driven_cold_pressure_bar,
                    tm.cold_pressure_bar
                  ) IS NOT NULL
              AND COALESCE(
                    tm.driven_cold_pressure_bar,
                    tm.cold_pressure_bar
                  ) > 0
              AND tm.target_pressure_bar IS NOT NULL
              AND tm.target_pressure_bar > 0
              AND tm.cold_tyre_temp_c IS NOT NULL
              AND tm.expected_hot_tyre_temp_c IS NOT NULL
            ORDER BY tm.updated_at DESC, tm.id DESC
            LIMIT 30
            """,
            (
                tyre_set_id,
                position,
                context["car_id"],
                context["track_id"],
                context["driver_id"],
                context["driver_id"],
            ),
        )

        residuals: list[float] = []

        for row in rows:
            try:
                physics_value = self.calculate_cold_pressure(
                    float(row["target_pressure_bar"]),
                    float(row["cold_tyre_temp_c"]),
                    float(row["expected_hot_tyre_temp_c"]),
                    float(row["ambient_pressure_bar"]),
                    0.0,
                )
            except (TypeError, ValueError):
                continue

            residuals.append(
                float(row["driven_cold_pressure_bar"])
                - physics_value
            )

        if len(residuals) < minimum_samples:
            return {
                "correction_bar": 0.0,
                "samples": len(residuals),
            }

        # Begrenzung schützt vor einzelnen fehlerhaften Altwerten.
        residuals = [
            max(-0.30, min(0.30, value))
            for value in residuals
        ]

        correction = sum(residuals) / len(residuals)

        return {
            "correction_bar": round(correction, 3),
            "samples": len(residuals),
        }

    def log_pressure_recommendation(
        self,
        tyre_set_id: int,
        position: str,
        target_hot_pressure_bar: float,
        cold_tyre_temp_c: float,
        expected_hot_tyre_temp_c: float,
        ambient_pressure_bar: float,
        history_correction_bar: float,
        recommended_cold_pressure_bar: float,
        model_version: str = "physics-history-v1",
    ) -> None:
        self.execute(
            """
            INSERT INTO pressure_recommendation_log (
                tyre_set_id,
                position,
                target_hot_pressure_bar,
                cold_tyre_temp_c,
                expected_hot_tyre_temp_c,
                ambient_pressure_bar,
                history_correction_bar,
                recommended_cold_pressure_bar,
                model_version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tyre_set_id,
                position,
                target_hot_pressure_bar,
                cold_tyre_temp_c,
                expected_hot_tyre_temp_c,
                ambient_pressure_bar,
                history_correction_bar,
                recommended_cold_pressure_bar,
                model_version,
            ),
        )

    def save_tyre_measurement(
        self,
        tyre_set_id: int,
        position: str,
        cold_pressure_bar: float | None,
        hot_pressure_bar: float | None,
        target_pressure_bar: float | None,
        temp_inside_c: float | None,
        temp_middle_c: float | None,
        temp_outside_c: float | None,
        wear_percent: float | None,
        notes: str,
        cold_tyre_temp_c: float | None = None,
        expected_hot_tyre_temp_c: float | None = None,
        ambient_pressure_bar: float = 1.01325,
        calculated_cold_pressure_bar: float | None = None,
        calibration_offset_bar: float = 0.0,
        calculation_model: str = "physics-history-v1",
        driven_cold_pressure_bar: float | None = None,
        reference_cold_pressure_bar: float | None = None,
        recommended_next_cold_pressure_bar: float | None = None,
    ) -> None:
        self.execute(
            """
            INSERT INTO tyre_measurements (
                tyre_set_id,
                position,
                cold_pressure_bar,
                hot_pressure_bar,
                target_pressure_bar,
                temp_inside_c,
                temp_middle_c,
                temp_outside_c,
                wear_percent,
                notes,
                cold_tyre_temp_c,
                expected_hot_tyre_temp_c,
                ambient_pressure_bar,
                calculated_cold_pressure_bar,
                calibration_offset_bar,
                calculation_model,
                driven_cold_pressure_bar,
                pressure_difference_bar,
                reference_cold_pressure_bar,
                recommended_next_cold_pressure_bar
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT(tyre_set_id, position)
            DO UPDATE SET
                cold_pressure_bar =
                    excluded.cold_pressure_bar,
                hot_pressure_bar =
                    excluded.hot_pressure_bar,
                target_pressure_bar =
                    excluded.target_pressure_bar,
                temp_inside_c =
                    excluded.temp_inside_c,
                temp_middle_c =
                    excluded.temp_middle_c,
                temp_outside_c =
                    excluded.temp_outside_c,
                wear_percent =
                    excluded.wear_percent,
                notes =
                    excluded.notes,
                cold_tyre_temp_c =
                    excluded.cold_tyre_temp_c,
                expected_hot_tyre_temp_c =
                    excluded.expected_hot_tyre_temp_c,
                ambient_pressure_bar =
                    excluded.ambient_pressure_bar,
                calculated_cold_pressure_bar =
                    excluded.calculated_cold_pressure_bar,
                calibration_offset_bar =
                    excluded.calibration_offset_bar,
                calculation_model =
                    excluded.calculation_model,
                driven_cold_pressure_bar =
                    excluded.driven_cold_pressure_bar,
                pressure_difference_bar =
                    excluded.pressure_difference_bar,
                reference_cold_pressure_bar =
                    excluded.reference_cold_pressure_bar,
                recommended_next_cold_pressure_bar =
                    excluded.recommended_next_cold_pressure_bar,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                tyre_set_id,
                position,
                cold_pressure_bar,
                hot_pressure_bar,
                target_pressure_bar,
                temp_inside_c,
                temp_middle_c,
                temp_outside_c,
                wear_percent,
                notes,
                cold_tyre_temp_c,
                expected_hot_tyre_temp_c,
                ambient_pressure_bar,
                calculated_cold_pressure_bar,
                calibration_offset_bar,
                calculation_model,
                driven_cold_pressure_bar,
                (
                    None
                    if hot_pressure_bar is None or target_pressure_bar is None
                    else round(hot_pressure_bar - target_pressure_bar, 3)
                ),
                reference_cold_pressure_bar,
                recommended_next_cold_pressure_bar,
            ),
        )


    def get_session_changes(self, session_id: int) -> list[sqlite3.Row]:
        return self.all(
            """
            SELECT *
            FROM session_changes
            WHERE session_id = ?
            ORDER BY id
            """,
            (session_id,),
        )

    # -----------------------------------------------------------------
    # Session setup
    # -----------------------------------------------------------------

    def get_setup_entries(self, session_id: int) -> list[sqlite3.Row]:
        return self.all(
            """
            SELECT *
            FROM session_setup_entries
            WHERE session_id = ?
            ORDER BY category, id
            """,
            (session_id,),
        )

    def get_setup_entry(self, setup_id: int) -> sqlite3.Row | None:
        return self.one(
            """
            SELECT *
            FROM session_setup_entries
            WHERE id = ?
            """,
            (setup_id,),
        )

    def save_setup_entry(
        self,
        setup_id: int | None,
        session_id: int,
        category: str,
        parameter_name: str,
        old_value: str,
        new_value: str,
        unit: str,
        notes: str,
    ) -> int:
        if setup_id is None:
            return self.execute(
                """
                INSERT INTO session_setup_entries (
                    session_id,
                    category,
                    parameter_name,
                    old_value,
                    new_value,
                    unit,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    category,
                    parameter_name,
                    old_value,
                    new_value,
                    unit,
                    notes,
                ),
            )

        self.execute(
            """
            UPDATE session_setup_entries
            SET
                category = ?,
                parameter_name = ?,
                old_value = ?,
                new_value = ?,
                unit = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                category,
                parameter_name,
                old_value,
                new_value,
                unit,
                notes,
                setup_id,
            ),
        )
        return setup_id

    def delete_setup_entry(self, setup_id: int) -> None:
        self.execute(
            "DELETE FROM session_setup_entries WHERE id = ?",
            (setup_id,),
        )


    # -----------------------------------------------------------------
    # Fahrzeugänderungen
    # -----------------------------------------------------------------

    def get_session_change(self, change_id: int) -> sqlite3.Row | None:
        return self.one(
            """
            SELECT *
            FROM session_changes
            WHERE id = ?
            """,
            (change_id,),
        )

    def save_session_change(
        self,
        change_id: int | None,
        session_id: int,
        category: str,
        title: str,
        description: str,
    ) -> int:
        if change_id is None:
            return self.execute(
                """
                INSERT INTO session_changes (
                    session_id,
                    category,
                    title,
                    description
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    category,
                    title,
                    description,
                ),
            )

        self.execute(
            """
            UPDATE session_changes
            SET
                category = ?,
                title = ?,
                description = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                category,
                title,
                description,
                change_id,
            ),
        )
        return change_id

    def delete_session_change(self, change_id: int) -> None:
        self.execute(
            "DELETE FROM session_changes WHERE id = ?",
            (change_id,),
        )


    # -----------------------------------------------------------------
    # Session media / files
    # -----------------------------------------------------------------

    def get_session_media(self, session_id: int) -> list[sqlite3.Row]:
        return self.all(
            """
            SELECT *
            FROM session_media
            WHERE session_id = ?
            ORDER BY id DESC
            """,
            (session_id,),
        )

    def get_media_item(self, media_id: int) -> sqlite3.Row | None:
        return self.one(
            """
            SELECT *
            FROM session_media
            WHERE id = ?
            """,
            (media_id,),
        )

    def add_media_item(
        self,
        session_id: int,
        title: str,
        file_path: str,
        media_type: str,
        notes: str,
    ) -> int:
        return self.execute(
            """
            INSERT INTO session_media (
                session_id,
                title,
                file_path,
                media_type,
                notes
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                title,
                file_path,
                media_type,
                notes,
            ),
        )

    def update_media_item(
        self,
        media_id: int,
        title: str,
        media_type: str,
        notes: str,
    ) -> None:
        self.execute(
            """
            UPDATE session_media
            SET
                title = ?,
                media_type = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                title,
                media_type,
                notes,
                media_id,
            ),
        )

    def delete_media_item(self, media_id: int) -> None:
        self.execute(
            "DELETE FROM session_media WHERE id = ?",
            (media_id,),
        )


    # -----------------------------------------------------------------
    # Reifenanalyse / KI-Datengrundlage
    # -----------------------------------------------------------------

    def get_pressure_analysis_rows(
        self,
        car_id: int | None = None,
        track_id: int | None = None,
        position: str | None = None,
        limit: int = 500,
    ) -> list[sqlite3.Row]:
        conditions = [
            """
            COALESCE(
                tm.driven_cold_pressure_bar,
                tm.cold_pressure_bar
            ) IS NOT NULL
            """,
        ]
        parameters: list[Any] = []

        if car_id is not None:
            conditions.append("s.car_id = ?")
            parameters.append(car_id)

        if track_id is not None:
            conditions.append("e.track_id = ?")
            parameters.append(track_id)

        if position is not None:
            conditions.append("tm.position = ?")
            parameters.append(position)

        parameters.append(limit)

        return self.all(
            f"""
            SELECT
                tm.id,
                tm.position,
                tm.cold_pressure_bar
                    AS recommended_cold_pressure_bar,
                tm.driven_cold_pressure_bar,
                tm.pressure_difference_bar,
                tm.hot_pressure_bar,
                tm.target_pressure_bar,
                tm.temp_middle_c,
                tm.wear_percent,
                tm.cold_tyre_temp_c,
                tm.expected_hot_tyre_temp_c,
                tm.ambient_pressure_bar,
                tm.calibration_offset_bar,
                tm.calculation_model,
                ts.id AS tyre_set_id,
                ts.set_number,
                ts.manufacturer AS tyre_manufacturer,
                ts.compound,
                ts.laps,
                ts.heat_cycles,
                s.id AS session_id,
                s.session_type,
                s.session_date,
                s.weather,
                s.air_temp_c,
                s.track_temp_c,
                s.humidity_percent,
                c.id AS car_id,
                c.manufacturer AS car_manufacturer,
                c.model AS car_model,
                e.id AS event_id,
                e.name AS event_name,
                t.id AS track_id,
                t.name AS track_name,
                d.first_name AS driver_first_name,
                d.last_name AS driver_last_name
            FROM tyre_measurements AS tm
            INNER JOIN tyre_sets AS ts
                ON tm.tyre_set_id = ts.id
            INNER JOIN sessions AS s
                ON ts.session_id = s.id
            INNER JOIN events AS e
                ON s.event_id = e.id
            INNER JOIN tracks AS t
                ON e.track_id = t.id
            INNER JOIN cars AS c
                ON s.car_id = c.id
            LEFT JOIN drivers AS d
                ON s.driver_id = d.id
            WHERE {' AND '.join(conditions)}
            ORDER BY
                s.session_date DESC,
                tm.updated_at DESC,
                tm.id DESC
            LIMIT ?
            """,
            parameters,
        )

    def get_pressure_analysis_summary(
        self,
        car_id: int | None = None,
        track_id: int | None = None,
        position: str | None = None,
    ) -> dict[str, float | int | None]:
        rows = self.get_pressure_analysis_rows(
            car_id=car_id,
            track_id=track_id,
            position=position,
            limit=2000,
        )

        if not rows:
            return {
                "samples": 0,
                "avg_recommended": None,
                "avg_driven": None,
                "avg_hot": None,
                "avg_target": None,
                "avg_difference": None,
                "avg_hot_error": None,
                "avg_middle_temp": None,
                "avg_wear": None,
                "confidence_percent": 0,
            }

        def values(column: str) -> list[float]:
            return [
                float(row[column])
                for row in rows
                if row[column] is not None
            ]

        def average(items: list[float]) -> float | None:
            if not items:
                return None
            return sum(items) / len(items)

        recommended = values(
            "recommended_cold_pressure_bar"
        )
        driven = values("driven_cold_pressure_bar")
        hot = values("hot_pressure_bar")
        target = values("target_pressure_bar")
        difference = values("pressure_difference_bar")
        middle_temp = values("temp_middle_c")
        wear = values("wear_percent")

        hot_errors = [
            float(row["hot_pressure_bar"])
            - float(row["target_pressure_bar"])
            for row in rows
            if row["hot_pressure_bar"] is not None
            and row["target_pressure_bar"] is not None
        ]

        sample_count = len(rows)

        # Ein transparenter Vertrauenswert als Vorbereitung für KI:
        # mehr Daten + geringe Heißdruckabweichung = höheres Vertrauen.
        quantity_score = min(70.0, sample_count * 4.0)
        avg_abs_hot_error = (
            average([abs(value) for value in hot_errors])
            or 0.30
        )
        quality_score = max(
            0.0,
            30.0 - min(30.0, avg_abs_hot_error * 100.0),
        )
        confidence = int(
            round(min(100.0, quantity_score + quality_score))
        )

        return {
            "samples": sample_count,
            "avg_recommended": average(recommended),
            "avg_driven": average(driven),
            "avg_hot": average(hot),
            "avg_target": average(target),
            "avg_difference": average(difference),
            "avg_hot_error": average(hot_errors),
            "avg_middle_temp": average(middle_temp),
            "avg_wear": average(wear),
            "confidence_percent": confidence,
        }


    # -----------------------------------------------------------------
    # Sessionvergleich
    # -----------------------------------------------------------------

    def get_all_sessions_for_comparison(
        self,
    ) -> list[sqlite3.Row]:
        return self.all(
            """
            SELECT
                s.*,
                e.name AS event_name,
                e.start_date AS event_start_date,
                t.id AS track_id,
                t.name AS track_name,
                c.id AS car_id,
                c.manufacturer,
                c.model,
                d.first_name AS driver_first_name,
                d.last_name AS driver_last_name,
                d.nickname AS driver_nickname
            FROM sessions AS s
            INNER JOIN events AS e
                ON s.event_id = e.id
            INNER JOIN tracks AS t
                ON e.track_id = t.id
            INNER JOIN cars AS c
                ON s.car_id = c.id
            LEFT JOIN drivers AS d
                ON s.driver_id = d.id
            ORDER BY
                s.session_date DESC,
                e.name,
                s.session_type,
                s.id DESC
            """
        )

    def get_session_tyre_summary(
        self,
        session_id: int,
    ) -> list[sqlite3.Row]:
        return self.all(
            """
            SELECT
                tm.*,
                ts.set_number,
                ts.manufacturer AS tyre_manufacturer,
                ts.compound,
                ts.laps,
                ts.heat_cycles
            FROM tyre_measurements AS tm
            INNER JOIN tyre_sets AS ts
                ON tm.tyre_set_id = ts.id
            WHERE ts.session_id = ?
            ORDER BY
                ts.id,
                CASE tm.position
                    WHEN 'FL' THEN 1
                    WHEN 'FR' THEN 2
                    WHEN 'RL' THEN 3
                    WHEN 'RR' THEN 4
                    ELSE 5
                END
            """,
            (session_id,),
        )

    def get_session_comparison_bundle(
        self,
        session_id: int,
    ) -> dict[str, Any]:
        session = self.get_session(session_id)

        if not session:
            raise ValueError(
                f"Session {session_id} wurde nicht gefunden."
            )

        return {
            "session": session,
            "setup": list(
                self.get_setup_entries(session_id)
            ),
            "changes": list(
                self.get_session_changes(session_id)
            ),
            "tyres": list(
                self.get_session_tyre_summary(session_id)
            ),
        }


    # -----------------------------------------------------------------
    # PDF-Berichte
    # -----------------------------------------------------------------

    def get_event_report_bundle(
        self,
        event_id: int,
    ) -> dict[str, Any]:
        event = self.get_event(event_id)

        if not event:
            raise ValueError(
                f"Rennevent {event_id} wurde nicht gefunden."
            )

        sessions = list(
            self.get_sessions_for_event(event_id)
        )

        session_bundles = []

        for session in sessions:
            session_id = int(session["id"])
            session_bundles.append(
                {
                    "session": session,
                    "tyres": list(
                        self.get_session_tyre_summary(
                            session_id
                        )
                    ),
                    "setup": list(
                        self.get_setup_entries(
                            session_id
                        )
                    ),
                    "changes": list(
                        self.get_session_changes(
                            session_id
                        )
                    ),
                    "media": list(
                        self.get_session_media(
                            session_id
                        )
                    ),
                }
            )

        return {
            "event": event,
            "sessions": session_bundles,
        }

