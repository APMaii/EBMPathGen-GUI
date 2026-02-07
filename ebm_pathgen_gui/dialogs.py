#========================================================================
#========================================================================
#========================================================================
'''                       import                                       '''
#========================================================================
#========================================================================
#========================================================================

#---------------------PM_EBM_CORE-------------------------------------------

from PM_EBM_CORE import Core_Mesh_Processor,Core_Heat_Processor,Core_OBF_Generator

import os   
import sys

#---------------------QT-------------------------------------------
from PyQt5.QtCore import Qt

from PyQt5.QtGui import QIcon, QPixmap ,QColor, QPalette

from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QLineEdit, QSplitter ,QComboBox,QSpinBox, QFormLayout,
    QCheckBox,QDoubleSpinBox, QStyleFactory, QTabBar, QFileDialog,QTextEdit,
    QMainWindow, QGroupBox,QRadioButton,QInputDialog,QDialogButtonBox,QDialog,
    QMessageBox,QScrollArea,QListWidget
)
from pyvistaqt import QtInteractor



#----------------Calculations---------------------------------------
import numpy as np
from scipy.spatial import distance
import math 

#--------------Formats-----------------------------------------
import obplib as obp
import json
import pickle
import pyvista as pv
import trimesh
from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.ops import unary_union, polygonize
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from shapely.geometry import MultiPoint
import svgwrite
from dataclasses import dataclass
from typing import List
from datetime import datetime


#----------------Figures-------------------
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas






#------
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QDialog, QVBoxLayout
from matplotlib.cm import get_cmap

from matplotlib.animation import FuncAnimation



