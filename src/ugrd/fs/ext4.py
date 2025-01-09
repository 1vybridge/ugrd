__version__ = "0.1.1"

def ext4_fsck(self) -> list[str]:
    """ Returns bash lines to run fsck on the root filesystem
    The root device is determined by checking the source of SWITCH_ROOT_TARGET

    """
    return [
        """ROOT_DEV=$(awk -v target="$(readvar SWITCH_ROOT_TARGET)" '$2 == target {print $1}' /proc/mounts)""",
        """ROOT_TYPE=$(awk -v target="$(readvar SWITCH_ROOT_TARGET)" '$2 == target {print $3}' /proc/mounts)""",
        """ROOT_OPTS=$(awk -v target="$(readvar SWITCH_ROOT_TARGET)" '$2 == target {print $4}' /proc/mounts)""",
        'if [ "$ROOT_TYPE" != "ext4" ]; then',
        "    einfo 'Root filesystem is not ext4, skipping fsck'",
        "    return",
        "fi",
        "einfo Running fsck on: $ROOT_DEV",
        "umount $(readvar SWITCH_ROOT_TARGET)",  # Unmount the root filesystem so fsck can run
        "einfo $(fsck.ext4 -p $ROOT_DEV)",
        "mount $ROOT_DEV $(readvar SWITCH_ROOT_TARGET) -o $ROOT_OPTS",  # Remount using the same options
    ]

