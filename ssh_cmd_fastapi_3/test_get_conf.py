
import pytest
from ssh_vmware import get_conf, ConfigNotFound
from pathlib import Path

def test_get_conf_file_not_found():
    conf_file = Path(__file__).parent / "fake_config.txt"
    with pytest.raises(ConfigNotFound):
        hosts = get_conf(conf_file)

def test_get_conf_file_found():
    conf_file = Path(__file__).parent / "ssh.conf"
    hosts = get_conf(conf_file)
    assert hosts is not None

def tmp_get_conf_file(tmp_path, content):
    conf_file = tmp_path / "ssh.conf"
    conf_file.write_text(content,encoding="utf-8")
    return conf_file

def test_get_conf_bad_lines_1(tmp_path):
    conf_file = tmp_get_conf_file(tmp_path, "#坏行 \n192.168.102.20,22,root")
    assert get_conf(conf_file) == [{"ip": "192.168.102.20", "port": 22, "username": "root"}]

def test_get_conf_bad_lines_2(tmp_path):
    conf_file = tmp_get_conf_file(tmp_path,"#坏行 \n a,22,root\n 192.168.102.20,a,root \n192.168.102.20,22,root")
    assert get_conf(conf_file) == [{"ip": "192.168.102.20", "port": 22, "username": "root"}]

