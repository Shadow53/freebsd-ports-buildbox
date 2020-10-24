#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 shadow53 <shadow53@shadow53.com>
#
# Distributed under terms of the MIT license.

"""
Python script that wraps poudriere to more easily build sets of packages.
"""

from concurrent.futures import ThreadPoolExecutor
import configparser
import itertools
import multiprocessing
import shutil
import subprocess


CONFIG_FILE = "/usr/local/etc/ports/ports.ini"
PKGLIST_DIR = "/usr/local/etc/ports/pkglists"

SECTION_PORTS = "ports"
SECTION_POUDRIERE = "poudriere"

DEFAULT_PORTS_DB = "/var/db/ports"
DEFAULT_PORTS_ROOT = "/usr/ports"

OPTION_PORTS_DB = "db"
OPTION_PORTS_DELETE = "delete"
OPTION_PORTS_ROOT = "root"
OPTION_PORTS_SETS = "sets"

DEFAULT_POUDRIERE_JAIL = "12amd64"
DEFAULT_POUDRIERE_PORTS = "default"
DEFAULT_POUDRIERE_PSET = "default"
DEFAULT_POUDRIERE_VERSION = "12.1-RELEASE"

OPTION_POUDRIERE_JAIL = "jail"
OPTION_POUDRIERE_PORTS = "ports"
OPTION_POUDRIERE_PSET = "set"
OPTION_POUDRIERE_VERSION = "version"


class Port:
    """Class representing a single port"""
    port_option_regex = re.compile(r"(?:^\s+)[A-Z]+(?:=)")
    option_file_list_regex = re.compile(r"(?:^_FILE_COMPLETE_OPTIONS_LIST=\s*)((\w+\s*)+)")

    def __init__(self, name, flavor=""):
        if "@" in name:
            if flavor != "":
                raise Exception("flavor given but name also contains flavor")

            at = name.index("@")
            flavor = name[at:]
            name = name[:at]

        self.name = name
        self.flavor = flavor

    def list_port_options(self, config):
        ports_root = config.get(SECTION_PORTS, OPTION_PORTS_ROOT,
                                DEFAULT_PORTS_ROOT)
        showconf = subprocess.run(args=["make", "-C",
                                        "%s/%s" % (ports_root, port.name),
                                        "showconfig"],
                                  capture_output=True,
                                  universal_newlines=True)
        lines = showconf.stdout.splitlines()
        lines = [line for line in lines if not line.startswith("=")]
        map(lambda line: self.port_option_regex.match(line).groups())
        options = [line[0] for line in lines if len(line) > 0]
        return set(options)

    def list_set_options(self, config):
        options_root = config.get(SECTION_PORTS, OPTION_PORTS_DB,
                                  DEFAULT_PORTS_DB)
        option_dir = self.name.replace("/", "_")
        options_file = "%s/%s/options" % (ports_root, option_dir)
        with open(options_file, "r") as options:
            lines = options.readlines()
            lines = [line for line in lines if line.startswith("_FILE_COMPLETE_OPTIONS_LIST=")]
            if len(lines) < 1:
                raise Exception("%s is not a valid port options file" % options_file)
            else:
                option_str = lines[0]
                options = self.option_file_list_regex.match(option_str).groups()
                if len(options) < 1:
                    return set()
                else:
                    option_str = options[0]
                    options = option_str.split()
                    return set(options)

    def has_new_options(self, config):
        set_options = self.list_set_options(config)
        port_options = self.list_port_options(config)
        diff = set_options ^ port_options
        return len(diff) > 0

    def set_options(self, config):
        db_dir = config.get(SECTION_PORTS, OPTION_PORTS_DB,
                            DEFAULT_PORTS_DB)
        ports_root = config.get(SECTION_PORTS, OPTION_PORTS_ROOT,
                                DEFAULT_PORTS_ROOT)
        args = []
        if self.flavor != "":
            args = ["make", "FLAVOR=%s" % self.flavor,
                    "PORT_DBDIR=%s" % db_dir, "-C",
                    "%s/%s" % (ports_root, self.name), "config"]
        else:
            args = ["make", "PORT_DBDIR=%s" % db_dir, "-C",
                    "%s/%s" % (ports_root, self.name), "config"]
        return subprocess.run(args).returncode


