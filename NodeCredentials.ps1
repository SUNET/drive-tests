<# .SYNOPSIS
    PowerShell script using dpapi to locally store credentials for Sunet Drive.
.DESCRIPTION
    Saves/Retrieves node-specific credentials for Sunet Drive, differentiating between production and test.
    Saves the entered credentials in pswd/<node>.drive.<target>.sunet.se using Export-Clixml, saving the password as SecureString
.NOTES
     Author     : Richard Freitag- freitag@sunet.se
#>
function Save-OcsCredentials([string]$node, [string]$env)
{
    $cred = Get-Credential
    if ($env -eq 'test'){
        $target = '.test'
    } else {
        $target = ''
    }

    if ($node -eq "gss"){
        $file = 'pswd\ocs_gss.drive' + $target + '.sunet.se.xml'
    } else {
        $file = 'pswd\ocs_' + $node + '.drive' + $target + '.sunet.se.xml'
    }
    $cred | Export-Clixml -Path $file
}

function Save-SeleniumCredentials([string]$node, [string]$env)
{
    $cred = Get-Credential
    if ($env -eq 'test'){
        $target = '.test'
    } else {
        $target = ''
    }

    if ($node -eq "gss"){
        $file = 'pswd\selenium_gss.drive' + $target + '.sunet.se.xml'
    } else {
        $file = 'pswd\selenium_' + $node + '.drive' + $target + '.sunet.se.xml'
    }
    $cred | Export-Clixml -Path $file
}

function Save-OcsAppCredentials([string]$node, [string]$env)
{
    $cred = Get-Credential
    if ($env -eq 'test'){
        $target = '.test'
    } else {
        $target = ''
    }

    if ($node -eq "gss"){
        $file = 'pswd\ocs_gss.drive' + $target + '.sunet.se.app.xml'
    } else {
        $file = 'pswd\ocs_' + $node + '.drive' + $target + '.sunet.se.app.xml'
    }
    $cred | Export-Clixml -Path $file
}

function Save-SeleniumAppCredentials([string]$node, [string]$env)
{
    $cred = Get-Credential
    if ($env -eq 'test'){
        $target = '.test'
    } else {
        $target = ''
    }

    if ($node -eq "gss"){
        $file = 'pswd\selenium_gss.drive' + $target + '.sunet.se.app.xml'
    } else {
        $file = 'pswd\selenium_' + $node + '.drive' + $target + '.sunet.se.app.xml'
    }
    $cred | Export-Clixml -Path $file
}

function Save-UserAppCredentials([string]$userid, [string]$node, [string]$env)
{
    $cred = Get-Credential
    if ($env -eq 'test'){
        $target = '.test'
    } else {
        $target = ''
    }

    if ($node -eq "gss"){
        $file = 'pswd\user_gss.drive' + $target + '.sunet.se.app.xml'
        Write-Host "GSS"
    } else {
        $file = 'pswd\' + $userid + '_' + $node + '.drive' + $target + '.sunet.se.app.xml'
        Write-Host "Node: " $node
        Write-Host "Target: " $target
    }
    Write-Host $file
    $cred | Export-Clixml -Path $file
}

function Get-OcsUser([string]$node, [string]$env)
{
    if ($env -eq 'test'){
        $target = '.test'
    } else {
        $target = ''
    }

    if ($node -eq "gss"){
        $file = 'pswd\ocs_gss.drive' + $target + '.sunet.se.xml'
    } else {
        $file = 'pswd\ocs_' + $node + '.drive' + $target + '.sunet.se.xml'
    }

    $cred = Import-Clixml -Path $file
    Write-Host -NoNewline $cred.UserName    
}

function Get-SeleniumUser([string]$node, [string]$env)
{
    if ($env -eq 'test'){
        $target = '.test'
    } else {
        $target = ''
    }

    if ($node -eq "gss"){
        $file = 'pswd\selenium_gss.drive' + $target + '.sunet.se.xml'
    } else {
        $file = 'pswd\selenium_' + $node + '.drive' + $target + '.sunet.se.xml'
    }

    $cred = Import-Clixml -Path $file
    Write-Host -NoNewline $cred.UserName    
}

function Get-OcsPassword([string]$node, [string]$env)
{
    if ($env -eq 'test'){
        $target = '.test'
    } else {
        $target = ''
    }

    if ($node -eq "gss"){
        $file = 'pswd\ocs_gss.drive' + $target + '.sunet.se.xml'
    } else {
        $file = 'pswd\ocs_' + $node + '.drive' + $target + '.sunet.se.xml'
    }
    $cred = Import-Clixml -Path $file
    $pwd = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($cred.Password))
    Write-Host -NoNewline $pwd
}

function Get-SeleniumPassword([string]$node, [string]$env)
{
    if ($env -eq 'test'){
        $target = '.test'
    } else {
        $target = ''
    }

    if ($node -eq "gss"){
        $file = 'pswd\selenium_gss.drive' + $target + '.sunet.se.xml'
    } else {
        $file = 'pswd\selenium_' + $node + '.drive' + $target + '.sunet.se.xml'
    }
    $cred = Import-Clixml -Path $file
    $pwd = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($cred.Password))
    Write-Host -NoNewline $pwd
}

function Get-OcsAppPassword([string]$node, [string]$env)
{
    if ($env -eq 'test'){
        $target = '.test'
    } else {
        $target = ''
    }

    if ($node -eq "gss"){
        $file = 'pswd\ocs_gss.drive' + $target + '.sunet.se.app.xml'
    } else {
        $file = 'pswd\ocs_' + $node + '.drive' + $target + '.sunet.se.app.xml'
    }
    $cred = Import-Clixml -Path $file
    $pwd = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($cred.Password))
    Write-Host -NoNewline $pwd
}

function Get-SeleniumAppPassword([string]$node, [string]$env)
{
    if ($env -eq 'test'){
        $target = '.test'
    } else {
        $target = ''
    }

    if ($node -eq "gss"){
        $file = 'pswd\selenium_gss.drive' + $target + '.sunet.se.app.xml'
    } else {
        $file = 'pswd\selenium_' + $node + '.drive' + $target + '.sunet.se.app.xml'
    }
    $cred = Import-Clixml -Path $file
    $pwd = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($cred.Password))
    Write-Host -NoNewline $pwd
}

function Get-UserAppPassword([string]$node, [string]$env)
{
    if ($env -eq 'test'){
        $target = '.test'
    } else {
        $target = ''
    }

    if ($node -eq "gss"){
        $file = 'pswd\user_gss.drive' + $target + '.sunet.se.app.xml'
    } else {
        $file = 'pswd\user_' + $node + '.drive' + $target + '.sunet.se.app.xml'
    }
    $cred = Import-Clixml -Path $file
    $pwd = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($cred.Password))
    Write-Host -NoNewline $pwd
}

function Save-SamlUserCredentials([string]$userid, [string]$target)
{
    $cred = Get-Credential
    $file = 'pswd\samluser_' + $userid + '_' + $target + '.xml'
    $cred | Export-Clixml -Path $file
}

function Get-SamlUserName([string]$userid, [string]$target)
{
    $file = 'pswd\samluser_' + $userid + '_' + $target + '.xml'
    $cred = Import-Clixml -Path $file
    Write-Host -NoNewline $cred.UserName    
}

function Get-SamlUserPassword([string]$userid, [string]$target)
{
    $file = 'pswd\samluser_' + $userid + '_' + $target + '.xml'
    $cred = Import-Clixml -Path $file
    $pwd = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($cred.Password))
    Write-Host -NoNewline $pwd
}
