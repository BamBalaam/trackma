# This file is part of Trackma.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

pyqt_version = 5

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableView, QAbstractItemView, QHeaderView, QSpinBox,
    QDialogButtonBox, QStackedWidget, QComboBox, QRadioButton)

from trackma.ui.qt.widgets import AddTableDetailsView, AddCardView

class AddDialog(QDialog):
    worker = None
    selected_show = None
    results = []

    def __init__(self, parent, worker, current_status, default=None):
        QDialog.__init__(self, parent)
        self.resize(950, 700)
        self.setWindowTitle('Search/Add from Remote')
        self.worker = worker
        self.current_status = current_status
        self.default = default
        if default:
            self.setWindowTitle('Search/Add from Remote for new show: %s' % default)

        layout = QVBoxLayout()

        # Create top layout
        top_layout = QHBoxLayout()
        self.search_rad = QRadioButton('By keyword:')
        self.search_rad.setChecked(True)
        self.search_txt = QLineEdit()
        self.search_txt.returnPressed.connect(self.s_search)
        self.search_txt.setFocus()
        if default:
            self.search_txt.setText(default)
        self.search_btn = QPushButton('Search')
        self.search_btn.clicked.connect(self.s_search)
        top_layout.addWidget(self.search_rad)
        top_layout.addWidget(self.search_txt)
        top_layout.addWidget(self.search_btn)
        
        # Create filter line
        filters_layout = QHBoxLayout()
        filters_layout.setAlignment(QtCore.Qt.AlignLeft)
        
        self.season_rad = QRadioButton('By season:')
        self.season_combo = QComboBox()
        self.season_combo.addItem('Winter')
        self.season_combo.addItem('Spring')
        self.season_combo.addItem('Summer')
        self.season_combo.addItem('Fall')
        
        self.season_year = QSpinBox()
        self.season_year.setRange(1900, 2017)
        self.season_year.setValue(2017)
        
        view_combo = QComboBox()
        view_combo.addItem('Table view')
        view_combo.addItem('Card view')
        view_combo.currentIndexChanged.connect(self.s_change_view)
        
        filters_layout.addWidget(self.season_rad)
        filters_layout.addWidget(self.season_combo)
        filters_layout.addWidget(self.season_year)
        filters_layout.addWidget(view_combo)

        # Create central content
        self.contents = QStackedWidget()
        
        # Set up views
        tableview = AddTableDetailsView(None, self.worker)
        tableview.changed.connect(self.s_selected)
        self.contents.addWidget(tableview)
        
        cardview = AddCardView(api_info=self.worker.engine.api_info)
        cardview.changed.connect(self.s_selected)
        self.contents.addWidget(cardview)
        
        self.set_results([{'id': 1, 'title': 'Hola', 'image': 'https://omaera.org/icon.png'}])

        bottom_buttons = QDialogButtonBox()
        bottom_buttons.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.add_btn = bottom_buttons.addButton("Add", QDialogButtonBox.AcceptRole)
        bottom_buttons.accepted.connect(self.s_add)
        bottom_buttons.rejected.connect(self.close)

        # Finish layout
        layout.addLayout(top_layout)
        layout.addLayout(filters_layout)
        layout.addWidget(self.contents)
        layout.addWidget(bottom_buttons)
        self.setLayout(layout)

    def worker_call(self, function, ret_function, *args, **kwargs):
        # Run worker in a thread
        self.worker.set_function(function, ret_function, *args, **kwargs)
        self.worker.start()

    def _enable_widgets(self, enable):
        self.search_btn.setEnabled(enable)
        self.contents.currentWidget().setEnabled(enable)

    def set_results(self, results):
        self.results = results
        self.contents.currentWidget().setResults(self.results)

    # Slots
    def s_change_view(self, item):
        self.contents.currentWidget().getModel().setResults(None)
        self.contents.setCurrentIndex(item)
        self.contents.currentWidget().getModel().setResults(self.results)
        
    def s_search(self):
        if self.search_rad.isChecked():
            criteria = self.search_txt.text().strip()
            if not criteria:
                return
            method = "kw"
        elif self.season_rad.isChecked():
            criteria = (self.season_combo.currentText().lower(), self.season_year.value())
            method = "season"
        
        self.contents.currentWidget().clearSelection()
        self.selected_show = None
        
        self._enable_widgets(True)
        self.add_btn.setEnabled(False)
        
        self.worker_call('search', self.r_searched, criteria, method)
    
    def s_selected(self, show):
        self.selected_show = show
        self.add_btn.setEnabled(True)
        
    def s_add(self):
        if self.selected_show:
            self.worker_call('add_show', self.r_added, self.selected_show, self.current_status)

    # Worker responses
    def r_searched(self, result):
        self._enable_widgets(True)
        
        if result['success']:
            self.set_results(result['results'])
            
            """
            if self.table.currentRow() is 0:  # Row number hasn't changed but the data probably has!
                self.s_show_selected(self.table.item(0, 0))
            self.table.setCurrentItem(self.table.item(0, 0))"""
        else:
            self.set_results(None)

    def r_added(self, result):
        if result['success']:
            if self.default:
                self.accept()
