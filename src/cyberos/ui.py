import os
import sys
import json
import threading
import subprocess
from pathlib import Path

import psutil
from PyQt6.QtCore import QTimer, Qt, QDir, QStandardPaths, QUrl
from PyQt6.QtGui import QDesktopServices, QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QTabWidget,
    QPlainTextEdit,
    QLineEdit,
    QPushButton,
    QFileSystemModel,
    QTreeView,
    QSplitter,
    QTextEdit,
    QProgressBar,
    QHBoxLayout,
    QMessageBox,
    QCheckBox,
)

from .resources import LIGHT_STYLESHEET, DARK_STYLESHEET, APP_NAME


class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.cpu_label = QLabel("CPU: -- %")
        self.cpu_bar = QProgressBar()
        self.mem_label = QLabel("Memory: -- %")
        self.mem_bar = QProgressBar()
        self.net_label = QLabel("Network: rx=0 tx=0")

        layout.addWidget(self.cpu_label)
        layout.addWidget(self.cpu_bar)
        layout.addWidget(self.mem_label)
        layout.addWidget(self.mem_bar)
        layout.addWidget(self.net_label)
        layout.addStretch()
        self.setLayout(layout)

        self.prev_net = psutil.net_io_counters()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

    def update_stats(self):
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        net = psutil.net_io_counters()
        rx = net.bytes_recv - self.prev_net.bytes_recv
        tx = net.bytes_sent - self.prev_net.bytes_sent
        self.prev_net = net

        self.cpu_label.setText(f"CPU: {cpu:.0f} %")
        self.cpu_bar.setValue(int(cpu))
        self.mem_label.setText(f"Memory: {mem:.0f} %")
        self.mem_bar.setValue(int(mem))
        self.net_label.setText(f"Network: rx={self._fmt_bytes(rx)}/s tx={self._fmt_bytes(tx)}/s")

    def _fmt_bytes(self, n: int) -> str:
        for unit in ['B','KB','MB','GB','TB']:
            if n < 1024.0:
                return f"{n:.1f}{unit}"
            n /= 1024.0
        return f"{n:.1f}PB"


class TerminalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        ctrl = QHBoxLayout()
        self.input = QLineEdit()
        self.run_btn = QPushButton("Run")
        self.clear_btn = QPushButton("Clear")
        ctrl.addWidget(self.input)
        ctrl.addWidget(self.run_btn)
        ctrl.addWidget(self.clear_btn)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)

        layout.addLayout(ctrl)
        layout.addWidget(self.output)
        self.setLayout(layout)

        self.run_btn.clicked.connect(self._on_run)
        self.clear_btn.clicked.connect(self.output.clear)

    def _on_run(self):
        cmd = self.input.text().strip()
        if not cmd:
            return
        self.output.appendPlainText(f"$ {cmd}")
        thread = threading.Thread(target=self._run_cmd, args=(cmd,))
        thread.daemon = True
        thread.start()

    def _run_cmd(self, cmd: str):
        # Runs local shell commands and streams output to the UI.
        # WARNING: This executes commands on the local machine — use responsibly.
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True)
            for line in proc.stdout:
                self.output.appendPlainText(line.rstrip())
            proc.wait()
            self.output.appendPlainText(f"[process exited with {proc.returncode}]\n")
        except Exception as e:
            self.output.appendPlainText(f"Error: {e}")


class FileBrowserWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        splitter = QSplitter()

        self.model = QFileSystemModel()
        root = QDir.homePath()
        self.model.setRootPath(root)
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(root))
        self.tree.doubleClicked.connect(self.open_file)
        splitter.addWidget(self.tree)

        self.viewer = QTextEdit()
        self.viewer.setReadOnly(True)
        splitter.addWidget(self.viewer)

        layout.addWidget(splitter)
        self.setLayout(layout)

    def open_file(self, index):
        path = self.model.filePath(index)
        if os.path.isdir(path):
            return
        try:
            with open(path, 'r', errors='ignore') as f:
                text = f.read(100000)
            self.viewer.setPlainText(text)
        except Exception as e:
            QMessageBox.warning(self, "Open file", f"Could not open file:\n{e}")


class ToolsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Tools — safe placeholders and plugin hooks"))
        layout.addWidget(QLabel("Use only on systems you own or have permission to test."))

        # Links to legal resources / tools documentation (read-only)
        def add_link(text, url):
            btn = QPushButton(text)
            btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
            layout.addWidget(btn)

        add_link("nmap docs (info only)", "https://nmap.org/book/man.html")
        add_link("Wireshark docs (info only)", "https://www.wireshark.org/docs/")

        # Plugin area — sample safe plugin loader
        self.plugins_box = QVBoxLayout()
        layout.addLayout(self.plugins_box)
        self.load_plugins()

        layout.addStretch()
        self.setLayout(layout)

    def load_plugins(self):
        self._clear_layout(self.plugins_box)
        plugins_dir = Path.cwd() / 'plugins'
        if not plugins_dir.exists():
            return
        for p in plugins_dir.glob('*.py'):
            name = p.stem
            btn = QPushButton(f"Run plugin: {name}")
            btn.clicked.connect(lambda _, path=p: self._run_plugin(path))
            self.plugins_box.addWidget(btn)

    def _run_plugin(self, path: Path):
        # Import plugin safely (sandboxing not provided) — plugins should be trusted.
        try:
            spec = __import__(f"plugins.{path.stem}", fromlist=['run'])
            if hasattr(spec, 'run'):
                out = spec.run()
                QMessageBox.information(self, "Plugin output", str(out))
            else:
                QMessageBox.warning(self, "Plugin", "No run() in plugin")
        except Exception as e:
            QMessageBox.warning(self, "Plugin error", str(e))

    def _clear_layout(self, lay):
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()


class SettingsWidget(QWidget):
    def __init__(self, parent=None, apply_theme_callback=None):
        super().__init__(parent)
        self.apply_theme = apply_theme_callback
        layout = QVBoxLayout()
        self.dark_cb = QCheckBox("Dark theme")
        layout.addWidget(self.dark_cb)
        save_btn = QPushButton("Save settings")
        layout.addWidget(save_btn)
        layout.addStretch()
        self.setLayout(layout)

        save_btn.clicked.connect(self.save)
        self.dark_cb.stateChanged.connect(self._on_toggle)
        self._load()

    def _on_toggle(self):
        self.apply_theme(self.dark_cb.isChecked())

    def _settings_path(self) -> Path:
        cfg = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
        if not cfg:
            return Path.home() / '.cyberos_settings.json'
        d = Path(cfg)
        d.mkdir(parents=True, exist_ok=True)
        return d / 'settings.json'

    def _load(self):
        p = self._settings_path()
        if p.exists():
            try:
                data = json.loads(p.read_text())
                self.dark_cb.setChecked(data.get('dark', False))
            except Exception:
                pass

    def save(self):
        p = self._settings_path()
        data = {'dark': self.dark_cb.isChecked()}
        try:
            p.write_text(json.dumps(data))
            QMessageBox.information(self, "Settings", "Saved")
        except Exception as e:
            QMessageBox.warning(self, "Settings", f"Could not save settings: {e}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(900, 600)
        self._central = QTabWidget()
        self.setCentralWidget(self._central)

        self.dashboard = DashboardWidget()
        self.terminal = TerminalWidget()
        self.files = FileBrowserWidget()
        self.tools = ToolsWidget()
        self.settings = SettingsWidget(apply_theme_callback=self.apply_theme)

        self._central.addTab(self.dashboard, "Dashboard")
        self._central.addTab(self.terminal, "Terminal")
        self._central.addTab(self.files, "Files")
        self._central.addTab(self.tools, "Tools")
        self._central.addTab(self.settings, "Settings")

        self._create_menu()
        # apply theme from settings on startup
        self.settings._load()
        self.apply_theme(self.settings.dark_cb.isChecked())

    def _create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._about)
        help_menu.addAction(about_action)

    def _about(self):
        QMessageBox.information(self, "About", f"{APP_NAME} — demo GUI\nUse only on systems you own or have permission to test.")

    def apply_theme(self, dark: bool):
        QApplication.instance().setStyleSheet(DARK_STYLESHEET if dark else LIGHT_STYLESHEET)
