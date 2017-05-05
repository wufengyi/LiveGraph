#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
# import serial
import _winreg
import threading
import time
import datetime
import random
import math
import FileDialog

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtGui import *
from PyQt4.QtCore import *

# GUI
from ui_viewerSecond import Ui_MainWindow

import pyqtgraph as pg
pg.setConfigOption('background', 'k')
COLORS = {
    'red': (214, 39, 40),
    'blue': (31, 119, 180),
    'cyan': (23, 190, 207),
    'green': (44, 160, 44),
    'yellow': (188, 189, 34)

}

'''PyQTGraph import
COLORS Dict for coloring plot's curves'''

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class MatplotlibWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(MatplotlibWidget, self).__init__(parent)
        # self.figure = mpl.figure()
        # self.axes = self.figure.add_axes([0.06, 0.16, 0.95, 0.8])#size plot place[0.05, 0.1, 0.84, 0.8][0.06, 0.2, 0.84, 0.8][0.06, 0.21, 0.83, 0.8]
        self.canvas = pg.PlotWidget()
        self.p = self.canvas.plotItem
        self.p.enableAutoRange('xy', True)
        self.p.showGrid(1, 1)
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.p.addItem(self.vLine, ignoreBounds=True)
        self.p.addItem(self.hLine, ignoreBounds=True)
        self.vb = self.p.vb
        self.p.scene().sigMouseMoved.connect(self.mouseMoved)
        self.layoutVertical = QtGui.QVBoxLayout(self)
        self.layoutVertical.addWidget(self.canvas)

        """Creating canvas and adding it to Main Window"""
        #
        # cid = self.canvas.mpl_connect('motion_notify_event', self.onmove)
        # cid = self.canvas.mpl_connect('axes_leave_event', self.onleave)

    def mouseMoved(self, evt):
        pos = evt
        if self.p.sceneBoundingRect().contains(pos):
            mousePoint = self.vb.mapSceneToView(pos)
            self.emit(QtCore.SIGNAL('MouseMove(int,QString)'), int(mousePoint.x()), str(round(mousePoint.y(), 2)))
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())


