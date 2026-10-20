from __future__ import annotations

from PySide6.QtCore import QDate, QLocale
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
)

from database import Database


SESSION_TYPES = (
    "FP1",
    "FP2",
    "FP3",
    "Qualifying",
    "Qualifying 1",
    "Qualifying 2",
    "Warm-up",
    "Rennen 1",
    "Rennen 2",
    "Test",
)


def set_date(widget: QDateEdit, value: str | None) -> None:
    if not value:
        return

    parsed = QDate.fromString(value, "yyyy-MM-dd")
    if parsed.isValid():
        widget.setDate(parsed)


class CarDialog(QDialog):
    def __init__(
        self,
        database: Database,
        car_id: int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.database = database
        self.car_id = car_id
        self.setWindowTitle("Fahrzeug")
        self.resize(520, 500)

        self.manufacturer = QLineEdit()
        self.model = QLineEdit()
        self.car_class = QLineEdit()
        self.start_number = QLineEdit()
        self.start_number.setPlaceholderText("z. B. 123")
        self.year = QSpinBox()
        self.weight = QDoubleSpinBox()
        self.power = QDoubleSpinBox()
        self.drive_type = QLineEdit()
        self.notes = QTextEdit()

        self.year.setRange(0, 2100)
        self.weight.setRange(0, 5000)
        self.power.setRange(0, 5000)

        form = QFormLayout()
        form.addRow("Hersteller", self.manufacturer)
        form.addRow("Modell", self.model)
        form.addRow("Klasse", self.car_class)
        form.addRow("Startnummer", self.start_number)
        form.addRow("Baujahr", self.year)
        form.addRow("Gewicht", self.weight)
        form.addRow("Leistung", self.power)
        form.addRow("Antrieb", self.drive_type)
        form.addRow("Notizen", self.notes)

        hint = QLabel(
            "Ziel-Heißdrücke werden jetzt bei der Rennstrecke für die "
            "Kombination Fahrer + Fahrzeug gespeichert."
        )
        hint.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(hint)
        layout.addWidget(buttons)

        if car_id is not None:
            row = self.database.get_car(car_id)
            if row:
                self.manufacturer.setText(row["manufacturer"] or "")
                self.model.setText(row["model"] or "")
                self.car_class.setText(row["car_class"] or "")
                if "start_number" in row.keys():
                    self.start_number.setText(row["start_number"] or "")
                self.year.setValue(int(row["year"] or 0))
                self.weight.setValue(float(row["weight_kg"] or 0))
                self.power.setValue(float(row["horsepower"] or 0))
                self.drive_type.setText(row["drive_type"] or "")
                self.notes.setPlainText(row["notes"] or "")

    def accept(self):
        if not self.manufacturer.text().strip() or not self.model.text().strip():
            QMessageBox.warning(
                self,
                "Fehlende Angaben",
                "Hersteller und Modell sind Pflicht.",
            )
            return

        self.database.save_car(
            self.car_id,
            self.manufacturer.text().strip(),
            self.model.text().strip(),
            self.car_class.text().strip(),
            int(self.year.value()),
            float(self.weight.value()),
            float(self.power.value()),
            self.drive_type.text().strip(),
            self.notes.toPlainText().strip(),
            self.start_number.text().strip(),
        )
        super().accept()


class DriverDialog(QDialog):
    def __init__(
        self,
        database: Database,
        driver_id: int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.database = database
        self.driver_id = driver_id
        self.setWindowTitle("Fahrer")
        self.resize(500, 430)

        self.first_name = QLineEdit()
        self.last_name = QLineEdit()
        self.nickname = QLineEdit()
        self.race_number = QLineEdit()
        self.licence_class = QLineEdit()
        self.notes = QTextEdit()

        form = QFormLayout()
        form.addRow("Vorname", self.first_name)
        form.addRow("Nachname", self.last_name)
        form.addRow("Spitzname/Kürzel", self.nickname)
        form.addRow("Startnummer", self.race_number)
        form.addRow("Lizenzklasse", self.licence_class)
        form.addRow("Notizen", self.notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        if driver_id is not None:
            row = self.database.get_driver(driver_id)
            if row:
                self.first_name.setText(row["first_name"] or "")
                self.last_name.setText(row["last_name"] or "")
                self.nickname.setText(row["nickname"] or "")
                self.race_number.setText(row["race_number"] or "")
                self.licence_class.setText(row["licence_class"] or "")
                self.notes.setPlainText(row["notes"] or "")

    def accept(self):
        if not self.first_name.text().strip():
            QMessageBox.warning(self, "Fehlende Angabe", "Vorname ist Pflicht.")
            return

        self.database.save_driver(
            self.driver_id,
            self.first_name.text().strip(),
            self.last_name.text().strip(),
            self.nickname.text().strip(),
            self.race_number.text().strip(),
            self.licence_class.text().strip(),
            self.notes.toPlainText().strip(),
        )
        super().accept()


class TrackDialog(QDialog):
    def __init__(
        self,
        database: Database,
        track_id: int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.database = database
        self.track_id = track_id
        self.setWindowTitle("Rennstrecke und Fahrer-Zielwerte")
        self.resize(760, 760)

        self.name = QLineEdit()
        self.country = QLineEdit()
        self.length = QDoubleSpinBox()
        self.corners = QSpinBox()
        self.address = QLineEdit()
        self.latitude = QLineEdit()
        self.longitude = QLineEdit()
        self.notes = QTextEdit()

        self.length.setLocale(QLocale.c())
        self.length.setRange(0.000, 1000.000)
        self.length.setDecimals(3)
        self.length.setSingleStep(0.001)
        self.length.setSuffix(" km")
        self.corners.setRange(0, 1000)

        track_form = QFormLayout()
        track_form.addRow("Name", self.name)
        track_form.addRow("Land", self.country)
        track_form.addRow("Länge km", self.length)
        track_form.addRow("Kurven", self.corners)
        track_form.addRow("Adresse", self.address)
        track_form.addRow("Breitengrad", self.latitude)
        track_form.addRow("Längengrad", self.longitude)
        track_form.addRow("Notizen", self.notes)

        pressure_title = QLabel(
            "Persönlicher Ziel-Heißdruck · Fahrer + Fahrzeug + Strecke"
        )
        pressure_title.setStyleSheet("font-size: 16px; font-weight: 700;")

        self.target_driver = QComboBox()
        self.target_car = QComboBox()
        self.target_front = QDoubleSpinBox()
        self.target_rear = QDoubleSpinBox()
        self.target_notes = QLineEdit()

        self.target_driver.addItem("Fahrer auswählen …", None)
        for row in self.database.get_drivers():
            label = (
                f'{row["first_name"]} {row["last_name"] or ""}'
            ).strip()
            if row["nickname"]:
                label += f' "{row["nickname"]}"'
            self.target_driver.addItem(label, row["id"])

        self.target_car.addItem("Fahrzeug auswählen …", None)
        for row in self.database.get_cars():
            self.target_car.addItem(
                f'{row["manufacturer"]} {row["model"]}',
                row["id"],
            )

        for spin in (self.target_front, self.target_rear):
            spin.setRange(0.0, 10.0)
            spin.setDecimals(3)
            spin.setSingleStep(0.01)
            spin.setSuffix(" bar")
            spin.setSpecialValueText("-")

        self.target_driver.currentIndexChanged.connect(
            self.load_selected_target
        )
        self.target_car.currentIndexChanged.connect(
            self.load_selected_target
        )

        pressure_form = QFormLayout()
        pressure_form.addRow("Fahrer", self.target_driver)
        pressure_form.addRow("Fahrzeug", self.target_car)
        pressure_form.addRow("Ziel-Heißdruck vorne", self.target_front)
        pressure_form.addRow("Ziel-Heißdruck hinten", self.target_rear)
        pressure_form.addRow("Notiz", self.target_notes)

        self.save_target_button = QPushButton(
            "Zielwert speichern / aktualisieren"
        )
        self.save_target_button.clicked.connect(self.save_target)
        self.delete_target_button = QPushButton("Zielwert löschen")
        self.delete_target_button.clicked.connect(self.delete_target)

        target_buttons = QHBoxLayout()
        target_buttons.addWidget(self.save_target_button)
        target_buttons.addWidget(self.delete_target_button)

        self.targets_table = QTableWidget()
        self.targets_table.setColumnCount(4)
        self.targets_table.setHorizontalHeaderLabels(
            ("Fahrer", "Fahrzeug", "Vorne", "Hinten")
        )
        self.targets_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.targets_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.targets_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.targets_table.doubleClicked.connect(
            self.select_target_from_table
        )

        hint = QLabel(
            "Beim Anlegen eines Reifensatzes übernimmt die App automatisch "
            "den Wert für den Fahrer, das Fahrzeug und diese Strecke."
        )
        hint.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Save).setText(
            "Strecke speichern"
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(track_form)
        layout.addWidget(pressure_title)
        layout.addLayout(pressure_form)
        layout.addLayout(target_buttons)
        layout.addWidget(self.targets_table)
        layout.addWidget(hint)
        layout.addWidget(buttons)

        if track_id is not None:
            row = self.database.get_track(track_id)
            if row:
                self.name.setText(row["name"] or "")
                self.country.setText(row["country"] or "")
                self.length.setValue(float(row["length_km"] or 0))
                self.corners.setValue(int(row["corners"] or 0))
                self.address.setText(row["address"] or "")
                self.latitude.setText(
                    "" if row["latitude"] is None else str(row["latitude"])
                )
                self.longitude.setText(
                    "" if row["longitude"] is None else str(row["longitude"])
                )
                self.notes.setPlainText(row["notes"] or "")

        self.update_target_controls()
        self.refresh_targets_table()

    def _optional_float(self, value: str):
        value = value.strip().replace(",", ".")
        if not value:
            return None
        return float(value)

    def update_target_controls(self):
        enabled = self.track_id is not None
        for widget in (
            self.target_driver,
            self.target_car,
            self.target_front,
            self.target_rear,
            self.target_notes,
            self.save_target_button,
            self.delete_target_button,
            self.targets_table,
        ):
            widget.setEnabled(enabled)

    def load_selected_target(self):
        if self.track_id is None:
            return
        driver_id = self.target_driver.currentData()
        car_id = self.target_car.currentData()
        if driver_id is None or car_id is None:
            self.target_front.setValue(0)
            self.target_rear.setValue(0)
            self.target_notes.clear()
            return

        row = self.database.get_driver_track_pressure_target(
            int(driver_id),
            int(self.track_id),
            int(car_id),
        )
        self.target_front.setValue(
            float(row["target_hot_front_bar"] or 0) if row else 0
        )
        self.target_rear.setValue(
            float(row["target_hot_rear_bar"] or 0) if row else 0
        )
        self.target_notes.setText(row["notes"] or "" if row else "")

    def save_target(self):
        if self.track_id is None:
            QMessageBox.information(
                self,
                "Strecke zuerst speichern",
                "Speichere zuerst die Strecke. Öffne sie danach erneut, "
                "um persönliche Zielwerte einzutragen.",
            )
            return

        driver_id = self.target_driver.currentData()
        car_id = self.target_car.currentData()
        if driver_id is None or car_id is None:
            QMessageBox.warning(
                self,
                "Auswahl fehlt",
                "Bitte Fahrer und Fahrzeug auswählen.",
            )
            return
        if self.target_front.value() <= 0 or self.target_rear.value() <= 0:
            QMessageBox.warning(
                self,
                "Ziel-Heißdruck fehlt",
                "Bitte für Vorder- und Hinterachse einen Wert größer 0 eintragen.",
            )
            return

        self.database.save_driver_track_pressure_target(
            int(driver_id),
            int(self.track_id),
            int(car_id),
            float(self.target_front.value()),
            float(self.target_rear.value()),
            self.target_notes.text().strip(),
        )
        self.refresh_targets_table()
        QMessageBox.information(
            self,
            "Gespeichert",
            "Der persönliche Ziel-Heißdruck wurde gespeichert.",
        )

    def delete_target(self):
        if self.track_id is None:
            return
        driver_id = self.target_driver.currentData()
        car_id = self.target_car.currentData()
        if driver_id is None or car_id is None:
            return

        answer = QMessageBox.question(
            self,
            "Zielwert löschen",
            "Diesen persönlichen Zielwert wirklich löschen?",
        )
        if answer != QMessageBox.Yes:
            return

        self.database.delete_driver_track_pressure_target(
            int(driver_id),
            int(self.track_id),
            int(car_id),
        )
        self.load_selected_target()
        self.refresh_targets_table()

    def refresh_targets_table(self):
        if self.track_id is None:
            self.targets_table.setRowCount(0)
            return

        rows = self.database.get_pressure_targets_for_track(
            int(self.track_id)
        )
        self.targets_table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            driver = (
                f'{row["first_name"]} {row["last_name"] or ""}'
            ).strip()
            if row["nickname"]:
                driver += f' "{row["nickname"]}"'
            car = f'{row["manufacturer"]} {row["model"]}'
            values = (
                driver,
                car,
                f'{float(row["target_hot_front_bar"]):.3f} bar',
                f'{float(row["target_hot_rear_bar"]):.3f} bar',
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(
                    32,
                    (
                        int(row["driver_id"]),
                        int(row["car_id"]),
                    ),
                )
                self.targets_table.setItem(index, column, item)
        self.targets_table.resizeColumnsToContents()

    def select_target_from_table(self):
        row_index = self.targets_table.currentRow()
        if row_index < 0:
            return
        item = self.targets_table.item(row_index, 0)
        if not item:
            return
        driver_id, car_id = item.data(32)
        driver_index = self.target_driver.findData(driver_id)
        car_index = self.target_car.findData(car_id)
        if driver_index >= 0:
            self.target_driver.setCurrentIndex(driver_index)
        if car_index >= 0:
            self.target_car.setCurrentIndex(car_index)
        self.load_selected_target()

    def accept(self):
        if not self.name.text().strip():
            QMessageBox.warning(
                self,
                "Fehlende Angabe",
                "Name ist Pflicht.",
            )
            return

        try:
            latitude = self._optional_float(self.latitude.text())
            longitude = self._optional_float(self.longitude.text())
        except ValueError:
            QMessageBox.warning(
                self,
                "Koordinaten ungültig",
                "Bitte Dezimalgrad verwenden, z. B. 47.2197 und 14.7647.",
            )
            return

        self.track_id = self.database.save_track(
            self.track_id,
            self.name.text().strip(),
            self.country.text().strip(),
            float(self.length.value()),
            int(self.corners.value()),
            self.address.text().strip(),
            latitude,
            longitude,
            self.notes.toPlainText().strip(),
        )
        self.update_target_controls()
        super().accept()


class EventDialog(QDialog):
    def __init__(
        self,
        database: Database,
        event_id: int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.database = database
        self.event_id = event_id
        self.setWindowTitle("Rennevent")
        self.resize(520, 450)

        self.name = QLineEdit()
        self.track = QComboBox()
        self.start_date = QDateEdit(QDate.currentDate())
        self.end_date = QDateEdit(QDate.currentDate())
        self.championship = QLineEdit()
        self.event_type = QLineEdit("Rennwochenende")
        self.notes = QTextEdit()

        for row in self.database.get_tracks():
            self.track.addItem(row["name"], row["id"])

        for widget in (self.start_date, self.end_date):
            widget.setCalendarPopup(True)
            widget.setDisplayFormat("yyyy-MM-dd")

        form = QFormLayout()
        form.addRow("Eventname", self.name)
        form.addRow("Rennstrecke", self.track)
        form.addRow("Startdatum", self.start_date)
        form.addRow("Enddatum", self.end_date)
        form.addRow("Meisterschaft", self.championship)
        form.addRow("Eventtyp", self.event_type)
        form.addRow("Notizen", self.notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        if event_id is not None:
            row = self.database.get_event(event_id)
            if row:
                self.name.setText(row["name"] or "")
                index = self.track.findData(row["track_id"])
                if index >= 0:
                    self.track.setCurrentIndex(index)
                set_date(self.start_date, row["start_date"])
                set_date(self.end_date, row["end_date"])
                self.championship.setText(row["championship"] or "")
                self.event_type.setText(row["event_type"] or "")
                self.notes.setPlainText(row["notes"] or "")

    def accept(self):
        if not self.name.text().strip() or self.track.currentData() is None:
            QMessageBox.warning(
                self,
                "Fehlende Angaben",
                "Eventname und Rennstrecke sind Pflicht.",
            )
            return

        self.database.save_event(
            self.event_id,
            self.name.text().strip(),
            int(self.track.currentData()),
            self.start_date.date().toString("yyyy-MM-dd"),
            self.end_date.date().toString("yyyy-MM-dd"),
            self.championship.text().strip(),
            self.event_type.text().strip(),
            self.notes.toPlainText().strip(),
        )
        super().accept()


class SessionDialog(QDialog):
    def __init__(
        self,
        database: Database,
        event_id: int,
        session_id: int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.database = database
        self.event_id = event_id
        self.session_id = session_id
        self.setWindowTitle("Session")
        self.resize(520, 520)

        self.car = QComboBox()
        self.drivers = QListWidget()
        self.drivers.setSelectionMode(QAbstractItemView.MultiSelection)
        self.drivers.setMinimumHeight(110)
        self.session_type = QComboBox()
        self.session_date = QDateEdit(QDate.currentDate())
        self.weather = QLineEdit("Trocken")
        self.air_temp = QDoubleSpinBox()
        self.track_temp = QDoubleSpinBox()
        self.rim_temp = QDoubleSpinBox()
        self.humidity = QDoubleSpinBox()
        self.notes = QTextEdit()

        for row in self.database.get_cars():
            self.car.addItem(
                f'{row["manufacturer"]} {row["model"]}',
                row["id"],
            )

        for row in self.database.get_drivers():
            label = f'{row["first_name"]} {row["last_name"] or ""}'.strip()
            item = QListWidgetItem(label)
            item.setData(256, int(row["id"]))
            self.drivers.addItem(item)

        self.session_type.addItems(SESSION_TYPES)
        self.session_date.setCalendarPopup(True)
        self.session_date.setDisplayFormat("yyyy-MM-dd")

        for spin in (self.air_temp, self.track_temp, self.rim_temp):
            spin.setRange(-50, 100)
            spin.setDecimals(1)
            spin.setSuffix(" °C")

        self.humidity.setRange(0, 100)
        self.humidity.setDecimals(1)
        self.humidity.setSuffix(" %")

        form = QFormLayout()
        form.addRow("Fahrzeug", self.car)
        form.addRow("Fahrer (Mehrfachauswahl)", self.drivers)
        form.addRow("Session-Typ", self.session_type)
        form.addRow("Datum", self.session_date)
        form.addRow("Wetter", self.weather)
        form.addRow("Lufttemperatur", self.air_temp)
        form.addRow("Asphalttemperatur", self.track_temp)
        form.addRow("Felgentemperatur", self.rim_temp)
        form.addRow("Luftfeuchtigkeit", self.humidity)
        form.addRow("Notizen", self.notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        if session_id is not None:
            row = self.database.get_session(session_id)
            if row:
                index = self.car.findData(row["car_id"])
                if index >= 0:
                    self.car.setCurrentIndex(index)
                selected_driver_ids = set(self.database.get_session_driver_ids(session_id))
                for i in range(self.drivers.count()):
                    item = self.drivers.item(i)
                    item.setSelected(int(item.data(256)) in selected_driver_ids)
                index = self.session_type.findText(row["session_type"])
                if index >= 0:
                    self.session_type.setCurrentIndex(index)
                set_date(self.session_date, row["session_date"])
                self.weather.setText(row["weather"] or "")
                self.air_temp.setValue(float(row["air_temp_c"] or 0))
                self.track_temp.setValue(float(row["track_temp_c"] or 0))
                self.rim_temp.setValue(float(row["rim_temp_c"] or 0))
                self.humidity.setValue(float(row["humidity_percent"] or 0))
                self.notes.setPlainText(row["notes"] or "")

    def accept(self):
        if self.car.currentData() is None:
            QMessageBox.warning(
                self,
                "Fehlendes Fahrzeug",
                "Bitte zuerst ein Fahrzeug anlegen.",
            )
            return

        driver_ids = [
            int(item.data(256))
            for item in self.drivers.selectedItems()
        ]
        driver_id = driver_ids[0] if driver_ids else None

        saved_session_id = self.database.save_session(
            self.session_id,
            self.event_id,
            int(self.car.currentData()),
            driver_id,
            self.session_type.currentText(),
            self.session_date.date().toString("yyyy-MM-dd"),
            self.weather.text().strip(),
            float(self.air_temp.value()),
            float(self.track_temp.value()),
            float(self.rim_temp.value()),
            float(self.humidity.value()),
            self.notes.toPlainText().strip(),
        )
        self.database.set_session_drivers(saved_session_id, driver_ids)
        super().accept()


class TyreSetDialog(QDialog):
    def __init__(
        self,
        database: Database,
        session_id: int,
        tyre_set_id: int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.database = database
        self.session_id = session_id
        self.tyre_set_id = tyre_set_id
        self.setWindowTitle("Reifensatz")
        self.resize(500, 430)

        self.set_number = QLineEdit()
        self.manufacturer = QLineEdit()
        self.tyre_type = QComboBox()
        self.tyre_type.addItems(["Slick", "Wet / Regenreifen"])
        self.condition = QComboBox()
        self.condition.addItems(["neu", "gebraucht", "verschlissen", "beim Reifendienst"])
        self.compound = QLineEdit()
        self.laps = QSpinBox()
        self.heat_cycles = QSpinBox()
        self.notes = QTextEdit()

        self.laps.setRange(0, 100000)
        self.heat_cycles.setRange(0, 1000)

        form = QFormLayout()
        form.addRow("Satznummer", self.set_number)
        form.addRow("Reifenart", self.tyre_type)
        form.addRow("Hersteller / Marke", self.manufacturer)
        form.addRow("Zustand", self.condition)
        form.addRow("Mischung", self.compound)
        form.addRow("Runden", self.laps)
        form.addRow("Heat Cycles", self.heat_cycles)
        form.addRow("Notizen", self.notes)

        self.note_button = QPushButton("Reifen Notiz")
        self.note_button.setEnabled(tyre_set_id is not None)
        self.note_button.clicked.connect(self.open_tyre_note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.note_button)
        layout.addWidget(buttons)

        if tyre_set_id is not None:
            row = self.database.get_tyre_set(tyre_set_id)
            if row:
                self.set_number.setText(row["set_number"] or "")
                self.manufacturer.setText(row["manufacturer"] or "")
                if "tyre_type" in row.keys():
                    idx = self.tyre_type.findText(row["tyre_type"] or "Slick")
                    if idx >= 0:
                        self.tyre_type.setCurrentIndex(idx)
                if "condition" in row.keys():
                    idx = self.condition.findText(row["condition"] or "gebraucht")
                    if idx >= 0:
                        self.condition.setCurrentIndex(idx)
                self.compound.setText(row["compound"] or "")
                self.laps.setValue(int(row["laps"] or 0))
                self.heat_cycles.setValue(int(row["heat_cycles"] or 0))
                self.notes.setPlainText(row["notes"] or "")

    def accept(self):
        self.database.save_tyre_set(
            self.tyre_set_id,
            self.session_id,
            self.set_number.text().strip(),
            self.manufacturer.text().strip(),
            self.compound.text().strip(),
            int(self.laps.value()),
            int(self.heat_cycles.value()),
            self.notes.toPlainText().strip(),
            self.tyre_type.currentText(),
            self.condition.currentText(),
        )
        super().accept()

    def open_tyre_note(self):
        if self.tyre_set_id is None:
            QMessageBox.information(
                self,
                "Reifensatz zuerst speichern",
                "Speichere den Reifensatz zuerst. Danach kannst du eine Reifen Notiz anlegen.",
            )
            return
        dialog = TyreNoteDialog(self.database, self.tyre_set_id, self)
        dialog.exec()


class TyreNoteDialog(QDialog):
    def __init__(self, database: Database, tyre_set_id: int, parent=None):
        super().__init__(parent)
        self.database = database
        self.tyre_set_id = tyre_set_id
        self.setWindowTitle("Reifen Notiz")
        self.resize(560, 520)

        tyre_set = database.get_tyre_set(tyre_set_id)
        self.action = QComboBox()
        self.action.addItems([
            "weggebracht",
            "neu bezogen",
            "montiert",
            "demontiert",
            "geprüft",
            "sonstiges",
        ])
        self.tyre_type = QComboBox()
        self.tyre_type.addItems(["Slick", "Wet / Regenreifen"])
        self.manufacturer = QLineEdit()
        self.condition_before = QComboBox()
        self.condition_before.addItems(["neu", "gebraucht", "verschlissen", "beim Reifendienst"])
        self.condition_after = QComboBox()
        self.condition_after.addItems(["neu", "gebraucht", "verschlissen", "beim Reifendienst"])
        self.notes = QTextEdit()
        self.notes.setPlaceholderText(
            "z. B. Reifen weggebracht, neue Slicks drauf / neue Regenreifen drauf ..."
        )

        if tyre_set:
            self.manufacturer.setText(tyre_set["manufacturer"] or "")
            if "tyre_type" in tyre_set.keys():
                idx = self.tyre_type.findText(tyre_set["tyre_type"] or "Slick")
                if idx >= 0:
                    self.tyre_type.setCurrentIndex(idx)
            if "condition" in tyre_set.keys():
                for box in (self.condition_before, self.condition_after):
                    idx = box.findText(tyre_set["condition"] or "gebraucht")
                    if idx >= 0:
                        box.setCurrentIndex(idx)

        session_info = database.one(
            """
            SELECT c.manufacturer, c.model, c.start_number, ts.set_number
            FROM tyre_sets ts
            JOIN sessions s ON s.id = ts.session_id
            JOIN cars c ON c.id = s.car_id
            WHERE ts.id = ?
            """,
            (tyre_set_id,),
        )
        header_text = ""
        if session_info:
            number = session_info["start_number"] or "-"
            header_text = (
                f'Fahrzeug #{number} · {session_info["manufacturer"]} '
                f'{session_info["model"]} · Satz {session_info["set_number"]}'
            )
        header = QLabel(header_text)
        header.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Aktion", self.action)
        form.addRow("Reifenart", self.tyre_type)
        form.addRow("Marke", self.manufacturer)
        form.addRow("Zustand vorher", self.condition_before)
        form.addRow("Zustand nachher", self.condition_after)
        form.addRow("Notiz", self.notes)

        history = QTextEdit()
        history.setReadOnly(True)
        history.setMinimumHeight(130)
        lines = []
        for row in database.get_tyre_notes(tyre_set_id):
            lines.append(
                f'{row["note_time"]} · {row["action"] or ""} · '
                f'{row["tyre_type"] or ""} · {row["manufacturer"] or ""} · '
                f'{row["notes"] or ""}'
            )
        history.setPlainText("\n".join(lines) if lines else "Noch keine Reifen Notizen.")

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(header)
        layout.addLayout(form)
        layout.addWidget(QLabel("Bisherige Reifen Notizen"))
        layout.addWidget(history)
        layout.addWidget(buttons)

    def accept(self):
        self.database.add_tyre_note(
            self.tyre_set_id,
            self.action.currentText(),
            self.tyre_type.currentText(),
            self.manufacturer.text().strip(),
            self.condition_before.currentText(),
            self.condition_after.currentText(),
            self.notes.toPlainText().strip(),
        )
        super().accept()


class TyreMeasurementDialog(QDialog):
    MODEL_VERSION = "box-correction-v2"

    def __init__(
        self,
        database: Database,
        tyre_set_id: int,
        position: str,
        parent=None,
    ):
        super().__init__(parent)
        self.database = database
        self.tyre_set_id = tyre_set_id
        self.position = position
        self.history_samples = 0
        self.existing_temp_inside = None
        self.existing_temp_outside = None

        wheel_names = {
            "FL": "Vorne links",
            "FR": "Vorne rechts",
            "RL": "Hinten links",
            "RR": "Hinten rechts",
        }

        self.setWindowTitle(
            f"Reifen · {wheel_names.get(position, position)}"
        )
        self.resize(610, 650)

        german_locale = QLocale(
            QLocale.German,
            QLocale.Germany,
        )

        # Eingaben für die automatische Berechnung.
        self.target = QDoubleSpinBox()
        self.cold_tyre_temp = QDoubleSpinBox()
        self.expected_hot_tyre_temp = QDoubleSpinBox()
        self.ambient_pressure = QDoubleSpinBox()
        self.history_correction = QDoubleSpinBox()

        # Automatisch berechneter Kaltdruck.
        self.cold = QDoubleSpinBox()
        self.cold.setReadOnly(True)
        self.cold.setButtonSymbols(
            QDoubleSpinBox.NoButtons
        )

        # Tatsächlich verwendeter Kaltdruck.
        self.driven_cold = QDoubleSpinBox()

        # Messwerte nach der Session.
        self.hot = QDoubleSpinBox()
        self.temp_middle = QDoubleSpinBox()
        self.wear = QDoubleSpinBox()
        self.notes = QTextEdit()

        # Komma-Eingabe für alle Dezimalwerte.
        for spin in (
            self.target,
            self.cold_tyre_temp,
            self.expected_hot_tyre_temp,
            self.ambient_pressure,
            self.history_correction,
            self.cold,
            self.driven_cold,
            self.driven_cold,
            self.hot,
            self.temp_middle,
            self.wear,
        ):
            spin.setLocale(german_locale)
            spin.setKeyboardTracking(False)

        for spin in (
            self.cold,
            self.driven_cold,
            self.hot,
            self.target,
        ):
            spin.setRange(0, 10)
            spin.setDecimals(3)
            spin.setSingleStep(0.01)
            spin.setSuffix(" bar")
            spin.setSpecialValueText("-")

        self.ambient_pressure.setRange(0.80000, 1.20000)
        self.ambient_pressure.setDecimals(5)
        self.ambient_pressure.setSingleStep(0.001)
        self.ambient_pressure.setSuffix(" bar abs")
        self.ambient_pressure.setValue(1.01325)

        self.history_correction.setRange(-0.300, 0.300)
        self.history_correction.setDecimals(3)
        self.history_correction.setSingleStep(0.005)
        self.history_correction.setSuffix(" bar")

        for spin in (
            self.cold_tyre_temp,
            self.expected_hot_tyre_temp,
            self.temp_middle,
        ):
            spin.setRange(-40, 200)
            spin.setDecimals(1)
            spin.setSingleStep(0.5)
            spin.setSuffix(" °C")

        self.cold_tyre_temp.setValue(20.0)
        self.expected_hot_tyre_temp.setValue(80.0)

        self.wear.setRange(0, 100)
        self.wear.setDecimals(1)
        self.wear.setSuffix(" %")

        calculate_button = QPushButton(
            "Kaltdruck neu berechnen"
        )
        calculate_button.clicked.connect(
            self.calculate_button_clicked
        )

        history_button = QPushButton(
            "Datenbank-Korrektur laden"
        )
        history_button.clicked.connect(
            self.load_history_correction
        )

        self.next_cold_label = QLabel("Noch kein Heißdruck gemessen.")
        self.next_cold_label.setWordWrap(True)
        self.next_cold_label.setObjectName("pressureCalculationResult")

        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        self.result_label.setObjectName(
            "pressureCalculationResult"
        )

        explanation = QLabel(
            "Du gibst Ziel-Heißdruck, aktuelle Reifentemperatur, "
            "erwartete heiße Reifentemperatur und Umgebungsdruck ein. "
            "Der Kaltdruck wird automatisch berechnet. "
            "Trage zusätzlich den tatsächlich gefahrenen Kaltdruck ein. "
            "Dieser Wert wird später für die Datenbank- und KI-Vergleiche "
            "verwendet. Als gemessene Reifentemperatur reicht die Temperatur "
            "in der Mitte der Lauffläche."
        )
        explanation.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Ziel-Heißdruck", self.target)
        form.addRow(
            "Reifentemperatur vor dem Einsatz",
            self.cold_tyre_temp,
        )
        form.addRow(
            "Erwartete Reifentemperatur heiß",
            self.expected_hot_tyre_temp,
        )
        form.addRow(
            "Umgebungsdruck",
            self.ambient_pressure,
        )
        form.addRow(
            "Datenbank-Korrektur",
            self.history_correction,
        )
        form.addRow(
            "Empfohlener Kaltdruck",
            self.cold,
        )
        form.addRow(
            "Referenz-Kaltdruck / gefahren mit",
            self.driven_cold,
        )
        form.addRow("", calculate_button)
        form.addRow("", history_button)
        form.addRow("", self.result_label)
        form.addRow("", explanation)

        form.addRow("Gemessener Heißdruck", self.hot)
        form.addRow("Empfehlung nächster Kaltwert", self.next_cold_label)
        form.addRow(
            "Reifentemperatur Mitte",
            self.temp_middle,
        )
        form.addRow("Verschleiß", self.wear)
        form.addRow("Notizen", self.notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        row = self.database.get_tyre_measurement(
            tyre_set_id,
            position,
        )

        if row:
            self.target.setValue(
                float(row["target_pressure_bar"] or 0)
            )
            self.hot.setValue(
                float(row["hot_pressure_bar"] or 0)
            )
            self.driven_cold.setValue(
                float(
                    (row["reference_cold_pressure_bar"] if "reference_cold_pressure_bar" in row.keys() else None)
                    or row["driven_cold_pressure_bar"]
                    or row["cold_pressure_bar"]
                    or 0
                )
            )
            self.temp_middle.setValue(
                float(row["temp_middle_c"] or 0)
            )
            self.existing_temp_inside = row["temp_inside_c"]
            self.existing_temp_outside = row["temp_outside_c"]
            self.wear.setValue(
                float(row["wear_percent"] or 0)
            )
            self.notes.setPlainText(
                row["notes"] or ""
            )

            if row["cold_tyre_temp_c"] is not None:
                self.cold_tyre_temp.setValue(
                    float(row["cold_tyre_temp_c"])
                )

            if (
                row["expected_hot_tyre_temp_c"]
                is not None
            ):
                self.expected_hot_tyre_temp.setValue(
                    float(
                        row[
                            "expected_hot_tyre_temp_c"
                        ]
                    )
                )

            if row["ambient_pressure_bar"] is not None:
                self.ambient_pressure.setValue(
                    float(row["ambient_pressure_bar"])
                )

            if (
                row["calibration_offset_bar"]
                is not None
            ):
                self.history_correction.setValue(
                    float(
                        row[
                            "calibration_offset_bar"
                        ]
                    )
                )

        # Live-Berechnung nach abgeschlossener Eingabe.
        for widget in (
            self.target,
            self.cold_tyre_temp,
            self.expected_hot_tyre_temp,
            self.ambient_pressure,
            self.history_correction,
        ):
            widget.valueChanged.connect(
                self.recalculate
            )

        self.hot.valueChanged.connect(self.update_box_correction)
        self.driven_cold.valueChanged.connect(self.update_box_correction)
        self.target.valueChanged.connect(self.update_box_correction)
        self.recalculate()
        self.update_box_correction()

    def update_box_correction(self, *_):
        reference = float(self.driven_cold.value())
        hot = float(self.hot.value())
        target = float(self.target.value())
        if reference <= 0 or hot <= 0 or target <= 0:
            self.next_cold_label.setText("Referenz kalt + Ziel heiß + gemessenen Heißdruck eintragen.")
            return None
        difference, recommended = self.database.calculate_next_cold_pressure(
            reference, hot, target
        )
        direction = "ablassen" if difference > 0 else "erhöhen" if difference < 0 else "keine Änderung"
        self.next_cold_label.setText(
            f"Abweichung {difference:+.2f} bar · {direction} · "
            f"nächster Kaltdruck {recommended:.2f} bar"
        )
        return recommended

    def _commit_spinbox_text(self):
        """
        Übernimmt auch einen gerade mit Komma eingegebenen Wert,
        bevor die Berechnung ausgeführt wird.
        """
        for widget in (
            self.target,
            self.cold_tyre_temp,
            self.expected_hot_tyre_temp,
            self.ambient_pressure,
            self.history_correction,
            self.hot,
            self.temp_middle,
            self.wear,
        ):
            widget.interpretText()

    def calculate_button_clicked(self):
        self._commit_spinbox_text()

        if self.target.value() <= 0:
            QMessageBox.warning(
                self,
                "Ziel-Heißdruck fehlt",
                "Bitte zuerst den Ziel-Heißdruck eingeben.",
            )
            self.target.setFocus()
            return

        result = self.recalculate(show_error=True)

        if result is not None:
            QMessageBox.information(
                self,
                "Kaltdruck berechnet",
                (
                    f"Empfohlener Kaltdruck: "
                    f"{result:.3f} bar"
                ),
            )

    def load_history_correction(self):
        result = (
            self.database
            .get_historical_pressure_correction(
                self.tyre_set_id,
                self.position,
            )
        )

        self.history_samples = int(
            result["samples"]
        )
        correction = float(
            result["correction_bar"]
        )

        self.history_correction.setValue(
            correction
        )

        if self.history_samples < 2:
            QMessageBox.information(
                self,
                "Noch zu wenig Vergleichsdaten",
                (
                    f"Es wurden {self.history_samples} passende "
                    "historische Datensätze gefunden. "
                    "Für eine automatische Korrektur werden "
                    "mindestens 2 benötigt."
                ),
            )
        else:
            QMessageBox.information(
                self,
                "Datenbank-Korrektur",
                (
                    f"{self.history_samples} vergleichbare "
                    "Datensätze wurden ausgewertet.\n\n"
                    f"Korrektur: {correction:+.3f} bar"
                ),
            )

        self.recalculate()

    def recalculate(self, *_, show_error=False):
        self._commit_spinbox_text()

        try:
            result = (
                self.database.calculate_cold_pressure(
                    float(self.target.value()),
                    float(
                        self.cold_tyre_temp.value()
                    ),
                    float(
                        self.expected_hot_tyre_temp.value()
                    ),
                    float(
                        self.ambient_pressure.value()
                    ),
                    float(
                        self.history_correction.value()
                    ),
                )
            )
        except ValueError as error:
            self.cold.setValue(0)
            self.result_label.setText(
                str(error)
            )

            if show_error:
                QMessageBox.warning(
                    self,
                    "Berechnung nicht möglich",
                    str(error),
                )

            return None

        self.cold.setValue(result)

        if self.driven_cold.value() <= 0:
            self.driven_cold.setValue(result)

        correction = (
            float(self.history_correction.value())
        )
        sample_text = (
            f" · {self.history_samples} Vergleichswerte"
            if self.history_samples
            else ""
        )

        self.result_label.setText(
            f"Empfehlung: {result:.3f} bar"
            f" · Korrektur {correction:+.3f} bar"
            f"{sample_text}"
        )

        return result

    def accept(self):
        self._commit_spinbox_text()

        if self.target.value() <= 0:
            QMessageBox.warning(
                self,
                "Ziel-Heißdruck fehlt",
                "Bitte den gewünschten Ziel-Heißdruck eingeben.",
            )
            return

        recommended = self.recalculate(
            show_error=True
        )

        if recommended is None:
            return

        if self.driven_cold.value() <= 0:
            QMessageBox.warning(
                self,
                "Gefahrener Reifendruck fehlt",
                (
                    "Bitte eintragen, mit welchem Kaltdruck "
                    "der Reifen tatsächlich gefahren wurde."
                ),
            )
            self.driven_cold.setFocus()
            return

        next_cold = self.update_box_correction()

        self.database.save_tyre_measurement(
            self.tyre_set_id,
            self.position,
            float(recommended),
            float(self.hot.value()),
            float(self.target.value()),
            self.existing_temp_inside,
            float(self.temp_middle.value()),
            self.existing_temp_outside,
            float(self.wear.value()),
            self.notes.toPlainText().strip(),
            cold_tyre_temp_c=float(
                self.cold_tyre_temp.value()
            ),
            expected_hot_tyre_temp_c=float(
                self.expected_hot_tyre_temp.value()
            ),
            ambient_pressure_bar=float(
                self.ambient_pressure.value()
            ),
            calculated_cold_pressure_bar=float(
                recommended
            ),
            calibration_offset_bar=float(
                self.history_correction.value()
            ),
            calculation_model=self.MODEL_VERSION,
            driven_cold_pressure_bar=float(
                self.driven_cold.value()
            ),
            reference_cold_pressure_bar=float(
                self.driven_cold.value()
            ),
            recommended_next_cold_pressure_bar=(
                float(next_cold) if next_cold is not None else None
            ),
        )

        self.database.log_pressure_recommendation(
            self.tyre_set_id,
            self.position,
            float(self.target.value()),
            float(self.cold_tyre_temp.value()),
            float(
                self.expected_hot_tyre_temp.value()
            ),
            float(self.ambient_pressure.value()),
            float(
                self.history_correction.value()
            ),
            float(recommended),
            self.MODEL_VERSION,
        )

        super().accept()


SETUP_CATEGORIES = (
    "Fahrwerk",
    "Spur/Sturz",
    "Aerodynamik",
    "Bremsen",
    "Differential",
    "ABS",
    "Traktionskontrolle",
    "Getriebe",
    "Reifendruck",
    "Sonstiges",
)


class SetupEntryDialog(QDialog):
    def __init__(
        self,
        database: Database,
        session_id: int,
        setup_id: int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.database = database
        self.session_id = session_id
        self.setup_id = setup_id

        self.setWindowTitle("Setup-Eintrag")
        self.resize(520, 430)

        self.category = QComboBox()
        self.category.addItems(SETUP_CATEGORIES)

        self.parameter_name = QLineEdit()
        self.old_value = QLineEdit()
        self.new_value = QLineEdit()
        self.unit = QLineEdit()
        self.notes = QTextEdit()

        form = QFormLayout()
        form.addRow("Kategorie", self.category)
        form.addRow("Parameter", self.parameter_name)
        form.addRow("Altwert", self.old_value)
        form.addRow("Neuwert", self.new_value)
        form.addRow("Einheit", self.unit)
        form.addRow("Notizen", self.notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        if setup_id is not None:
            row = self.database.get_setup_entry(setup_id)
            if row:
                index = self.category.findText(row["category"] or "")
                if index >= 0:
                    self.category.setCurrentIndex(index)

                self.parameter_name.setText(
                    row["parameter_name"] or ""
                )
                self.old_value.setText(row["old_value"] or "")
                self.new_value.setText(row["new_value"] or "")
                self.unit.setText(row["unit"] or "")
                self.notes.setPlainText(row["notes"] or "")

    def accept(self):
        if not self.parameter_name.text().strip():
            QMessageBox.warning(
                self,
                "Fehlende Angabe",
                "Bitte einen Parameter eingeben.",
            )
            return

        self.database.save_setup_entry(
            self.setup_id,
            self.session_id,
            self.category.currentText(),
            self.parameter_name.text().strip(),
            self.old_value.text().strip(),
            self.new_value.text().strip(),
            self.unit.text().strip(),
            self.notes.toPlainText().strip(),
        )
        super().accept()


CHANGE_CATEGORIES = (
    "Fahrwerk",
    "Spur/Sturz",
    "Aerodynamik",
    "Bremsen",
    "Motor",
    "Getriebe",
    "Differential",
    "Elektronik",
    "Reparatur",
    "Sonstiges",
)


class SessionChangeDialog(QDialog):
    def __init__(
        self,
        database: Database,
        session_id: int,
        change_id: int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.database = database
        self.session_id = session_id
        self.change_id = change_id

        self.setWindowTitle("Fahrzeugänderung")
        self.resize(540, 430)

        self.category = QComboBox()
        self.category.addItems(CHANGE_CATEGORIES)

        self.title_edit = QLineEdit()
        self.description = QTextEdit()

        form = QFormLayout()
        form.addRow("Kategorie", self.category)
        form.addRow("Bezeichnung", self.title_edit)
        form.addRow("Beschreibung / Alt → Neu", self.description)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        if change_id is not None:
            row = self.database.get_session_change(change_id)

            if row:
                index = self.category.findText(
                    row["category"] or ""
                )
                if index >= 0:
                    self.category.setCurrentIndex(index)

                self.title_edit.setText(
                    row["title"] or ""
                )
                self.description.setPlainText(
                    row["description"] or ""
                )

    def accept(self):
        title = self.title_edit.text().strip()

        if not title:
            QMessageBox.warning(
                self,
                "Fehlende Angabe",
                "Bitte eine Bezeichnung eingeben.",
            )
            return

        self.database.save_session_change(
            self.change_id,
            self.session_id,
            self.category.currentText(),
            title,
            self.description.toPlainText().strip(),
        )
        super().accept()


MEDIA_TYPES = (
    "Fahrzeug",
    "Reifen",
    "Setupblatt",
    "Schaden",
    "Wetter",
    "Dokument",
    "Video",
    "Sonstiges",
)


class MediaDialog(QDialog):
    def __init__(
        self,
        database: Database,
        session_id: int,
        media_id: int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.database = database
        self.session_id = session_id
        self.media_id = media_id
        self.selected_file = ""

        self.setWindowTitle("Bild oder Datei")
        self.resize(560, 430)

        self.title_edit = QLineEdit()
        self.media_type = QComboBox()
        self.media_type.addItems(MEDIA_TYPES)
        self.file_edit = QLineEdit()
        self.file_edit.setReadOnly(True)
        self.notes = QTextEdit()

        browse_button = QPushButton("Datei auswählen")
        browse_button.clicked.connect(self.choose_file)

        file_row = QHBoxLayout()
        file_row.addWidget(self.file_edit, 1)
        file_row.addWidget(browse_button)

        form = QFormLayout()
        form.addRow("Titel", self.title_edit)
        form.addRow("Kategorie", self.media_type)
        form.addRow("Datei", file_row)
        form.addRow("Notizen", self.notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        if media_id is not None:
            row = self.database.get_media_item(media_id)
            if row:
                self.title_edit.setText(row["title"] or "")
                index = self.media_type.findText(row["media_type"] or "")
                if index >= 0:
                    self.media_type.setCurrentIndex(index)
                self.selected_file = row["file_path"] or ""
                self.file_edit.setText(self.selected_file)
                self.notes.setPlainText(row["notes"] or "")

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Bild oder Datei auswählen",
            "",
            (
                "Alle unterstützten Dateien "
                "(*.jpg *.jpeg *.png *.webp *.bmp *.pdf *.doc *.docx "
                "*.xls *.xlsx *.csv *.txt *.mp4 *.mov *.avi);;"
                "Bilder (*.jpg *.jpeg *.png *.webp *.bmp);;"
                "Dokumente (*.pdf *.doc *.docx *.xls *.xlsx *.csv *.txt);;"
                "Videos (*.mp4 *.mov *.avi);;"
                "Alle Dateien (*.*)"
            ),
        )

        if path:
            self.selected_file = path
            self.file_edit.setText(path)

            if not self.title_edit.text().strip():
                from pathlib import Path
                self.title_edit.setText(Path(path).stem)

    def accept(self):
        title = self.title_edit.text().strip()

        if not title:
            QMessageBox.warning(
                self,
                "Fehlende Angabe",
                "Bitte einen Titel eingeben.",
            )
            return

        if self.media_id is None and not self.selected_file:
            QMessageBox.warning(
                self,
                "Datei fehlt",
                "Bitte eine Bild- oder Dokumentdatei auswählen.",
            )
            return

        if self.media_id is None:
            self.database.add_media_item(
                self.session_id,
                title,
                self.selected_file,
                self.media_type.currentText(),
                self.notes.toPlainText().strip(),
            )
        else:
            self.database.update_media_item(
                self.media_id,
                title,
                self.media_type.currentText(),
                self.notes.toPlainText().strip(),
            )

        super().accept()
