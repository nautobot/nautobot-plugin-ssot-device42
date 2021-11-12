"""DiffSyncModel DCIM subclasses for Nautobot Device42 data sync."""

import re
from decimal import Decimal
from typing import List, Optional, Union

from diffsync import DiffSyncModel
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from nautobot.circuits.models import Circuit as NautobotCircuit
from nautobot.circuits.models import CircuitTermination as NautobotCT
from nautobot.core.settings_funcs import is_truthy
from nautobot.dcim.models import Cable as NautobotCable
from nautobot.dcim.models import Device as NautobotDevice
from nautobot.dcim.models import DeviceType as NautobotDeviceType
from nautobot.dcim.models import Interface as NautobotInterface
from nautobot.dcim.models import Manufacturer as NautobotManufacturer
from nautobot.dcim.models import Site as NautobotSite
from nautobot.dcim.models import VirtualChassis as NautobotVC
from nautobot.dcim.models.racks import Rack as NautobotRack
from nautobot.dcim.models.racks import RackGroup as NautobotRackGroup
from nautobot.extras.choices import CustomFieldTypeChoices
from nautobot.extras.models import CustomField
from nautobot.extras.models import Status as NautobotStatus
from nautobot.ipam.models import VLAN as NautobotVLAN
from nautobot_ssot_device42.constant import DEFAULTS, INTF_SPEED_MAP, PLUGIN_CFG
from nautobot_ssot_device42.utils import device42, nautobot


class Building(DiffSyncModel):
    """Device42 Building model."""

    _modelname = "building"
    _identifiers = ("name",)
    _shortname = ("name",)
    _attributes = ("address", "latitude", "longitude", "contact_name", "contact_phone", "tags", "custom_fields")
    _children = {"room": "rooms"}
    name: str
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    contact_name: Optional[str]
    contact_phone: Optional[str]
    rooms: List["Room"] = list()
    tags: Optional[List[str]]
    custom_fields: Optional[List[dict]]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Site object in Nautobot."""
        def_site_status = NautobotStatus.objects.get(name=DEFAULTS.get("site_status"))
        new_site = NautobotSite(
            name=ids["name"],
            slug=slugify(ids["name"]),
            status=def_site_status,
            physical_address=attrs["address"] if attrs.get("address") else "",
            latitude=round(Decimal(attrs["latitude"] if attrs["latitude"] else 0.0), 6),
            longitude=round(Decimal(attrs["longitude"] if attrs["longitude"] else 0.0), 6),
            contact_name=attrs["contact_name"] if attrs.get("contact_name") else "",
            contact_phone=attrs["contact_phone"] if attrs.get("contact_phone") else "",
        )
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
                new_site.tags.add(_tag)
            _facility = device42.get_facility(tags=attrs["tags"], diffsync=diffsync)
            if _facility:
                new_site.facility = _facility.upper()
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotSite).id)
                new_site.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        new_site.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Site object in Nautobot."""
        _site = NautobotSite.objects.get(slug=slugify(self.name))
        if attrs.get("address"):
            _site.physical_address = attrs["address"]
        if attrs.get("latitude"):
            _site.latitude = round(Decimal(attrs["latitude"]), 6)
        if attrs.get("longitude"):
            _site.longitude = round(Decimal(attrs["longitude"]), 6)
        if attrs.get("contact_name"):
            _site.contact_name = attrs["contact_name"]
        if attrs.get("contact_phone"):
            _site.contact_phone = attrs["contact_phone"]
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
                _site.tags.add(_tag)
            _facility = device42.get_facility(tags=attrs["tags"], diffsync=self.diffsync)
            if _facility:
                _site.facility = _facility.upper()
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotSite).id)
                _site.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _site.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Site object from Nautobot.

        Because Site has a direct relationship with many other objects it can't be deleted before anything else.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"Site {self.name} will be deleted.")
        super().delete()
        site = NautobotSite.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["site"].append(site)  # pylint: disable=protected-access
        return self


class Room(DiffSyncModel):
    """Device42 Room model."""

    _modelname = "room"
    _identifiers = ("name", "building")
    _shortname = ("name",)
    _attributes = ("notes", "custom_fields")
    _children = {"rack": "racks"}
    name: str
    building: str
    notes: Optional[str]
    racks: List["Rack"] = list()
    custom_fields: Optional[List[dict]]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create RackGroup object in Nautobot."""
        new_rg = NautobotRackGroup(
            name=ids["name"],
            slug=slugify(ids["name"]),
            site=NautobotSite.objects.get(name=ids["building"]),
            description=attrs["notes"] if attrs.get("notes") else "",
        )
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotRackGroup).id)
                new_rg.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        new_rg.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update RackGroup object in Nautobot."""
        _rg = NautobotRackGroup.objects.get(name=self.name, site__name=self.building)
        if attrs.get("notes"):
            _rg.description = attrs["notes"]
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotRackGroup).id)
                _rg.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _rg.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete RackGroup object from Nautobot.

        Because RackGroup has a direct relationship to Rack objects it can't be deleted before any Racks.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"RackGroup {self.name} will be deleted.")
        super().delete()
        rackgroup = NautobotRackGroup.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["rackgroup"].append(rackgroup)  # pylint: disable=protected-access
        return self


