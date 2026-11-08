param([string]$Name)
if ($null -eq $Name) { $Name = 'Game' }
[IO.Path]::GetFullPath($Name)
