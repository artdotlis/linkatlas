from pathlib import Path
import tomllib
from utilslink.container.conf import AgentConf
from utilslink.error.exceptions import BootstrapEx


def create_agent_config(conf: Path) -> AgentConf:
    print(f"parsing {conf} - AGENT")
    with conf.open("rb") as fh_c:
        conf_d = tomllib.load(fh_c)
        if not("agent" in conf_d and isinstance(conf_d["agent"], dict)):
            raise BootstrapEx("no agent config found")
        return AgentConf(**conf_d["agent"])
