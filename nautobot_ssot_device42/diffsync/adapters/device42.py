"""DiffSync adapter for Device42."""

import re
from decimal import Decimal
from typing import Union, List

from diffsync import DiffSync
from diffsync.exceptions import ObjectAlreadyExists, ObjectNotFound
from django.utils.functional import classproperty
from django.utils.text import slugify
from nautobot_ssot_device42.constant import PLUGIN_CFG
from nautobot_ssot_device42.diffsync.models.base import assets, circuits, dcim, ipam
from nautobot_ssot_device42.utils.device42 import get_facility, get_intf_type, get_netmiko_platform
from netutils.bandwidth import name_to_bits
from netutils.dns import is_fqdn_resolvable, fqdn_to_ip

from nautobot.core.settings_funcs import is_truthy


def sanitize_string(san_str: str):
    """Sanitize string to ensure it doesn't have invisible characters."""
    return san_str.replace("\u200b", "").replace("\r", "")


def get_circuit_status(status: str) -> str:
    """Map Device42 Status to Nautobot Status.

    Args:
        status (str): Device42 Status to be mapped.

    Returns:
        str: Device42 mapped Status.
    """
    STATUS_MAP = {
        "Production": "Active",
        "Provisioning": "Provisioning",
        "Canceled": "Deprovisioning",
        "Decommissioned": "Decommissioned",
    }
    if status in STATUS_MAP:
        return STATUS_MAP[status]
    else:
        return "Offline"


def get_site_from_mapping(device_name: str) -> Union[str, bool]:
    """Method to map a Device to a Site based upon their name using a regex pattern in the settings.

    This works in conjunction with the `hostname_mapping` setting to have a Device assigned to a Site by hostname. This is done using a regex pattern mapped to the Site slug.

    Args:
        device_name (str): Name of the Device to be matched. Must match one of the regex patterns provided to get a response.

    Returns:
        Union[str, bool]: The Site slug of the associated Site for the Device in the mapping. Returns False if match not found.
    """
    for _entry in PLUGIN_CFG["hostname_mapping"]:
        for _mapping, _slug in _entry.items():
            site_match = re.match(_mapping, device_name)
            if site_match:
                return _slug
    return False


def get_dns_a_record(dev_name: str):
    """Method to obtain A record for a Device.

    Args:
        dev_name (str): Name of Device to perform DNS query for.

    Returns:
        str: A record for Device if exists, else False.
    """
    if is_fqdn_resolvable(dev_name):
        return fqdn_to_ip(dev_name)
    else:
        return False