class Rack(DiffSyncModel):
    """Device42 Rack model."""

    _modelname = "rack"
    _identifiers = ("name", "building", "room")
    _shortname = ("name",)
    _attributes = ("height", "numbering_start_from_bottom", "tags", "custom_fields")
    _children = {}
    name: str
    building: str
    room: str
    height: int
    numbering_start_from_bottom: str
    tags: Optional[List[str]]
    custom_fields: Optional[List[dict]]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Rack object in Nautobot."""
        _site = NautobotSite.objects.get(name=ids["building"])
        _rg = NautobotRackGroup.objects.get(name=ids["room"], site__name=ids["building"])
        new_rack = NautobotRack(
            name=ids["name"],
            site=_site,
            group=_rg,
            status=NautobotStatus.objects.get(name=DEFAULTS.get("rack_status")),
            u_height=attrs["height"] if attrs.get("height") else 1,
            desc_units=not (is_truthy(attrs["numbering_start_from_bottom"])),
        )
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
                new_rack.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotRack).id)
                new_rack.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        new_rack.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Rack object in Nautobot."""
        _rack = NautobotRack.objects.get(name=self.name, group__name=self.room, site__name=self.building)
        if attrs.get("height"):
            _rack.u_height = attrs["height"]
        if attrs.get("numbering_start_from_bottom"):
            _rack.desc_units = not (is_truthy(attrs["numbering_start_from_bottom"]))
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
                _rack.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotRack).id)
                _rack.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _rack.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Rack object from Nautobot.

        Because Rack has a direct relationship with Devices it can't be deleted before they are.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"Rack {self.name} will be deleted.")
        super().delete()
        rack = NautobotRack.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["rack"].append(rack)  # pylint: disable=protected-access
        return self


class Vendor(DiffSyncModel):
    """Device42 Vendor model."""

    _modelname = "vendor"
    _identifiers = ("name",)
    _shortname = ("name",)
    _attributes = ("custom_fields",)
    _children = {}
    name: str
    custom_fields: Optional[List[dict]]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Manufacturer object in Nautobot."""
        diffsync.job.log_debug(f"Creating Manufacturer {ids['name']}")
        try:
            NautobotManufacturer.objects.get(slug=slugify(ids["name"]))
        except NautobotManufacturer.DoesNotExist:
            new_manu = NautobotManufacturer(
                name=ids["name"],
                slug=slugify(ids["name"]),
            )
            if attrs.get("custom_fields"):
                for _cf in attrs["custom_fields"]:
                    _cf_dict = {
                        "name": slugify(_cf["key"]),
                        "type": CustomFieldTypeChoices.TYPE_TEXT,
                        "label": _cf["key"],
                    }
                    field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                    field.content_types.add(ContentType.objects.get_for_model(NautobotManufacturer).id)
                    new_manu.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
            new_manu.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Manufacturer object in Nautobot."""
        _manu = NautobotManufacturer.objects.get(name=self.name)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotManufacturer).id)
                _manu.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _manu.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Manufacturer object from Nautobot.

        Because Manufacturer has a direct relationship with DeviceTypes and other objects it can't be deleted before them.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"Manufacturer {self.name} will be deleted.")
        super().delete()
        _manu = NautobotManufacturer.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["manufacturer"].append(_manu)  # pylint: disable=protected-access
        return self


class Hardware(DiffSyncModel):
    """Device42 Hardware model."""

    _modelname = "hardware"
    _identifiers = ("name",)
    _shortname = ("name",)
    _attributes = ("manufacturer", "size", "depth", "part_number", "custom_fields")
    _children = {}
    name: str
    manufacturer: str
    size: float
    depth: Optional[str]
    part_number: Optional[str]
    custom_fields: Optional[List[dict]]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create DeviceType object in Nautobot."""
        diffsync.job.log_debug(f"Creating DeviceType {ids['name']}")
        try:
            NautobotDeviceType.objects.get(slug=slugify(ids["name"]))
        except NautobotDeviceType.DoesNotExist:
            new_dt = NautobotDeviceType(
                model=ids["name"],
                slug=slugify(ids["name"]),
                manufacturer=NautobotManufacturer.objects.get(slug=slugify(attrs["manufacturer"])),
                part_number=attrs["part_number"] if attrs.get("part_number") else "",
                u_height=int(attrs["size"]) if attrs.get("size") else 1,
                is_full_depth=bool(attrs.get("depth") == "Full Depth"),
            )
            if attrs.get("custom_fields"):
                for _cf in attrs["custom_fields"]:
                    _cf_dict = {
                        "name": slugify(_cf["key"]),
                        "type": CustomFieldTypeChoices.TYPE_TEXT,
                        "label": _cf["key"],
                    }
                    field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                    field.content_types.add(ContentType.objects.get_for_model(NautobotDeviceType).id)
                    new_dt.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
            new_dt.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update DeviceType object in Nautobot."""
        _dt = NautobotDeviceType.objects.get(model=self.name)
        if attrs.get("manufacturer"):
            _dt.manufacturer = NautobotManufacturer.objects.get(slug=slugify(attrs["manufacturer"]))
        if attrs.get("part_number"):
            _dt.part_number = attrs["part_number"]
        if attrs.get("size"):
            _dt.u_height = int(attrs["size"])
        if attrs.get("depth"):
            _dt.is_full_depth = bool(attrs["depth"] == "Full Depth")
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotDeviceType).id)
                _dt.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _dt.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete DeviceType object from Nautobot.

        Because DeviceType has a direct relationship with Devices it can't be deleted before all Devices are.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"DeviceType {self.name} will be deleted.")
        super().delete()
        _dt = NautobotDeviceType.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["device_type"].append(_dt)  # pylint: disable=protected-access
        return self


