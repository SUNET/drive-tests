
<?php
$path = 'mappingfile.json';
$jsonString = file_get_contents($path);
$jsonData = json_decode($jsonString, true);

$users = ['name@sunet.se','first.last@sunet.se', 'first.last@hh.se', 'first.last@shh.se',
          'name@sub.sunet.se','first.last@sub.sunet.se', 'first.last@sub.hh.se', 'first.last@sub.shh.se',
          'name@sub.inst.sunet.se','first.last@sub.inst.sunet.se', 'first.last@sub.inst.hh.se', 'first.last@sub.inst.shh.se',
          'sunet.se@sub.inst.sunet.se','ki.se@sub.inst.sunet.se', 'sub.inst.shh.se@sub.inst.hh.se', 'sub.inst.hh.se@sub.inst.shh.se',
          '@.shh.se', 'some@.hh.se', 'some@inst.shhs', 'sunet.se',
          'some-user@eduid.se','ki.se@somedomain.edu','ki.se@ki.se.somedomain.edu'];

foreach ($users as &$user)
{
    foreach ($jsonData as $regex => $node) {
        // printf("Testing regex: %s\n", $regex);
        if (preg_match($regex, $user, $matches) === 1)
        {
            printf("%35s: %s\n", $user, $node );
            break;
        }
    }
}
?>
