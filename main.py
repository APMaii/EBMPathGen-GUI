#========================================================================
#========================================================================
#========================================================================
'''                       Entry point: run the GUI                      '''
#========================================================================
#========================================================================
#========================================================================

import sys
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox

from ebm_pathgen_gui import ProjectSetupDialog, STLManipulatorTabs


if __name__ == '__main__':
    #app = QApplication([])
    #window = STLManipulatorTabs()
    #window.show()
    #app.exec_()

    app = QApplication(sys.argv)

    try:
        # Show project setup dialog
        dialog = ProjectSetupDialog()
        if dialog.exec_() == QDialog.Accepted:

            project_details = dialog.get_project_details()
            if project_details["name"] and project_details["material"] :

                window = STLManipulatorTabs(project_details)
                window.show()
                sys.exit(app.exec_())

    except Exception as e:
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Critical)
        error_msg.setWindowTitle("Error")
        error_msg.setText("An unexpected error occurred!")
        error_msg.setInformativeText(str(e))  # Show the actual error message
        error_msg.exec_()
