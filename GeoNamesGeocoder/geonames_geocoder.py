# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeoNamesGeocoder
                                 A QGIS plugin
 Geo-coding of places, based on a local copy of the GeoNames database
                              -------------------
        begin                : 2016-02-09
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Thomas Becker (Aarhus Univiersity)
        email                : thob@envs.au.dk
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QMessageBox, QApplication
import db_manager.db_plugins.postgis.connector as pg_con
from qgis.core import QgsDataSourceURI
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from geonames_geocoder_dialog import GeoNamesGeocoderDialog
import os.path


class GeoNamesGeocoder:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GeoNamesGeocoder_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = GeoNamesGeocoderDialog()
        
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&GeoNames Geocoder')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'GeoNamesGeocoder')
        self.toolbar.setObjectName(u'GeoNamesGeocoder')
        # invoke the select_output_file function
        self.dlg.ledt_csv.clear()
        self.dlg.btn_csv.clicked.connect(self.select_output_file)
        # invoke the get_field_names function
        self.dlg.cmb_lay.currentIndexChanged.connect(self.get_field_names)
        # invoke the get_connection function
        self.dlg.cmb_db.currentIndexChanged.connect(self.get_connections)
        # invoke the get_db_tables function
        self.dlg.cmb_con.currentIndexChanged.connect(self.get_db_tables)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('GeoNamesGeocoder', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToDatabaseMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/GeoNamesGeocoder/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'GeoNames Geocoder'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginDatabaseMenu(
                self.tr(u'&GeoNames Geocoder'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def get_field_names(self):
        """Retrieves the field names of the selected combobox item."""
        layers = []
        for layer in self.iface.legendInterface().layers():
            layers.append(layer)
        try:
            selected_layer_index = self.dlg.cmb_lay.currentIndex()
            selected_layer = layers[selected_layer_index]
            fields_list = []
            for field in selected_layer.pendingFields():
                fields_list.append(field.name())
            
            self.dlg.cmb_cntr.clear()
            self.dlg.cmb_cntr.addItems(fields_list)
            self.dlg.cmb_place.clear()
            self.dlg.cmb_place.addItems(fields_list)
            self.dlg.cmb_zip.clear()
            self.dlg.cmb_zip.addItems(fields_list)
        except IndexError:
            QMessageBox.critical(None,
                                 'Layer and Tables:',
                                 """It seems like you have no layers or tables loaded.\n
Close the dialog, load at least the information to geo-code, and start again.\n\n
If that is not the case then get in contact with the developer.""")

    def get_connections(self):
        """Get the db connections, based on the selection in the database field"""
        qs = QSettings()
        con_list = []
        selected_db_name = self.dlg.cmb_db.currentText()
        if not selected_db_name == '':
            for k in qs.allKeys():
                qsk = k.split('/')
                if qsk[0] == selected_db_name and qsk[2] not in con_list and qsk[2] is not 'selected':
                    con_list.append(qsk[2])

        if len(con_list) > 0:
            con_list.remove('selected')
        self.dlg.cmb_con.clear()
        self.dlg.cmb_con.addItems(con_list)

    def get_db_tables(self):
        """Retrieve all tables from the selected database."""
        self.dlg.cmb_geo.clear()
        db_name = self.dlg.cmb_db.currentText()
        con_name = self.dlg.cmb_con.currentText()
        con_str = "{db}/connections/{con}/".format(db=db_name, con=con_name)
        qs = QSettings()
        db_host = qs.value(con_str + "host")
        db_port = qs.value(con_str + "port")
        db_name = qs.value(con_str + "database")
        con_usr = qs.value(con_str + "username")
        con_pwd = qs.value(con_str + "password")
        uri = QgsDataSourceURI()
        uri.setConnection(db_host, db_port, db_name, con_usr, con_pwd)
        post_c = pg_con.PostGisDBConnector(uri)
        tbl_list = []
        for table in post_c.getTables():
            if table[3] or table[1] == 'spatial_ref_sys':
                pass
            else:
                tbl_list.append(table[1])
        if len(tbl_list) == 0:
            QMessageBox.warning(None,
                                'Layer and Tables',
                                """There are no tables to geo-code in this database.""")
        else:
            self.dlg.cmb_geo.addItems(tbl_list)



    def select_output_file(self):
        """Provides a file dialog to specify location and filename for the output file."""
        filename = QFileDialog.getSaveFileName(self.dlg, 'Select output file ', '', self.tr('CSV Files (*.csv)'))
        self.dlg.ledt_csv.setText(filename)

    def run(self):
        """Run method that performs all the real work"""
        # get all available Databases and their connections.
        db_default = ['PostgreSQL', 'SpatialLite']
        db_con_dict = {}
        qs = QSettings()
        for k in qs.allKeys():
            qsk = k.split('/')
            if qsk[0] in db_default and qsk[0] not in db_con_dict.keys():
                db_con_dict.update({qsk[0]: qsk[2]})

        self.dlg.cmb_db.clear()
        self.dlg.cmb_db.addItems(db_con_dict.keys())
        self.get_connections()
        self.get_db_tables()
        # list tables to select geonames
        tables = self.iface.legendInterface().layers()
        layers_list = []
        for layer in tables:
            layers_list.append(layer.name())

        self.dlg.cmb_lay.clear()
        self.dlg.cmb_lay.addItems(layers_list)
        # list field names of initial table
        self.get_field_names()
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