class Cluster(DiffSyncModel):
    """Device42 Cluster model."""

    _modelname = "cluster"
    _identifiers = ("name",)
    _shortname = ("name",)
    _attributes = ("members", "tags", "custom_fields")
    _children = {}
    name: str
    members: Optional[List[str]]
    tags: Optional[List[str]]
    custom_fields: Optional[List[dict]]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Virtual Chassis object in Nautobot.

        As the master node of the VC needs to be a regular Device, we'll create that and then the VC.
        Member devices will be added to VC at Device creation.
        """
        diffsync.job.log_debug(f"Creating VC Master Device {ids['name']}.")
        new_vc = NautobotVC(
            name=ids["name"],
        )
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
                new_vc.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotVC).id)
                new_vc.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        new_vc.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Virtual Chassis object in Nautobot."""
        _vc = NautobotVC.objects.get(name=self.name)
        if attrs.get("members"):
            for _member in attrs["members"]:
                try:
                    device = NautobotDevice.objects.get(name=_member)
                    device.virtual_chassis = _vc
                    switch_pos = re.search(r".+-\s([sS]witch)\s?(?P<pos>\d+)", _member)
                    node_pos = re.search(r".+-\s([nN]ode)\s?(?P<pos>\d+)", _member)
                    if switch_pos or node_pos:
                        if switch_pos:
                            position = int(switch_pos.group("pos"))
                        if node_pos:
                            position = int(node_pos.group("pos")) + 1
                    else:
                        position = len(NautobotDevice.objects.filter(virtual_chassis__name=self.name))
                    device.vc_position = position + 1
                except NautobotDevice.DoesNotExist as err:
                    if PLUGIN_CFG.get("verbose_debug"):
                        self.diffsync.job.log_warning(f"Unable to find {_member} to add to VC {self.name} {err}")
                    continue
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
                _vc.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotVC).id)
                _vc.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _vc.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Virtual Chassis object from Nautobot.

        Because Virtual Chassis has a direct relationship with Devices it can't be deleted before they are.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"Virtual Chassis {self.name} will be deleted.")
        super().delete()
        _cluster = NautobotVC.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["cluster"].append(_cluster)  # pylint: disable=protected-access
        return self


