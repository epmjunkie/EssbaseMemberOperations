import sys
from enum import Enum

sys.path.append('lib/ess_es_server.jar')
sys.path.append('lib/ess_japi.jar')
sys.path.append('lib/ojdl.jar')
from com.essbase.api.session import IEssbase
from com.essbase.api.datasource import IEssCube


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

    def __init__(self, essbase, application, database):
        self.connection = essbase
        self.application = application
        self.database = database
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

    def save(self):
        if self.haschanges:
            self.otl.verify(True)
        self.otl.save()
        self.otl.restructureCube(IEssCube.EEssRestructureOption.KEEP_ALL_DATA)


class Member(object):
    def __init__(self, outline, name=None, member=None):
        self.outline = outline
        if member:
            self.member = member
            self.name = member.toString()
        else:
            self.name = str(name)
            self.member = self.outline.otl.findMember(self.name)

    def delete1(self):
        self.member.delete()

    def delete(self, operation):
        if operation == Operation.Member:
            if self.count > 0:
                return False, "Member: %(member)s is not level zero, please choose an appropriate action." % {
                    'member': self.name}
            else:
                self.member.delete()
            return True, "Member: %(member)s has been deleted." % {'member': self.name}
        elif operation == Operation.Descendants:
            if self.count == 0:
                return False, "Member: %(member)s is level zero, please choose an appropriate action." % {
                    'member': self.name}
            for child in self.children:
                child.delete(Operation.IDescendants)
            return True, "Children of member: %(member)s have been deleted." % {'member': self.name}
        elif operation == Operation.IDescendants:
            for child in self.children:
                child.delete(operation)
            self.member.delete()
            return True, "Member: %(member)s and its children have been deleted." % {'member': self.name}
        elif operation == Operation.Level0:
            if self.isLevel0:
                self.member.delete()
                return True, "Member: %(member)s is level 0 and has been deleted." % {'member': self.name}
            else:
                for child in self.children:
                    child.delete(operation)
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
            return True, "Shared children the member: %(member)s have been deleted." % {'member': self.name}
        return False, "Member: %(member)s Unknown Operation." % {'member': self.name}

    def rename(self, name):
        self.member.rename(name)
        self.name = name

    @property
    def count(self):
        return self.member.getChildMembers().getCount()

    @property
    def isLevel0(self):
        return self.member.getLevelNumber() == 0

    @property
    def isShared(self):
        return self.member.shareOption.toString() == "Shared member"

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
