# Inspect the RawInput.Touchpad.dll to see what properties TouchpadContact has

Add-Type -Path "RawInput.Touchpad.dll"

$type = [RawInput.Touchpad.TouchpadContact]

Write-Host "TouchpadContact Properties:"
$type.GetProperties() | ForEach-Object {
    Write-Host "  - $($_.Name): $($_.PropertyType.Name)"
}

Write-Host ""
Write-Host "TouchpadContact Fields:"
$type.GetFields() | ForEach-Object {
    Write-Host "  - $($_.Name): $($_.FieldType.Name)"
}
