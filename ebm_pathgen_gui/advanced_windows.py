# Advanced windows: layer/object parameterization UIs
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel,
    QScrollArea, QGroupBox, QFormLayout, QSpinBox, QComboBox,
    QPushButton, QTabWidget, QHBoxLayout, QListWidget
)
from pyvistaqt import QtInteractor
from PM_EBM_CORE import Core_Mesh_Processor

from .constants import next_button_styles

class AdvancedWindow_layers(QWidget):
    """Advanced parameterization window: layer list, per-layer parameters form, and 3D slice preview."""

    def __init__(self, box, mesh, number_of_layers=5):
        """
        Args:
            box: PyVista mesh for the build box (optional).
            mesh: PyVista mesh to slice and display.
            number_of_layers: Number of layers to list and parameterize.
        """
        super().__init__()
        self.setWindowTitle("Advanced Parameterization")
        self.showMaximized()
        self.number_of_layers = number_of_layers  
        self.pv_mesh = mesh
        self.box = box

        self.main_layout = QHBoxLayout()
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout()

        # ✅ **Layer Selection List**
        self.layer_list = QListWidget()
        self.layer_list.addItems([f"Layer {i}" for i in range(1, self.number_of_layers + 1)])
        self.layer_list.currentRowChanged.connect(self.display_layer_parameters)
        self.left_layout.addWidget(QLabel("Select a Layer:"))
        self.left_layout.addWidget(self.layer_list)

        # ✅ **Layer Parameter Section (Dynamically Updated)**
        self.param_scroll = QScrollArea()
        self.param_scroll.setWidgetResizable(True)
        self.param_widget = QWidget()
        self.param_layout = QVBoxLayout()
        self.param_widget.setLayout(self.param_layout)
        self.param_scroll.setWidget(self.param_widget)

        self.left_layout.addWidget(self.param_scroll)

        # ✅ **Apply Button**
        self.param_button = QPushButton("Apply Final Parametrization")
        self.param_button.clicked.connect(self.on_parametrization)
        self.left_layout.addWidget(self.param_button)

        self.left_panel.setLayout(self.left_layout)
        self.left_panel.setFixedWidth(300)  

        # ✅ **Right Panel (3D Plotter)**
        self.plotter = QtInteractor()
        self.setup_plotter()
        self.right_layout = QVBoxLayout()
        self.right_layout.addWidget(self.plotter)
        self.right_panel = QWidget()
        self.right_panel.setLayout(self.right_layout)

        # ✅ **Main Layout**
        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.right_panel)
        self.setLayout(self.main_layout)

        # ✅ **Auto-select First Layer**
        if self.number_of_layers > 0:
            self.layer_list.setCurrentRow(0)

    def setup_plotter(self):
        """Initialize the 3D plotter with box (if any), sliced mesh layers, axes, and camera."""
        if self.box:
            self.plotter.add_mesh(self.box, color="lightgray", opacity=0.3)
            
        PM_Processor=Core_Mesh_Processor()
          
        #self.plotter.add_mesh(self.pv_mesh)
        
        
        self.test_slice_planes, *_ =PM_Processor.pyvista_slicer(self.pv_mesh,n_layers=self.number_of_layers)
        
        for plane in self.test_slice_planes:
            self.plotter.add_mesh(plane, color="blue", opacity=0.5)


        self.plotter.add_axes()
        self.plotter.render()   
    
    
        
        
        self.plotter.reset_camera()
        position = self.plotter.camera_position
        self.plotter.camera_position = [
            (position[0][0] * 1.5, position[0][1] * 1.5, position[0][2] * 1.5),
            position[1],  
            position[2]   
        ]
        

    def display_layer_parameters(self, index):
        """Clear and repopulate the parameter area with the form for the layer at the given index."""
        if index < 0:
            return  # No layer selected

        # ✅ **Clear previous parameters**
        for i in reversed(range(self.param_layout.count())):
            self.param_layout.itemAt(i).widget().deleteLater()

        # ✅ **Create a parameter group for the selected layer**
        section_box = QGroupBox(f"Layer {index + 1} Parameters")
        form = QFormLayout()

        heat_algo = QComboBox()
        heat_algo.addItems(["Heat1", "Heat2"])
        form.addRow("Heat Algorithm:", heat_algo)

        speed_spin = QSpinBox()
        speed_spin.setRange(0, 100)
        form.addRow("Speed:", speed_spin)

        power_spin = QSpinBox()
        power_spin.setRange(0, 100)
        form.addRow("Power:", power_spin)

        section_box.setLayout(form)
        self.param_layout.addWidget(section_box)
        
        self.plotter_show_layer(index)
        
        
    def plotter_show_layer(self,layer_number):
        """Highlight the slice at layer_number in the 3D plotter (e.g. red, higher opacity)."""
        for plane in range(0,len(self.test_slice_planes)):
            if plane==layer_number:
                self.plotter.add_mesh(self.test_slice_planes[plane], color="red", opacity=0.8)
            

        
    def on_parametrization(self):
        """Handle Apply Final Parametrization: log and close the window."""
        print("Parametrization button clicked")
        self.close()  # This will close the window










