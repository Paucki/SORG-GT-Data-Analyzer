from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import os
import secrets
import subprocess
import tempfile
import urllib.error
import urllib.request

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

LATEST_URL = "https://raw.githubusercontent.com/Paucki/SORG-GT-Data-Analyzer/main/update/latest.json"
ACCOUNT_SERVER_URL = os.environ.get("SORG_ACCOUNT_SERVER_URL", "").strip().rstrip("/")


@dataclass
class UserSession:
    username: str = ""
    display_name: str = ""
    role: str = "user"
    channel: str = "stable"
    token: str = ""


class LoginDialog(QDialog):
    """Start-Anmeldung. Funktioniert lokal und optional gegen den SORG-Account-Server."""

    def __init__(self, update_client, parent=None):
        super().__init__(parent)
        self.update_client = update_client
        self.user_session: UserSession | None = None
        self.setWindowTitle("SORG GT Data Analyzer · Anmeldung")
        self.setModal(True)
        self.resize(440, 300)

        root = QVBoxLayout(self)
        title = QLabel("SORG GT DATA ANALYZER")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: white; padding: 12px;")
        root.addWidget(title)

        subtitle = QLabel("Bitte anmelden, um die Anwendung zu starten.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #aeb6c2; margin-bottom: 12px;")
        root.addWidget(subtitle)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Benutzername")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Passwort")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.returnPressed.connect(self.try_login)

        form = QFormLayout()
        form.addRow("Benutzername", self.username)
        form.addRow("Passwort", self.password)
        root.addLayout(form)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color: #f59e0b;")
        root.addWidget(self.status)

        buttons = QHBoxLayout()
        self.setup_button = QPushButton("Ersten Benutzer anlegen")
        self.setup_button.clicked.connect(self.create_first_user)
        self.login_button = QPushButton("Anmelden")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.try_login)
        cancel = QPushButton("Beenden")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(self.setup_button)
        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(self.login_button)
        root.addLayout(buttons)

        self._refresh_mode()

    @property
    def account_file(self) -> Path:
        return self.update_client.data_folder / "local_accounts.json"

    def _refresh_mode(self):
        if ACCOUNT_SERVER_URL:
            self.status.setText("Online-Anmeldung aktiviert.")
            self.setup_button.setVisible(False)
            return
        if self.account_file.exists():
            self.status.setText("Lokale Anmeldung.")
            self.setup_button.setVisible(False)
        else:
            self.status.setText("Noch kein lokaler Benutzer vorhanden. Lege zuerst einen Benutzer an.")
            self.setup_button.setVisible(True)

    @staticmethod
    def _hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
        salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 240_000)
        return digest.hex(), salt.hex()

    def create_first_user(self):
        if ACCOUNT_SERVER_URL:
            QMessageBox.information(self, "Anmeldung", "Benutzer werden über den Account-Server verwaltet.")
            return
        username = self.username.text().strip()
        password = self.password.text()
        if len(username) < 3:
            QMessageBox.warning(self, "Benutzer anlegen", "Benutzername muss mindestens 3 Zeichen haben.")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "Benutzer anlegen", "Passwort muss mindestens 6 Zeichen haben.")
            return
        digest, salt = self._hash_password(password)
        self.update_client.data_folder.mkdir(parents=True, exist_ok=True)
        data = {"users": [{
            "username": username,
            "display_name": username,
            "role": "admin",
            "channel": "stable",
            "password_hash": digest,
            "password_salt": salt,
        }]}
        self.account_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        QMessageBox.information(self, "Benutzer angelegt", "Der erste Benutzer wurde als Administrator angelegt.")
        self._refresh_mode()
        self.try_login()

    def _local_login(self, username: str, password: str) -> UserSession:
        if not self.account_file.exists():
            raise RuntimeError("Noch kein lokaler Benutzer vorhanden.")
        data = json.loads(self.account_file.read_text(encoding="utf-8"))
        for user in data.get("users", []):
            if user.get("username", "").lower() != username.lower():
                continue
            digest, _ = self._hash_password(password, user["password_salt"])
            if not secrets.compare_digest(digest, user["password_hash"]):
                break
            return UserSession(
                username=user["username"],
                display_name=user.get("display_name") or user["username"],
                role=user.get("role", "user"),
                channel=user.get("channel", "stable"),
            )
        raise RuntimeError("Benutzername oder Passwort ist falsch.")

    def _online_login(self, username: str, password: str) -> UserSession:
        body = json.dumps({
            "username": username,
            "password": password,
            "client_version": self.update_client.current_version,
            "platform": "windows",
        }).encode("utf-8")
        request = urllib.request.Request(
            ACCOUNT_SERVER_URL + "/api/login",
            data=body,
            headers={"Content-Type": "application/json", "User-Agent": "SORG-GT-Data-Analyzer"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            try:
                detail = json.loads(error.read().decode("utf-8")).get("detail", str(error))
            except Exception:
                detail = str(error)
            raise RuntimeError(detail) from error
        return UserSession(
            username=data.get("username", username),
            display_name=data.get("display_name", username),
            role=data.get("role", "user"),
            channel=data.get("channel", "stable"),
            token=data.get("token", ""),
        )

    def try_login(self):
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            self.status.setText("Bitte Benutzername und Passwort eingeben.")
            return
        self.login_button.setEnabled(False)
        try:
            session = self._online_login(username, password) if ACCOUNT_SERVER_URL else self._local_login(username, password)
        except Exception as error:
            self.status.setText(str(error))
            self.login_button.setEnabled(True)
            return
        self.user_session = session
        self.accept()


class UpdateClient:
    def __init__(self, app_name: str, current_version: str, data_folder):
        self.app_name = app_name
        self.current_version = current_version
        self.data_folder = Path(data_folder)
        self.data_folder.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _version_tuple(value):
        parts = []
        for section in str(value).lstrip("vV").split("."):
            digits = "".join(ch for ch in section if ch.isdigit())
            parts.append(int(digits or 0))
        return tuple((parts + [0, 0, 0])[:3])

    def fetch_latest(self):
        request = urllib.request.Request(LATEST_URL, headers={"User-Agent": "SORG-GT-Data-Analyzer"})
        with urllib.request.urlopen(request, timeout=8) as response:
            return json.loads(response.read().decode("utf-8-sig"))

    def check_and_prompt(self, parent, user_session=None, manual=False):
        try:
            info = self.fetch_latest()
        except Exception as error:
            if manual:
                QMessageBox.warning(parent, "Update-Prüfung", f"Update-Prüfung nicht möglich:\n{error}")
            return
        latest = str(info.get("version", "0"))
        if self._version_tuple(latest) <= self._version_tuple(self.current_version):
            if manual:
                QMessageBox.information(parent, "Update-Prüfung", f"Version {self.current_version} ist aktuell.")
            return
        notes = str(info.get("notes", "")).replace(" | ", "\n• ")
        answer = QMessageBox.question(
            parent,
            "Update verfügbar",
            f"Version {latest} ist verfügbar.\n\n• {notes}\n\nUpdate jetzt herunterladen?",
        )
        if answer == QMessageBox.Yes:
            self.download_and_start(parent, info)

    def download_and_start(self, parent, info):
        url = info.get("url")
        expected = (info.get("sha256") or "").lower().strip()
        if not url:
            return
        try:
            target = Path(tempfile.gettempdir()) / "SORG_GT_Data_Analyzer_Setup.exe"
            urllib.request.urlretrieve(url, target)
            if expected:
                actual = hashlib.sha256(target.read_bytes()).hexdigest().lower()
                if actual != expected:
                    raise RuntimeError("SHA256-Prüfsumme stimmt nicht.")
            subprocess.Popen([str(target)], shell=False)
            QMessageBox.information(parent, "Update", "Installer wurde gestartet. Die App kann jetzt geschlossen werden.")
        except Exception as error:
            QMessageBox.critical(parent, "Update fehlgeschlagen", str(error))
