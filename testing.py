from essbase import Essbase
from essbase import Outline
from essbase import Member
from essbase import Operation
import settings

conn = Essbase(username=settings.username, password=settings.password, server=settings.server)
otl = Outline(essbase=conn, application=settings.application, database=settings.database)
conn.open()
otl.open()
# member = Member(name='ROCE Measures', outline=otl).delete(Operation.Shared)
member = Member(name='CROCE Measures', outline=otl)
member.rename("CROCE Measures1")
print(member.name)
otl.save()
otl.close()
conn.close()