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
# member = Member(name='ROCE Measures', outline=otl).delete(Operation.Shared)
member = Member(name='CROCE Measures1', outline=otl)
member.storage = DataStorage.Stored
print(member.storage)
print(member.name)
otl.save()
otl.close()
conn.close()