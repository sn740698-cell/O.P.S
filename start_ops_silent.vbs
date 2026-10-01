Set WshShell = CreateObject("WScript.Shell")
' Run start_ops.bat in hidden mode (Window style 0, false for async execution)
WshShell.Run "cmd /c start_ops.bat /background", 0, False
