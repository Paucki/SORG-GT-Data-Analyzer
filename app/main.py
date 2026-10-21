from __future__ import annotations

import sys
import webbrowser
import csv
import os
import shutil
import subprocess
import json
import hashlib
import base64
from pathlib import Path
from urllib.parse import quote

from PySide6.QtCore import Qt, QUrl, QSize, QTimer, QEventLoop, QPointF, QRectF
from PySide6.QtGui import (
    QAction,
    QFont,
    QDesktopServices,
    QPixmap,
    QIcon,
    QPainter,
    QPainterPath,
    QColor,
    QPen,
    QBrush,
)
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QGridLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QLineEdit,
    QInputDialog,
    QComboBox,
    QCheckBox,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QSplitter,
    QScrollArea,
    QSizePolicy,
    QWidget,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QFileDialog,
    QTabWidget,
)

from database import Database
from report_generator import MotorsportReport
from updater_client import LoginDialog, UpdateClient, UserSession, UserAdminDialog
from cloud_sync import CloudSync
from version import APP_VERSION
from dialogs import (
    CarDialog,
    DriverDialog,
    EventDialog,
    SessionDialog,
    TrackDialog,
    TyreMeasurementDialog,
    TyreSetDialog,
    SetupEntryDialog,
    SessionChangeDialog,
    MediaDialog,
)


APP_NAME = "SORG GT Data Analyzer"
NORDSCHLEIFE_TRACK_B64 = "iVBORw0KGgoAAAANSUhEUgAAAMwAAADACAAAAABti9NVAAAFHklEQVR4Ad3BC3Ybh4JEMdz9L7qGkvM8ia1Ps0WRPALyg+QHyQ+S7zbkLvLNJpN7yLcaYbmHfKMhF8s95FvML3m13ENuby7y/yb3kFsb8h+Te8itTf4wuYecN/nL5E+Te8hZ8yJ/mPxpcg85acLIv438ZbmHnLS8GLmYiwz5y/IVyyE5Z/LLNP+Sv01Om1/ymZwz+ceQV3ORv0zOmjAX+VjOmfxj5LfJ3yYnTV6NfCinTN4x+dvknOV/Jh/JCSNXGjlj+W3kfbnakKuNnDD5bch7crXJKUMOGfll8m+Td+Rak7PmX/Km+UdeTP5r8rZcbfJl8yp/mBcxuZj8YfK2XG9yE0P+bfJq8mLyp+VtOWEucguT30ZeTS5G/rK8LedMbmLyj5EXI3ORNyxvy0mTmxh5MXk1v+RNk7flrOVG5pe8mFd5z+RtOWu5mSG/LJP3Le/IWcu3GPKB5R05a/kWQz4weVtOmjzIkDfkpOVxJm/IOZMHmvwtp0weafK3nDF5qMnfcsLksSZ/y/UmDzNheUOuNnmY+SVvyLUmDzN5X640eZzJ+3KVkceZfCDXmDzQ5CO5xuSBJh/JNSaPM/lQrrI8zuRDucbkcSYfyhUmDzT5UK6wPNLkQ7nC8kiTD+UKyyNNPpQrLI80+VCOmzzS5EM5bvJIy8dy3PJAIx/LYZNHmYt8IoctjzLyuRw1eZDJETlo8iCTQ3LM5FEmh+SQyaNMjskRk4dZDsrnRh5mclA+NfIwk6PymcnjjByVj408zshh+ciQx5lcIe8bckcjvw25Rt4z5J7mRV7MRa6T9yx3NWL+J1fLe5Z7mrwackreM3I/k6/K+0buZvJF+cjIvYx8ST40uZu5yHn52OSORk7LJyb3NDkrn5jc1eSkfGZyT5OT8pnJXS0n5VOTe1pOyqcmdzQ5KZ+b3M3krHxuci8jZ+WA5U4m5+WAyT2MfEGOWL7fyJfkiOXbTb4oR0y+18hX5YjJdxr5uhwx+T4jt5BDlm8zchM5ZPkmIzeSQ5bvMXIrOWT5DiO3k0OW2xu5pRyy3NzITeWIyY2N3FiOmNzWyK3liOWmRm4vB0xuafIdcsDkdka+RQ5YbmIy8k1ywHIT0+Tb5IDlNka+Tw5YbmEu8n1ywOTrRpPvkyMmXzTyzXLI5CtGvl0OmXzByPfLMZOzRu4hB03OGbmLHDU5Y3InOWxyvcm95LjJtSZ3kyuMXGVyP7nK5ArTcje5zuSwyT3lSpOjlrvKtSbHTO4q15p8YC2vJveVq82LvG1NXix3listhrxtLS8md5YrzUUmf5nMRUzuLdeaFpM/DK21TO4uZ03+Y5oXMbm/nDX5j8mLxeT+ctr8IxcjhoY8QM6bXMwvGZqLPEJuYGj+kUfJrYyMPExuZGTkcfJ18yojD5QvmVd5MfJI+YqR30YeKV8w+W1e5IFy3uS3IcsD5bTJb3PR5IFy1uT/jYY8UE6aMHIxcrE8UM6ZzKsYuZg8UE6ZmLCMPIGcspgwjTyDnDIxskaeQs4ZMa/yHHLWZC7yLHLatDyTnLYszyRnTZNnkrOmyTPJWcvyVHLSNHkqOWmaPJWctCzPJScty3PJOdPIU8k5kyFPJOdMGHkeOWm5mDyPnLQYeSI5ZzLyTHLKNPJccsY08mRywlzk6eR6c5Hnk6tNkyeUq02TJ5SrDXlG+UHyg+QHyQ+SHyQ/SH6Q/CD5QfKD5AfJD5IfJD9IfpD8IPlB8oPkB8kPkh8kP0h+kP8Ds5ew0KaKRtYAAAAASUVORK5CYII="
APP_DATA_FOLDER = Path(
    os.environ.get(
        "LOCALAPPDATA",
        Path.home() / "AppData" / "Local",
    )
 ) / "SORG Rennsport" / "GT Data Analyzer"

EXPERT_AUTH_FILE = APP_DATA_FOLDER / "expert_auth.json"

def _expert_password_hash(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000).hex()

def resource_path(filename: str) -> Path:
    """
    Liefert im Python-Projekt und in der PyInstaller-EXE
    denselben gültigen Pfad zu eingebetteten Dateien.
    """
    base = Path(
        getattr(
            sys,
            "_MEIPASS",
            Path(__file__).resolve().parent,
        )
    )
    return base / filename


def writable_database_path() -> Path:
    """
    Die installierte EXE kann unter Program Files liegen.
    Daher wird die Datenbank in LocalAppData gespeichert.
    Beim ersten Start wird die mitgelieferte Datenbank kopiert.
    """
    APP_DATA_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = APP_DATA_FOLDER / "sorg_gt_v2.db"

    if not target.exists():
        bundled = resource_path("sorg_gt_v2.db")

        if bundled.exists():
            shutil.copy2(bundled, target)

    return target



WHEEL_NAMES = {
    "FL": "Vorne links",
    "FR": "Vorne rechts",
    "RL": "Hinten links",
    "RR": "Hinten rechts",
}


def driver_name(row) -> str:
    first = row["driver_first_name"] or ""
    last = row["driver_last_name"] or ""
    nickname = row["driver_nickname"] or ""
    name = f"{first} {last}".strip()

    if nickname:
        return f'{name} "{nickname}"'.strip()

    return name or "Ohne Fahrer"


class ZoomableImageView(QGraphicsView):
    """
    Bildansicht mit:
    - Mausrad zum Zoomen
    - gedrückter linker Maustaste zum Verschieben
    - Doppelklick zum Zurücksetzen
    - Zoom-Schaltflächen über zoom_in/zoom_out/reset_zoom
    """

    MIN_SCALE = 0.10
    MAX_SCALE = 12.0
    ZOOM_FACTOR = 1.20

    def __init__(self, parent=None):
        super().__init__(parent)

        self._scene = QGraphicsScene(self)
        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)
        self.setScene(self._scene)

        self._has_image = False
        self._user_zoomed = False

        self.setRenderHints(
            QPainter.Antialiasing
            | QPainter.SmoothPixmapTransform
        )
        self.setTransformationAnchor(
            QGraphicsView.AnchorUnderMouse
        )
        self.setResizeAnchor(
            QGraphicsView.AnchorViewCenter
        )
        self.setDragMode(
            QGraphicsView.ScrollHandDrag
        )
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.setFrameShape(QFrame.NoFrame)
        self.setBackgroundBrush(Qt.black)
        self.setToolTip(
            "Mausrad: zoomen · Ziehen: Bild verschieben · "
            "Doppelklick: Ansicht zurücksetzen"
        )

    def setPixmap(self, pixmap: QPixmap) -> None:
        """Kompatibel zur bisherigen QLabel-Verwendung."""
        if pixmap is None or pixmap.isNull():
            self.clear_image()
            return

        self._pixmap_item.setPixmap(pixmap)
        self._scene.setSceneRect(
            self._pixmap_item.boundingRect()
        )
        self._has_image = True
        self._user_zoomed = False
        self.reset_zoom()

    def clear_image(self) -> None:
        self._pixmap_item.setPixmap(QPixmap())
        self._scene.setSceneRect(0, 0, 1, 1)
        self._has_image = False
        self._user_zoomed = False
        self.resetTransform()

    def reset_zoom(self) -> None:
        if not self._has_image:
            return

        self.resetTransform()
        self.fitInView(
            self._pixmap_item,
            Qt.KeepAspectRatio,
        )
        self.centerOn(self._pixmap_item)
        self._user_zoomed = False

    def zoom_in(self) -> None:
        self._apply_zoom(self.ZOOM_FACTOR)

    def zoom_out(self) -> None:
        self._apply_zoom(1.0 / self.ZOOM_FACTOR)

    def _current_scale(self) -> float:
        return float(self.transform().m11())

    def _apply_zoom(self, factor: float) -> None:
        if not self._has_image:
            return

        current = self._current_scale()
        target = current * factor

        if target < self.MIN_SCALE:
            factor = self.MIN_SCALE / current
        elif target > self.MAX_SCALE:
            factor = self.MAX_SCALE / current

        self.scale(factor, factor)
        self._user_zoomed = True

    def wheelEvent(self, event) -> None:
        if not self._has_image:
            super().wheelEvent(event)
            return

        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

        event.accept()

    def mouseDoubleClickEvent(self, event) -> None:
        self.reset_zoom()
        event.accept()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

        # Bei einer vom Benutzer gezoomten Ansicht nicht automatisch
        # zurückspringen. Nur die Standardansicht passt sich dem Fenster an.
        if self._has_image and not self._user_zoomed:
            self.reset_zoom()



class DashboardPage(QWidget):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.layout = QVBoxLayout(self)

        title = QLabel("Dashboard")
        title.setObjectName("pageTitle")
        self.layout.addWidget(title)

        hero = QFrame()
        hero.setObjectName("heroPanel")
        hero.setMinimumHeight(205)
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(28, 28, 28, 24)

        hero_background = resource_path("motorsport_hero.jpg")

        if hero_background.exists():
            hero.setStyleSheet(
                """
                QFrame#heroPanel {
                    border-image: url("""
                + str(hero_background).replace("\\", "/")
                + """) 0 0 0 0 stretch stretch;
                    border-radius: 16px;
                    border: 1px solid #475569;
                }
                """
            )

        # Kompakte Glass-Box links unten:
        # Der Text liegt nicht mehr über der hellen Fahrzeugfront
        # und bleibt auch bei kleineren Fenstern vollständig lesbar.
        hero_text_panel = QFrame()
        hero_text_panel.setObjectName("heroTextPanel")
        hero_text_panel.setMaximumWidth(760)

        hero_text_layout = QVBoxLayout(hero_text_panel)
        hero_text_layout.setContentsMargins(18, 12, 18, 12)
        hero_text_layout.setSpacing(3)

        hero_title = QLabel("SORG RENNSPORT")
        hero_title.setObjectName("heroTitle")
        hero_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hero_title.setWordWrap(False)

        hero_accent = QFrame()
        hero_accent.setObjectName("heroAccent")
        hero_accent.setFixedHeight(4)
        hero_accent.setMaximumWidth(330)

        hero_subtitle = QLabel(
            "GT Data Analyzer · Motorsport Engineering"
        )
        hero_subtitle.setObjectName("heroSubtitle")
        hero_subtitle.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hero_subtitle.setWordWrap(True)

        hero_text_layout.addWidget(hero_title)
        hero_text_layout.addWidget(hero_accent)
        hero_text_layout.addWidget(hero_subtitle)

        hero_layout.addStretch()
        hero_layout.addWidget(
            hero_text_panel,
            0,
            Qt.AlignLeft | Qt.AlignBottom,
        )
        self.layout.addWidget(hero)

        self.cards_widget = QWidget()
        self.cards_layout = QGridLayout(self.cards_widget)
        self.cards_layout.setSpacing(14)
        self.layout.addWidget(self.cards_widget)
        self.layout.addStretch()
        self.refresh()

    def refresh(self) -> None:
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        stats = self.database.statistics()
        entries = (
            ("Rennevents", stats["events"]),
            ("Sessions", stats["sessions"]),
            ("Reifensätze", stats["tyre_sets"]),
            ("Fahrzeuge", stats["cars"]),
            ("Fahrer", stats["drivers"]),
            ("Strecken", stats["tracks"]),
            ("Setup-Einträge", stats["session_setup_entries"]),
        )

        icons = {
            "Rennevents": "🏁",
            "Sessions": "📅",
            "Reifensätze": "🛞",
            "Fahrzeuge": "🏎",
            "Fahrer": "👤",
            "Strecken": "📍",
            "Setup-Einträge": "⚙",
        }

        for index, (title, value) in enumerate(entries):
            card = QFrame()
            card.setObjectName("dashboardCard")
            card_layout = QVBoxLayout(card)

            icon_label = QLabel(icons.get(title, "•"))
            icon_label.setObjectName("dashboardIcon")
            icon_label.setAlignment(Qt.AlignCenter)

            value_label = QLabel(str(value))
            value_label.setObjectName("dashboardValue")
            value_label.setAlignment(Qt.AlignCenter)

            title_label = QLabel(title)
            title_label.setObjectName("dashboardLabel")
            title_label.setAlignment(Qt.AlignCenter)

            card_layout.addWidget(icon_label)
            card_layout.addWidget(value_label)
            card_layout.addWidget(title_label)

            row = index // 4
            column = index % 4
            self.cards_layout.addWidget(card, row, column)


class CrudTablePage(QWidget):
    def __init__(
        self,
        title: str,
        columns: tuple[str, ...],
        loader,
        add_callback,
        edit_callback,
        delete_callback,
    ) -> None:
        super().__init__()
        self.loader = loader
        self.columns = columns
        self.add_callback = add_callback
        self.edit_callback = edit_callback
        self.delete_callback = delete_callback

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        header.addWidget(heading)
        header.addStretch()

        add_button = QPushButton("+ Neu")
        add_button.clicked.connect(self.add_callback)
        header.addWidget(add_button)

        edit_button = QPushButton("Bearbeiten")
        edit_button.clicked.connect(self.edit_selected)
        header.addWidget(edit_button)

        delete_button = QPushButton("Löschen")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self.delete_selected)
        header.addWidget(delete_button)

        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(list(columns))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.doubleClicked.connect(self.edit_selected)
        layout.addWidget(self.table)

    def refresh(self) -> None:
        rows = list(self.loader())
        self.table.setRowCount(len(rows))

        for row_index, (row_id, values) in enumerate(rows):
            for column_index, value in enumerate(values):
                item = QTableWidgetItem("" if value is None else str(value))
                if column_index == 0:
                    item.setData(Qt.UserRole, row_id)
                self.table.setItem(row_index, column_index, item)

    def selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return int(item.data(Qt.UserRole)) if item else None

    def edit_selected(self) -> None:
        row_id = self.selected_id()
        if row_id is None:
            QMessageBox.information(self, "Auswahl fehlt", "Bitte Zeile auswählen.")
            return
        self.edit_callback(row_id)

    def delete_selected(self) -> None:
        row_id = self.selected_id()
        if row_id is None:
            QMessageBox.information(self, "Auswahl fehlt", "Bitte Zeile auswählen.")
            return
        self.delete_callback(row_id)



