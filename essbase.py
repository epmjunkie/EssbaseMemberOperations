import sys

sys.path.append('lib/ess_es_server.jar')
sys.path.append('lib/ess_japi.jar')
sys.path.append('lib/ojdl.jar')
from com.essbase.api.session import IEssbase
from com.essbase.api.datasource import IEssCube


class essbase(object):
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

    def test(self):
        conn = essbase(username='automation', password='Hyperion1', server='brtuxhypap03d.phillips66.net')
        conn.open()
        if conn.connected():
            print("Connected to Essbase")
        else:
            print("Failed to connect to Essbase")
        conn.close()


class outline(object):

    class Operation(object):
        Member = 1
        Descendants = 2
        IDescendants = 3
        Shared = 4
        Level0 = 0

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

    def delete(self, member, operation=None):
        member = Member(member, self.otl)
        if operation == self.Operation.Member:
            if member.count > 0:
                return False, "Member: %(member)s is not level zero, please choose an appropriate action." % {'member': member}
            member.delete()
            return True, "Member: %(member)s has been deleted." % {'member': member}
        elif operation == self.Operation.Descendants:
            if member.count == 0:
                return False, "Member: %(member)s is level zero, please choose an appropriate action." % {'member': member}
            for child in member.children:
                child.delete()
            return True, "Children of member: %(member)s have been deleted." % {'member': member}
        elif operation == self.Operation.IDescendants:
            if member.count > 0:
                for child in member.children:
                    child.delete()
            member.delete()
            return True, "Member: %(member)s and its children have been deleted." % {'member': member}
        elif operation == self.Operation.Level0:
            if member.count == 0:
                member.delete()
                return True, "Member: %(member)s is level 0 and has been deleted." % {'member': member}
            else:
                for child in member.children:
                    if child.isLevel0:
                        child.delete()
                    else:
                        self.delete(child, operation)
                return True, "Level 0 children of the member: %(member)s have been deleted." % {'member': member}
        elif operation == self.Operation.Shared:
            if member.count == 0:
                return False, "Member has no shared children;"
            else:
                for child in member.children:
                    if child.isShared:
                        child.delete()
                    else:
                        self.delete(child, operation)
        return False, "Unknown operation"


class Member(object):
    def __init__(self, name, outline):
        self.name = str(name)
        self.outline = outline
        self.member = outline.findMember(self.name)

    def delete(self):
        self.member.delete()

    @property
    def count(self):
        return self.member.getChildMembers().getCount()

    @property
    def isLevel0(self):
        return self.member.getLevelNumber() == 0

    @property
    def isShared(self):
        return self.member.getSharedOption().lower() == 'shared member'

    @property
    def children(self):
        child = []
        children = self.member.getChildMembers()
        for i in range(0, children.getCount()):
            child.append(Member(name=children.getAt(i).toString(), outline=self.outline))
        return child

    def __str__(self):
        return self.name