class Device42Adapter(DiffSync):
    """DiffSync adapter using requests to communicate to Device42 server."""

    building = dcim.Building
    room = dcim.Room
    rack = dcim.Rack
    vendor = dcim.Vendor
    hardware = dcim.Hardware
    cluster = dcim.Cluster
    device = dcim.Device
    port = dcim.Port
    vrf = ipam.VRFGroup
    subnet = ipam.Subnet
    ipaddr = ipam.IPAddress
    vlan = ipam.VLAN
    conn = dcim.Connection
    provider = circuits.Provider
    circuit = circuits.Circuit
    patchpanel = assets.PatchPanel
    patchpanelfrontport = assets.PatchPanelFrontPort
    patchpanelrearport = assets.PatchPanelRearPort

    top_level = [
        "building",
        "vendor",
        "hardware",
        "vrf",
        "subnet",
        "vlan",
        "cluster",
        "device",
        "patchpanel",
        "patchpanelrearport",
        "patchpanelfrontport",
        "ipaddr",
        "provider",
        "circuit",
        "conn",
    ]

    def __init__(self, *args, job=None, sync=None, client, **kwargs):
        """Initialize Device42Adapter.

        Args:
            job (object, optional): Nautobot job. Defaults to None.
            sync (object, optional): Nautobot DiffSync. Defaults to None.
            client (object): Device42API client connection object.
        """
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self.device42_hardware_dict = {}
        self.device42 = client
        self.device42_clusters = self.device42.get_cluster_members()

        # mapping of SiteCode (facility) to Building name
        self.d42_building_sitecode_map = {}
        # mapping of Building PK to Building info
        self.d42_building_map = self.device42.get_building_pks()
        # mapping of Customer PK to Customer info
        self.d42_customer_map = self.device42.get_customer_pks()
        # mapping of Room PK to Room info
        self.d42_room_map = self.device42.get_room_pks()
        # mapping of Rack PK to Rack info
        self.d42_rack_map = self.device42.get_rack_pks()
        # mapping of VLAN PK to VLAN name and ID
        self.d42_vlan_map = self.device42.get_vlan_info()
        # mapping of Device PK to Device name
        self.d42_device_map = self.device42.get_device_pks()
        # mapping of Port PK to Port name
        self.d42_port_map = self.device42.get_port_pks()
        # mapping of Vendor PK to Vendor info
        self.d42_vendor_map = self.device42.get_vendor_pks()

    @classproperty
    def _device42_hardwares(self):
        if not self.device42_hardware_dict:
            device42_hardware_list = self.device42.api_call(path="api/2.0/hardwares/")["models"]
            for hardware in device42_hardware_list["models"]:
                self.device42_hardware_dict[hardware["hardware_id"]] = hardware
        return self.device42_hardware_dict

    def get_building_for_device(self, dev_record: dict) -> str:
        """Method to determine the Building (Site) for a Device.

        Args:
            dev_record (dict): Dictionary of Device information from Device42. Needs to have name, customer, and building keys depending upon enabled plugin settings.

        Returns:
            str: Slugified version of the Building (Site) for a Device.
        """
        _building = False
        if PLUGIN_CFG.get("hostname_mapping") and len(PLUGIN_CFG["hostname_mapping"]) > 0:
            _building = get_site_from_mapping(device_name=dev_record["name"])

        if not _building:
            if (
                PLUGIN_CFG.get("customer_is_facility")
                and dev_record.get("customer")
                and dev_record["customer"] in self.d42_building_sitecode_map
            ):
                _building = self.d42_building_sitecode_map[dev_record["customer"].upper()]
            else:
                _building = dev_record.get("building")
        if _building is not None:
            return slugify(_building)
        return ""

    def load_buildings(self):
        """Load Device42 buildings."""
        for record in self.device42.get_buildings():
            if self.job.kwargs.get("debug"):
                self.job.log_info(message=f"Loading {record['name']} building from Device42.")
            _tags = record["tags"] if record.get("tags") else []
            if len(_tags) > 1:
                _tags.sort()
            building = self.building(
                name=record["name"],
                address=sanitize_string(record["address"]) if record.get("address") else "",
                latitude=round(Decimal(record["latitude"] if record["latitude"] else 0.0), 6),
                longitude=round(Decimal(record["longitude"] if record["longitude"] else 0.0), 6),
                contact_name=record["contact_name"] if record.get("contact_name") else "",
                contact_phone=record["contact_phone"] if record.get("contact_phone") else "",
                rooms=record["rooms"] if record.get("rooms") else [],
                custom_fields=sorted(record["custom_fields"], key=lambda d: d["key"]),
                tags=_tags,
                uuid=None,
            )
            _facility = get_facility(diffsync=self, tags=_tags)
            if _facility:
                self.d42_building_sitecode_map[_facility.upper()] = record["name"]
            try:
                self.add(building)
            except ObjectAlreadyExists as err:
                if self.job.kwargs.get("debug"):
                    self.job.log_warning(message=f"{record['name']} is already loaded. {err}")

    def load_rooms(self):
        """Load Device42 rooms."""
        for record in self.device42.get_rooms():
            if self.job.kwargs.get("debug"):
                self.job.log_info(message=f"Loading {record['name']} room from Device42.")
            _tags = record["tags"] if record.get("tags") else []
            if len(_tags) > 1:
                _tags.sort()
            if record.get("building"):
                room = self.room(
                    name=record["name"],
                    building=record["building"],
                    notes=record["notes"] if record.get("notes") else "",
                    custom_fields=sorted(record["custom_fields"], key=lambda d: d["key"]),
                    tags=_tags,
                    uuid=None,
                )
                try:
                    self.add(room)
                    _site = self.get(self.building, record.get("building"))
                    _site.add_child(child=room)
                except ObjectAlreadyExists as err:
                    if self.job.kwargs.get("debug"):
                        self.job.log_warning(message=f"{record['name']} is already loaded. {err}")
            else:
                if self.job.kwargs.get("debug"):
                    self.job.log_warning(message=f"{record['name']} is missing Building and won't be imported.")
                continue

    def load_racks(self):
        """Load Device42 racks."""
        if self.job.kwargs.get("debug"):
            self.job.log_info(message="Loading racks from Device42.")
        for record in self.device42.get_racks():
            _tags = record["tags"] if record.get("tags") else []
            if len(_tags) > 1:
                _tags.sort()
            if record.get("building") and record.get("room"):
                rack = self.rack(
                    name=record["name"],
                    building=record["building"],
                    room=record["room"],
                    height=record["size"] if record.get("size") else 1,
                    numbering_start_from_bottom=record["numbering_start_from_bottom"],
                    custom_fields=sorted(record["custom_fields"], key=lambda d: d["key"]),
                    tags=_tags,
                    uuid=None,
                )
                try:
                    self.add(rack)
                    _room = self.get(
                        self.room, {"name": record["room"], "building": record["building"], "room": record["room"]}
                    )
                    _room.add_child(child=rack)
                except ObjectAlreadyExists as err:
                    if self.job.kwargs.get("debug"):
                        self.job.log_warning(message=f"Rack {record['name']} already exists. {err}")
            else:
                if self.job.kwargs.get("debug"):
                    self.job.log_warning(
                        message=f"{record['name']} is missing Building and Room and won't be imported."
                    )
                continue

    def load_vendors(self):
        """Load Device42 vendors."""
        for _vendor in self.device42.get_vendors():
            if self.job.kwargs.get("debug"):
                self.job.log_info(message=f"Loading vendor {_vendor['name']} from Device42.")
            vendor = self.vendor(
                name=_vendor["name"],
                custom_fields=_vendor["custom_fields"],
                uuid=None,
            )
            self.add(vendor)

    def load_hardware_models(self):
        """Load Device42 hardware models."""
        for _model in self.device42.get_hardware_models():
            if self.job.kwargs.get("debug"):
                self.job.log_info(message=f"Loading hardware model {_model['name']} from Device42.")
            if _model.get("manufacturer"):
                model = self.hardware(
                    name=sanitize_string(_model["name"]),
                    manufacturer=_model["manufacturer"] if _model.get("manufacturer") else "Unknown",
                    size=float(round(_model["size"])) if _model.get("size") else 1.0,
                    depth=_model["depth"] if _model.get("depth") else "Half Depth",
                    part_number=_model["part_no"] if _model.get("part_no") else "",
                    custom_fields=sorted(_model["custom_fields"], key=lambda d: d["key"])
                    if _model.get("custom_fields")
                    else [],
                    uuid=None,
                )
                try:
                    self.add(model)
                except ObjectAlreadyExists as err:
                    if self.job.kwargs.get("debug"):
                        self.job.log_warning(message=f"Hardware model already exists. {err}")
                    continue

    def get_cluster_host(self, device: str) -> Union[str, bool]:
        """Get name of cluster host if device is in a cluster.

        Args:
            device (str): Name of device to see if part of cluster.

        Returns:
            Union[str, bool]: Name of cluster device is part of or returns False.
        """
        for _cluster, _info in self.device42_clusters.items():
            if device in _info["members"]:
                return _cluster
        return False

    def load_cluster(self, cluster_info: dict):
        """Load Device42 clusters into DiffSync model.

        Args:
            cluster_info (dict): Information of cluster to be added to DiffSync model.

        Returns:
            models.Cluster: Cluster model that has been created or found.
        """
        try:
            _cluster = self.get(self.cluster, cluster_info["name"][:64])
        except ObjectAlreadyExists as err:
            if self.job.kwargs.get("debug"):
                self.job.log_warning(message=f"Cluster {cluster_info['name']} already has been added. {err}")
        except ObjectNotFound:
            if self.job.kwargs.get("debug"):
                self.job.log_info(message=f"Cluster {cluster_info['name']} being added.")
            _clus = self.device42_clusters[cluster_info["name"]]
            _tags = cluster_info["tags"] if cluster_info.get("tags") else []
            if PLUGIN_CFG.get("ignore_tag") and PLUGIN_CFG["ignore_tag"] in _tags:
                return
            _members = _clus["members"]
            if len(_members) > 1:
                _members.sort()
            if len(_tags) > 1:
                _tags.sort()
            _cluster = self.cluster(
                name=cluster_info["name"][:64],
                members=_members,
                tags=_tags,
                custom_fields=sorted(cluster_info["custom_fields"], key=lambda d: d["key"]),
                uuid=None,
            )
            self.add(_cluster)
            # Add master device to hold stack info like intfs and IPs
            _building = self.get_building_for_device(dev_record={**_clus, **cluster_info})
            _device = self.device(
                name=cluster_info["name"][:64],
                building=_building if _building else "",
                rack="",
                rack_orientation="rear",
                room="",
                hardware=sanitize_string(_clus["hardware"]),
                os=get_netmiko_platform(_clus["os"][:100]) if _clus.get("os") else "",
                in_service=cluster_info.get("in_service"),
                tags=_tags,
                cluster_host=cluster_info["name"][:64],
                master_device=True,
                serial_no="",
                custom_fields=sorted(cluster_info["custom_fields"], key=lambda d: d["key"]),
                rack_position=None,
                os_version=None,
                uuid=None,
            )
            self.add(_device)

    def load_devices_and_clusters(self):
        """Load Device42 devices."""
        # Get all Devices from Device42
        if self.job.kwargs.get("debug"):
            self.job.log_info(message="Retrieving devices from Device42.")
        _devices = self.device42.api_call(path="api/1.0/devices/all/?is_it_switch=yes")["Devices"]

        # Add all Clusters first
        if self.job.kwargs.get("debug"):
            self.job.log_info(message="Loading clusters...")
        for _record in _devices:
            if _record.get("type") == "cluster" and _record.get("name") in self.device42_clusters.keys():
                if self.job.kwargs.get("debug"):
                    self.job.log_info(message=f"Attempting to load cluster {_record['name']}")
                self.load_cluster(_record)

        # Then iterate through again and add Devices and if are part of a cluster, add to Cluster
        for _record in _devices:
            if _record.get("type") != "cluster" and _record.get("hw_model"):
                _tags = _record["tags"] if _record.get("tags") else []
                if PLUGIN_CFG.get("ignore_tag") and PLUGIN_CFG["ignore_tag"] in _tags:
                    continue
                if len(_tags) > 1:
                    _tags.sort()
                _building = self.get_building_for_device(dev_record=_record)
                # only consider devices that have a Building
                if _building == "":
                    if self.job.kwargs.get("debug"):
                        self.job.log_debug(
                            message=f"Device {_record['name']} is not being added. Unable to find Building."
                        )
                    continue
                _device = self.device(
                    name=_record["name"][:64],
                    building=_building,
                    room=_record["room"] if _record.get("room") else "",
                    rack=_record["rack"] if _record.get("rack") else "",
                    rack_position=int(_record["start_at"]) if _record.get("start_at") else None,
                    rack_orientation="front" if _record.get("orientation") == 1 else "rear",
                    hardware=sanitize_string(_record["hw_model"]),
                    os=get_netmiko_platform(_record["os"][:100]) if _record.get("os") else "",
                    os_version=re.sub(r"^[a-zA-Z]+\s", "", _record["osver"]) if _record.get("osver") else "",
                    in_service=_record.get("in_service"),
                    serial_no=_record["serial_no"],
                    master_device=False,
                    tags=_tags,
                    custom_fields=sorted(_record["custom_fields"], key=lambda d: d["key"]),
                    cluster_host=None,
                    uuid=None,
                )
                try:
                    cluster_host = self.get_cluster_host(_record["name"])
                    if cluster_host:
                        if is_truthy(self.device42_clusters[cluster_host]["is_network"]) is False:
                            if self.job.kwargs.get("debug"):
                                self.job.log_warning(
                                    message=f"{cluster_host} has network device members but isn't marked as network. This should be corrected in Device42."
                                )
                        _device.cluster_host = cluster_host
                        if _device.name == cluster_host:
                            _device.master_device = True
                    if self.job.kwargs.get("debug"):
                        self.job.log_info(message=f"Device {_record['name']} being added.")
                    self.add(_device)
                except ObjectAlreadyExists as err:
                    if self.job.kwargs.get("debug"):
                        self.job.log_warning(message=f"Device already added. {err}")
                    continue

    def load_ports(self):
        """Load Device42 ports."""
        vlan_ports = self.device42.get_ports_with_vlans()
        no_vlan_ports = self.device42.get_ports_wo_vlans()
        merged_ports = self.filter_ports(vlan_ports, no_vlan_ports)
        # merged_ports = vlan_ports + no_vlan_ports
        default_cfs = self.device42.get_port_default_custom_fields()
        _cfs = self.device42.get_port_custom_fields()
        for _port in merged_ports:
            if _port.get("port_name") and _port.get("device_name"):
                if self.job.kwargs.get("debug"):
                    self.job.log_info(message=f"Loading Port {_port['port_name']} for Device {_port['device_name']}")
                _tags = _port["tags"].split(",") if _port.get("tags") else []
                if len(_tags) > 1:
                    _tags.sort()
                try:
                    new_port = self.port(
                        name=_port["port_name"][:63].strip(),
                        device=_port["device_name"],
                        enabled=is_truthy(_port["up_admin"]),
                        mtu=_port["mtu"] if _port.get("mtu") in range(1, 65537) else 1500,
                        description=_port["description"],
                        mac_addr=_port["hwaddress"][:13],
                        type=get_intf_type(intf_record=_port),
                        tags=_tags,
                        mode="access",
                        custom_fields=None,
                        uuid=None,
                    )
                    if _port.get("vlan_pks"):
                        _tags = []
                        for _pk in _port["vlan_pks"]:
                            if _pk in self.d42_vlan_map and self.d42_vlan_map[_pk]["vid"] != 0:
                                _tags.append(
                                    {
                                        "vlan_name": self.d42_vlan_map[_pk]["name"],
                                        "vlan_id": str(self.d42_vlan_map[_pk]["vid"]),
                                    }
                                )
                        _sorted_list = sorted(_tags, key=lambda k: k["vlan_id"])
                        _vlans = [i for n, i in enumerate(_sorted_list) if i not in _sorted_list[n + 1 :]]  # noqa: E203
                        new_port.vlans = _vlans
                        if len(_vlans) > 1:
                            new_port.mode = "tagged"
                    if _port["device_name"] in _cfs and _cfs[_port["device_name"]].get(_port["port_name"]):
                        new_port.custom_fields = sorted(
                            _cfs[_port["device_name"]][_port["port_name"]], key=lambda d: d["key"]
                        )
                    else:
                        new_port.custom_fields = default_cfs
                    self.add(new_port)
                    try:
                        _dev = self.get(self.device, _port["device_name"])
                        _dev.add_child(new_port)
                    except ObjectNotFound as err:
                        if self.job.kwargs.get("debug"):
                            self.job.log_warning(message=f"Device {_port['device_name']} not found. {err}")
                        continue
                except ObjectAlreadyExists as err:
                    if self.job.kwargs.get("debug"):
                        self.job.log_warning(message=f"Port already exists. {err}")
                    continue

    def filter_ports(self, vlan_ports: List[dict], no_vlan_ports: List[dict]) -> List[dict]:
        """Method to combine lists of ports while removing duplicates.

        Args:
            vlan_ports (List[dict]): List of Ports with tagged VLANs.
            no_vlan_ports (List[dict]): List of Ports without VLANs.

        Returns:
            List[dict]: Merged list of Ports with duplicates removed.
        """
        no_vlan_ports_only = []
        for no_vlan_port in no_vlan_ports:
            for vlan_port in vlan_ports:
                if no_vlan_port["hwaddress"] == vlan_port["hwaddress"] or (
                    no_vlan_port["port_name"] == vlan_port["port_name"]
                    and no_vlan_port["device_name"] == vlan_port["device_name"]
                ):
                    if self.job.kwargs.get("debug"):
                        self.job.log_debug(f"Duplicate port {no_vlan_port} found and won't be added.")
                    break
            else:
                no_vlan_ports_only.append(no_vlan_port)
        return vlan_ports + no_vlan_ports_only

    def load_vrfgroups(self):
        """Load Device42 VRFGroups."""
        for _grp in self.device42.api_call(path="api/1.0/vrfgroup/")["vrfgroup"]:
            if self.job.kwargs.get("debug"):
                self.job.log_info(message="Retrieving VRF groups from Device42.")
            try:
                _tags = _grp["tags"] if _grp.get("tags") else []
                if len(_tags) > 1:
                    _tags.sort()
                new_vrf = self.vrf(
                    name=_grp["name"],
                    description=_grp["description"],
                    tags=_tags,
                    custom_fields=sorted(_grp["custom_fields"], key=lambda d: d["key"]),
                    uuid=None,
                )
                self.add(new_vrf)
            except ObjectAlreadyExists as err:
                if self.job.kwargs.get("debug"):
                    self.job.log_warning(message=f"VRF Group {_grp['name']} already exists. {err}")
                continue

    def load_subnets(self):
        """Load Device42 Subnets."""
        if self.job.kwargs.get("debug"):
            self.job.log_info(message="Retrieving Subnets from Device42.")
        default_cfs = self.device42.get_port_default_custom_fields()
        _cfs = self.device42.get_subnet_custom_fields()
        for _pf in self.device42.get_subnets():
            _tags = _pf["tags"].split(",") if _pf.get("tags") else []
            if len(_tags) > 1:
                _tags.sort()
            if _pf["mask_bits"] != 0:
                try:
                    new_pf = self.subnet(
                        network=_pf["network"],
                        mask_bits=_pf["mask_bits"],
                        description=_pf["name"],
                        vrf=_pf["vrf"],
                        tags=_tags,
                        custom_fields=None,
                        uuid=None,
                    )
                    if f"{_pf['network']}/{_pf['mask_bits']}" in _cfs:
                        new_pf.custom_fields = sorted(
                            _cfs[f"{_pf['network']}/{_pf['mask_bits']}"], key=lambda d: d["key"]
                        )
                    else:
                        new_pf.custom_fields = default_cfs
                    self.add(new_pf)
                except ObjectAlreadyExists as err:
                    if self.job.kwargs.get("debug"):
                        self.job.log_warning(message=f"Subnet {_pf['network']} {_pf['mask_bits']} {_pf['vrf']} {err}")
                    continue
            else:
                if self.job.kwargs.get("debug"):
                    self.job.log_warning(
                        message=f"Unable to import Subnet with a 0 mask bits. {_pf['network']} {_pf['name']}."
                    )
                continue

    def load_ip_addresses(self):
        """Load Device42 IP Addresses."""
        if self.job.kwargs.get("debug"):
            self.job.log_info(message="Retrieving IP Addresses from Device42.")
        default_cfs = self.device42.get_ipaddr_default_custom_fields()
        _cfs = self.device42.get_ipaddr_custom_fields()
        for _ip in self.device42.get_ip_addrs():
            _ipaddr = f"{_ip['ip_address']}/{str(_ip['netmask'])}"
            try:
                _tags = _ip["tags"].split(",") if _ip.get("tags") else []
                if len(_tags) > 1:
                    _tags.sort()
                new_ip = self.ipaddr(
                    address=_ipaddr,
                    available=_ip["available"],
                    label=_ip["label"],
                    device=_ip["device"] if _ip.get("device") else "",
                    interface=_ip["port_name"] if _ip.get("port_name") else "",
                    primary=False,
                    vrf=_ip["vrf"],
                    tags=_tags,
                    custom_fields=None,
                    uuid=None,
                )
                if _ipaddr in _cfs:
                    print(f"{_ipaddr} found in _cfs. CustomFields being added.")
                    new_ip.custom_fields = _cfs[_ipaddr]
                else:
                    new_ip.custom_fields = default_cfs
                self.add(new_ip)
            except ObjectAlreadyExists as err:
                if self.job.kwargs.get("debug"):
                    self.job.log_warning(message=f"IP Address {_ipaddr} already exists.{err}")
                continue

    def load_vlans(self):
        """Load Device42 VLANs."""
        _vlans = self.device42.get_vlans_with_location()
        for _info in _vlans:
            try:
                _vlan_name = _info["vlan_name"].strip()
                if _info.get("building"):
                    new_vlan = self.get(
                        self.vlan, {"name": _vlan_name, "vlan_id": _info["vid"], "building": _info["building"]}
                    )
                elif is_truthy(PLUGIN_CFG.get("customer_is_facility")) and _info.get("customer"):
                    new_vlan = self.get(
                        self.vlan,
                        {
                            "name": _vlan_name,
                            "vlan_id": _info["vid"],
                            "building": self.d42_building_sitecode_map[_info["customer"]],
                        },
                    )
                else:
                    new_vlan = self.get(self.vlan, {"name": _vlan_name, "vlan_id": _info["vid"], "building": "Unknown"})
            except ObjectAlreadyExists as err:
                if self.job.kwargs.get("debug"):
                    self.job.log_warning(message=f"VLAN {_vlan_name} already exists. {err}")
            except ObjectNotFound:
                if _info["vlan_pk"] in self.d42_vlan_map and self.d42_vlan_map[_info["vlan_pk"]].get("custom_fields"):
                    _cfs = sorted(self.d42_vlan_map[_info["vlan_pk"]]["custom_fields"], key=lambda d: d["key"])
                else:
                    _cfs = None
                new_vlan = self.vlan(
                    name=_vlan_name,
                    vlan_id=int(_info["vid"]),
                    description=_info["description"] if _info.get("description") else "",
                    custom_fields=_cfs if _cfs else [],
                    building=None,
                    uuid=None,
                )
                if _info.get("building"):
                    new_vlan.building = _info["building"]
                elif is_truthy(PLUGIN_CFG.get("customer_is_facility")) and _info.get("customer"):
                    new_vlan.building = self.d42_building_sitecode_map[_info["customer"]]
                else:
                    new_vlan.building = "Unknown"
                self.add(new_vlan)

    def load_connections(self):
        """Load Device42 connections."""
        _port_conns = self.device42.get_port_connections()
        for _conn in _port_conns:
            try:
                new_conn = self.conn(
                    src_device=self.d42_device_map[_conn["src_device"]]["name"],
                    src_port=self.d42_port_map[_conn["src_port"]]["port"],
                    src_port_mac=self.d42_port_map[_conn["src_port"]]["hwaddress"],
                    src_type="interface",
                    dst_device=self.d42_device_map[_conn["dst_device"]]["name"],
                    dst_port=self.d42_port_map[_conn["dst_port"]]["port"],
                    dst_port_mac=self.d42_port_map[_conn["dst_port"]]["hwaddress"],
                    dst_type="interface",
                    tags=None,
                    uuid=None,
                )
                self.add(new_conn)
                # in order to have cables match up to Nautobot, we need to add from both sides
                rev_conn = self.conn(
                    src_device=self.d42_device_map[_conn["dst_device"]]["name"],
                    src_port=self.d42_port_map[_conn["dst_port"]]["port"],
                    src_port_mac=self.d42_port_map[_conn["dst_port"]]["hwaddress"],
                    src_type="interface",
                    dst_device=self.d42_device_map[_conn["src_device"]]["name"],
                    dst_port=self.d42_port_map[_conn["src_port"]]["port"],
                    dst_port_mac=self.d42_port_map[_conn["src_port"]]["hwaddress"],
                    dst_type="interface",
                    tags=None,
                    uuid=None,
                )
                self.add(rev_conn)
            except ObjectAlreadyExists as err:
                if self.job.kwargs.get("debug"):
                    self.job.log_warning(message=err)
                continue

    def load_provider(self, provider_info: dict):
        """Load Device42 Providers."""
        _prov = self.d42_vendor_map[provider_info["vendor_fk"]]
        try:
            self.get(self.provider, _prov.get("name"))
        except ObjectNotFound:
            new_provider = self.provider(
                name=_prov["name"],
                notes=_prov["notes"],
                vendor_url=_prov["home_page"],
                vendor_acct=_prov["account_no"][:30],
                vendor_contact1=_prov["escalation_1"],
                vendor_contact2=_prov["escalation_2"],
                tags=None,
                uuid=None,
            )
            self.add(new_provider)

    def load_providers_and_circuits(self):
        """Load Device42 Providrs and Telco Circuits."""
        _circuits = self.device42.get_telcocircuits()
        origin_int, origin_dev, endpoint_int, endpoint_dev = False, False, False, False
        ppanel_ports = self.device42.get_patch_panel_port_pks()
        for _tc in _circuits:
            self.load_provider(_tc)
            if _tc["origin_type"] == "Device Port" and _tc["origin_netport_fk"] is not None:
                origin_int = self.d42_port_map[_tc["origin_netport_fk"]]["port"]
                origin_dev = self.d42_port_map[_tc["origin_netport_fk"]]["device"]
            if _tc["end_point_type"] == "Device Port" and _tc["end_point_netport_fk"] is not None:
                endpoint_int = self.d42_port_map[_tc["end_point_netport_fk"]]["port"]
                endpoint_dev = self.d42_port_map[_tc["end_point_netport_fk"]]["device"]
            if _tc["origin_type"] == "Patch panel port" and _tc["origin_patchpanelport_fk"] is not None:
                origin_int = ppanel_ports[_tc["origin_patchpanelport_fk"]]["number"]
                origin_dev = ppanel_ports[_tc["origin_patchpanelport_fk"]]["name"]
            if _tc["end_point_type"] == "Patch panel port" and _tc["end_point_patchpanelport_fk"] is not None:
                origin_int = ppanel_ports[_tc["end_point_patchpanelport_fk"]]["number"]
                origin_dev = ppanel_ports[_tc["end_point_patchpanelport_fk"]]["name"]
            new_circuit = self.circuit(
                circuit_id=_tc["circuit_id"],
                provider=self.d42_vendor_map[_tc["vendor_fk"]]["name"],
                notes=_tc["notes"],
                type=_tc["type_name"],
                status=get_circuit_status(_tc["status"]),
                install_date=_tc["turn_on_date"] if _tc.get("turn_on_date") else _tc["provision_date"],
                origin_int=origin_int if origin_int else None,
                origin_dev=origin_dev if origin_dev else None,
                endpoint_int=endpoint_int if endpoint_int else None,
                endpoint_dev=endpoint_dev if endpoint_dev else None,
                bandwidth=name_to_bits(f"{_tc['bandwidth']}{_tc['unit'].capitalize()}") / 1000,
                tags=_tc["tags"].split(",") if _tc.get("tags") else [],
                uuid=None,
            )
            self.add(new_circuit)
            # Add Connection from A side connection Device to Circuit
            if origin_dev and origin_int:
                a_side_conn = self.conn(
                    src_device=origin_dev,
                    src_port=origin_int,
                    src_port_mac=self.d42_port_map[_tc["origin_netport_fk"]]["hwaddress"]
                    if _tc["origin_type"] == "Device"
                    else None,
                    src_type="interface" if _tc["origin_type"] == "Device Port" else "patch panel",
                    dst_device=_tc["circuit_id"],
                    dst_port=_tc["circuit_id"],
                    dst_type="circuit",
                    dst_port_mac=None,
                    tags=None,
                    uuid=None,
                )
                self.add(a_side_conn)
            # Add Connection from Z side connection Circuit to Device
            if endpoint_dev and endpoint_int:
                z_side_conn = self.conn(
                    src_device=_tc["circuit_id"],
                    src_port=_tc["circuit_id"],
                    src_type="circuit",
                    dst_device=endpoint_dev,
                    dst_port=endpoint_int,
                    dst_port_mac=self.d42_port_map[_tc["end_point_netport_fk"]]["hwaddress"]
                    if _tc["end_point_type"] == "Device"
                    else None,
                    dst_type="interface" if _tc["end_point_type"] == "Device Port" else "patch panel",
                    src_port_mac=None,
                    tags=None,
                    uuid=None,
                )
                self.add(z_side_conn)

    def check_dns(self):
        """Method to check if a Device has a DNS record and assign as primary if so."""
        for _device in self.store.get_all(model=dcim.Device):
            if not re.search(r"\s-\s\w+\s?\d+", _device.name) and not re.search(
                r"AP[A-F0-9]{4}\.[A-F0-9]{4}.[A-F0-9]{4}", _device.name
            ):
                self.set_primary_from_dns(dev_name=_device.name, diffsync=self.job)
            else:
                if self.job.kwargs.get("debug"):
                    self.job.log_warning(message=f"Skipping {_device.name} due to invalid Device name.")
                continue

    def get_management_intf(self, dev_name: str, diffsync=None):
        """Method to find a Device's management interface or create one if one doesn't exist.

        Args:
            dev_name (str): Name of Device to find Management interface.
            diffsync (object, optional): DiffSync object for handling interactions with Job, such as logging. Defaults to None.

        Returns:
            Port: DiffSyncModel Port object that's assumed to be Management interface if found. False if not found.
        """
        try:
            _intf = self.get(self.port, {"device": dev_name, "name": "mgmt0"})
        except ObjectNotFound:
            try:
                _intf = self.get(self.port, {"device": dev_name, "name": "management"})
            except ObjectNotFound:
                try:
                    _intf = self.get(self.port, {"device": dev_name, "name": "management0"})
                except ObjectNotFound:
                    try:
                        _intf = self.get(self.port, {"device": dev_name, "name": "Management"})
                    except ObjectNotFound:
                        return False
        return _intf

    def add_management_interface(self, dev_name: str, diffsync=None):
        """Method to add a Management interface DiffSyncModel object.

        Args:
            dev_name (str): Name of Device to find Management interface.
            diffsync (object, optional): Diffsync object for handling interactions with Job, such as logging. Defaults to None.
        """
        _intf = self.port(
            name="Management",
            device=dev_name,
            type="other",
            enabled=True,
            description="Interface added by script for Management of device using DNS A record.",
            mode="access",
            mtu=None,
            mac_addr=None,
            custom_fields=None,
            tags=None,
            uuid=None,
        )
        try:
            self.add(_intf)
            _device = self.get(self.device, dev_name)
            _device.add_child(_intf)
            return _intf
        except ObjectAlreadyExists as err:
            diffsync.log_warning(message=f"Management interface for {dev_name} already exists. {err}")

    def set_primary_from_dns(self, dev_name: str, diffsync=None):
        """Method to resolve Device FQDNs A records into an IP and set primary IP for that Device to it if found.

            Checks if `use_dns` setting variable is `True`.

        Args:
            dev_name (str): Name of Device to perform DNS query on.
            diffsync (object, optional): Diffsync object for handling interactions with Job, such as logging. Defaults to None.
        """
        _devname = re.search(r"[a-zA-Z0-9\.\/\?\:\-_=#]+\.[a-zA-Z]{2,6}", dev_name)
        if _devname:
            _devname = _devname.group()
        else:
            return ""
        _a_record = get_dns_a_record(dev_name=_devname)
        if _a_record:
            _ip = self.find_ipaddr(address=_a_record)
            mgmt_intf = self.get_management_intf(dev_name=dev_name)
            if _ip is False:
                if not mgmt_intf:
                    mgmt_intf = self.add_management_interface(dev_name=dev_name, diffsync=diffsync)
                self.add_ipaddr(address=f"{_a_record}/32", dev_name=dev_name, interface=mgmt_intf.name)
            else:
                if mgmt_intf and _ip.device != dev_name:
                    _ip.device = dev_name
                    _ip.interface = mgmt_intf.name
                    _ip.primary = True
                elif _ip.device == dev_name:
                    _ip.primary = True

    def find_ipaddr(self, address: str):
        """Method to find IPAddress DiffSyncModel object."""
        if ":" in address:
            bits = 128
        else:
            bits = 32

        while bits > 0:
            _addr = f"{address}/{bits}"
            for _vrf in self.get_all("vrf"):
                try:
                    return self.get(self.ipaddr, {"address": _addr, "vrf": _vrf.name})
                except ObjectNotFound:
                    pass
            else:
                try:
                    return self.get(self.ipaddr, {"address": _addr, "vrf": None})
                except ObjectNotFound:
                    bits = bits - 1
        else:
            return False

    def add_ipaddr(self, address: str, dev_name: str, interface: str):
        """Method to add IPAddress DiffSyncModel object if one isn't found.

        Used in conjunction with the `use_dns` feature.
        """
        _ip = self.ipaddr(
            address=address,
            available=False,
            device=dev_name,
            interface=interface,
            primary=True,
            label=None,
            vrf=None,
            tags=None,
            custom_fields=None,
            uuid=None,
        )
        self.add(_ip)

    def load_patch_panels_and_ports(self):
        """Load Device42 Patch Panels and Patch Panel Ports."""
        panels = self.device42.get_patch_panels()
        for panel in panels:
            _building, _room, _rack = None, None, None
            if PLUGIN_CFG.get("customer_is_facility") and panel["customer_fk"] is not None:
                _building = self.d42_customer_map[panel["customer_fk"]]["name"]
            if panel["building_fk"] is not None:
                _building = self.d42_building_map[panel["building_fk"]]["name"]
            elif panel["calculated_building_fk"] is not None:
                _building = self.d42_building_map[panel["calculated_building_fk"]]["name"]
            if panel["room_fk"] is not None:
                _room = self.d42_room_map[panel["room_fk"]]["name"]
            elif panel["calculated_room_fk"] is not None:
                _room = self.d42_room_map[panel["calculated_room_fk"]]["name"]
            if panel["rack_fk"] is not None:
                _rack = self.d42_rack_map[panel["rack_fk"]]["name"]
            elif panel["calculated_rack_fk"] is not None:
                _rack = self.d42_rack_map[panel["rack_fk"]]["name"]
            if _building is None and _room is None and _rack is None:
                if self.job.kwargs.get("debug"):
                    self.job.log_debug(
                        message=f"Unable to determine Site, Room, or Rack for patch panel {panel['name']} so it will NOT be imported."
                    )
                continue
            try:
                new_hw = self.get(self.hardware, panel["model_name"])
            except ObjectNotFound:
                new_hw = self.hardware(
                    name=panel["model_name"],
                    manufacturer=panel["vendor"],
                    size=panel["size"] if panel.get("size") else 1.0,
                    depth="Half Depth" if panel["depth"] == 2 else "Full Depth",
                    part_number=None,
                    custom_fields=None,
                    uuid=None,
                )
                self.add(new_hw)
            try:
                new_pp = self.get(self.patchpanel, panel["name"])
            except ObjectNotFound:
                new_pp = self.patchpanel(
                    name=panel["name"],
                    in_service=panel["in_service"],
                    vendor=panel["vendor"],
                    model=panel["model_name"],
                    size=panel["size"] if panel.get("size") else 1.0,
                    depth="Half Depth" if panel["depth"] == 2 else "Full Depth",
                    position=panel["position"],
                    orientation="front" if panel.get("orientation") == "Front" else "rear",
                    num_ports=panel["number_of_ports"],
                    rack=_rack,
                    serial_no=panel["serial_no"],
                    building=_building,
                    room=_room,
                    uuid=None,
                )
                self.add(new_pp)
                ind = 1
                while ind <= panel["number_of_ports"]:
                    if "LC" in panel["port_type"]:
                        port_type = "lc"
                    elif "FC" in panel["port_type"]:
                        port_type = "fc"
                    else:
                        port_type = "8p8c"
                    front_intf = self.patchpanelfrontport(
                        name=f"{ind}",
                        patchpanel=panel["name"],
                        port_type=port_type,
                        uuid=None,
                    )
                    rear_intf = self.patchpanelrearport(
                        name=f"{ind}",
                        patchpanel=panel["name"],
                        port_type=port_type,
                        uuid=None,
                    )
                    try:
                        self.add(front_intf)
                        self.add(rear_intf)
                    except ObjectAlreadyExists as err:
                        if self.job.kwargs.get("debug"):
                            self.job.log_warning(
                                message=f"Patch panel port {ind} for {panel['name']} is already loaded. {err}"
                            )
                    ind = ind + 1

    def load(self):
        """Load data from Device42."""
        self.load_buildings()
        self.load_rooms()
        self.load_racks()
        self.load_vendors()
        self.load_hardware_models()
        self.load_vrfgroups()
        self.load_vlans()
        self.load_subnets()
        self.load_devices_and_clusters()
        self.load_ports()
        self.load_ip_addresses()
        if is_truthy(PLUGIN_CFG.get("use_dns")):
            self.check_dns()
        self.load_connections()
        self.load_providers_and_circuits()
        self.load_patch_panels_and_ports()