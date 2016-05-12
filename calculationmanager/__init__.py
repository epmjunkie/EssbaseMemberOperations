import sys
import os

os.environ["EPM_ORACLE_INSTANCE"] = 'C:\Users\kiktak\PycharmProjects\EssbaseMemberOperations\planning\config\fake'

sys.path.append('lib/HspJS.jar')
sys.path.append('lib/css.jar')
sys.path.append('lib/ojdl.jar')
sys.path.append('lib/javax.servlet_1.0.0.0_2-5.jar')
sys.path.append('lib/hbrhppluginjar.jar')
sys.path.append('lib/calcmgrcommon.jar')
sys.path.append('lib/ess_japi.jar')
sys.path.append('lib/json.jar')
sys.path.append('lib/registry-api.jar')
sys.path.append('lib/com.bea.core.apache.commons.lang_2.1.0.jar')
sys.path.append('lib/dms.jar')

sys.path.append('lib/epm_planning_server.jar')
# from com.hyperion.planning.calcmgr.cmdlnlauncher import HspCalcMgrCmdLineLauncher
from com.hyperion.planning import HyperionPlanningBean
from com.hyperion.planning.calcmgr import HspCalcMgr, HspCalcMgrKey, HspCalcMgrServer
from java.util import Locale


class calculationManager(object):
    def __init__(self, server=None, username=None, password=None, application=None, database=None,
                 locale=Locale.ENGLISH):
        self.server = server
        self.username = username
        self.password = password
        self.application = application
        self.database = database
        self.connection = None
        self.planning = None
        self.calcmgr = None
        self.calcmgrkey = None
        self.locale = locale

    def connect(self):
        self.planning = HyperionPlanningBean()
        self.planning.Login(self.server,
                            self.username,
                            self.password,
                            self.application)
        self.calcmgrkey = HspCalcMgrKey()
        self.calcmgrkey.setLocation(self.planning.getCurrentCluster(),
                                    self.application,
                                    self.database)
        self.calcmgrkey.setPlanningUser(self.username,
                                        self.planning.getUserSid(self.username),
                                        self.planning.getUserID(),
                                        self.planning.GetSSOToken(),
                                        self.planning.getSessionId())
        self.calcmgr = HspCalcMgr(self.locale)
        HspCalcMgrServer()

    def disconnect(self):
        if self.calcmgr:
            self.calcmgr.releaseConnections(self.planning.getSessionId())
        if self.planning:
            self.planning.LogOff()

    def launchRule(self, rule, rtp=None):
        params = self.calcmgr.getRTPs(self.calcmgrkey, rule)
        job = self.calcmgr.getRule(self.calcmgrkey, rule)

        cube = self.planning.getCube(job.getLocationSubType())
        if not cube:
            raise "Invalid plan type: " + job.getLocationSubType()
