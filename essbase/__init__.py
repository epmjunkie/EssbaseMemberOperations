import sys
from enum import Enum

sys.path.append('lib/ess_es_server.jar')
sys.path.append('lib/ess_japi.jar')
sys.path.append('lib/ojdl.jar')
from com.essbase.api.session import IEssbase
from com.essbase.api.datasource import IEssCube
from com.essbase.api.datasource import EssOtlExportOptions
from com.essbase.api.metadata.IEssMember import EEssShareOption


class Essbase(object):
    def __init__(self, username=None, password=None, provider='Embedded', server=None, version="11.1.2.4",
                 application=None,
                 database=None):
        self.username = username
        self.password = password
        self.provider = provider
        self.server = server
        self.version = version
        self.application = application
        self.database = database
        self.essbaselogin = None
        self.connection = None

    def open(self, username=None, password=None, provider=None, server=None):
        if username:
            self.username = username
        if password:
            self.password = password
        if provider:
            self.provider = provider
        if server:
            self.server = server

        if not self.username and self.password:
            raise "Username or password missing."
        if not self.provider:
            raise "Provider is required"
        if not self.server:
            raise "Server is required"

        self.essbaselogin = IEssbase.Home.create(self.version)
        self.connection = self.essbaselogin.signOn(self.username, self.password, False, None, self.provider,
                                                   self.server)

    def close(self):
        try:
            self.connection.clearActive()
            self.connection.disconnect()
            self.essbaselogin.signOff()
        except Exception as e:
            print("Unexpected exception: " + e.message)

    def getApp(self, application=None):
        if application:
            self.application = application
        return self.connection.getApplication(self.application)

    def setActive(self, application=None, database=None):
        if application:
            self.application = application
        if database:
            self.database = database
        self.connection.setActive(self.application, self.database)

    def connected(self):
        if self.connection and self.connection.connected:
            return True
        return False

    def signedon(self):
        if self.essbaselogin and self.essbaselogin.signedOn:
            return True
        return False


class Outline(object):
    def __init__(self, essbase, application=None, database=None):
        self.application = application
        self.database = database
        self.connection = essbase
        if not application and essbase.application:
            self.application = essbase.application
        if not database and essbase.database:
            self.database = essbase.database
        self.otl = None
        self.haschanges = False

    def open(self, application=None, database=None):
        if application:
            self.application = application
        if database:
            self.database = database
        app = self.connection.getApp(self.application)
        cube = app.getCube(self.database)
        self.connection.setActive(self.application, self.database)
        self.otl = cube.openOutline(False, True, True)

    def close(self, save=False):
        if save:
            self.save()
        self.otl.close()

    def save(self, verify=False):
        if self.haschanges and verify:
            self.otl.verify(True)
        self.otl.save()
        self.otl.restructureCube(IEssCube.EEssRestructureOption.KEEP_ALL_DATA)

    def xmlexport(self, filepath, dimensions=[], application=None, database=None):
        if application:
            self.application = application
        if database:
            self.database = database
        options = EssOtlExportOptions()
        if len(dimensions) > 0:
            options.setDimList(dimensions)
            options.setOutputFlag(1)
        else:
            options.setOutputFlag(0)
        app = self.connection.getApp(self.application)
        cube = app.getCube(self.database)
        cube.exportOutline(options, filepath)


