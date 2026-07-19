import pytest
from zsm.core.system import validate_name

def test_valid_names(): assert validate_name("NAS3") == "NAS3"
@pytest.mark.parametrize("name",["","../bad","bad/name","a"*65])
def test_invalid_names(name):
    with pytest.raises(ValueError): validate_name(name)