class Device(DiffSyncModel):
    """Device42 Device model."""

    _modelname = "device"
    _identifiers = ("name",)
    _shortname = ("name",)
    _attributes = (
        "building",
        "room",
        "rack",
        "rack_position",
        "rack_orientation",
        "hardware",
        "os",
        "in_service",
        "serial_no",
        "tags",
        "cluster_host",
        "master_device",
        "custom_fields",
    )
    _children = {"port": "interfaces"}
    name: str
    building: Optional[str]
    room: Optional[str]
    rack: Optional[str]
    rack_position: Optional[float]
    rack_orientation: Optional[str]
    hardware: str
    os: Optional[str]
    in_service: Optional[bool]
    interfaces: Optional[List["Port"]] = list()
    serial_no: Optional[str]
    tags: Optional[List[str]]
    cluster_host: Optional[str]
    master_device: bool
    custom_fields: Optional[List[dict]]

    @classmethod
    def _get_site(cls, diffsync, ids, attrs):
        if attrs.get("rack") and attrs.get("room"):
            try:
                _site = NautobotRack.objects.get(name=attrs["rack"], group__name=attrs["room"]).site
                return _site
            except NautobotRack.DoesNotExist as err:
                diffsync.job.log_debug(f"Unable to find Site by Rack/Room. {attrs['rack']} {attrs['room']} {err}")
        if attrs.get("building"):
            try:
                _site = NautobotSite.objects.get(slug=attrs["building"])
                return _site
            except NautobotSite.DoesNotExist as err:
                diffsync.job.log_debug(f"Unable to find Site {attrs['building']}. {err}")
        else:
            diffsync.job.log_debug(f"Device {ids['name']} is missing Building or Customer so can't determine Site.")
            return False

    @classmethod
    def create(cls, diffsync, ids, attrs):  # pylint: disable=inconsistent-return-statements
        """Create Device object in Nautobot."""
        if attrs["in_service"]:
            _status = NautobotStatus.objects.get(name="Active")
        else:
            _status = NautobotStatus.objects.get(name="Offline")
        if attrs.get("building"):
            diffsync.job.log_debug(f"Creating device {ids['name']}.")
            if attrs.get("tags") and len(attrs["tags"]) > 0:
                _role = nautobot.verify_device_role(device42.find_device_role_from_tags(tag_list=attrs["tags"]))
            else:
                _role = nautobot.verify_device_role(role_name=DEFAULTS.get("device_role"))
            try:
                _dt = NautobotDeviceType.objects.get(model=attrs["hardware"])
                _site = cls._get_site(diffsync, ids, attrs)
                if not _site:
                    diffsync.job.log_debug(f"Can't create {ids['name']} as unable to determine Site.")
                    return None
                new_device = NautobotDevice(
                    name=ids["name"][:64],
                    status=_status,
                    site=_site,
                    device_type=_dt,
                    device_role=_role,
                    serial=attrs["serial_no"] if attrs.get("serial_no") else "",
                )
                if attrs.get("rack"):
                    new_device.rack = NautobotRack.objects.get(name=attrs["rack"], group__name=attrs["room"])
                    new_device.position = int(attrs["rack_position"]) if attrs["rack_position"] else None
                    new_device.face = attrs["rack_orientation"] if attrs["rack_orientation"] else "front"
                if attrs.get("os"):
                    new_device.platform = nautobot.verify_platform(
                        platform_name=attrs["os"],
                        manu=NautobotDeviceType.objects.get(model=attrs["hardware"]).manufacturer,
                    )
                new_device.validated_save()
                if attrs.get("cluster_host"):
                    try:
                        _vc = NautobotVC.objects.get(name=attrs["cluster_host"])
                        new_device.virtual_chassis = _vc
                        if attrs.get("master_device") and attrs["master_device"]:
                            new_device.vc_position = 1
                            new_device.validated_save()
                            _vc.master = new_device
                            _vc.validated_save()
                        else:
                            switch_pos = re.search(r".+-\s([sS]witch)\s?(?P<pos>\d+)", ids["name"])
                            node_pos = re.search(r".+-\s([nN]ode)\s?(?P<pos>\d+)", ids["name"])
                            if switch_pos or node_pos:
                                if switch_pos:
                                    position = int(switch_pos.group("pos"))
                                if node_pos:
                                    position = int(node_pos.group("pos")) + 1
                            else:
                                position = len(
                                    NautobotDevice.objects.filter(virtual_chassis__name=attrs["cluster_host"])
                                )
                            new_device.vc_position = position + 1
                    except NautobotVC.DoesNotExist as err:
                        if PLUGIN_CFG.get("verbose_debug"):
                            diffsync.job.log_warning(f"Unable to find VC {attrs['cluster_host']} {err}")
                if attrs.get("tags"):
                    for _tag in nautobot.get_tags(attrs["tags"]):
                        new_device.tags.add(_tag)
                if attrs.get("custom_fields"):
                    for _cf in attrs["custom_fields"]:
                        _cf_dict = {
                            "name": slugify(_cf["key"]),
                            "type": CustomFieldTypeChoices.TYPE_TEXT,
                            "label": _cf["key"],
                        }
                        field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                        field.content_types.add(ContentType.objects.get_for_model(NautobotDevice).id)
                        new_device.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
                new_device.validated_save()
                return super().create(diffsync=diffsync, ids=ids, attrs=attrs)
            except NautobotRack.DoesNotExist:
                diffsync.job.log_debug(f"Unable to find matching Rack {attrs.get('rack')} for {_site.name}")
            except NautobotDeviceType.DoesNotExist:
                diffsync.job.log_debug(f"Unable to find matching DeviceType {attrs['hardware']} for {ids['name']}.")
        else:
            diffsync.job.log_debug(f"Device {ids['name']} is missing a Building and won't be created.")

    def update(self, attrs):
        """Update Device object in Nautobot."""
        _dev = NautobotDevice.objects.get(name=self.name)
        if attrs.get("building"):
            _dev.site = self._get_site(diffsync=self.diffsync, ids=self.get_identifiers(), attrs=attrs)
        if attrs.get("rack") and attrs.get("room"):
            try:
                _dev.site = self._get_site(diffsync=self.diffsync, ids=self.get_identifiers(), attrs=attrs)
                _dev.rack = NautobotRack.objects.get(name=attrs["rack"], group__name=attrs["room"])
                if _dev.site.name == _dev.rack.site.name:
                    if attrs.get("rack_position"):
                        _dev.position = int(attrs["rack_position"])
                    else:
                        _dev.position = None
                    if attrs.get("rack_orientation"):
                        _dev.face = attrs["rack_orientation"]
                    else:
                        _dev.face = "rear"
            except NautobotRack.DoesNotExist as err:
                if PLUGIN_CFG.get("verbose_debug"):
                    self.diffsync.job.log_warning(f"Unable to find rack {attrs['rack']} in {attrs['room']} {err}")
        if attrs.get("hardware"):
            _dt = NautobotDeviceType.objects.get(model=attrs["hardware"])
            _dev.device_type = _dt
        if attrs.get("os"):
            if attrs.get("hardware"):
                _hardware = NautobotDeviceType.objects.get(model=attrs["hardware"])
            else:
                _hardware = _dev.device_type
            _dev.platform = nautobot.verify_platform(
                platform_name=attrs["os"],
                manu=_hardware.manufacturer,
            )
        if attrs.get("in_service"):
            if attrs["in_service"]:
                _status = NautobotStatus.objects.get(name="Active")
            else:
                _status = NautobotStatus.objects.get(name="Offline")
            _dev.status = _status
        if attrs.get("serial_no"):
            _dev.serial = attrs["serial_no"]
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
                _dev.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotDevice).id)
                _dev.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        # ensure that VC Master Device is set to that
        if attrs.get("cluster_host") or attrs.get("master_device"):
            if attrs.get("cluster_host"):
                _clus_host = attrs["cluster_host"]
            else:
                _clus_host = self.cluster_host
            try:
                _vc = NautobotVC.objects.get(name=_clus_host)
                _dev.virtual_chassis = _vc
                if attrs.get("master_device") and attrs["master_device"]:
                    _dev.vc_position = 1
                    _dev.validated_save()
                    _vc.master = _dev
                    _vc.validated_save()
                else:
                    # switch devices start at 1 so can use that as position
                    switch_pos = re.search(r".+-\s([sS]witch)\s?(?P<pos>\d+)", self.name)
                    # node devices start at 0 so need to be incremented by 2 instead of 1
                    node_pos = re.search(r".+-\s([nN]ode)\s?(?P<pos>\d+)", self.name)
                    if switch_pos or node_pos:
                        if switch_pos:
                            position = int(switch_pos.group("pos"))
                        if node_pos:
                            position = int(node_pos.group("pos")) + 1
                    else:
                        position = len(NautobotDevice.objects.filter(virtual_chassis__name=_clus_host))
                    _dev.vc_position = position + 1
            except NautobotVC.DoesNotExist as err:
                if PLUGIN_CFG.get("verbose_debug"):
                    self.diffsync.job.log_warning(f"Unable to find VC {_clus_host} {err}")
        _dev.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Device object from Nautobot.

        Because Device has a direct relationship with Ports and IP Addresses it can't be deleted before they are.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"Device {self.name} will be deleted.")
        super().delete()
        _dev = NautobotDevice.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["device"].append(_dev)  # pylint: disable=protected-access
        return self