class EventCard(QFrame):
    def __init__(self, event, sessions, image_path, selected=False, parent=None):
        super().__init__(parent)
        self.event_id = int(event["id"])
        self.setObjectName("eventCardSelected" if selected else "eventCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(172)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)

        title = QLabel(event["name"])
        title.setObjectName("eventCardTitle")

        track = QLabel(f'📍 {event["track_name"]}')
        date = QLabel(
            f'📅 {event["start_date"]}'
            + (
                f' – {event["end_date"]}'
                if event["end_date"] and event["end_date"] != event["start_date"]
                else ""
            )
        )

        driver_text = "Ohne Fahrer"
        car_text = "Ohne Fahrzeug"
        if sessions:
            driver_text = driver_name(sessions[0])
            car_text = (
                f'{sessions[0]["manufacturer"]} '
                f'{sessions[0]["model"]}'
            )

        driver = QLabel(f"👤 {driver_text}")
        car = QLabel(f"🏎 {car_text}")

        for label in (track, date, driver, car):
            label.setObjectName("eventMeta")

        badges = QHBoxLayout()
        badges.setSpacing(5)
        for session in sessions[:5]:
            badge = QLabel(session["session_type"])
            badge.setObjectName("sessionBadge")
            badges.addWidget(badge)
        badges.addStretch()

        text_layout.addWidget(title)
        text_layout.addWidget(track)
        text_layout.addWidget(date)
        text_layout.addWidget(driver)
        text_layout.addWidget(car)
        text_layout.addLayout(badges)
        layout.addLayout(text_layout, 1)

        preview = QLabel()
        preview.setObjectName("eventThumb")
        preview.setFixedSize(122, 142)
        preview.setAlignment(Qt.AlignCenter)

        if image_path and Path(image_path).exists():
            pixmap = QPixmap(str(image_path))
        else:
            pixmap = QPixmap(
                str(resource_path("motorsport_preview.jpg"))
            )

        if not pixmap.isNull():
            preview.setPixmap(
                pixmap.scaled(
                    preview.size(),
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation,
                )
            )

        layout.addWidget(preview)


class TyreAnalysisPage(QWidget):
    POSITION_NAMES = {
        "FL": "Vorne links",
        "FR": "Vorne rechts",
        "RL": "Hinten links",
        "RR": "Hinten rechts",
    }

    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()

        title_box = QVBoxLayout()
        title = QLabel("Reifenanalyse")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Historische Drücke vergleichen und KI-Datengrundlage prüfen"
        )
        subtitle.setObjectName("analysisSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header.addLayout(title_box)
        header.addStretch()

        self.car_filter = QComboBox()
        self.car_filter.setMinimumWidth(190)
        self.car_filter.currentIndexChanged.connect(
            self.refresh
        )

        self.track_filter = QComboBox()
        self.track_filter.setMinimumWidth(180)
        self.track_filter.currentIndexChanged.connect(
            self.refresh
        )

        self.position_filter = QComboBox()
        self.position_filter.addItem(
            "Alle Reifenpositionen",
            None,
        )
        for code, name in self.POSITION_NAMES.items():
            self.position_filter.addItem(name, code)
        self.position_filter.currentIndexChanged.connect(
            self.refresh
        )

        header.addWidget(QLabel("Fahrzeug"))
        header.addWidget(self.car_filter)
        header.addWidget(QLabel("Strecke"))
        header.addWidget(self.track_filter)
        header.addWidget(QLabel("Position"))
        header.addWidget(self.position_filter)

        layout.addLayout(header)

        self.summary_widget = QWidget()
        self.summary_layout = QGridLayout(
            self.summary_widget
        )
        self.summary_layout.setSpacing(10)
        layout.addWidget(self.summary_widget)

        recommendation = QFrame()
        recommendation.setObjectName(
            "analysisRecommendation"
        )
        recommendation_layout = QVBoxLayout(
            recommendation
        )

        recommendation_title = QLabel(
            "DATENBANK-EMPFEHLUNG"
        )
        recommendation_title.setObjectName(
            "analysisCardLabel"
        )

        self.recommendation_value = QLabel("-")
        self.recommendation_value.setObjectName(
            "analysisRecommendationValue"
        )

        self.recommendation_text = QLabel(
            "Noch keine ausreichenden Vergleichsdaten."
        )
        self.recommendation_text.setWordWrap(True)
        self.recommendation_text.setObjectName(
            "analysisRecommendationText"
        )

        recommendation_layout.addWidget(
            recommendation_title
        )
        recommendation_layout.addWidget(
            self.recommendation_value
        )
        recommendation_layout.addWidget(
            self.recommendation_text
        )
        layout.addWidget(recommendation)

        self.table = QTableWidget()
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels(
            [
                "Datum",
                "Event",
                "Strecke",
                "Fahrzeug",
                "Session",
                "Position",
                "Reifen",
                "Empfohlen",
                "Gefahren",
                "Differenz",
                "Heiß",
                "Ziel",
                "Temp. Mitte",
                "Verschleiß",
            ]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.table.horizontalHeader().setStretchLastSection(
            True
        )
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)

        self.populate_filters()
        self.refresh()

    def populate_filters(self) -> None:
        current_car = self.car_filter.currentData()
        current_track = self.track_filter.currentData()

        for combo in (
            self.car_filter,
            self.track_filter,
        ):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Alle", None)

        for row in self.database.get_cars():
            self.car_filter.addItem(
                f'{row["manufacturer"]} {row["model"]}',
                row["id"],
            )

        for row in self.database.get_tracks():
            self.track_filter.addItem(
                row["name"],
                row["id"],
            )

        def restore(combo, value):
            index = combo.findData(value)
            combo.setCurrentIndex(
                index if index >= 0 else 0
            )

        restore(self.car_filter, current_car)
        restore(self.track_filter, current_track)

        for combo in (
            self.car_filter,
            self.track_filter,
        ):
            combo.blockSignals(False)

    @staticmethod
    def fmt(
        value,
        decimals: int = 2,
        suffix: str = "",
        signed: bool = False,
    ) -> str:
        if value is None:
            return "-"

        number = float(value)
        format_string = (
            f"{{:{'+' if signed else ''}.{decimals}f}}"
        )
        return format_string.format(number) + suffix

    def clear_summary(self) -> None:
        while self.summary_layout.count():
            item = self.summary_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def add_summary_card(
        self,
        index: int,
        title: str,
        value: str,
        detail: str = "",
    ) -> None:
        card = QFrame()
        card.setObjectName("analysisCard")
        card_layout = QVBoxLayout(card)

        label = QLabel(title)
        label.setObjectName("analysisCardLabel")

        value_label = QLabel(value)
        value_label.setObjectName("analysisCardValue")

        detail_label = QLabel(detail)
        detail_label.setObjectName(
            "analysisCardDetail"
        )
        detail_label.setWordWrap(True)

        card_layout.addWidget(label)
        card_layout.addWidget(value_label)
        card_layout.addWidget(detail_label)

        self.summary_layout.addWidget(
            card,
            index // 4,
            index % 4,
        )

    def refresh(self) -> None:
        self.populate_filters()

        car_id = self.car_filter.currentData()
        track_id = self.track_filter.currentData()
        position = self.position_filter.currentData()

        rows = self.database.get_pressure_analysis_rows(
            car_id=car_id,
            track_id=track_id,
            position=position,
        )
        summary = (
            self.database.get_pressure_analysis_summary(
                car_id=car_id,
                track_id=track_id,
                position=position,
            )
        )

        self.clear_summary()

        cards = (
            (
                "DATENSÄTZE",
                str(summary["samples"]),
                "Verwertbare Reifenmessungen",
            ),
            (
                "Ø EMPFOHLEN",
                self.fmt(
                    summary["avg_recommended"],
                    3,
                    " bar",
                ),
                "Physik- und Datenbankmodell",
            ),
            (
                "Ø GEFAHREN",
                self.fmt(
                    summary["avg_driven"],
                    3,
                    " bar",
                ),
                "Tatsächlich verwendeter Kaltdruck",
            ),
            (
                "Ø ABWEICHUNG",
                self.fmt(
                    summary["avg_difference"],
                    3,
                    " bar",
                    signed=True,
                ),
                "Gefahren minus empfohlen",
            ),
            (
                "Ø HEISSDRUCK",
                self.fmt(
                    summary["avg_hot"],
                    3,
                    " bar",
                ),
                "Nach der Session gemessen",
            ),
            (
                "Ø HEISS-FEHLER",
                self.fmt(
                    summary["avg_hot_error"],
                    3,
                    " bar",
                    signed=True,
                ),
                "Heißdruck minus Ziel",
            ),
            (
                "Ø TEMP. MITTE",
                self.fmt(
                    summary["avg_middle_temp"],
                    1,
                    " °C",
                ),
                "Laufflächenmitte",
            ),
            (
                "VERTRAUEN",
                (
                    f'{summary["confidence_percent"]} %'
                ),
                "Datenmenge und Zielgenauigkeit",
            ),
        )

        for index, card in enumerate(cards):
            self.add_summary_card(index, *card)

        samples = int(summary["samples"])
        avg_driven = summary["avg_driven"]
        avg_hot_error = summary["avg_hot_error"]
        confidence = int(
            summary["confidence_percent"]
        )

        if samples == 0 or avg_driven is None:
            self.recommendation_value.setText("-")
            self.recommendation_text.setText(
                "Noch keine passenden Datensätze vorhanden. "
                "Fahre und speichere weitere Reifensätze."
            )
        else:
            self.recommendation_value.setText(
                self.fmt(avg_driven, 3, " bar")
            )

            if samples < 5:
                quality = "erste Tendenz"
            elif confidence < 70:
                quality = "mittlere Datenbasis"
            else:
                quality = "starke Datenbasis"

            correction_text = self.fmt(
                avg_hot_error,
                3,
                " bar",
                signed=True,
            )

            self.recommendation_text.setText(
                f"Für den gewählten Vergleich liegt der bisher "
                f"tatsächlich gefahrene Kaltdruck im Mittel bei "
                f"{self.fmt(avg_driven, 3, ' bar')}. "
                f"Die durchschnittliche Abweichung vom Ziel-Heißdruck "
                f"beträgt {correction_text}. "
                f"Bewertung: {quality}, Vertrauen {confidence} %. "
                f"Diese Auswertung ist die Grundlage für das spätere "
                f"KI-Empfehlungsmodell."
            )

        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            driver = (
                f'{row["driver_first_name"] or ""} '
                f'{row["driver_last_name"] or ""}'
            ).strip()

            tyre_name = " ".join(
                value
                for value in (
                    row["tyre_manufacturer"] or "",
                    row["compound"] or "",
                    (
                        f'Satz {row["set_number"]}'
                        if row["set_number"]
                        else ""
                    ),
                )
                if value
            )

            values = (
                row["session_date"],
                row["event_name"],
                row["track_name"],
                (
                    f'{row["car_manufacturer"]} '
                    f'{row["car_model"]}'
                ),
                (
                    f'{row["session_type"]}'
                    + (f" · {driver}" if driver else "")
                ),
                self.POSITION_NAMES.get(
                    row["position"],
                    row["position"],
                ),
                tyre_name,
                self.fmt(
                    row[
                        "recommended_cold_pressure_bar"
                    ],
                    3,
                ),
                self.fmt(
                    row["driven_cold_pressure_bar"],
                    3,
                ),
                self.fmt(
                    row["pressure_difference_bar"],
                    3,
                    signed=True,
                ),
                self.fmt(
                    row["hot_pressure_bar"],
                    3,
                ),
                self.fmt(
                    row["target_pressure_bar"],
                    3,
                ),
                self.fmt(
                    row["temp_middle_c"],
                    1,
                ),
                self.fmt(
                    row["wear_percent"],
                    1,
                ),
            )

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(
                    "" if value is None else str(value)
                )
                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.table.resizeColumnsToContents()



class SessionComparisonPage(QWidget):
    POSITION_NAMES = {
        "FL": "Vorne links",
        "FR": "Vorne rechts",
        "RL": "Hinten links",
        "RR": "Hinten rechts",
    }

    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.session_rows = []

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        header = QHBoxLayout()

        title_box = QVBoxLayout()
        title = QLabel("Sessionvergleich")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Zwei Sessions direkt vergleichen: Wetter, Reifen, Setup und Änderungen"
        )
        subtitle.setObjectName("analysisSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header.addLayout(title_box)
        header.addStretch()

        self.session_a_combo = QComboBox()
        self.session_a_combo.setMinimumWidth(360)
        self.session_a_combo.currentIndexChanged.connect(
            self.refresh_comparison
        )

        self.session_b_combo = QComboBox()
        self.session_b_combo.setMinimumWidth(360)
        self.session_b_combo.currentIndexChanged.connect(
            self.refresh_comparison
        )

        swap_button = QPushButton("⇄ Tauschen")
        swap_button.clicked.connect(self.swap_sessions)

        export_button = QPushButton("CSV exportieren")
        export_button.clicked.connect(self.export_csv)

        header.addWidget(QLabel("Session A"))
        header.addWidget(self.session_a_combo)
        header.addWidget(QLabel("Session B"))
        header.addWidget(self.session_b_combo)
        header.addWidget(swap_button)
        header.addWidget(export_button)

        root.addLayout(header)

        self.overview = QWidget()
        self.overview_layout = QGridLayout(self.overview)
        self.overview_layout.setSpacing(10)
        root.addWidget(self.overview)

        self.recommendation = QFrame()
        self.recommendation.setObjectName(
            "comparisonRecommendation"
        )
        recommendation_layout = QVBoxLayout(
            self.recommendation
        )

        rec_label = QLabel("VERGLEICHSERGEBNIS")
        rec_label.setObjectName("analysisCardLabel")

        self.recommendation_title = QLabel(
            "Bitte zwei Sessions auswählen"
        )
        self.recommendation_title.setObjectName(
            "comparisonRecommendationTitle"
        )

        self.recommendation_text = QLabel("")
        self.recommendation_text.setWordWrap(True)
        self.recommendation_text.setObjectName(
            "analysisRecommendationText"
        )

        recommendation_layout.addWidget(rec_label)
        recommendation_layout.addWidget(
            self.recommendation_title
        )
        recommendation_layout.addWidget(
            self.recommendation_text
        )
        root.addWidget(self.recommendation)

        self.tabs = QTabWidget()

        self.tyre_table = QTableWidget()
        self.tyre_table.setColumnCount(12)
        self.tyre_table.setHorizontalHeaderLabels(
            [
                "Reifensatz",
                "Position",
                "A empfohlen",
                "B empfohlen",
                "Δ empfohlen",
                "A gefahren",
                "B gefahren",
                "Δ gefahren",
                "A heiß",
                "B heiß",
                "A Temp. Mitte",
                "B Temp. Mitte",
            ]
        )
        self.configure_table(self.tyre_table)
        self.tabs.addTab(
            self.tyre_table,
            "Reifen",
        )

        self.setup_table = QTableWidget()
        self.setup_table.setColumnCount(6)
        self.setup_table.setHorizontalHeaderLabels(
            [
                "Kategorie",
                "Parameter",
                "Session A",
                "Session B",
                "Änderung",
                "Einheit",
            ]
        )
        self.configure_table(self.setup_table)
        self.tabs.addTab(
            self.setup_table,
            "Setup",
        )

        changes_widget = QWidget()
        changes_layout = QHBoxLayout(changes_widget)

        self.changes_a = QTreeWidget()
        self.changes_a.setHeaderLabels(
            ("Session A · Änderung", "Beschreibung")
        )
        self.changes_a.header().setStretchLastSection(
            True
        )

        self.changes_b = QTreeWidget()
        self.changes_b.setHeaderLabels(
            ("Session B · Änderung", "Beschreibung")
        )
        self.changes_b.header().setStretchLastSection(
            True
        )

        changes_layout.addWidget(self.changes_a)
        changes_layout.addWidget(self.changes_b)
        self.tabs.addTab(
            changes_widget,
            "Fahrzeugänderungen",
        )

        self.raw_table = QTableWidget()
        self.raw_table.setColumnCount(5)
        self.raw_table.setHorizontalHeaderLabels(
            [
                "Bereich",
                "Wert Session A",
                "Wert Session B",
                "Differenz",
                "Bewertung",
            ]
        )
        self.configure_table(self.raw_table)
        self.tabs.addTab(
            self.raw_table,
            "Sessiondaten",
        )

        root.addWidget(self.tabs, 1)

        self.populate_sessions()
        self.refresh_comparison()

    @staticmethod
    def configure_table(table: QTableWidget) -> None:
        table.setAlternatingRowColors(True)
        table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(
            True
        )

    @staticmethod
    def driver_label(row) -> str:
        first = row["driver_first_name"] or ""
        last = row["driver_last_name"] or ""
        nickname = row["driver_nickname"] or ""
        text = f"{first} {last}".strip()

        if nickname:
            text = f'{text} "{nickname}"'.strip()

        return text or "Ohne Fahrer"

    @staticmethod
    def fmt(
        value,
        decimals: int = 2,
        suffix: str = "",
        signed: bool = False,
    ) -> str:
        if value is None:
            return "-"

        number = float(value)
        format_spec = (
            f"+.{decimals}f"
            if signed
            else f".{decimals}f"
        )
        return format(number, format_spec) + suffix

    def populate_sessions(self) -> None:
        selected_a = self.session_a_combo.currentData()
        selected_b = self.session_b_combo.currentData()

        self.session_rows = list(
            self.database.get_all_sessions_for_comparison()
        )

        for combo in (
            self.session_a_combo,
            self.session_b_combo,
        ):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(
                "Session auswählen ...",
                None,
            )

            for row in self.session_rows:
                label = (
                    f'{row["session_date"]} · '
                    f'{row["event_name"]} · '
                    f'{row["session_type"]} · '
                    f'{row["manufacturer"]} '
                    f'{row["model"]} · '
                    f'{self.driver_label(row)}'
                )
                combo.addItem(label, row["id"])

        def restore(combo, value, fallback):
            index = combo.findData(value)

            if index < 0:
                index = fallback

            combo.setCurrentIndex(
                min(index, combo.count() - 1)
            )

        restore(
            self.session_a_combo,
            selected_a,
            1 if self.session_a_combo.count() > 1 else 0,
        )
        restore(
            self.session_b_combo,
            selected_b,
            2 if self.session_b_combo.count() > 2 else 0,
        )

        for combo in (
            self.session_a_combo,
            self.session_b_combo,
        ):
            combo.blockSignals(False)

    def refresh(self) -> None:
        self.populate_sessions()
        self.refresh_comparison()

    def swap_sessions(self) -> None:
        value_a = self.session_a_combo.currentData()
        value_b = self.session_b_combo.currentData()

        index_a = self.session_a_combo.findData(value_b)
        index_b = self.session_b_combo.findData(value_a)

        self.session_a_combo.blockSignals(True)
        self.session_b_combo.blockSignals(True)

        self.session_a_combo.setCurrentIndex(
            index_a if index_a >= 0 else 0
        )
        self.session_b_combo.setCurrentIndex(
            index_b if index_b >= 0 else 0
        )

        self.session_a_combo.blockSignals(False)
        self.session_b_combo.blockSignals(False)
        self.refresh_comparison()

    def clear_overview(self) -> None:
        while self.overview_layout.count():
            item = self.overview_layout.takeAt(0)
            widget = item.widget()

            if widget:
                widget.deleteLater()

    def add_overview_card(
        self,
        column: int,
        title: str,
        session,
    ) -> None:
        card = QFrame()
        card.setObjectName("comparisonSessionCard")
        layout = QVBoxLayout(card)

        heading = QLabel(title)
        heading.setObjectName("analysisCardLabel")

        name = QLabel(
            f'{session["session_type"]} · '
            f'{session["session_date"]}'
        )
        name.setObjectName("comparisonSessionTitle")

        details = QLabel(
            f'<b>{session["event_name"]}</b><br>'
            f'{session["track_name"]}<br>'
            f'{session["manufacturer"]} '
            f'{session["model"]}<br>'
            f'{driver_name(session)}<br><br>'
            f'Wetter: {session["weather"] or "-"}<br>'
            f'Luft: {float(session["air_temp_c"] or 0):.1f} °C · '
            f'Asphalt: {float(session["track_temp_c"] or 0):.1f} °C · '
            f'Feuchte: {float(session["humidity_percent"] or 0):.1f} %'
        )
        details.setWordWrap(True)

        layout.addWidget(heading)
        layout.addWidget(name)
        layout.addWidget(details)

        self.overview_layout.addWidget(
            card,
            0,
            column,
        )

    def refresh_comparison(self) -> None:
        session_a_id = self.session_a_combo.currentData()
        session_b_id = self.session_b_combo.currentData()

        self.clear_overview()
        self.clear_tables()

        if (
            session_a_id is None
            or session_b_id is None
        ):
            self.recommendation_title.setText(
                "Bitte zwei Sessions auswählen"
            )
            self.recommendation_text.setText(
                "Danach werden Reifen, Setup, Wetter und "
                "Fahrzeugänderungen automatisch verglichen."
            )
            return

        if int(session_a_id) == int(session_b_id):
            self.recommendation_title.setText(
                "Dieselbe Session wurde zweimal ausgewählt"
            )
            self.recommendation_text.setText(
                "Wähle für einen sinnvollen Vergleich "
                "zwei unterschiedliche Sessions."
            )
            return

        try:
            bundle_a = (
                self.database.get_session_comparison_bundle(
                    int(session_a_id)
                )
            )
            bundle_b = (
                self.database.get_session_comparison_bundle(
                    int(session_b_id)
                )
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Vergleich fehlgeschlagen",
                str(error),
            )
            return

        session_a = bundle_a["session"]
        session_b = bundle_b["session"]

        self.add_overview_card(
            0,
            "SESSION A",
            session_a,
        )
        self.add_overview_card(
            1,
            "SESSION B",
            session_b,
        )

        self.fill_tyre_table(
            bundle_a["tyres"],
            bundle_b["tyres"],
        )
        self.fill_setup_table(
            bundle_a["setup"],
            bundle_b["setup"],
        )
        self.fill_changes(
            bundle_a["changes"],
            bundle_b["changes"],
        )
        self.fill_session_data(
            session_a,
            session_b,
        )
        self.build_recommendation(
            bundle_a,
            bundle_b,
        )

    def clear_tables(self) -> None:
        self.tyre_table.setRowCount(0)
        self.setup_table.setRowCount(0)
        self.raw_table.setRowCount(0)
        self.changes_a.clear()
        self.changes_b.clear()

    @staticmethod
    def tyre_key(row) -> tuple:
        return (
            str(row["set_number"] or row["tyre_set_id"]),
            str(row["position"]),
        )

    def fill_tyre_table(
        self,
        rows_a,
        rows_b,
    ) -> None:
        map_a = {
            self.tyre_key(row): row
            for row in rows_a
        }
        map_b = {
            self.tyre_key(row): row
            for row in rows_b
        }

        keys = sorted(
            set(map_a) | set(map_b),
            key=lambda key: (
                key[0],
                ("FL", "FR", "RL", "RR").index(key[1])
                if key[1] in ("FL", "FR", "RL", "RR")
                else 9,
            ),
        )

        self.tyre_table.setRowCount(len(keys))

        for row_index, key in enumerate(keys):
            a = map_a.get(key)
            b = map_b.get(key)

            def get(row, column):
                return None if row is None else row[column]

            recommended_a = get(
                a,
                "cold_pressure_bar",
            )
            recommended_b = get(
                b,
                "cold_pressure_bar",
            )
            driven_a = get(
                a,
                "driven_cold_pressure_bar",
            )
            driven_b = get(
                b,
                "driven_cold_pressure_bar",
            )

            values = (
                f"Satz {key[0]}",
                self.POSITION_NAMES.get(
                    key[1],
                    key[1],
                ),
                self.fmt(recommended_a, 3),
                self.fmt(recommended_b, 3),
                self.delta_text(
                    recommended_a,
                    recommended_b,
                    3,
                ),
                self.fmt(driven_a, 3),
                self.fmt(driven_b, 3),
                self.delta_text(
                    driven_a,
                    driven_b,
                    3,
                ),
                self.fmt(
                    get(a, "hot_pressure_bar"),
                    3,
                ),
                self.fmt(
                    get(b, "hot_pressure_bar"),
                    3,
                ),
                self.fmt(
                    get(a, "temp_middle_c"),
                    1,
                ),
                self.fmt(
                    get(b, "temp_middle_c"),
                    1,
                ),
            )

            for column, value in enumerate(values):
                self.tyre_table.setItem(
                    row_index,
                    column,
                    QTableWidgetItem(str(value)),
                )

        self.tyre_table.resizeColumnsToContents()

    @staticmethod
    def setup_key(row) -> tuple[str, str]:
        return (
            str(row["category"] or ""),
            str(row["parameter_name"] or ""),
        )

    def fill_setup_table(
        self,
        rows_a,
        rows_b,
    ) -> None:
        map_a = {
            self.setup_key(row): row
            for row in rows_a
        }
        map_b = {
            self.setup_key(row): row
            for row in rows_b
        }

        keys = sorted(set(map_a) | set(map_b))
        self.setup_table.setRowCount(len(keys))

        for row_index, key in enumerate(keys):
            a = map_a.get(key)
            b = map_b.get(key)

            value_a = (
                a["new_value"]
                if a is not None
                else "-"
            )
            value_b = (
                b["new_value"]
                if b is not None
                else "-"
            )
            unit = (
                (b["unit"] if b is not None else "")
                or (a["unit"] if a is not None else "")
            )

            if value_a == value_b:
                change = "gleich"
            elif value_a == "-":
                change = "nur Session B"
            elif value_b == "-":
                change = "nur Session A"
            else:
                change = f"{value_a} → {value_b}"

            values = (
                key[0],
                key[1],
                value_a,
                value_b,
                change,
                unit,
            )

            for column, value in enumerate(values):
                self.setup_table.setItem(
                    row_index,
                    column,
                    QTableWidgetItem(str(value)),
                )

        self.setup_table.resizeColumnsToContents()

    def fill_changes(
        self,
        changes_a,
        changes_b,
    ) -> None:
        for change in changes_a:
            self.changes_a.addTopLevelItem(
                QTreeWidgetItem(
                    (
                        f'{change["category"]} · '
                        f'{change["title"]}',
                        change["description"] or "",
                    )
                )
            )

        for change in changes_b:
            self.changes_b.addTopLevelItem(
                QTreeWidgetItem(
                    (
                        f'{change["category"]} · '
                        f'{change["title"]}',
                        change["description"] or "",
                    )
                )
            )

    def fill_session_data(
        self,
        session_a,
        session_b,
    ) -> None:
        rows = (
            (
                "Lufttemperatur",
                session_a["air_temp_c"],
                session_b["air_temp_c"],
                "°C",
            ),
            (
                "Asphalttemperatur",
                session_a["track_temp_c"],
                session_b["track_temp_c"],
                "°C",
            ),
            (
                "Felgentemperatur",
                session_a["rim_temp_c"],
                session_b["rim_temp_c"],
                "°C",
            ),
            (
                "Luftfeuchtigkeit",
                session_a["humidity_percent"],
                session_b["humidity_percent"],
                "%",
            ),
        )

        self.raw_table.setRowCount(len(rows))

        for index, (
            label,
            value_a,
            value_b,
            unit,
        ) in enumerate(rows):
            difference = (
                None
                if value_a is None or value_b is None
                else float(value_b) - float(value_a)
            )

            if difference is None:
                rating = "keine Bewertung"
            elif abs(difference) < 0.5:
                rating = "nahezu gleich"
            elif difference > 0:
                rating = "Session B höher"
            else:
                rating = "Session B niedriger"

            values = (
                label,
                self.fmt(value_a, 1, f" {unit}"),
                self.fmt(value_b, 1, f" {unit}"),
                self.fmt(
                    difference,
                    1,
                    f" {unit}",
                    signed=True,
                ),
                rating,
            )

            for column, value in enumerate(values):
                self.raw_table.setItem(
                    index,
                    column,
                    QTableWidgetItem(str(value)),
                )

        self.raw_table.resizeColumnsToContents()

    @staticmethod
    def delta_value(value_a, value_b):
        if value_a is None or value_b is None:
            return None

        return float(value_b) - float(value_a)

    def delta_text(
        self,
        value_a,
        value_b,
        decimals: int,
    ) -> str:
        return self.fmt(
            self.delta_value(value_a, value_b),
            decimals,
            signed=True,
        )

    def build_recommendation(
        self,
        bundle_a,
        bundle_b,
    ) -> None:
        tyres_a = bundle_a["tyres"]
        tyres_b = bundle_b["tyres"]

        def average(rows, field):
            values = [
                float(row[field])
                for row in rows
                if row[field] is not None
            ]
            return (
                sum(values) / len(values)
                if values
                else None
            )

        hot_a = average(
            tyres_a,
            "hot_pressure_bar",
        )
        hot_b = average(
            tyres_b,
            "hot_pressure_bar",
        )
        target_a = average(
            tyres_a,
            "target_pressure_bar",
        )
        target_b = average(
            tyres_b,
            "target_pressure_bar",
        )
        driven_a = average(
            tyres_a,
            "driven_cold_pressure_bar",
        )
        driven_b = average(
            tyres_b,
            "driven_cold_pressure_bar",
        )

        error_a = (
            None
            if hot_a is None or target_a is None
            else abs(hot_a - target_a)
        )
        error_b = (
            None
            if hot_b is None or target_b is None
            else abs(hot_b - target_b)
        )

        if error_a is None and error_b is None:
            winner = "Noch keine klare Reifenbewertung"
            reason = (
                "Für mindestens eine Session fehlen "
                "Heißdruck- oder Zieldruckwerte."
            )
        elif error_b is None or (
            error_a is not None
            and error_a < error_b
        ):
            winner = "Session A liegt näher am Ziel-Heißdruck"
            reason = (
                f"Mittlere absolute Abweichung A: "
                f"{self.fmt(error_a, 3, ' bar')} · "
                f"B: {self.fmt(error_b, 3, ' bar')}."
            )
        elif error_a is None or error_b < error_a:
            winner = "Session B liegt näher am Ziel-Heißdruck"
            reason = (
                f"Mittlere absolute Abweichung A: "
                f"{self.fmt(error_a, 3, ' bar')} · "
                f"B: {self.fmt(error_b, 3, ' bar')}."
            )
        else:
            winner = "Beide Sessions sind beim Heißdruck gleichwertig"
            reason = (
                f"Beide liegen im Mittel etwa "
                f"{self.fmt(error_a, 3, ' bar')} "
                f"vom Ziel entfernt."
            )

        setup_a = {
            self.setup_key(row)
            for row in bundle_a["setup"]
        }
        setup_b = {
            self.setup_key(row)
            for row in bundle_b["setup"]
        }
        setup_changes = len(
            setup_a.symmetric_difference(setup_b)
        )

        self.recommendation_title.setText(winner)
        self.recommendation_text.setText(
            reason
            + " "
            + (
                f"Der mittlere gefahrene Kaltdruck änderte sich "
                f"von {self.fmt(driven_a, 3, ' bar')} auf "
                f"{self.fmt(driven_b, 3, ' bar')}. "
            )
            + (
                f"Im Setupvergleich wurden {setup_changes} "
                f"unterschiedliche oder nur einseitig vorhandene "
                f"Parameter erkannt. "
            )
            + (
                "Diese Vergleichsansicht liefert später die "
                "Merkmale für eine KI-gestützte Setup-Empfehlung."
            )
        )

    def export_csv(self) -> None:
        if self.session_a_combo.currentData() is None:
            QMessageBox.information(
                self,
                "Keine Vergleichsdaten",
                "Bitte zuerst zwei Sessions auswählen.",
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Sessionvergleich exportieren",
            "sessionvergleich.csv",
            "CSV-Dateien (*.csv)",
        )

        if not path:
            return

        if not path.lower().endswith(".csv"):
            path += ".csv"

        try:
            with open(
                path,
                "w",
                newline="",
                encoding="utf-8-sig",
            ) as handle:
                writer = csv.writer(
                    handle,
                    delimiter=";",
                )

                writer.writerow(
                    [
                        "SORG RENNSPORT",
                        "Sessionvergleich",
                    ]
                )
                writer.writerow(
                    [
                        "Session A",
                        self.session_a_combo.currentText(),
                    ]
                )
                writer.writerow(
                    [
                        "Session B",
                        self.session_b_combo.currentText(),
                    ]
                )
                writer.writerow([])

                self.write_table_to_csv(
                    writer,
                    "Reifen",
                    self.tyre_table,
                )
                self.write_table_to_csv(
                    writer,
                    "Setup",
                    self.setup_table,
                )
                self.write_table_to_csv(
                    writer,
                    "Sessiondaten",
                    self.raw_table,
                )
        except OSError as error:
            QMessageBox.critical(
                self,
                "Export fehlgeschlagen",
                str(error),
            )
            return

        QMessageBox.information(
            self,
            "Export abgeschlossen",
            f"Die CSV-Datei wurde gespeichert:\n\n{path}",
        )

    @staticmethod
    def write_table_to_csv(
        writer,
        title: str,
        table: QTableWidget,
    ) -> None:
        writer.writerow([title])
        writer.writerow(
            [
                table.horizontalHeaderItem(column).text()
                for column in range(table.columnCount())
            ]
        )

        for row in range(table.rowCount()):
            writer.writerow(
                [
                    (
                        table.item(row, column).text()
                        if table.item(row, column)
                        else ""
                    )
                    for column in range(table.columnCount())
                ]
            )

        writer.writerow([])



class ReportsPage(QWidget):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(14)

        header = QHBoxLayout()

        title_box = QVBoxLayout()
        title = QLabel("PDF-Berichte")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Komplette Rennwochenenden als professionellen Teambericht exportieren"
        )
        subtitle.setObjectName("analysisSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header.addLayout(title_box)
        header.addStretch()

        refresh_button = QPushButton("Aktualisieren")
        refresh_button.clicked.connect(self.refresh)
        header.addWidget(refresh_button)

        root.addLayout(header)

        selection_panel = QFrame()
        selection_panel.setObjectName(
            "reportSelectionPanel"
        )
        selection_layout = QGridLayout(
            selection_panel
        )

        event_label = QLabel("Rennevent")
        event_label.setObjectName("analysisCardLabel")

        self.event_combo = QComboBox()
        self.event_combo.setMinimumWidth(520)
        self.event_combo.currentIndexChanged.connect(
            self.update_preview
        )

        self.export_button = QPushButton(
            "PDF-Bericht erstellen"
        )
        self.export_button.setObjectName(
            "primaryActionButton"
        )
        self.export_button.clicked.connect(
            self.export_pdf
        )

        selection_layout.addWidget(
            event_label,
            0,
            0,
        )
        selection_layout.addWidget(
            self.event_combo,
            1,
            0,
        )
        selection_layout.addWidget(
            self.export_button,
            1,
            1,
        )
        selection_layout.setColumnStretch(0, 1)

        root.addWidget(selection_panel)

        preview_splitter = QSplitter(
            Qt.Horizontal
        )

        self.event_preview = QFrame()
        self.event_preview.setObjectName(
            "reportPreviewPanel"
        )
        preview_layout = QVBoxLayout(
            self.event_preview
        )

        preview_title = QLabel("BERICHTSUMFANG")
        preview_title.setObjectName(
            "analysisCardLabel"
        )
        self.preview_heading = QLabel("-")
        self.preview_heading.setObjectName(
            "reportPreviewTitle"
        )
        self.preview_text = QLabel("")
        self.preview_text.setWordWrap(True)
        self.preview_text.setObjectName(
            "analysisRecommendationText"
        )

        preview_layout.addWidget(preview_title)
        preview_layout.addWidget(
            self.preview_heading
        )
        preview_layout.addWidget(
            self.preview_text
        )
        preview_layout.addStretch()

        self.contents_tree = QTreeWidget()
        self.contents_tree.setHeaderLabels(
            ("Inhalt", "Anzahl / Details")
        )
        self.contents_tree.header().setStretchLastSection(
            True
        )
        self.contents_tree.setAlternatingRowColors(
            True
        )

        preview_splitter.addWidget(
            self.event_preview
        )
        preview_splitter.addWidget(
            self.contents_tree
        )
        preview_splitter.setStretchFactor(0, 2)
        preview_splitter.setStretchFactor(1, 3)
        preview_splitter.setSizes([520, 800])

        root.addWidget(preview_splitter, 1)

        info_panel = QFrame()
        info_panel.setObjectName(
            "reportInfoPanel"
        )
        info_layout = QVBoxLayout(info_panel)

        info_title = QLabel(
            "DER PDF-BERICHT ENTHÄLT"
        )
        info_title.setObjectName(
            "analysisCardLabel"
        )
        info_text = QLabel(
            "Eventdaten · Sessions · Fahrzeuge · Fahrer · Wetter · "
            "Reifendrücke · Reifentemperatur Mitte · Setup · "
            "Fahrzeugänderungen · Notizen · gespeicherte Bilder"
        )
        info_text.setWordWrap(True)

        info_layout.addWidget(info_title)
        info_layout.addWidget(info_text)
        root.addWidget(info_panel)

        self.refresh()

    def refresh(self) -> None:
        selected = self.event_combo.currentData()

        self.event_combo.blockSignals(True)
        self.event_combo.clear()
        self.event_combo.addItem(
            "Rennevent auswählen ...",
            None,
        )

        for event in self.database.get_events():
            label = (
                f'{event["start_date"]} · '
                f'{event["name"]} · '
                f'{event["track_name"]}'
            )
            self.event_combo.addItem(
                label,
                event["id"],
            )

        index = self.event_combo.findData(selected)

        if index < 0 and self.event_combo.count() > 1:
            index = 1

        self.event_combo.setCurrentIndex(
            max(0, index)
        )
        self.event_combo.blockSignals(False)
        self.update_preview()

    def update_preview(self) -> None:
        self.contents_tree.clear()
        event_id = self.event_combo.currentData()

        if event_id is None:
            self.preview_heading.setText(
                "Kein Event ausgewählt"
            )
            self.preview_text.setText(
                "Wähle ein Rennevent aus, um den Berichtsumfang zu sehen."
            )
            return

        try:
            bundle = (
                self.database.get_event_report_bundle(
                    int(event_id)
                )
            )
        except Exception as error:
            self.preview_heading.setText(
                "Vorschau nicht verfügbar"
            )
            self.preview_text.setText(str(error))
            return

        event = bundle["event"]
        sessions = bundle["sessions"]

        tyre_count = sum(
            len(item["tyres"])
            for item in sessions
        )
        setup_count = sum(
            len(item["setup"])
            for item in sessions
        )
        change_count = sum(
            len(item["changes"])
            for item in sessions
        )
        media_count = sum(
            len(item["media"])
            for item in sessions
        )

        self.preview_heading.setText(
            event["name"]
        )
        self.preview_text.setText(
            f'{event["track_name"]}\n'
            f'{event["start_date"]} bis '
            f'{event["end_date"] or event["start_date"]}\n\n'
            f'{len(sessions)} Sessions · '
            f'{tyre_count} Reifenmessungen · '
            f'{setup_count} Setup-Einträge · '
            f'{change_count} Fahrzeugänderungen · '
            f'{media_count} Medien'
        )

        event_item = QTreeWidgetItem(
            (
                event["name"],
                event["track_name"],
            )
        )
        self.contents_tree.addTopLevelItem(
            event_item
        )

        for session_bundle in sessions:
            session = session_bundle["session"]
            session_item = QTreeWidgetItem(
                (
                    (
                        f'{session["session_date"]} · '
                        f'{session["session_type"]}'
                    ),
                    (
                        f'{session["manufacturer"]} '
                        f'{session["model"]}'
                    ),
                )
            )
            event_item.addChild(session_item)

            session_item.addChild(
                QTreeWidgetItem(
                    (
                        "Reifendaten",
                        str(
                            len(
                                session_bundle["tyres"]
                            )
                        ),
                    )
                )
            )
            session_item.addChild(
                QTreeWidgetItem(
                    (
                        "Setup",
                        str(
                            len(
                                session_bundle["setup"]
                            )
                        ),
                    )
                )
            )
            session_item.addChild(
                QTreeWidgetItem(
                    (
                        "Fahrzeugänderungen",
                        str(
                            len(
                                session_bundle["changes"]
                            )
                        ),
                    )
                )
            )
            session_item.addChild(
                QTreeWidgetItem(
                    (
                        "Bilder & Dateien",
                        str(
                            len(
                                session_bundle["media"]
                            )
                        ),
                    )
                )
            )

        self.contents_tree.expandAll()

    def export_pdf(self) -> None:
        event_id = self.event_combo.currentData()

        if event_id is None:
            QMessageBox.information(
                self,
                "Rennevent auswählen",
                "Bitte zuerst ein Rennevent auswählen.",
            )
            return

        event = self.database.get_event(
            int(event_id)
        )

        default_name = (
            f"SORG_{event['name']}_{event['start_date']}.pdf"
            .replace(" ", "_")
            .replace("/", "-")
        )

        path, _ = QFileDialog.getSaveFileName(
            self,
            "PDF-Bericht speichern",
            default_name,
            "PDF-Dateien (*.pdf)",
        )

        if not path:
            return

        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        self.export_button.setEnabled(False)
        self.export_button.setText(
            "Bericht wird erstellt ..."
        )
        QApplication.processEvents()

        try:
            bundle = (
                self.database.get_event_report_bundle(
                    int(event_id)
                )
            )

            report = MotorsportReport(
                path,
                logo_path=resource_path("sorg_full_logo.jpg"),
                hero_path=resource_path("motorsport_hero.jpg"),
            )
            report.build_event_report(bundle)
        except Exception as error:
            QMessageBox.critical(
                self,
                "PDF-Export fehlgeschlagen",
                str(error),
            )
            return
        finally:
            self.export_button.setEnabled(True)
            self.export_button.setText(
                "PDF-Bericht erstellen"
            )

        answer = QMessageBox.question(
            self,
            "PDF-Bericht erstellt",
            (
                f"Der Bericht wurde gespeichert:\n\n{path}\n\n"
                "Jetzt öffnen?"
            ),
        )

        if answer == QMessageBox.Yes:
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(
                    str(Path(path).resolve())
                )
            )



