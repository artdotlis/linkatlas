from pathlib import Path
import tomllib
from utilslink.container.conf import LPSNConf
from utilslink.error.exceptions import BootstrapEx


def create_lpsn_config(conf: Path) -> LPSNConf:
    print(f"parsing {conf} - LPSN")
    with conf.open("rb") as fh_c:
        conf_d = tomllib.load(fh_c)
        if "dsmz_keycloak" not in conf_d and not isinstance(
            conf_d["dsmz_keycloak"], dict
        ):
            raise BootstrapEx("no dsmz_keycloak config found")
        return LPSNConf(**conf_d["dsmz_keycloak"])
