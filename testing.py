from essbase import essbase
from essbase import outline

conn = essbase(username="admin", password="password", server="essbase.server.net")
otl = outline(essbase=conn, application="Sample", database="Basic")
conn.open()
otl.open()
status, message = otl.delete(member='TAXRATE', operation=otl.Operation.Level0)
print(status)
print(message)
otl.save()
otl.close()
conn.close()