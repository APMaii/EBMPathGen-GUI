"""
Application-wide constants for EBM PathGen GUI.

Defines default dimensions (base radius, thickness, Z max), and shared UI styling
(e.g. next-button stylesheet) used across the application.
"""
#========================================================================
#========================================================================
#========================================================================
'''                       Default Variables                            '''
#========================================================================
#========================================================================
#======================================================================== 
#??? it must set before


DEFAULT_BASE_RADIUS=50000 #radius of basement of EBM
DEFAULT_BASE_THICKNESS=10000
Z_MAX_EBM_BASE=200000

#-----HERE WE NEED .PNG files



#========================================================================
#========================================================================
#========================================================================
'''                       Tab Setting                                '''
#========================================================================
#========================================================================
#========================================================================


next_button_styles="""
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
"""
