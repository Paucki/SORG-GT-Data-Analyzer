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
import urllib.parse
import urllib.request

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

LATEST_URL = "https://raw.githubusercontent.com/Paucki/SORG-GT-Data-Analyzer/main/update/latest.json"
ACCOUNT_SERVER_URL = os.environ.get("SORG_ACCOUNT_SERVER_URL", "").strip().rstrip("/")
SUPABASE_URL = "https://cdhfmhxhhtqqoetlferj.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_r9xkC56K3zezl30297f1qQ_fsz6ztfl"
MOBILE_APP_URL = "https://paucki.github.io/SORG-GT-Data-Analyzer/mobile/"
ADMIN_USERS_URL = SUPABASE_URL + "/functions/v1/admin-users"


@dataclass
class UserSession:
    username: str = ""
    display_name: str = ""
    role: str = "user"
    channel: str = "stable"
    token: str = ""
    user_id: str = ""
    team_id: str = ""


class LoginDialog(QDialog):
    """Start-Anmeldung. Funktioniert lokal und optional gegen den SORG-Account-Server."""

    def __init__(self, update_client, parent=None):
        super().__init__(parent)
        self.update_client = update_client
        self.user_session: UserSession | None = None
        self.setWindowTitle("SORG GT Data Analyzer")
        self.setModal(True)
        self.setFixedSize(520, 560)
        self.setStyleSheet("""
            QDialog {
                background: #07090c;
                color: #f5f7fa;
            }
            QFrame#loginCard {
                background: #11151a;
                border: 1px solid #2a3038;
                border-radius: 18px;
            }
            QLabel#brand {
                color: #ffffff;
                font-size: 30px;
                font-weight: 900;
                letter-spacing: 2px;
            }
            QLabel#gt {
                color: #e21b2d;
                font-size: 13px;
                font-weight: 900;
                letter-spacing: 4px;
            }
            QLabel#headline {
                color: #ffffff;
                font-size: 20px;
                font-weight: 800;
            }
            QLabel#subtle {
                color: #929ba7;
                font-size: 12px;
            }
            QLineEdit {
                min-height: 46px;
                padding: 0 14px;
                color: #ffffff;
                background: #090c10;
                border: 1px solid #303640;
                border-radius: 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #e21b2d;
            }
            QPushButton {
                min-height: 44px;
                border-radius: 10px;
                font-weight: 800;
                padding: 0 16px;
            }
            QPushButton#loginPrimary {
                color: #ffffff;
                background: #e21b2d;
                border: 1px solid #e21b2d;
            }
            QPushButton#loginPrimary:hover {
                background: #f0293a;
            }
            QPushButton#secondary {
                color: #d8dde4;
                background: #171b21;
                border: 1px solid #303640;
            }
            QPushButton#passwordToggle {
                color: #aab2bd;
                background: transparent;
                border: 0;
                min-height: 28px;
                padding: 0 4px;
            }
            QCheckBox {
                color: #aeb6c2;
                spacing: 8px;
            }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(34, 28, 34, 28)
        outer.setSpacing(0)

        brand = QLabel("SORG")
        brand.setObjectName("brand")
        brand.setAlignment(Qt.AlignCenter)
        outer.addWidget(brand)

        gt = QLabel("GT DATA ANALYZER")
        gt.setObjectName("gt")
        gt.setAlignment(Qt.AlignCenter)
        outer.addWidget(gt)
        outer.addSpacing(22)

        card = QFrame()
        card.setObjectName("loginCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 26, 28, 26)
        card_layout.setSpacing(12)

        headline = QLabel("Willkommen zurück")
        headline.setObjectName("headline")
        headline.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(headline)

        subtitle = QLabel("Melde dich an und starte direkt ins Rennwochenende.")
        subtitle.setObjectName("subtle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(10)

        user_label = QLabel("Benutzername")
        user_label.setObjectName("subtle")
        card_layout.addWidget(user_label)
        self.username = QLineEdit()
        self.username.setPlaceholderText("Benutzername eingeben")
        self.username.setClearButtonEnabled(True)
        card_layout.addWidget(self.username)

        pass_row = QHBoxLayout()
        pass_label = QLabel("Passwort")
        pass_label.setObjectName("subtle")
        self.show_password = QPushButton("Anzeigen")
        self.show_password.setObjectName("passwordToggle")
        self.show_password.setCheckable(True)
        self.show_password.toggled.connect(
            lambda checked: (
                self.password.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password),
                self.show_password.setText("Verbergen" if checked else "Anzeigen"),
            )
        )
        pass_row.addWidget(pass_label)
        pass_row.addStretch()
        pass_row.addWidget(self.show_password)
        card_layout.addLayout(pass_row)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Passwort eingeben")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.returnPressed.connect(self.try_login)
        card_layout.addWidget(self.password)

        self.remember_user = QCheckBox("Benutzername auf diesem PC merken")
        card_layout.addWidget(self.remember_user)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("color: #f3a6ad; font-size: 12px; min-height: 22px;")
        card_layout.addWidget(self.status)

        self.login_button = QPushButton("ANMELDEN")
        self.login_button.setObjectName("loginPrimary")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.try_login)
        card_layout.addWidget(self.login_button)

        forgot = QPushButton("Passwort vergessen?")
        forgot.setObjectName("passwordToggle")
        forgot.clicked.connect(self.request_password_reset)
        card_layout.addWidget(forgot)

        self.setup_button = QPushButton("Ersten Benutzer anlegen")
        self.setup_button.setObjectName("secondary")
        self.setup_button.clicked.connect(self.create_first_user)
        card_layout.addWidget(self.setup_button)

        cancel = QPushButton("Beenden")
        cancel.setObjectName("passwordToggle")
        cancel.clicked.connect(self.reject)
        card_layout.addWidget(cancel)

        outer.addWidget(card)
        outer.addStretch()

        footer = QLabel("SORG Rennsport · gemeinsames Konto für PC & Mobile")
        footer.setObjectName("subtle")
        footer.setAlignment(Qt.AlignCenter)
        outer.addWidget(footer)

        try:
            remembered = (self.update_client.data_folder / "remembered_user.txt")
            if remembered.exists():
                self.username.setText(remembered.read_text(encoding="utf-8").strip())
                self.remember_user.setChecked(bool(self.username.text()))
                self.password.setFocus()
            else:
                self.username.setFocus()
        except Exception:
            self.username.setFocus()

        self._refresh_mode()

    @property
    def account_file(self) -> Path:
        return self.update_client.data_folder / "local_accounts.json"

    def _refresh_mode(self):
        if ACCOUNT_SERVER_URL or SUPABASE_URL:
            self.status.setText("Online-Anmeldung · PC & Mobile")
            self.setup_button.setVisible(False)
            return
        if self.account_file.exists():
            self.status.setText("")
            self.setup_button.setVisible(False)
        else:
            self.status.setText("Noch kein Benutzer vorhanden. Lege einmalig den ersten Benutzer an.")
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

    def _supabase_request(self, path: str, *, method="GET", body=None, token=""):
        headers = {
            "apikey": SUPABASE_PUBLISHABLE_KEY,
            "Content-Type": "application/json",
            "User-Agent": "SORG-GT-Data-Analyzer",
        }
        if token:
            headers["Authorization"] = "Bearer " + token
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            SUPABASE_URL + path,
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as error:
            try:
                detail = json.loads(error.read().decode("utf-8"))
                message = detail.get("msg") or detail.get("message") or detail.get("error_description") or str(detail)
            except Exception:
                message = str(error)
            raise RuntimeError(message) from error

    def _supabase_login(self, username: str, password: str) -> UserSession:
        body = json.dumps({"username": username, "password": password}).encode("utf-8")
        request = urllib.request.Request(
            SUPABASE_URL + "/functions/v1/auth-login",
            data=body,
            headers={
                "apikey": SUPABASE_PUBLISHABLE_KEY,
                "Content-Type": "application/json",
                "User-Agent": "SORG-GT-Data-Analyzer",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            try:
                detail = json.loads(error.read().decode("utf-8"))
                message = detail.get("error") or detail.get("message") or "Benutzername oder Passwort ist falsch."
            except Exception:
                message = "Benutzername oder Passwort ist falsch."
            raise RuntimeError(message) from error

        token = data.get("access_token", "")
        user = data.get("user") or {}
        user_id = user.get("id", "")
        display_name = data.get("display_name") or username
        role = "user"
        team_id = ""

        if token and user_id:
            try:
                memberships = self._supabase_request(
                    f"/rest/v1/team_members?user_id=eq.{user_id}&select=team_id,role&limit=1",
                    token=token,
                ) or []
                if memberships:
                    team_id = memberships[0].get("team_id", "")
                    role = memberships[0].get("role") or role
            except Exception:
                pass

        return UserSession(
            username=username,
            display_name=display_name,
            role=role,
            channel="stable",
            token=token,
            user_id=user_id,
            team_id=team_id,
        )

    def _online_login(self, username: str, password: str) -> UserSession:
        if SUPABASE_URL:
            return self._supabase_login(username, password)

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

    def request_password_reset(self):
        username = self.username.text().strip()
        if not username:
            self.status.setText("Bitte zuerst deinen Benutzernamen eingeben.")
            return
        body = json.dumps({
            "username": username,
            "redirect_to": MOBILE_APP_URL,
        }).encode("utf-8")
        request = urllib.request.Request(
            SUPABASE_URL + "/functions/v1/auth-recover",
            data=body,
            headers={
                "apikey": SUPABASE_PUBLISHABLE_KEY,
                "Content-Type": "application/json",
                "User-Agent": "SORG-GT-Data-Analyzer",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=12):
                pass
            QMessageBox.information(
                self,
                "Passwort zurücksetzen",
                "Wenn für diesen Zugang eine Wiederherstellung möglich ist, wurde eine Reset-Nachricht versendet.\n\n"
                "Alternativ kann ein Administrator dein Passwort direkt ändern.",
            )
        except Exception as error:
            self.status.setText(f"Passwort-Reset nicht möglich: {error}")

    def try_login(self):
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            self.status.setText("Bitte Benutzername und Passwort eingeben.")
            return
        self.login_button.setEnabled(False)
        try:
            session = self._online_login(username, password) if (ACCOUNT_SERVER_URL or SUPABASE_URL) else self._local_login(username, password)
        except Exception as error:
            self.status.setText(str(error))
            self.login_button.setEnabled(True)
            return
        try:
            remember_path = self.update_client.data_folder / "remembered_user.txt"
            if self.remember_user.isChecked():
                remember_path.write_text(username, encoding="utf-8")
            elif remember_path.exists():
                remember_path.unlink()
        except Exception:
            pass
        self.user_session = session
        self.accept()


class UserAdminDialog(QDialog):
    """Benutzerverwaltung für SORG-Administratoren."""

    def __init__(self, session: UserSession, parent=None):
        super().__init__(parent)
        self.session = session
        self.users = []
        self.setWindowTitle("SORG GT · Benutzerverwaltung")
        self.resize(760, 520)
        self.setModal(True)

        layout = QVBoxLayout(self)
        title = QLabel("Benutzerverwaltung")
        title.setStyleSheet("font-size:22px;font-weight:800;")
        layout.addWidget(title)

        hint = QLabel("Administratoren können Benutzer anlegen, Rollen ändern, Passwörter setzen und Zugänge deaktivieren.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#9ca3af;")
        layout.addWidget(hint)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Name", "Benutzername", "Funktion", "Telefon", "Wohnort", "Status", "Letzte Anmeldung"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table, 1)

        buttons = QHBoxLayout()
        add_btn = QPushButton("+ Benutzer anlegen")
        add_btn.clicked.connect(self.create_user)
        buttons.addWidget(add_btn)

        pw_btn = QPushButton("Passwort setzen")
        pw_btn.clicked.connect(self.set_password)
        buttons.addWidget(pw_btn)

        active_btn = QPushButton("Aktiv / Inaktiv")
        active_btn.clicked.connect(self.toggle_active)
        buttons.addWidget(active_btn)

        role_btn = QPushButton("Admin-Recht ändern")
        role_btn.clicked.connect(self.change_role)
        buttons.addWidget(role_btn)

        buttons.addStretch()
        refresh_btn = QPushButton("Aktualisieren")
        refresh_btn.clicked.connect(self.refresh)
        buttons.addWidget(refresh_btn)
        layout.addLayout(buttons)

        self.status = QLabel("")
        self.status.setStyleSheet("color:#f3a6ad;")
        layout.addWidget(self.status)
        self.refresh()

    def _call(self, payload):
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            ADMIN_USERS_URL,
            data=data,
            headers={
                "apikey": SUPABASE_PUBLISHABLE_KEY,
                "Authorization": "Bearer " + self.session.token,
                "Content-Type": "application/json",
                "User-Agent": "SORG-GT-Data-Analyzer",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            try:
                detail = json.loads(error.read().decode("utf-8"))
                message = detail.get("error") or detail.get("message") or str(detail)
            except Exception:
                message = str(error)
            raise RuntimeError(message) from error

    def refresh(self):
        try:
            data = self._call({"action": "list"})
            self.users = data.get("users", [])
        except Exception as error:
            self.status.setText(str(error))
            return
        self.table.setRowCount(len(self.users))
        for row, user in enumerate(self.users):
            values = [
                user.get("display_name", ""),
                user.get("username", ""),
                user.get("team_role", "Mechaniker"),
                user.get("phone", ""),
                user.get("residence", ""),
                "Inaktiv" if user.get("inactive") else "Aktiv",
                user.get("last_sign_in_at") or "—",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, user.get("id"))
                self.table.setItem(row, col, item)
        self.table.resizeColumnsToContents()
        self.status.setText(f"{len(self.users)} Benutzer")

    def _selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.users):
            QMessageBox.information(self, "Benutzerverwaltung", "Bitte zuerst einen Benutzer auswählen.")
            return None
        return self.users[row]

    def create_user(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Benutzer anlegen")
        form = QFormLayout(dialog)
        name = QLineEdit()
        username = QLineEdit()
        phone = QLineEdit()
        residence = QLineEdit()
        password = QLineEdit()
        password.setEchoMode(QLineEdit.Password)
        team_role = QComboBox()
        team_role.addItems(["Reifen", "Mechaniker", "Car Chief", "Fahrer"])
        permission = QComboBox()
        permission.addItems(["user", "admin"])
        form.addRow("Name", name)
        form.addRow("Benutzername", username)
        form.addRow("Telefon", phone)
        form.addRow("Wohnort", residence)
        form.addRow("Funktion", team_role)
        form.addRow("Berechtigung", permission)
        form.addRow("Passwort", password)
        row = QHBoxLayout()
        ok = QPushButton("Anlegen")
        cancel = QPushButton("Abbrechen")
        row.addWidget(ok)
        row.addWidget(cancel)
        form.addRow(row)
        ok.clicked.connect(dialog.accept)
        cancel.clicked.connect(dialog.reject)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            self._call({
                "action": "create",
                "display_name": name.text().strip(),
                "username": username.text().strip(),
                "phone": phone.text().strip(),
                "residence": residence.text().strip(),
                "team_role": team_role.currentText(),
                "permission": permission.currentText(),
                "password": password.text(),
            })
            self.refresh()
        except Exception as error:
            QMessageBox.critical(self, "Benutzer anlegen", str(error))

    def set_password(self):
        user = self._selected()
        if not user:
            return
        password, ok = QInputDialog.getText(
            self, "Passwort setzen", f"Neues Passwort für {user.get('username','')}:", QLineEdit.Password
        )
        if not ok:
            return
        try:
            self._call({"action": "set_password", "user_id": user["id"], "password": password})
            QMessageBox.information(self, "Passwort", "Passwort wurde geändert.")
        except Exception as error:
            QMessageBox.critical(self, "Passwort", str(error))

    def toggle_active(self):
        user = self._selected()
        if not user:
            return
        active = bool(user.get("inactive"))
        label = "aktivieren" if active else "deaktivieren"
        if QMessageBox.question(self, "Benutzer", f"{user.get('username','')} wirklich {label}?") != QMessageBox.Yes:
            return
        try:
            self._call({"action": "set_active", "user_id": user["id"], "active": active})
            self.refresh()
        except Exception as error:
            QMessageBox.critical(self, "Benutzer", str(error))

    def change_role(self):
        user = self._selected()
        if not user:
            return
        choices = ["user", "admin"]
        current = user.get("permission", "user")
        value, ok = QInputDialog.getItem(
            self, "Admin-Recht ändern", "Berechtigung:", choices, choices.index(current) if current in choices else 0, False
        )
        if not ok:
            return
        try:
            self._call({"action": "set_role", "user_id": user["id"], "role": value})
            self.refresh()
        except Exception as error:
            QMessageBox.critical(self, "Rolle", str(error))


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
