"""
***************************************************************************
   OSFWF_RunSWAT.py
-------------------------------------
    Copyright (C) 2014 TIGER-NET (www.tiger-net.org)

***************************************************************************
* This plugin is part of the Water Observation Information System (WOIS)  *
* developed under the TIGER-NET project funded by the European Space      *
* Agency as part of the long-term TIGER initiative aiming at promoting    *
* the use of Earth Observation (EO) for improved Integrated Water         *
* Resources Management (IWRM) in Africa.                                  *
*                                                                         *
* WOIS is a free software i.e. you can redistribute it and/or modify      *
* it under the terms of the GNU General Public License as published       *
* by the Free Software Foundation, either version 3 of the License,       *
* or (at your option) any later version.                                  *
*                                                                         *
* WOIS is distributed in the hope that it will be useful, but WITHOUT ANY * 
* WARRANTY; without even the implied warranty of MERCHANTABILITY or       *
* FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License   *
* for more details.                                                       *
*                                                                         *
* You should have received a copy of the GNU General Public License along *
* with this program.  If not, see <http://www.gnu.org/licenses/>.         *
***************************************************************************
"""

import os
from datetime import date, timedelta, datetime
import numpy
import subprocess
from PyQt4 import QtGui
from processing.core.parameters import *
from SWATAlgorithm import SWATAlgorithm
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from ClimateStationsSWAT import ClimateStationsSWAT
from ModelFile import ModelFile

class OSFWF_RunSWAT(SWATAlgorithm):

    MODEL_FILE = "MODEL_FILE"
    IO_FOLDER = "IO_FOLDER"
    SWAT_EXE = "SWAT_EXE"

    def __init__(self):
        super(OSFWF_RunSWAT, self).__init__(__file__)

    def defineCharacteristics(self):
        self.name = "3 - Run SWAT model (OSFWF)"
        self.group = "Operational simulation and forecasting workflow (OSFWF)"
        self.addParameter(ParameterFile(OSFWF_RunSWAT.MODEL_FILE, "Model description file", False, False))
        self.addParameter(ParameterFile(OSFWF_RunSWAT.IO_FOLDER, "Model input/output folder", True))
        self.addParameter(ParameterFile(OSFWF_RunSWAT.SWAT_EXE, "SWAT executable", False, False))

    def processAlgorithm(self, progress):
        MODEL_FILE = self.getParameterValue(OSFWF_RunSWAT.MODEL_FILE)
        model = ModelFile(MODEL_FILE)
        CSTATIONS_FILE = model.Path + os.sep + model.desc['Stations']
        IO_FOLDER = self.getParameterValue(OSFWF_RunSWAT.IO_FOLDER)
        SWAT_EXE = self.getParameterValue(OSFWF_RunSWAT.SWAT_EXE)

        # Updating climate files
        CSTATIONS = ClimateStationsSWAT(CSTATIONS_FILE)
        log_file = open(IO_FOLDER + os.sep + "cstations_log.txt", "w")
        last_pcp_date,last_tmp_date = CSTATIONS.writeSWATrunClimateFiles(IO_FOLDER,log_file)
        log_file.close()

        # Updating cio file
        last_date = min(last_pcp_date,last_tmp_date)
        if os.path.isfile(IO_FOLDER + os.sep + "file.cio"):
            cio_file = open(IO_FOLDER + os.sep + "file.cio", "r")
            cio=cio_file.readlines()
            cio_file.close()
            startyear = int(cio[8][0:16])
            nbyears = last_date.year - startyear + 1
            endjulianday = (last_date-date(last_date.year,1,1)).days + 1
            nbyearline = str(nbyears).rjust(16) + cio[7][16:len(cio[7])]
            endjdayline = str(endjulianday).rjust(16) + cio[10][16:len(cio[10])]
            cio[7]=nbyearline
            cio[10]=endjdayline
            cio_file = open(IO_FOLDER + os.sep + "file.cio", "w")
            cio_file.writelines(cio)
            cio_file.close()
        else:
            raise GeoAlgorithmExecutionException('cio-file ' + IO_FOLDER + os.sep + "file.cio" + ' does not exist')

        # Running SWAT
        currpath = os.getcwd()
        os.chdir(IO_FOLDER)
        runres = subprocess.call(SWAT_EXE)
        os.chdir(currpath)
        if runres != 0:
            raise GeoAlgorithmExecutionException('SWAT run unsuccessful')