def check_dependencies():
    if shutil.which("poudriere"):
        raise Exception("Poudriere does not exist")


def get_all_ports(config):
    ports = set()
    with os.scandir(PKGLIST_DIR) as it:
        for direntry in [f for f in it if f.is_file()]:
            with open(direntry.path, "r") as f:
                lines = map(lambda line: line[:line.find("#")].strip(),
                            f.readlines())
                for line in [line for line in lines if len(line) > 0]:
                    ports.add(Port(line))
    return ports


def poudriere_build(config):
    # Sync options
    jail = config.get(SECTION_POUDRIERE, OPTION_POUDRIERE_JAIL,
                      DEFAULT_POUDRIERE_JAIL)
    ports = config.get(SECTION_POUDRIERE, OPTION_POUDRIERE_PORTS,
                       DEFAULT_POUDRIERE_PORTS)
    pset = config.get(SECTION_POUDRIERE, OPTION_POUDRIERE_PSET,
                      DEFAULT_POUDRIERE_PSET)
    subprocess.run("poudriere", "bulk",
                   "-j", jail, "-p", ports, "-z", pset,
                   *get_pkglist_files(config))


def poudriere_clean(config):
    jail = config.get(SECTION_POUDRIERE, OPTION_POUDRIERE_JAIL,
                      DEFAULT_POUDRIERE_JAIL)
    ports = config.get(SECTION_POUDRIERE, OPTION_POUDRIERE_PORTS,
                       DEFAULT_POUDRIERE_PORTS)
    pset = config.get(SECTION_POUDRIERE, OPTION_POUDRIERE_PSET,
                      DEFAULT_POUDRIERE_PSET)
    subprocess.run("poudriere", "pkgclean",
                   "-j", jail, "-p", ports, "-z", pset,
                   *get_pkglist_files(config))


def poudriere_options(config):
    def get_port_deps(port):
        ports_root = config.get(SECTION_PORTS, OPTION_PORTS_ROOT,
                                DEFAULT_PORTS_ROOT)
        env = {"PORT_DBDIR": ports_root}
        if port.flavor != "":
            env["FLAVOR"] = port.flavor
        args = ["make", env, "-C",
                os.path.join(ports_root, port.name),
                "config-conditional"]
        prog = subprocess.run(args=args, universal_newlines=True,
                              capture_output=True)
        return map(Port, prog.stdout.splitlines())

    def port_with_has_new_options(port):
        return (port, port.has_new_options(config))

    # Get list of all ports
    all_ports = get_all_ports(config)
    # Count number of ports
    num_ports = len(all_ports)
    # Get number of cpu cores
    num_cores = multiprocessing.cpu_count()
    # Get num per thread
    per_thread = round(float(num_ports) / float(num_cores))

    with ThreadPoolExecutor(num_cores) as executor:
        ports = executor.map(get_port_deps, all_ports)
        ports = list(itertools.chain(*ports))
        ports = executor.map(port_with_has_new_options, ports)
        ports = [port[0] for port in ports if port[1]]

        for port in ports:
            port.set_options(config)

    return None


def poudriere_setup(config):
    jail = config.get(SECTION_POUDRIERE, OPTION_POUDRIERE_JAIL,
                      DEFAULT_POUDRIERE_JAIL)
    ports = config.get(SECTION_POUDRIERE, OPTION_POUDRIERE_PORTS,
                       DEFAULT_POUDRIERE_PORTS)
    version = config.get(SECTION_POUDRIERE, OPTION_POUDRIERE_VERSION,
                         DEFAULT_POUDRIERE_VERSION)
    # Create poudriere jail
    subprocess.run("poudriere", "jail", "-c", "-j", jail, "-v", version)
    # Create poudriere ports collection
    subprocess.run("poudriere", "ports", "-c", "-p", ports)


def poudriere_update_ports(config):
    if shutil.which("portshaker"):
        subprocess.run("portshaker")
    else:
        ports = config.get(SECTION_POUDRIERE, OPTION_POUDRIERE_PORTS)
        subprocess.run("poudriere", "ports", "-u", "-p", ports)
    with config.get(SECTION_PORTS, OPTION_PORTS_DELETE) as to_del:
        for file in to_del:
            os.remove(file)


def load_config(config_file=CONFIG_FILE):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config


def set_options():

