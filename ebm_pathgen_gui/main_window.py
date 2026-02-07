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


#---------------------ebm_pathgen_gui package-------------------------------------------
from .constants import DEFAULT_BASE_RADIUS, DEFAULT_BASE_THICKNESS, Z_MAX_EBM_BASE, next_button_styles
from .dialogs import PlotDialog, StatusDialog, PrintRedirector, ColoredTabBar, ProjectSetupDialog
from .advanced_windows import AdvancedWindow_layers, AdvancedWindow_objects

class STLManipulatorTabs(QMainWindow):
    """Main application window: tabbed EBM path generation workflow (box, geometry, slicing, preheating, hatching, postcooling, parametrization, preview)."""

    def __init__(self, project_details):
        """Initialize the main window and project state from setup dialog.

        Args:
            project_details: Dict with keys: material, name, revision, author_name, description, notes.
        """
        super().__init__()
        
        
        
        #===================================================
        #------------Informations related project-----------
        
        self.Project_case_number=1
        self.Project_material = project_details["material"]
        self.Project_name = project_details["name"]
        self.Project_revision_number=project_details['revision']

        
        self.Project_author_name=project_details['author_name']
        self.Project_description = project_details["description"] 
        self.Project_notes = project_details["notes"]
        
        
        if self.Project_revision_number is None or not isinstance(self.Project_revision_number, (int, float)):
            self.Project_revision_number=1
        
        
        
        if self.Project_description is None:
            self.Project_description='No Description'
            
        if self.Project_notes is None:
            self.Project_notes='no additional notes'
            


        #------------setup top panel---------------------

        self.setWindowTitle("Advanced PM-EBM")
        self.setGeometry(100, 100, 1200, 800)

        # Create main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        # Create top panel for controls
        self.top_panel = QWidget()
       # self.top_panel.setStyleSheet("background-color: black;")
        top_layout = QVBoxLayout(self.top_panel)
        #top_panel.setFixedHeight(300)  # Adjust this value as needed

        # Create tab widget
        self.tabs = QTabWidget()
        #self.tabs.setFixedSize(1450, 150)  # Set the size of the tab widget
        
        
        #Creat Tab for colour maping (green)
        self.tabs.setTabBar(ColoredTabBar())
        
        top_layout.addWidget(self.tabs)
        
        # Connect tab changed signal to handle height adjustment
        self.tabs.currentChanged.connect(self.adjust_top_panel_height)
        
        # Dictionary to store desired heights for each tab
        self.tab_heights = {
            "Create Box": 300,      # Adjust these values as needed
            "Import Geometry": 300,
            "Slicing": 250,
            "Pre-heating": 400,
            "Hatching": 350,
            "post_cooling": 300,
            "Parametrization":150,
            "Preview": 250
        }




        #---------------pyvista panel in the down side------------------
        self.pyvista_panel = QWidget()
        self.pyvista_layout = QVBoxLayout(self.pyvista_panel)
        self.plotter = QtInteractor(self.pyvista_panel)
        self.plotter.set_background("white")
        self.pyvista_layout.addWidget(self.plotter.interactor)



        #----------adding top panel and pyvista panel--------------------
        self.main_layout.addWidget(self.top_panel)
        self. main_layout.addWidget(self.pyvista_panel)
        
        self.plotter.interactor.setVisible(True)
        
        
        
        
        #----------set up matplotlib panel and unvisible------------
        
        self.matplotlib_panel = QWidget()
        self.matplotlib_layout = QVBoxLayout(self.matplotlib_panel)
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        #self.matplotlib_layout.addWidget(self.matplotlib_panel)
        self.matplotlib_layout.addWidget(self.canvas)
        
        self.canvas.setVisible(False)
        self.main_layout.addWidget(self.matplotlib_panel) 
        
        
        
        #-------------Variables for controling--------------------------
        self.box = None
        self.mesh = None
        self.pv_mesh = None
        self.translation = np.array([0, 0, 0])
        self.transform_for_once=0
        
        self.EBM_base_is_created=False
        self.is_create_box=False
        self.is_create_geom=False
        self.is_sliced=False
        self.is_preheated=False
        self.is_hatched=False
        self.is_postcooled=False
        self.is_parametrizated=False

        self.run_slice_stage=0
        self.run_hatch_stage=0
        self.s_previous_message=''
        self.h_previous_message=''
        self.slice_message_status=None
        self.hatched_message_status=None
        
        
        self.postcooling_pixel_skip=None
        self.j_pixel_skip=None
        self.j_pixel_skip_is=None
        self.postcooling_pixel_skip_is=None

        
        self.j_pixel_anim=None
        self.postcooling_anim=None
        
        self.click_on_apply_multiple=None
        self.it_is_final_multiples=False
        
        self.apply_jump_safe_step=None
        
        
        self.start_heat_is_Pro_state=False
        

        self.finalized_slice_n_layers=0
        
        self.workflow_state = {
            'box_created': False,
            'geometry_imported': False,
            'geometry_saved': False,
            'slicing_completed': False,
            'preheating_completed':False,
            'hatching_completed': False,
            'post_cooling_completed': False,
            'parametrization_completed':False
        }
        
        


        #-------------Creat all tabs within its function--------------------------
        self.setup_box_tab()
        self.setup_geometry_tab()
        self.setup_slicing_tab()
        self.setup_preheating_tab()
        self.setup_hatching_tab()
        self.setup_postcooling_tab()
        self.setup_parametrization_tab()
        self.setup_preview_tab()
        
        #update order and colour
        self.update_tab_states()
        

    

    def adjust_top_panel_height(self, index):
        """
        called in __init__ 
        Adjust top panel height based on selected tab
        
        """
        current_tab_text = self.tabs.tabText(index)
        if current_tab_text in self.tab_heights:
            self.top_panel.setFixedHeight(self.tab_heights[current_tab_text])
            # Force layout update
            self.main_layout.update()
            
    def set_tab_height(self, tab_name, height):
        """called in __init__ 
        
        Set or update the desired height for a specific tab"""
        self.tab_heights[tab_name] = height
        # If this is the current tab, update immediately
        current_tab_text = self.tabs.tabText(self.tabs.currentIndex())
        if current_tab_text == tab_name:
            self.adjust_top_panel_height(self.tabs.currentIndex())
            
   
    def update_tab_states(self):
        """
        called in __init__ 
        Update the enabled state and color of all tabs based on workflow state
        
        """
        
        #$$$
        #when go next , can not back again
        
        # Define tab indices
        BOX_TAB = 0
        GEOMETRY_TAB = 1
        SLICING_TAB = 2
        PREHEATING_TAB = 3
        HATCHING_TAB =4
        POSTCOOLING_TAB = 5
        PARAMETRIZATION_TAB = 6
        PREVIEW_TAB = 7
        
        

        # Enable/disable tabs based on workflow state
        self.tabs.setTabEnabled(GEOMETRY_TAB, self.workflow_state['box_created'])
        self.tabs.setTabEnabled(SLICING_TAB, self.workflow_state['geometry_saved'])
        self.tabs.setTabEnabled(PREHEATING_TAB, self.workflow_state['slicing_completed'])
        self.tabs.setTabEnabled(HATCHING_TAB, self.workflow_state['preheating_completed'])
        self.tabs.setTabEnabled(POSTCOOLING_TAB, self.workflow_state['hatching_completed'])
        self.tabs.setTabEnabled(PARAMETRIZATION_TAB, self.workflow_state['post_cooling_completed'])
        self.tabs.setTabEnabled(PREVIEW_TAB, self.workflow_state['parametrization_completed'])
        

        # Update colors for completed steps
        tabbar = self.tabs.tabBar()
        if self.workflow_state['box_created']:
            tabbar.setTabTextColor(BOX_TAB, QColor('green'))
        if self.workflow_state['geometry_saved']:
            tabbar.setTabTextColor(GEOMETRY_TAB, QColor('green'))
        if self.workflow_state['slicing_completed']:
            tabbar.setTabTextColor(SLICING_TAB, QColor('green'))
        if self.workflow_state['preheating_completed']:
            tabbar.setTabTextColor(PREHEATING_TAB, QColor('green'))
            
        if self.workflow_state['hatching_completed']:
            tabbar.setTabTextColor(HATCHING_TAB, QColor('green'))
            
        if self.workflow_state['post_cooling_completed']:
            tabbar.setTabTextColor(POSTCOOLING_TAB, QColor('green'))
            
        if self.workflow_state['parametrization_completed']:
            tabbar.setTabTextColor(PARAMETRIZATION_TAB, QColor('green'))
        
        
            
            


    #----------------------------------------------
    #----------------------------------------------
    #----------------------------------------------
    '''              Box Tab                 '''
    #----------------------------------------------
    #----------------------------------------------
    #----------------------------------------------
    

    #first SETUP BOX TAB
    def setup_box_tab(self):
        """
        First Tab for creating box in cm
        
        it has create_box and create_ebm function inside
        
        
        
        """
        
        
        #===================================================
        #------------------Structure of the BOX Tab---------
        
        
        box_tab = QWidget()
        #box_tab.setFixedSize(500, 100)
        #sub_tabs.setFixedSize(600, 400) 
        #box_tab.setFixedHeight(200)  # Fix height for box tab panel
        main_layout= QHBoxLayout()
        # Create a QTabWidget to manage the sub-tabs
        sub_tabs = QTabWidget()
        #sub_tabs.setFixedSize(600, 400) 

        box_layout = QVBoxLayout()  # Changed to horizontal layout
        # Create form for box dimensions
        form1 = QFormLayout()
        form2 = QFormLayout()
        form3 = QFormLayout()
        
        self.box_x = QDoubleSpinBox()
        self.box_x.setRange(1, 1000)
        self.box_x.setValue(100)
        self.box_y = QDoubleSpinBox()
        self.box_y.setRange(1, 1000)
        self.box_y.setValue(100)
        self.box_z = QDoubleSpinBox()
        self.box_z.setRange(1, 1000)
        self.box_z.setValue(100)
        
        

        form1.addRow("Box Length (X) (cm):", self.box_x)
        form2.addRow("Box Width (Y) (cm):", self.box_y)
        form3.addRow("Box Height (Z) (cm):", self.box_z)



        form1_widget = QWidget()
        form1_widget.setLayout(form1)
        
        form2_widget = QWidget()
        form2_widget.setLayout(form2)
        
        form3_widget = QWidget()
        form3_widget.setLayout(form3)
        
        
        form_layout=QHBoxLayout()
        
        form_layout.addWidget(form1_widget)
        form_layout.addWidget(form2_widget)
        form_layout.addWidget(form3_widget)
        
        
        form_widget=QWidget()
        form_widget.setLayout(form_layout)
        
        
        #box_layout.addWidget(form_widget)
        #create_box_button = QPushButton("Create Box")
        #create_box_button.clicked.connect(self.create_box)
        #box_layout.addWidget(create_box_button)
        #box_layout.addStretch()
        #neww----- upper lien ignore
        #box_tab_widget = QWidget()
        #box_tab_widget.setLayout(box_layout)
        #sub_tabs.addTab(box_tab_widget, "Box")  # Add Box tab

    
        
        #base_ebm_layout1 = QVBoxLayout()
        #??? default values
        self.buildPistonDistance =QLineEdit("-0.1")
        self.powdersize =QLineEdit("100")
        self.powderPistonDistance =QLineEdit("0.2")
        self.recoaterAdvanceSpeed =QLineEdit("100.0")
        self.recoaterRetractSpeed =QLineEdit("100.0")
        self.recoaterDwellTime =QLineEdit("0")
        self.recoaterFullRepeats =QLineEdit("0")
        self.recoaterBuildRepeats =QLineEdit("0")
        self.triggeredStart =QLineEdit("true")
        
        
        ebm_base_form = QFormLayout()
        
        ebm_base_form.addRow("build Piston Distance (mm):", self.buildPistonDistance)
        #ebm_base_form.addRow("Powder Size (mm):", self.powdersize)
        ebm_base_form.addRow("powder Piston Distance (mm):", self.powderPistonDistance)
        ebm_base_form.addRow("recoater Advance Speed (mm):", self.recoaterAdvanceSpeed)
        ebm_base_form.addRow("recoater Retract Speed (mm):", self.recoaterRetractSpeed)
        
        
        
        ebm_base_form_widget = QWidget()
        ebm_base_form_widget.setLayout(ebm_base_form)
        #base_ebm_layout1.addWidget(ebm_base_form_widget)
        
        
        
        
        
        #base_ebm_layout2 = QVBoxLayout()  
        ebm_base_form2 = QFormLayout() 
        ebm_base_form2.addRow("recoater Dwell Time (mm):", self.recoaterDwellTime)
        ebm_base_form2.addRow("recoater Full Repeats (mm):", self.recoaterFullRepeats)
        ebm_base_form2.addRow("recoater Build Repeats (mm):", self.recoaterBuildRepeats)
        ebm_base_form2.addRow("triggered Start (mm):", self.triggeredStart)
        
        
        ebm_base_form_widget2 = QWidget()
        ebm_base_form_widget2.setLayout(ebm_base_form2)
        #base_ebm_layout2.addWidget(ebm_base_form_widget2)
        
        

        
        base_ebm_layout=QHBoxLayout()
        base_ebm_layout.addWidget(ebm_base_form_widget)
        base_ebm_layout.addWidget(ebm_base_form_widget2)
        
        


        ebm_base_form3 = QFormLayout()
        ebm_base_form3.addRow("Powder Size (mm):", self.powdersize)

        
        powdersize_widget = QWidget()
        powdersize_widget.setLayout(ebm_base_form3)
        
        
        EBM_BASE3=QVBoxLayout()
        EBM_BASE3.addWidget(powdersize_widget)
        create_ebm_base_button = QPushButton("Create EBM Base")
        
        create_ebm_base_button.setStyleSheet(next_button_styles)



        create_ebm_base_button.clicked.connect(self.create_ebm_base)
        EBM_BASE3.addWidget(create_ebm_base_button)
        
  
        
        EBM_BASE3_Widget=QWidget()
        EBM_BASE3_Widget.setLayout(EBM_BASE3)
        
        

        base_ebm_layout.addWidget(EBM_BASE3_Widget)
        
        

        # Set Base EBM tab layout
        base_ebm_tab_widget = QWidget()
        base_ebm_tab_widget.setLayout(base_ebm_layout)
        
        '''
        # Start Heat Tab
        start_heat_layout = QVBoxLayout()
        
        # Exposure Area Selection
        exposure_group = QGroupBox("Exposure Area")
        exposure_layout = QVBoxLayout()
        
        self.square_radio = QRadioButton("Square")
        self.circle_radio = QRadioButton("Circle")
        self.square_radio.setChecked(True)
        
        exposure_layout.addWidget(self.square_radio)
        exposure_layout.addWidget(self.circle_radio)
        
        # Square dimensions
        self.square_widget = QWidget()
        square_form = QFormLayout()
        self.square_length = QDoubleSpinBox()
        self.square_length.setRange(0.1, 1000)
        self.square_length.setValue(10)
        square_form.addRow("Length (mm):", self.square_length)
        self.square_widget.setLayout(square_form)
        
        # Circle dimensions
        self.circle_widget = QWidget()
        circle_form = QFormLayout()
        self.circle_radius = QDoubleSpinBox()
        self.circle_radius.setRange(0.1, 1000)
        self.circle_radius.setValue(5)
        circle_form.addRow("Radius (mm):", self.circle_radius)
        self.circle_widget.setLayout(circle_form)
        
        exposure_layout.addWidget(self.square_widget)
        exposure_layout.addWidget(self.circle_widget)
        self.circle_widget.hide()
        
        exposure_group.setLayout(exposure_layout)
        
        # Connect radio buttons
        self.square_radio.toggled.connect(lambda checked: self.square_widget.setVisible(checked))
        self.circle_radio.toggled.connect(lambda checked: self.circle_widget.setVisible(checked))
        
        # Beam Settings
        beam_group = QGroupBox("Beam Settings")
        beam_form = QFormLayout()
        
        self.spot_size = QDoubleSpinBox()
        self.spot_size.setRange(0.1, 100)
        self.spot_size.setValue(1.0)
        
        self.beam_current = QDoubleSpinBox()
        self.beam_current.setRange(0.1, 1000)
        self.beam_current.setValue(10.0)
        
        beam_form.addRow("Spot Size (mm):", self.spot_size)
        beam_form.addRow("Beam Current (mA):", self.beam_current)
        
        beam_group.setLayout(beam_form)
        
        start_heat_layout.addWidget(exposure_group)
        start_heat_layout.addWidget(beam_group)
        
        create_heat_button = QPushButton("Create Start Heat")
        create_heat_button.clicked.connect(self.create_start_heat)
        start_heat_layout.addWidget(create_heat_button)
        
        start_heat_widget = QWidget()
        start_heat_widget.setLayout(start_heat_layout)
        '''
        start_heat_layout = QHBoxLayout()  # Changed from QVBoxLayout to QHBoxLayout

        # ===== Exposure Area =====
        exposure_group = QGroupBox("Exposure Area")
        exposure_layout = QVBoxLayout()
        
        
        self.circle_radio = QRadioButton("Circle")
        self.square_radio = QRadioButton("Square")
        self.circle_radio.setChecked(True)
        
        
        
        exposure_layout.addWidget(self.circle_radio)
        exposure_layout.addWidget(self.square_radio)



        
        
        # Circle dimensions
        self.circle_widget = QWidget()
        circle_form = QFormLayout()
        self.circle_radius = QDoubleSpinBox()
        self.circle_radius.setRange(0.1, DEFAULT_BASE_RADIUS/1000)
        self.circle_radius.setValue(DEFAULT_BASE_RADIUS/1000)
        circle_form.addRow("Radius (mm):", self.circle_radius)
        self.circle_widget.setLayout(circle_form)
        

        
        # Square dimensions
        self.square_widget = QWidget()
        square_form = QFormLayout()
        self.square_length = QDoubleSpinBox()
        self.square_length.setRange(0.1, DEFAULT_BASE_RADIUS*2/1000)
        self.square_length.setValue(DEFAULT_BASE_RADIUS*2/1000)
        self.square_length.setDisabled(True)  # Make it read-only
       # square_form.addRow("Length (mm):", self.square_length)
        square_form.addRow("NOT AVAILABLE", self.square_length)
        
        self.square_widget.setLayout(square_form)
        
        exposure_layout.addWidget(self.circle_widget)
        exposure_layout.addWidget(self.square_widget)
        
        
        self.square_widget.hide()
        self.circle_radio.toggled.connect(lambda checked: self.circle_widget.setVisible(checked))
        self.square_radio.toggled.connect(lambda checked: self.square_widget.setVisible(checked))

        
        exposure_group.setLayout(exposure_layout)
        
        # ===== Beam Settings =====
        beam_group = QGroupBox("Beam Settings")
        beam_form = QFormLayout()
        
        self.spot_size = QDoubleSpinBox()
        self.spot_size.setRange(0.1, 10000)
        self.spot_size.setValue(2000)
        
        self.beam_current = QDoubleSpinBox()
        self.beam_current.setRange(0.1, 2000)
        self.beam_current.setValue(600)
        
        self.target_temp = QDoubleSpinBox()
        self.target_temp.setRange(0, 2000)
        self.target_temp.setValue(800)
        
        self.dwell_time = QDoubleSpinBox()
        self.dwell_time.setRange(0.01, 100)
        self.dwell_time.setValue(20)
        
        beam_form.addRow("Spot Size (mm):", self.spot_size)
        beam_form.addRow("Beam Current (mA):", self.beam_current)
        beam_form.addRow("Target Temp (°C):", self.target_temp)
        beam_form.addRow("Dwell Time (ms):", self.dwell_time)
        
        beam_group.setLayout(beam_form)
        
        # ===== Spot Spread Settings =====
        spread_group = QGroupBox("Spot Spread")
        spread_form = QFormLayout()
        
        self.spread_algorithm = QComboBox()
        self.spread_algorithm.addItems(["snake", "random",'single directional'])
        #alternative
        #also top to down or ....
        
        self.jump_length = QDoubleSpinBox()
        self.jump_length.setRange(1, 100)
        self.jump_length.setValue(2)
        
        spread_form.addRow("Algorithm:", self.spread_algorithm)
        spread_form.addRow("Jump Length (mm):", self.jump_length)
        
        spread_group.setLayout(spread_form)
        
        #=======ADDITIONAL==============
        #$$$$$$
        #ADDITIONAL LIKE GRID , SEED AND OTHER THIGNS ,.....
        
        # ===== Add to Main Horizontal Layout =====
        start_heat_layout.addWidget(exposure_group)
        start_heat_layout.addWidget(beam_group)
        start_heat_layout.addWidget(spread_group)
        
        
        self.pro_heat_option = QCheckBox("Pro Start Heat")
        self.pro_heat_option.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:checked {
                background-color: #28a745;  /* green when checked */
                border-radius: 10px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #cccccc;  /* gray when off */
                border-radius: 10px;
            }
        """)
        self.pro_heat_option.stateChanged.connect(self.on_pro_heat_toggled)
        #start_heat_layout.addWidget(self.pro_heat_option)



        # ===== Button =====
        create_demo_heat_button = QPushButton("Demo Start Heat")
        create_demo_heat_button.clicked.connect(self.demo_start_heat)
        
        
        
        # ===== Button =====
        button_layout = QVBoxLayout()
        create_heat_button = QPushButton("Create Start Heat")
        create_heat_button.setStyleSheet(next_button_styles)
        
        

        create_heat_button.clicked.connect(self.create_start_heat)
        
        
        button_layout.addWidget(self.pro_heat_option)
        button_layout.addWidget(create_demo_heat_button)
        button_layout.addWidget(create_heat_button)
        
        start_heat_layout.addLayout(button_layout)
        
        # ===== Final Widget Assignment =====
        start_heat_widget = QWidget()
        start_heat_widget.setLayout(start_heat_layout)
        
        
        sub_tabs.addTab(base_ebm_tab_widget, "Base EBM")
        sub_tabs.addTab(start_heat_widget, "Start Heat")
        
    
        
        main_layout.addWidget(sub_tabs)

        #===================================================
        #------------------Final setup---------
        
        box_tab.setLayout(main_layout)
        self.tabs.addTab(box_tab, "Create Box")
        
        

    
    def on_pro_heat_toggled(self, state):
        """Toggle Pro start-heat mode on or off based on checkbox state."""
        if state == Qt.Checked:
            self.start_heat_is_Pro_state=True
            print("Pro Start Heat ENABLED")
        else:
            self.start_heat_is_Pro_state=False
            print("Pro Start Heat DISABLED")

        
    def demo_start_heat(self):
        """Run a demo start-heat path and show it in a plot dialog (no state saved)."""
        if self.EBM_base_is_created!=True:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Empty EBM Base")
            msg_box.setText("The EBM Base is Empty.\n"
                            "Please go to the EBM Base section, create a base entry, and then continue.")
            msg_box.setStandardButtons(QMessageBox.Ok )
            response = msg_box.exec_()
            return
        
        
        
        if self.square_radio.isChecked():
            start_heat_shape = "Square"
            start_heat_dimension = self.square_length.value() * 1000  # Get square length
                        
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Not Available")
            msg_box.setText("The square is not available .\n")
            msg_box.setStandardButtons(QMessageBox.Ok )
            response = msg_box.exec_()
            return
        
        
        else:
            start_heat_shape = "Circle"
            start_heat_dimension = self.circle_radius.value() *1000  # Get circle radius
    
        spread_algorithm=self.spread_algorithm.currentText()
        jump_length=self.jump_length.value() * 1000
    
    
        heat_process=Core_Heat_Processor()
        
        points=heat_process.start_heat_generatore_demo(start_heat_shape,start_heat_dimension,spread_algorithm,jump_length)
        

        if points:
            xs, ys = zip(*points)
            dialog = PlotDialog(xs, ys, spread_algorithm)
            dialog.exec_()
 
       

       
   
    def create_start_heat(self):
        """Create and store start-heat parameters from UI; mark box step complete and switch to next tab."""
        if self.EBM_base_is_created!=True:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Empty EBM Base")
            msg_box.setText("The EBM Base is Empty.\n"
                            "Please go to the EBM Base section, create a base entry, and then continue.")
            msg_box.setStandardButtons(QMessageBox.Ok )
            response = msg_box.exec_()
            return

            
            
            
            
        else:
        
            if self.square_radio.isChecked():
                self.start_heat_shape = "Square"
                self.start_heat_dimension = self.square_length.value() * 1000  # Get square length
                
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("Not Available")
                msg_box.setText("The square is not available .\n")
                msg_box.setStandardButtons(QMessageBox.Ok )
                response = msg_box.exec_()
                return
            
            
            else:
                self.start_heat_shape = "Circle"
                self.start_heat_dimension = self.circle_radius.value() * 1000  # Get circle radius
        
            # Get beam settings
            self.start_heat_spot_size = self.spot_size.value()
            self.start_heat_beam_current = self.beam_current.value()
            
            self.start_heat_target_temp=self.target_temp.value()
            self.start_heat_temp_sensor='Sensor 1'
            
            #????
            self.start_heat_dwell_time=self.dwell_time.value() * 1000
            self.start_heat_algorithm = self.spread_algorithm.currentText()
            self.start_heat_jump_length=self.jump_length.value() * 1000
            
            
           # self.start_heat_algorithem=self.spread_algorithm.currentText()
                
            
            
    
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)  # Information icon
            msg.setWindowTitle("Setup Completed")
            msg.setText("Start heat setup has been completed successfully.")
            msg.setStandardButtons(QMessageBox.Ok)  # Add an OK button
           
            
            result = msg.exec_()  # Execute the message box and capture the return value
    
            if result == QMessageBox.Ok:
                #--------------update teh tabs----------------------------
                # Update workflow state
                self.workflow_state['box_created'] = True
                self.update_tab_states()
                self.tabs.setCurrentIndex(1)  # Switch to the next tab
           
 
    
 
   
    def create_box(self):
        """Build the build-volume box from UI dimensions (cm) and display it in the plotter."""
        x = self.box_x.value() 
        y = self.box_y.value()
        z = self.box_z.value()
        
        
        
        if x>100 or y>100 or z>100:
            warning_msg = QMessageBox()
            warning_msg.setIcon(QMessageBox.Warning)
            warning_msg.setWindowTitle("Dimension Warning")
            warning_msg.setText("Please be careful! The box dimensions are in centimeters (CM).")
            warning_msg.setStandardButtons(QMessageBox.Ok)
            warning_msg.exec_()
        

        #for viewer it is better if it was on the main (0, 0, 0,)
        #aslso we must check teh algorithem
        self.box = pv.Box(bounds=(-x*10/2, x*10/2, -y*10/2, y*10/2, -z*10/2, z*10/2))
        #self.box = pv.Box(bounds=(0, x*10, 0, y*10, 0, z*10))
        self.plotter.clear()
        self.plotter.add_mesh(self.box, color="lightgray", opacity=0.3)
        self.plotter.add_axes()
        self.plotter.render()



        #--------update_tabs----------------
        # Update workflow state
        self.workflow_state['box_created'] = True
        self.update_tab_states()
        # Automatically switch to the next tab
        self.tabs.setCurrentIndex(1)
        #self.tabs.setFixedSize(1400, 300)  # Set the size of the tab widget




    #??? where is center
    def create_ebm_base(self):
        """Build the EBM base (cylinder) from defaults and display it; set EBM_base_is_created."""
        #radius = self.plate_radius.value() * 10  # Convert to mm
        #thickness = self.plate_thickness.value() * 10  # Convert to mm
        
        self.radius =DEFAULT_BASE_RADIUS
        thickness =DEFAULT_BASE_THICKNESS
        
        
        
        # Create a cylinder (flat disc with volume) at Z < 0
        #no self.base_plate 
        self.box = pv.Cylinder(
            center=(0, 0, -thickness / 2),  # Place it under z=0
            direction=(0, 0, 1),  # Upward normal
            radius=self.radius,
            height=thickness,
            resolution=100  # Smooth appearance
        )
    
        # Clear and add the new shape
        #oinstead of self.--> box
        
        self.plotter.clear()
        self.plotter.add_mesh(self.box, color="lightgray", opacity=0.3)
        self.plotter.add_axes()
        self.plotter.render()
        self.EBM_base_is_created=True
        
        
        
        '''
        #--------------update teh tabs----------------------------
        # Update workflow state
        self.workflow_state['box_created'] = True
        self.update_tab_states()
        self.tabs.setCurrentIndex(1)  # Switch to the next tab
        '''




    #----------------------------------------------
    #----------------------------------------------
    #----------------------------------------------
    '''              Geometry Tab              '''
    #----------------------------------------------
    #----------------------------------------------
    #----------------------------------------------

    def setup_geometry_tab(self):
        """Build the Geometry tab: import STL, transform, center, save, primitives, and go-to-slicer."""
        
        
        
        #===========================================================
        #------------Create Setup of Geometry with buttons-----------
        geometry_tab = QWidget()
        main_layout=QHBoxLayout()
        
        #left layout------------------------
        left_layout_widget=QWidget()
        left_layout=QVBoxLayout()

        #left layout ----- Main buttons at top panel
        main_buttons_layout=QHBoxLayout()

        import_button = QPushButton("Import STL File")
        import_button.clicked.connect(self.import_file)
        main_buttons_layout.addWidget(import_button)

        apply_button = QPushButton("Apply Transformation")
        apply_button.clicked.connect(self.update_transformation)
        main_buttons_layout.addWidget(apply_button)

        center_button = QPushButton("Placed on Center")
        center_button.clicked.connect(self.update_center_button)
        main_buttons_layout.addWidget(center_button)
        
        save_button = QPushButton("Save Transformed STL")
        save_button.clicked.connect(self.save_stl)
        main_buttons_layout.addWidget(save_button)
        
        next_to_slice_button = QPushButton("Go To slicer Madule")
        next_to_slice_button.clicked.connect(self.next_to_slicer)
        
        next_to_slice_button.setStyleSheet("""
    QPushButton {
        background-color: #28a745;   /* Bootstrap-like green */
        color: white;
        font-weight: bold;
        border-radius: 3px;
        padding: 4px 12px;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #43A047;   /* Slightly darker on hover */
    }
    QPushButton:pressed {
        background-color: #388E3C;   /* Even darker when pressed */
    }
