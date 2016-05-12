from calculationmanager import calculationManager
import settings

cm = calculationManager(server=settings.pserver, username=settings.username, password=settings.password,
                        database=settings.pdatabase, application=settings.papplication)
cm.connect()

cm.disconnect()
