"""Define the colors and Qt stylesheet used by the desktop editor."""

INK = "#201b2d"
ACCENT = "#574bad"
LAVENDER = "#ebe6fc"
BORDER = "#dcd5ee"
SURFACE = "#ffffff"


WINDOW_STYLE = f"""
QMainWindow {{ background: #f2eff9; }}
QWidget {{ color: {INK}; }}
QFrame#panel {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; }}
QLabel#sectionTitle {{ color: #382967; font-size: 17px; font-weight: 700; }}
QLabel#hint {{ color: #60576f; }}
QPushButton {{
    background: {SURFACE}; border: 1px solid #c8bedf; border-radius: 5px;
    min-height: 28px; padding: 0 10px; font-weight: 600;
}}
QPushButton:hover {{ background: #f3efff; border-color: #8380d4; }}
QPushButton:checked {{ background: {LAVENDER}; border-color: #8380d4; color: #382967; }}
QPushButton#runButton {{ background: {ACCENT}; border-color: {ACCENT}; color: {SURFACE}; }}
QPushButton#runButton:hover {{ background: #443888; }}
QPushButton:disabled, QPushButton#runButton:disabled {{
    background: #f5f2fa; border-color: {BORDER}; color: #716782;
}}
QPushButton:focus {{ border-color: {ACCENT}; }}
QLineEdit {{ selection-background-color: {LAVENDER}; selection-color: {INK}; }}
QSpinBox#initialState, QSpinBox#qubitCount {{
    background: {SURFACE}; color: {INK};
    border: 1px solid #c8bedf; border-radius: 5px; padding-left: 8px;
}}
QSpinBox#initialState QLineEdit {{ placeholder-text-color: #60576f; }}
QSpinBox#initialState:focus, QSpinBox#qubitCount:focus {{ border-color: {ACCENT}; }}
QSpinBox#initialState::up-button, QSpinBox#qubitCount::up-button {{ subcontrol-position: top right; }}
QSpinBox#initialState::down-button, QSpinBox#qubitCount::down-button {{ subcontrol-position: bottom right; }}
QGraphicsView, QTableWidget {{ border: 1px solid {BORDER}; border-radius: 5px; }}
QGraphicsView#circuitGrid QScrollBar, QGraphicsView#circuitGrid::corner {{ background: #f2eff9; }}
QGraphicsView#circuitGrid QScrollBar:horizontal {{ height: 14px; }}
QGraphicsView#circuitGrid QScrollBar:vertical {{ width: 14px; }}
QGraphicsView#circuitGrid QScrollBar::handle {{
    background: #b8aad7; border: 2px solid #f2eff9; border-radius: 5px;
}}
QGraphicsView#circuitGrid QScrollBar::handle:horizontal {{ min-width: 24px; }}
QGraphicsView#circuitGrid QScrollBar::handle:vertical {{ min-height: 24px; }}
QGraphicsView#circuitGrid QScrollBar::handle:hover {{ background: #9384c4; }}
QGraphicsView#circuitGrid QScrollBar::add-line, QGraphicsView#circuitGrid QScrollBar::sub-line {{
    width: 0; height: 0;
}}
QGraphicsView#circuitGrid QScrollBar::add-page, QGraphicsView#circuitGrid QScrollBar::sub-page {{
    background: transparent;
}}
QSplitter::handle {{ background: #f2eff9; }}
QSplitter::handle:hover {{ background: #dcd4f1; }}
QTableWidget {{
    background: {SURFACE}; alternate-background-color: #f8f6fd; gridline-color: #e9e3f3;
    selection-background-color: {LAVENDER}; selection-color: {INK};
}}
QHeaderView::section {{
    background: {LAVENDER}; color: #382967; border: 0; border-right: 1px solid {BORDER};
    border-bottom: 1px solid {BORDER}; padding: 6px; font-weight: 600;
}}
"""