""")


        main_buttons_layout.addWidget(next_to_slice_button)


        #if main_button_layout cna not add layer
        #we can use widget and then
        
        #left layout -----inputs at top panel
        inputs_layout=QHBoxLayout()


        movement_layout=QVBoxLayout()
        self.input_x = QLineEdit("0")
        self.input_y = QLineEdit("0")
        self.input_scale = QLineEdit("1")
        
        movement_form = QFormLayout()
        movement_form.addRow("Movement in axis X (mm):", self.input_x)
        movement_form.addRow("Movement in axis Y (mm):", self.input_y)
        movement_form.addRow("Scaler (x):", self.input_scale)
        
        movement_widget = QWidget()
        movement_widget.setLayout(movement_form)
        movement_layout.addWidget(movement_widget)
        
        rotation_layout=QVBoxLayout()
        self.input_rx = QLineEdit("0")
        self.input_ry = QLineEdit("0")
        self.input_rz = QLineEdit("0")
        
        rotation_form = QFormLayout()
        rotation_form.addRow("Rotation around RX (°):", self.input_rx)
        rotation_form.addRow("Rotation around RY (°):", self.input_ry)
        rotation_form.addRow("Rotation around RZ (°) :", self.input_rz)
        
        rotation_widget = QWidget()
        rotation_widget.setLayout(rotation_form)
        rotation_layout.addWidget(rotation_widget)
        

        multiple_layout=QVBoxLayout()
        self.input_multiple = QLineEdit("1")
        self.input_space = QLineEdit("10")
        
        multiple_form = QFormLayout()
        multiple_form.addRow("Number of replicated object :", self.input_multiple)
        multiple_form.addRow("space between them (Cm):", self.input_space)
        
        multiple_widget = QWidget()
        multiple_widget.setLayout(multiple_form)
        multiple_layout.addWidget(multiple_widget)


        multiple_button_layout=QVBoxLayout()
        apply_multiply_button = QPushButton("Apply Multiples")
        apply_multiply_button.clicked.connect(self.apply_multiply)
        multiple_button_layout.addWidget(apply_multiply_button)
        
        final_multiply_button = QPushButton("Finalise Multiple numbers")
        final_multiply_button.setStyleSheet("background-color: lightgreen;")

        final_multiply_button.clicked.connect(self.final_multiply)
        multiple_button_layout.addWidget(final_multiply_button)
        

        inputs_layout.addLayout(movement_layout)
        inputs_layout.addLayout(rotation_layout)
        inputs_layout.addLayout(multiple_layout)
        inputs_layout.addLayout(multiple_button_layout)

        
        left_layout.addLayout(main_buttons_layout)
        left_layout.addLayout(inputs_layout)
        left_layout_widget.setLayout(left_layout)
        #right layout--------------------------
        #right_layout_widget=QWidget()
        #right_layout=QVBoxLayout()
        #right_layout_widget.setLayout(right_layout)
        
        #???
        #check this geom_icons/
        
        icon_layout = QHBoxLayout()  
        button_layout = QVBoxLayout()  
        button_names = ["Cube", "Rectangular Box", "Cylinder", "Sphere", "Pyramid", "Cone"]
        functions = [self.create_cube, self.create_rectangular_box, self.create_cylinder, self.create_sphere, self.create_pyramid, self.create_cone]  # Corresponding functions
        for i, (button_name, func) in enumerate(zip(button_names, functions), 1):
            button = QPushButton(f"{button_name}")
            button.setIcon(QIcon(f"geom_icons/icon{i}.png"))  # Assuming icons are named icon1.png, icon2.png, etc.
            button.clicked.connect(lambda _, func=func, button_name=button_name: self.ask_for_parameters(func, button_name))  # Pass function and button name
            button_layout.addWidget(button)
        
        button_layout.addStretch()
        icon_layout.addLayout(button_layout)
        
        main_layout.addWidget(left_layout_widget)
        #main_layout.addWidget(right_layout_widget)
        main_layout.addLayout(icon_layout)
        
        

        
        geometry_tab.setLayout(main_layout)
        
        self.tabs.addTab(geometry_tab, "Import Geometry")
        
        #$$$
        #other formats and tehn to STL ,...
        
        '''
        # 2. 3MF Tab
        three_mf_tab = QWidget()
        three_mf_layout = QVBoxLayout()
        
        create_3mf_button = QPushButton("Import 3MF File")
        create_3mf_button.clicked.connect(self.create_3mf)
        three_mf_layout.addWidget(create_3mf_button)
        three_mf_tab.setLayout(three_mf_layout)

        tab_widget.addTab(stl_tab, "STL")
        tab_widget.addTab(three_mf_tab, "3MF")

        layout.addWidget(tab_widget)
        '''
        
        
        
        
        

    #----------------------------------------------
    '''              Import Button             '''
    #----------------------------------------------
    
        
    def import_file(self):
        """Open file dialog and load selected STL file via load_stl."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Import STL File", "", 
                                                 "STL Files (*.stl);;All Files (*)", options=options)
        if file_path:
            self.load_stl(file_path)



    def load_stl(self, file_path,from_icons=False):
        """Load STL from file_path; optionally scale if too large; display in plotter. from_icons skips trimesh load."""
        try:
            #---------one is mesh in trimesh obkject
            #-------another in pv style
            
            if from_icons==True:
                pass
            else:
                self.mesh = trimesh.load_mesh(file_path)

            if self.check_size_of_object(self.mesh)=='normal':
                pass
            
            
            elif self.check_size_of_object(self.mesh)=='large':
                
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("Large STL Detected")
                msg_box.setText("The STL volume is larger than allowed volume).\n"
                                "Do you want to scale it automatically?")
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                response = msg_box.exec_()
                if response == QMessageBox.Yes:
                    # Scale the mesh
                    self.mesh=self.rescale_to_fit(self.mesh)
                elif response == QMessageBox.Cancel:
                    print("STL loading cancelled by user.")
                    return  # Stop the function
                
                
            elif self.check_size_of_object(self.mesh)=='small':
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("Small STL Detected")
                msg_box.setText("The STL volume is too small than normal volume. Our dimensions are in Millimeter.\n"
                                "Do you want to scale it automatically?")
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                response = msg_box.exec_()
                if response == QMessageBox.Yes:
                    # Scale the mesh
                    self.mesh=self.rescale_to_fit_milli(self.mesh)
                elif response == QMessageBox.Cancel:
                    print("STL loading cancelled by user.")
                    return  # Stop the function
                

            #------------------------------------------------
 
            vertices = self.mesh.vertices  # (N, 3) array of (x, y, z) points

            min_z = vertices[:, 2].min()  # Lowest Z coordinate
            change_value=-1*min_z
            translation=[0,0,0]
            translation[2]=float(change_value)
            self.mesh.apply_translation(translation)
            #------
            self.pv_mesh = pv.wrap(self.mesh)
            self.plotter.clear()
            if self.box:
                self.plotter.add_mesh(self.box, color="lightgray", opacity=0.3)
            #self.plotter.add_mesh(self.pv_mesh, color="orange")

            self.plotter.add_mesh(self.pv_mesh, color="black")
            
            self.plotter.add_axes()

            self.plotter.render()

            print(f"Loaded STL file: {file_path}")

        except Exception as e:
            print(f"Failed to load STL file: {e}")
            self.mesh=None
            self.pv_mesh=None
            # Show the error in a QMessageBox
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("Failed to load STL file.")
            error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()
            
            
            
    #it must check carefully in future *******
    def check_size_of_object(self,mesh):
        """Classify mesh size vs EBM base: 'large', 'small', or 'normal' (in mm, Z_MAX_EBM_BASE)."""
        Z_MAX=Z_MAX_EBM_BASE
        #bounding_box = self.mesh.bounds  # Min and max points
        #mesh_width = bounding_box[1][0] - bounding_box[0][0]  # X size
        #mesh_length = bounding_box[1][1] - bounding_box[0][1]  # Y size
        vertices_xy = mesh.vertices[:, :2]  # Extract (x, y) coordinates
        # Compute squared distance from origin (0,0) in XY plane
        distances_squared = np.sum(vertices_xy**2, axis=1)
        # Check if all points are inside the circle
        inside = np.all(distances_squared <= self.radius**2)

        z_values = mesh.vertices[:, 2]  # Extract Z values
        mesh_height = np.max(z_values) - np.min(z_values)
        inside_height = mesh_height <= Z_MAX
        
        
        
        
        outside = np.all(distances_squared <= self.radius**2/10000)
        outside_height = mesh_height <= Z_MAX/1000
        
        
        
        
        if inside==False or inside_height==False: 
            print('large........')
            return 'large'
        
        elif outside==True or outside_height==True:
            print('small........')
            return 'small'
        else:
            print('normall........')
            return 'normal'
        
        
        
        

        
        
    def rescale_to_fit_milli(self,mesh):
        """Scale mesh (in mm) to fit within base radius and Z_MAX; may up-scale or down-scale. Returns scaled trimesh."""
        #or just * 100
        Z_MAX=Z_MAX_EBM_BASE
        vertices = mesh.vertices
        x_y = vertices[:, :2]  # Extract (x, y)
        z_values = vertices[:, 2]  # Extract Z values
        # Compute current max distance from (0,0) in XY plane
        distances = np.sqrt(np.sum(x_y**2, axis=1))
        max_xy = np.max(distances)  # Farthest point from center
        # Compute current height (Z range)
        current_height = np.max(z_values) - np.min(z_values)
        # Compute scale factors
        scale_xy = max_xy / self.radius if max_xy < self.radius/100 else 1.0
        scale_z =current_height/ Z_MAX  if current_height < Z_MAX/100 else 1.0
        # Use the smallest scale to ensure both conditions are met
        scale_factor = min(scale_xy, scale_z)
        
        print(f'{scale_factor} ........')

        #----it must changeeee......
        if scale_factor>1000:
            scale_factor=1000
            mesh.apply_scale(scale_factor)
            
            final_mesh=self.rescale_to_fit(mesh)
            
            
        else:
            scale_factor=1/scale_factor
           
            
            mesh.apply_scale(scale_factor)
            final_mesh=self.rescale_to_fit(mesh)
            print(f"Mesh scaled by factor {scale_factor:.4f} to fit within bounds.")
        
        return final_mesh

        
      


    def rescale_to_fit(self,mesh):
        """Scale mesh down to fit within base radius and Z_MAX if needed; return mesh (possibly in-place scaled)."""
        Z_MAX=Z_MAX_EBM_BASE
        vertices = mesh.vertices
        x_y = vertices[:, :2]  # Extract (x, y)
        z_values = vertices[:, 2]  # Extract Z values
        # Compute current max distance from (0,0) in XY plane
        distances = np.sqrt(np.sum(x_y**2, axis=1))
        max_xy = np.max(distances)  # Farthest point from center
        # Compute current height (Z range)
        current_height = np.max(z_values) - np.min(z_values)
        # Compute scale factors
        scale_xy = self.radius / max_xy if max_xy > self.radius else 1.0
        scale_z = Z_MAX / current_height if current_height > Z_MAX else 1.0
        # Use the smallest scale to ensure both conditions are met
        scale_factor = min(scale_xy, scale_z)
        
        print(f'{scale_factor} ........')

        #----it must changeeee......
        if scale_factor < 1.0:  # Only scale if needed
            mesh.apply_scale(scale_factor)
            print(f"Mesh scaled by factor {scale_factor:.4f} to fit within bounds.")
            
            return mesh
        else:
            print("Mesh already fits inside the circle and height limit.")
            return mesh


    





    

    #----------------------------------------------
    '''              Save Button             '''
    #----------------------------------------------
    def save_stl(self):
        """Save current mesh to STL via file dialog; warns if multiples applied but not finalized."""
        if self.click_on_apply_multiple==True:
            
            if self.it_is_final_multiples==False:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("The numbers go out the boundary")
                msg_box.setText("You apply multipel object but until you don't finalize , it doesn't apply!"
                                "Do you want to continue only with one object?")
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
    
                response = msg_box.exec_()
    
                if response == QMessageBox.Yes:
                    pass
    
                elif response == QMessageBox.Cancel:
                    print("STL loading cancelled by user.")
                    return  # Stop the function 
            else:
                pass
                


        if not self.mesh:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("No STL file loaded!")
            #error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()
            
            print("No STL file loaded!")
            return
        
        #in transformation we have indicator and said you dont change anything to save
        file_path, _ = QFileDialog.getSaveFileName(self, "Save STL File", "", 
                                                 "STL Files (*.stl);;All Files (*)")
        if file_path:
            
            try:
                self.mesh.export(file_path)
                print(f"Saved STL file: {file_path}")
                
            except Exception as e:
                print(f"Failed to save STL file: {e}")
                # Show the error in a QMessageBox
                error_msg = QMessageBox()
                error_msg.setIcon(QMessageBox.Critical)
                error_msg.setWindowTitle("Error")
                error_msg.setText("Failed to save STL file.")
                error_msg.setInformativeText(str(e))  # Display the error message
                error_msg.exec_()
                
                
    
    
    
    #----------------------------------------------
    '''        Transformation  Button           '''
    #----------------------------------------------
    def update_transformation(self):
        """Apply scale, translation, and rotation from geometry inputs to current mesh and redraw."""
        if self.click_on_apply_multiple==True:
            
            if self.it_is_final_multiples==False:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("The numbers go out the boundary")
                msg_box.setText("You apply multipel object but until you don't finalize , it doesn't apply!"
                                "Do you want to continue only with one object?")
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
    
                response = msg_box.exec_()
    
                if response == QMessageBox.Yes:
                    pass
    
                elif response == QMessageBox.Cancel:
                    print("STL loading cancelled by user.")
                    return  # Stop the function  
            else:
                pass
            
            
        if not self.mesh:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("No STL file loaded!")
            #error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()
            
            print("No STL file loaded!")
            return
        
        try:
            self.transform_for_once=1
            scale_factor = float(self.input_scale.text())
            scale_matrix = trimesh.transformations.scale_matrix(scale_factor)
            self.mesh.apply_transform(scale_matrix)

            # Update translation
            self.translation[0] = float(self.input_x.text())*1000
            self.translation[1] = float(self.input_y.text())*1000
            #self.translation[2] = float(self.input_z.text())

            # Update rotation angles
            rx = float(self.input_rx.text())
            ry = float(self.input_ry.text())
            rz = float(self.input_rz.text())

            # Apply translation
            self.mesh.apply_translation(self.translation)


            # Generate rotation matrices and apply rotations
            #mayeb based on center of teh obejct *********
            
            rot_x = trimesh.transformations.rotation_matrix(np.radians(rx), [1, 0, 0])
            rot_y = trimesh.transformations.rotation_matrix(np.radians(ry), [0, 1, 0])
            rot_z = trimesh.transformations.rotation_matrix(np.radians(rz), [0, 0, 1])

            # Combine rotations and apply
            combined_rotation = trimesh.transformations.concatenate_matrices(rot_x, rot_y, rot_z)
            self.mesh.apply_transform(combined_rotation)
            #again check that
            #-------ensure that 
            vertices = self.mesh.vertices  # (N, 3) array of (x, y, z) points
            min_z = vertices[:, 2].min()  # Lowest Z coordinate
            change_value=-1*min_z
            translation=[0,0,0]
            translation[2]=float(change_value)
            self.mesh.apply_translation(translation)
            #--------


            # Update visualization
            #***also we change the pv_mesh
            self.pv_mesh = pv.wrap(self.mesh)
            self.plotter.clear()
            if self.box:
                self.plotter.add_mesh(self.box, color="lightgray", opacity=0.3)
            self.plotter.add_mesh(self.pv_mesh, color="orange")
            self.plotter.add_axes()
            self.plotter.render()


            # Reset input fields
            self.input_x.setText("0")
            self.input_y.setText("0")
            
            #self.input_z.setText("0")
            self.input_scale.setText("1")
            
            self.input_rx.setText("0")
            self.input_ry.setText("0")
            self.input_rz.setText("0")

        except ValueError:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("Please enter valid numeric values for translation and rotation.!")
            #error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()
            
            print("Please enter valid numeric values for translation and rotation.")
            

    

    #----------------------------------------------
    '''              Place Button             '''
    #----------------------------------------------

    def update_center_button(self):
        """Center mesh on base and move min Z to 0; update plotter."""
        if self.click_on_apply_multiple==True:
            print('yes click on it')
            if self.it_is_final_multiples==False:
                print('no not finalized')
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("The numbers go out the boundary")
                msg_box.setText("You apply multipel object but until you don't finalize , it doesn't apply!"
                                "Do you want to continue only with one object?")
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
    
                response = msg_box.exec_()
    
                if response == QMessageBox.Yes:
                    pass
    
                elif response == QMessageBox.Cancel:
                    print("STL loading cancelled by user.")
                    return  # Stop the function
                
            else:
                pass
            
  
        if not self.mesh:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("No STL file loaded!")
            #error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()
            
            print("No STL file loaded!")
            return

        #center_x, center_y, _ = self.box.center
        #print(f"Center of the object: X = {center_x}, Y = {center_y}")

        centroid = self.mesh.center_mass
        
        translation_vector = -np.array(centroid)



        #center_x=0
        #center_y=0
        #translatioon + cnetroid = center
        
        translation_vector = -np.array(centroid)

        self.mesh.apply_translation(translation_vector)

        vertices = self.mesh.vertices  # (N, 3) array of (x, y, z) points
        min_z = vertices[:, 2].min()  # Lowest Z coordinate
        change_value=-1*min_z
        translation=[0,0,0]
        translation[2]=float(change_value)
        self.mesh.apply_translation(translation)
        

        self.pv_mesh = pv.wrap(self.mesh)
        self.plotter.clear()
        if self.box:
            self.plotter.add_mesh(self.box, color="lightgray", opacity=0.3)
        self.plotter.add_mesh(self.pv_mesh, color="orange")
        self.plotter.add_axes()
        self.plotter.render()
    

    
    
    #----------------------------------------------
    '''              Multiple Button           '''
    #----------------------------------------------

    def apply_multiply(self):
        """Create preview of multiple copies from inputs (count, spacing); show demo_mesh or offer rescale."""
        if self.click_on_apply_multiple==True and self.it_is_final_multiples==True:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("FTER FINALIZING THE MULTIPLE, YOU CAN NOT USE MULTIPLE AGAIN!")
            error_msg.exec_()
            return
        self.click_on_apply_multiple=True
        
        if not self.mesh:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("No STL file loaded!")
            #error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()
            print("No STL file loaded!")
            return
        
        
        if self.check_size_of_object(self.mesh)=='large':
            
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Large STL Detected")
            msg_box.setText("The STL volume is larger than allowed volume).\n"
                            "Do you want to scale it automatically?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

            response = msg_box.exec_()

            if response == QMessageBox.Yes:
                # Scale the mesh
                self.mesh=self.rescale_to_fit(self.mesh)

            elif response == QMessageBox.Cancel:
                print("STL loading cancelled by user.")
                return  # Stop the function
            
        try:
            
            bounding_box = self.mesh.bounds  # shape: (2, 3), [min_xyz, max_xyz]
            min_bounds, max_bounds = bounding_box
            
            length_x = max_bounds[0] - min_bounds[0]  # width
            length_y = max_bounds[1] - min_bounds[1]  # depth
            #length_z = max_bounds[2] - min_bounds[2]  # height
            
            min_space=max(length_x,length_y)


            num_objects = int(self.input_multiple.text())  # Number of replicated objects
            space_between = float(self.input_space.text())*1000 + min_space # Space between objects (mm)
            
            if num_objects <= 0 or space_between <= 0:
                raise ValueError("Both values must be positive numbers.")
    
        except ValueError as e:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText(f"Invalid input: {e}")
            error_msg.exec_()
            return

        centroid = self.mesh.center_mass
        
        translation_vector = -np.array(centroid)

        #center_x=0
        #center_y=0
        #translatioon + cnetroid = center
        translation_vector = -np.array(centroid)
        self.mesh.apply_translation(translation_vector)

        meshes_to_merge = []
        #bounding_box = self.mesh.get_bounding_box()
        #bounding_box = self.mesh.bounds
        grid_size = math.ceil(math.sqrt(num_objects))  # Create a square grid layout for the objects

        for i in range(num_objects):
            
            row = i // grid_size
            col = i % grid_size
            new_position = np.array([col * space_between, row * space_between, 0])  # Distribute along X and Y
            # Calculate the new position for each mesh (space along one axis, e.g., X-axis)
            #new_position = np.array([i * space_between, 0, 0])  # Distribute along X
            # Make a copy of the original mesh and move it to the new position
            new_mesh = self.mesh.copy()  # Create a copy of the mesh
            new_mesh.apply_translation(new_position)  # Move the new mesh
            # Add the transformed mesh to the list
            meshes_to_merge.append(new_mesh)
        global_mesh = trimesh.util.concatenate(meshes_to_merge)

        # Optionally, you can apply further transformations on the global mesh if needed
        #self.apply_transformations_to_global_mesh(global_mesh)
    
        # Add the global mesh to the scene or visualization
        #self.add_global_mesh_to_scene(global_mesh)
        #self.mesh=global_mesh
        if self.check_size_of_object(global_mesh)=='large':
            
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("The numbers go out the boundary")
            msg_box.setText("The length of this object go out of the boundary.\n"
                            "The software automatically decrease the scale of object to fit inside the EBM base.\n"
                            "Do you want to continue?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

            response = msg_box.exec_()
            if response == QMessageBox.Yes:

                # Scale the mesh
                self.demo_mesh=self.rescale_to_fit(global_mesh)

            elif response == QMessageBox.Cancel:
                print("STL loading cancelled by user.")
                return  # Stop the function

        else:
            self.demo_mesh=global_mesh
            

        centroid = self.demo_mesh.center_mass
        
        translation_vector = -np.array(centroid)
        #center_x=0
        #center_y=0
        #translatioon + cnetroid = center
        
        translation_vector = -np.array(centroid)

        self.demo_mesh.apply_translation(translation_vector)
        
        #------------------------------------------------
        vertices = self.demo_mesh.vertices  # (N, 3) array of (x, y, z) points
        # Find the minimum Z value
        min_z = vertices[:, 2].min()  # Lowest Z coordinate
        change_value=-1*min_z
        translation=[0,0,0]
        translation[2]=float(change_value)
        self.demo_mesh.apply_translation(translation)
        

        self.pv_mesh = pv.wrap(self.demo_mesh)
        self.plotter.clear()
        if self.box:
            self.plotter.add_mesh(self.box, color="lightgray", opacity=0.3)
        self.plotter.add_mesh(self.pv_mesh, color="orange")
        self.plotter.add_axes()
        self.plotter.render()
        
        
        


        
        
        
    def final_multiply(self):
        """Commit demo_mesh as the current mesh and show success message."""
        self.it_is_final_multiples=True

        self.mesh=self.demo_mesh
        
        self.pv_mesh = pv.wrap(self.mesh)
        self.plotter.clear()
        if self.box:
            self.plotter.add_mesh(self.box, color="lightgray", opacity=0.3)
        self.plotter.add_mesh(self.pv_mesh, color="orange")
        self.plotter.add_axes()
        self.plotter.render()
        
        info_msg = QMessageBox()
        info_msg.setIcon(QMessageBox.Information)
        info_msg.setWindowTitle("Multiple Object")
        info_msg.setText("Successfull")
        info_msg.setStandardButtons(QMessageBox.Ok)
        info_msg.exec_()
        
        
        






    #----------------------------------------------
    '''          Basic STL buttons             '''
    #----------------------------------------------
    
    def ask_for_parameters(self, func, shape_name):
        """
        Ask for parameters dynamically based on the shape type when a button is clicked.
        :param func: The geometry creation function
        :param shape_name: The name of the shape (used to customize the dialog)
        """
        # Depending on the shape, we'll ask for different parameters
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Enter {shape_name} Parameters")
        
        form_layout = QFormLayout(dialog)
    
        # Define input fields based on the shape
        if shape_name == "Cube":
            size_input = QLineEdit("10.0")  # Default value for cube size
            form_layout.addRow("Size:", size_input)
    
        elif shape_name == "Cylinder":
            radius_input = QLineEdit("5.0")
            height_input = QLineEdit("20.0")
            form_layout.addRow("Radius:", radius_input)
            form_layout.addRow("Height:", height_input)
    
        elif shape_name == "Sphere":
            radius_input = QLineEdit("10.0")
            form_layout.addRow("Radius:", radius_input)
    
        elif shape_name == "Pyramid":
            base_size_input = QLineEdit("10.0")
            height_input = QLineEdit("15.0")
            form_layout.addRow("Base Size:", base_size_input)
            form_layout.addRow("Height:", height_input)
    
        elif shape_name == "Cone":
            radius_input = QLineEdit("5.0")
            height_input = QLineEdit("15.0")
            form_layout.addRow("Radius:", radius_input)
            form_layout.addRow("Height:", height_input)
            
            
        elif shape_name == "Rectangular Box":
            length_input = QLineEdit("20.0")
            width_input = QLineEdit("10.0")
            height_input = QLineEdit("10.0")
            
            form_layout.addRow("Length:", length_input)
            form_layout.addRow("Width:", width_input)
            form_layout.addRow("Height:", height_input)
            
            
            
    
        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        form_layout.addWidget(button_box)
    
        if dialog.exec_() == QDialog.Accepted:
            # Retrieve the values entered by the user
            values = {}
            if shape_name == "Cube":
                values['size'] = float(size_input.text())*1000
            elif shape_name == "Cylinder":
                values['radius'] = float(radius_input.text())*1000
                values['height'] = float(height_input.text())*1000
            elif shape_name == "Sphere":
                values['radius'] = float(radius_input.text())*1000
            elif shape_name == "Pyramid":
                values['base_size'] = float(base_size_input.text())*1000
                values['height'] = float(height_input.text())*1000
            elif shape_name == "Cone":
                values['radius'] = float(radius_input.text())*1000
                values['height'] = float(height_input.text())*1000
                
            elif shape_name == "Rectangular Box":
                values['length'] =float(length_input.text())*1000
                values['width'] = float(width_input.text())*1000
                values['height'] = float(height_input.text())*1000
                
    
            # Create the shape using the entered values
            self.create_shape(func, values)
    
    def create_shape(self, func, values):
        """
        Call the shape creation function with the provided parameters.
        :param func: The function that creates the mesh (e.g., create_cube, create_sphere, etc.)
        :param values: A dictionary of parameters to pass to the function (size, radius, etc.)
        """
        mesh = func(**values)  # Pass the parameters to the function
        self.mesh=mesh
        
        self.load_stl(file_path=None,from_icons=True)
        
        #self.display_mesh(mesh)  # Call a function to display the generated mesh (you can implement this)
    
    
    def create_cube(self,size=10.0):
        """
        Create a cube mesh.
        :param size: Length of each side of the cube.
        :return: Trimesh mesh of a cube.
        """
        return trimesh.creation.box(extents=(size, size, size))
    
    
    
    def create_rectangular_box(self, length=10.0, width=10.0, height=10.0):
        """
        Create a rectangular box mesh.
        :param length: Length of the box.
        :param width: Width of the box.
        :param height: Height of the box.
        :return: Trimesh mesh of a rectangular box.
        """
        return trimesh.creation.box(extents=(length, width, height))
    
    
    
    def create_sphere(self,radius=10.0):
        """
        Create a sphere mesh.
        :param radius: Radius of the sphere.
        :return: Trimesh mesh of a sphere.
        """
        return trimesh.creation.icosphere(subdivisions=3, radius=radius)
    
    def create_cylinder(self,radius=5.0, height=20.0):
        """
        Create a cylinder mesh.
        :param radius: Radius of the cylinder.
        :param height: Height of the cylinder.
        :return: Trimesh mesh of a cylinder.
        """
        return trimesh.creation.cylinder(radius=radius, height=height, sections=32)
    
    def create_cone(self,radius=5.0, height=15.0):
        """
        Create a cone mesh.
        :param radius: Base radius of the cone.
        :param height: Height of the cone.
        :return: Trimesh mesh of a cone.
        """
        return trimesh.creation.cone(radius=radius, height=height, sections=32)
    
    def create_torus(self,radius_major=10.0, radius_minor=3.0):
        """
        Create a torus (donut shape) mesh.
        :param radius_major: Distance from the center to the middle of the tube.
        :param radius_minor: Radius of the tube.
        :return: Trimesh mesh of a torus.
        """
        return trimesh.creation.torus(radius_major=radius_major, radius_minor=radius_minor, sections=32)
    
    def create_pyramid(self,base_size=10.0, height=15.0):
        """
        Create a pyramid mesh.
        :param base_size: Length of the square base.
        :param height: Height of the pyramid.
        :return: Trimesh mesh of a pyramid.
        """
        # Define vertices
        vertices = np.array([
            [0, 0, 0],  # Base corner 1
            [base_size, 0, 0],  # Base corner 2
            [base_size, base_size, 0],  # Base corner 3
            [0, base_size, 0],  # Base corner 4
            [base_size / 2, base_size / 2, height]  # Pyramid peak
        ])
        
        # Define faces
        faces = np.array([
            [0, 1, 2], [0, 2, 3],  # Base
            [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]  # Sides
        ])
        
        return trimesh.Trimesh(vertices=vertices, faces=faces)
    
    
    #$$$$
    
    def extra_stl(self):
        """Placeholder for extra STL actions (not implemented)."""
        pass
        
    def create_3mf(self):
        """Placeholder for 3MF import (not implemented)."""
        pass
       
        

    
    #----------------------------------------------
    '''          Final Button                '''
    #----------------------------------------------

    #^^^^^^^^^
    #also
    #$$$ 
    #the calculation must go to PM_EBM_CORE
    
    def next_to_slicer(self):
        """Validate mesh/multiples then set geometry_saved and switch to Slicing tab."""
        if self.click_on_apply_multiple==True:
            if self.it_is_final_multiples==False:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("The numbers go out the boundary")
                msg_box.setText("You apply multipel object but until you don't finalize , it doesn't apply!"
                                "Do you want to continue only with one object?")
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
    
                response = msg_box.exec_()
    
                if response == QMessageBox.Yes:
                    pass

                elif response == QMessageBox.Cancel:
                    print("STL loading cancelled by user.")
                    return  # Stop the function
            else:
                pass
            

        if not self.mesh:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("No STL file loaded!")
            #error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()
            
            print("No STL file loaded!")
            return
        
        
        
        #check that

        our_mesh=self.pv_mesh

        #our_mesh.save("our_final_mesh.vtk")
        
        #slice_plane = our_mesh.slice(normal=[0, 0, 1], origin=[0, 0, 0])
        #squares=self.get_minimum_bounding_squares_pyvista(slice_plane, overlap_threshold=20)
        
        ##first_sl,shapely_n_objects=self.first_slice_shapely()
        #also we can first pv mesh and then go to the shapely and ...

       #squares=self.get_minimum_bounding_squares_pyvista(our_mesh, overlap_threshold=20)
       
        slice_plane = our_mesh.slice(normal=[0, 0, 1], origin=[0, 0, 0.00000000000000001])
        #slice_plane.save("slice_plane_main.vtk")
        #print(type(slice_plane))
        #poly_slice_plane=pv.PolyData(slice_plane)
        squares=self.get_minimum_bounding_squares_pyvista(slice_plane, overlap_threshold=20)

        self.numb_object_based_on_squares=len(squares)
        self.object_boundary_squares= squares 

        #first_sl,shapely_n_objects=self.first_slice_shapely()
        
        first_sl,shapely_n_objects=self.first_slice_shapely(self.pv_mesh)

        if shapely_n_objects==self.numb_object_based_on_squares:
            
            if self.numb_object_based_on_squares>1:
            
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("Multiple objects detected)")
                msg_box.setText(f"{self.numb_object_based_on_squares} objects are detected!\n"
                                "The software consider multiple objects or not (only single object)?")
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    
                response = msg_box.exec_()
    
                if response == QMessageBox.Yes:
                    pass
    
                elif response == QMessageBox.No:
                    
                    self.numb_object_based_on_squares==1
                    
                    #it consideer only one 
                    #pass
    
                    return  # Stop the function
            else:
                
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("single object detected)")
                msg_box.setText(f"{self.numb_object_based_on_squares} object is detected!\n"
                                "Do you confirm there is only one object ?")
                
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    
                response = msg_box.exec_()
                
                if response == QMessageBox.Yes:
                    self.numb_object_based_on_squares==1
                    
                    pass
    
                elif response == QMessageBox.No:
    
                    #wqe must go for advaces
                    #it consideer only one 
    
                    return  # Stop the function
                
                
        else:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("Somehting get wrong with object detections")
            #error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()
            
            print("No STL file loaded!")
            
            #if yes it dconsider one 
            #if it said no , it can not
            #maybe some tools to get circle and square around its object
            return

        # Update workflow state
        self.workflow_state['geometry_saved'] = True
        self.update_tab_states()
        
        # Automatically switch to the next tab
        self.tabs.setCurrentIndex(2)
        #self.tabs.setFixedSize(1450, 250)

        self.plotter.add_mesh(self.pv_mesh, color="black")
        
        
        
    #must perform based on Core...
    #It must perform in PM_EBM_CORE 
    def first_slice_shapely(self,mesh):
        """Slice mesh at z≈0, polygonize contours, return Shapely geometry (polygon or MultiPolygon) and count."""
        slice_plane = mesh.slice(normal=[0, 0, 1], origin=[0, 0, 0.00000000000000001])
    
        if slice_plane is None:
            print('error')
        try:
            # Get all cells from the slice plane
            polygons = []
            
            # Get unique cells that form closed loops
            edges = []
            for i in range(slice_plane.n_cells):
                cell = slice_plane.get_cell(i)
                points = cell.points[:, :2]  # Get only X,Y coordinates
                edges.append((points[0], points[1]))
            
            # Use polygonize to create proper polygons from edges
            lines = [LineString(edge) for edge in edges]
            merged_lines = unary_union(lines)
            polygons = list(polygonize(merged_lines))
            
            if not polygons:
                print("No valid polygons found")
                return None
                
            # Create a multipolygon if we have multiple polygons
            if len(polygons) > 1:
                return MultiPolygon(polygons) ,len(polygons)
            else:
                return polygons[0] , len(polygons)
                
        except Exception as e:
            print(f"Error in convert_slice_to_shapely: {str(e)}")
            return None , 0
            

            
    def calculate_overlap_percentage(self,square1, square2):
        """
        Calculate the overlap percentage between two squares.
        
        Parameters:
        - square1, square2: Tuples of (center_x, center_y, side_length)
        
        Returns:
        - float: Overlap percentage relative to the smaller square's area
        """
        x1, y1, s1 = square1
        x2, y2, s2 = square2
        
        # Calculate the intersection rectangle
        x_left = max(x1 - s1/2, x2 - s2/2)
        y_bottom = max(y1 - s1/2, y2 - s2/2)
        x_right = min(x1 + s1/2, x2 + s2/2)
        y_top = min(y1 + s1/2, y2 + s2/2)
        
        # Check if squares overlap
        if x_right > x_left and y_top > y_bottom:
            intersection_area = (x_right - x_left) * (y_top - y_bottom)
            smaller_square_area = min(s1 * s1, s2 * s2)
            return (intersection_area / smaller_square_area) * 100
        return 0
    
    def merge_squares(self,square1, square2):
        """
        Merge two squares into one that encompasses both.
        
        Parameters:
        - square1, square2: Tuples of (center_x, center_y, side_length)
        
        Returns:
        - tuple: New square (center_x, center_y, side_length)
        """
        x1, y1, s1 = square1
        x2, y2, s2 = square2
        
        # Find the extremes of both squares
        left = min(x1 - s1/2, x2 - s2/2)
        right = max(x1 + s1/2, x2 + s2/2)
        bottom = min(y1 - s1/2, y2 - s2/2)
        top = max(y1 + s1/2, y2 + s2/2)
        
        # Calculate new square parameters
        new_side = max(right - left, top - bottom)
        new_center_x = (left + right) / 2
        new_center_y = (bottom + top) / 2
        
        return (new_center_x, new_center_y, new_side)
    
    def optimize_squares(self,squares, overlap_threshold=20):
        """
        Optimize squares by merging overlapping ones and removing contained squares.
        
        Parameters:
        - squares: List of (center_x, center_y, side_length)
        - overlap_threshold: Percentage threshold for merging squares
        
        Returns:
        - list: Optimized squares
        """
        if not squares:
            return []
        
        # Sort squares by area (largest first)
        squares = sorted(squares, key=lambda x: x[2]**2, reverse=True)
        
        # First pass: remove completely contained squares
        i = 0
        while i < len(squares):
            j = i + 1
            while j < len(squares):
                # Check if square j is contained within square i
                overlap = self.calculate_overlap_percentage(squares[i], squares[j])
                if overlap > 95:  # Using 95% as threshold for "completely contained"
                    squares.pop(j)
                else:
                    j += 1
            i += 1
        
        # Second pass: merge overlapping squares
        changed = True
        while changed:
            changed = False
            i = 0
            while i < len(squares):
                j = i + 1
                while j < len(squares):
                    overlap = self.calculate_overlap_percentage(squares[i], squares[j])
                    if overlap > overlap_threshold:
                        # Merge squares i and j
                        new_square = self.merge_squares(squares[i], squares[j])
                        squares.pop(j)
                        squares[i] = new_square
                        changed = True
                    else:
                        j += 1
                i += 1
        
        return squares
    
    def get_minimum_bounding_squares_pyvista(self,mesh, overlap_threshold=20):
        """
        Finds and optimizes minimum bounding squares for each contour in a PyVista mesh.
        
        Parameters:
        - mesh: PyVista PolyData mesh
        - overlap_threshold: Percentage threshold for merging squares
        
        Returns:
        - squares: List of tuples [(center_x, center_y, side_length), ...]
        """
        squares = []
        
        # Get bounds for each separate contour in the mesh
        contours = mesh.split_bodies()
        
        for contour in contours:
            # Get only x and y coordinates
            points = contour.points[:, :2]
            
            # Calculate bounds
            min_x, max_x = np.min(points[:, 0]), np.max(points[:, 0])
            min_y, max_y = np.min(points[:, 1]), np.max(points[:, 1])
            
            # Calculate square parameters
            side_length = max(max_x - min_x, max_y - min_y)
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            
            squares.append((center_x, center_y, side_length))
        
        # Optimize the squares
        return self.optimize_squares(squares, overlap_threshold)








    #----------------------------------------------
    #----------------------------------------------
    #----------------------------------------------
    '''              slice Tab                 '''
    #----------------------------------------------
    #----------------------------------------------
    #----------------------------------------------

    def setup_slicing_tab(self):
        """Build Slicing tab: layer/interval options, Slice/Analyze/Finalize buttons, status area."""
        #===================================================
        #------------------------Setup---------------------

        slicing_tab = QWidget()
        layout = QHBoxLayout()  # Horizontal layout to place widgets side-by-side
    
        # Left panel for form and buttons
        left_panel = QVBoxLayout()
        form = QFormLayout()
        
        
        self.layer_radio = QRadioButton("Select Number of Layers")
        self.length_interval_radio = QRadioButton("Select Length interval")
        self.layer_radio.setChecked(True)  # Default to selecting layers

        self.select_n_layers = QSpinBox()
        self.select_n_layers.setRange(1, 10000)
        self.select_n_layers.setValue(10)
        #form.addRow("Number of Layers:", self.select_n_layers)
        
        
        self.select_layer_interval = QSpinBox()
        self.select_layer_interval.setRange(1, 100)
        self.select_layer_interval.setValue(1)
        self.select_layer_interval.setEnabled(False)  # Disable diameter by default

        
        form.addRow(self.layer_radio, self.select_n_layers)
        form.addRow(self.length_interval_radio, self.select_layer_interval)
        
        
        self.layer_radio.toggled.connect(self.layer_lentgh_toggle_selection)

        form_widget = QWidget()
        form_widget.setLayout(form)
        left_panel.addWidget(form_widget)
    
        slice_button = QPushButton("Slice Model")
        slice_button.clicked.connect(self.slicing)
        left_panel.addWidget(slice_button)
        
        analyze_button = QPushButton("Analyze Model")
        analyze_button.clicked.connect(self.slice_analyzing)
        left_panel.addWidget(analyze_button)
    
        next_button = QPushButton("Finalize Model")
        
        next_button.setStyleSheet(next_button_styles)
        
        
        next_button.clicked.connect(self.after_slice)
        left_panel.addWidget(next_button)
    
        left_panel.addStretch()
    
        # Right panel for status messages
        right_panel = QVBoxLayout()
        self.status_label = QLabel("Status: Not analyzed yet")
        self.status_label.setWordWrap(True)  # Allow text to wrap if too long
        self.status_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        #self.status_label.setStyleSheet("color: black;")  # Set text color to black
        
        
        # Set the background color to black and text color to white
        self.status_label.setStyleSheet("""
            color: white;  /* Text color */
            background-color: black;  /* Background color */
            border: 1px solid gray;  /* Optional border for clarity */
            padding: 5px;  /* Optional padding for better spacing */
        """)

        #right_panel.addWidget(self.status_label)
        
        self.slicer_scroll_area = QScrollArea()
        self.slicer_scroll_area.setWidget(self.status_label)  # Add QLabel to QScrollArea
        self.slicer_scroll_area.setWidgetResizable(True)  # Allow the QLabel to adjust its size within the scroll area
        self.slicer_scroll_area.setFixedHeight(200)  # Set a fixed height for the scroll area
        self.slicer_scroll_area.setStyleSheet("""
            border: 1px solid gray;  /* Match border style with QLabel */
        """)
        
        # Add the scroll area to the layout
        right_panel.addWidget(self.slicer_scroll_area)
    

        # Add left and right panels to main layout
        layout.addLayout(left_panel, stretch=3)
        layout.addLayout(right_panel, stretch=2)

        slicing_tab.setLayout(layout)
        self.tabs.addTab(slicing_tab, "Slicing")
        
  
    
    def layer_lentgh_toggle_selection(self):
        """Enable number-of-layers or length-interval spinbox based on selected radio."""
        if self.layer_radio.isChecked():
            self.select_n_layers.setEnabled(True)
            self.select_layer_interval.setEnabled(False)
        else:
            self.select_n_layers.setEnabled(False)
            self.select_layer_interval.setEnabled(True)
        
        




    



    #-------------------------------------
    '''       slice button             '''
    #-------------------------------------

    #^^^^^^^^^^ mayeb is better smewhere else
    #check taht after slicing the numebrs restart?
    def slicing(self):
        """Run mesh slicing (Core_Mesh_Processor); set slice planes, layer count, and height for later analyze."""
        PM_PROCESSOR=Core_Mesh_Processor()
        
        
        if not self.pv_mesh:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("No STL file loaded!")
            #error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()

            return
        
        
        if self.select_n_layers.value()>100:
            info_msg = QMessageBox()
            info_msg.setIcon(QMessageBox.Information)
            info_msg.setWindowTitle("Processing Information")
            info_msg.setText("Creating layers may take some time. Please wait patiently.")
            info_msg.setStandardButtons(QMessageBox.Ok)
            info_msg.exec_()
            
            
          
        
        self.plotter.clear()
        
        if self.length_interval_radio.isChecked():
            
            self.select_layer_interval=self.select_layer_interval.value()*1000
            if self.box:
                self.plotter.add_mesh(self.box, color="lightgray", opacity=0.3)


            self.test_slice_planes, self.slice_n_layers ,self.slice_layer_height,self.number_of_successive_layer,self.number_of_failed_geom,self.number_of_failed_slice,self.failed_slice_id=PM_PROCESSOR.pyvista_slicer(self.pv_mesh,layer_interval=self.select_layer_interval)
            for plane in self.test_slice_planes:
                self.plotter.add_mesh(plane, color="blue", opacity=0.6)
                

        elif self.layer_radio.isChecked():
            
            self.selected_n_layers = self.select_n_layers.value()
            
            
            if self.box:
                self.plotter.add_mesh(self.box, color="lightgray", opacity=0.3)


            self.test_slice_planes, self.slice_n_layers ,self.slice_layer_height,self.number_of_successive_layer,self.number_of_failed_geom,self.number_of_failed_slice,self.failed_slice_id=PM_PROCESSOR.pyvista_slicer(self.pv_mesh,n_layers=self.selected_n_layers)
            for plane in self.test_slice_planes:
                self.plotter.add_mesh(plane, color="blue", opacity=0.6)


        self.plotter.add_axes()
        self.plotter.render()   
        self.is_sliced=True
        #----------in beststl08 we have something from previous if needed




    def slice_analyzing(self):
        """Update slice analysis and status display from current slice data."""
        #here is in beststl08 the all of teh code but now it convert to 
        #slice and here only we achieved the mai parameters for shows
        if self.is_sliced is not True:
            
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("First slice your object and then you can analyze")
            #error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()
            return

        # Determine the color for each line based on the conditions
        self.color_slice = "red" if self.number_of_failed_slice > 0 else "green"
        self.color_geom = "red" if self.number_of_failed_geom > 0 else "green"

        self.run_slice_stage=self.run_slice_stage+1

        current_datetime = datetime.now()
        slice_time_run = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        # Create the styled message
        self.s_message = f'''--------------------------------------------<br>
        <span style='color:white;'> Run stage number. {self.run_slice_stage} || Time : {slice_time_run} </span><br>
        <br>--------------------------------------------<br>
                <span style='color:white;'>Totally {self.number_of_successive_layer} Layers are build successfully !.</span><br>
                <span style='color:{self.color_slice};'>There are {self.number_of_failed_slice} failed slices without points.</span><br>
                <span style='color:{self.color_geom};'>There are {self.number_of_failed_geom} failed geoms.</span><br>
        '''
        if len(self.failed_slice_id)>0:
            self.s_message=self.s_message+f'''<span style='color:red;'>the id of failed layers from z=0 : {self.failed_slice_id}</span><br>'''
        
        if self.run_slice_stage==1:
            self.slice_message_status=self.s_previous_message + '================================================== \n' + self.s_message
            self.s_previous_message=self.s_message
        else:
            self.slice_message_status=self.slice_message_status + '================================================== \n' + self.s_message
             

        if self.slice_message_status is None:
            self.status_label.setText("----------------STATUS----------:\n Waiting for analyzing .......")
            
        else:
        # Update the label with the styled message
            self.status_label.setText(f"----------------STATUS----------:<br>{self.slice_message_status}")
            # Auto-scroll to the bottom

        vertical_scroll_bar = self.slicer_scroll_area.verticalScrollBar()
        vertical_scroll_bar.setValue(vertical_scroll_bar.maximum()+200)
        #message=f'''------------STATUS AFTER ANALYZING-------------\n
        #there is  {self.number_of_failed_slice} failed slices without points \n 
        #there is {self.number_of_failed_geom} failed geom \n
        
        #'''
        #self.status_label.setText(f"Status: {message}")

        



    def after_slice(self):
        """Finalize slice (copy to finalized_*), set workflow state, and switch to Preheating tab."""
        if not self.pv_mesh:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("No STL file loaded!")
            #error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()

            return
        
        
        if self.is_sliced is not True:
            
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("First slice your object and then you can analyze")
            #error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()
            return
        
        
        
        #maybee more details are needed
        details=f"""
        
        object sliced to {self.number_of_successive_layer} layers 

        
        """
        
        # Create the message box
        message_box = QMessageBox()
        message_box.setWindowTitle("Confirm Details")
        message_box.setText(f"This is your object with the following details:\n\n{details}\n\nDo you want to continue?")
        message_box.setIcon(QMessageBox.Question)
        
        # Add Yes and No buttons
        message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        message_box.setDefaultButton(QMessageBox.No)
    
        # Execute the message box and get the user's response
        user_response = message_box.exec()
    
    
    
        # Handle the user's response
        if user_response == QMessageBox.Yes:
            print("User chose to continue.")
            #search this teh name of finaized before finzal
            #self.final_slice_planes=self.test_slice_planes
            
            self.finalized_test_slice_planes=self.test_slice_planes
            self.finalized_slice_n_layers=self.slice_n_layers
            self.finalized_slice_layer_height=self.slice_layer_height



            # Update workflow state
            self.workflow_state['slicing_completed'] = True
            self.update_tab_states()
            # Automatically switch to the next tab
            self.tabs.setCurrentIndex(3)
            
            print('=============')
            print(self.finalized_slice_n_layers)
            
            
            
            # Proceed with the next step
        elif user_response == QMessageBox.No:
            print("User chose not to continue.")
            #self.final_slice_planes=None
            
            self.finalized_test_slice_planes=None
            return
        
        
        

        
    #----------------------------------------------
    #----------------------------------------------
    #----------------------------------------------
    '''              PRE HEAT Tab                 '''
    #----------------------------------------------
    #----------------------------------------------
    #----------------------------------------------
    
    '''
    self.pro_heat_option = QCheckBox("Pro Start Heat")
    self.pro_heat_option.setStyleSheet("""
        QCheckBox {
            font-weight: bold;
        }
        QCheckBox::indicator {
            width: 20px;
            height: 20px;
        }
        QCheckBox::indicator:checked {
            background-color: #28a745;  /* green when checked */
            border-radius: 10px;
        }
        QCheckBox::indicator:unchecked {
            background-color: #cccccc;  /* gray when off */
            border-radius: 10px;
        }
    """)
    self.pro_heat_option.stateChanged.connect(self.on_pro_heat_toggled)
    
    
    def on_pro_heat_toggled(self, state):
        """Toggle Pro start-heat option in preheating tab (slicing tab duplicate)."""
        if state == Qt.Checked:
            self.start_heat_is_Pro_state=True
            print("Pro Start Heat ENABLED")
        else:
            self.start_heat_is_Pro_state=False
            print("Pro Start Heat DISABLED")


'''




    def setup_preheating_tab(self):
        """Build Preheating tab: jump-safe settings, preview/apply, and finalize."""
        preheating_tab = QWidget()
        main_layout = QHBoxLayout()
        splitter = QSplitter()
    

    
        #////////////////////////////////////////////////
        #////////////////////////////////////////////////
        
        #------------ JUMP SAFE ----------------------
        
        #////////////////////////////////////////////////
        #////////////////////////////////////////////////

        #==========================================================
        #==========================================================

        jumpsafe_tabs = QTabWidget()
        
        
        j_pixel_tab = QWidget()
        j_pixel_layout = QVBoxLayout()
        
        #j_pixel ****
        j_pixel_layout.addWidget(QLabel("Jump safe - PIXEL Algorithm Settings"))
        
        #form_layout = QFormLayout()
        
        form_layout_left = QFormLayout()
        form_layout_right = QFormLayout()
        
        
        
        # Algorithm Selection
        self.j_pixel_algorithm_selector = QComboBox()
        self.j_pixel_algorithm_selector.addItems(["Snake", "Random", "Single Directional"])
        self.j_pixel_algorithm_selector.setCurrentText("Random")
        form_layout_left.addRow("Algorithm:", self.j_pixel_algorithm_selector)
        


        # Shape
        self.j_pixel_shape_selector = QComboBox()
        self.j_pixel_shape_selector.addItems(["Square", "Circle"])
        self.j_pixel_shape_selector.setCurrentText("Circle")
        form_layout_left.addRow("Shape:", self.j_pixel_shape_selector)
        
        
        # Length/Radius
        self.j_pixel_length_radius_input = QDoubleSpinBox()
        self.j_pixel_length_radius_input.setRange(1, DEFAULT_BASE_RADIUS/1000)
        self.j_pixel_length_radius_input.setValue(DEFAULT_BASE_RADIUS/1000)
        form_layout_left.addRow("Length/Radius:", self.j_pixel_length_radius_input)
        
        


        # Jump Length
        self.j_pixel_jump_length_input = QDoubleSpinBox()
        self.j_pixel_jump_length_input.setRange(0, 200)
        self.j_pixel_jump_length_input.setValue(2)
        form_layout_left.addRow("Jump Length (mm):", self.j_pixel_jump_length_input)
        
        
        
        # Theta
        self.j_pixel_theta_input = QDoubleSpinBox()
        self.j_pixel_theta_input.setRange(-360, 360)
        self.j_pixel_theta_input.setSingleStep(45)  # Only 45-degree steps
        self.j_pixel_theta_input.setValue(0)
        form_layout_left.addRow("Theta:", self.j_pixel_theta_input)
        

        #-----right side------


        
        
        # Dwell Time
        self.j_pixel_dwell_time_input = QDoubleSpinBox()
        self.j_pixel_dwell_time_input.setRange(0, 100)
        self.j_pixel_dwell_time_input.setValue(60) 
        form_layout_right.addRow("Dwell Time (micros):", self.j_pixel_dwell_time_input)
        
        
        # Repetition
        self.j_pixel_repetition_input = QSpinBox()
        self.j_pixel_repetition_input.setRange(1, 100)
        self.j_pixel_repetition_input.setValue(10)
        form_layout_right.addRow("Repetitions:", self.j_pixel_repetition_input)
        
        
        
        # Spot Size
        self.j_pixel_spot_size_input = QDoubleSpinBox()
        self.j_pixel_spot_size_input.setRange(1, 10000)  # Adjust as needed
        self.j_pixel_spot_size_input.setValue(2000)      # Default value in micrometers
        form_layout_right.addRow("Spot Size (µm):", self.j_pixel_spot_size_input)
        
        # Power
        self.j_pixel_power_input = QDoubleSpinBox()
        self.j_pixel_power_input.setRange(0, 1000)       # Adjust range based on your system
        self.j_pixel_power_input.setValue(600)           # Default value in Watts
        form_layout_right.addRow("Power (W):", self.j_pixel_power_input)


        
        # Pro Option Toggle
        self.j_pixel_pro_option = QCheckBox("Pro Jump Heat")
        self.j_pixel_pro_option.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:checked {
                background-color: #28a745;
                border-radius: 10px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #cccccc;
                border-radius: 10px;
            }
        """)
        self.j_pixel_pro_option.stateChanged.connect(self.on_j_pro_heat_toggled)
        
        form_layout_right.addRow(self.j_pixel_pro_option)
        
        
        
        # Combine both form layouts into a horizontal layout
        horizontal_form_layout = QHBoxLayout()
        horizontal_form_layout.addLayout(form_layout_left)
        horizontal_form_layout.addLayout(form_layout_right)
        
        
        
        

        # Add the horizontal layout to the main layout
        j_pixel_layout.addLayout(horizontal_form_layout)
        j_pixel_tab.setLayout(j_pixel_layout)
        


        
        # Add form to main layout
        #First_layout.addLayout(form_layout)
        
        
        

        
       # j_pixel_skip_button = QPushButton("Skip")
       # j_pixel_skip_button.clicked.connect(self.j_pixel_skip)
       # j_pixel_layout.addWidget(j_pixel_skip_button)
        
        
        
        self.j_pixel_skip = QPushButton("Skip")
        self.j_pixel_skip.setCheckable(True)
        self.j_pixel_skip.clicked.connect(self.toggle_j_pixel_form_enabled)
        
        self.j_pixel_skip.setStyleSheet("""
    QPushButton {
        background-color: red;
        color: white;
        font-weight: bold;
        border: 1px solid darkred;
        border-radius: 4px;
        padding: 4px 8px;
    }
    QPushButton:checked {
        background-color: darkred;
    }
""")


        j_pixel_layout.addWidget(self.j_pixel_skip)
        
        
        
        
        # Preview
        j_pixel_preview_button = QPushButton("Preview")
       # j_pixel_preview_button.clicked.connect(self.preview_spatter_line_algorithem)
        j_pixel_preview_button.clicked.connect(self.preview_jump_pixel)
        j_pixel_layout.addWidget(j_pixel_preview_button)
        
        # Apply
        j_pixel_apply_button = QPushButton("Apply Settings")
       # j_pixel_apply_button.clicked.connect(self.spatter_line_algorithem)
        j_pixel_apply_button.clicked.connect(self.apply_jump_pixel)
        j_pixel_apply_button.setStyleSheet(next_button_styles)
        j_pixel_layout.addWidget(j_pixel_apply_button)
        
        j_pixel_tab.setLayout(j_pixel_layout)
        jumpsafe_tabs.addTab(j_pixel_tab, "PIXEL Algorithms")


    
    
    
    

        #----------------------------------------------------------
        # Jumpsafe - Line Algorithm Tab
        j_line_tab = QWidget()
        j_line_layout = QVBoxLayout()

        
        j_line_layout.addWidget(QLabel("<h2>Coming Soon</h2>", alignment=Qt.AlignCenter))
        j_line_tab.setLayout(j_line_layout)
        jumpsafe_tabs.addTab(j_line_tab, "Line Algorithms")
        
        

        
    
        splitter.addWidget(jumpsafe_tabs)
    

    
    
    
        #////////////////////////////////////////////////
        #////////////////////////////////////////////////
        
        #------------ SPATTER SAFE ----------------------
        
        #////////////////////////////////////////////////
        #////////////////////////////////////////////////
        
        
        #===================================================
        # Left section (Spattersafe)
        spattersafe_tabs = QTabWidget()
        
        
        First_tab = QWidget()
        First_layout = QVBoxLayout()
        
        
        
        First_layout.addWidget(QLabel("<h2>Coming Soon</h2>", alignment=Qt.AlignCenter))
        First_tab.setLayout(First_layout)
        spattersafe_tabs.addTab(First_tab, "PIXEL Algorithm")


        



        #----------------------------------------------------------
        # Spattersafe - Line Algorithm Tab

        line_tab = QWidget()
        line_layout = QVBoxLayout()

    
        
        line_layout.addWidget(QLabel("<h2>Coming Soon</h2>", alignment=Qt.AlignCenter))
        line_tab.setLayout(line_layout)
        spattersafe_tabs.addTab(line_tab, "Line Algorithms")
        
        

        
        splitter.addWidget(spattersafe_tabs)
    
    
    


        #======================
        #======================
        #======================
        #======================
        #======================
        #======================
        
        
        # Add Splitter to Layout
        main_layout.addWidget(splitter)
        
        final_preheat = QPushButton("Final Preheat")
        
        final_preheat.setStyleSheet(next_button_styles)
        final_preheat.clicked.connect(self.Final_preheating)
        main_layout.addWidget(final_preheat)
        
        
        preheating_tab.setLayout(main_layout)
        # Add this tab to the main QTabWidget
        self.tabs.addTab(preheating_tab, "Pre-heating")
        
        
        
    def j_pixel_skip(self):
        """Placeholder for jump-pixel skip toggle (not implemented)."""
        pass
        
    
    
    def toggle_j_pixel_form_enabled(self):
        """Enable/disable jump-safe form and update button text/style based on skip checkbox."""
        is_disabled = self.j_pixel_skip.isChecked()
        
        # Update button text
        if is_disabled:
            self.j_pixel_skip.setText("Activate Jump safe")
            
            self.j_pixel_skip_is=True
            
            self.j_pixel_skip.setStyleSheet("""
    QPushButton {
        background-color: red;
        color: white;
        font-weight: bold;
        border: 1px solid darkred;
        border-radius: 4px;
        padding: 4px 8px;
    }
    QPushButton:checked {
        background-color: #007BFF;  /* Bootstrap blue */
        border: 1px solid #0056b3;
    }
""")

        else:
            self.j_pixel_skip_is=False
            self.j_pixel_skip.setText("Skip")
    
        # Disable or enable all form widgets
        for widget in [
            self.j_pixel_algorithm_selector,
            self.j_pixel_repetition_input,
            self.j_pixel_shape_selector,
            self.j_pixel_length_radius_input,
            self.j_pixel_jump_length_input,
            self.j_pixel_theta_input,
            self.j_pixel_dwell_time_input,
            self.j_pixel_pro_option,
            self.j_pixel_spot_size_input,
            self.j_pixel_power_input
        ]:
            widget.setDisabled(is_disabled)
        
        
    
    
    #in preview and other ....
    #it must self.j_pixel_skip check thi sand say first activate
    
    
    
    def on_j_pro_heat_toggled(self):
        """Placeholder for jump-pixel Pro heat toggle (not implemented)."""
        pass
    #----------also here we neeed this CORE-------------------------
    
   
    
    
    #previous --> #preview_spatter_line_algorithem
    def preview_jump_pixel(self):
        """Preview jump-safe pattern from UI settings; show plot or prompt to activate first."""
        #if self.j_pixel_skip.isChecked():
        if self.j_pixel_skip_is:
            QMessageBox.information(self, "Skip Active", "Please activate the settings first to preview.")
            return
    
        # Read settings from UI
        j_pixel_shape = self.j_pixel_shape_selector.currentText()
        j_pixel_algorithm = self.j_pixel_algorithm_selector.currentText()
        
        try:
            j_pixel_length_or_radius = float(self.j_pixel_length_radius_input.value()) * 1000
            j_pixel_jump = float(self.j_pixel_jump_length_input.value()) * 1000
            j_pixel_theta = float(self.j_pixel_theta_input.value())
            j_pixel_dwell = float(self.j_pixel_dwell_time_input.value()) * 1000
            j_pixel_repetitions = int(self.j_pixel_repetition_input.value())
            pro_heat_enabled = self.j_pixel_pro_option.isChecked()
    
    
    
    
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numerical values.")
            return
        
        if j_pixel_shape=='Square':
            QMessageBox.information(self, "Not Available", "Square shape is not available.")
            return
        
        else:
            
            
            self.plotter.interactor.setVisible(False)
            self.canvas.setVisible(True)
            
            
            heat_process=Core_Heat_Processor()
            points=heat_process.jump_safe_generatore_demo(j_pixel_shape.lower(),j_pixel_length_or_radius, j_pixel_algorithm.lower(), j_pixel_jump,j_pixel_theta)
            if points:
                self.plot_jump_algorithem(points,DEFAULT_BASE_RADIUS  )

     
            
            
    
            
    #very very basic and just lines
    def plot_jump_algorithem1(self, points, radius):
        """
        Plots a circle and parallel lines using pairs of given points.
        
        Parameters:
        - points: List of (x, y) tuples.
        - radius: Radius of the circle (defines the boundary).
        """
        self.ax.clear()  # Clear the previous plot
    
        # Plot the circle boundary
        circle = plt.Circle((0, 0), radius, color='r', fill=False, linewidth=2)
        self.ax.add_artist(circle)
    
        # Plot lines between consecutive pairs of points
        for i in range(0, len(points) - 1, 2):
            x_values, y_values = zip(*[points[i], points[i + 1]])
            self.ax.plot(x_values, y_values, 'b-', linewidth=1.5)
    
        # Formatting
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.set_xlim(-radius - 1, radius + 1)
        self.ax.set_ylim(-radius - 1, radius + 1)
        self.ax.set_title("Parallel Lines Inside a Circle")
    
        self.canvas.draw()
        
        
        
        
    #from upper but with colour
    def plot_jump_algorithem2(self, points, radius):
        """
        Plots a circle and visualizes the order of given points.
        
        Parameters:
        - points: List of (x, y) tuples.
        - radius: Radius of the circle (defines the boundary).
        """
        self.ax.clear()
    
        # Draw the boundary circle
        circle = plt.Circle((0, 0), radius, color='r', fill=False, linewidth=2)
        self.ax.add_artist(circle)
    
        # Use a colormap to represent progression
        cmap = get_cmap("viridis")
        total = len(points)
    
        # Plot the points and connect them with lines and arrows
        for i in range(len(points)):
            x, y = points[i]
            color = cmap(i / total)
            self.ax.plot(x, y, 'o', color=color)  # point marker
    
            if i < len(points) - 1:
                x_next, y_next = points[i + 1]
                self.ax.annotate("",
                                 xy=(x_next, y_next), xytext=(x, y),
                                 arrowprops=dict(arrowstyle="->", color=color, lw=1))
    
        # Plot formatting
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.set_xlim(-radius - 1, radius + 1)
        self.ax.set_ylim(-radius - 1, radius + 1)
        self.ax.set_title("Jump Algorithm Order")
    
        self.canvas.draw()
        
        
   #animation
        
    def plot_jump_algorithem(self, points, radius):
        """
        Animates the jump algorithm by plotting points in order inside a circle.
        
        Parameters:
        - points: List of (x, y) tuples.
        - radius: Radius of the circle boundary.
        """
        
        if self.j_pixel_anim:
            self.j_pixel_anim.event_source.stop()
            self.j_pixel_anim = None
        
        
        self.ax.clear()
        
        # Draw circle boundary once
        circle = plt.Circle((0, 0), radius, color='r', fill=False, linewidth=2)
        self.ax.add_artist(circle)
    
        # Plot setup
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.set_xlim(-radius - 1, radius + 1)
        self.ax.set_ylim(-radius - 1, radius + 1)
        self.ax.set_title("Jump Algorithm Animation")
    
        # Initialization lists for animation
        point_dots, = self.ax.plot([], [], 'bo')  # dots
        arrows = []
    
        def init():
            point_dots.set_data([], [])
            return [point_dots] + arrows
    
        def update(frame):
            self.ax.clear()
            self.ax.add_artist(circle)
            self.ax.set_xlim(-radius - 1, radius + 1)
            self.ax.set_ylim(-radius - 1, radius + 1)
            self.ax.set_title("Jump Algorithm Animation")
    
            xs = [pt[0] for pt in points[:frame+1]]
            ys = [pt[1] for pt in points[:frame+1]]
            self.ax.plot(xs, ys, 'bo')
    
            for i in range(frame):
                self.ax.annotate("",
                                 xy=points[i+1], xytext=points[i],
                                 arrowprops=dict(arrowstyle="->", color="blue", lw=1))
            return []
    
        # Create the animation
        #instead of self.anim
        self.j_pixel_anim = FuncAnimation(self.canvas.figure,
                                  update,
                                  frames=len(points),
                                  init_func=init,
                                  interval=70,
                                  repeat=False)
    
        self.canvas.draw()
    
    
    
    
    
    
    
    #previous --> #spatter_line_algorithem
    def apply_jump_pixel(self):
        """Apply jump-safe settings from UI, run generator, and mark preheating step applied."""
        if self.j_pixel_anim:
            self.j_pixel_anim.event_source.stop()
            self.j_pixel_anim = None
    
        # Read settings from UI
        self.jump_pixel_shape = self.j_pixel_shape_selector.currentText()
        self.jump_pixel_algorithm = self.j_pixel_algorithm_selector.currentText()
        
        try:
            self.jump_pixel_length_or_radius = float(self.j_pixel_length_radius_input.value()) * 1000
            self.jump_pixel_jump = float(self.j_pixel_jump_length_input.value()) * 1000
            self.jump_pixel_theta = float(self.j_pixel_theta_input.value())
            self.jump_pixel_dwell = float(self.j_pixel_dwell_time_input.value()) * 1000
            self.jump_pixel_repetitions = int(self.j_pixel_repetition_input.value())
            self.jump_pro_heat_enabled = self.j_pixel_pro_option.isChecked()
    
            self.jump_pixel_spot_size_input=float(self.j_pixel_spot_size_input.value())
            self.jump_pixel_power_input=float(self.j_pixel_spot_size_input.value()    )
    
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numerical values.")
            return
        
        if self.jump_pixel_shape=='Square':
            QMessageBox.information(self, "Not Available", "Square shape is not available.")
            return
        
        else:
            if self.j_pixel_skip_is:
            #if self.j_pixel_skip.isChecked():
                QMessageBox.information(self, "Skip Active", "Jump safe (Not active) is set up successfully")
            else:

                self.plotter.interactor.setVisible(False)
                self.canvas.setVisible(True)
                
                
                heat_process=Core_Heat_Processor()
                points=heat_process.jump_safe_generatore_demo(self.jump_pixel_shape.lower(),self.jump_pixel_length_or_radius, self.jump_pixel_algorithm.lower(), self.jump_pixel_jump,self.jump_pixel_theta)
                if points:
                    self.plot_jump_algorithem2(points,DEFAULT_BASE_RADIUS  )
                    QMessageBox.information(self, "Jump Safe", "Jump Safe setup completed successfully.")
                    
                    self.apply_jump_safe_step=True
    
    


    def main_spatter_line_algorithem(self):
        """Placeholder for main spatter-line algorithm (not implemented)."""
        pass
        

    def spatter_line_algorithem(self):
        """Placeholder for spatter line algorithm (not implemented)."""
        pass

     
    def spatter_pixel_algorithem(self):
        """Placeholder for spatter pixel algorithm (not implemented)."""
        pass
    
    def spatter_random_algorithem(self):
        """Placeholder for spatter random algorithm (not implemented)."""
        pass
    
    def spatter_proheat_algorithem(self):
        """Placeholder for spatter proheat algorithm (not implemented)."""
        pass
    def j_line_algorithem(self):
        """Placeholder for jump line algorithm (not implemented)."""
        pass
    
    def j_pixel_algorithem(self):
        """Placeholder for jump pixel algorithm (not implemented)."""
        pass
    
    def j_random_algorithem(self):
        """Placeholder for jump random algorithm (not implemented)."""
        pass
    def j_proheat_algorithem(self):
        """Placeholder for jump proheat algorithm (not implemented)."""
        pass
    
    
     #parallel_lines_geenrator
     #spot_melting_generator
     #plot_parallel_lines
     #random_spot_generator
     #plot_parallel_lines_in_circle
     #plot_parallel_lines_in_circle2
     #plot_points
     #plot_points_and_lines
     #preview_spatter_line_algorithem
     #they are in BESTSTLEBM1 AND BACK UP OF BESTSTLEBM2
   
    
   
    

    
    def old_Final_preheating(self):
        """Legacy finalize preheating: set workflow state and switch to Hatching tab."""
        if self.is_hatched is not True:
            
            print('No you need first hatch your things')
            
        if self.j_pixel_skip is None:
                QMessageBox.information(self, "Skip Active", "Jump safe is not active, are you sure to continue?")

            

        # Implement preheating functionality
        # After completion:
        self.workflow_state['preheating_completed'] = True
        self.update_tab_states()
        self.tabs.setCurrentIndex(4) #before5
        
        
    def Final_preheating(self):
        """Confirm jump-safe (or skip), then set preheating_completed and switch to Hatching tab."""
        #if not self.is_hatched:
        #    QMessageBox.warning(self, "Warning", "No, you need to hatch your geometry first.")
       #     return
    
        #if self.j_pixel_skip is None or not self.j_pixel_skip.isChecked(): 
        if self.j_pixel_skip_is:
        #if self.j_pixel_skip.isChecked():
            reply = QMessageBox.question(
                self,
                "Jump Safe Not Active",
                "Jump safe is not active. Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        elif self.apply_jump_safe_step is not True:
            QMessageBox.warning(self, "Warning", "No,  First you must apply your selected pre-heating pattern with click on Apply.")
            return

            
    
        # Implement preheating functionality
        # After completion:
        self.workflow_state['preheating_completed'] = True
        self.update_tab_states()
        self.tabs.setCurrentIndex(4)  # before5



    #----------------------------------------------
    #----------------------------------------------
    #----------------------------------------------
    '''             HATCHING Tab                 '''
    #----------------------------------------------
    #----------------------------------------------
    #----------------------------------------------
    
    #why hatching not work?? about this --> 

    def setup_hatching_tab(self):
        """Build Hatching tab with sub-tabs: Raster, Spiral, Contour, Island."""
        #some lines regarding the layout but it is in beststl08
        self.hatch_pattern=None
        
        hatching_tab = QWidget()
        layout = QHBoxLayout() 
        
        
        #new tab for different pattern
        subtabs = QTabWidget()
        
        raster_tab = self.create_raster_tab()
        spiral_tab = self.create_spiral_tab()
        contour_tab = self.create_contour_tab()
        island_tab = self.create_island_tab()
        subtabs.addTab(raster_tab, "Raster Hatching")
        subtabs.addTab(spiral_tab, "Spiral Hatching")
        subtabs.addTab(contour_tab, "Contour Pattern")
        subtabs.addTab(island_tab, "Island Pattern")
        
        layout.addWidget(subtabs)
        hatching_tab.setLayout(layout)
        self.tabs.addTab(hatching_tab, "Hatching")





    #^^^^change the deault value of that and range of pseed and ..
    def create_raster_tab(self):
        """Create raster (linear) hatching sub-tab with hatch/analyze/final buttons and status."""
        tab = QWidget()
        layout = QHBoxLayout()
        
        
        main_left_panel=QHBoxLayout()
        
        
        
        # Left panel for form and buttons
        left_panel = QVBoxLayout()
        form = QFormLayout()
        
        self.linear_hatch_angle = QDoubleSpinBox()
        self.linear_hatch_angle.setRange(0, 180)
        self.linear_hatch_angle.setValue(45)
        form.addRow("Hatch Angle (°):", self.linear_hatch_angle)
        
        self.linear_hatch_spacing = QDoubleSpinBox()
        self.linear_hatch_spacing.setRange(0.01, 1)
        self.linear_hatch_spacing.setValue(0.5)
        self.linear_hatch_spacing.setSingleStep(0.01)
        form.addRow("Hatch Spacing (mm):", self.linear_hatch_spacing)
        
        
        self.linear_hatch_speed = QDoubleSpinBox()
        self.linear_hatch_speed.setRange(0, 200)
        self.linear_hatch_speed.setValue(0.1)
        self.linear_hatch_speed.setSingleStep(0.01)
        form.addRow("Speed (micrometers per second):", self.linear_hatch_speed)
        
        
        self.linear_hatch_power = QDoubleSpinBox()
        self.linear_hatch_power.setRange(0, 2000)
        self.linear_hatch_power.setValue(1200)
        self.linear_hatch_power.setSingleStep(1)
        form.addRow("Electron Power (Watts):", self.linear_hatch_power)
        
        
        self.linear_hatch_spot_size = QDoubleSpinBox()
        self.linear_hatch_spot_size.setRange(1, 10000)
        self.linear_hatch_spot_size.setValue(300)
        self.linear_hatch_spot_size.setSingleStep(1)
        form.addRow("Spot size ( micrometers):", self.linear_hatch_spot_size)
        
        # Add the checkbox for "Complete the Contour"
        self.linear_complete_contour_checkbox = QCheckBox("Complete the Contour")
        form.addRow(self.linear_complete_contour_checkbox)
        
        
        
    
        
        form_widget = QWidget()
        form_widget.setLayout(form)
        left_panel.addWidget(form_widget)
        
        
        
        left_widget=QWidget()
        left_widget.setLayout(left_panel)
        
        
        main_left_panel.addWidget(left_widget)
        
        
        buttons_widget=QWidget()
        buttons_layout = QVBoxLayout()
        
        
        
        hatch_button = QPushButton("Generate Hatching")
        hatch_button.clicked.connect(self.raster_hatching)
        buttons_layout.addWidget(hatch_button)
        
        analyze_hatch_button = QPushButton("Analyze Hatching")
        analyze_hatch_button.clicked.connect(self.analyzing_raster_hatching)
        buttons_layout.addWidget(analyze_hatch_button)
        
        final_hatch_button = QPushButton("Final Hatching")
        
        final_hatch_button.setStyleSheet(next_button_styles)
        
        final_hatch_button.clicked.connect(self.final_hatching)
        buttons_layout.addWidget(final_hatch_button)
        
        buttons_widget.setLayout(buttons_layout)
        

        main_left_panel.addWidget(buttons_widget)
        
        
        left_panel.addStretch()
        
        # Right panel for status messages
        right_panel = QVBoxLayout()
        self.hstatus_label = QLabel("Status: Not analyzed yet")
        self.hstatus_label.setWordWrap(True)
        self.hstatus_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.hstatus_label.setStyleSheet("""
            color: white;
            background-color: black;
            border: 1px solid gray;
            padding: 5px;
        """)
        #right_panel.addWidget(self.hstatus_label)
        self.hatching_scroll_area = QScrollArea()
        self.hatching_scroll_area.setWidget(self.hstatus_label)  # Add QLabel to QScrollArea
        self.hatching_scroll_area.setWidgetResizable(True)  # Allow the QLabel to adjust its size within the scroll area
        self.hatching_scroll_area.setFixedHeight(200)  # Set a fixed height for the scroll area
        self.hatching_scroll_area.setStyleSheet("""
            border: 1px solid gray;  /* Match border style with QLabel */
        """)
        
        # Add the scroll area to the layout
        right_panel.addWidget(self.hatching_scroll_area)

        
        
        layout.addLayout(main_left_panel, stretch=3)
        #layout.addLayout(left_panel, stretch=3)
        layout.addLayout(right_panel, stretch=2)
        tab.setLayout(layout)
        return tab
    
    
    

    #^^^again we defien this , is it ok?
    def raster_hatching(self):
        """Run raster (linear) hatching via Core_Mesh_Processor; set hatch_pattern and test_hatched_layers."""
        PM_PROCESSOR=Core_Mesh_Processor()
        
        
        self.hatch_pattern='Raster_Linear'

        if self.finalized_test_slice_planes is None:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("Final Slice is not defined or is empty")
            #error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()

            return


        #too show that
        self.canvas.setVisible(False)
        self.plotter.interactor.setVisible(True)
        


        self.selected_linear_hatch_angle = self.linear_hatch_angle.value()
        self.selected_linear_hatch_spacing = self.linear_hatch_spacing.value()*1000
        self.selected_linear_hatch_speed= self.linear_hatch_speed.value()
        self.selected_linear_hatch_power = self.linear_hatch_power.value()
        self.selected_linear_hatch_spot_size = self.linear_hatch_spot_size.value()
 
    
        
        
        #we can also have some analyzing inside the CORE function
        '''
        self.number_of_failed_hatch_line=0
        self.number_of_failed_hatch_line_no_points=0
        self.number_of_successive_hatched_layer=0
        self.failed_hatch_id=[]
        
        
        **instead of teh slcie plane
        we just give teh mesh
        untill here self.pv_mesh doesnt change anything
        and we slice with self.finalized_slice_n_layers
        
        spacing and angle is selected
        
        '''
        self.test_hatched_layers,self.test_whole_points,self.test_whole_lines,self.number_of_failed_hatch_line=PM_PROCESSOR.pyvista_mesh_linear_hatcher(self.pv_mesh,
                                                 spacing=self.selected_linear_hatch_spacing,
                                                 angle=self.selected_linear_hatch_angle,
                                                 n_layers=self.finalized_slice_n_layers,
                                                 just_show=True)
        
        
        
        self.plotter.clear()
        if self.box:
            self.plotter.add_mesh(self.box, color="lightgray", opacity=0.3)
            
            
            
            
        for i, (slice_plane, hatched) in enumerate(zip(self.finalized_test_slice_planes, self.test_hatched_layers)):
            if hatched is not None:
                
                #it show the all of them 
                #first it show the slice_plane and then 
                #the hatches
                
                # Add the slice plane with transparency
                self.plotter.add_mesh(
                    slice_plane,
                    color='lightgray',
                    opacity=0.3,
                    show_edges=True,
                    line_width=2,
                    edge_color='black'
                )
                
                # Add the hatching lines
                self.plotter.add_mesh(
                    hatched,
                    color='blue',
                    line_width=1,
                    style='wireframe'  # This ensures we only see the lines
                )
                
                
      #  our_layers=self.test_hatched_layers
         # -->list of polydatass that each one has lines and points
     #   with open("at_once_hatched.pkl", "wb") as f:
       #     pickle.dump(our_layers, f)





        # Set up the camera and lighting
        self.plotter.set_background('white')
        self.plotter.enable_anti_aliasing()

        # Add a scalar bar
        self.plotter.add_axes()

        #self.plotter.show()
        self.plotter.render()
        
        self.is_hatched=True
        
        
        
        #8e729834794379879839087098803384802
 






    def analyzing_raster_hatching(self):
        """Analyze raster hatch result; update status and finalized hatch data if valid."""
        if self.finalized_test_slice_planes is None:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("Final Slice is not defined or is empty")
            #error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()

            return
        

        if self.is_hatched is not True:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("First Hatch your object and then you can analyze")
            #error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()
            return

        #it must shwo the all thing related from the apply_hatching function parmaeters
        
        """
        message=f'''------------STATUS AFTER ANALYZING-------------\n
        there is  {self.number_of_failed_slice} failed slices without points \n 
        there is {self.number_of_failed_geom} failed geom \n
        there is {self.number_of_failed_hatch_line} failed hatch lines from {self.total_number_of_hatch_line} hatch lines
        there is .... failed slioces with only one line 
        

        '''
        
        self.hstatus_label.setText(f"Status: {message}")
        """
        # Determine the color for each line based on the conditions
        self.color_hatch = "red" if self.number_of_failed_hatch_line > 0 else "green"
        #self.color_hatch_point = "red" if self.number_of_failed_hatch_line_no_points > 0 else "green"
        self.run_hatch_stage=self.run_hatch_stage+1

        current_datetime = datetime.now()
        hatch_time_run = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        # if we add soem statistci parameter to hatch in CORE PROCESSOR and
        #teh hatched we cna actiev this message
        #self.h_message = f'''--------------------------------------------<br>
       # <span style='color:white;'> Run stage number. {self.run_hatch_stage} || Time : {hatch_time_run} </span><br>
        #<br>--------------------------------------------<br>
        #        <span style='color:white;'>Totally {self.number_of_successive_hatched_layer} Layers are build successfully !.</span><br>
       #         <span style='color:{self.color_hatch};'>There are {self.number_of_failed_hatch_line} failed hatched lines.</span><br>
       #         <span style='color:{self.color_hatch_point};'>There are {self.number_of_failed_hatch_line_no_points} failed hatched layer without points.</span><br>
#
       # 
       # '''
        self.number_of_successive_hatched_layer=len(self.test_hatched_layers)
       
       
        self.h_message = f'''--------------------------------------------<br>
        <span style='color:white;'> Run stage number. {self.run_hatch_stage} || Time : {hatch_time_run} </span><br>
        <br>--------------------------------------------<br>
                <span style='color:white;'>Totally {self.number_of_successive_hatched_layer} Layers are build successfully !.</span><br>
                <span style='color:{self.color_hatch};'>There are {self.number_of_failed_hatch_line} failed hatched lines.</span><br>
        
        '''
        #if len(self.failed_hatch_id)>0:
        #    self.h_message=self.h_message+f'''<span style='color:red;'>the id of failed layers from z=0 : {self.failed_hatch_id}</span><br>'''

        if self.run_hatch_stage==1:
            self.hatched_message_status=self.h_previous_message + '================================================== \n' + self.h_message
            self.h_previous_message=self.h_message
        else:

            self.hatched_message_status =self.h_previous_message + '================================================== \n' + self.h_message
            self.h_previous_message=self.h_message
            #i think this is false
            #self.run_hatch_stage=self.hatched_message_status + '================================================== \n' + self.h_message

        if self.slice_message_status is None:
            self.hstatus_label.setText("----------------STATUS----------:\n Waiting for analyzing .......")
            
        else:

        # Update the label with the styled message
            self.hstatus_label.setText(f"----------------STATUS----------:<br>{self.hatched_message_status}")
            # Auto-scroll to the bottom

        h_vertical_scroll_bar = self.hatching_scroll_area.verticalScrollBar()
        h_vertical_scroll_bar.setValue(h_vertical_scroll_bar.maximum()+200)
        
        
        
        
        
        
        
        
        
        
        
        
    def create_spiral_tab(self):
        """Create spiral hatching sub-tab (currently disabled)."""
        self.hatch_pattern='point and random ....'

        tab = QWidget()
        layout = QHBoxLayout()
        
        # Left panel
        left_panel = QVBoxLayout()
        form = QFormLayout()
        
        self.spiral_spacing = QDoubleSpinBox()
        self.spiral_spacing.setRange(0.01, 1)
        self.spiral_spacing.setValue(0.1)
        self.spiral_spacing.setSingleStep(0.01)
        form.addRow("Spiral Spacing (mm):", self.spiral_spacing)
        
        self.spiral_turns = QSpinBox()
        self.spiral_turns.setRange(1, 100)
        self.spiral_turns.setValue(10)
        form.addRow("Number of Turns:", self.spiral_turns)
        
        form_widget = QWidget()
        form_widget.setLayout(form)
        left_panel.addWidget(form_widget)
        
        generate_spiral_button = QPushButton("Generate Spiral")
        
        #disable
        generate_spiral_button.setDisabled(True)  # Disable the button
        generate_spiral_button.setStyleSheet("color: gray;")  # Optional: visually dim
        
        
        #generate_spiral_button.clicked.connect(self.generate_spiral)
        left_panel.addWidget(generate_spiral_button)
        
        analyze_hatch_button = QPushButton("Analyze Hatching")
        #analyze_hatch_button.clicked.connect(self.analyzing_spiral_hatching)
        left_panel.addWidget(analyze_hatch_button)
        
        final_hatch_button = QPushButton("Final Hatching")
        final_hatch_button.clicked.connect(self.final_hatching)
        left_panel.addWidget(final_hatch_button)

        left_panel.addStretch()
        
        # Right panel
        right_panel = QVBoxLayout()
        self.spiral_status_label = QLabel("Status: Not generated")
        self.spiral_status_label.setStyleSheet("""
            color: white;
            background-color: black;
            border: 1px solid gray;
            padding: 5px;
        """)
        right_panel.addWidget(self.spiral_status_label)
        
        
        
        #------ not available------
        # Show unavailable warning
        unavailable_label = QLabel("⚠️ Spiral hatching not available in current version")
        unavailable_label.setStyleSheet("color: red; font-weight: bold;")
        left_panel.insertWidget(0, unavailable_label)




        
        layout.addLayout(left_panel, stretch=3)
        layout.addLayout(right_panel, stretch=2)
        tab.setLayout(layout)
        return tab
    
    def create_contour_tab(self):
        """Create contour-pattern hatching sub-tab (form and buttons)."""
        tab = QWidget()
        layout = QHBoxLayout()
        
        # Left panel
        left_panel = QVBoxLayout()
        form = QFormLayout()
        
        self.contour_offset = QDoubleSpinBox()
        self.contour_offset.setRange(0.01, 1)
        self.contour_offset.setValue(0.1)
        self.contour_offset.setSingleStep(0.01)
        form.addRow("Contour Offset (mm):", self.contour_offset)
        
        self.contour_layers = QSpinBox()
        self.contour_layers.setRange(1, 20)
        self.contour_layers.setValue(5)
        form.addRow("Number of Layers:", self.contour_layers)
        
        form_widget = QWidget()
        form_widget.setLayout(form)
        left_panel.addWidget(form_widget)
        
        generate_contour_button = QPushButton("Generate Contours")
        
        #disable
        generate_contour_button.setDisabled(True)  # Disable the button
        generate_contour_button.setStyleSheet("color: gray;")  # Optional: visually dim
        
        
       # generate_contour_button.clicked.connect(self.generate_contours)
        left_panel.addWidget(generate_contour_button)
        
        analyze_hatch_button = QPushButton("Analyze Hatching")
        #analyze_hatch_button.clicked.connect(self.analyzing_contours_hatching)
        left_panel.addWidget(analyze_hatch_button)
        
        final_hatch_button = QPushButton("Final Hatching")
        final_hatch_button.clicked.connect(self.final_hatching)
        left_panel.addWidget(final_hatch_button)

        left_panel.addStretch()
        
        # Right panel
        right_panel = QVBoxLayout()
        self.contour_status_label = QLabel("Status: Not generated")
        self.contour_status_label.setStyleSheet("""
            color: white;
            background-color: black;
            border: 1px solid gray;
            padding: 5px;
        """)
        right_panel.addWidget(self.contour_status_label)
        
        
        
        #------ not available------
        # Show unavailable warning
        unavailable_label = QLabel("⚠️ Countor hatching not available in current version")
        unavailable_label.setStyleSheet("color: red; font-weight: bold;")
        left_panel.insertWidget(0, unavailable_label)



        
        layout.addLayout(left_panel, stretch=3)
        layout.addLayout(right_panel, stretch=2)
        tab.setLayout(layout)
        return tab
    
    def create_island_tab(self):
        """Create island-pattern hatching sub-tab (form and buttons)."""
        tab = QWidget()
        layout = QHBoxLayout()
        
        # Left panel
        left_panel = QVBoxLayout()
        form = QFormLayout()
        
        self.island_size = QDoubleSpinBox()
        self.island_size.setRange(0.1, 10)
        self.island_size.setValue(1.0)
        self.island_size.setSingleStep(0.1)
        form.addRow("Island Size (mm):", self.island_size)
        
        self.island_spacing = QDoubleSpinBox()
        self.island_spacing.setRange(0.01, 1)
        self.island_spacing.setValue(0.1)
        self.island_spacing.setSingleStep(0.01)
        form.addRow("Island Spacing (mm):", self.island_spacing)
        
        form_widget = QWidget()
        form_widget.setLayout(form)
        left_panel.addWidget(form_widget)
        
        generate_island_button = QPushButton("Generate Islands")
        #generate_island_button.clicked.connect(self.generate_islands)
        
        #disable
        generate_island_button.setDisabled(True)  # Disable the button
        generate_island_button.setStyleSheet("color: gray;")  # Optional: visually dim
        
        
        
        
        left_panel.addWidget(generate_island_button)
        
        analyze_hatch_button = QPushButton("Analyze Hatching")
        #analyze_hatch_button.clicked.connect(self.analyzing_islands_hatching)
        left_panel.addWidget(analyze_hatch_button)
        
        final_hatch_button = QPushButton("Final Hatching")
        final_hatch_button.clicked.connect(self.final_hatching)
        left_panel.addWidget(final_hatch_button)

        left_panel.addStretch()
        
        # Right panel
        right_panel = QVBoxLayout()
        self.island_status_label = QLabel("Status: Not generated")
        self.island_status_label.setStyleSheet("""
            color: white;
            background-color: black;
            border: 1px solid gray;
            padding: 5px;
        """)
        right_panel.addWidget(self.island_status_label)
        
        
        
        #------ not available------
        # Show unavailable warning
        unavailable_label = QLabel("⚠️ Island hatching not available in current version")
        unavailable_label.setStyleSheet("color: red; font-weight: bold;")
        left_panel.insertWidget(0, unavailable_label)

        
        layout.addLayout(left_panel, stretch=3)
        layout.addLayout(right_panel, stretch=2)
        tab.setLayout(layout)
        return tab
        
        

 
    
    def final_hatching(self):
        """Finalize hatching (copy to whole_*), set workflow state, switch to Postcooling tab."""
        if self.finalized_test_slice_planes is None:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("Final Slice is not defined or is empty")
            #error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()

            return

        
        if self.is_hatched is not True:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText("First Hatch your object and then you can analyze")
            #error_msg.setInformativeText(str(e))  # Display the error message
            error_msg.exec_()
            return

       

        #it show how many layer we have
        #self.number_of_all_hatched_lines=len(self.test_whole_lines)
        self.number_of_all_hatched_lines=0
        for layer in self.test_hatched_layers:
            
            if layer is not None:
                self.number_of_all_hatched_lines=self.number_of_all_hatched_lines+layer.n_lines
           
        #we need details
        details=f"""
        
        object sliced to {self.number_of_successive_hatched_layer} layers 
        with {self.number_of_all_hatched_lines}  lines totally

        """
        
        # Create the message box
        message_box = QMessageBox()
        message_box.setWindowTitle("Confirm Details")
        message_box.setText(f"This is your object with the following details:\n\n{details}\n\nDo you want to continue?")
        message_box.setIcon(QMessageBox.Question)
        
        # Add Yes and No buttons
        message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        message_box.setDefaultButton(QMessageBox.No)
    
        # Execute the message box and get the user's response
        user_response = message_box.exec()
    
        # Handle the user's response
        if user_response == QMessageBox.Yes:
            print("User chose to continue.")
            
            
            
 
                  
            self.DEFAULT_hatched_pattern  =self.hatch_pattern 
            self.DEFAULT_hatched_layers=self.test_hatched_layers
            
            self.DEFAULT_whole_points=self.test_whole_points
            self.DEFAULT_whole_lines=self.test_whole_lines
            
            
            self.DEFAULT_linear_hatch_angle=self.selected_linear_hatch_angle
            self.DEFAULT_linear_hatch_spacing=self.selected_linear_hatch_spacing 
            self.DEFAULT_linear_hatch_speed=self.selected_linear_hatch_speed
            self.DEFAULT_linear_hatch_power =self.selected_linear_hatch_power 
            self.DEFAULT_linear_hatch_spot_size=self.selected_linear_hatch_spot_size
            
            

            if self.linear_complete_contour_checkbox.isChecked():
                self.DEFAULT_LINE_COMPLETE_CONNECTION=True
                
                #line_connection=True
            else:
                self.DEFAULT_LINE_COMPLETE_CONNECTION=False
                #line_connection=False
                


            #self.final_dict=self.layer_builder(self.final_hatched_layers,connect_or_not=line_connection)

            #-------------------------------------------

            #-----> hatching to the pm class

            #it is compelte before it is 5
            self.workflow_state['hatching_completed'] = True
            self.update_tab_states()
            self.tabs.setCurrentIndex(5)

            
            # Proceed with the next step
        elif user_response == QMessageBox.No:
            
            print("User chose not to continue.")
            self.final_hatched_layers=None
            return

        

    '''
    prevuioys beststl14bahmanv2.py has 3 functions
    
    lines_separation , optimize_lines_with_order, layer_builder (that get loaded_layer)
    and get us the dictionary
    
    
    '''

    #it was hatching 2 that get from go to 2d plot
    #also it can go to pyvista and translate to any other type
    #all codes are available in beststl08.py
        
  
 
    

    
    #----------------------------------------------
    #----------------------------------------------
    #----------------------------------------------
    '''             Post Cooling Tab             '''
    #----------------------------------------------
    #----------------------------------------------
    #----------------------------------------------

    def setup_postcooling_tab(self):
        """Build Postcooling tab: shape/algorithm/jump/dwell form, preview/apply, skip toggle."""
        postcooling_tab = QWidget()
        
        postcooling_tab.setObjectName("post_cooling")  # Set object name
        
        main_layout = QVBoxLayout()
        #main_layout = QhBoxLayout()

        #self.tabs.addTab(postcooling_tab, "post_cooling")
        
        form_layout_left = QFormLayout()
        form_layout_middle =QFormLayout()
        form_layout_right = QFormLayout()
        
        
        
        #-------------LEFT-------------------
        # Algorithm Selection
        self.postcooling_algorithm_selector = QComboBox()
        self.postcooling_algorithm_selector.addItems(["Snake", "Random", "Single Directional"])
        self.postcooling_algorithm_selector.setCurrentText("Random")
        form_layout_left.addRow("Algorithm:", self.postcooling_algorithm_selector)
        


        # Shape
        self.postcooling_shape_selector = QComboBox()
        self.postcooling_shape_selector.addItems(["Square", "Circle"])
        self.postcooling_shape_selector.setCurrentText("Circle")
        form_layout_left.addRow("Shape:", self.postcooling_shape_selector)
        
        
        # Length/Radius
        self.postcooling_length_radius_input = QDoubleSpinBox()
        self.postcooling_length_radius_input.setRange(1, DEFAULT_BASE_RADIUS/1000)
        self.postcooling_length_radius_input.setValue(DEFAULT_BASE_RADIUS/1000)
        form_layout_left.addRow("Length/Radius:", self.postcooling_length_radius_input)
        
        
        
        
        
        #----midddle-----------------------

        # Jump Length
        self.postcooling_jump_length_input = QDoubleSpinBox()
        self.postcooling_jump_length_input.setRange(0, 200)
        self.postcooling_jump_length_input.setValue(2)
        form_layout_middle.addRow("Jump Length (mm):", self.postcooling_jump_length_input)
        
        
        
        # Theta
        self.postcooling_theta_input = QDoubleSpinBox()
        self.postcooling_theta_input.setRange(-360, 360)
        self.postcooling_theta_input.setSingleStep(45)  # Only 45-degree steps
        self.postcooling_theta_input.setValue(0)
        form_layout_middle.addRow("Theta:", self.postcooling_theta_input)
        

        # Dwell Time
        self.postcooling_dwell_time_input = QDoubleSpinBox()
        self.postcooling_dwell_time_input.setRange(0, 100)
        self.postcooling_dwell_time_input.setValue(60) 
        form_layout_middle.addRow("Dwell Time (micros):", self.postcooling_dwell_time_input)
        
        
        
        #-----right-------
        
        # Repetition
        self.postcooling_repetition_input = QSpinBox()
        self.postcooling_repetition_input.setRange(1, 100)
        self.postcooling_repetition_input.setValue(10)
        form_layout_right.addRow("Repetitions:", self.postcooling_repetition_input)
        
        
        
        # Spot Size
        self.postcooling_spot_size_input = QDoubleSpinBox()
        self.postcooling_spot_size_input.setRange(1, 10000)  # Adjust as needed
        self.postcooling_spot_size_input.setValue(2000)      # Default value in micrometers
        form_layout_right.addRow("Spot Size (µm):", self.postcooling_spot_size_input)
        
        # Power
        self.postcooling_power_input = QDoubleSpinBox()
        self.postcooling_power_input.setRange(0, 1000)       # Adjust range based on your system
        self.postcooling_power_input.setValue(600)           # Default value in Watts
        form_layout_right.addRow("Power (W):", self.postcooling_power_input)

        

        horizontal_form_layout = QHBoxLayout()
        horizontal_form_layout.addLayout(form_layout_left)
        horizontal_form_layout.addLayout(form_layout_middle)
        horizontal_form_layout.addLayout(form_layout_right)
        
        
        
        

        
        
        
        self.postcooling_pixel_skip = QPushButton("Skip")
        self.postcooling_pixel_skip.setCheckable(True)
        self.postcooling_pixel_skip.clicked.connect(self.toggle_postcooling_pixel_form_enabled)
        
        self.postcooling_pixel_skip.setStyleSheet("""
    QPushButton {
        background-color: red;
        color: white;
        font-weight: bold;
        border: 1px solid darkred;
        border-radius: 4px;
        padding: 4px 8px;
    }
    QPushButton:checked {
        background-color: darkred;
    }
""")

        

        main_layout.addLayout(horizontal_form_layout)

        main_layout.addWidget(self.postcooling_pixel_skip)
        
        
        
        
        # Preview
        postcooling_preview_button = QPushButton("Preview")
       # j_pixel_preview_button.clicked.connect(self.preview_spatter_line_algorithem)
        postcooling_preview_button.clicked.connect(self.preview_postcooling)
        main_layout.addWidget(postcooling_preview_button)
        
        # Apply
        postcooling_apply_button = QPushButton("Apply Settings")
       # j_pixel_apply_button.clicked.connect(self.spatter_line_algorithem)
        postcooling_apply_button.clicked.connect(self.apply_postcooling)
        postcooling_apply_button.setStyleSheet(next_button_styles)
        main_layout.addWidget(postcooling_apply_button)
        
    

        
        
        #postcooling_tab.setLayout(main_layout)


     
       # main_layout.addWidget(final_postcool_button)
        
        #***
        #.setStyleSheet(next_button_styles)
        
        
        


        postcooling_tab.setLayout(main_layout)
        # Add this tab to the main QTabWidget
        self.tabs.addTab(postcooling_tab, "Post Cooling")
        
        
        #self.workflow_state['post_cooling_completed'] = True
        #self.update_tab_states()
        #self.tabs.setCurrentIndex(6)  # Switch to the next tab
        #pass
        
    
    
    
    
    
    
    
    def toggle_postcooling_pixel_form_enabled(self):
        """Enable/disable postcooling form and update button text/style based on skip checkbox."""
        is_disabled = self.postcooling_pixel_skip.isChecked()
        
        # Update button text
        if is_disabled:
            self.postcooling_pixel_skip.setText("Activate Jump safe")
            
            self.postcooling_pixel_skip_is=True
            
            self.postcooling_pixel_skip.setStyleSheet("""
    QPushButton {
        background-color: red;
        color: white;
        font-weight: bold;
        border: 1px solid darkred;
        border-radius: 4px;
        padding: 4px 8px;
    }
    QPushButton:checked {
        background-color: #007BFF;  /* Bootstrap blue */
        border: 1px solid #0056b3;
    }
""")
    
        else:
            self.postcooling_pixel_skip_is=False
            self.postcooling_pixel_skip.setText("Skip")
    
        # Disable or enable all form widgets
        for widget in [
            self.postcooling_algorithm_selector,
            self.postcooling_repetition_input,
            self.postcooling_shape_selector,
            self.postcooling_length_radius_input,
            self.postcooling_jump_length_input,
            self.postcooling_theta_input,
            self.postcooling_dwell_time_input,
           # self.j_pixel_pro_option,
            self.postcooling_spot_size_input,
            self.postcooling_power_input
        ]:
            widget.setDisabled(is_disabled)
   
    
    
    
    
    def preview_postcooling(self):
        """Preview postcooling path from UI settings; show plot or prompt to activate first."""
        if self.postcooling_pixel_skip_is:
        #if self.postcooling_pixel_skip.isChecked():
            QMessageBox.information(self, "Skip Active", "Please activate the settings first to preview.")
            return
        # Read settings from UI
        pcool_shape = self.postcooling_shape_selector.currentText()
        pcool_algorithm = self.postcooling_algorithm_selector.currentText()
        
        try:
            pcool_length_or_radius = float(self.postcooling_length_radius_input.value()) * 1000
            pcool_jump = float(self.postcooling_jump_length_input.value()) * 1000
            pcool_theta = float(self.postcooling_theta_input.value())
            pcool_dwell = float(self.postcooling_dwell_time_input.value()) * 1000
            pcool_repetitions = int(self.postcooling_repetition_input.value())
          #  pro_heat_enabled = self.postcooling_pro_option.isChecked()
    
    
    
    
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numerical values.")
            return
        
        if pcool_shape=='Square':
            QMessageBox.information(self, "Not Available", "Square shape is not available.")
            return
        
        else:
            
            
            self.plotter.interactor.setVisible(False)
            self.canvas.setVisible(True)
            
            
            heat_process=Core_Heat_Processor()
            points=heat_process.postcooling_generatore_demo(pcool_shape.lower(),pcool_length_or_radius, pcool_algorithm.lower(), pcool_jump,pcool_theta)
            if points:
                self.plot_postcooling_algorithem(points,DEFAULT_BASE_RADIUS  )

     
            
   
        
    def plot_postcooling_algorithem2(self,points,radius):
        """
        Plots a circle and visualizes the order of given points.
        
        Parameters:
        - points: List of (x, y) tuples.
        - radius: Radius of the circle (defines the boundary).
        """
        self.ax.clear()
    
        # Draw the boundary circle
        circle = plt.Circle((0, 0), radius, color='r', fill=False, linewidth=2)
        self.ax.add_artist(circle)
    
        # Use a colormap to represent progression
        cmap = get_cmap("viridis")
        total = len(points)
    
        # Plot the points and connect them with lines and arrows
        for i in range(len(points)):
            x, y = points[i]
            color = cmap(i / total)
            self.ax.plot(x, y, 'o', color=color)  # point marker
    
            if i < len(points) - 1:
                x_next, y_next = points[i + 1]
                self.ax.annotate("",
                                 xy=(x_next, y_next), xytext=(x, y),
                                 arrowprops=dict(arrowstyle="->", color=color, lw=1))
    
        # Plot formatting
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.set_xlim(-radius - 1, radius + 1)
        self.ax.set_ylim(-radius - 1, radius + 1)
        self.ax.set_title("Jump Algorithm Order")
    
        self.canvas.draw()
        
        
    
    def plot_postcooling_algorithem(self, points, radius):
        """
        Animates the jump algorithm by plotting points in order inside a circle.
        
        Parameters:
        - points: List of (x, y) tuples.
        - radius: Radius of the circle boundary.
        """
        
        if self.postcooling_anim:
            self.postcooling_anim.event_source.stop()
            self.postcooling_anim = None
        
        
        self.ax.clear()
        
        # Draw circle boundary once
        circle = plt.Circle((0, 0), radius, color='r', fill=False, linewidth=2)
        self.ax.add_artist(circle)
    
        # Plot setup
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.set_xlim(-radius - 1, radius + 1)
        self.ax.set_ylim(-radius - 1, radius + 1)
        self.ax.set_title("Jump Algorithm Animation")
    
        # Initialization lists for animation
        point_dots, = self.ax.plot([], [], 'bo')  # dots
        arrows = []
    
        def init():
            point_dots.set_data([], [])
            return [point_dots] + arrows
    
        def update(frame):
            self.ax.clear()
            self.ax.add_artist(circle)
            self.ax.set_xlim(-radius - 1, radius + 1)
            self.ax.set_ylim(-radius - 1, radius + 1)
            self.ax.set_title("Jump Algorithm Animation")
    
            xs = [pt[0] for pt in points[:frame+1]]
            ys = [pt[1] for pt in points[:frame+1]]
            self.ax.plot(xs, ys, 'bo')
    
            for i in range(frame):
                self.ax.annotate("",
                                 xy=points[i+1], xytext=points[i],
                                 arrowprops=dict(arrowstyle="->", color="blue", lw=1))
            return []
    
        # Create the animation
        #instead of self.anim
        self.postcooling_anim = FuncAnimation(self.canvas.figure,
                                  update,
                                  frames=len(points),
                                  init_func=init,
                                  interval=70,
                                  repeat=False)
    
        self.canvas.draw()
        
        
        
    
    
    def apply_postcooling(self):
        """Apply postcooling settings from UI; optionally skip; then set post_cooling_completed and switch tab."""
      #  our_layers=self.DEFAULT_hatched_layers
        # -->list of polydatass that each one has lines and points
      #  with open("layers_default_hatched_layers.pkl", "wb") as f:
       #     pickle.dump(our_layers, f)
      #      
            
            
       # our_layers=self.test_hatched_layers
       # with open("ltest_hatched_layers.pkl", "wb") as f:
       #    pickle.dump(our_layers, f)
        
        
        
        
        
        
        if self.postcooling_anim:
            self.postcooling_anim.event_source.stop()
            self.postcooling_anim = None
        
        self.postcooling_shape = self.postcooling_shape_selector.currentText()
        self.postcooling_algorithm = self.postcooling_algorithm_selector.currentText()
        
        try:
            self.postcooling_length_or_radius = float(self.postcooling_length_radius_input.value()) * 1000
            self.postcooling_jump = float(self.postcooling_jump_length_input.value()) * 1000
            self.postcooling_theta = float(self.postcooling_theta_input.value())
            self.postcooling_dwell = float(self.postcooling_dwell_time_input.value()) * 1000
            self.postcooling_repetitions = int(self.postcooling_repetition_input.value())
            #self.jump_pro_heat_enabled = self.j_pixel_pro_option.isChecked()
    
            self.postcooling_spot_size_input=float(self.postcooling_spot_size_input.value())
            self.postcooling_power_input=float(self.postcooling_power_input.value())
    
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numerical values.")
            return
        
        
        
       
        
        #if self.postcooling_pixel_skip is None or not self.postcooling_pixel_skip.isChecked():
        if self.postcooling_pixel_skip_is:
      #  if self.postcooling_pixel_skip.isChecked():
            reply = QMessageBox.question(
                self,
                "Post cooling Not Active",
                "Post cooling is not active. Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            
            
            
            if reply == QMessageBox.No:
                return
            
            else:
                self.workflow_state['post_cooling_completed'] = True
                self.update_tab_states()
                self.tabs.setCurrentIndex(6)  # Switch to the next tab
                
        else:
            
                
            
            
            if self.postcooling_shape=='Square':
                QMessageBox.information(self, "Not Available", "Square shape is not available.")
                return
            
            else:
                
                
                self.plotter.interactor.setVisible(False)
                self.canvas.setVisible(True)
                
                
                heat_process=Core_Heat_Processor()
                points=heat_process.postcooling_generatore_demo(self.postcooling_shape.lower(),self.postcooling_length_or_radius, self.postcooling_algorithm.lower(), self.postcooling_jump,self.postcooling_theta)
                if points:
                    self.plot_postcooling_algorithem2(points,DEFAULT_BASE_RADIUS  )
                    

        
                QMessageBox.information(self, "Jump Safe", "Jump Safe setup completed successfully.")
                
                
                
                self.workflow_state['post_cooling_completed'] = True
                self.update_tab_states()
                self.tabs.setCurrentIndex(6)  # Switch to the next tab
        
       
                

                
        

    
    def final_post_cooling(self):
        """Set post_cooling_completed and switch to Parametrization tab."""
        self.workflow_state['post_cooling_completed'] = True
        self.update_tab_states()
        self.tabs.setCurrentIndex(6)  # Switch to the next tab
        
    
        
    
    
    
    #----------------------------------------------
    #----------------------------------------------
    #----------------------------------------------
    '''         PARAMETRIZATION Tab             '''
    #----------------------------------------------
    #----------------------------------------------
    #----------------------------------------------
    def setup_parametrization_tab(self):
        """Build Parametrization tab: advanced layer/object buttons and continue-to-preview."""
        self.advanced_window=None
        self.parametrization_tab = QWidget()
        self.parametrization_tab.setObjectName("parametrization_tab")
        self.tabs.addTab(self.parametrization_tab, "Parametrization")
        
        advanced_layer_parametrization_button=QPushButton('Advanced Layer Parametrization')
        advanced_layer_parametrization_button.clicked.connect(self.advanced_layer_parametrization)
        
        
        advanced_objects_parametrization_button=QPushButton('Advanced Object Parametrization')
        advanced_objects_parametrization_button.clicked.connect(self.advanced_object_parametrization)
        

        countinue_button=QPushButton('Countinue to Preview')
        
        countinue_button.setStyleSheet(next_button_styles)
        
        countinue_button.clicked.connect(self.countinue_to_preview)
        
        layer_layout=QHBoxLayout()
        
        layer_layout.addWidget(advanced_layer_parametrization_button)
        layer_layout.addWidget(advanced_objects_parametrization_button)
        
        
        layer_layout.addWidget(countinue_button)
        self.parametrization_tab.setLayout(layer_layout)

        # Add the parametrization tab to main tabs
        self.tabs.addTab(self.parametrization_tab, "Parametrization")
        #self.advanced_window = None
        
        

    def countinue_to_preview(self):
        """Set parametrization_completed and switch to Preview tab."""
        self.workflow_state['parametrization_completed'] = True
        self.update_tab_states()
        self.tabs.setCurrentIndex(7)  # Switch to the next tab
        
    
    def advanced_layer_parametrization(self):
        """Open advanced layer parametrization window (AdvancedWindow_layers)."""
        #flag and check
        if self.advanced_window is None:
            #self.advanced_window = AdvancedWindow()
            self.advanced_window = AdvancedWindow_layers(self.box,self.pv_mesh,number_of_layers=self.finalized_slice_n_layers)
        else:
            self.advanced_window.show()
            

        
    def advanced_object_parametrization(self):
        if self.advanced_window is None:
            #self.advanced_window = AdvancedWindow()
            self.advanced_window = AdvancedWindow_objects(self.box,self.pv_mesh,number_of_final_object=self.numb_object_based_on_squares)
        else:
            self.advanced_window.show()
        

    #----------------------------------------------
    #----------------------------------------------
    #----------------------------------------------
    '''               PREVIEW Tab               '''
    #----------------------------------------------
    #----------------------------------------------
    #----------------------------------------------
    #setup preview tabs and all the path and path2,3, and ..
    #is available in beststl14bahmanv2.py
    def setup_preview_tab(self):
        preview_tab = QWidget()
        preview_tab.setObjectName("preview_tab")
        

        #---------------------
        
        # Create main layout for the preview tab
        main_layout = QVBoxLayout()
        preview_tab.setLayout(main_layout)
        
        # Top section with controls and electron path
        top_layout = QHBoxLayout()
        
        # Control panel
        control_panel = QWidget()
        control_layout = QHBoxLayout()
        control_panel.setLayout(control_layout)
        
        # Left control section
        lcontrol = QVBoxLayout()
        preview_button = QPushButton("Preview Additive Path")
        preview_button.clicked.connect(self.preview_func)
        lcontrol.addWidget(preview_button)
        
        '''
        advanced_button = QPushButton("Advanced Parametrization")
        advanced_button.clicked.connect(self.advanced_parametrization)
        lcontrol.addWidget(advanced_button)
        control_layout.addLayout(lcontrol)
        '''
        control_layout.addLayout(lcontrol)
        # Right control section
        rcontrol = QVBoxLayout()
        label = QLabel("Select Input Type:")
        rcontrol.addWidget(label)
        
        input_selector = QComboBox()
        input_selector.addItems([
            "EBM Input - OBF",
            "FDM Input - STL", 
            "FDM Input - GCode", 
            "SLM Input - CAD",
            "SLM Input - Mesh",
            "EBM Input - Surface"
        ])
        rcontrol.addWidget(input_selector)
        
        run_button = QPushButton("Save")
        run_button.clicked.connect(self.run_preview)
        
        run_button.setStyleSheet(next_button_styles)
        
        rcontrol.addWidget(run_button)
        rcontrol.addStretch()
        control_layout.addLayout(rcontrol)
        

        # Add control panel to top layout
        top_layout.addWidget(control_panel)
        
        # Create and add electron path canvas to top layout
        self.figure_electron = plt.figure(figsize=(6, 4))
        self.ax_electron = self.figure_electron.add_subplot(111)  # Changed to 2D
        self.canvas_electron = FigureCanvas(self.figure_electron)
        #self.canvas_electron.setMinimumWidth(300)  # Set minimum width before in 400
        #self.canvas_electron.setMinimumHeight(300)  # Set minimum height
        
        self.canvas_electron.setFixedHeight(300)
        self.canvas_electron.setFixedWidth(300)
        top_layout.addWidget(self.canvas_electron)
        
        
        
        # Create top panel and add to main layout
        top_panel = QWidget()
        top_panel.setLayout(top_layout)
        main_layout.addWidget(top_panel)
        
        # Bottom section with additive path
        down_layout = QVBoxLayout()
        self.figure_additive = plt.figure(figsize=(10, 6))
        self.ax_additive = self.figure_additive.add_subplot(111, projection='3d')
        self.canvas_additive = FigureCanvas(self.figure_additive)
        self.canvas_additive.setMinimumHeight(400)  # Set minimum height
        down_layout.addWidget(self.canvas_additive)
        
        # Create bottom panel and add to main layout
        down_panel = QWidget()
        down_panel.setLayout(down_layout)
        main_layout.addWidget(down_panel)
        
        # Store reference to input selector
        self.input_selector = input_selector
        
        # Add tab to main tab widget
        self.tabs.addTab(preview_tab, "Preview")
        
        # Initialize both canvases as hidden initially
        self.canvas_additive.setVisible(False)
        self.canvas_electron.setVisible(False)
        

        # Store reference to Advanced Window
        #self.advanced_window = None
        
        
        

    def visualize_additive_path2(self, our_dict):
        # Clear previous plot
        self.ax_additive.clear()
        
        # Get all z-heights for proper scaling
        all_heights = [our_dict[f'layer_{i}']['height'] 
                       for i in range(1, len(our_dict) + 1)]
        
        # Set axis limits based on data
        max_xy = max([np.max(np.abs(our_dict[f'layer_{i}']['all_points'][:, :2])) 
                     for i in range(1, len(our_dict) + 1)])
        
        self.ax_additive.set_xlim(-max_xy*1.1, max_xy*1.1)
        self.ax_additive.set_ylim(-max_xy*1.1, max_xy*1.1)
        self.ax_additive.set_zlim(min(all_heights)-1, max(all_heights)+1)
    
        # Initialize empty line collection
        lines = []
        
        # Track animation state
        current_layer = 1
        current_line = 0
        
        def init():
            self.ax_additive.set_xlabel('X')
            self.ax_additive.set_ylabel('Y')
            self.ax_additive.set_zlabel('Z')
            self.ax_additive.set_title('Additive Manufacturing Path')
            return []
    
        def animate(frame):
            nonlocal current_layer, current_line
            
            # Clear old lines if starting new frame
            if frame == 0:
                for line in lines:
                    line.remove()
                lines.clear()
                current_layer = 1
                current_line = 0
                return lines
            
            # Get current layer data
            layer_key = f'layer_{current_layer}'
            if layer_key not in our_dict:
                return lines
            
            layer_data = our_dict[layer_key]
            points = layer_data['all_points']
            connections = layer_data['opt_lines']
            
            # Draw current connection
            if current_line < len(connections):
                start_idx, end_idx = connections[current_line]
                start_point = points[start_idx]
                end_point = points[end_idx]
                
                # Calculate intermediate point for animation
                progress = (frame % 10) / 10
                current_point = start_point + (end_point - start_point) * progress
                
                # Plot the line
                line = self.ax_additive.plot([start_point[0], current_point[0]],
                                           [start_point[1], current_point[1]],
                                           [start_point[2], current_point[2]],
                                           'r-', linewidth=2)[0]
                lines.append(line)
                
                # Move to next line or layer
                if frame % 10 == 9:
                    current_line += 1
                    if current_line >= len(connections):
                        current_line = 0
                        current_layer += 1
            
            # Add layer indicator
            self.ax_additive.set_title(f'Additive Manufacturing Path - Layer {current_layer}')
            return lines
        
        # Create animation
        anim = FuncAnimation(self.figure_additive, animate, init_func=init,
                            frames=len(our_dict) * 200,
                            interval=20,
                            blit=False, repeat=True)
        
        # Show the canvas
        self.canvas_additive.setVisible(True)
        self.canvas_additive.draw()
        return anim
    
    
    def visualize_electron_path(self, our_dict):
        # Clear previous plot
        self.ax_electron.clear()
        
        # Calculate total number of layers
        num_layers = len(our_dict)
        
        # Get data extents for X and Y only
        max_xy = max([np.max(np.abs(our_dict[f'layer_{i}']['all_points'][:, :2])) 
                      for i in range(1, num_layers + 1)])
        
        # Set axis limits for 2D view
        self.ax_electron.set_xlim(-max_xy * 1.1, max_xy * 1.1)
        self.ax_electron.set_ylim(-max_xy * 1.1, max_xy * 1.1)
        
        # Calculate total number of lines across all layers
        total_connections = sum(len(our_dict[f'layer_{i}']['opt_lines']) 
                              for i in range(1, num_layers + 1))
        
        # Store all lines initially
        lines = []
        layer_line_counts = []  # Store number of lines per layer
        
        for layer in range(1, num_layers + 1):
            layer_key = f'layer_{layer}'
            connections = our_dict[layer_key]['opt_lines']
            layer_line_counts.append(len(connections))
            for _ in range(len(connections)):
                line, = self.ax_electron.plot([], [], 'b-', linewidth=2)
                lines.append(line)
    
        progress_steps = 10
    
        def init():
            """Initialize empty lines."""
            for line in lines:
                line.set_data([], [])
            return lines
    
        def animate(frame):
            """Efficiently update the animation."""
            current_index = (frame // progress_steps) % total_connections
            progress = (frame % progress_steps) / progress_steps
    
            # Find correct layer and connection index
            cumsum = 0
            layer_number = 1
            for i, count in enumerate(layer_line_counts):
                if cumsum + count > current_index:
                    layer_number = i + 1
                    connection_index = current_index - cumsum
                    break
                cumsum += count
    
            layer_data = our_dict[f'layer_{layer_number}']
            points = layer_data['all_points']
            connections = layer_data['opt_lines']
            
            start_idx, end_idx = connections[connection_index]
            start_point = points[start_idx]
            end_point = points[end_idx]
    
            # Compute interpolated point (only X and Y coordinates)
            current_point = start_point + (end_point - start_point) * progress
    
            # Update the corresponding line (2D only)
            lines[current_index].set_data([start_point[0], current_point[0]],
                                        [start_point[1], current_point[1]])
    
            # Update title with layer information
            self.ax_electron.set_title(f'Electron Beam Path (Top View) - Layer {layer_number}')
            
            return [lines[current_index]]
    
        # Set labels and grid
        self.ax_electron.set_xlabel('X')
        self.ax_electron.set_ylabel('Y')
        self.ax_electron.grid(True, color='lightgray')
    
        # Create animation
        anim = FuncAnimation(self.figure_electron, animate, init_func=init,
                            frames=total_connections * progress_steps,
                            interval=5,
                            blit=True, repeat=True)
    
        # Show the canvas
        self.canvas_electron.setVisible(True)
        self.canvas_electron.draw()
        return anim
    
   
    
    def preview_func(self):
        
        
        QMessageBox.warning(self, "Not Available", "This feature is not available now.")
        
        '''
        self.is_previewed_yet=True
        
        self.final_dict=self.layer_builder(self.final_hatched_layers,connect_or_not= self.complete_connection_to_each_other)
        
        self.set_tab_height("Preview", 800)
#plotter unvisible

        
        # Start both animations
        self.additive_anim = self.visualize_additive_path(self.final_dict)
        self.electron_anim = self.visualize_electron_path(self.final_dict)
        '''
        return
        
        
        


    def run_preview(self):
        
        selected_input = self.input_selector.currentText()
        
        if selected_input =="EBM Input - OBF":
            
            #file_path, _ = QFileDialog.getOpenFileName(self, "Select OBF File", "", "OBF Files (*.obf);;All Files (*)")
            
            folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")



            '''
            
            OLD WAY 
            if  self.is_previewed_yet==False:
                self.final_dict=self.layer_builder(self.final_hatched_layers,connect_or_not= self.complete_connection_to_each_other)
            #we msut get back the all; of them but nay way
            self.CREATE_OBF_FILE(folder_path,self.final_dict)
            '''
            
            
            '''
            
            with open("final_layers.pkl", "wb") as f:
                    pickle.dump(self.DEFAULT_hatched_layers, f)
                    
              
            #----------- TEST---------------------
            # Create a dictionary of all parameters
            obf_data = {
                "project": {
                    "name": self.Project_name,
                    "description": self.Project_description,
                    "revision_number": self.Project_revision_number,
                    "notes": self.Project_notes,
                    "material": self.Project_material,
                    "powder_size": float(self.powdersize.text()),
                    "folder_path": folder_path,
                },
                "hatching": {
                    "default_layers": 'final_layers.pkl',
                    "number_of_lines": self.number_of_all_hatched_lines,
                },
                "start_heat": {
                    "enabled": self.start_heat_is_Pro_state,
                    "algorithm": self.start_heat_algorithm,
                    "shape": self.start_heat_shape,
                    "dimension": self.start_heat_dimension,
                    "spot_size": self.start_heat_spot_size,
                    "beam_current": self.start_heat_beam_current,
                    "target_temp": self.start_heat_target_temp,
                    "temp_sensor": self.start_heat_temp_sensor,
                    "dwell_time": self.start_heat_dwell_time,
                    "jump_length": self.start_heat_jump_length,
                },
                "jump_safe": {
                    "shape": self.jump_pixel_shape,
                    "algorithm": self.jump_pixel_algorithm,
                    "length_or_radius": self.jump_pixel_length_or_radius,
                    "jump": self.jump_pixel_jump,
                    "theta": self.jump_pixel_theta,
                    "dwell": self.jump_pixel_dwell,
                    "repetitions": self.jump_pixel_repetitions,
                    "enabled": self.jump_pro_heat_enabled,
                    "spot_size": self.jump_pixel_spot_size_input,
                    "power": self.jump_pixel_power_input,
                },
                "post_cooling": {
                    "shape": self.postcooling_shape,
                    "algorithm": self.postcooling_algorithm,
                    "length_or_radius": self.postcooling_length_or_radius,
                    "jump": self.postcooling_jump,
                    "theta": self.postcooling_theta,
                    "dwell": self.postcooling_dwell,
                    "repetitions": self.postcooling_repetitions,
                    "spot_size": self.postcooling_spot_size_input,
                    "power": self.postcooling_power_input,
                },
                "melt": {
                    "speed": self.DEFAULT_linear_hatch_speed,
                    "spot_size": self.DEFAULT_linear_hatch_spot_size,
                    "power": self.DEFAULT_linear_hatch_power,
                    "connection": self.DEFAULT_LINE_COMPLETE_CONNECTION,
                },
                "jason": {
                    "build_piston_distance": float(self.buildPistonDistance.text()),
                    "powder_piston_distance": float(self.powderPistonDistance.text()),
                    "recoater_advance_speed": float(self.recoaterAdvanceSpeed.text()),
                    "recoater_retract_speed": float(self.recoaterRetractSpeed.text()),
                    "recoater_dwell_time": int(self.recoaterDwellTime.text()),
                    "recoater_full_repeats": int(self.recoaterFullRepeats.text()),
                    "recoater_build_repeats": int(self.recoaterBuildRepeats.text()),
                    "triggered_start": self.triggeredStart.text().lower() == 'true',
                }
            }
            
            # Save to JSON file
            with open("obf_config_test.json", "w") as f:
                json.dump(obf_data, f, indent=4)
                
            
            QMessageBox.information(self, "Saved", "Configuration saved to obf_config.json.")
            
            '''
            
            # Create and show the log window

            try:
                
                self.status_dialog = StatusDialog(self)
                self.status_dialog.show()
            
                # Redirect stdout
                old_stdout = sys.stdout
                sys.stdout = PrintRedirector(self.status_dialog.update_print_line)

                #self.status_dialog = StatusDialog(self)
                #self.status_dialog.show()   

                
                #i am not sure about self.number_of_successive_layer
                     
    
        
                #also look at the start heating and jump for repetitions ( inside repetation)
                #self.status_dialog.update_status("Starting OBF Generator...")
                
                
                
                obf_generator=Core_OBF_Generator(self.Project_name,folder_path,self.DEFAULT_hatched_layers,self.number_of_all_hatched_lines,
                                                  self.j_pixel_skip_is,self.postcooling_pixel_skip_is,self.start_heat_is_Pro_state,self.jump_pro_heat_enabled,
                                                  self.numb_object_based_on_squares,self.Project_description,self.Project_revision_number,
                                                  self.Project_notes,self.Project_material,
                                                  self.powdersize.text())
                                 
                 #revision number must be number (int)
                 
                 
                #self.status_dialog.update_status("Initializing Start Heat...")
                 
                
                self.status_dialog.update_top_label("Initializing Start Heat...")
                 
                obf_generator.init__start_heat(self.start_heat_algorithm,self.start_heat_shape,self.start_heat_dimension,self.start_heat_spot_size,self.start_heat_beam_current,
                                                  self.start_heat_target_temp,self.start_heat_temp_sensor,self.start_heat_dwell_time,
                                                  self.start_heat_jump_length)
                
                 
                 
                 
                #self.status_dialog.update_status("Initializing Jump Safe...")
                self.status_dialog.update_top_label("Initializing Jump Safe...")
                 #check the dwell times
                 
                obf_generator.init__jump_safe(self.jump_pixel_shape,self.jump_pixel_algorithm,self.jump_pixel_length_or_radius,
                                                 self.jump_pixel_jump,self.jump_pixel_theta,self.jump_pixel_dwell,self.jump_pixel_repetitions,
                                                 self.jump_pro_heat_enabled,self.jump_pixel_spot_size_input,self.jump_pixel_power_input)
                 
                
                # obf_generator.__init__spatter_safe()
                
                #we must change the name of these variables because of buttons
                
                self.status_dialog.update_top_label("Initializing Post Cooling...")
    
    
    
    
                obf_generator.init__post_cooling(self.postcooling_shape,self.postcooling_algorithm,
                                                   self.postcooling_length_or_radius ,
                                                  self.postcooling_jump,self.postcooling_theta,
                                                  self.postcooling_dwell,self.postcooling_repetitions,
                                                  self.postcooling_spot_size_input,
                                                  self.postcooling_power_input)
                
                 
                
                self.status_dialog.update_top_label("Initializing OBP file...")
                #self.status_dialog.update_status("Creating OBF file...")
                 
                obf_generator.init__melt(self.DEFAULT_linear_hatch_speed,self.DEFAULT_linear_hatch_spot_size,
                                             self.DEFAULT_linear_hatch_power,self.DEFAULT_LINE_COMPLETE_CONNECTION)
                 
                
                 
                 
                build_piston_distance = float(self.buildPistonDistance.text())
                powder_size = float(self.powdersize.text())
                powder_piston_distance = float(self.powderPistonDistance.text())
                recoater_advance_speed = float(self.recoaterAdvanceSpeed.text())
                recoater_retract_speed = float(self.recoaterRetractSpeed.text())
                recoater_dwell_time = int(self.recoaterDwellTime.text())
                recoater_full_repeats = int(self.recoaterFullRepeats.text())
                recoater_build_repeats = int(self.recoaterBuildRepeats.text())
                triggered_start = self.triggeredStart.text().lower() == 'true'  # Converts to boolean
    
    
                 #we must check triggeret True or true?
                 
                obf_generator.init__jason(build_piston_distance,powder_piston_distance,
                                            recoater_advance_speed,
                                            recoater_retract_speed,
                                            recoater_dwell_time,
                                            recoater_full_repeats,
                                            recoater_build_repeats,
                                            triggered_start)
                
                
                #in the name of god
                obf_generator.CREATE_OBF_FILE()
                
                
                #self.status_dialog.update_status("All files created successfully.")

                #self.status_dialog.close()
                
                QMessageBox.information(self, "Done...!", "ALL OBF File and OBPs files are created successfully")
                



                #......
                
            
            except Exception as e:
                QMessageBox.warning(self, "Unexpected Error", f"{e}")
                return
            
            finally:
                sys.stdout = old_stdout
                self.status_dialog.close()
                
            
        
            
        
        else:
            
            QMessageBox.warning(self, "Input Error", "Please enter valid numerical values.")
            return
        
        '''
        
        elif selected_input =="FDM Input - GCode":
            
      
            #-------------------------------------
            def calculate_extrusion(start, end):
                """
                Calculate extrusion amount based on distance between two points.
                :param start: numpy array [x, y, z] for the start point.
                :param end: numpy array [x, y, z] for the end point.
                :return: Extrusion amount.
                """
                distance = np.linalg.norm(end - start)  # Efficient distance calculation
                return distance * 0.05  # Extrusion factor (adjust as needed)
            #-------------------------------------
       
                
            self.gcode = []

            # Start G-code setup
            self.gcode.append("; G-code for FDM Printing")
            self.gcode.append("G21 ; Set units to millimeters")
            self.gcode.append("G90 ; Set to absolute positioning")
            self.gcode.append("M82 ; Set extruder to absolute mode")
            self.gcode.append("G28 ; Home all axes")
            self.gcode.append("G1 Z0.2 F300 ; Move to starting height")
            
            
            
    
    
    
        
            #-------------------------------------
            for layer_idx in range(len(self.pm_layer_points)):
                layer_points = self.pm_layer_points[layer_idx]
                layer_lines = self.pm_layer_lines[layer_idx]
                # Add comment for the layer
                self.gcode.append(f"; Layer {layer_idx + 1}")
                
                for line in layer_lines:
                    start_idx, end_idx = line  # Each line is a NumPy array of two indices
                    start_point = layer_points[start_idx]
                    end_point = layer_points[end_idx]
        
                    # Move to start point without extrusion
                    self.gcode.append(f"G0 X{start_point[0]:.2f} Y{start_point[1]:.2f} Z{start_point[2]:.2f}")
        
                    # Print line to end point with extrusion
                    #extrusion = self.calculate_extrusion(start_point, end_point)
                    #self.gcode.append(f"G1 X{end_point[0]:.2f} Y{end_point[1]:.2f} Z{end_point[2]:.2f} E{extrusion:.2f}")
                    self.gcode.append(f"G1 X{end_point[0]:.2f} Y{end_point[1]:.2f} Z{end_point[2]:.2f}")
             #-------------------------------------
       
                    
                    
    
            for layer_idx in range(1,len(self.final_dict)+1):

                layer_points = self.final_dict[f'layer_{layer_idx}']['all_points'].tolist()
                layer_lines = self.final_dict[f'layer_{layer_idx}']['opt_lines']
                
                # Add comment for the layer
                self.gcode.append(f"; Layer {layer_idx}")
                
                
                
                
                
                for line in layer_lines:
                    start_idx, end_idx = np.array(line)  # Each line is a NumPy array of two indices
                    start_point = layer_points[start_idx]
                    end_point = layer_points[end_idx]
        
                    # Move to start point without extrusion
                    self.gcode.append(f"G0 X{start_point[0]:.2f} Y{start_point[1]:.2f} Z{start_point[2]:.2f}")
        
                    # Print line to end point with extrusion
                    #extrusion = self.calculate_extrusion(start_point, end_point)
                    #self.gcode.append(f"G1 X{end_point[0]:.2f} Y{end_point[1]:.2f} Z{end_point[2]:.2f} E{extrusion:.2f}")
                    self.gcode.append(f"G1 X{end_point[0]:.2f} Y{end_point[1]:.2f} Z{end_point[2]:.2f}")
                    
                    
            
    
            # Finish G-code
            self.gcode.append("M104 S0 ; Turn off hotend")
            self.gcode.append("M140 S0 ; Turn off bed")
            self.gcode.append("G28 X0 ; Home X axis")
            self.gcode.append("M84 ; Disable motors")
            self.gcode.append("; End of G-code")
            

            # Open file dialog to select save path
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(
                None,
                "Save G-code File",
                "",
                "G-code Files (*.gcode);;All Files (*)",
                options=options,
            )
    
            if file_path:
                # Save G-code to the selected file
                with open(file_path, "w") as file:
                    file.write("\n".join(self.gcode))
                print(f"G-code saved to {file_path}")
                
            '''
                
                
                
                
                
    def layer_to_obp_file(self,layer,speed,spot_size,power,save_name,return_obp_lines=False):
        
        opt_lines=layer['opt_lines']
        all_points=layer['all_points'].tolist()
        
        beam_params=obp.Beamparameters(spot_size,power)
        
        obp_points=[]
        

        obp_lines=[]
            
        
        for line in opt_lines:

            
            obp_lines.append(obp.Line(obp.Point(all_points[line[0]][0], all_points[line[0]][1]),  obp.Point(all_points[line[1]][0], all_points[line[1]][1]), speed,beam_params))

        obp.write_obp(obp_lines, save_name)
        
        
        if return_obp_lines==True:
            
            return obp_lines  
        
        
    def all_layers_to_obp_files(self,layers,speed,spot_size,power):
        #it must get layers and others..
        
        
        os.makedirs("obp", exist_ok=True)
        

        count=0
        for i in range(1,len(layers)+1):
            
            self.layer_to_obp_file(layers[f'layer_{i}'],speed,spot_size,power,f'obp/layer_{i}.obp')
            
            count=count+1
            
            
        print(f'Congrats {count} file is saved!')
        
        
    def create_builtprocessors(self,filename,default=True):
        
        if default==True:
            
            data ={
      "default": {
        "type": "lua",
        "entryPoint": "buildProcessors/lua/build.lua"
      },
      "old-lua": {
        "type": "lua",
        "entryPoint": "buildProcessors/lua/old_build.lua"
      },
      "lua-with-args": {
        "type": "lua",
        "entryPoint": "buildProcessors/lua/build.lua",
        "args": [
          "amount=40"
        ]
      }
    }

        
            
            with open(filename, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, indent=4, ensure_ascii=False)
            
            print(f"JSON file '{filename}' has been created successfully!")
            
            
        else:
            pass
            
            



    def create_manifest_jason(self,filename,default=True):
        if default==True:
            
            
            data = {
      "formatVersion": "3.0",
      "project": {
        "id": "4a8a3fb1-1568-4e87-b1f9-048e4a43ff85",
        "name": f"{self.project_name_input.text().strip()}",
        "description": f"{ self.description_input.toPlainText()}",
        "revision": {
          "number": int(self.revision.text().strip()),
          "note": f"{self.notes_input.toPlainText().strip()}"
        }
      },
      "author": {
        "name": f"{self.author_name.text().strip()}",
        "email": "test.author@example.com"
      },
      "license": "MIT",
      "copyright": "Copyright \u00a9 2023 Freemelt AB",
      "reference": {
        "name": "pixelmelt",
        "uri": "https://pixelmelt.io/projects/4a8a3fb1-1568-4e87-b1f9-048e4a43ff85/1"
      }
    }

            
            with open(filename, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, indent=4, ensure_ascii=False)
            
            print(f"JSON file '{filename}' has been created successfully!")
            
            
        else:
            pass





    def create_buildInfo_json(self,filename,number_of_layers,default=True):
        
        if default==True:
            
            
            melt_list=[]
            for i in range(1,number_of_layers+1):
                
                melt_list.append({'file':f'obp/layer_{i}.obp',"repetitions": int(self.revision.text().strip())})
                
                

            
            data = {
      "startHeat": {
        "file": "obp/startHeat.obp",
        "temperatureSensor": "Sensor1",
        "targetTemperature": 650.0,
        "timeout": 14400
      },
      "layerDefaults": {
        "layerFeed": {
          "buildPistonDistance": f'{self.buildPistonDistance.text()}',
          "powderPistonDistance": f'{self.powderPistonDistance.text()}',
          "recoaterAdvanceSpeed": f'{self.recoaterAdvanceSpeed.text()}',
          "recoaterRetractSpeed": f'{self.recoaterRetractSpeed .text()}',
          "recoaterDwellTime":f'{self.recoaterDwellTime.text()}',
          "recoaterFullRepeats": f'{self.recoaterFullRepeats.text()}',
          "recoaterBuildRepeats": f'{self.recoaterBuildRepeats.text()}',
             #what is that here? true or True
          "triggeredStart": f'{self.triggeredStart.text().lower()}'
        },
        "spatterSafe": [
          {
            "file": "obp/spatterSafe.obp",
            "repetitions": 3
          }
        ],
        "jumpSafe": [
          {
            "file": "obp/jumpSafe.obp",
            "repetitions": 3
          }
        ],
        "heatBalance": [
          {
            "file": "obp/heatBalance.obp",
            "repetitions": 5
          }
        ]
      },
      "layers": [
        {
          "melt": melt_list
        }
      ]
    }

            
            with open(filename, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, indent=4, ensure_ascii=False)
            
            print(f"JSON file '{filename}' has been created successfully!")
            
            
        else:
            pass
        


    def create_dependencies_json(self,filename,default=True):
        
        if default==True:
            
      
                
            data = {
      "material": {
        "name": f'{self.project_material_input.text().strip()}',
        "powderSize": f'{self.powdersize.text()}'
      },
      "software": {
        "freemelt-recoaterservice": {
          "ge": "0.8.0",
          "lt": "1.0.0"
        },
        "freemelt-chamberservice": {
          "eq": "1.0.0"
        }
      }
    }

            
            with open(filename, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, indent=4, ensure_ascii=False)
            
            print(f"JSON file '{filename}' has been created successfully!")
            
            
        else:
            pass
        
        
    def CREATE_OBF_FILE(self,base_path,layers):
        
        os.chdir(base_path)
        
        #idd=int(np.random.uniform(1000000,1000000000000))
        
        from datetime import datetime

        # Get current time
        now = datetime.now()
        
        # Format: YY/MM/DD/H
        formatted_time = now.strftime("%y_%m_%d_%H")

       
        file_name=f"obf_{self.project_name_input.text().strip()}_{formatted_time}"
        #---------CREATE BASE FOLDER NAMED OBF---------------------
        
        os.makedirs(f"{file_name}", exist_ok=True)
        
        
        #----------------------BuildProcessors------------------------------
        os.makedirs(f"{file_name}/BuildProcessors", exist_ok=True)
        #---------BuildProcessors.json---------------------
        #---------BuildProcessors.lua---------------------

        self.create_builtprocessors(f"{file_name}/BuildProcessors/BuildProcessors.json")


        #---------manifest.json---------------------
        self.create_manifest_jason(f'{file_name}/manifest.json')
        
        
        #---------Dependencies.json---------------------
        
        self.create_dependencies_json(f'{file_name}/Dependencies.json')
        
        
        
        
        #---------OPB files---------------------
        os.makedirs(f"{file_name}/obp", exist_ok=True)
        
        count=0
        for i in range(1,len(layers)+1):
            #for each layer maybe it is different the speed and others...
            #for each object maybe it is different
            self.layer_to_obp_file(layers[f'layer_{i}'],200,100,90,f'{file_name}/obp/layer_{i}.obp')
            
            count=count+1
            
            
        print(f'Congrats {count} file is saved!')
        
        
        
        
        #---------buildInfo.json---------------------
        
        self.create_buildInfo_json(f'{file_name}/buildInfo.json',len(layers))
        











from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, 
    QScrollArea, QGroupBox, QFormLayout, QSpinBox, QComboBox, 
    QPushButton, QTabWidget, QHBoxLayout
)