class EventsPage(QWidget):
    def __init__(self, database: Database, changed_callback) -> None:
        super().__init__()
        self.database = database
        self.changed_callback = changed_callback
        self.selected_event_id = None
        self.selected_session_id = None
        self.expanded_keys = set()

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        hero = QFrame()
        hero.setObjectName("eventHero")
        hero.setFixedHeight(210)
        hero_image = resource_path("motorsport_hero.jpg")
        if hero_image.exists():
            hero.setStyleSheet(
                "QFrame#eventHero {"
                f"border-image: url({str(hero_image).replace(chr(92), '/')}) "
                "0 0 0 0 stretch stretch;"
                "border: 1px solid #34363c; border-radius: 12px;}"
            )

        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(24, 20, 24, 20)
        hero_layout.addStretch()

        hero_glass = QFrame()
        hero_glass.setObjectName("eventHeroGlass")
        hero_glass.setMaximumWidth(610)
        glass_layout = QVBoxLayout(hero_glass)
        glass_layout.setContentsMargins(22, 16, 22, 16)

        hero_title = QLabel("SORG RENNSPORT")
        hero_title.setObjectName("eventHeroMainTitle")
        hero_sub = QLabel("GT Data Analyzer")
        hero_sub.setObjectName("eventHeroMainSub")
        accent = QFrame()
        accent.setObjectName("heroAccent")
        accent.setFixedHeight(4)
        hero_info = QLabel(
            "Rennwochenenden. Reifen. Setup. Performance."
        )
        hero_info.setObjectName("eventHeroInfo")

        glass_layout.addWidget(hero_title)
        glass_layout.addWidget(hero_sub)
        glass_layout.addWidget(accent)
        glass_layout.addWidget(hero_info)
        hero_layout.insertWidget(0, hero_glass, 0, Qt.AlignLeft | Qt.AlignBottom)
        root.addWidget(hero)

        self._build_filters(root)

        actions = QHBoxLayout()
        actions.addStretch()
        for text, callback in (
            ("+ Event", self.new_event),
            ("+ Session", self.new_session),
            ("+ Reifensatz", self.new_tyre_set),
            ("+ Änderung", self.new_change_entry),
            ("+ Setup", self.new_setup_entry),
            ("+ Bild/Datei", self.new_media_item),
        ):
            button = QPushButton(text)
            if text == "+ Bild/Datei":
                button.setObjectName("primaryRed")
            button.clicked.connect(callback)
            actions.addWidget(button)
        root.addLayout(actions)

        body = QSplitter(Qt.Horizontal)
        body.setChildrenCollapsible(False)

        # Left: Event cards
        event_panel = QFrame()
        event_panel.setObjectName("panel")
        event_panel_layout = QVBoxLayout(event_panel)
        event_panel_layout.setContentsMargins(8, 8, 8, 8)

        event_header = QHBoxLayout()
        event_title = QLabel("RENNEVENTS")
        event_title.setObjectName("sectionRed")
        self.event_count = QLabel("0")
        self.event_count.setObjectName("countBadge")
        event_header.addWidget(event_title)
        event_header.addStretch()
        event_header.addWidget(self.event_count)
        event_panel_layout.addLayout(event_header)

        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setFrameShape(QFrame.NoFrame)
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(9)
        self.cards_layout.addStretch()
        self.cards_scroll.setWidget(self.cards_container)
        event_panel_layout.addWidget(self.cards_scroll)

        # Middle: structure
        structure_panel = QFrame()
        structure_panel.setObjectName("panel")
        structure_layout = QVBoxLayout(structure_panel)
        structure_layout.setContentsMargins(8, 8, 8, 8)

        self.structure_title = QLabel("STRUKTUR")
        self.structure_title.setObjectName("sectionRed")
        structure_layout.addWidget(self.structure_title)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(22)
        self.tree.setFont(QFont("Segoe UI", 10))
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)
        self.tree.currentItemChanged.connect(self.on_tree_selection)
        self.tree.itemDoubleClicked.connect(self.handle_double_click)
        structure_layout.addWidget(self.tree)

        # Right: media/details/metrics
        detail_panel = QFrame()
        detail_panel.setObjectName("panel")
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(8, 8, 8, 8)
        detail_layout.setSpacing(8)

        detail_header = QHBoxLayout()
        self.detail_title = QLabel("DETAILS")
        self.detail_title.setObjectName("sectionRed")
        detail_header.addWidget(self.detail_title)
        detail_header.addStretch()

        self.media_add_button = QPushButton("+ Bild/Datei")
        self.media_add_button.setObjectName("primaryRed")
        self.media_add_button.clicked.connect(self.new_media_item)
        detail_header.addWidget(self.media_add_button)

        edit_button = QPushButton("Bearbeiten")
        edit_button.clicked.connect(self.edit_selected)
        detail_header.addWidget(edit_button)

        delete_button = QPushButton("Löschen")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self.delete_selected)
        detail_header.addWidget(delete_button)
        detail_layout.addLayout(detail_header)

        zoom_out_button = QPushButton("−")
        zoom_out_button.setObjectName("zoomButton")
        zoom_out_button.setToolTip("Bild verkleinern")
        zoom_out_button.setFixedSize(34, 30)

        reset_zoom_button = QPushButton("100%")
        reset_zoom_button.setObjectName("zoomButton")
        reset_zoom_button.setToolTip(
            "Bild vollständig einpassen"
        )
        reset_zoom_button.setFixedSize(58, 30)

        zoom_in_button = QPushButton("+")
        zoom_in_button.setObjectName("zoomButton")
        zoom_in_button.setToolTip("Bild vergrößern")
        zoom_in_button.setFixedSize(34, 30)

        detail_header.addWidget(zoom_out_button)
        detail_header.addWidget(reset_zoom_button)
        detail_header.addWidget(zoom_in_button)

        self.preview_label = ZoomableImageView()
        self.preview_label.setObjectName("mainPreview")
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setAlignment(Qt.AlignCenter)
        detail_layout.addWidget(self.preview_label, 2)

        zoom_out_button.clicked.connect(
            self.preview_label.zoom_out
        )
        reset_zoom_button.clicked.connect(
            self.preview_label.reset_zoom
        )
        zoom_in_button.clicked.connect(
            self.preview_label.zoom_in
        )

        self.thumb_scroll = QScrollArea()
        self.thumb_scroll.setFixedHeight(92)
        self.thumb_scroll.setWidgetResizable(True)
        self.thumb_scroll.setFrameShape(QFrame.NoFrame)
        self.thumb_container = QWidget()
        self.thumb_layout = QHBoxLayout(self.thumb_container)
        self.thumb_layout.setContentsMargins(0, 0, 0, 0)
        self.thumb_layout.setSpacing(7)
        self.thumb_layout.addStretch()
        self.thumb_scroll.setWidget(self.thumb_container)
        detail_layout.addWidget(self.thumb_scroll)

        metrics = QGridLayout()
        metrics.setSpacing(8)

        self.session_info = QLabel()
        self.session_info.setObjectName("metricCard")
        self.session_info.setWordWrap(True)

        self.tyre_pressure = QLabel()
        self.tyre_pressure.setObjectName("metricCard")
        self.tyre_pressure.setWordWrap(True)

        self.tyre_temps = QLabel()
        self.tyre_temps.setObjectName("metricCard")
        self.tyre_temps.setWordWrap(True)

        self.changes_info = QLabel()
        self.changes_info.setObjectName("metricCard")
        self.changes_info.setWordWrap(True)

        metrics.addWidget(self.session_info, 0, 0)
        metrics.addWidget(self.tyre_pressure, 0, 1)
        metrics.addWidget(self.tyre_temps, 1, 0)
        metrics.addWidget(self.changes_info, 1, 1)
        detail_layout.addLayout(metrics, 2)

        body.addWidget(event_panel)
        body.addWidget(structure_panel)
        body.addWidget(detail_panel)
        body.setStretchFactor(0, 3)
        body.setStretchFactor(1, 3)
        body.setStretchFactor(2, 6)
        body.setSizes([370, 430, 800])
        root.addWidget(body, 1)

        self.refresh()

    def _build_filters(self, root):
        bar = QFrame()
        bar.setObjectName("compactFilterBar")
        bar.setFixedHeight(52)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 7, 8, 7)
        layout.setSpacing(7)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("⌕  Suche...")
        self.search_edit.setMaximumWidth(220)
        self.search_edit.textChanged.connect(self.refresh)

        self.year_filter = QComboBox()
        self.track_filter = QComboBox()
        self.championship_filter = QComboBox()
        self.driver_filter = QComboBox()
        self.car_filter = QComboBox()
        self.status_filter = QComboBox()
        self.sort_filter = QComboBox()

        self.status_filter.addItem("Alle Events", "all")
        self.status_filter.addItem("Zukünftig", "future")
        self.status_filter.addItem("Vergangen", "past")
        self.status_filter.addItem("Heute aktiv", "today")

        self.sort_filter.addItem("Datum neu → alt", "date_desc")
        self.sort_filter.addItem("Datum alt → neu", "date_asc")
        self.sort_filter.addItem("Strecke A → Z", "track")
        self.sort_filter.addItem("Event A → Z", "event")

        combos = (
            (self.year_filter, "Jahr"),
            (self.track_filter, "Strecke"),
            (self.championship_filter, "Serie"),
            (self.driver_filter, "Fahrer"),
            (self.car_filter, "Fahrzeug"),
        )
        for combo, tip in combos:
            combo.setMinimumWidth(100)
            combo.setMaximumWidth(145)
            combo.setToolTip(tip)
            combo.currentIndexChanged.connect(self.refresh)

        self.status_filter.currentIndexChanged.connect(self.refresh)
        self.sort_filter.currentIndexChanged.connect(self.refresh)

        reset = QPushButton("↻")
        reset.setObjectName("filterReset")
        reset.setFixedSize(38, 30)
        reset.clicked.connect(self.reset_filters)

        layout.addWidget(self.search_edit, 1)
        for combo, _ in combos:
            layout.addWidget(combo)
        layout.addWidget(self.status_filter)
        layout.addWidget(self.sort_filter)
        layout.addWidget(reset)
        root.addWidget(bar)

    def populate_filters(self):
        values = {
            self.year_filter: sorted(
                {
                    str(row["start_date"] or "")[:4]
                    for row in self.database.get_events()
                    if str(row["start_date"] or "")[:4].isdigit()
                },
                reverse=True,
            ),
            self.track_filter: [
                (row["id"], row["name"]) for row in self.database.get_tracks()
            ],
            self.championship_filter: sorted(
                {
                    row["championship"]
                    for row in self.database.get_events()
                    if row["championship"]
                }
            ),
            self.driver_filter: [
                (
                    row["id"],
                    f'{row["first_name"]} {row["last_name"] or ""}'.strip(),
                )
                for row in self.database.get_drivers()
            ],
            self.car_filter: [
                (row["id"], f'{row["manufacturer"]} {row["model"]}')
                for row in self.database.get_cars()
            ],
        }

        for combo, options in values.items():
            current = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Alle", None)
            for option in options:
                if isinstance(option, tuple):
                    combo.addItem(option[1], option[0])
                else:
                    combo.addItem(str(option), option)
            index = combo.findData(current)
            combo.setCurrentIndex(index if index >= 0 else 0)
            combo.blockSignals(False)

    def reset_filters(self):
        self.search_edit.clear()
        for combo in (
            self.year_filter,
            self.track_filter,
            self.championship_filter,
            self.driver_filter,
            self.car_filter,
            self.status_filter,
            self.sort_filter,
        ):
            combo.setCurrentIndex(0)
        self.refresh()

    def filtered_events(self):
        from datetime import date

        search = self.search_edit.text().strip().lower()
        year = self.year_filter.currentData()
        track = self.track_filter.currentData()
        series = self.championship_filter.currentData()
        driver = self.driver_filter.currentData()
        car = self.car_filter.currentData()
        status = self.status_filter.currentData()
        today = date.today()
        result = []

        for event in self.database.get_events():
            sessions = list(self.database.get_sessions_for_event(event["id"]))
            start_text = str(event["start_date"] or "")
            end_text = str(event["end_date"] or "") or start_text

            if year and not start_text.startswith(str(year)):
                continue
            if track is not None and event["track_id"] != track:
                continue
            if series and event["championship"] != series:
                continue
            if driver is not None and not any(s["driver_id"] == driver for s in sessions):
                continue
            if car is not None and not any(s["car_id"] == car for s in sessions):
                continue

            try:
                start_date = date.fromisoformat(start_text)
                end_date = date.fromisoformat(end_text)
            except ValueError:
                start_date = end_date = None

            if status == "future" and (not start_date or start_date <= today):
                continue
            if status == "past" and (not end_date or end_date >= today):
                continue
            if status == "today" and (
                not start_date or not end_date or not start_date <= today <= end_date
            ):
                continue

            searchable = " ".join(
                str(x or "")
                for x in (
                    event["name"],
                    event["track_name"],
                    event["championship"],
                    event["notes"],
                    *[
                        " ".join(
                            str(v or "")
                            for v in (
                                s["session_type"],
                                s["manufacturer"],
                                s["model"],
                                driver_name(s),
                            )
                        )
                        for s in sessions
                    ],
                )
            ).lower()
            if search and search not in searchable:
                continue

            result.append((event, sessions))

        sort_mode = self.sort_filter.currentData()
        if sort_mode == "date_asc":
            result.sort(key=lambda p: p[0]["start_date"] or "")
        elif sort_mode == "track":
            result.sort(key=lambda p: (p[0]["track_name"] or "").lower())
        elif sort_mode == "event":
            result.sort(key=lambda p: (p[0]["name"] or "").lower())
        else:
            result.sort(
                key=lambda p: (p[0]["start_date"] or "", p[0]["id"]),
                reverse=True,
            )
        return result

    def refresh(self):
        self.populate_filters()
        events = self.filtered_events()

        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.event_count.setText(str(len(events)))

        if self.selected_event_id is None and events:
            self.selected_event_id = int(events[0][0]["id"])

        for event, sessions in events:
            media_image = None
            for session in sessions:
                for media in self.database.get_session_media(session["id"]):
                    suffix = Path(media["file_path"]).suffix.lower()
                    if suffix in (".jpg", ".jpeg", ".png", ".webp", ".bmp"):
                        media_image = media["file_path"]
                        break
                if media_image:
                    break

            card = EventCard(
                event,
                sessions,
                media_image,
                selected=int(event["id"]) == self.selected_event_id,
            )
            card.mousePressEvent = (
                lambda e, event_id=int(event["id"]): self.select_event(event_id)
            )
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

        self.rebuild_tree()
        self.update_detail_panels()

    def select_event(self, event_id):
        self.selected_event_id = event_id
        sessions = self.database.get_sessions_for_event(event_id)
        self.selected_session_id = int(sessions[0]["id"]) if sessions else None
        self.refresh()

    def rebuild_tree(self):
        self.tree.clear()
        event = self.database.get_event(self.selected_event_id) if self.selected_event_id else None
        if not event:
            self.structure_title.setText("STRUKTUR")
            return

        self.structure_title.setText(
            f'STRUKTUR – {event["name"].upper()} – {event["track_name"].upper()}'
        )

        root_item = QTreeWidgetItem((f'📁 {event["name"]} – {event["track_name"]}',))
        root_item.setData(0, Qt.UserRole, ("event", event["id"], None))
        self.tree.addTopLevelItem(root_item)

        info = QTreeWidgetItem(("▣ Event-Informationen",))
        info.setData(0, Qt.UserRole, ("event", event["id"], None))
        root_item.addChild(info)

        for session in self.database.get_sessions_for_event(event["id"]):
            session_item = QTreeWidgetItem(
                (f'📁 {session["session_type"]} – {session["session_date"]}',)
            )
            session_item.setData(
                0, Qt.UserRole, ("session", session["id"], event["id"])
            )
            root_item.addChild(session_item)

            pressure = QTreeWidgetItem(("◉ Reifendruck",))
            pressure.setData(
                0, Qt.UserRole, ("tyre_category", session["id"], event["id"])
            )
            session_item.addChild(pressure)

            for tyre_set in self.database.get_tyre_sets_for_session(session["id"]):
                tyre_item = QTreeWidgetItem(
                    (f'🛞 Reifensatz {tyre_set["set_number"] or tyre_set["id"]}',)
                )
                tyre_item.setData(
                    0,
                    Qt.UserRole,
                    ("tyre_set", tyre_set["id"], session["id"]),
                )
                pressure.addChild(tyre_item)
                for wheel in self.database.get_tyre_measurements(tyre_set["id"]):
                    wheel_item = QTreeWidgetItem(
                        (WHEEL_NAMES.get(wheel["position"], wheel["position"]),)
                    )
                    wheel_item.setData(
                        0,
                        Qt.UserRole,
                        ("wheel", tyre_set["id"], wheel["position"]),
                    )
                    tyre_item.addChild(wheel_item)

            changes = QTreeWidgetItem(("🛠 Fahrzeugänderungen",))
            changes.setData(
                0, Qt.UserRole, ("changes", session["id"], event["id"])
            )
            session_item.addChild(changes)
            for row in self.database.get_session_changes(session["id"]):
                child = QTreeWidgetItem((f'{row["category"]} · {row["title"]}',))
                child.setData(
                    0, Qt.UserRole, ("change_entry", row["id"], session["id"])
                )
                changes.addChild(child)

            setup = QTreeWidgetItem(("⚙ Setup",))
            setup.setData(
                0, Qt.UserRole, ("setup_category", session["id"], event["id"])
            )
            session_item.addChild(setup)
            for row in self.database.get_setup_entries(session["id"]):
                child = QTreeWidgetItem(
                    (f'{row["category"]} · {row["parameter_name"]}',)
                )
                child.setData(
                    0, Qt.UserRole, ("setup_entry", row["id"], session["id"])
                )
                setup.addChild(child)

            weather = QTreeWidgetItem(("☁ Wetter",))
            weather.setData(
                0, Qt.UserRole, ("session", session["id"], event["id"])
            )
            session_item.addChild(weather)

            notes = QTreeWidgetItem(("▤ Notizen",))
            notes.setData(
                0, Qt.UserRole, ("session", session["id"], event["id"])
            )
            session_item.addChild(notes)

            media_cat = QTreeWidgetItem(("▧ Bilder & Dateien",))
            media_cat.setData(
                0, Qt.UserRole, ("media_category", session["id"], event["id"])
            )
            session_item.addChild(media_cat)
            for media in self.database.get_session_media(session["id"]):
                child = QTreeWidgetItem(
                    (f'{media["media_type"] or "Datei"} · {media["title"]}',)
                )
                child.setData(
                    0, Qt.UserRole, ("media_item", media["id"], session["id"])
                )
                media_cat.addChild(child)

        self.tree.expandToDepth(1)

    def selected_data(self):
        item = self.tree.currentItem()
        return item.data(0, Qt.UserRole) if item else None

    def on_tree_selection(self, current, previous=None):
        data = current.data(0, Qt.UserRole) if current else None
        if data and data[0] in ("session", "tyre_category", "changes",
                               "setup_category", "media_category"):
            self.selected_session_id = int(data[1])
        elif data and data[0] in ("tyre_set", "change_entry",
                                  "setup_entry", "media_item"):
            self.selected_session_id = int(data[2])
        self.update_detail_panels()

    def update_detail_panels(self):
        session = (
            self.database.get_session(self.selected_session_id)
            if self.selected_session_id else None
        )
        if not session:
            self.detail_title.setText("DETAILS")
            self._set_default_preview()
            self.session_info.setText("<b>SESSION INFORMATIONEN</b><br>Keine Session ausgewählt")
            self.tyre_pressure.setText("<b>REIFENDRUCK</b><br>Keine Daten")
            self.tyre_temps.setText("<b>REIFENTEMPERATUREN</b><br>Keine Daten")
            self.changes_info.setText("<b>FAHRZEUGÄNDERUNGEN</b><br>Keine Daten")
            return

        self.detail_title.setText(
            f'DETAILS – {session["session_type"]} – {session["session_date"]}'
        )
        self.session_info.setText(
            "<b>SESSION INFORMATIONEN</b><br><br>"
            f'Session: {session["session_type"]}<br>'
            f'Datum: {session["session_date"]}<br>'
            f'Strecke: {session["track_name"]}<br>'
            f'Fahrzeug: {session["manufacturer"]} {session["model"]}<br>'
            f'Fahrer: {driver_name(session)}<br>'
            f'Wetter: {session["weather"] or "-"}<br>'
            f'Luft: {float(session["air_temp_c"] or 0):.1f} °C<br>'
            f'Asphalt: {float(session["track_temp_c"] or 0):.1f} °C<br>'
            f'Felge: {float(session["rim_temp_c"] or 0):.1f} °C'
        )

        tyre_sets = self.database.get_tyre_sets_for_session(session["id"])
        measurements = (
            self.database.get_tyre_measurements(tyre_sets[0]["id"])
            if tyre_sets else []
        )

        pressure_lines = ["<b>REIFENDRUCK</b><br>"]
        temp_lines = ["<b>REIFENTEMPERATUREN</b><br>"]
        for row in measurements:
            name = WHEEL_NAMES.get(row["position"], row["position"])
            cold = "-" if row["cold_pressure_bar"] is None else f'{row["cold_pressure_bar"]:.2f}'
            hot = "-" if row["hot_pressure_bar"] is None else f'{row["hot_pressure_bar"]:.2f}'
            pressure_lines.append(f"{name}: {cold} / {hot} bar")
            middle = "-" if row["temp_middle_c"] is None else f'{row["temp_middle_c"]:.1f}'
            temp_lines.append(f"{name}: {inside} / {middle} / {outside} °C")

        self.tyre_pressure.setText("<br>".join(pressure_lines))
        self.tyre_temps.setText("<br>".join(temp_lines))

        changes = self.database.get_session_changes(session["id"])
        change_lines = ["<b>FAHRZEUGÄNDERUNGEN</b><br>"]
        for row in changes[:6]:
            change_lines.append(
                f'{row["title"]}: {row["description"] or "-"}'
            )
        self.changes_info.setText("<br>".join(change_lines))

        self.rebuild_media_gallery(session["id"])

    def _set_default_preview(self):
        image = resource_path("motorsport_preview.jpg")
        pixmap = QPixmap(str(image))
        if not pixmap.isNull():
            self.preview_label.setPixmap(pixmap)

    def rebuild_media_gallery(self, session_id):
        while self.thumb_layout.count() > 1:
            item = self.thumb_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        media_items = self.database.get_session_media(session_id)
        first_image = None
        for media in media_items:
            path = Path(media["file_path"])
            suffix = path.suffix.lower()
            button = QPushButton()
            button.setFixedSize(112, 72)
            button.setToolTip(media["title"])

            if path.exists() and suffix in (".jpg", ".jpeg", ".png", ".webp", ".bmp"):
                pixmap = QPixmap(str(path))
                button.setIcon(QIcon(pixmap))
                button.setIconSize(QSize(106, 66))
                if first_image is None:
                    first_image = path
                button.clicked.connect(
                    lambda checked=False, p=str(path): self.show_image(p)
                )
            else:
                button.setText(media["media_type"] or "Datei")
                button.clicked.connect(
                    lambda checked=False, p=str(path): QDesktopServices.openUrl(
                        QUrl.fromLocalFile(p)
                    )
                )
            self.thumb_layout.insertWidget(self.thumb_layout.count() - 1, button)

        if first_image:
            self.show_image(str(first_image))
        else:
            self._set_default_preview()

    def show_image(self, path):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.preview_label.setPixmap(pixmap)

    def selected_session_for_action(self):
        data = self.selected_data()
        if data:
            if data[0] in ("session", "tyre_category", "changes",
                           "setup_category", "media_category"):
                return int(data[1])
            if data[0] in ("tyre_set", "change_entry",
                           "setup_entry", "media_item"):
                return int(data[2])
        return self.selected_session_id

    def new_event(self):
        if EventDialog(self.database, parent=self).exec():
            self.changed_callback()
            self.refresh()

    def new_session(self):
        if self.selected_event_id is None:
            QMessageBox.information(self, "Event auswählen", "Bitte Event auswählen.")
            return
        if SessionDialog(
            self.database, event_id=self.selected_event_id, parent=self
        ).exec():
            self.changed_callback()
            self.refresh()

    def new_tyre_set(self):
        session_id = self.selected_session_for_action()
        if session_id is None:
            QMessageBox.information(self, "Session auswählen", "Bitte Session auswählen.")
            return
        if TyreSetDialog(self.database, session_id=session_id, parent=self).exec():
            self.changed_callback()
            self.refresh()

    def new_change_entry(self):
        session_id = self.selected_session_for_action()
        if session_id is None:
            QMessageBox.information(self, "Session auswählen", "Bitte Session auswählen.")
            return
        if SessionChangeDialog(
            self.database, session_id=session_id, parent=self
        ).exec():
            self.changed_callback()
            self.refresh()

    def new_setup_entry(self):
        session_id = self.selected_session_for_action()
        if session_id is None:
            QMessageBox.information(self, "Session auswählen", "Bitte Session auswählen.")
            return
        if SetupEntryDialog(
            self.database, session_id=session_id, parent=self
        ).exec():
            self.changed_callback()
            self.refresh()

    def new_media_item(self):
        session_id = self.selected_session_for_action()
        if session_id is None:
            QMessageBox.information(self, "Session auswählen", "Bitte Session auswählen.")
            return
        if MediaDialog(
            self.database, session_id=session_id, parent=self
        ).exec():
            self.changed_callback()
            self.refresh()

    def edit_selected(self):
        data = self.selected_data()
        if not data:
            if self.selected_event_id:
                dialog = EventDialog(self.database, self.selected_event_id, self)
                if dialog.exec():
                    self.refresh()
            return

        kind, value, parent = data
        if kind == "event":
            dialog = EventDialog(self.database, int(value), self)
        elif kind == "session":
            dialog = SessionDialog(
                self.database,
                event_id=int(parent),
                session_id=int(value),
                parent=self,
            )
        elif kind == "tyre_set":
            dialog = TyreSetDialog(
                self.database,
                session_id=int(parent),
                tyre_set_id=int(value),
                parent=self,
            )
        elif kind == "wheel":
            dialog = TyreMeasurementDialog(
                self.database,
                tyre_set_id=int(value),
                position=str(parent),
                parent=self,
            )
        elif kind == "change_entry":
            dialog = SessionChangeDialog(
                self.database,
                session_id=int(parent),
                change_id=int(value),
                parent=self,
            )
        elif kind == "setup_entry":
            dialog = SetupEntryDialog(
                self.database,
                session_id=int(parent),
                setup_id=int(value),
                parent=self,
            )
        elif kind == "media_item":
            dialog = MediaDialog(
                self.database,
                session_id=int(parent),
                media_id=int(value),
                parent=self,
            )
        else:
            return

        if dialog.exec():
            self.changed_callback()
            self.refresh()

    def delete_selected(self):
        data = self.selected_data()
        if not data:
            return
        kind, value, _ = data
        if kind not in ("event", "session", "tyre_set",
                        "change_entry", "setup_entry", "media_item"):
            return

        if QMessageBox.question(
            self,
            "Löschen",
            "Eintrag wirklich löschen?",
        ) != QMessageBox.Yes:
            return

        try:
            if kind == "event":
                self.database.delete_event(int(value))
                self.selected_event_id = None
            elif kind == "session":
                self.database.delete_session(int(value))
                self.selected_session_id = None
            elif kind == "tyre_set":
                self.database.delete_tyre_set(int(value))
            elif kind == "change_entry":
                self.database.delete_session_change(int(value))
            elif kind == "setup_entry":
                self.database.delete_setup_entry(int(value))
            else:
                self.database.delete_media_item(int(value))
        except Exception as error:
            QMessageBox.critical(self, "Fehler", str(error))
        self.changed_callback()
        self.refresh()

    def handle_double_click(self, item, column):
        data = item.data(0, Qt.UserRole)
        if data and data[0] == "media_item":
            media = self.database.get_media_item(int(data[1]))
            if media and Path(media["file_path"]).exists():
                QDesktopServices.openUrl(
                    QUrl.fromLocalFile(str(Path(media["file_path"]).resolve()))
                )
                return
        self.edit_selected()

    def open_context_menu(self, position):
        menu = QMenu(self)
        menu.addAction("Bearbeiten", self.edit_selected)
        menu.addAction("Löschen", self.delete_selected)
        menu.exec(self.tree.viewport().mapToGlobal(position))


