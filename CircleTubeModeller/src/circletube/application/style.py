STYLE = """
QMainWindow, QDialog { background: #1b1f26; color: #f1f4f8; }
QWidget { color: #f1f4f8; font-size: 13px; }
QMenuBar, QMenu, QDockWidget, QScrollArea { background: #1b1f26; color: #f1f4f8; }
QMenuBar::item { padding: 5px 8px; }
QMenuBar::item:selected, QMenu::item:selected { background: #3b5bdb; color: white; }
QMenu::item { padding: 5px 24px 5px 8px; }
QDockWidget::title { padding: 5px; background: #2a3039; color: #f1f4f8; }
QGroupBox { background: #242a33; color: #f1f4f8; font-weight: 600; border: 1px solid #424b58; border-radius: 6px; margin-top: 10px; padding: 8px 6px 6px 6px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #dce5f2; }
QPushButton { color: #f1f4f8; padding: 5px 8px; border: 1px solid #505a68; border-radius: 5px; background: #303741; }
QPushButton:hover { background: #3c4653; }
QPushButton:pressed { background: #252b34; }
QPushButton:checked { background: #3b5bdb; color: white; border-color: #6682ed; }
QPushButton:disabled { color: #8993a1; background: #272c34; border-color: #3b424d; }
QPushButton#primary { background: #3b5bdb; color: white; border-color: #6682ed; font-weight: 600; }
QPushButton#primary:hover { background: #4a6bea; }
QComboBox, QDoubleSpinBox, QPlainTextEdit { background: #11151b; color: #f1f4f8; border: 1px solid #505a68; border-radius: 4px; padding: 4px; selection-background-color: #3b5bdb; selection-color: white; }
QComboBox QAbstractItemView { background: #202630; color: #f1f4f8; selection-background-color: #3b5bdb; selection-color: white; border: 1px solid #505a68; }
QCheckBox { spacing: 7px; }
QCheckBox::indicator { width: 15px; height: 15px; background: #11151b; border: 1px solid #697585; border-radius: 3px; }
QCheckBox::indicator:checked { background: #3b5bdb; border-color: #8197f1; }
QSlider::groove:horizontal { height: 5px; background: #424b58; border-radius: 2px; }
QSlider::handle:horizontal { width: 14px; margin: -5px 0; background: #8da3ff; border: 1px solid #b5c2ff; border-radius: 7px; }
QStatusBar { background: #20252d; color: #e1e7ef; }
QStatusBar QLabel { padding: 0 10px; color: #e1e7ef; }
QToolTip { color: #f1f4f8; background: #303741; border: 1px solid #697585; }
"""
