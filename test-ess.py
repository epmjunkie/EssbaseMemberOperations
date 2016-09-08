from essbase import Essbase
from essbase import Outline
from essbase import Member
from essbase import Operation
from essbase import DataStorage
import settings

conn = Essbase(username=settings.username, password=settings.password, server=settings.server,
               application=settings.application, database=settings.database)
otl = Outline(essbase=conn)
conn.open()
otl.open()
otl.xmlexport("outline-export1.xml", dimensions=["Measure", "Organization"])
# member = Member(name='ROCE Measures', outline=otl).delete(Operation.Shared)
# member = Member(name='CROCE Measures', outline=otl)
# member.storage = DataStorage.Stored
# print(member.storage)
# print(member.name)
# otl.save()
otl.close()
conn.close()


def appendCount(file, start=0):
    f = open(file, "r+")
    lines = f.readlines()
    f.seek(0)
    i = start
    for line in lines:
        i += 1
        f.write(line.replace('\n', '') + '|' + str(i) + '\n')
    f.close()
    return i
