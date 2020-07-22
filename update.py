from eman import Eman
from secrets import USERNAME, PASSWORD

am = Eman(USERNAME, PASSWORD)

interfaces = (

)

for i in interfaces:
    result = am.Eman.mod_scope(scope_name=i,
                         selectiontags=("IPPhones", "OtherDevices"))
    print(result)

    result = am.Eman.mod_scope