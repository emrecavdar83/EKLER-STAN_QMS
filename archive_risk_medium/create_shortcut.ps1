$TargetFile = "c:\Projeler\S_program\EKLERİSTAN_QMS\baslat.bat"
$ShortcutFile = "$([Environment]::GetFolderPath('Desktop'))\EKLERISTAN QMS.lnk"
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutFile)
$Shortcut.TargetPath = $TargetFile
$Shortcut.WorkingDirectory = "c:\Projeler\S_program\EKLERİSTAN_QMS"
$Shortcut.Description = "Ekleristan Kalite Yönetim Sistemi Başlat"
$Shortcut.IconLocation = "c:\Projeler\S_program\EKLERİSTAN_QMS\baslat.bat,0" 
$Shortcut.Save()
Write-Host "Kısayol başarıyla oluşturuldu: $ShortcutFile"