class QuickWorkflowPage(QWidget):
    """Geführte Schnellerfassung für den Einsatz an der Rennstrecke."""

    def __init__(self, database: Database, refresh_callback):
        super().__init__()
        self.database = database
        self.refresh_callback = refresh_callback

        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 28, 34, 28)
        layout.setSpacing(18)

        title = QLabel("Schnellerfassung")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Event auswählen und danach Session, Reifensatz und Messwerte "
            "in einer klaren Reihenfolge erfassen."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("mutedText")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        selection = QFrame()
        selection.setObjectName("contentCard")
        selection_layout = QGridLayout(selection)
        selection_layout.setContentsMargins(22, 22, 22, 22)
        selection_layout.setHorizontalSpacing(14)
        selection_layout.setVerticalSpacing(14)

        selection_layout.addWidget(QLabel("1 · Event"), 0, 0)
        self.event_combo = QComboBox()
        self.event_combo.currentIndexChanged.connect(self._event_changed)
        selection_layout.addWidget(self.event_combo, 0, 1)
        new_event = QPushButton("+ Neues Event")
        new_event.clicked.connect(self.new_event)
        selection_layout.addWidget(new_event, 0, 2)

        selection_layout.addWidget(QLabel("2 · Session"), 1, 0)
        self.session_combo = QComboBox()
        self.session_combo.currentIndexChanged.connect(self._session_changed)
        selection_layout.addWidget(self.session_combo, 1, 1)
        new_session = QPushButton("+ Neue Session")
        new_session.clicked.connect(self.new_session)
        selection_layout.addWidget(new_session, 1, 2)

        selection_layout.addWidget(QLabel("3 · Reifensatz"), 2, 0)
        self.tyre_set_combo = QComboBox()
        selection_layout.addWidget(self.tyre_set_combo, 2, 1)
        new_set = QPushButton("+ Neuer Reifensatz")
        new_set.clicked.connect(self.new_tyre_set)
        selection_layout.addWidget(new_set, 2, 2)

        layout.addWidget(selection)

        measurement = QFrame()
        measurement.setObjectName("contentCard")
        measurement_layout = QVBoxLayout(measurement)
        measurement_layout.setContentsMargins(22, 22, 22, 22)
        measurement_layout.setSpacing(14)

        measurement_title = QLabel("4 · Reifenmessung")
        measurement_title.setObjectName("sectionTitle")
        measurement_layout.addWidget(measurement_title)

        wheel_grid = QGridLayout()
        for index, (position, label) in enumerate((
            ("FL", "Vorne links"),
            ("FR", "Vorne rechts"),
            ("RL", "Hinten links"),
            ("RR", "Hinten rechts"),
        )):
            button = QPushButton(f"🛞  {label}")
            button.setMinimumHeight(62)
            button.clicked.connect(
                lambda checked=False, pos=position: self.measure_tyre(pos)
            )
            wheel_grid.addWidget(button, index // 2, index % 2)
        measurement_layout.addLayout(wheel_grid)

        all_button = QPushButton("Alle vier Reifen nacheinander erfassen")
        all_button.setObjectName("primaryButton")
        all_button.setMinimumHeight(52)
        all_button.clicked.connect(self.measure_all)
        measurement_layout.addWidget(all_button)

        layout.addWidget(measurement)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setObjectName("mutedText")
        layout.addWidget(self.status_label)
        layout.addStretch()

    def refresh(self):
        event_id = self.event_combo.currentData()
        self.event_combo.blockSignals(True)
        self.event_combo.clear()
        for row in self.database.get_events():
            track = row["track_name"] if "track_name" in row.keys() else ""
            text = f'{row["name"]} · {track}'.strip(" ·")
            self.event_combo.addItem(text, row["id"])
        self.event_combo.blockSignals(False)
        if event_id is not None:
            index = self.event_combo.findData(event_id)
            if index >= 0:
                self.event_combo.setCurrentIndex(index)
        self._event_changed()

    def _event_changed(self):
        session_id = self.session_combo.currentData()
        self.session_combo.blockSignals(True)
        self.session_combo.clear()
        event_id = self.event_combo.currentData()
        if event_id is not None:
            for row in self.database.get_sessions_for_event(int(event_id)):
                driver = " ".join(
                    part for part in (
                        row["driver_first_name"], row["driver_last_name"]
                    ) if part
                ) or "Ohne Fahrer"
                car = f'{row["manufacturer"]} {row["model"]}'.strip()
                self.session_combo.addItem(
                    f'{row["session_type"]} · {driver} · {car}', row["id"]
                )
        self.session_combo.blockSignals(False)
        if session_id is not None:
            index = self.session_combo.findData(session_id)
            if index >= 0:
                self.session_combo.setCurrentIndex(index)
        self._session_changed()

    def _session_changed(self):
        tyre_set_id = self.tyre_set_combo.currentData()
        self.tyre_set_combo.clear()
        session_id = self.session_combo.currentData()
        if session_id is not None:
            for row in self.database.get_tyre_sets_for_session(int(session_id)):
                number = row["set_number"] or row["id"]
                detail = " · ".join(
                    value for value in (row["manufacturer"], row["compound"]) if value
                )
                self.tyre_set_combo.addItem(
                    f'Reifensatz {number}' + (f' · {detail}' if detail else ""),
                    row["id"],
                )
        if tyre_set_id is not None:
            index = self.tyre_set_combo.findData(tyre_set_id)
            if index >= 0:
                self.tyre_set_combo.setCurrentIndex(index)
        self._update_status()

    def _update_status(self):
        if self.event_combo.count() == 0:
            text = "Beginne mit einem Event. Strecke, Fahrer und Fahrzeug können unter Stammdaten angelegt werden."
        elif self.session_combo.count() == 0:
            text = "Event gewählt. Lege jetzt die erste Session an."
        elif self.tyre_set_combo.count() == 0:
            text = "Session gewählt. Lege jetzt einen Reifensatz an."
        else:
            text = "Bereit: Reifendaten können direkt erfasst werden."
        self.status_label.setText(text)

    def new_event(self):
        if EventDialog(self.database, parent=self).exec():
            self.refresh_callback()

    def new_session(self):
        event_id = self.event_combo.currentData()
        if event_id is None:
            QMessageBox.information(self, "Event fehlt", "Bitte zuerst ein Event anlegen oder auswählen.")
            return
        if SessionDialog(self.database, int(event_id), parent=self).exec():
            self.refresh_callback()

    def new_tyre_set(self):
        session_id = self.session_combo.currentData()
        if session_id is None:
            QMessageBox.information(self, "Session fehlt", "Bitte zuerst eine Session anlegen oder auswählen.")
            return
        if TyreSetDialog(self.database, int(session_id), parent=self).exec():
            self.refresh_callback()

    def measure_tyre(self, position: str) -> bool:
        tyre_set_id = self.tyre_set_combo.currentData()
        if tyre_set_id is None:
            QMessageBox.information(self, "Reifensatz fehlt", "Bitte zuerst einen Reifensatz anlegen oder auswählen.")
            return False
        accepted = TyreMeasurementDialog(
            self.database, int(tyre_set_id), position, self
        ).exec()
        if accepted:
            self.refresh_callback()
        return bool(accepted)

    def measure_all(self):
        for position in ("FL", "FR", "RL", "RR"):
            if not self.measure_tyre(position):
                break


class SimpleResultPage(QWidget):
    """Klare Ergebnisanzeige mit Ampelbewertung für den ausgewählten Reifensatz."""

    GREEN_LIMIT = 0.03
    ORANGE_LIMIT = 0.08

    STATUS_STYLES = {
        "green": "background:#173d2a; border:2px solid #35c46a; border-radius:14px; color:#eafff0;",
        "orange": "background:#4a3514; border:2px solid #f5a623; border-radius:14px; color:#fff5df;",
        "red": "background:#4b1d22; border:2px solid #ef5350; border-radius:14px; color:#ffe9e9;",
        "neutral": "background:#252a31; border:1px solid #4b5563; border-radius:14px; color:#e5e7eb;",
    }

    def __init__(self, database: Database):
        super().__init__()
        self.database = database
        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 28, 34, 28)
        layout.setSpacing(16)

        title = QLabel("Ergebnis")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Reifensatz auswählen – die Ampel zeigt sofort, ob der Druck passt.")
        subtitle.setObjectName("mutedText")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        selector = QFrame()
        selector.setObjectName("contentCard")
        grid = QGridLayout(selector)
        grid.addWidget(QLabel("Event"), 0, 0)
        self.event_combo = QComboBox()
        self.event_combo.currentIndexChanged.connect(self._event_changed)
        grid.addWidget(self.event_combo, 0, 1)
        grid.addWidget(QLabel("Session"), 1, 0)
        self.session_combo = QComboBox()
        self.session_combo.currentIndexChanged.connect(self._session_changed)
        grid.addWidget(self.session_combo, 1, 1)
        grid.addWidget(QLabel("Reifensatz"), 2, 0)
        self.tyre_set_combo = QComboBox()
        self.tyre_set_combo.currentIndexChanged.connect(self._render)
        grid.addWidget(self.tyre_set_combo, 2, 1)
        layout.addWidget(selector)

        self.overall_status = QLabel("⚪  Noch kein Reifensatz ausgewählt")
        self.overall_status.setAlignment(Qt.AlignCenter)
        self.overall_status.setMinimumHeight(78)
        self.overall_status.setFont(QFont("Arial", 18, QFont.Bold))
        self.overall_status.setStyleSheet(self.STATUS_STYLES["neutral"])
        layout.addWidget(self.overall_status)

        self.cards = {}
        cards_grid = QGridLayout()
        cards_grid.setSpacing(14)
        for index, (position, label_text) in enumerate((("FL", "Vorne links"), ("FR", "Vorne rechts"), ("RL", "Hinten links"), ("RR", "Hinten rechts"))):
            card = QFrame()
            card.setStyleSheet(self.STATUS_STYLES["neutral"])
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 16, 18, 16)
            heading = QLabel(label_text)
            heading.setObjectName("sectionTitle")
            heading.setAlignment(Qt.AlignCenter)
            value = QLabel("⚪\nNoch keine Messung")
            value.setWordWrap(True)
            value.setAlignment(Qt.AlignCenter)
            value.setMinimumHeight(120)
            value.setFont(QFont("Arial", 13, QFont.Bold))
            card_layout.addWidget(heading)
            card_layout.addWidget(value, 1)
            cards_grid.addWidget(card, index // 2, index % 2)
            self.cards[position] = {"frame": card, "value": value}
        layout.addLayout(cards_grid)

        legend = QLabel("🟢 passend: bis ±0,03 bar   ·   🟠 fahrbar: bis ±0,08 bar   ·   🔴 schlecht: über ±0,08 bar")
        legend.setObjectName("mutedText")
        legend.setAlignment(Qt.AlignCenter)
        legend.setWordWrap(True)
        layout.addWidget(legend)

        self.summary = QLabel("")
        self.summary.setObjectName("mutedText")
        self.summary.setWordWrap(True)
        self.summary.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.summary)
        layout.addStretch()

    @staticmethod
    def _number(value):
        return None if value is None else float(value)

    @classmethod
    def _traffic_status(cls, difference: float) -> tuple[str, str, str]:
        absolute = abs(difference)
        if absolute <= cls.GREEN_LIMIT:
            return "green", "🟢", "PASSEND"
        if absolute <= cls.ORANGE_LIMIT:
            return "orange", "🟠", "FAHRBAR"
        return "red", "🔴", "SCHLECHT"

    def refresh(self):
        current = self.event_combo.currentData()
        self.event_combo.blockSignals(True)
        self.event_combo.clear()
        for row in self.database.get_events():
            track = row["track_name"] if "track_name" in row.keys() else ""
            self.event_combo.addItem(f'{row["name"]} · {track}'.strip(" ·"), row["id"])
        self.event_combo.blockSignals(False)
        idx = self.event_combo.findData(current)
        if idx >= 0:
            self.event_combo.setCurrentIndex(idx)
        self._event_changed()

    def _event_changed(self):
        current = self.session_combo.currentData()
        self.session_combo.blockSignals(True)
        self.session_combo.clear()
        event_id = self.event_combo.currentData()
        if event_id is not None:
            for row in self.database.get_sessions_for_event(int(event_id)):
                driver = " ".join(x for x in (row["driver_first_name"], row["driver_last_name"]) if x) or "Ohne Fahrer"
                car = f'{row["manufacturer"]} {row["model"]}'.strip()
                self.session_combo.addItem(f'{row["session_type"]} · {driver} · {car}', row["id"])
        self.session_combo.blockSignals(False)
        idx = self.session_combo.findData(current)
        if idx >= 0:
            self.session_combo.setCurrentIndex(idx)
        self._session_changed()

    def _session_changed(self):
        current = self.tyre_set_combo.currentData()
        self.tyre_set_combo.blockSignals(True)
        self.tyre_set_combo.clear()
        session_id = self.session_combo.currentData()
        if session_id is not None:
            for row in self.database.get_tyre_sets_for_session(int(session_id)):
                number = row["set_number"] or row["id"]
                self.tyre_set_combo.addItem(f"Reifensatz {number}", row["id"])
        self.tyre_set_combo.blockSignals(False)
        idx = self.tyre_set_combo.findData(current)
        if idx >= 0:
            self.tyre_set_combo.setCurrentIndex(idx)
        self._render()

    def _render(self):
        tyre_set_id = self.tyre_set_combo.currentData()
        rows = {} if tyre_set_id is None else {
            row["position"]: row
            for row in self.database.get_tyre_measurements(int(tyre_set_id))
        }
        complete = 0
        statuses = []

        for position, widgets in self.cards.items():
            frame = widgets["frame"]
            label = widgets["value"]
            row = rows.get(position)
            if row is None:
                frame.setStyleSheet(self.STATUS_STYLES["neutral"])
                label.setText("⚪\nNOCH KEINE MESSUNG")
                continue

            hot = self._number(row["hot_pressure_bar"])
            target = self._number(row["target_pressure_bar"])
            cold = self._number(
                row["driven_cold_pressure_bar"]
                if "driven_cold_pressure_bar" in row.keys()
                else row["cold_pressure_bar"]
            )
            recommendation = self._number(
                row["calculated_cold_pressure_bar"]
                if "calculated_cold_pressure_bar" in row.keys()
                else None
            )

            if hot is not None and target is not None:
                difference = hot - target
                colour, symbol, rating = self._traffic_status(difference)
                statuses.append(colour)
                frame.setStyleSheet(self.STATUS_STYLES[colour])
                if abs(difference) <= self.GREEN_LIMIT:
                    detail = "Zieldruck passt"
                elif difference > 0:
                    detail = f"{difference:.2f} bar zu hoch"
                else:
                    detail = f"{abs(difference):.2f} bar zu niedrig"
                complete += 1
            else:
                symbol, rating, detail = "⚪", "UNVOLLSTÄNDIG", "Heiß- oder Zieldruck fehlt"
                frame.setStyleSheet(self.STATUS_STYLES["neutral"])

            lines = [f"{symbol}  {rating}", detail]
            if hot is not None and target is not None:
                lines.append(f"Heiß {hot:.2f} · Ziel {target:.2f} bar")
            if recommendation is not None:
                lines.append(f"Nächster Kaltdruck: {recommendation:.2f} bar")
            elif cold is not None:
                lines.append(f"Gefahrener Kaltdruck: {cold:.2f} bar")
            label.setText("\n".join(lines))

        if tyre_set_id is None:
            self.overall_status.setText("⚪  Noch kein Reifensatz ausgewählt")
            self.overall_status.setStyleSheet(self.STATUS_STYLES["neutral"])
            self.summary.setText("Bitte zuerst einen Reifensatz auswählen.")
        elif complete < 4:
            self.overall_status.setText("⚪  FAHRZEUGSTATUS UNVOLLSTÄNDIG")
            self.overall_status.setStyleSheet(self.STATUS_STYLES["neutral"])
            self.summary.setText(f"{complete} von 4 Reifen vollständig ausgewertet.")
        elif "red" in statuses:
            self.overall_status.setText("🔴  FAHRZEUGSTATUS SCHLECHT – DRUCK ANPASSEN")
            self.overall_status.setStyleSheet(self.STATUS_STYLES["red"])
            self.summary.setText("Mindestens ein Reifen liegt deutlich außerhalb des Zieldrucks.")
        elif "orange" in statuses:
            self.overall_status.setText("🟠  FAHRZEUGSTATUS FAHRBAR – OPTIMIERUNG EMPFOHLEN")
            self.overall_status.setStyleSheet(self.STATUS_STYLES["orange"])
            self.summary.setText("Alle Reifen sind fahrbar, mindestens ein Druck kann aber verbessert werden.")
        else:
            self.overall_status.setText("🟢  FAHRZEUGSTATUS PASSEND")
            self.overall_status.setStyleSheet(self.STATUS_STYLES["green"])
            self.summary.setText("Alle vier Reifen liegen innerhalb der Zieldruck-Toleranz.")


