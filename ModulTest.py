# -*- coding: utf-8 -*-
"""
/***************************************************************************
 KlasaTest
                                 A QGIS plugin
 testowanie
                              -------------------
        begin                : 2016-02-08
        git sha              : $Format:%H$
        copyright            : (C) 2016 by agata
        email                : agata@agata
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
from PyQt4.QtCore import *
from PyQt4.QtGui import QAction, QIcon, QFileDialog
from qgis.utils import iface
##from qgis.gui import QgsMapCanvas
from qgis.core import QgsMapLayerRegistry, QgsField, QgsPoint, QgsExpression
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from ModulTest_dialog import KlasaTestDialog
import os.path
import processing
import csv


class KlasaTest:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
           # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'KlasaTest_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = KlasaTestDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&WtyczkaTestowa')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'KlasaTest')
        self.toolbar.setObjectName(u'KlasaTest')

        self.dlg.pushButton.clicked.connect(self.select_output_file)

        self.dlg.comboBox_2.currentIndexChanged.connect(self.feature_list)

        self.layer_name = self.dlg.comboBox_2.currentText()

    def feature_list(self):
        self.dlg.comboBox_3.clear()
        self.layer_name = self.dlg.comboBox_2.currentText()

        try:
            self.dlg.comboBox_3.addItems(self.get_features_names(
                QgsMapLayerRegistry.instance().mapLayersByName(self.layer_name)[0]))
        except:
            print 'error', self.layer_name
            self.dlg.comboBox_3.clear()
#        self.dlg.comboBox_3.addItems(self.get_features_names(QgsMapLayerRegistry.instance().mapLayersByName("wojewodztwa")[0]))

    def select_output_file(self):
        filename = QFileDialog.getSaveFileName(None, "Select output folder ", "", '.csv')
        self.dlg.lineEdit.setText(filename)

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
        return QCoreApplication.translate('KlasaTest', message)

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
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/KlasaTest/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'TestujeTestowaWtyczke'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&WtyczkaTestowa'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def get_features_dict(self, layer):
        data_tab = []
        field_names = self.get_features_names(layer)
        for x in layer.getFeatures():
            data_tab.append(dict(zip(field_names, x.attributes())))

        return data_tab

    def get_features_names(self, layer):

        return [field.name() for field in layer.pendingFields()]

        # liczy dlugosc  i dodaje do tabeli pole z wyliczonymi wartosciami

    def calculate_length(self):
        layer = QgsMapLayerRegistry.instance().mapLayersByName("memory:temp_layer")[0]
        provider = layer.dataProvider()

        #field = QgsField("length", QVariant.Double,len = 6, prec = 2)
        provider.addAttributes([QgsField("dlu", QVariant.Double, len=6, prec=2)])
        layer.updateFields()

        idx = layer.fieldNameIndex('dlu')

        layer.startEditing()
        for feat in layer.getFeatures():
            lengths = feat.geometry().length()
            layer.changeAttributeValue(feat.id(), idx, lengths)
        layer.commitChanges()

    def calculate_field_value(self):
        layer = QgsMapLayerRegistry.instance().mapLayersByName("memory:temp_layer")[0]
        provider = layer.dataProvider()
        layer.startEditing()

        provider.addAttributes([QgsField('n', QVariant.Double)])
        layer.updateFields()

        idx = layer.fieldNameIndex('n')

        e = QgsExpression("dlu * 2")
        e.prepare(layer.pendingFields())

        for f in layer.getFeatures():
            f[idx] = e.evaluate(f)
            layer.changeAttributeValue(f.id(), idx, e.evaluate(f))
        layer.commitChanges()

        # wybór kolumn do zapisania w csv
    def save_columns_i_want(self, layer):
        layer = QgsMapLayerRegistry.instance().mapLayersByName("memory:temp_layer")[0]
        features = layer.getFeatures()
        col_name = self.dlg.comboBox_3.currentText()
        columns = [col_name, 'dlu', 'num_of_vert', 'n']

        filteredFields = []
        for feature in features:
            attrs = [feature[column] for column in columns]
            filteredFields.append(attrs)

        return filteredFields

    def column_names(self):
        col_name = self.dlg.comboBox_3.currentText()
        columns = [col_name, 'dlu', 'num_of_vert', 'n']
        return columns

        # zlicza ilość wezlow w odcinku
    def number_of_vertices(self):
        layer = QgsMapLayerRegistry.instance().mapLayersByName("memory:temp_layer")[0]
        prov = layer.dataProvider()

        prov.addAttributes([QgsField('num_of_vert', QVariant.Int)])
        layer.updateFields()

        idx = layer.fieldNameIndex('num_of_vert')

        layer.startEditing()
        for feature in layer.getFeatures():
            if feature.geometry().isMultipart():
                a_s = (sum(len(i) for i in feature.geometry().asMultiPolyline()))
                layer.changeAttributeValue(feature.id(), idx, a_s)
            else:
                b_s = (len(feature.geometry().asPolyline()))
                layer.changeAttributeValue(feature.id(), idx, b_s)
        layer.commitChanges()


#    def get_layer_list(self)

    def run(self):

        # get the layer list
        layers = self.iface.legendInterface().layers()
        layers_name_list = [layer.name() for layer in layers]

        # clear all comboBoxes
        self.dlg.comboBox.clear()
        self.dlg.comboBox_2.clear()
        self.dlg.comboBox_3.clear()
        # add layer list to each comoBox
        self.dlg.comboBox.addItems(layers_name_list)
        self.dlg.comboBox_2.addItems(layers_name_list)

        # show the dialog screen
        self.dlg.show()
        # get the 'ok' button state
        result = self.dlg.exec_()
        # determine if "ok" button was pressed
        if result:

            selectedLayer = layers[self.dlg.comboBox.currentIndex()]
            selectedLayer_2 = layers[self.dlg.comboBox_2.currentIndex()]

            processing.runandload("qgis:intersection", selectedLayer,
                                  selectedLayer_2, "memory:temp_layer")
            layer = QgsMapLayerRegistry.instance().mapLayersByName("memory:temp_layer")[0]

            self.calculate_length()
            self.number_of_vertices()
            self.calculate_field_value()
            column_names = self.column_names()

            ##selected_field = self.dlg.comboBox_3.currentText()

            save = self.save_columns_i_want(layer)
            intersection_data = self.get_features_dict(layer)
            save_path = self.dlg.lineEdit.text()
            if not save_path:
                save_path = os.path.dirname(__file__)

            with open(save_path, 'a') as csvfile:
                writer = csv.writer(csvfile, delimiter=',')
                writer.writerow(column_names)
                for field in save:
                    writer.writerow(field)

            # delete temp layer
            QgsMapLayerRegistry.instance().removeMapLayers([layer.id()])

#
#
#
