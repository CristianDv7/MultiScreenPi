' Lanza el agente de escritorio en segundo plano, sin ventana de consola.
' Se copia una copia de este archivo a la carpeta de Inicio de Windows
' para que arranque solo al encender el PC (ver README de este folder).

Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "C:\Python314\pythonw.exe ""D:\DesarrolloCristian\PantallaRaspberryPI\MultiScreenPi\desktop-agent\agent.py""", 0, False