class SimpleMeasurementPage(QWidget):
    """Einfacher Rennbetrieb: automatisch vorausgewählt und nur die nächsten nötigen Aktionen sichtbar."""

    def __init__(self, database: Database, refresh_callback):
        super().__init__()
        self.database = database
        self.refresh_callback = refresh_callback

        root = QVBoxLayout(self)
        root.setContentsMargins(38, 30, 38, 30)
        root.setSpacing(18)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Rennbetrieb")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Alles Wichtige für die Boxengasse auf einer Seite.")
        subtitle.setObjectName("mutedText")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()

        self.change_selection = QPushButton("Auswahl ändern")
        self.change_selection.setCheckable(True)
        self.change_selection.clicked.connect(self._toggle_selection)
        header.addWidget(self.change_selection)
        root.addLayout(header)

        self.selection_card = QFrame()
        self.selection_card.setObjectName("contentCard")
        sel = QGridLayout(self.selection_card)
        sel.setContentsMargins(20, 18, 20, 18)
        sel.setHorizontalSpacing(12)
        sel.setVerticalSpacing(10)

        sel.addWidget(QLabel("Rennwochenende"), 0, 0)
        self.event_combo = QComboBox()
        self.event_combo.currentIndexChanged.connect(self._event_changed)
        sel.addWidget(self.event_combo, 0, 1)
        new_event = QPushButton("+ Neu")
        new_event.clicked.connect(self.new_event)
        sel.addWidget(new_event, 0, 2)

        sel.addWidget(QLabel("Session"), 1, 0)
        self.session_combo = QComboBox()
        self.session_combo.currentIndexChanged.connect(self._session_changed)
        sel.addWidget(self.session_combo, 1, 1)
        new_session = QPushButton("+ Neu")
        new_session.clicked.connect(self.new_session)
        sel.addWidget(new_session, 1, 2)

        sel.addWidget(QLabel("Reifensatz"), 2, 0)
        self.tyre_set_combo = QComboBox()
        self.tyre_set_combo.currentIndexChanged.connect(self._update_screen)
        sel.addWidget(self.tyre_set_combo, 2, 1)
        new_set = QPushButton("+ Neu")
        new_set.clicked.connect(self.new_tyre_set)
        sel.addWidget(new_set, 2, 2)

        root.addWidget(self.selection_card)
        self.selection_card.setVisible(False)

        self.current_card = QFrame()
        self.current_card.setObjectName("simpleHeroCard")
        current_layout = QVBoxLayout(self.current_card)
        current_layout.setContentsMargins(26, 22, 26, 22)
        current_layout.setSpacing(8)

        current_label = QLabel("AKTUELL")
        current_label.setObjectName("simpleEyebrow")
        current_layout.addWidget(current_label)

        self.current_event = QLabel("Noch kein Rennwochenende")
        self.current_event.setObjectName("simpleMainValue")
        self.current_event.setWordWrap(True)
        current_layout.addWidget(self.current_event)

        self.current_session = QLabel("")
        self.current_session.setObjectName("simpleSubValue")
        self.current_session.setWordWrap(True)
        current_layout.addWidget(self.current_session)

        self.current_set = QLabel("")
        self.current_set.setObjectName("simpleSubValue")
        self.current_set.setWordWrap(True)
        current_layout.addWidget(self.current_set)
        root.addWidget(self.current_card)

        self.next_card = QFrame()
        self.next_card.setObjectName("contentCard")
        next_layout = QVBoxLayout(self.next_card)
        next_layout.setContentsMargins(24, 22, 24, 22)
        next_layout.setSpacing(12)

        self.next_title = QLabel("Bereit")
        self.next_title.setObjectName("sectionTitle")
        next_layout.addWidget(self.next_title)

        self.next_text = QLabel("")
        self.next_text.setObjectName("mutedText")
        self.next_text.setWordWrap(True)
        next_layout.addWidget(self.next_text)

        self.next_button = QPushButton("")
        self.next_button.setObjectName("primaryButton")
        self.next_button.setMinimumHeight(58)
        next_layout.addWidget(self.next_button)

        root.addWidget(self.next_card)

        self.measurement_card = QFrame()
        self.measurement_card.setObjectName("contentCard")
        m = QVBoxLayout(self.measurement_card)
        m.setContentsMargins(24, 22, 24, 22)
        m.setSpacing(14)

        m_title = QHBoxLayout()
        heading = QLabel("Reifendruck erfassen")
        heading.setObjectName("sectionTitle")
        m_title.addWidget(heading)
        m_title.addStretch()
        self.progress_label = QLabel("0 / 4")
        self.progress_label.setObjectName("simpleProgress")
        m_title.addWidget(self.progress_label)
        m.addLayout(m_title)

        self.wheel_buttons = {}
        wheel_grid = QGridLayout()
        wheel_grid.setSpacing(12)
        for index, (position, label) in enumerate((
            ("FL", "VORNE LINKS"),
            ("FR", "VORNE RECHTS"),
            ("RL", "HINTEN LINKS"),
            ("RR", "HINTEN RECHTS"),
        )):
            button = QPushButton(label)
            button.setObjectName("wheelAction")
            button.setMinimumHeight(84)
            button.clicked.connect(lambda checked=False, pos=position: self.measure_tyre(pos))
            wheel_grid.addWidget(button, index // 2, index % 2)
            self.wheel_buttons[position] = button
        m.addLayout(wheel_grid)

        all_button = QPushButton("ALLE 4 NACHEINANDER MESSEN")
        all_button.setObjectName("primaryButton")
        all_button.setMinimumHeight(58)
        all_button.clicked.connect(self.measure_all)
        m.addWidget(all_button)

        result_button = QPushButton("Ergebnis ansehen")
        result_button.setMinimumHeight(46)
        result_button.clicked.connect(self._open_result)
        m.addWidget(result_button)

        root.addWidget(self.measurement_card)
        root.addStretch()

    def _toggle_selection(self):
        self.selection_card.setVisible(self.change_selection.isChecked())
        self.change_selection.setText(
            "Auswahl schließen" if self.change_selection.isChecked() else "Auswahl ändern"
        )

    def refresh(self):
        previous = self.event_combo.currentData()
        self.event_combo.blockSignals(True)
        self.event_combo.clear()
        for row in self.database.get_events():
            track = row["track_name"] if "track_name" in row.keys() else ""
            self.event_combo.addItem(f'{row["name"]} · {track}'.strip(" ·"), row["id"])
        self.event_combo.blockSignals(False)
        if previous is not None:
            idx = self.event_combo.findData(previous)
            if idx >= 0:
                self.event_combo.setCurrentIndex(idx)
        self._event_changed()

    def _event_changed(self):
        previous = self.session_combo.currentData()
        self.session_combo.blockSignals(True)
        self.session_combo.clear()
        event_id = self.event_combo.currentData()
        if event_id is not None:
            for row in self.database.get_sessions_for_event(int(event_id)):
                driver = " ".join(
                    x for x in (row["driver_first_name"], row["driver_last_name"]) if x
                ) or "Ohne Fahrer"
                car = f'{row["manufacturer"]} {row["model"]}'.strip() or "Ohne Fahrzeug"
                self.session_combo.addItem(
                    f'{row["session_type"]} · {driver} · {car}', row["id"]
                )
        self.session_combo.blockSignals(False)
        if previous is not None:
            idx = self.session_combo.findData(previous)
            if idx >= 0:
                self.session_combo.setCurrentIndex(idx)
        self._session_changed()

    def _session_changed(self):
        previous = self.tyre_set_combo.currentData()
        self.tyre_set_combo.blockSignals(True)
        self.tyre_set_combo.clear()
        session_id = self.session_combo.currentData()
        if session_id is not None:
            for row in self.database.get_tyre_sets_for_session(int(session_id)):
                number = row["set_number"] or row["id"]
                detail = " · ".join(
                    value for value in (row["manufacturer"], row["compound"]) if value
                )
                self.tyre_set_combo.addItem(
                    f'Reifensatz {number}' + (f' · {detail}' if detail else ""),
                    row["id"],
                )
        self.tyre_set_combo.blockSignals(False)
        if previous is not None:
            idx = self.tyre_set_combo.findData(previous)
            if idx >= 0:
                self.tyre_set_combo.setCurrentIndex(idx)
        self._update_screen()

    def _update_screen(self):
        event_text = self.event_combo.currentText().strip()
        session_text = self.session_combo.currentText().strip()
        set_text = self.tyre_set_combo.currentText().strip()

        self.current_event.setText(event_text or "Noch kein Rennwochenende")
        self.current_session.setText(session_text if session_text else "Noch keine Session")
        self.current_set.setText(set_text if set_text else "Noch kein Reifensatz")

        if self.event_combo.currentData() is None:
            self.next_card.setVisible(True)
            self.measurement_card.setVisible(False)
            self.next_title.setText("1 · Rennwochenende anlegen")
            self.next_text.setText("Einmal anlegen – danach bleibt es ausgewählt.")
            self.next_button.setText("RENNWOCHENENDE ANLEGEN")
            self._set_next_action(self.new_event)
            return

        if self.session_combo.currentData() is None:
            self.next_card.setVisible(True)
            self.measurement_card.setVisible(False)
            self.next_title.setText("2 · Session anlegen")
            self.next_text.setText("Fahrer, Fahrzeug und Session auswählen.")
            self.next_button.setText("SESSION ANLEGEN")
            self._set_next_action(self.new_session)
            return

        if self.tyre_set_combo.currentData() is None:
            self.next_card.setVisible(True)
            self.measurement_card.setVisible(False)
            self.next_title.setText("3 · Reifensatz anlegen")
            self.next_text.setText("Danach kannst du sofort mit der Messung beginnen.")
            self.next_button.setText("REIFENSATZ ANLEGEN")
            self._set_next_action(self.new_tyre_set)
            return

        self.next_card.setVisible(False)
        self.measurement_card.setVisible(True)
        self._refresh_measurement_progress()

    def _set_next_action(self, callback):
        try:
            self.next_button.clicked.disconnect()
        except Exception:
            pass
        self.next_button.clicked.connect(callback)

    def _refresh_measurement_progress(self):
        tyre_set_id = self.tyre_set_combo.currentData()
        measured = {}
        if tyre_set_id is not None:
            measured = {
                row["position"]: row
                for row in self.database.get_tyre_measurements(int(tyre_set_id))
            }
        count = len([p for p in ("FL", "FR", "RL", "RR") if p in measured])
        self.progress_label.setText(f"{count} / 4 gemessen")
        labels = {
            "FL": "VORNE LINKS",
            "FR": "VORNE RECHTS",
            "RL": "HINTEN LINKS",
            "RR": "HINTEN RECHTS",
        }
        for position, button in self.wheel_buttons.items():
            if position in measured:
                button.setText(f"✓  {labels[position]}\nMESSUNG VORHANDEN")
                button.setProperty("measured", True)
            else:
                button.setText(f"{labels[position]}\nMESSEN")
                button.setProperty("measured", False)
            button.style().unpolish(button)
            button.style().polish(button)

    def new_event(self):
        if EventDialog(self.database, parent=self).exec():
            self.refresh_callback()

    def new_session(self):
        event_id = self.event_combo.currentData()
        if event_id is None:
            return
        if SessionDialog(self.database, int(event_id), parent=self).exec():
            self.refresh_callback()

    def new_tyre_set(self):
        session_id = self.session_combo.currentData()
        if session_id is None:
            return
        if TyreSetDialog(self.database, int(session_id), parent=self).exec():
            self.refresh_callback()

    def measure_tyre(self, position: str) -> bool:
        tyre_set_id = self.tyre_set_combo.currentData()
        if tyre_set_id is None:
            return False
        accepted = TyreMeasurementDialog(
            self.database, int(tyre_set_id), position, self
        ).exec()
        if accepted:
            self.refresh_callback()
            self._refresh_measurement_progress()
        return bool(accepted)

    def measure_all(self):
        for position in ("FL", "FR", "RL", "RR"):
            if not self.measure_tyre(position):
                break

    def _open_result(self):
        window = self.window()
        if hasattr(window, "navigate_to"):
            window.navigate_to(1)


class MainWindow(QMainWindow):
    def __init__(
        self,
        update_client: UpdateClient | None = None,
        user_session: UserSession | None = None,
    ) -> None:
        super().__init__()
        self.update_client = update_client
        self.user_session = user_session
        user_suffix = (
            f" · {user_session.display_name} [{user_session.channel}]"
            if user_session is not None
            else " · Offline"
        )
        self.setWindowTitle(
            f"SORG Motorsport · GT Data Analyzer {APP_VERSION}{user_suffix}"
        )
        self.resize(1640, 960)
        self.setMinimumSize(1280, 760)

        database_path = writable_database_path()
        self.database = Database(database_path)
        self.cloud_sync = CloudSync(self.database, self.user_session) if self.user_session is not None else None
        self._cloud_sync_scheduled = False
        self.expert_authenticated = False
        self.current_page_index = 0

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        sidebar_layout = QVBoxLayout(sidebar)

        brand = QLabel()
        brand.setObjectName("brandImage")
        brand.setAlignment(Qt.AlignCenter)
        brand.setFixedHeight(104)

        logo_path = resource_path("sorg_full_logo.jpg")
        if logo_path.exists():
            logo_pixmap = QPixmap(str(logo_path))
            brand.setPixmap(
                logo_pixmap.scaled(
                    QSize(190, 92),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )
        else:
            brand.setText("SORG RENNSPORT")

        sidebar_layout.addWidget(brand)

        self.stack = QStackedWidget()

        self.dashboard_page = DashboardPage(self.database)
        self.quick_page = SimpleMeasurementPage(self.database, self.refresh_all)
        self.result_page = SimpleResultPage(self.database)
        self.events_page = EventsPage(self.database, self.refresh_all)

        self.cars_page = CrudTablePage(
            "Fahrzeuge",
            ("Startnr.", "Hersteller", "Modell", "Klasse", "PS", "Gewicht"),
            lambda: [
                (row["id"], (row["start_number"] or "", row["manufacturer"], row["model"], row["car_class"], row["horsepower"], row["weight_kg"]))
                for row in self.database.get_cars()
            ],
            self.add_car, self.edit_car, self.delete_car,
        )
        self.drivers_page = CrudTablePage(
            "Fahrer",
            ("Vorname", "Nachname", "Startnummer", "Lizenz"),
            lambda: [
                (row["id"], (row["first_name"], row["last_name"], row["race_number"], row["licence_class"]))
                for row in self.database.get_drivers()
            ],
            self.add_driver, self.edit_driver, self.delete_driver,
        )
        self.tracks_page = CrudTablePage(
            "Rennstrecken · Fahrer-Ziel-Heißdruck",
            ("Name", "Land", "Länge km", "Kurven", "Adresse"),
            lambda: [
                (row["id"], (row["name"], row["country"], row["length_km"], row["corners"], row["address"]))
                for row in self.database.get_tracks()
            ],
            self.add_track, self.edit_track, self.delete_track,
        )

        self.tyre_analysis_page = TyreAnalysisPage(self.database)
        self.session_comparison_page = SessionComparisonPage(self.database)
        self.reports_page = ReportsPage(self.database)

        self.analysis_hub = QTabWidget()
        self.analysis_hub.addTab(self.tyre_analysis_page, "Reifenanalyse")
        self.analysis_hub.addTab(self.session_comparison_page, "Sessionvergleich")
        self.analysis_hub.addTab(self.reports_page, "PDF-Berichte")

        self.master_data_hub = QTabWidget()
        self.master_data_hub.addTab(self.cars_page, "Fahrzeuge")
        self.master_data_hub.addTab(self.drivers_page, "Fahrer")
        self.master_data_hub.addTab(self.tracks_page, "Strecken & Zieldruck")

        navigation_label = QLabel("SCHNELLSTART")
        navigation_label.setObjectName("sidebarSection")
        sidebar_layout.addWidget(navigation_label)

        self.expert_hub = QTabWidget()
        self.expert_hub.addTab(self.dashboard_page, "Übersicht")
        self.expert_hub.addTab(self.events_page, "Rennevents")
        self.expert_hub.addTab(self.analysis_hub, "Auswertung")
        self.expert_hub.addTab(self.master_data_hub, "Stammdaten")

        pages = (
            ("🏁  Rennbetrieb", self.quick_page),
            ("✓  Ergebnis", self.result_page),
            ("⚙  Mehr / Experten", self.expert_hub),
        )

        self.navigation_buttons = []
        for index, (title, page) in enumerate(pages):
            button = QPushButton(title)
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.clicked.connect(lambda checked=False, i=index: self.navigate_to(i))
            sidebar_layout.addWidget(button)
            self.stack.addWidget(page)
            self.navigation_buttons.append(button)
            if index == 0:
                button.setChecked(True)
                self.stack.setCurrentIndex(0)

        sidebar_photo = QLabel()
        sidebar_photo.setObjectName("sidebarPhoto")
        sidebar_photo.setAlignment(Qt.AlignCenter)
        sidebar_photo.setMinimumHeight(120)

        sidebar_image = resource_path("motorsport_sidebar.jpg")

        if sidebar_image.exists():
            sidebar_pixmap = QPixmap(str(sidebar_image))
            sidebar_photo.setPixmap(
                sidebar_pixmap.scaled(
                    QSize(190, 120),
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation,
                )
            )

        sidebar_layout.addWidget(sidebar_photo)

        tools_label = QLabel("SERVICE")
        tools_label.setObjectName("sidebarSection")
        sidebar_layout.addWidget(tools_label)

        maps_button = QPushButton("📍 Strecke öffnen")
        maps_button.clicked.connect(self.open_selected_track_maps)
        sidebar_layout.addWidget(maps_button)

        update_button = QPushButton("🔄 Nach Updates suchen")
        update_button.setToolTip("Prüft GitHub auf eine neue Version des SORG GT Data Analyzers.")
        update_button.clicked.connect(
            lambda: self.update_client.check_and_prompt(
                self,
                self.user_session,
                manual=True,
            ) if self.update_client is not None else None
        )
        sidebar_layout.addWidget(update_button)

        if self.user_session is not None and self.user_session.role == "admin":
            users_button = QPushButton("👤 Benutzerverwaltung")
            users_button.clicked.connect(self.open_user_admin)
            sidebar_layout.addWidget(users_button)

            update_status_button = QPushButton("● Live Update-Status")
            update_status_button.setToolTip(
                "Admin-Liveansicht für Build, Release und Installer-Verfügbarkeit."
            )
            update_status_button.clicked.connect(
                lambda: webbrowser.open(
                    "https://paucki.github.io/SORG-GT-Data-Analyzer/update-status.html"
                )
            )
            sidebar_layout.addWidget(update_status_button)

        logout_button = QPushButton("↪ Abmelden")
        logout_button.clicked.connect(self.logout_user)
        sidebar_layout.addWidget(logout_button)

        sidebar_layout.addStretch()

        root.addWidget(sidebar)
        root.addWidget(self.stack, 1)

        refresh_action = QAction("Aktualisieren", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_all)
        self.addAction(refresh_action)

        self.statusBar().showMessage(f"Datenbank: {database_path}")

        self.refresh_all()
        if self.cloud_sync is not None and self.cloud_sync.enabled:
            QTimer.singleShot(1200, self.sync_cloud)
        if self.update_client is not None and self.user_session is not None:
            QTimer.singleShot(
                1500,
                lambda: self.update_client.check_and_prompt(
                    self,
                    self.user_session,
                    manual=False,
                ),
            )

    def open_user_admin(self):
        if self.user_session is None or self.user_session.role != "admin":
            QMessageBox.warning(self, "Benutzerverwaltung", "Nur Administratoren dürfen Benutzer verwalten.")
            return
        UserAdminDialog(self.user_session, self).exec()

    def logout_user(self):
        if QMessageBox.question(
            self,
            "Abmelden",
            "Möchtest du dich wirklich abmelden?",
        ) != QMessageBox.Yes:
            return
        if self.update_client is not None:
            self.update_client.clear_saved_session()
        try:
            remembered = APP_DATA_FOLDER / "remembered_user.txt"
            if remembered.exists():
                remembered.unlink()
        except Exception:
            pass
        try:
            subprocess.Popen([sys.executable, *sys.argv[1:]], shell=False)
        except Exception:
            pass
        QApplication.quit()

    def _load_expert_auth(self):
        try:
            if not EXPERT_AUTH_FILE.exists():
                return None
            return json.loads(EXPERT_AUTH_FILE.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _setup_expert_password(self) -> bool:
        password, ok = QInputDialog.getText(
            self,
            "Expertenmodus einrichten",
            "Beim ersten Öffnen bitte ein Expertenpasswort festlegen:",
            QLineEdit.Password,
        )
        if not ok or not password:
            return False
        confirm, ok = QInputDialog.getText(
            self,
            "Expertenmodus einrichten",
            "Passwort wiederholen:",
            QLineEdit.Password,
        )
        if not ok or confirm != password:
            QMessageBox.warning(self, "Expertenmodus", "Die Passwörter stimmen nicht überein.")
            return False
        salt = os.urandom(16)
        data = {
            "salt": base64.b64encode(salt).decode("ascii"),
            "hash": _expert_password_hash(password, salt),
        }
        APP_DATA_FOLDER.mkdir(parents=True, exist_ok=True)
        EXPERT_AUTH_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        QMessageBox.information(self, "Expertenmodus", "Expertenpasswort wurde gespeichert.")
        return True

    def _ensure_expert_login(self) -> bool:
        if self.expert_authenticated:
            return True
        auth = self._load_expert_auth()
        if not auth:
            if not self._setup_expert_password():
                return False
            auth = self._load_expert_auth()
        password, ok = QInputDialog.getText(
            self,
            "Experten-Anmeldung",
            "Expertenpasswort:",
            QLineEdit.Password,
        )
        if not ok:
            return False
        try:
            salt = base64.b64decode(auth["salt"])
            expected = auth["hash"]
        except Exception:
            QMessageBox.warning(self, "Expertenmodus", "Experten-Anmeldung konnte nicht gelesen werden.")
            return False
        if _expert_password_hash(password, salt) != expected:
            QMessageBox.warning(self, "Expertenmodus", "Falsches Expertenpasswort.")
            return False
        self.expert_authenticated = True
        self.statusBar().showMessage("Expertenmodus angemeldet")
        return True

    def navigate_to(self, index: int):
        if index == 2 and not self._ensure_expert_login():
            self.navigation_buttons[self.current_page_index].setChecked(True)
            return
        self.current_page_index = index
        self.stack.setCurrentIndex(index)
        page = self.stack.currentWidget()
        refresh = getattr(page, "refresh", None)
        if callable(refresh):
            refresh()

    def show_page(self, index: int):
        # Rückwärtskompatibilität für vorhandene Aufrufe.
        self.navigate_to(index)

    def refresh_all(self):
        for page in (
            self.dashboard_page,
            self.quick_page,
            self.result_page,
            self.events_page,
            self.tyre_analysis_page,
            self.session_comparison_page,
            self.reports_page,
            self.cars_page,
            self.drivers_page,
            self.tracks_page,
        ):
            refresh = getattr(page, "refresh", None)
            if callable(refresh):
                refresh()
        self.schedule_cloud_sync()

    def schedule_cloud_sync(self):
        if self.cloud_sync is None or not self.cloud_sync.enabled or self._cloud_sync_scheduled:
            return
        self._cloud_sync_scheduled = True
        QTimer.singleShot(700, self.sync_cloud)

    def sync_cloud(self):
        self._cloud_sync_scheduled = False
        if self.cloud_sync is None or not self.cloud_sync.enabled:
            return
        try:
            self.cloud_sync.sync()
            self.statusBar().showMessage("Cloud synchronisiert", 2500)
        except Exception as error:
            self.statusBar().showMessage(f"Cloud-Sync nicht möglich: {error}", 6000)

    def add_car(self):
        if CarDialog(self.database, parent=self).exec():
            self.refresh_all()

    def edit_car(self, car_id: int):
        if CarDialog(self.database, car_id, self).exec():
            self.refresh_all()

    def delete_car(self, car_id: int):
        self._delete_with_confirmation(
            "Fahrzeug",
            lambda: self.database.delete_car(car_id),
        )

    def add_driver(self):
        if DriverDialog(self.database, parent=self).exec():
            self.refresh_all()

    def edit_driver(self, driver_id: int):
        if DriverDialog(self.database, driver_id, self).exec():
            self.refresh_all()

    def delete_driver(self, driver_id: int):
        self._delete_with_confirmation(
            "Fahrer",
            lambda: self.database.delete_driver(driver_id),
        )

    def add_track(self):
        if TrackDialog(self.database, parent=self).exec():
            self.refresh_all()

    def edit_track(self, track_id: int):
        if TrackDialog(self.database, track_id, self).exec():
            self.refresh_all()

    def delete_track(self, track_id: int):
        self._delete_with_confirmation(
            "Strecke",
            lambda: self.database.delete_track(track_id),
        )

    def _delete_with_confirmation(self, title: str, callback):
        answer = QMessageBox.question(
            self,
            f"{title} löschen",
            f"{title} wirklich löschen?",
        )
        if answer != QMessageBox.Yes:
            return

        try:
            callback()
        except Exception as error:
            QMessageBox.critical(
                self,
                "Löschen fehlgeschlagen",
                str(error),
            )
            return

        self.refresh_all()

    def open_selected_track_maps(self):
        track_id = self.tracks_page.selected_id()
        if track_id is None:
            QMessageBox.information(
                self,
                "Strecke auswählen",
                "Öffne die Seite Strecken und wähle eine Strecke aus.",
            )
            return

        track = self.database.get_track(track_id)
        if not track:
            return

        if track["latitude"] is not None and track["longitude"] is not None:
            query = f'{track["latitude"]},{track["longitude"]}'
        elif track["address"]:
            query = track["address"]
        else:
            query = track["name"]

        webbrowser.open(
            "https://www.google.com/maps/search/?api=1&query="
            + quote(str(query))
        )

    def closeEvent(self, event):
        self.database.close()
        super().closeEvent(event)


class NuerburgringSplash(QWidget):
    """Klassischer SORG Startbildschirm mit korrekter Nordschleifenform."""

    ROUTE = [
        (52, 168), (66, 148), (72, 137), (84, 129), (101, 118), (118, 108),
        (138, 97), (151, 88), (139, 82), (158, 74), (174, 57), (180, 42),
        (178, 28), (168, 19), (155, 18), (145, 24), (130, 22), (116, 25),
        (106, 18), (104, 5), (99, 4), (97, 13), (88, 17), (77, 12),
        (66, 13), (55, 22), (49, 34), (48, 48), (39, 61), (27, 70),
        (34, 82), (37, 99), (45, 113), (57, 124), (68, 133), (63, 145),
        (57, 154), (52, 168),
    ]

    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(900, 520)
        self.progress = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._advance_car)
        self.track_pixmap = QPixmap()
        self.track_pixmap.loadFromData(
            base64.b64decode(NORDSCHLEIFE_TRACK_B64),
            "PNG",
        )

        screen = QApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            self.move(
                area.x() + (area.width() - self.width()) // 2,
                area.y() + (area.height() - self.height()) // 2,
            )

    def start(self):
        self.show()
        self.raise_()
        self._timer.start()

    def _advance_car(self):
        self.progress = (self.progress + 0.0036) % 1.0
        self.update()

    def _route_point(self, rect: QRectF) -> tuple[QPointF, float]:
        points = self.ROUTE
        pos = self.progress * (len(points) - 1)
        i = min(int(pos), len(points) - 2)
        t = pos - i
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        px = rect.left() + (x / 204.0) * rect.width()
        py = rect.top() + (y / 192.0) * rect.height()
        angle = -__import__("math").degrees(
            __import__("math").atan2(y2 - y1, x2 - x1)
        )
        return QPointF(px, py), angle

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#06080b"))

        # Dezenter roter Hintergrundakzent wie im ursprünglichen Startscreen.
        painter.setBrush(QBrush(QColor(60, 10, 18, 150)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(500, 35, 390, 390))

        painter.setPen(QColor("#ffffff"))
        brand_font = QFont("Segoe UI", 30, QFont.Black)
        brand_font.setLetterSpacing(QFont.AbsoluteSpacing, 2.5)
        painter.setFont(brand_font)
        painter.drawText(
            QRectF(54, 35, 350, 55),
            Qt.AlignLeft | Qt.AlignVCenter,
            "SORG",
        )

        painter.setPen(QColor("#e21b2d"))
        gt_font = QFont("Segoe UI", 15, QFont.Black)
        gt_font.setLetterSpacing(QFont.AbsoluteSpacing, 4.0)
        painter.setFont(gt_font)
        painter.drawText(
            QRectF(54, 82, 350, 36),
            Qt.AlignLeft | Qt.AlignVCenter,
            "GT DATA ANALYZER",
        )

        painter.setPen(QColor("#8e98a5"))
        sub_font = QFont("Segoe UI", 10, QFont.Bold)
        sub_font.setLetterSpacing(QFont.AbsoluteSpacing, 2.0)
        painter.setFont(sub_font)
        painter.drawText(
            QRectF(54, 120, 420, 28),
            Qt.AlignLeft | Qt.AlignVCenter,
            "NÜRBURGRING NORDSCHLEIFE · RENNBETRIEB",
        )

        # Richtige Nordschleife aus der vom Nutzer bereitgestellten Referenz.
        target = QRectF(300, 145, 535, 255)
        draw_rect = target
        if not self.track_pixmap.isNull():
            scaled = self.track_pixmap.scaled(
                QSize(int(target.width()), int(target.height())),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            draw_rect = QRectF(
                target.center().x() - scaled.width() / 2,
                target.center().y() - scaled.height() / 2,
                scaled.width(),
                scaled.height(),
            )
            painter.drawPixmap(draw_rect.toRect(), scaled)

        # Animierter Wagen bleibt erhalten.
        car, angle = self._route_point(draw_rect)
        painter.save()
        painter.translate(car)
        painter.rotate(angle)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#e21b2d"))
        painter.drawRoundedRect(QRectF(-17, -8, 34, 16), 5, 5)
        painter.setBrush(QColor("#f3f5f7"))
        painter.drawRoundedRect(QRectF(-7, -11, 14, 7), 3, 3)
        painter.setBrush(QColor("#050607"))
        painter.drawRoundedRect(QRectF(-15, -10, 6, 4), 1.5, 1.5)
        painter.drawRoundedRect(QRectF(9, -10, 6, 4), 1.5, 1.5)
        painter.drawRoundedRect(QRectF(-15, 6, 6, 4), 1.5, 1.5)
        painter.drawRoundedRect(QRectF(9, 6, 6, 4), 1.5, 1.5)
        painter.restore()

        painter.setPen(QColor("#ffffff"))
        title_font = QFont("Segoe UI", 22, QFont.Black)
        painter.setFont(title_font)
        painter.drawText(
            QRectF(54, 430, 530, 42),
            Qt.AlignLeft | Qt.AlignVCenter,
            "Willkommen im Rennwochenende",
        )

        painter.setPen(QColor("#838d99"))
        status_font = QFont("Segoe UI", 10, QFont.DemiBold)
        painter.setFont(status_font)
        painter.drawText(
            QRectF(55, 473, 500, 24),
            Qt.AlignLeft | Qt.AlignVCenter,
            "Fahrzeug- und Teamdaten werden vorbereitet …",
        )

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#222830"))
        painter.drawRoundedRect(QRectF(615, 462, 225, 5), 2.5, 2.5)
        painter.setBrush(QColor("#e21b2d"))
        width = 225 * ((self.progress * 2.4) % 1.0)
        painter.drawRoundedRect(QRectF(615, 462, width, 5), 2.5, 2.5)


def show_nuerburgring_splash(duration_ms: int = 2300):
    splash = NuerburgringSplash()
    loop = QEventLoop()
    QTimer.singleShot(duration_ms, loop.quit)
    splash.start()
    loop.exec()
    splash._timer.stop()
    splash.close()
    QApplication.processEvents()


def apply_style(application: QApplication) -> None:
    application.setFont(QFont("Segoe UI", 10))
    application.setStyleSheet(
        """
        QMainWindow, QWidget {
            background: #090b0f;
            color: #f4f4f5;
        }


        #brandImage {
            background: #090a0c;
            border-bottom: 1px solid #2b2d31;
            padding: 4px;
        }

        #eventHeroGlass {
            background: rgba(4, 5, 7, 220);
            border: 1px solid rgba(255,255,255,35);
            border-radius: 9px;
        }

        #eventHeroMainTitle {
            color: white;
            font-size: 29px;
            font-weight: 900;
        }

        #eventHeroMainSub {
            color: #f5f5f5;
            font-size: 18px;
        }

        #eventHeroInfo {
            color: #d1d5db;
            font-size: 12px;
        }

        #compactFilterBar {
            background: #101114;
            border: 1px solid #303238;
            border-radius: 8px;
        }

        #panel {
            background: #0e0f12;
            border: 1px solid #303238;
            border-radius: 8px;
        }

        #sectionRed {
            color: #ef2b31;
            font-size: 11px;
            font-weight: 900;
        }

        #countBadge {
            color: white;
            background: #8e1b20;
            border-radius: 8px;
            padding: 2px 7px;
            font-weight: 800;
        }

        #eventCard, #eventCardSelected {
            background: #15171b;
            border: 1px solid #292c32;
            border-radius: 8px;
        }

        #eventCard:hover {
            border-color: #7f1d1d;
            background: #1a1c21;
        }

        #eventCardSelected {
            border: 2px solid #ef2b31;
            background: #19191c;
        }

        #eventCardTitle {
            color: white;
            font-size: 14px;
            font-weight: 800;
        }

        #eventMeta {
            color: #d1d5db;
            font-size: 10px;
        }

        #sessionBadge {
            color: #86efac;
            background: #101612;
            border: 1px solid #214b2c;
            border-radius: 5px;
            padding: 2px 5px;
            font-size: 9px;
        }

        #eventThumb {
            background: #08090b;
            border: 1px solid #34363b;
            border-radius: 6px;
        }

        #zoomButton {
            background: #17191e;
            border: 1px solid #3b3e45;
            border-radius: 6px;
            padding: 2px;
            text-align: center;
            font-weight: 800;
        }

        #zoomButton:hover {
            background: #991b1b;
            border-color: #ef4444;
        }

        #mainPreview {
            background: #07080a;
            border: 1px solid #34363b;
            border-radius: 7px;
        }

        #metricCard {
            color: #e5e7eb;
            background: #111214;
            border: 1px solid #303238;
            border-radius: 7px;
            padding: 10px;
            font-size: 10px;
        }

        #metricCard b {
            color: #ef2b31;
        }

        #primaryRed {
            background: #a6191e;
            border-color: #ef2b31;
        }

        #filterReset {
            background: #111214;
            border: 1px solid #ef2b31;
            color: white;
        }

        QToolTip {
            background: #172033;
            color: white;
            border: 1px solid #334155;
        }

        #sidebar {
            background: #0c0d10;
            border-right: 1px solid #292b31;
        }

        #brand {
            font-size: 20px;
            font-weight: 900;
            color: white;
            padding: 20px 10px 0 10px;
            letter-spacing: 2px;
            border-bottom: 3px solid #d81f26;
        }

        #brandSubtitle {
            color: #94a3b8;
            padding: 0 8px 22px 8px;
        }

        #pageTitle {
            font-size: 26px;
            font-weight: 800;
            padding: 8px;
        }

        #eventHeroTitle {
            font-size: 24px;
            font-weight: 900;
            color: white;
            background: rgba(0, 0, 0, 155);
            border-left: 4px solid #dc2626;
            padding: 4px 10px;
        }

        #eventHeroSubtitle {
            font-size: 12px;
            color: #e5e7eb;
            background: rgba(0, 0, 0, 155);
            padding: 4px 10px;
        }

        #heroPanel {
            background: #172554;
            border: 1px solid #37588a;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 10px;
        }

        #heroTextPanel {
            background: rgba(4, 6, 10, 205);
            border: 1px solid rgba(255, 255, 255, 45);
            border-left: 5px solid #dc2626;
            border-radius: 10px;
        }

        #heroTitle {
            font-size: 31px;
            font-weight: 900;
            color: #ffffff;
            background: transparent;
            padding: 0;
            letter-spacing: 1px;
        }

        #heroAccent {
            background: #dc2626;
            border: none;
            border-radius: 2px;
        }

        #heroSubtitle {
            font-size: 13px;
            font-weight: 500;
            color: #e5e7eb;
            background: transparent;
            padding: 2px 0 0 0;
        }

        #simpleHeroCard {
            background: #11151a;
            border: 1px solid #303640;
            border-left: 5px solid #dc2626;
            border-radius: 16px;
        }

        #simpleEyebrow {
            color: #dc2626;
            font-size: 10px;
            font-weight: 900;
            letter-spacing: 2px;
        }

        #simpleMainValue {
            color: #ffffff;
            font-size: 24px;
            font-weight: 900;
            padding-top: 4px;
        }

        #simpleSubValue {
            color: #aeb6c2;
            font-size: 13px;
        }

        #simpleProgress {
            color: #ffffff;
            background: #20242b;
            border: 1px solid #343b45;
            border-radius: 14px;
            padding: 6px 10px;
            font-weight: 800;
        }

        QPushButton#wheelAction {
            background: #14181d;
            border: 1px solid #363d47;
            border-radius: 12px;
            color: #ffffff;
            font-size: 13px;
            font-weight: 900;
            text-align: center;
        }

        QPushButton#wheelAction:hover {
            border: 1px solid #dc2626;
            background: #1a1f25;
        }

        QPushButton#wheelAction[measured="true"] {
            background: #153524;
            border: 1px solid #2f9f63;
            color: #eafff0;
        }

        #sidebarSection {
            color: #64748b;
            font-size: 10px;
            font-weight: 800;
            padding: 16px 10px 5px 10px;
        }

        #sidebarPhoto {
            background: #0b1220;
            border: 1px solid #26344d;
            border-radius: 11px;
            margin: 8px;
        }

        #dashboardCard {
            background: #111a2d;
            border: 1px solid #2c3c5a;
            border-radius: 15px;
            min-width: 170px;
            min-height: 150px;
            padding: 10px;
        }

        #dashboardCard:hover {
            background: #17233a;
            border-color: #3b82f6;
        }

        #dashboardIcon {
            font-size: 28px;
        }

        #dashboardLabel {
            color: #cbd5e1;
            font-size: 12px;
        }

        #dashboardValue {
            font-size: 34px;
            font-weight: 800;
        }

        #filterFrame {
            background: #101114;
            border: 1px solid #303238;
            border-radius: 9px;
            padding: 4px;
        }

        #filterFrame QLabel {
            color: #94a3b8;
            font-size: 9px;
        }

        #filterFrame QLineEdit,
        #filterFrame QComboBox {
            min-height: 24px;
            max-height: 30px;
            padding: 2px 7px;
            font-size: 9px;
            border-radius: 5px;
        }

        #filterFrame QPushButton {
            min-height: 25px;
            padding: 3px 8px;
            font-size: 9px;
        }

        #filterFrame QCheckBox {
            color: #cbd5e1;
            font-size: 9px;
        }

        QPushButton {
            background: #1b1d22;
            border: 1px solid #3a3d44;
            border-radius: 9px;
            padding: 10px 14px;
            text-align: left;
            font-weight: 600;
        }

        QPushButton:hover {
            background: #2a2d33;
            border-color: #dc2626;
        }

        QPushButton:checked {
            background: #991b1b;
            border-color: #ef4444;
            color: white;
        }

        #analysisSubtitle {
            color: #9ca3af;
            font-size: 11px;
            padding-left: 8px;
        }

        #analysisCard {
            background: #111318;
            border: 1px solid #303238;
            border-left: 3px solid #dc2626;
            border-radius: 9px;
            min-height: 92px;
        }

        #analysisCardLabel {
            color: #9ca3af;
            font-size: 9px;
            font-weight: 800;
        }

        #analysisCardValue {
            color: #ffffff;
            font-size: 23px;
            font-weight: 900;
        }

        #analysisCardDetail {
            color: #6b7280;
            font-size: 9px;
        }

        #analysisRecommendation {
            background: #15171c;
            border: 1px solid #3f424a;
            border-left: 5px solid #dc2626;
            border-radius: 10px;
            padding: 8px;
        }

        #analysisRecommendationValue {
            color: #ffffff;
            font-size: 30px;
            font-weight: 900;
        }

        #analysisRecommendationText {
            color: #d1d5db;
            font-size: 11px;
        }

        #comparisonSessionCard {
            background: #111318;
            border: 1px solid #303238;
            border-top: 4px solid #dc2626;
            border-radius: 10px;
            min-height: 155px;
        }

        #comparisonSessionTitle {
            color: #ffffff;
            font-size: 20px;
            font-weight: 900;
        }

        #comparisonRecommendation {
            background: #15171c;
            border: 1px solid #3f424a;
            border-left: 5px solid #dc2626;
            border-radius: 10px;
            padding: 8px;
        }

        #comparisonRecommendationTitle {
            color: #ffffff;
            font-size: 21px;
            font-weight: 900;
        }

        #reportSelectionPanel {
            background: #111318;
            border: 1px solid #303238;
            border-left: 4px solid #dc2626;
            border-radius: 10px;
            padding: 8px;
        }

        #reportPreviewPanel {
            background: #111318;
            border: 1px solid #303238;
            border-top: 4px solid #dc2626;
            border-radius: 10px;
            padding: 10px;
        }

        #reportPreviewTitle {
            color: #ffffff;
            font-size: 24px;
            font-weight: 900;
        }

        #reportInfoPanel {
            background: #15171c;
            border: 1px solid #303238;
            border-radius: 9px;
            padding: 6px;
        }

        #primaryActionButton {
            background: #991b1b;
            border: 1px solid #ef4444;
            font-size: 12px;
            font-weight: 900;
            text-align: center;
            padding: 10px 18px;
        }

        #primaryActionButton:hover {
            background: #b91c1c;
        }

        QTabWidget::pane {
            border: 1px solid #303238;
            border-radius: 8px;
            background: #101114;
        }

        QTabBar::tab {
            background: #17191e;
            border: 1px solid #303238;
            padding: 8px 18px;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background: #991b1b;
            border-color: #ef4444;
        }

        #accountPanel {
            background: #111318;
            border: 1px solid #303238;
            border-left: 3px solid #dc2626;
            border-radius: 9px;
            margin: 6px;
        }

        #accountTitle {
            color: #ffffff;
            font-size: 11px;
            font-weight: 900;
        }

        #accountDetail {
            color: #9ca3af;
            font-size: 9px;
        }

        #dangerButton {
            background: #991b1b;
            border-color: #dc2626;
        }

        #dangerButton:hover {
            background: #b91c1c;
        }

        QTreeWidget, QTableWidget {
            background: #101114;
            alternate-background-color: #17181c;
            border: 1px solid #303238;
            border-radius: 10px;
            gridline-color: #26344d;
            padding: 4px;
        }

        QTreeWidget::item {
            min-height: 39px;
            padding: 6px 8px;
            font-size: 12px;
        }

        QTreeWidget QHeaderView::section {
            min-height: 34px;
            font-size: 11px;
            font-weight: 700;
        }

        QTreeWidget::item:selected,
        QTableWidget::item:selected {
            background: #9f1d24;
            color: white;
            border-left: 3px solid #ff3b30;
        }

        #detailsPanel {
            background: #101114;
            border: 1px solid #303238;
            border-radius: 12px;
            min-width: 360px;
        }

        #detailsTitle {
            font-size: 20px;
            font-weight: 800;
            padding: 8px;
        }

        #previewLabel {
            background: #0b1220;
            border: 1px dashed #334155;
            border-radius: 10px;
            color: #94a3b8;
            font-size: 34px;
            padding: 10px;
        }

        #detailsText {
            color: #dbeafe;
            font-size: 12px;
            line-height: 1.5;
        }

        QHeaderView::section {
            background: #172033;
            color: #f8fafc;
            border: none;
            border-right: 1px solid #26344d;
            padding: 8px;
        }

        QLineEdit, QTextEdit, QComboBox, QDateEdit,
        QSpinBox, QDoubleSpinBox {
            background: #f8fafc;
            color: #111827;
            border: 1px solid #94a3b8;
            border-radius: 5px;
            padding: 6px;
        }

        QDialog {
            background: #0f172a;
        }
        """
    )


    application.setStyleSheet(application.styleSheet() + """
        QMainWindow, QWidget { background: #080a0d; color: #f7f8fa; }
        #sidebar { background: #0b0e12; border-right: 1px solid #262b32; }
        #brandImage { background: #0b0e12; border-bottom: 1px solid #262b32; padding: 8px; }
        #sidebarSection { color: #77818d; font-size: 9px; font-weight: 900; padding: 18px 12px 6px 12px; letter-spacing: 1px; }
        QPushButton {
            background: transparent; border: 1px solid transparent; border-radius: 10px;
            padding: 10px 13px; color: #d9dde2; text-align: left; font-weight: 650;
        }
        QPushButton:hover { background: #15191f; border-color: #2c333c; }
        QPushButton:checked { background: #1a1115; border-color: #7e202a; color: #ffffff; }
        #pageTitle { color: #ffffff; font-size: 25px; font-weight: 900; padding: 10px 6px; }
        #dashboardCard, #analysisCard, #comparisonSessionCard, #reportSelectionPanel,
        #reportPreviewPanel, #detailsPanel, #panel, #simpleHeroCard {
            background: #11151a; border: 1px solid #2a3038; border-radius: 14px;
        }
        #dashboardCard:hover { background: #151a20; border-color: #7e202a; }
        #dashboardValue { color: #ffffff; font-size: 32px; font-weight: 900; }
        #dashboardLabel { color: #9aa3ad; font-size: 11px; }
        QTreeWidget, QTableWidget {
            background: #0e1115; alternate-background-color: #12161b;
            border: 1px solid #2a3038; border-radius: 12px; gridline-color: #20262d; padding: 5px;
        }
        QHeaderView::section {
            background: #14191f; color: #cfd5dc; border: none; border-right: 1px solid #252c34;
            padding: 9px; font-weight: 800;
        }
        QTreeWidget::item:selected, QTableWidget::item:selected { background: #7f1d27; color: #ffffff; }
        QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
            background: #0d1014; color: #f5f7f9; border: 1px solid #333a44;
            border-radius: 8px; padding: 7px 9px; selection-background-color: #9f2230;
        }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus,
        QSpinBox:focus, QDoubleSpinBox:focus { border-color: #a52a35; }
        QTabWidget::pane { background: #0e1115; border: 1px solid #292f37; border-radius: 11px; }
        QTabBar::tab { background: #10141a; border: 1px solid #292f37; padding: 9px 17px; margin-right: 3px; border-radius: 7px; }
        QTabBar::tab:selected { background: #7f1d27; border-color: #a72b38; }
        #heroTextPanel { background: rgba(7, 9, 12, 225); border: 1px solid rgba(255,255,255,28); border-left: 4px solid #e21b2d; border-radius: 12px; }
        #primaryActionButton, #primaryRed { background: #b51f2e; border: 1px solid #e21b2d; color: #ffffff; }
        QStatusBar { background: #090c10; color: #7f8994; border-top: 1px solid #20262c; }
        QToolTip { background: #151a20; color: #f4f6f8; border: 1px solid #333a44; padding: 5px; }
    """)


def main() -> int:
    # Windows: eigenes App-Symbol auch in Taskleiste/Alt-Tab verwenden.
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "SORG.Rennsport.GTDataAnalyzer"
            )
        except Exception:
            pass

    application = QApplication(sys.argv)

    app_icon_path = resource_path("sorg_gt.ico")
    if app_icon_path.exists():
        app_icon = QIcon(str(app_icon_path))
        application.setWindowIcon(app_icon)
    else:
        app_icon = QIcon()

    apply_style(application)
    show_nuerburgring_splash()

    try:
        update_client = UpdateClient(
            app_name=APP_NAME,
            current_version=APP_VERSION,
            data_folder=APP_DATA_FOLDER,
        )

        user_session = update_client.restore_saved_session()

        if user_session is None:
            login = LoginDialog(update_client)
            result = login.exec()

            if result == LoginDialog.Rejected:
                return 0

            user_session = login.user_session

        window = MainWindow(
            update_client=update_client,
            user_session=user_session,
        )
        if not app_icon.isNull():
            window.setWindowIcon(app_icon)
        window.show()
        return application.exec()
    except Exception as error:
        QMessageBox.critical(None, "Startfehler", str(error))
        raise


if __name__ == "__main__":
    raise SystemExit(main())
