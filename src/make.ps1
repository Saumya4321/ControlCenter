# Define paths
$desktopPath = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktopPath "RunMyPythonScript.lnk"
$targetScript = "C:\Users\SLS Machine\Documents\GitHub\ControlCenter\ControlCenter\src\script.ps1"

# Create a WScript.Shell COM object
$wShell = New-Object -ComObject WScript.Shell
$shortcut = $wShell.CreateShortcut($shortcutPath)

# Set shortcut properties
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$targetScript`""
$shortcut.WorkingDirectory = Split-Path $targetScript
$shortcut.WindowStyle = 1 # 1 = Normal, 7 = Minimized
$shortcut.IconLocation = "powershell.exe,0" # optional icon
$shortcut.Save()
