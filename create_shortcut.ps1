$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\QMS_LEGACY_BASLAT.lnk")
$Shortcut.TargetPath = "C:\Projeler\S_program\EKLERİSTAN_QMS\baslat.bat"
$Shortcut.WorkingDirectory = "C:\Projeler\S_program\EKLERİSTAN_QMS"
$Shortcut.Description = "Legacy QMS Projesi"
$Shortcut.Save()
Write-Host "Yeni kisayol olusturuldu: QMS_LEGACY_BASLAT.lnk"