class Port(DiffSyncModel):
    """Device42 Port model."""

    _modelname = "port"
    _identifiers = ("device", "name")
    _shortname = ("name",)
    _attributes = ("enabled", "mtu", "description", "mac_addr", "type", "mode", "tags", "vlans", "custom_fields")
    _children = {}
    name: str
    device: str
    enabled: Optional[bool]
    mtu: Optional[int]
    description: Optional[str]
    mac_addr: Optional[str]
    type: str
    tags: Optional[List[str]]
    mode: Optional[str]
    vlans: Optional[List[dict]] = list()
    custom_fields: Optional[List[dict]]

    @classmethod
    def create(cls, diffsync, ids, attrs):  # pylint: disable=inconsistent-return-statements
        """Create Interface object in Nautobot."""
        diffsync.job.log_debug(f"Creating Interface {ids['name']} for {ids['device']}.")
        try:
            if ids.get("device"):
                _dev = NautobotDevice.objects.get(name=ids["device"])
                new_intf = NautobotInterface(
                    name=ids["name"],
                    device=_dev,
                    enabled=is_truthy(attrs["enabled"]),
                    mtu=attrs["mtu"] if attrs.get("mtu") else 1500,
                    description=attrs["description"],
                    type=attrs["type"],
                    mac_address=attrs["mac_addr"][:12] if attrs.get("mac_addr") else None,
                    mode=attrs["mode"],
                )
                if attrs.get("tags"):
                    for _tag in nautobot.get_tags(attrs["tags"]):
                        new_intf.tags.add(_tag)
                if attrs.get("custom_fields"):
                    for _cf in attrs["custom_fields"]:
                        _cf_dict = {
                            "name": slugify(_cf["key"]),
                            "type": CustomFieldTypeChoices.TYPE_TEXT,
                            "label": _cf["key"],
                        }
                        field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                        field.content_types.add(ContentType.objects.get_for_model(NautobotInterface).id)
                        new_intf.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
                new_intf.validated_save()
                try:
                    if attrs.get("vlans"):
                        if attrs["mode"] == "access" and len(attrs["vlans"]) == 1:
                            _vlan = attrs["vlans"][0]
                            vlan_found = NautobotVLAN.objects.filter(
                                name=_vlan["vlan_name"], vid=_vlan["vlan_id"], site=_dev.site
                            )
                            if vlan_found:
                                new_intf.untagged_vlan = vlan_found[0]
                        else:
                            tagged_vlans = []
                            for _vlan in attrs["vlans"]:
                                tagged_vlan = NautobotVLAN.objects.filter(
                                    name=_vlan["vlan_name"], vid=_vlan["vlan_id"], site=_dev.site
                                )
                                if not tagged_vlan:
                                    tagged_vlan = NautobotVLAN.objects.filter(
                                        name=_vlan["vlan_name"], vid=_vlan["vlan_id"]
                                    )
                                if tagged_vlan:
                                    tagged_vlans.append(tagged_vlan[0])
                            new_intf.tagged_vlans.set(tagged_vlans)
                except NautobotVLAN.DoesNotExist as err:
                    diffsync.job.log_debug(f"{err}: {_vlan['vlan_name']} {_vlan['vlan_id']} ")
                new_intf.validated_save()
                return super().create(ids=ids, diffsync=diffsync, attrs=attrs)
        except NautobotDevice.DoesNotExist as err:
            if PLUGIN_CFG.get("verbose_debug"):
                diffsync.job.log_warning(f"{ids['name']} doesn't exist. {err}")

    def update(self, attrs):
        """Update Interface object in Nautobot."""
        _port = NautobotInterface.objects.get(name=self.name, device__name=self.device)
        if attrs.get("enabled"):
            _port.enabled = is_truthy(attrs["enabled"])
        if attrs.get("mtu"):
            _port.mtu = attrs["mtu"]
        if attrs.get("description"):
            _port.description = attrs["description"]
        if attrs.get("mac_addr"):
            _port.mac_address = attrs["mac_addr"][:12]
        if attrs.get("type"):
            _port.type = attrs["type"]
        if attrs.get("mode"):
            _port.mode = attrs["mode"]
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
                _port.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotInterface).id)
                _port.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        if attrs.get("vlans"):
            if attrs.get("mode"):
                _mode = attrs["mode"]
            else:
                _mode = self.mode
            if _mode == "access" and len(attrs["vlans"]) == 1:
                _vlan = attrs["vlans"][0]
                vlan_found = NautobotVLAN.objects.filter(
                    name=_vlan["vlan_name"],
                    vid=_vlan["vlan_id"],
                    site=NautobotDevice.objects.get(name=self.device).site,
                )
                if vlan_found:
                    _port.untagged_vlan = vlan_found[0]
            else:
                tagged_vlans = []
                for _vlan in attrs["vlans"]:
                    tagged_vlan = NautobotVLAN.objects.filter(
                        name=_vlan["vlan_name"],
                        vid=_vlan["vlan_id"],
                        site=NautobotDevice.objects.get(name=self.device).site,
                    )
                    if not tagged_vlan:
                        tagged_vlan = NautobotVLAN.objects.filter(name=_vlan["vlan_name"], vid=_vlan["vlan_id"])
                    if tagged_vlan:
                        tagged_vlans.append(tagged_vlan[0])
                _port.tagged_vlans.set(tagged_vlans)
        _port.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Interface object from Nautobot.

        Because Interface has a direct relationship with Cables and IP Addresses it can't be deleted before they are.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        if PLUGIN_CFG.get("verbose_debug"):
            self.diffsync.job.log_warning(f"Interface {self.name} for {self.device} will be deleted.")
        super().delete()
        _dev = NautobotInterface.objects.get(
            name=self.get_identifiers()["name"], device__name=self.get_identifiers()["device"]
        )
        self.diffsync._objects_to_delete["port"].append(_dev)  # pylint: disable=protected-access
        return self