class Member(object):
    def __init__(self, outline, name=None, member=None):
        self.outline = outline
        if member:
            self.member = member
            self.name = member.toString()
        else:
            self.name = str(name)
            self.member = self.outline.otl.findMember(self.name)

    def delete(self, operation):
        if operation == Operation.Member:
            if self.count > 0:
                return False, "Member: %(member)s is not level zero, please choose an appropriate action." % {
                    'member': self.name}
            else:
                self.member.delete()
            self.outline.haschanges = True
            return True, "Member: %(member)s has been deleted." % {'member': self.name}
        elif operation == Operation.Descendants:
            if self.count == 0:
                return False, "Member: %(member)s is level zero, please choose an appropriate action." % {
                    'member': self.name}
            for child in self.children:
                child.delete(Operation.IDescendants)
            self.outline.haschanges = True
            return True, "Children of member: %(member)s have been deleted." % {'member': self.name}
        elif operation == Operation.IDescendants:
            for child in self.children:
                child.delete(operation)
            self.member.delete()
            self.outline.haschanges = True
            return True, "Member: %(member)s and its children have been deleted." % {'member': self.name}
        elif operation == Operation.Level0:
            if self.isLevel0:
                self.member.delete()
                return True, "Member: %(member)s is level 0 and has been deleted." % {'member': self.name}
            else:
                for child in self.children:
                    child.delete(operation)
            self.outline.haschanges = True
            return True, "Level 0 children of the member: %(member)s have been deleted." % {'member': self.name}
        elif operation == Operation.Shared:
            if self.count == 0:
                return False, "Member: %(member)s has no shared children;" % {'member': self.name}
            else:
                for child in self.children:
                    if child.isShared:
                        child.delete(Operation.Member)
                    else:
                        child.delete(operation)
            self.outline.haschanges = True
            return True, "Shared children the member: %(member)s have been deleted." % {'member': self.name}
        return False, "Member: %(member)s Unknown Operation." % {'member': self.name}

    def rename(self, name):
        self.member.rename(name)
        self.name = name
        self.outline.haschanges = True

    @property
    def storage(self):
        if self.member.shareOption == EEssShareOption.STORE_DATA:
            return 'Store Data'
        elif self.member.shareOption == EEssShareOption.NEVER_SHARE:
            return 'Never Share'
        elif self.member.shareOption == EEssShareOption.LABEL_ONLY:
            return 'Label Only'
        elif self.member.shareOption == EEssShareOption.SHARED_MEMBER:
            return 'Shared Member'
        elif self.member.shareOption == EEssShareOption.DYNAMIC_CALC_AND_STORE:
            return 'Dynamic Calc and Store'
        elif self.member.shareOption == EEssShareOption.DYNAMIC_CALC:
            return 'Dynamic Calc'

    @storage.setter
    def storage(self, value):
        if isinstance(value, DataStorage):
            if value == DataStorage.Stored:
                self.member.shareOption = EEssShareOption.STORE_DATA
            elif value == DataStorage.NeverShare:
                self.member.shareOption = EEssShareOption.NEVER_SHARE
            elif value == DataStorage.LabelOnly:
                self.member.shareOption = EEssShareOption.LABEL_ONLY
            elif value == DataStorage.SharedMember:
                self.member.shareOption = EEssShareOption.SHARED_MEMBER
            elif value == DataStorage.DynamicCalcAndStore:
                self.member.shareOption = EEssShareOption.DYNAMIC_CALC_AND_STORE
            elif value == DataStorage.DynamicCalc:
                self.member.shareOption = EEssShareOption.DYNAMIC_CALC
        else:
            if value.lower() == 'store data':
                self.member.shareOption = EEssShareOption.STORE_DATA
            elif value.lower() == 'never share':
                self.member.shareOption = EEssShareOption.NEVER_SHARE
            elif value.lower() == 'label only':
                self.member.shareOption = EEssShareOption.LABEL_ONLY
            elif value.lower() == 'shared member':
                self.member.shareOption = EEssShareOption.SHARED_MEMBER
            elif value.lower() == 'dynamic calc and store':
                self.member.shareOption = EEssShareOption.DYNAMIC_CALC_AND_STORE
            elif value.lower() == 'dynamic calc':
                self.member.shareOption = EEssShareOption.DYNAMIC_CALC
        self.outline.haschanges = True

    @property
    def count(self):
        return self.member.getChildMembers().getCount()

    @property
    def isLevel0(self):
        return self.member.getLevelNumber() == 0

    @property
    def isShared(self):
        return self.member.shareOption == EEssShareOption.SHARED_MEMBER

    @property
    def children(self):
        child = []
        children = self.member.getChildMembers()
        for i in range(0, children.getCount()):
            child.append(Member(member=children.getAt(i), outline=self.outline))
        return child

    def __str__(self):
        return self.name


class Operation(Enum):
    Member = 1
    Descendants = 2
    IDescendants = 3
    Shared = 4
    Level0 = 0


class DataStorage(Enum):
    Stored = 0  # EEssShareOption.STORE_DATA
    NeverShare = 1  # EEssShareOption.NEVER_SHARE
    LabelOnly = 2  # EEssShareOption.LABEL_ONLY
    SharedMember = 3  # EEssShareOption.SHARED_MEMBER
    DynamicCalcAndStore = 4  # EEssShareOption.DYNAMIC_CALC_AND_STORE
    DynamicCalc = 5  # EEssShareOption.DYNAMIC_CALC


class item(object):
    def __init__(self, parent, child, uda):
        self.parent = parent
        self.child = child
        self.uda = uda
