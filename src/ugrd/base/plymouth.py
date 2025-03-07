__version__ = "0.4.0"

from configparser import ConfigParser
from pathlib import Path

PLYMOUTH_CONFIG_FILES = ["/etc/plymouth/plymouthd.conf", "/usr/share/plymouth/plymouthd.defaults"]


def find_plymouth_config(self) -> None:
    """Processes themes from plymouth config file
    Sets the config file if it is the first one found"""
    for file in PLYMOUTH_CONFIG_FILES:
        plymouth_config = ConfigParser()
        plymouth_config.read(file)
        if plymouth_config.has_section("Daemon") and plymouth_config.has_option("Daemon", "Theme"):
            self["plymouth_themes"] += plymouth_config["Daemon"]["Theme"]
            if str(self["plymouth_config"]) == ".":  # Set the first config file found
                self["plymouth_config"] = file
            continue
        self.logger.debug("Plymouth config file missing theme option: %s" % file)
    if not self["plymouth_themes"]:
        self.logger.error("No plymouth theme found in config files.")


def _process_plymouth_themes_multi(self, theme) -> None:
    """Checks that the theme is valid"""
    theme_dir = Path("/usr/share/plymouth/themes") / theme
    if not theme_dir.exists():
        raise FileNotFoundError("Theme directory not found: %s" % theme_dir)
    self.data["plymouth_themes"].append(theme)


def pull_plymouth(self) -> None:
    """Adds plymouth files to dependencies"""
    dir_list = [Path("/usr/lib64/plymouth")]
    for theme in self["plymouth_themes"]:
        dir_list += [Path("/usr/share/plymouth/themes/") / theme]
    self.logger.debug("Adding plymouth files to dependencies.")
    for directory in dir_list:
        for file in directory.rglob("*"):
            self["dependencies"] = file

    if str(self["plymouth_config"]) != "/usr/share/plymouth/plymouthd.defaults":
        self["copies"] = {
            "plymouth_config_file": {"source": self["plymouth_config"], "destination": "/etc/plymouth/plymouthd.conf"}
        }


def make_devpts(self) -> str:
    """Creates /dev/pts and mounts the fstab entry"""
    return """
    mkdir -m755 -p /dev/pts
    mount /dev/pts
    """


def _get_plymouthd_args(self) -> str:
    """Returns arguments for running plymouthd"""
    base_args = "--mode=boot --pid-file=/run/plymouth/plymouth.pid --attach-to-session"
    cmdline_args = []
    if "ugrd.kmod.novideo" in self["modules"]:  # If novideo is enabled, force the plymouth.use-simpledrm option
        cmdline_args.append("plymouth.use-simpledrm")
    if self["plymouth_force_splash"]:
        base_args += " --splash"

    if cmdline_args:
        return f'{base_args} --kernel-command-line="{" ".join(cmdline_args)} $(< /proc/cmdline)"'
    return base_args


def start_plymouth(self) -> str:
    """Returns shell lines to run plymouthd"""
    return f"""
    plymouthd {_get_plymouthd_args(self)}
    if ! plymouth --ping; then
        eerror "Failed to start plymouthd"
        return 1
    fi
    setvar plymouth 1
    plymouth show-splash
    """