class Connection(DiffSyncModel):
    """Device42 Connection model."""

    _modelname = "conn"
    _identifiers = ("src_device", "src_port", "src_port_mac", "dst_device", "dst_port", "dst_port_mac")
    _attributes = ("src_type", "dst_type")
    _children = {}

    src_device: str
    src_port: str
    src_type: str
    src_port_mac: Optional[str]
    dst_device: str
    dst_port: str
    dst_type: str
    dst_port_mac: Optional[str]
    tags: Optional[List[str]]

    @classmethod
    def create(cls, diffsync, ids, attrs):  # pylint: disable=inconsistent-return-statements
        """Create Cable object in Nautobot."""
        # Handle Circuit Terminations
        if attrs["src_type"] == "circuit" or attrs["dst_type"] == "circuit":
            new_cable = cls.get_circuit_connections(cls, diffsync=diffsync, ids=ids, attrs=attrs)
        elif attrs["src_type"] == "interface" and attrs["dst_type"] == "interface":
            new_cable = cls.get_device_connections(cls, diffsync=diffsync, ids=ids)
        if new_cable:
            new_cable.validated_save()
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def get_circuit_connections(self, diffsync, ids, attrs) -> Optional[NautobotCable]:
        """Method to create a Cable between a Circuit and a Device.

        Args:
            diffsync (obj): DiffSync job used for logging.
            ids (dict): Identifying attributes for the object.
            attrs (dict): Non-identifying attributes for the object.

        Returns:
            Optional[NautobotCable]: If the Interfaces are found and a cable is created, returns Cable else None.
        """
        _intf = None
        if attrs["src_type"] == "interface":
            try:
                _intf = NautobotInterface.objects.get(
                    device__name=self.get_dev_name(ids["src_device"]), name=ids["src_port"]
                )
                circuit = NautobotCircuit.objects.get(cid=ids["dst_device"])
            except NautobotInterface.DoesNotExist as err:
                if PLUGIN_CFG.get("verbose_debug"):
                    print(
                        f"Unable to find source port for {ids['src_device']}: {ids['src_port']} to connect to Circuit {ids['dst_device']} {err}"
                    )
                return None
            except NautobotCircuit.DoesNotExist as err:
                if PLUGIN_CFG.get("verbose_debug"):
                    print(f"Unable to find Circuit {ids['dst_device']} {err}")
                return None
        if attrs["dst_type"] == "interface":
            try:
                circuit = NautobotCircuit.objects.get(cid=ids["src_device"])
                _intf = NautobotInterface.objects.get(
                    device__name=self.get_dev_name(ids["dst_device"]), name=ids["dst_port"]
                )
            except NautobotInterface.DoesNotExist as err:
                if PLUGIN_CFG.get("verbose_debug"):
                    print(
                        f"Unable to find destination port for {ids['dst_device']}: {ids['dst_port']} to connect to Circuit {ids['src_device']} {err}"
                    )
                return None
            except NautobotCircuit.DoesNotExist as err:
                if PLUGIN_CFG.get("verbose_debug"):
                    print(f"Unable to find Circuit {ids['dst_device']} {err}")
                return None
        _ct = {
            "circuit": circuit,
            "site": _intf.device.site,
        }
        if attrs["src_type"] == "interface":
            _ct["term_side"] = "A"
        if attrs["dst_type"] == "interface":
            _ct["term_side"] = "Z"
        try:
            circuit_term = NautobotCT.objects.get(**_ct)
        except NautobotCT.DoesNotExist:
            circuit_term = NautobotCT(**_ct)
            circuit_term.port_speed = INTF_SPEED_MAP[_intf.type]
            circuit_term.validated_save()
        if _intf and not _intf.cable and not circuit_term.cable:
            new_cable = NautobotCable(
                termination_a_type=ContentType.objects.get(app_label="dcim", model="interface"),
                termination_a_id=_intf.id,
                termination_b_type=ContentType.objects.get(app_label="circuits", model="circuittermination"),
                termination_b_id=circuit_term.id,
                status=NautobotStatus.objects.get(name="Connected"),
                color=nautobot.get_random_color(),
            )
            new_cable.validated_save()

    def get_device_connections(self, diffsync, ids) -> Optional[NautobotCable]:
        """Method to create a Cable between two Devices.

        Args:
            diffsync (obj): DiffSync job used for logging.
            ids (dict): Identifying attributes for the object.

        Returns:
            Optional[NautobotCable]: If the Interfaces are found and a cable is created, returns Cable else None.
        """
        _src_port, _dst_port = None, None
        try:
            if ids.get("src_port_mac"):
                _src_port = NautobotInterface.objects.get(mac_address=ids["src_port_mac"])
        except NautobotInterface.DoesNotExist:
            try:
                _src_port = NautobotInterface.objects.get(
                    device__name=self.get_dev_name(ids["src_device"]), name=ids["src_port"]
                )
            except NautobotInterface.DoesNotExist as err:
                if PLUGIN_CFG.get("verbose_debug"):
                    diffsync.job.log_warning(
                        f"Unable to find source port for {ids['src_device']}: {ids['src_port']} {ids['src_port_mac']} {err}"
                    )
                return None
        try:
            if ids.get("dst_port_mac"):
                _dst_port = NautobotInterface.objects.get(mac_address=ids["dst_port_mac"])
        except NautobotInterface.DoesNotExist:
            try:
                _dst_port = NautobotInterface.objects.get(
                    device__name=self.get_dev_name(ids["dst_device"]), name=ids["dst_port"]
                )
            except NautobotInterface.DoesNotExist:
                if PLUGIN_CFG.get("verbose_debug"):
                    diffsync.job.log_warning(
                        f"Unable to find destination port for {ids['dst_device']}: {ids['dst_port']} {ids['dst_port_mac']}"
                    )
                return None
        if (_src_port and not _src_port.cable) and (_dst_port and not _dst_port.cable):
            new_cable = NautobotCable(
                termination_a_type=ContentType.objects.get(app_label="dcim", model="interface"),
                termination_a_id=_src_port.id,
                termination_b_type=ContentType.objects.get(app_label="dcim", model="interface"),
                termination_b_id=_dst_port.id,
                status=NautobotStatus.objects.get(name="Connected"),
                color=nautobot.get_random_color(),
            )
            return new_cable
        return None

    @staticmethod
    def get_dev_name(dev_name: str):
        """Strips cluster member names to get cluster master name.

        This is required as D42 API doesn't show interfaces on cluster members, just on the cluster master.

        Args:
            dev_name (str): Device name to check if cluster member or master.

        Returns:
            str: Returns name of cluster master if member found, else the device name itself.
        """
        if re.search(r"\s-\s\w.+", dev_name):
            _dev = re.sub(r"\s-\s\w.+", "", dev_name)
        else:
            _dev = dev_name
        return _dev

    def delete(self):
        """Delete Cable object from Nautobot."""
        print(f"Deleting {self.get_identifiers()}")
        if PLUGIN_CFG.get("verbose_debug"):
            print(f"Cable between {self.src_device} and {self.dst_device} will be deleted.")
        try:
            if self.src_port_mac is not None:
                _term_a = NautobotInterface.objects.get(mac_address=self.src_port_mac)
            else:
                # Circuit Terminations should have identical port and device, the CircuitID
                if self.src_port == self.src_device:
                    _circuit = NautobotCircuit.objects.get(cid=self.src_device)
                    _term_a = NautobotCT.objects.get(circuit=_circuit, term_side="A")
                else:
                    _term_a = NautobotInterface.objects.get(name=self.src_port, device__name=self.src_device)
        except NautobotInterface.DoesNotExist as err:
            if PLUGIN_CFG.get("verbose_debug"):
                print(f"Unable to find source port. {self.src_port} {self.src_port_mac} {self.src_device} {err}")
            return None
        except NautobotCT.DoesNotExist as err:
            if PLUGIN_CFG.get("verbose_debug"):
                print(f"Unable to find Circuit ID. {self.src_device} {self.src_port} {err}")
            return None
        try:
            if self.dst_port_mac is not None:
                _term_b = NautobotInterface.objects.get(mac_address=self.dst_port_mac)
            else:
                # Circuit Terminations should have identical port and device, the CircuitID
                if self.dst_port == self.dst_device:
                    _circuit = NautobotCircuit.objects.get(cid=self.dst_device)
                    _term_b = NautobotCT.objects.get(circuit=_circuit, term_side="Z")
                else:
                    _term_b = NautobotInterface.objects.get(name=self.dst_port, device__name=self.dst_device)
        except NautobotInterface.DoesNotExist as err:
            if PLUGIN_CFG.get("verbose_debug"):
                print(f"Unable to find destination port. {self.dst_port} {self.dst_port_mac}  {self.dst_device} {err}")
            return None
        except NautobotCT.DoesNotExist as err:
            if PLUGIN_CFG.get("verbose_debug"):
                print(f"Unable to find Circuit ID. {self.dst_device} {self.dst_port} {err}")
            return None
        if self.src_device == self.src_port:
            _conn = self.find_cable_to_circuitterm(term_a=_term_a, term_b=_term_b)
        elif self.dst_device == self.dst_port:
            _conn = self.find_cable_to_circuitterm(term_a=_term_a, term_b=_term_b)
        else:
            try:
                _conn = self.find_cable_to_interface(term_a=_term_a, term_b=_term_b)
            except NautobotCable.DoesNotExist:
                _conn = self.find_cable_to_interface(term_a=_term_b, term_b=_term_a)
        if _conn:
            _conn.delete()
            super().delete()
        return self

    def find_cable_to_circuitterm(self, term_a, term_b):
        """Method to find a Cable between an interface and a Circuit Termination.

        Args:
            term_a (Union[NautobotCable, NautobotCT]): Either a Cable or CircuitTermination.
            term_b (Union[NautobotCable, NautobotCT]): Either a Cable or CircuitTermination.

        Returns:
            NautobotCable: Cable if found.
        """
        try:
            conn = self.find_cable(
                term_a=term_a,
                term_a_type=ContentType.objects.get(app_label="circuits", model="circuittermination"),
                term_b=term_b,
                term_b_type=ContentType.objects.get(app_label="dcim", model="interface"),
            )
        except NautobotCable.DoesNotExist:
            try:
                conn = self.find_cable(
                    term_a=term_a,
                    term_a_type=ContentType.objects.get(app_label="dcim", model="interface"),
                    term_b=term_b,
                    term_b_type=ContentType.objects.get(app_label="circuits", model="circuittermination"),
                )
            except NautobotCable.DoesNotExist:
                return False
        return conn

    def find_cable_to_interface(self, term_a, term_b):
        """Method to find a Cable between two interfaces.

        Args:
            term_a (Union[NautobotCable, NautobotCT]): Either a Cable or CircuitTermination.
            term_b (Union[NautobotCable, NautobotCT]): Either a Cable or CircuitTermination.

        Returns:
            NautobotCable: Cable if found.
        """
        try:
            conn = self.find_cable(
                term_a=term_a,
                term_a_type=ContentType.objects.get(app_label="dcim", model="interface"),
                term_b=term_b,
                term_b_type=ContentType.objects.get(app_label="dcim", model="interface"),
            )
            return conn
        except NautobotCable.DoesNotExist:
            return False

    def find_cable(
        self,
        term_a: Union[NautobotCable, NautobotCT],
        term_a_type: ContentType,
        term_b: Union[NautobotCable, NautobotCT],
        term_b_type: ContentType,
    ) -> NautobotCable:
        """Method to find a Cable.

        Args:
            term_a (Union[NautobotCable, NautobotCT]): Either a Cable or CircuitTermination.
            term_a_type (ContentType): The ContentType for `term_a`.
            term_b (Union[NautobotCable, NautobotCT]): Either a Cable or CircuitTermination.
            term_b_type (ContentType): The ContentType for `term_b`.

        Returns:
            NautobotCable: Cable if found.
        """
        return NautobotCable.objects.get(
            termination_a_type=term_a_type,
            termination_a_id=term_a.id,
            termination_b_type=term_b_type,
            termination_b_id=term_b.id,
        )


Building.update_forward_refs()
Room.update_forward_refs()
Rack.update_forward_refs()
Vendor.update_forward_refs()
Cluster.update_forward_refs()
Device.update_forward_refs()