class PlotDialog(QDialog):
    """Modal dialog that displays a 2D plot of start-heat pattern points (e.g. random, snake, single directional)."""

    def __init__(self, xs, ys, spread_algorithm, parent=None):
        """
        Args:
            xs: X coordinates of the pattern points.
            ys: Y coordinates of the pattern points.
            spread_algorithm: Algorithm name ('random', 'snake', 'single directional') for color/title.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Start Heat Pattern")
        self.setFixedSize(600, 600)

        layout = QVBoxLayout()
        self.setLayout(layout)
        color_map = {
    "random": "green",
    "snake": "blue",
    "single directional": "red"
    }

        plot_color = color_map.get(spread_algorithm.lower(), "black")  # default to black if unknown

        fig = Figure(figsize=(6, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.plot(xs, ys,
                marker='o',
                #color='green' if spread_algorithm == 'random' else 'blue',
                color=plot_color,
                linestyle='-' if spread_algorithm in [ 'snake' ,'single directional']  else 'None',
                linewidth=0.8,
                markersize=3)
        ax.scatter([0], [0], color='red', label='Center (0,0)', zorder=5)
        ax.set_title(f"{spread_algorithm.capitalize()} Pattern Heat Path")
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.set_aspect('equal', adjustable='box')
        ax.grid(True)
        ax.legend()

        layout.addWidget(canvas)

#===============
#===== loading====
#==================
'''
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt

class StatusDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Please wait...")
        self.setFixedSize(300, 100)
        self.label = QLabel("Initializing...", self)
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Optional: make it look like a modal loading window
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
    
    def update_status(self, message):
        self.label.setText(message)
        QApplication.processEvents()  # force UI update
'''
        
        
        
import sys
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt

class PrintRedirector:
    """Redirects stdout writes to a callback (e.g. for displaying print output in the GUI)."""

    def __init__(self, update_func):
        """
        Args:
            update_func: Callable taking a single string argument; called for each non-empty line written.
        """
        self.update_func = update_func

    def write(self, text):
        """Forward non-empty stripped lines to the update callback."""
        if text.strip():  # Ignore empty lines
            self.update_func(text.strip())

    def flush(self):
        """No-op; required for compatibility with file-like interface."""
        pass  # Required for compatibility



class StatusDialog(QDialog):
    """Modal dialog showing a top status message and a bottom line (e.g. for print output) during long operations."""

    def __init__(self, parent=None):
        """Initialize the dialog with two labels (top and bottom)."""
        super().__init__(parent)
        self.setWindowTitle("Processing...")
        self.setFixedSize(400, 120)

        self.top_label = QLabel("Initializing...", self)
        self.bottom_label = QLabel("", self)

        self.top_label.setAlignment(Qt.AlignCenter)
        self.bottom_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.top_label)
        layout.addWidget(self.bottom_label)
        self.setLayout(layout)

        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        
    def update_top_label(self,text):
        """Set the top label text and process pending events so the UI updates."""
        self.top_label.setText(text)
        QApplication.processEvents()
        
        

    def update_print_line(self, text):
        """Set the bottom label text (e.g. last print line) and process pending events."""
        self.bottom_label.setText(text)
        QApplication.processEvents()






class ColoredTabBar(QTabBar):
    """Custom tab bar that applies a stylesheet for disabled tab appearance (gray background, gray text)."""

    def __init__(self):
        """Initialize the tab bar with disabled-tab styling."""
        super().__init__()
        self.setStyleSheet("""
            QTabBar::tab:disabled {
                background-color: #f0f0f0;
                color: #808080;
            }
        """)
        
    
#========================================================================
#========================================================================
#========================================================================
'''                      Project SETUP Window                         '''
#========================================================================
#========================================================================
#========================================================================

    
class ProjectSetupDialog(QDialog):
    """First-window dialog for new project: project name, material, description, notes, revision, author, and optional image."""

    def __init__(self):
        """Initialize the project setup dialog with image, inputs, and license link."""
        super().__init__()
        self.setWindowTitle("New Project")

        self.setGeometry(550, 100, 400, 250)
        
        layout = QVBoxLayout()

        # Add Image
        self.image_label = QLabel(self)
        pixmap = QPixmap("ebm_background.png")
        if pixmap.isNull():
            self.image_label.setText("Image not found!")
        else:
            self.image_label.setPixmap(pixmap.scaled(400, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)
        

        form_layout = QFormLayout()
        
        self.author_name = QLineEdit()
        form_layout.addRow(QLabel("Author Name:"), self.author_name)

        self.project_name_input = QLineEdit()
        form_layout.addRow(QLabel("Project Name:"), self.project_name_input)

        self.project_material_input = QLineEdit()
        form_layout.addRow(QLabel("Material:"), self.project_material_input)
        
        self.description_input = QTextEdit()
        form_layout.addRow(QLabel("Description:"), self.description_input)

        self.notes_input = QTextEdit()
        form_layout.addRow(QLabel("Notes:"), self.notes_input)
        
        self.revision =QLineEdit()
        form_layout.addRow(QLabel("revision:"), self.revision)


        #&&&
        #here we must handle the accept
        #also check the detail that author provide in main()
        
        layout.addLayout(form_layout)
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        
        #???
        #check the directory...
        
        self.another_image_label = QLabel(self)
        pixmap = QPixmap("logo_background.png")
        if pixmap.isNull():
            self.another_image_label.setText("Image not found!")
        else:
            self.another_image_label.setPixmap(pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.another_image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.another_image_label)
        
        
        
        self.license = QLabel(self)
        self.license.setTextFormat(Qt.RichText)
        self.license.setOpenExternalLinks(True)
        self.license.setText('All rights reserved to <a href="https://people.epfl.ch/ali.pilehvarmeibody?lang=en">Ali Pilehvar Meibody</a>.')
        layout.addWidget(self.license)
        

        self.setLayout(layout)
        
        
        
        
    def get_project_details(self):
        """Return a dict with keys: author_name, name, description, notes, material, revision."""
        return {
            'author_name': self.author_name.text().strip(),
            "name": self.project_name_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
            "notes": self.notes_input.toPlainText().strip(),
            "material": self.project_material_input.text().strip(),
            'revision':self.revision.text().strip()
        }




        