# main window
class MWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()
        self.setupUi(self)
        #
        # self.serial = serial.Serial()#UART
        self.FLAG = False
        self.send_timer = QtCore.QTimer()  # timer
        self.time_timer = QtCore.QTimer()  # timer
        # 0- read file, 1 - read COM port
        self.mode = 0
        # thread
        self.alive = threading.Event()
        self.thread = None
        # file
        self.i = 0
        self.f = None  # file object
        self.path_file = ''  # path
        #
        self.f_pause = False
        #
        # data for plot
        self.mass_plot = []  #
        #
        self.mass_time = []
        #
        self.mass_ac_voltage_t = []
        self.mass_ac_voltage = []  #
        self.mass_ac_voltage_x = []  #
        #
        self.mass_dc_voltage_t = []  #
        self.mass_dc_voltage = []  #
        self.mass_dc_voltage_x = []  #
        #
        self.mass_ac_current_t = []  #
        self.mass_ac_current = []  #
        self.mass_ac_current_x = []  #
        #
        self.mass_dc_current_t = []  #
        self.mass_dc_current = []  #
        self.mass_dc_current_x = []  #
        #
        self.mass_resistance_t = []  #
        self.mass_resistance = []  #
        self.mass_resistance_x = []  #
        #
        self.mass_test_continuity_t = []  #
        self.mass_test_continuity = []  #
        self.mass_test_continuity_x = []  #
        #
        self.mass_logic_level_t = []  #
        self.mass_logic_level = []  #
        self.mass_logic_level_x = []  #
        # time
        self.first_time = ''
        self.last_time = ''
        #
        self.last_period = False  #
        self.period = 50
        self.replay_speed = 500  # ms
        self.f_first = True  # firsf plot settings
        self.log_file = None  # log file *.csv
        # OpenDialog
        self.dialogTXT = QtGui.QFileDialog()
        self.dialogTXT.setNameFilter("Data files (*.txt)")
        self.dialogTXT.setViewMode(QtGui.QFileDialog.Detail)
        # MessageBox Error
        self.msgBoxError = QMessageBox()
        self.msgBoxError.setWindowTitle("Error")
        self.msgBoxError.setIcon(QMessageBox.Critical)
        # Info box
        self.msgBox = QtGui.QMessageBox()
        self.msgBox.setWindowTitle(_fromUtf8("Message"))
        # self.msgBox.setWindowIcon(icon)
        self.msgBox.setIcon(QMessageBox.Question)
        self.msgBox.addButton(QtGui.QPushButton(_fromUtf8('Yes')), QtGui.QMessageBox.YesRole)
        self.msgBox.addButton(QtGui.QPushButton(_fromUtf8('No')), QtGui.QMessageBox.NoRole)
        # Font
        self.Bfont = QtGui.QFont()
        self.Bfont.setBold(True)
        # graph1
        self.matplotlibWidget = MatplotlibWidget(self)  # graph
        self.groupBox.setLayout(self.matplotlibWidget.layoutVertical)  #
        QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL("clicked()"), self.selectFile)  # select file
        QtCore.QObject.connect(self.pushButton_2, QtCore.SIGNAL("clicked()"), self.start)  # start read file
        QtCore.QObject.connect(self.pushButton_3, QtCore.SIGNAL("clicked()"), self.connectUart)  # connect UART
        QtCore.QObject.connect(self.pushButton_4, QtCore.SIGNAL("clicked()"), self.stop)  # start read file
        QtCore.QObject.connect(self.pushButton_5, QtCore.SIGNAL("clicked()"), self.restart)  # restart
        QtCore.QObject.connect(self.send_timer, QtCore.SIGNAL("timeout()"), self.checkTimer)  #
        QtCore.QObject.connect(self.time_timer, QtCore.SIGNAL("timeout()"), self.checkTimeTimer)  #
        QtCore.QObject.connect(self, QtCore.SIGNAL("OutputData(QString,QString,QString)"), self.viewData)  #
        QtCore.QObject.connect(self.comboBox, QtCore.SIGNAL("currentIndexChanged(int)"), self.selectFrequency)  #
        QtCore.QObject.connect(self.comboBox_2, QtCore.SIGNAL("currentIndexChanged(int)"), self.selectOutput)  #
        QtCore.QObject.connect(self.matplotlibWidget, QtCore.SIGNAL("MouseMove(int,QString)"), self.mouseMove)  #
        QtCore.QObject.connect(self.matplotlibWidget, QtCore.SIGNAL("MouseLeave"), self.mouseLeave)  #
        # self.matplotlibWidget.spos.on_changed(self.update)
        # menu and action
        self.menubar = QtGui.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 900, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menu = QtGui.QMenu(self.menubar)
        self.menu.setObjectName(_fromUtf8("menu"))
        self.setMenuBar(self.menubar)
        self.action_Exit = QtGui.QAction(self)
        self.action_Exit.setObjectName(_fromUtf8("action_Exit"))
        self.menu.addAction(self.action_Exit)
        self.menubar.addAction(self.menu.menuAction())
        self.menu.setTitle("File")
        self.action_Exit.setText("Exit")
        QtCore.QObject.connect(self.action_Exit, QtCore.SIGNAL("triggered()"), self,
                               QtCore.SLOT("close()"))  # close event
        # activate function
        self.activate()
        self.loadPorts()

    def activate(self):
        # self.setMinimumSize(QtCore.QSize(1100, 700))#minimum size
        # self.setMaximumSize(QtCore.QSize(1200, 800))#maximum size
        self.label_1000 = QtGui.QLabel(self)
        self.label_1000.setMinimumSize(QtCore.QSize(85, 20))  #
        self.label_1000.setMaximumSize(QtCore.QSize(85, 20))
        self.label_1000.setFont(self.Bfont)
        self.statusbar.addWidget(self.label_1000)  # statusbar label
        self.label_1000.setText('')
        #
        #self.matplotlibWidget.p.setLabels()
        #
        # initial range of plot
        self.comboBox_4.addItem(_fromUtf8("-1V:+1V"))
        self.comboBox_4.addItem(_fromUtf8("-5V:+5V"))
        self.comboBox_4.addItem(_fromUtf8("-12V:+12V"))
        self.comboBox_4.setCurrentIndex(0)  #
        #
        # txt = u'\u00B1'
        # self.label_8.setText(txt + '1V')
        #
        self.StartThread()  # start thread

    # load available com ports from OS
    def loadPorts(self):
        index = 0
        self.comboBox_3.clear()
        mass = self.ScanPortFromReg()
        nn = len(mass)
        if nn == 0:
            self.comboBox_3.setEnabled(False)
            self.msgBoxError.setText(_fromUtf8("The system doesn't have the serial ports!"))
            self.msgBoxError.setVisible(True)
            return
        for n in range(nn):
            try:
                self.comboBox_3.addItem(str(mass[n]))
            except:
                pass
        self.comboBox_3.setCurrentIndex(index)

    def getTime(self):
        utc = datetime.datetime.utcnow()
        iso = utc.isoformat()  # t = time.time()
        ind = iso.find('.')
        ti = ''
        if ind != -1:
            ti = iso[:ind + 2] + '+10:00'
        else:
            print iso
            ti = iso + '.0+10:00'
        return [utc, ti]

    # the windows registry
    def ScanPortFromReg(self):
        available = []
        try:
            explorer = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "Hardware\\Devicemap\\serialcomm")
        except:
            return available
        i = 0
        while 1:
            try:
                name, value, type = _winreg.EnumValue(explorer, i)
                available.append(value)
                i = i + 1
            except WindowsError:
                break
        _winreg.CloseKey(explorer)
        available.sort()
        return available

    # mouse has left axes
    def mouseLeave(self):
        self.label_31.setText('---')
        self.label_30.setText('---')

    # mouse move signal
    def mouseMove(self, x_pos, y_pos):
        try:
            if x_pos == 0:
                pass
            else:
                self.label_31.setText('<' + self.mass_time[x_pos] + ' , ' + y_pos + ' >')
                self.label_30.setText('<sample ' + str(x_pos) + ' , ' + y_pos + ' >')
        except:
            pass

    # send to UART the type of output
    def initSendtoUART(self):
        out = self.comboBox_2.currentText()
        try:
            self.serial.write(str(out))
        except:
            pass

    # read data from uart
    def connectUart(self):
        if self.pushButton_3.isChecked():
            try:
                self.stop()  # close data from file
                self.serial.port = str(self.comboBox_3.currentText())
                self.serial.baudrate = 19200
                self.serial.bytesize = serial.EIGHTBITS
                self.serial.parity = serial.PARITY_NONE
                self.serial.stopbits = serial.STOPBITS_ONE
                self.serial.timeout = None  # default = 0.2
                self.serial.open()
                #
                self.initSendtoUART()
                #
                self.FLAG = True
                self.mode = 1  # read from UART
                self.log_file = open(time.strftime("%Y%m%d_%H-%M-%S") + '.csv', "wb+")  # always new file
                #
                self.pushButton_3.setText(_fromUtf8("Disconnect"))
                self.label_1000.setText(_fromUtf8(str(self.comboBox_3.currentText())))
                self.pushButton_2.setEnabled(False)  # disable "Start"
                self.pushButton_4.setEnabled(False)  # disable "Stop"
                self.pushButton_5.setEnabled(False)  # disable "Restart"
                self.pushButton.setEnabled(False)  #
                self.comboBox.setEnabled(False)  #
                self.first_time = self.getTime()[1]
                self.time_timer.start(100)  # 100 ms
            except:
                self.stop()
                self.pushButton_3.setChecked(False)  #
                self.serial.close()  #
                self.log_file.close()  # close log
                self.pushButton_3.setText(_fromUtf8("Connect"))
                self.label_1000.setText(_fromUtf8("Disconnected"))
                self.msgBoxError.setText(_fromUtf8("Error!"))
                self.msgBoxError.setVisible(True)
                self.pushButton_2.setEnabled(True)  # enable "Start"
                self.pushButton_4.setEnabled(True)  # enable "Stop"
                self.pushButton_5.setEnabled(True)  # enable "Restart"
                self.pushButton.setEnabled(True)  #
                self.comboBox.setEnabled(True)  #
                self.time_timer.stop()
                return
        else:
            self.stop()
            self.serial.close()
            self.log_file.close()  # close log
            self.FLAG = False
            self.pushButton_3.setText(_fromUtf8("Connect"))
            self.label_1000.setText(_fromUtf8("Disconnected"))
            self.pushButton_2.setEnabled(True)  # enable "Start"
            self.pushButton_4.setEnabled(True)  # enable "Stop"
            self.pushButton_5.setEnabled(True)  # enable "Restart"
            self.pushButton.setEnabled(True)  #
            self.comboBox.setEnabled(True)  #
            self.time_timer.stop()

    # select data file
    def selectFile(self):
        self.dialogTXT.setDirectory(os.getcwd())
        if self.dialogTXT.exec_():
            pp = self.dialogTXT.selectedFiles()
            self.path_file = pp[0]  #
            ff = unicode(pp[0]).encode('CP1251')
            tokens1 = ff.split("/")  #
            p1 = len(tokens1[len(tokens1) - 1]) + 1  #
            l = len(ff) - p1  #
            tt = ff[:l]  #
            tokens = pp[0].split("/")
            p = tokens[len(tokens) - 1]
            self.lineEdit.setText(p)

    # ms
    def selectFrequency(self):
        fr = self.comboBox.currentIndex()
        if fr == 0:
            self.replay_speed = 500
        elif fr == 1:
            self.replay_speed = 1000
        elif fr == 2:
            self.replay_speed = 2000
        elif fr == 3:
            self.replay_speed = 5000
        elif fr == 4:
            self.replay_speed = 10000
        elif fr == 5:
            self.replay_speed = 60000
        elif fr == 6:
            self.replay_speed = 120000
        elif fr == 7:
            self.replay_speed = 300000
        elif fr == 8:
            self.replay_speed = 600000
        else:
            self.replay_speed = 1000

    # select type of output
    def selectOutput(self):
        out = self.comboBox_2.currentIndex()
        self.comboBox_4.clear()
        if out == 0:
            self.label_2.setText('AC Voltage')
            self.label_15.setText('V')
            self.label_8.setText('')
            self.comboBox_4.addItem(_fromUtf8("-1V:+1V"))
            self.comboBox_4.addItem(_fromUtf8("-5V:+5V"))
            self.comboBox_4.addItem(_fromUtf8("-12V:+12V"))
            self.comboBox_4.setCurrentIndex(0)  #
        elif out == 1:
            self.label_2.setText('DC Voltage')
            self.label_15.setText('V')
            self.label_8.setText('')
            self.comboBox_4.addItem(_fromUtf8("-1V:+1V"))
            self.comboBox_4.addItem(_fromUtf8("-5V:+5V"))
            self.comboBox_4.addItem(_fromUtf8("-12V:+12V"))
            self.comboBox_4.setCurrentIndex(0)  #
        elif out == 2:
            self.label_2.setText('AC Current')
            self.label_15.setText('A')
            self.label_8.setText('')
            self.comboBox_4.addItem(_fromUtf8("-200mA:+200mA"))
            self.comboBox_4.addItem(_fromUtf8("-10mA:+10mA"))
            self.comboBox_4.setCurrentIndex(0)  #
        elif out == 3:
            self.label_2.setText('DC Current')
            self.label_15.setText('A')
            self.label_8.setText('')
            self.comboBox_4.addItem(_fromUtf8("-200mA:+200mA"))
            self.comboBox_4.addItem(_fromUtf8("-10mA:+10mA"))
            self.comboBox_4.setCurrentIndex(0)  #
        elif out == 4:
            self.label_2.setText('Resistance')
            self.label_15.setText('Ohm')
            self.label_8.setText('')
            txt = u'\u03A9'
            self.comboBox_4.addItem(_fromUtf8('0 - 1k' + txt))
            self.comboBox_4.addItem(_fromUtf8('0 - 1M' + txt))
            self.comboBox_4.setCurrentIndex(0)  #
        elif out == 5:
            self.label_2.setText('Continuity')
            self.label_15.setText('')
            self.label_8.setText('')
            self.comboBox_4.addItem(_fromUtf8('---'))
            self.comboBox_4.setCurrentIndex(0)  #
        elif out == 6:
            self.label_2.setText('Logic Level')
            self.label_15.setText('')
            self.label_8.setText('')
            self.comboBox_4.addItem(_fromUtf8('---'))
            self.comboBox_4.setCurrentIndex(0)  #
        else:
            pass
        # send to UART message
        self.initSendtoUART()

    # timer
    def checkTimer(self):
        self.FLAG = True

    # time timer
    def checkTimeTimer(self):
        self.label_28.setText(self.first_time + ' / ' + self.getTime()[1])

    # restart
    def restart(self):
        self.msgBox.setText(_fromUtf8('Are you sure you want to restart?'))
        reply = self.msgBox.exec_()
        if reply == 0:
            # restart
            self.stop()
            self.start()
        else:
            pass

    # start (reading dummy data)
    def start(self):
        if self.pushButton_2.text() == _fromUtf8("Start"):
            if self.f_pause:
                self.mode = 0
                self.send_timer.start(self.replay_speed)  # 1000,200,100 ms
                self.FLAG = True
                self.pushButton_2.setText(_fromUtf8("Pause"))
                self.f_pause = False
            else:
                if self.path_file == '':
                    self.msgBoxError.setText(_fromUtf8("You didn't select the data file!"))
                    self.msgBoxError.setVisible(True)
                    return
                else:
                    try:
                        self.f = open(self.path_file, "rb")  #
                        self.log_file = open(time.strftime("%Y%m%d_%H-%M-%S") + '.csv', "wb+")  # open log file
                        self.send_timer.start(self.replay_speed)  # 1000,200,100 ms
                        self.FLAG = True
                        self.pushButton_3.setEnabled(False)  # disable "Connect"
                        #
                        self.pushButton_2.setText(_fromUtf8("Pause"))
                        self.f_pause = False
                        self.mode = 0
                        #
                        self.first_time = self.getTime()[1]
                        self.time_timer.start(100)  # 100 ms
                    except:
                        self.msgBoxError.setText(_fromUtf8("Error opening file!"))
                        self.msgBoxError.setVisible(True)
                        self.pushButton_3.setEnabled(True)
                        self.pushButton_2.setText(_fromUtf8("Start"))
                        self.time_timer.stop()
                        try:
                            self.log_file.close()
                        except:
                            pass
                        return
        else:
            self.pushButton_2.setText(_fromUtf8("Start"))
            self.FLAG = False
            self.f_pause = True
            self.time_timer.stop()
            try:
                self.send_timer.stop()
            except:
                pass

    # stop read file
    def stop(self):
        self.FLAG = False
        try:
            self.send_timer.stop()
        except:
            pass
        #
        self.time_timer.stop()
        #
        self.mass_plot = []  #
        self.mass_ac_voltage = []  #
        self.mass_ac_voltage_x = []  #
        self.mass_dc_voltage = []  #
        self.mass_dc_voltage_x = []  #
        self.mass_ac_current = []  #
        self.mass_ac_current_x = []  #
        self.mass_dc_current = []  #
        self.mass_dc_current_x = []  #
        self.mass_resistance = []  #
        self.mass_resistance_x = []  #
        self.mass_test_continuity = []  #
        self.mass_test_continuity_x = []  #
        self.mass_logic_level = []  #
        self.mass_logic_level_x = []  #
        #
        self.pushButton_3.setEnabled(True)  # enable "Connect"
        self.f_pause = False
        self.pushButton_2.setText(_fromUtf8("Start"))
        self.matplotlibWidget.p.clear()  # clear axes
        #self.matplotlibWidget.canvas.draw()  # clear plot view
        try:
            self.log_file.close()
        except:
            pass

    # def update(self,val):
    #    #print 'hello'
    #    pos = self.matplotlibWidget.spos.val
    #    self.matplotlibWidget.axes.axis([pos-10,pos+10,0,50])
    #    self.matplotlibWidget.canvas.draw()
    #    self.canvas.draw()

    # plotting and set digital,analog
    def viewData(self, num, mode, val):
        #
        # if self.mode == 0:#for read from file - test
        #    pass
        # else:
        line = self.getTime()[1] + ',' + (num) + ',' + str(mode) + ',' + str(val).strip('\r\n') + '\r\n'
        self.log_file.write(line)  # write log file
        #
        self.mass_time.append(self.getTime()[1])
        # digital v,dv,c,dc,r,t,l
        if mode == 'v':
            self.label_2.setText('AC Voltage')
            self.label_15.setText('V')
            self.label_7.setText(str(round(float(val), 2)))  # Voltage
            txt = u'\u00B1'
            if -12 <= float(val) < -5 or 5 < float(val) <= 12:
                self.label_8.setText(txt + '12V')
            elif -5 <= float(val) < -1 or 1 < float(val) <= 5:
                self.label_8.setText(txt + '5V')
            elif -1 <= float(val) <= 1:
                self.label_8.setText(txt + '1V')
            self.mass_ac_voltage_t.append(self.getTime()[0])
            self.mass_ac_voltage.append(float(val))
            self.mass_ac_voltage_x.append(int(num))
            self.mass_dc_voltage_t = []
            self.mass_dc_voltage = []
            self.mass_dc_voltage_x = []
            self.mass_ac_current_t = []
            self.mass_ac_current = []
            self.mass_ac_current_x = []
            self.mass_dc_current_t = []
            self.mass_dc_current = []
            self.mass_dc_current_x = []
            self.mass_resistance_t = []
            self.mass_resistance = []
            self.mass_resistance_x = []
            self.mass_test_continuity_t = []
            self.mass_test_continuity = []  #
            self.mass_test_continuity_x = []  #
            self.mass_logic_level_t = []
            self.mass_logic_level = []  #
            self.mass_logic_level_x = []  #
        elif mode == 'dv':
            self.label_2.setText('DC Voltage')
            self.label_15.setText('V')
            self.label_7.setText(str(round(float(val), 2)))  # Voltage
            txt = u'\u00B1'
            if -12 <= float(val) < -5 or 5 < float(val) <= 12:
                self.label_8.setText(txt + '12V')
            elif -5 <= float(val) < -1 or 1 < float(val) <= 5:
                self.label_8.setText(txt + '5V')
            elif -1 <= float(val) <= 1:
                self.label_8.setText(txt + '1V')
            self.mass_dc_voltage_t.append(self.getTime()[0])
            self.mass_dc_voltage.append(float(val))
            self.mass_dc_voltage_x.append(int(num))
            self.mass_ac_voltage_t = []
            self.mass_ac_voltage = []
            self.mass_ac_voltage_x = []
            self.mass_ac_current_t = []
            self.mass_ac_current = []
            self.mass_ac_current_x = []
            self.mass_dc_current_t = []
            self.mass_dc_current = []
            self.mass_dc_current_x = []
            self.mass_resistance_t = []
            self.mass_resistance = []
            self.mass_resistance_x = []
            self.mass_test_continuity_t = []
            self.mass_test_continuity = []  #
            self.mass_test_continuity_x = []  #
            self.mass_logic_level_t = []
            self.mass_logic_level = []  #
            self.mass_logic_level_x = []  #
        elif mode == 'c':
            self.label_2.setText('AC Current')
            self.label_15.setText('A')
            self.label_7.setText(str(round(float(val), 2)))  # Current
            txt = u'\u00B1'
            if -200 <= float(val) < -10:
                self.label_8.setText(txt + '200mA')
            elif -10 <= float(val) < 10:
                self.label_8.setText(txt + '10mA')
            elif 10 < float(val) <= 200:
                self.label_8.setText(txt + '200mA')
            self.mass_ac_current_t.append(self.getTime()[0])
            self.mass_ac_current.append(float(val))
            self.mass_ac_current_x.append(int(num))
            self.mass_dc_current_t = []
            self.mass_dc_current = []
            self.mass_dc_current_x = []
            self.mass_dc_voltage_t = []
            self.mass_dc_voltage = []
            self.mass_dc_voltage_x = []
            self.mass_ac_voltage_t = []
            self.mass_ac_voltage = []
            self.mass_ac_voltage_x = []
            self.mass_resistance_t = []
            self.mass_resistance = []
            self.mass_resistance_x = []
            self.mass_test_continuity_t = []
            self.mass_test_continuity = []  #
            self.mass_test_continuity_x = []  #
            self.mass_logic_level_t = []
            self.mass_logic_level = []  #
            self.mass_logic_level_x = []  #
        elif mode == 'dc':
            self.label_2.setText('DC Current')
            self.label_15.setText('A')
            self.label_7.setText(str(round(float(val), 2)))  # Current
            txt = u'\u00B1'
            if -200 <= float(val) < -10:
                self.label_8.setText(txt + '200mA')
            elif -10 <= float(val) < 10:
                self.label_8.setText(txt + '10mA')
            elif 10 < float(val) <= 200:
                self.label_8.setText(txt + '200mA')
            self.mass_dc_current_t.append(self.getTime()[0])
            self.mass_dc_current.append(float(val))
            self.mass_dc_current_x.append(int(num))
            self.mass_ac_current_t = []
            self.mass_ac_current = []
            self.mass_ac_current_x = []
            self.mass_ac_voltage_t = []
            self.mass_ac_voltage = []
            self.mass_ac_voltage_x = []
            self.mass_dc_voltage_t = []
            self.mass_dc_voltage = []
            self.mass_dc_voltage_x = []
            self.mass_resistance_t = []
            self.mass_resistance = []
            self.mass_resistance_x = []
            self.mass_test_continuity_t = []
            self.mass_test_continuity = []  #
            self.mass_test_continuity_x = []  #
            self.mass_logic_level_t = []
            self.mass_logic_level = []  #
            self.mass_logic_level_x = []  #
        elif mode == 'r':
            self.label_2.setText('Resistance')
            self.label_15.setText('Ohm')
            self.label_7.setText(str(round(float(val), 2)))  # Resistance
            if 0 <= float(val) <= 1000:
                txt = u'\u03A9'
                self.label_8.setText('0 - 1k' + txt)
            elif 1000 <= float(val) <= 1000000:
                txt = u'\u03A9'
                self.label_8.setText('0 - 1M' + txt)
            #
            self.mass_resistance_t.append(self.getTime()[0])
            self.mass_resistance.append(float(val))
            self.mass_resistance_x.append(int(num))
            self.mass_ac_current_t = []
            self.mass_ac_current = []
            self.mass_ac_current_x = []
            self.mass_dc_current_t = []
            self.mass_dc_current = []
            self.mass_dc_current_x = []
            self.mass_ac_voltage_t = []
            self.mass_ac_voltage = []
            self.mass_ac_voltage_x = []
            self.mass_dc_voltage_t = []
            self.mass_dc_voltage = []
            self.mass_dc_voltage_x = []
            self.mass_test_continuity_t = []
            self.mass_test_continuity = []  #
            self.mass_test_continuity_x = []  #
            self.mass_logic_level_t = []
            self.mass_logic_level = []  #
            self.mass_logic_level_x = []  #
        elif mode == 't':
            self.label_2.setText('Continuity')
            self.label_15.setText('')
            self.label_8.setText('')
            if int(val) == 0:
                self.label_7.setText('LOW')
            elif int(val) == 1:
                self.label_7.setText('HIGH')
            else:
                pass
            self.mass_test_continuity_t.append(self.getTime()[0])
            self.mass_test_continuity.append(float(val))
            self.mass_test_continuity_x.append(int(num))
            self.mass_ac_current_t = []
            self.mass_ac_current = []
            self.mass_ac_current_x = []
            self.mass_dc_current_t = []
            self.mass_dc_current = []
            self.mass_dc_current_x = []
            self.mass_ac_voltage_t = []
            self.mass_ac_voltage = []
            self.mass_ac_voltage_x = []
            self.mass_dc_voltage_t = []
            self.mass_dc_voltage = []
            self.mass_dc_voltage_x = []
            self.mass_resistance_t = []
            self.mass_resistance = []
            self.mass_resistance_x = []
            self.mass_logic_level_t = []
            self.mass_logic_level = []  #
            self.mass_logic_level_x = []  #
        elif mode == 'l':
            self.label_2.setText('Logic Level')
            self.label_15.setText('')
            self.label_8.setText('')
            if int(val) == 0:
                self.label_7.setText('LOW')
            elif int(val) == 1:
                self.label_7.setText('HIGH')
            else:
                pass
            self.mass_logic_level_t.append(self.getTime()[0])
            self.mass_logic_level.append(float(val))
            self.mass_logic_level_x.append(int(num))
            self.mass_ac_current_t = []
            self.mass_ac_current = []
            self.mass_ac_current_x = []
            self.mass_dc_current_t = []
            self.mass_dc_current = []
            self.mass_dc_current_x = []
            self.mass_ac_voltage_t = []
            self.mass_ac_voltage = []
            self.mass_ac_voltage_x = []
            self.mass_dc_voltage_t = []
            self.mass_dc_voltage = []
            self.mass_dc_voltage_x = []
            self.mass_resistance_t = []
            self.mass_resistance = []
            self.mass_resistance_x = []
            self.mass_test_continuity_t = []
            self.mass_test_continuity = []  #
            self.mass_test_continuity_x = []  #
        else:
            pass
        self.matplotlibWidget.p.setLabel('left', None)
        self.matplotlibWidget.p.setLabel('bottom', None)
        # plotting
        if len(self.mass_ac_voltage) != 0:
            curve = self.matplotlibWidget.p.plot(self.mass_ac_voltage_x, self.mass_ac_voltage, pen=COLORS['red'])  # ,label='Voltage,V')
            self.matplotlibWidget.p.setLabel('left', 'V')
            self.matplotlibWidget.p.setLabel('bottom', 'time unit')
            '''range_ = self.comboBox_4.currentIndex()
            if range_ == 0:
                self.matplotlibWidget.p.setLimits(yMin=-1, yMax=1)
            elif range_ == 1:
                self.matplotlibWidget.p.setLimits(yMin=-5, yMax=5)
            elif range_ == 2:
                self.matplotlibWidget.p.setLimits(yMin=-12, yMax=12)
            else:
                pass'''
        elif len(self.mass_dc_voltage) != 0:
            curve = self.matplotlibWidget.p.plot(self.mass_dc_voltage_x, self.mass_dc_voltage, pen=COLORS['red'])  # ,label='Voltage,V')
            self.matplotlibWidget.p.setLabel('left', 'V')
            self.matplotlibWidget.p.setLabel('bottom', 'time unit')
            '''range_ = self.comboBox_4.currentIndex()
            if range_ == 0:
                self.matplotlibWidget.p.setLimits(yMin=-1, yMax=1)
            elif range_ == 1:
                self.matplotlibWidget.p.setLimits(yMin=-5, yMax=5)
            elif range_ == 2:
                self.matplotlibWidget.p.setLimits(yMin=-12, yMax=12)
            else:
                pass'''
        elif len(self.mass_ac_current) != 0:
            curve = self.matplotlibWidget.p.plot(self.mass_ac_current_x, self.mass_ac_current,pen=COLORS['green'])  # ,label='Current,A')
            self.matplotlibWidget.p.setLabel('left', 'A')
            self.matplotlibWidget.p.setLabel('bottom', 'time unit')
            '''range_ = self.comboBox_4.currentIndex()
            if range_ == 0:
                self.matplotlibWidget.p.setLimits(yMin=-200, yMax=200)
            elif range_ == 1:
                self.matplotlibWidget.p.setLimits(yMin=-10, yMax=10)
            else:
                pass'''
        elif len(self.mass_dc_current) != 0:
            curve = self.matplotlibWidget.p.plot(self.mass_dc_current_x, self.mass_dc_current,pen=COLORS['green'])  # ,label='Current,A')
            self.matplotlibWidget.p.setLabel('left', 'A')
            self.matplotlibWidget.p.setLabel('bottom', 'time unit')
            '''range_ = self.comboBox_4.currentIndex()
            if range_ == 0:
                self.matplotlibWidget.p.setLimits(yMin=-200, yMax=200)
            elif range_ == 1:
                self.matplotlibWidget.p.setLimits(yMin=-10, yMax=10)
            else:
                pass'''
        elif len(self.mass_resistance) != 0:
            curve = self.matplotlibWidget.p.plot(self.mass_resistance_x, self.mass_resistance,pen=COLORS['blue'])  # ,label='Resistance, Om')
            self.matplotlibWidget.p.setLabel('left', 'Ohm')
            self.matplotlibWidget.p.setLabel('bottom', 'time unit')
            '''range_ = self.comboBox_4.currentIndex()
            if range_ == 0:
                self.matplotlibWidget.p.setLimits(yMin=0, yMax=1000)
            elif range_ == 1:
                self.matplotlibWidget.p.setLimits(yMin=0, yMax=1000000)
            else:
                pass'''
        elif len(self.mass_test_continuity) != 0:
            curve = self.matplotlibWidget.p.plot(self.mass_test_continuity_x, self.mass_test_continuity,pen=COLORS['cyan'])  # ,label='Resistance, Om')
            self.matplotlibWidget.p.setLabel('left', 'TEST')
            self.matplotlibWidget.p.setLabel('bottom', 'time unit')
        elif len(self.mass_logic_level) != 0:
            curve = self.matplotlibWidget.p.plot(self.mass_logic_level_x, self.mass_logic_level,pen=COLORS['yellow'])  # ,label='Resistance, Om')
            self.matplotlibWidget.p.setLabel('left', 'HIGH, LOW')
            self.matplotlibWidget.p.setLabel('bottom', 'time unit')
        else:
            pass


    # start thread
    def StartThread(self):
        self.thread = threading.Thread(target=self.fileReadTread)
        self.alive.set()
        self.thread.start()

    # stop thread
    def StopThread(self):
        if self.thread is not None:
            self.alive.clear()  # clear alive event for thread
            self.thread = None

    # file read thread
    def fileReadTread(self):
        while self.alive.isSet():
            if self.FLAG:
                # read file
                if self.mode == 0:
                    text = self.f.readline()  # read before \r\n
                    if text:
                        text = text.replace('\x00', '')
                        tokens = text.split(',')
                        if len(tokens) == 3:
                            number = tokens[0]  # number sample
                            typ = tokens[1]  # mode
                            value = tokens[2]  # value
                            self.emit(QtCore.SIGNAL('OutputData(QString,QString,QString)'), str(number), str(typ),
                                      str(value))  # signal for update
                            self.FLAG = False  # reset flag
                    else:
                        self.stop()
                # read serial port
                else:
                    text = self.serial.readline()  # port
                    if text:
                        text = text.replace('\x00', '')
                        tokens = text.split(',')
                        if len(tokens) == 3:
                            number = tokens[0]  # number sample
                            typ = tokens[1]  # mode
                            value = tokens[2]  # value
                            self.emit(QtCore.SIGNAL('OutputData(QString,QString,QString)'), str(number), str(typ),
                                      str(value))  # signal for update
                    else:
                        pass
            time.sleep(0.05)  # timeout 50ms

    # close event
    def closeEvent(self, event):
        self.FLAG = False
        if self.thread is not None:
            self.alive.clear()  # clear alive event for thread
            self.thread = None
        try:
            self.f.close()  # data file
            self.log_file.close()  # log file
            self.serial.close()  #
        except:
            pass


# launch
app = QtGui.QApplication(sys.argv)
form = MWindow()
form.show()
app.exec_()
