import sys
import os
import psutil
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QSystemTrayIcon, QMenu, 
    QListWidget, QPushButton, QSpinBox, QLabel, 
    QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, 
    QFileDialog, QListWidgetItem, QCheckBox, QGroupBox
)
from PyQt6.QtCore import QTimer, Qt, QSize
from PyQt6.QtGui import QIcon, QAction, QFont, QPixmap, QPainter

class AppMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.monitored_apps = []
        self.tray_icon = None
        self.current_user = os.getlogin()
        self.system_processes = [
            'svchost.exe', 'csrss.exe', 'wininit.exe', 'services.exe', 
            'lsass.exe', 'winlogon.exe', 'spoolsv.exe', 'taskhost.exe',
            'dwm.exe', 'explorer.exe', 'conhost.exe', 'RuntimeBroker.exe',
            'SearchIndexer.exe', 'SearchProtocolHost.exe', 'SearchFilterHost.exe',
            'smss.exe', 'fontdrvhost.exe', 'sihost.exe', 'taskhostw.exe',
            'ctfmon.exe', 'dllhost.exe', 'backgroundTaskHost.exe', 'WmiPrvSE.exe',
            'msmpeng.exe', 'NisSrv.exe', 'SecurityHealthService.exe', 'Memory Compression',
            'Registry', 'System', 'System Idle Process'
        ]
        self.last_notification_apps = []
        self.init_ui()
        self.init_tray()
        self.setup_timer()
        
    def create_tray_icon(self):
        """Create a custom tray icon"""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.darkGreen)
        painter.setPen(Qt.GlobalColor.darkGreen)
        painter.drawEllipse(2, 2, 12, 12)
        painter.setBrush(Qt.GlobalColor.white)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(5, 12, "A")
        painter.end()
        
        return QIcon(pixmap)
        
    def init_ui(self):
        self.setWindowTitle("Application Running Notifier")
        self.setGeometry(300, 300, 700, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel("Monitoring GUI applications (filtered for user applications only)")
        info_label.setStyleSheet("QLabel { background-color: #e6f3ff; padding: 5px; border-radius: 3px; }")
        layout.addWidget(info_label)
        
        # Monitored applications group
        monitored_group = QGroupBox("Applications to monitor")
        monitored_layout = QVBoxLayout()
        self.app_list = QListWidget()
        self.app_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Application")
        self.add_btn.clicked.connect(self.add_application)
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_applications)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        
        monitored_layout.addWidget(self.app_list)
        monitored_layout.addLayout(btn_layout)
        monitored_group.setLayout(monitored_layout)
        layout.addWidget(monitored_group)
        
        # Running applications group
        running_group = QGroupBox("Running Applications (GUI only)")
        running_layout = QVBoxLayout()
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh Running Apps")
        self.refresh_btn.clicked.connect(self.populate_running_apps)
        
        # Running apps list
        running_apps_label = QLabel("Double-click on a running application to add it to monitoring:")
        running_apps_label.setStyleSheet("QLabel { font-weight: bold; }")
        
        self.running_apps_list = QListWidget()
        self.running_apps_list.itemDoubleClicked.connect(self.add_running_app_to_monitor)
        
        running_layout.addWidget(self.refresh_btn)
        running_layout.addWidget(running_apps_label)
        running_layout.addWidget(self.running_apps_list)
        running_group.setLayout(running_layout)
        layout.addWidget(running_group)
        
        # Settings group
        settings_group = QGroupBox("Settings")
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("Check interval (seconds):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(5, 3600)
        self.interval_spin.setValue(60)
        self.interval_spin.valueChanged.connect(self.interval_changed)
        settings_layout.addWidget(self.interval_spin)
        settings_layout.addStretch()
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Minimize to tray button
        self.tray_btn = QPushButton("Minimize to System Tray")
        self.tray_btn.clicked.connect(self.hide)
        layout.addWidget(self.tray_btn)
        
        central_widget.setLayout(layout)
        
        # Initial population of running apps
        self.populate_running_apps()
        
    def is_system_process(self, process_name):
        """Check if a process is a system process"""
        if not process_name:
            return True
            
        process_lower = process_name.lower()
        for system_process in self.system_processes:
            if system_process.lower() in process_lower:
                return True
        return False
        
    def populate_running_apps(self):
        self.running_apps_list.clear()
        gui_apps = set()
        
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                proc_name = proc.info['name']
                proc_exe = proc.info['exe']
                
                # Skip processes without a name or executable path
                if not proc_name or not proc_exe:
                    continue
                    
                # Skip system processes
                if self.is_system_process(proc_name):
                    continue
                    
                # Skip processes in system directories (unless they're known GUI apps)
                if proc_exe and 'system32' in proc_exe.lower() and proc_name.lower() not in ['notepad.exe', 'calc.exe', 'mspaint.exe']:
                    continue
                    
                # Skip background processes and services
                if 'service' in proc_name.lower() or 'host' in proc_name.lower():
                    continue
                    
                # Add the process if it passes all filters
                gui_apps.add(proc_name)
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process may have terminated, skip it
                continue
                
        # Add GUI apps to the list
        for app_name in sorted(gui_apps):
            item = QListWidgetItem(app_name)
            item.setData(Qt.ItemDataRole.UserRole, app_name)
            self.running_apps_list.addItem(item)
            
        # Update the status
        self.statusBar().showMessage(f"Found {len(gui_apps)} GUI applications")
                
    def add_running_app_to_monitor(self, item):
        """Add a running application to the monitoring list when double-clicked"""
        app_name = item.data(Qt.ItemDataRole.UserRole)
        
        if app_name and app_name not in self.monitored_apps:
            self.monitored_apps.append(app_name)
            self.app_list.addItem(app_name)
            self.statusBar().showMessage(f"Added '{app_name}' to monitoring list", 3000)
            
    def init_tray(self):
        # Create system tray icon
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(self.create_tray_icon())
            
            # Create tray menu
            tray_menu = QMenu()
            restore_action = QAction("Restore", self)
            restore_action.triggered.connect(self.show_restore)
            tray_menu.addAction(restore_action)
            
            refresh_action = QAction("Refresh Running Apps", self)
            refresh_action.triggered.connect(self.populate_running_apps)
            tray_menu.addAction(refresh_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.tray_icon_activated)
            self.tray_icon.messageClicked.connect(self.notification_clicked)
            self.tray_icon.show()
            
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_restore()
            
    def notification_clicked(self):
        """Handle notification click - open the applications"""
        for app_name in self.last_notification_apps:
            try:
                # Try to find the application path from running processes first
                app_path = None
                for proc in psutil.process_iter(['name', 'exe']):
                    try:
                        if proc.info['name'] == app_name and proc.info['exe']:
                            app_path = proc.info['exe']
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # If not found in running processes, try common locations
                if not app_path:
                    program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
                    program_files_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')
                    local_appdata = os.environ.get('LOCALAPPDATA', '')
                    
                    possible_locations = [
                        os.path.join(program_files, app_name),
                        os.path.join(program_files_x86, app_name),
                        os.path.join(local_appdata, app_name),
                    ]
                    
                    for location in possible_locations:
                        exe_path = location if location.endswith('.exe') else location + '.exe'
                        if os.path.exists(exe_path):
                            app_path = exe_path
                            break
                
                # Launch the application if we found a path
                if app_path:
                    subprocess.Popen([app_path])
                    self.statusBar().showMessage(f"Launched {app_name}", 3000)
                else:
                    self.statusBar().showMessage(f"Could not find path for {app_name}", 3000)
                    
            except Exception as e:
                self.statusBar().showMessage(f"Error launching {app_name}: {str(e)}", 3000)
            
    def show_restore(self):
        self.show()
        self.activateWindow()
        self.raise_()
        self.populate_running_apps()  # Refresh the list when restoring
        
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_applications)
        self.timer.start(self.interval_spin.value() * 1000)
        
    def interval_changed(self):
        self.timer.setInterval(self.interval_spin.value() * 1000)
        
    def add_application(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Application", 
            "C:\\", "Executable files (*.exe)"
        )
        if file_path:
            app_name = os.path.basename(file_path)
            if app_name not in self.monitored_apps:
                self.monitored_apps.append(app_name)
                self.app_list.addItem(app_name)
                self.statusBar().showMessage(f"Added '{app_name}' to monitoring list", 3000)
                
    def remove_applications(self):
        removed_count = 0
        for item in self.app_list.selectedItems():
            app_name = item.text()
            if app_name in self.monitored_apps:
                self.monitored_apps.remove(app_name)
                removed_count += 1
            self.app_list.takeItem(self.app_list.row(item))
            
        if removed_count > 0:
            self.statusBar().showMessage(f"Removed {removed_count} applications from monitoring", 3000)
            
    def check_applications(self):
        running_apps = []
        
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name']
                
                # Check if this is one of our monitored apps and not a system process
                if (proc_name in self.monitored_apps and 
                    not self.is_system_process(proc_name)):
                    running_apps.append(proc_name)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        if running_apps:
            # Store for notification click handling
            self.last_notification_apps = running_apps.copy()
            
            message = "Monitored applications are running:\n" + "\n".join(running_apps)
            if self.tray_icon:
                self.tray_icon.showMessage(
                    "Application Monitor", 
                    message, 
                    QSystemTrayIcon.MessageIcon.Information, 
                    5000  # Show for 5 seconds
                )
                
    def closeEvent(self, event):
        # Minimize to tray instead of closing
        if self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()
            
    def quit_application(self):
        if self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()

def main():
    # Fix for locale issue - set the environment variable before creating QApplication
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''
    
    app = QApplication(sys.argv)
    
    # Ensure the application doesn't quit when the window is closed
    app.setQuitOnLastWindowClosed(False)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Set application name and organization for better system integration
    app.setApplicationName("Application Monitor")
    app.setOrganizationName("AppMonitor")
    
    monitor = AppMonitor()
    monitor.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()