#we must add soemthign liek optionss to it
class AdvancedWindow_layers1(QWidget):
    """Advanced parameterization window with a scrollable list of layer parameter sections and 3D plotter."""

    def __init__(self, box, mesh, number_of_layers=5):
        """
        Args:
            box: PyVista build box mesh (optional).
            mesh: PyVista mesh to display.
            number_of_layers: Number of layer parameter sections to create.
        """
        super().__init__()
        self.setWindowTitle("Advanced Parameterization")
        self.showMaximized()
        self.number_of_layers = number_of_layers  # Define number of layers
        self.pv_mesh = mesh
        self.box = box

        self.main_layout = QHBoxLayout()
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout()

        # Create and add layers section directly (without tabs)
        self.layers_section = self.create_scroll_section("Layers", self.number_of_layers, self.create_layer_parameters)
        self.left_layout.addWidget(self.layers_section)

        self.param_button = QPushButton("Apply Final Parametrization")
        self.param_button.clicked.connect(self.on_parametrization)
        self.left_layout.addWidget(self.param_button)

        self.left_panel.setLayout(self.left_layout)
        self.left_panel.setFixedWidth(300)  # Adjust width as needed

        # Right side (Plotter)
        self.plotter = QtInteractor()
        self.setup_plotter()

        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_layout.addWidget(self.plotter)
        self.right_panel.setLayout(self.right_layout)

        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.right_panel)
        self.setLayout(self.main_layout)

    def setup_plotter(self):
        """Add box and mesh to the plotter and adjust camera distance."""
        if self.box:
            self.plotter.add_mesh(self.box, color="lightgray", opacity=0.3)
        self.plotter.add_mesh(self.pv_mesh)
        self.plotter.reset_camera()
        position = self.plotter.camera_position
        self.plotter.camera_position = [
            (position[0][0] * 1.5, position[0][1] * 1.5, position[0][2] * 1.5),
            position[1],  
            position[2]   
        ]

    def create_scroll_section(self, title, count, create_function):
        """Build a scrollable section with a title, count label, and count group boxes; each box's form is filled by create_function."""
        section_widget = QWidget()
        section_layout = QVBoxLayout()

        title_label = QLabel(f"{title} (Count: {count})")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        section_layout.addWidget(title_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        content_layout = QVBoxLayout()

        for i in range(1, count + 1):
            section_box = QGroupBox(f"{title[:-1]} {i}")
            section_form = QFormLayout()
            create_function(section_form)  # Use create_layer_parameters
            section_box.setLayout(section_form)
            content_layout.addWidget(section_box)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        section_layout.addWidget(scroll_area)
        section_widget.setLayout(section_layout)
        return section_widget

    def create_layer_parameters(self, form):
        """Add Heat Algorithm, Speed, and Power controls to the given form layout."""
        heat_algo = QComboBox()
        heat_algo.addItems(["Heat1", "Heat2"])
        form.addRow("Heat Algorithm:", heat_algo)

        speed_spin = QSpinBox()
        speed_spin.setRange(0, 100)
        form.addRow("Speed:", speed_spin)

        power_spin = QSpinBox()
        power_spin.setRange(0, 100)
        form.addRow("Power:", power_spin)

    def on_parametrization(self):
        """Handle Apply button: log and close the window."""
        print("Parametrization button clicked")
        self.close()  # This will close the window


class AdvancedWindow_layers0(QWidget):
    """Advanced parameterization with Objects and Layers tabs, scroll sections, and 3D plotter."""

    def __init__(self,box, mesh, number_of_layers=3):
        """
        Args:
            box: PyVista build box (optional).
            mesh: PyVista mesh.
            number_of_layers: Number of layers for the layers tab.
        """
        super().__init__()
        self.setWindowTitle("Advanced Parameterization")
        self.showMaximized()
        self.number_of_layers = number_of_layers
        self.box=box
        self.pv_mesh = mesh

        self.main_layout = QHBoxLayout()
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        
        self.objects_tab = QWidget()
        self.layers_tab = QWidget()

        self.setup_objects_tab()
        self.setup_layers_tab()

        self.tab_widget.addTab(self.objects_tab, "Objects")
        self.tab_widget.addTab(self.layers_tab, "Layers")

        self.param_button = QPushButton("Apply Final Parametrization")
        self.param_button.clicked.connect(self.on_parametrization)

        self.left_layout.addWidget(self.tab_widget)
        self.left_layout.addWidget(self.param_button)
        self.left_panel.setLayout(self.left_layout)
        #sasds
        #self.left_panel.setMaximumWidth(1100)
        self.left_panel.setFixedWidth(1000)

        # Right side (Plotter)
        self.plotter = QtInteractor()
        
        # Set up the plotter
        self.setup_plotter()
        
        
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout()
        
        # Add plotter and buttons to right layout
        self.right_layout.addWidget(self.plotter)
        
        
        self.right_panel.setLayout(self.right_layout)
        
      
        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.right_panel)
        self.setLayout(self.main_layout)

    def setup_plotter(self):
        """Add box and mesh to the plotter and zoom out the camera."""
        # Add a sample sphere to visualize something
        # Replace this with your actual 3D model
        if self.box:
            self.plotter.add_mesh(self.box, color="lightgray", opacity=0.3)
            
            
        self.plotter.add_mesh(self.pv_mesh)
        
        #********
        #show the box also
        self.plotter.reset_camera()
        
        # Get the current camera position
        position = self.plotter.camera_position
    
        # Move the camera further away (zoom out effect)
        self.plotter.camera_position = [
            (position[0][0] * 1.5, position[0][1] * 1.5, position[0][2] * 1.5),  # Move camera further
            position[1],  # Focal point remains the same
            position[2]   # View up direction remains the same
        ]
        
    def setup_objects_tab(self):
        """Populate the Objects tab with a scroll section of object parameter groups."""
        layout = QVBoxLayout()
        self.object_scroll = self.create_scroll_section("Objects", self.number_of_final_object, self.create_object_parameters)
        layout.addWidget(self.object_scroll)
        self.objects_tab.setLayout(layout)

    def setup_layers_tab(self):
        """Populate the Layers tab with a scroll section of layer parameter groups."""
        layout = QVBoxLayout()
        self.layer_scroll = self.create_scroll_section("Layers", self.number_of_layers, self.create_layer_parameters)
        layout.addWidget(self.layer_scroll)
        self.layers_tab.setLayout(layout)

    def create_scroll_section(self, title, count, create_function):
        """Build a scrollable section with title, count, and group boxes; create_function(section_form, section_box) fills each box."""
        section_widget = QWidget()
        section_layout = QVBoxLayout()

        title_label = QLabel(f"{title} (Count: {count})")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        section_layout.addWidget(title_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        content_layout = QVBoxLayout()

        for i in range(1, count + 1):
            section_box = QGroupBox(f"{title[:-1]} {i}")
            section_form = QFormLayout()
            self.create_object_parameters(section_form, section_box)
            section_box.setLayout(section_form)
            content_layout.addWidget(section_box)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        section_layout.addWidget(scroll_area)
        section_widget.setLayout(section_layout)
        return section_widget

    def create_object_parameters(self, form, section_box):
        """Creates object parameters with a checkbox to enable/disable settings."""
        # Checkbox to enable/disable settings
        enable_checkbox = QCheckBox("Enable Settings")
        enable_checkbox.setChecked(False)

        # Power SpinBox
        power_spin = QSpinBox()
        power_spin.setRange(0, 100)
        form.addRow("Power:", power_spin)

        # Speed SpinBox
        speed_spin = QSpinBox()
        speed_spin.setRange(0, 100)
        form.addRow("Speed:", speed_spin)

        # Spot Size SpinBox
        spot_size_spin = QSpinBox()
        spot_size_spin.setRange(1, 10)
        form.addRow("Spot Size:", spot_size_spin)

        # Heat Pattern ComboBox
        heat_pattern = QComboBox()
        heat_pattern.addItems(["Pattern 1", "Pattern 2", "Pattern 3"])
        form.addRow("Heat Pattern:", heat_pattern)

        # Add checkbox to form
        form.insertRow(0, enable_checkbox)

        # Store all elements in a list to manage enabling/disabling
        settings_widgets = [power_spin, speed_spin, spot_size_spin, heat_pattern]

        # Initially disable widgets
        for widget in settings_widgets:
            widget.setEnabled(False)

        # Connect checkbox signal to enable/disable widgets
        enable_checkbox.stateChanged.connect(lambda state: self.toggle_settings(state, settings_widgets))



    def create_layer_parameters(self, form):
        heat_algo = QComboBox()
        heat_algo.addItems(["Heat1", "Heat2"])
        form.addRow("Heat Algorithm:", heat_algo)
        
        speed_spin = QSpinBox()
        speed_spin.setRange(0, 100)
        form.addRow("Speed:", speed_spin)
        
        power_spin = QSpinBox()
        power_spin.setRange(0, 100)
        form.addRow("Power:", power_spin)
        
    def toggle_settings(self, state, widgets):
        """Enable or disable a list of widgets based on checkbox state."""
        for widget in widgets:
            widget.setEnabled(state == 2)  # 2 = Checked
        
        '''
        here first we saw that this is in layer or other things
        also we can create two windows
        
        
        
        
        '''
    def on_parametrization(self):
        """Handle Apply button: log and close the window."""
        print("Parametrization button clicked")
        self.close()  # This will close the window














class AdvancedWindow_objects(QWidget):
    def __init__(self, box, mesh, number_of_final_object=5):
        super().__init__()
        self.setWindowTitle("Advanced Parameterization")
        self.showMaximized()
        self.number_of_final_object = number_of_final_object
        self.pv_mesh = mesh
        self.box = box
        self.object_checkboxes = []  # To track checkboxes
        self.object_meshes = {}  
        

        self.main_layout = QHBoxLayout()
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout()
        self.tab_widget = QTabWidget()

        # Only one tab now
        self.objects_tab = QWidget()
        self.setup_objects_tab()
        self.tab_widget.addTab(self.objects_tab, "Objects")

        self.param_button = QPushButton("Apply Final Parametrization")
        self.param_button.clicked.connect(self.on_parametrization)

        self.left_layout.addWidget(self.tab_widget)
        self.left_layout.addWidget(self.param_button)
        self.left_panel.setLayout(self.left_layout)
        self.left_panel.setFixedWidth(1000)

        # Right side (Plotter)
        self.plotter = QtInteractor()
        self.setup_plotter()

        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_layout.addWidget(self.plotter)
        self.right_panel.setLayout(self.right_layout)

        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.right_panel)
        self.setLayout(self.main_layout)
        
        
        
       



    def setup_plotter(self):
        """Add box and mesh to the plotter and zoom out the camera."""
        if self.box:
            self.plotter.add_mesh(self.box, color="lightgray", opacity=0.3)

        self.plotter.add_mesh(self.pv_mesh)
        self.plotter.reset_camera()

        # Adjust camera position
        position = self.plotter.camera_position
        self.plotter.camera_position = [
            (position[0][0] * 1.5, position[0][1] * 1.5, position[0][2] * 1.5),
            position[1],
            position[2]
        ]

    def setup_objects_tab(self):
        """Populate the Objects tab with a scroll section of object parameter groups."""
        layout = QVBoxLayout()
        self.object_scroll = self.create_scroll_section("Objects", self.number_of_final_object, self.create_object_parameters)
        layout.addWidget(self.object_scroll)
        self.objects_tab.setLayout(layout)

    def create_scroll_section(self, title, count, create_function):
        """Build a scrollable section with title, count, and group boxes; create_function(form, index) fills each box."""
        section_widget = QWidget()
        section_layout = QVBoxLayout()

        title_label = QLabel(f"{title} (Count: {count})")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        section_layout.addWidget(title_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        content_layout = QVBoxLayout()

        for i in range(1, count + 1):
            section_box = QGroupBox(f"{title[:-1]} {i}")
            section_form = QFormLayout()
            self.create_object_parameters(section_form,i)
            section_box.setLayout(section_form)
            content_layout.addWidget(section_box)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        section_layout.addWidget(scroll_area)
        section_widget.setLayout(section_layout)
        return section_widget


#add index
    def create_object_parameters(self, form,index):
        """Add Enable Settings checkbox and Power, Speed, Spot Size, Heat Pattern for object at index; connect to toggle_settings with index for plot preview."""
        enable_checkbox = QCheckBox("Enable Settings")
        enable_checkbox.setChecked(False)

        power_spin = QSpinBox()
        power_spin.setRange(0, 100)
        form.addRow("Power:", power_spin)

        speed_spin = QSpinBox()
        speed_spin.setRange(0, 100)
        form.addRow("Speed:", speed_spin)

        spot_size_spin = QSpinBox()
        spot_size_spin.setRange(1, 10)
        form.addRow("Spot Size:", spot_size_spin)

        heat_pattern = QComboBox()
        heat_pattern.addItems(["Pattern 1", "Pattern 2", "Pattern 3"])
        form.addRow("Heat Pattern:", heat_pattern)

        form.insertRow(0, enable_checkbox)
        settings_widgets = [power_spin, speed_spin, spot_size_spin, heat_pattern]

        for widget in settings_widgets:
            widget.setEnabled(False)

        enable_checkbox.stateChanged.connect(lambda state: self.toggle_settings(state, settings_widgets,index))
        
        self.object_checkboxes.append(enable_checkbox)  # Store checkbox



    
            
        
        
        
    def toggle_settings(self, state, widgets,index):
        """Enable/disable widgets and optionally add or remove the object cylinder preview in the plotter for the given index."""
        for widget in widgets:
            widget.setEnabled(state == 2)  # 2 = Checked
            
        if state == 2:  # If checkbox is checked, plot the object
            if index not in self.object_meshes:
        #self.object_meshes[index] doesn do because each time it show
                x_list, y_list, side_length = self.object_cenetr_parameetr()
        
                if index - 1 < len(x_list):  # Ensure index is valid
                    RADIUS = side_length[index - 1]
                    X = x_list[index - 1]
                    Y = y_list[index - 1]
        
                    cylinder = self.create_cylinder(radius=RADIUS, height=50)
                    cylinder.apply_translation([X, Y, 25])
                    
                    self.object_meshes[index] = self.plotter.add_mesh(cylinder, color="red", opacity=0.1)
        
                    #self.plotter.add_mesh(cylinder, color="red", opacity=0.1)
                    self.plotter.reset_camera()  # Update camera view
                    
        
            
        else:  # If checkbox is unchecked, remove the object
           if index in self.object_meshes:
               self.plotter.remove_actor(self.object_meshes[index])
               del self.object_meshes[index]  # Remove from dictionary
        
        
        
    def object_cenetr_parameetr(self):
        """Detect bounding squares for the mesh and return (x_list, y_list, side_length) for each object."""
        PM_Processor=Core_Mesh_Processor()
        
        squares=PM_Processor.object_detection(self.pv_mesh)
        
        x_list=[]
        y_list=[]
        side_length=[]
        
        for x,y,r in squares:
            x_list.append(x)
            y_list.append(y)
            side_length.append(r)
        
        return x_list,y_list,side_length
        
    def create_cylinder(self,radius=5.0, height=20.0):
        """
        Create a trimesh cylinder for 3D preview.

        Args:
            radius: Radius of the cylinder.
            height: Height of the cylinder.

        Returns:
            Trimesh cylinder mesh (32 sections).
        """
        return trimesh.creation.cylinder(radius=radius, height=height, sections=32)
      
        
      

        
        

    def on_parametrization(self):
        """Handle Apply button: log and close the window."""
        print("Parametrization button clicked")
        self.close()  # This will close the window


















#it must get the default values as default 
class AdvancedWindow_objects0(QWidget):
    """Advanced parameterization with Objects and Layers tabs, scroll sections, and 3D plotter (variant with object/layer forms)."""

    def __init__(self, box,mesh, number_of_final_object=5):
        """
        Args:
            box: PyVista build box (optional).
            mesh: PyVista mesh.
            number_of_final_object: Number of objects for the Objects tab.
        """
        super().__init__()
        self.setWindowTitle("Advanced Parameterization")
        self.showMaximized()
        self.number_of_final_object = number_of_final_object
        self.pv_mesh = mesh
        self.box=box
        
        self.main_layout = QHBoxLayout()
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        
        self.objects_tab = QWidget()
        self.layers_tab = QWidget()

        #self.setup_objects_tab()
        #self.setup_layers_tab()

        #self.tab_widget.addTab(self.objects_tab, "Objects")
        #self.tab_widget.addTab(self.layers_tab, "Layers")

        self.param_button = QPushButton("Apply Final Parametrization")
        self.param_button.clicked.connect(self.on_parametrization)

        self.left_layout.addWidget(self.tab_widget)
        self.left_layout.addWidget(self.param_button)
        self.left_panel.setLayout(self.left_layout)
        #sasds
        #self.left_panel.setMaximumWidth(1100)
        self.left_panel.setFixedWidth(1000)

        # Right side (Plotter)
        self.plotter = QtInteractor()
        
        # Set up the plotter
        self.setup_plotter()
        
        
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout()
        
        # Add plotter and buttons to right layout
        self.right_layout.addWidget(self.plotter)
        
        
        self.right_panel.setLayout(self.right_layout)
        
      
        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.right_panel)
        self.setLayout(self.main_layout)

    def setup_plotter(self):
        """Add box and mesh to the plotter and zoom out the camera."""
        if self.box:
            self.plotter.add_mesh(self.box, color="lightgray", opacity=0.3)
            
            
        # Add a sample sphere to visualize something
        # Replace this with your actual 3D model
        self.plotter.add_mesh(self.pv_mesh)
        
        #********
        #show the box also
        self.plotter.reset_camera()
        
        # Get the current camera position
        position = self.plotter.camera_position
    
        # Move the camera further away (zoom out effect)
        self.plotter.camera_position = [
            (position[0][0] * 1.5, position[0][1] * 1.5, position[0][2] * 1.5),  # Move camera further
            position[1],  # Focal point remains the same
            position[2]   # View up direction remains the same
        ]
        
    def setup_objects_tab(self):
        """Populate the Objects tab with a scroll section of object parameter groups."""
        layout = QVBoxLayout()
        self.object_scroll = self.create_scroll_section("Objects", self.number_of_final_object, self.create_object_parameters)
        layout.addWidget(self.object_scroll)
        self.objects_tab.setLayout(layout)

    def setup_layers_tab(self):
        """Populate the Layers tab with a scroll section of layer parameter groups."""
        layout = QVBoxLayout()
        self.layer_scroll = self.create_scroll_section("Layers", self.number_of_layers, self.create_layer_parameters)
        layout.addWidget(self.layer_scroll)
        self.layers_tab.setLayout(layout)

    def create_scroll_section(self, title, count, create_function):
        """Build a scrollable section with title, count, and group boxes; create_function(form, section_box) fills each box."""
        section_widget = QWidget()
        section_layout = QVBoxLayout()

        title_label = QLabel(f"{title} (Count: {count})")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        section_layout.addWidget(title_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        content_layout = QVBoxLayout()

        for i in range(1, count + 1):
            section_box = QGroupBox(f"{title[:-1]} {i}")
            section_form = QFormLayout()
            self.create_object_parameters(section_form, section_box)
            section_box.setLayout(section_form)
            content_layout.addWidget(section_box)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        section_layout.addWidget(scroll_area)
        section_widget.setLayout(section_layout)
        return section_widget

    def create_object_parameters(self, form, section_box):
        """Add Enable Settings checkbox and Power, Speed, Spot Size, Heat Pattern; connect checkbox to toggle_settings."""
        # Checkbox to enable/disable settings
        enable_checkbox = QCheckBox("Enable Settings")
        enable_checkbox.setChecked(False)

        # Power SpinBox
        power_spin = QSpinBox()
        power_spin.setRange(0, 100)
        form.addRow("Power:", power_spin)

        # Speed SpinBox
        speed_spin = QSpinBox()
        speed_spin.setRange(0, 100)
        form.addRow("Speed:", speed_spin)

        # Spot Size SpinBox
        spot_size_spin = QSpinBox()
        spot_size_spin.setRange(1, 10)
        form.addRow("Spot Size:", spot_size_spin)

        # Heat Pattern ComboBox
        heat_pattern = QComboBox()
        heat_pattern.addItems(["Pattern 1", "Pattern 2", "Pattern 3"])
        form.addRow("Heat Pattern:", heat_pattern)

        # Add checkbox to form
        form.insertRow(0, enable_checkbox)

        # Store all elements in a list to manage enabling/disabling
        settings_widgets = [power_spin, speed_spin, spot_size_spin, heat_pattern]

        # Initially disable widgets
        for widget in settings_widgets:
            widget.setEnabled(False)

        # Connect checkbox signal to enable/disable widgets
        enable_checkbox.stateChanged.connect(lambda state: self.toggle_settings(state, settings_widgets))



    def create_layer_parameters(self, form):
        heat_algo = QComboBox()
        heat_algo.addItems(["Heat1", "Heat2"])
        form.addRow("Heat Algorithm:", heat_algo)
        
        speed_spin = QSpinBox()
        speed_spin.setRange(0, 100)
        form.addRow("Speed:", speed_spin)
        
        power_spin = QSpinBox()
        power_spin.setRange(0, 100)
        form.addRow("Power:", power_spin)
        
    def toggle_settings(self, state, widgets):
        """Enable or disable a list of widgets based on checkbox state."""
        for widget in widgets:
            widget.setEnabled(state == 2)  # 2 = Checked

        '''
        here first we saw that this is in layer or other things
        also we can create two windows
        
        '''
    def on_parametrization(self):
        """Handle Apply button: log and close the window."""
        print("Parametrization button clicked")












#^^^ here just make sure t have somje fucntiosn to chekc the project details  
   
