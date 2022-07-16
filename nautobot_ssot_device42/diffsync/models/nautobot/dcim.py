"""DiffSyncModel DCIM subclasses for Nautobot Device42 data sync."""

import re
from decimal import Decimal
from typing import Optional

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from nautobot.circuits.models import Circuit as OrmCircuit
from nautobot.circuits.models import CircuitTermination as OrmCT
from nautobot.core.settings_funcs import is_truthy
from nautobot.dcim.models import Cable as OrmCable
from nautobot.dcim.models import Device as OrmDevice
from nautobot.dcim.models import DeviceType as OrmDeviceType
from nautobot.dcim.models import FrontPort as OrmFrontPort
from nautobot.dcim.models import Interface as OrmInterface
from nautobot.dcim.models import Manufacturer as OrmManufacturer
from nautobot.dcim.models import Rack as OrmRack
from nautobot.dcim.models import RackGroup as OrmRackGroup
from nautobot.dcim.models import Site as OrmSite
from nautobot.dcim.models import VirtualChassis as OrmVC
from nautobot.extras.choices import CustomFieldTypeChoices
from nautobot.extras.models import CustomField, Relationship, RelationshipAssociation
from nautobot.extras.models import Status as OrmStatus
from nautobot.ipam.models import VLAN as OrmVLAN
from nautobot_ssot_device42.constant import DEFAULTS, INTF_SPEED_MAP, PLUGIN_CFG
from nautobot_ssot_device42.diffsync.models.base.dcim import (
    Building,
    Room,
    Rack,
    Vendor,
    Hardware,
    Cluster,
    Device,
    Port,
    Connection,
)
from nautobot_ssot_device42.utils import device42, nautobot

try:
    from nautobot_device_lifecycle_mgmt.models import SoftwareLCM

    LIFECYCLE_MGMT = True
except ImportError:
    print("Device Lifecycle plugin isn't installed so will revert to CustomField for OS version.")
    LIFECYCLE_MGMT = False


class NautobotBuilding(Building):
    """Nautobot Building model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Site object in Nautobot."""
        def_site_status = OrmStatus.objects.get(name=DEFAULTS.get("site_status"))
        new_site = OrmSite(
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
                field.content_types.add(ContentType.objects.get_for_model(OrmSite).id)
                new_site.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        new_site.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Site object in Nautobot."""
        _site = OrmSite.objects.get(id=self.uuid)
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
                field.content_types.add(ContentType.objects.get_for_model(OrmSite).id)
                _site.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _site.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Site object from Nautobot.

        Because Site has a direct relationship with many other objects it can't be deleted before anything else.
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        if PLUGIN_CFG.get("delete_on_sync"):
            super().delete()
            if self.diffsync.job.kwargs.get("debug"):
                self.diffsync.job.log_warning(message=f"Site {self.name} will be deleted.")
            site = OrmSite.objects.get(id=self.uuid)
            self.diffsync.objects_to_delete["site"].append(site)  # pylint: disable=protected-access
        return self


class NautobotRoom(Room):
    """Nautobot Room model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create RackGroup object in Nautobot."""
        new_rg = OrmRackGroup(
            name=ids["name"],
            slug=slugify(ids["name"]),
            site=OrmSite.objects.get(name=ids["building"]),
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
                field.content_types.add(ContentType.objects.get_for_model(OrmRackGroup).id)
                new_rg.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        new_rg.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update RackGroup object in Nautobot."""
        _rg = OrmRackGroup.objects.get(id=self.uuid)
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
                field.content_types.add(ContentType.objects.get_for_model(OrmRackGroup).id)
                _rg.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _rg.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete RackGroup object from Nautobot."""
        if PLUGIN_CFG.get("delete_on_sync"):
            super().delete()
            if self.diffsync.job.kwargs.get("debug"):
                self.diffsync.job.log_warning(message=f"RackGroup {self.name} will be deleted.")
            rackgroup = OrmRackGroup.objects.get(id=self.uuid)
            rackgroup.delete()
        return self


class NautobotRack(Rack):
    """Nautobot Rack model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Rack object in Nautobot."""
        _site = OrmSite.objects.get(name=ids["building"])
        _rg = OrmRackGroup.objects.get(name=ids["room"], site__name=ids["building"])
        new_rack = OrmRack(
            name=ids["name"],
            site=_site,
            group=_rg,
            status=OrmStatus.objects.get(name=DEFAULTS.get("rack_status")),
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
                field.content_types.add(ContentType.objects.get_for_model(OrmRack).id)
                new_rack.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        new_rack.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Rack object in Nautobot."""
        _rack = OrmRack.objects.get(id=self.uuid)
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
                field.content_types.add(ContentType.objects.get_for_model(OrmRack).id)
                _rack.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _rack.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Rack object from Nautobot.

        Because Rack has a direct relationship with Devices it can't be deleted before they are.
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        if PLUGIN_CFG.get("delete_on_sync"):
            super().delete()
            if self.diffsync.job.kwargs.get("debug"):
                self.diffsync.job.log_warning(message=f"Rack {self.name} will be deleted.")
            rack = OrmRack.objects.get(id=self.uuid)
            self.diffsync.objects_to_delete["rack"].append(rack)  # pylint: disable=protected-access
        return self


class NautobotVendor(Vendor):
    """Nautobot Vendor model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Manufacturer object in Nautobot."""
        if diffsync.job.kwargs.get("debug"):
            diffsync.job.log_debug(message=f"Creating Manufacturer {ids['name']}")
        try:
            OrmManufacturer.objects.get(slug=slugify(ids["name"]))
        except OrmManufacturer.DoesNotExist:
            new_manu = OrmManufacturer(
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
                    field.content_types.add(ContentType.objects.get_for_model(OrmManufacturer).id)
                    new_manu.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
            new_manu.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Manufacturer object in Nautobot."""
        _manu = OrmManufacturer.objects.get(id=self.uuid)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(OrmManufacturer).id)
                _manu.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _manu.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Manufacturer object from Nautobot.

        Because Manufacturer has a direct relationship with DeviceTypes and other objects it can't be deleted before them.
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        if PLUGIN_CFG.get("delete_on_sync"):
            super().delete()
            if self.diffsync.job.kwargs.get("debug"):
                self.diffsync.job.log_warning(message=f"Manufacturer {self.name} will be deleted.")
            _manu = OrmManufacturer.objects.get(id=self.uuid)
            self.diffsync.objects_to_delete["manufacturer"].append(_manu)  # pylint: disable=protected-access
        return self


class NautobotHardware(Hardware):
    """Nautobot Hardware model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create DeviceType object in Nautobot."""
        if diffsync.job.kwargs.get("debug"):
            diffsync.job.log_debug(message=f"Creating DeviceType {ids['name']}")
        try:
            OrmDeviceType.objects.get(slug=slugify(ids["name"]))
        except OrmDeviceType.DoesNotExist:
            new_dt = OrmDeviceType(
                model=ids["name"],
                slug=slugify(ids["name"]),
                manufacturer=OrmManufacturer.objects.get(slug=slugify(attrs["manufacturer"])),
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
                    field.content_types.add(ContentType.objects.get_for_model(OrmDeviceType).id)
                    new_dt.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
            new_dt.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update DeviceType object in Nautobot."""
        _dt = OrmDeviceType.objects.get(id=self.uuid)
        if attrs.get("manufacturer"):
            _dt.manufacturer = OrmManufacturer.objects.get(slug=slugify(attrs["manufacturer"]))
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
                field.content_types.add(ContentType.objects.get_for_model(OrmDeviceType).id)
                _dt.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _dt.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete DeviceType object from Nautobot.

        Because DeviceType has a direct relationship with Devices it can't be deleted before all Devices are.
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        if PLUGIN_CFG.get("delete_on_sync"):
            super().delete()
            if self.diffsync.job.kwargs.get("debug"):
                self.diffsync.job.log_warning(message=f"DeviceType {self.name} will be deleted.")
            _dt = OrmDeviceType.objects.get(id=self.uuid)
            self.diffsync.objects_to_delete["device_type"].append(_dt)  # pylint: disable=protected-access
        return self


class NautobotCluster(Cluster):
    """Nautobot Cluster model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Virtual Chassis object in Nautobot.

        As the master node of the VC needs to be a regular Device, we'll create that and then the VC.
        Member devices will be added to VC at Device creation.
        """
        if diffsync.job.kwargs.get("debug"):
            diffsync.job.log_debug(message=f"Creating VC Master Device {ids['name']}.")
        new_vc = OrmVC(
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
                field.content_types.add(ContentType.objects.get_for_model(OrmVC).id)
                new_vc.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        new_vc.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Virtual Chassis object in Nautobot."""
        _vc = OrmVC.objects.get(id=self.uuid)
        if attrs.get("members"):
            for _member in attrs["members"]:
                try:
                    device = OrmDevice.objects.get(name=_member)
                    device.virtual_chassis = _vc
                    switch_pos = re.search(r".+-\s([sS]witch)\s?(?P<pos>\d+)", _member)
                    node_pos = re.search(r".+-\s([nN]ode)\s?(?P<pos>\d+)", _member)
                    if switch_pos or node_pos:
                        if switch_pos:
                            position = int(switch_pos.group("pos"))
                        if node_pos:
                            position = int(node_pos.group("pos")) + 1
                    else:
                        position = len(OrmDevice.objects.filter(virtual_chassis__name=self.name))
                    device.vc_position = position + 1
                except OrmDevice.DoesNotExist as err:
                    if self.diffsync.job.kwargs.get("debug"):
                        self.diffsync.job.log_warning(
                            message=f"Unable to find {_member} to add to VC {self.name} {err}"
                        )
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
                field.content_types.add(ContentType.objects.get_for_model(OrmVC).id)
                _vc.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _vc.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Virtual Chassis object from Nautobot.

        Because Virtual Chassis has a direct relationship with Devices it can't be deleted before they are.
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        if PLUGIN_CFG.get("delete_on_sync"):
            super().delete()
            if self.diffsync.job.kwargs.get("debug"):
                self.diffsync.job.log_warning(message=f"Virtual Chassis {self.name} will be deleted.")
            _cluster = OrmVC.objects.get(id=self.uuid)
            self.diffsync.objects_to_delete["cluster"].append(_cluster)  # pylint: disable=protected-access
        return self


class NautobotDevice(Device):
    """Nautobot Device model."""

    @staticmethod
    def _get_site(diffsync, ids, attrs):
        if attrs.get("rack") and attrs.get("room"):
            try:
                _site = OrmRack.objects.get(name=attrs["rack"], group__name=attrs["room"]).site
                return _site
            except OrmRack.DoesNotExist as err:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_debug(
                        message=f"Unable to find Site by Rack/Room. {attrs['rack']} {attrs['room']} {err}"
                    )
        if attrs.get("building"):
            try:
                _site = OrmSite.objects.get(slug=attrs["building"])
                return _site
            except OrmSite.DoesNotExist as err:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_debug(message=f"Unable to find Site {attrs['building']}. {err}")
        else:
            if diffsync.job.kwargs.get("debug"):
                diffsync.job.log_debug(
                    message=f"Device {ids['name']} is missing Building or Customer so can't determine Site."
                )
            return False

    @classmethod
    def create(cls, diffsync, ids, attrs):  # pylint: disable=inconsistent-return-statements
        """Create Device object in Nautobot."""
        if attrs["in_service"]:
            _status = OrmStatus.objects.get(name="Active")
        else:
            _status = OrmStatus.objects.get(name="Offline")
        if diffsync.job.debug:
            diffsync.job.log_debug(message=f"Creating device {ids['name']}.")
        if attrs.get("tags") and len(attrs["tags"]) > 0:
            _role = nautobot.verify_device_role(device42.find_device_role_from_tags(tag_list=attrs["tags"]))
        else:
            _role = nautobot.verify_device_role(role_name=DEFAULTS.get("device_role"))
        try:
            _dt = OrmDeviceType.objects.get(model=attrs["hardware"])
            _site = cls._get_site(diffsync, ids, attrs)
            if not _site:
                diffsync.job.log_debug(message=f"Can't create {ids['name']} as unable to determine Site.")
                return None
            new_device = OrmDevice(
                name=ids["name"][:64],
                status=_status,
                site=_site,
                device_type=_dt,
                device_role=_role,
                serial=attrs["serial_no"] if attrs.get("serial_no") else "",
            )
            if attrs.get("rack"):
                # check that the rack position is available for the Device to be assigned. Unassigns Device if found.
                devs = OrmDevice.objects.filter(
                    rack__name=attrs["rack"],
                    rack__group__name=attrs["room"],
                    position=attrs["rack_position"],
                    face=attrs["rack_orientation"],
                )
                if len(devs) == 1:
                    old_dev = devs[0]
                    old_dev.position = None
                    old_dev.validated_save()
                else:
                    new_device.rack = OrmRack.objects.get(name=attrs["rack"], group__name=attrs["room"])
                    new_device.position = int(attrs["rack_position"]) if attrs["rack_position"] else None
                    new_device.face = attrs["rack_orientation"] if attrs["rack_orientation"] else "front"
            if attrs.get("os"):
                new_device.platform = nautobot.verify_platform(
                    platform_name=attrs["os"],
                    manu=OrmDeviceType.objects.get(model=attrs["hardware"]).manufacturer,
                )
            new_device.validated_save()
            if attrs.get("os_version"):
                if LIFECYCLE_MGMT and attrs.get("os"):
                    soft_lcm = cls._add_software_lcm(
                        os=attrs["os"], version=attrs["os_version"], hardware=attrs["hardware"]
                    )
                    cls._assign_version_to_device(device=new_device, software_lcm=soft_lcm)
                else:
                    attrs["custom_fields"].append({"key": "OS Version", "value": attrs["os_version"]})
            if attrs.get("cluster_host"):
                try:
                    _vc = OrmVC.objects.get(name=attrs["cluster_host"])
                    new_device.virtual_chassis = _vc
                    if attrs.get("master_device") and attrs["master_device"]:
                        new_device.vc_position = 1
                        new_device.validated_save()
                        _vc.master = new_device
                        _vc.validated_save()
                    else:
                        switch_pos = re.search(r".+-\s([sS]witch)\s?(?P<pos>\d+)", ids["name"])
                        node_pos = re.search(r".+-\s([nN]ode)\s?(?P<pos>\d+)", ids["name"])
                        position = 1
                        if switch_pos or node_pos:
                            if switch_pos:
                                position = int(switch_pos.group("pos"))
                            if node_pos:
                                position = int(node_pos.group("pos")) + 1
                        else:
                            position = len(OrmDevice.objects.filter(virtual_chassis__name=attrs["cluster_host"])) + 1
                        new_device.vc_position = position + 1
                except OrmVC.DoesNotExist as err:
                    if diffsync.job.kwargs.get("debug"):
                        diffsync.job.log_warning(message=f"Unable to find VC {attrs['cluster_host']} {err}")
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
                    field.content_types.add(ContentType.objects.get_for_model(OrmDevice).id)
                    new_device.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
            try:
                new_device.validated_save()
                return super().create(diffsync=diffsync, ids=ids, attrs=attrs)
            except ValidationError as err:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_debug(message=f"Validation error when creating Device {ids['name']}. {err}")
        except OrmRack.DoesNotExist:
            if diffsync.job.kwargs.get("debug"):
                diffsync.job.log_debug(message=f"Unable to find matching Rack {attrs.get('rack')} for {_site.name}")
        except OrmDeviceType.DoesNotExist:
            if diffsync.job.kwargs.get("debug"):
                diffsync.job.log_debug(
                    message=f"Unable to find matching DeviceType {attrs['hardware']} for {ids['name']}.",
                )
        return None

    def update(self, attrs):
        """Update Device object in Nautobot."""
        _dev = OrmDevice.objects.get(id=self.uuid)
        if attrs.get("building"):
            _dev.site = self._get_site(diffsync=self.diffsync, ids=self.get_identifiers(), attrs=attrs)
        if attrs.get("rack") and attrs.get("room"):
            try:
                _dev.site = self._get_site(diffsync=self.diffsync, ids=self.get_identifiers(), attrs=attrs)
                _dev.rack = OrmRack.objects.get(name=attrs["rack"], group__name=attrs["room"])
                if _dev.site.name == _dev.rack.site.name:
                    if attrs.get("rack_position"):
                        _dev.position = int(attrs["rack_position"])
                    else:
                        _dev.position = None
                    if attrs.get("rack_orientation"):
                        _dev.face = attrs["rack_orientation"]
                    else:
                        _dev.face = "rear"
            except OrmRack.DoesNotExist as err:
                if self.diffsync.job.kwargs.get("debug"):
                    self.diffsync.job.log_warning(
                        message=f"Unable to find rack {attrs['rack']} in {attrs['room']} {err}"
                    )
        if attrs.get("hardware"):
            _dt = OrmDeviceType.objects.get(model=attrs["hardware"])
            _dev.device_type = _dt
        if attrs.get("os"):
            if attrs.get("hardware"):
                _hardware = OrmDeviceType.objects.get(model=attrs["hardware"])
            else:
                _hardware = _dev.device_type
            _dev.platform = nautobot.verify_platform(
                platform_name=attrs["os"],
                manu=_hardware.manufacturer,
            )
        if attrs.get("os_version"):
            if attrs.get("os"):
                _os = attrs["os"]
            else:
                _os = self.os
            if attrs.get("hardware"):
                _hardware = attrs["hardware"]
            else:
                _hardware = self.hardware
            if LIFECYCLE_MGMT:
                soft_lcm = self._add_software_lcm(os=_os, version=attrs["os_version"], hardware=_hardware)
                self._assign_version_to_device(device=_dev, software_lcm=soft_lcm)
            else:
                attrs["custom_fields"].append(
                    {"key": "OS Version", "value": attrs["os_version"] if attrs.get("os_version") else self.os_version}
                )
        if attrs.get("in_service"):
            if attrs["in_service"]:
                _status = OrmStatus.objects.get(name="Active")
            else:
                _status = OrmStatus.objects.get(name="Offline")
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
                field.content_types.add(ContentType.objects.get_for_model(OrmDevice).id)
                _dev.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        # ensure that VC Master Device is set to that
        if attrs.get("cluster_host") or attrs.get("master_device"):
            if attrs.get("cluster_host"):
                _clus_host = attrs["cluster_host"]
            else:
                _clus_host = self.cluster_host
            try:
                _vc = OrmVC.objects.get(name=_clus_host)
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
                        position = len(OrmDevice.objects.filter(virtual_chassis__name=_clus_host))
                    _dev.vc_position = position + 1
            except OrmVC.DoesNotExist as err:
                if self.diffsync.job.kwargs.get("debug"):
                    self.diffsync.job.log_warning(message=f"Unable to find VC {_clus_host} {err}")
        print(f"Saving Device {self.name} in {_dev.site} {_dev.rack}")
        try:
            _dev.validated_save()
            return super().update(attrs)
        except ValidationError as err:
            print(f"Unable to update Device {self.name} with {attrs}. {err}")
            return None

    def delete(self):
        """Delete Device object from Nautobot.

        Because Device has a direct relationship with Ports and IP Addresses it can't be deleted before they are.
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        if PLUGIN_CFG.get("delete_on_sync"):
            super().delete()
            if self.diffsync.job.kwargs.get("debug"):
                self.diffsync.job.log_warning(message=f"Device {self.name} will be deleted.")
            _dev = OrmDevice.objects.get(id=self.uuid)
            self.diffsync.objects_to_delete["device"].append(_dev)  # pylint: disable=protected-access
        return self

    @staticmethod
    def _add_software_lcm(os: str, version: str, hardware: str):
        """Add OS Version as SoftwareLCM if Device Lifecycle Plugin found."""
        _platform = nautobot.verify_platform(
            platform_name=os,
            manu=OrmDeviceType.objects.get(model=hardware).manufacturer,
        )
        try:
            os_ver = SoftwareLCM.objects.get(device_platform=_platform, version=version)
        except SoftwareLCM.DoesNotExist:
            os_ver = SoftwareLCM(
                device_platform=_platform,
                version=version,
            )
            os_ver.validated_save()
        return os_ver

    @staticmethod
    def _assign_version_to_device(device, software_lcm):
        """Add Relationship between Device and SoftwareLCM."""
        new_assoc = RelationshipAssociation(
            relationship=Relationship.objects.get(name="Software on Device"),
            source_type=ContentType.objects.get_for_model(SoftwareLCM),
            source_id=software_lcm.id,
            destination_type=ContentType.objects.get_for_model(OrmDevice),
            destination_id=device.id,
        )
        try:
            new_assoc.validated_save()
        except ValidationError:
            return None


class NautobotPort(Port):
    """Nautobot Port model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):  # pylint: disable=inconsistent-return-statements
        """Create Interface object in Nautobot."""
        try:
            if ids.get("device"):
                _dev = OrmDevice.objects.get(name=ids["device"])
                new_intf = OrmInterface(
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
                        field.content_types.add(ContentType.objects.get_for_model(OrmInterface).id)
                        new_intf.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
                new_intf.validated_save()
                try:
                    if attrs.get("vlans"):
                        if attrs["mode"] == "access" and len(attrs["vlans"]) == 1:
                            _vlan = attrs["vlans"][0]
                            vlan_found = OrmVLAN.objects.filter(
                                name=_vlan["vlan_name"], vid=_vlan["vlan_id"], site=_dev.site
                            )
                            if vlan_found:
                                new_intf.untagged_vlan = vlan_found[0]
                        else:
                            tagged_vlans = []
                            for _vlan in attrs["vlans"]:
                                tagged_vlan = OrmVLAN.objects.filter(
                                    name=_vlan["vlan_name"], vid=_vlan["vlan_id"], site=_dev.site
                                )
                                if not tagged_vlan:
                                    tagged_vlan = OrmVLAN.objects.filter(name=_vlan["vlan_name"], vid=_vlan["vlan_id"])
                                if tagged_vlan:
                                    tagged_vlans.append(tagged_vlan[0])
                            new_intf.tagged_vlans.set(tagged_vlans)
                except OrmVLAN.DoesNotExist as err:
                    if diffsync.job.kwargs.get("debug"):
                        diffsync.job.log_debug(message=f"{err}: {_vlan['vlan_name']} {_vlan['vlan_id']}")
                new_intf.validated_save()
                return super().create(ids=ids, diffsync=diffsync, attrs=attrs)
        except OrmDevice.DoesNotExist as err:
            if diffsync.job.kwargs.get("debug"):
                diffsync.job.log_warning(message=f"{ids['name']} doesn't exist. {err}")
                return False

    def update(self, attrs):
        """Update Interface object in Nautobot."""
        _port = OrmInterface.objects.get(id=self.uuid)
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
                field.content_types.add(ContentType.objects.get_for_model(OrmInterface).id)
                _port.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        if attrs.get("vlans"):
            if attrs.get("mode"):
                _mode = attrs["mode"]
            else:
                _mode = self.mode
            if _mode == "access" and len(attrs["vlans"]) == 1:
                _vlan = attrs["vlans"][0]
                vlan_found = OrmVLAN.objects.filter(
                    name=_vlan["vlan_name"],
                    vid=_vlan["vlan_id"],
                    site=OrmDevice.objects.get(name=self.device).site,
                )
                if vlan_found:
                    _port.untagged_vlan = vlan_found[0]
            else:
                tagged_vlans = []
                for _vlan in attrs["vlans"]:
                    tagged_vlan = OrmVLAN.objects.filter(
                        name=_vlan["vlan_name"],
                        vid=_vlan["vlan_id"],
                        site=OrmDevice.objects.get(name=self.device).site,
                    )
                    if not tagged_vlan:
                        tagged_vlan = OrmVLAN.objects.filter(name=_vlan["vlan_name"], vid=_vlan["vlan_id"])
                    if tagged_vlan:
                        tagged_vlans.append(tagged_vlan[0])
                _port.tagged_vlans.set(tagged_vlans)
        try:
            _port.validated_save()
            return super().update(attrs)
        except ValidationError as err:
            if self.diffsync.job.kwargs.get("debug"):
                self.diffsync.job.log_debug(message=f"Validation error for updating Port: {err}")
            return None

    def delete(self):
        """Delete Interface object from Nautobot."""
        if PLUGIN_CFG.get("delete_on_sync"):
            super().delete()
            if self.diffsync.job.kwargs.get("debug"):
                self.diffsync.job.log_warning(message=f"Interface {self.name} for {self.device} will be deleted.")
            _intf = OrmInterface.objects.get(id=self.uuid)
            self.diffsync.objects_to_delete["port"].append(_intf)  # pylint: disable=protected-access
        return self


class NautobotConnection(Connection):
    """Nautobot Connection model."""

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
        else:
            return None

    def get_circuit_connections(self, diffsync, ids, attrs) -> Optional[OrmCable]:
        """Method to create a Cable between a Circuit and a Device.

        Args:
            diffsync (obj): DiffSync job used for logging.
            ids (dict): Identifying attributes for the object.
            attrs (dict): Non-identifying attributes for the object.

        Returns:
            Optional[OrmCable]: If the Interfaces are found and a cable is created, returns Cable else None.
        """
        _intf, circuit = None, None
        if attrs["src_type"] == "interface":
            try:
                _intf = OrmInterface.objects.get(device__name=ids["src_device"], name=ids["src_port"])
                circuit = OrmCircuit.objects.get(cid=ids["dst_device"])
            except OrmInterface.DoesNotExist as err:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_warning(
                        message=f"Unable to find source port for {ids['src_device']}: {ids['src_port']} to connect to Circuit {ids['dst_device']} {err}"
                    )
                return None
            except OrmCircuit.DoesNotExist as err:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_warning(message=f"Unable to find Circuit {ids['dst_device']} {err}")
                return None
        elif attrs["src_type"] == "patch panel":
            try:
                _intf = OrmFrontPort.objects.get(device__name=ids["src_device"], name=ids["src_port"])
                circuit = OrmCircuit.objects.get(cid=ids["dst_device"])
            except OrmFrontPort.DoesNotExist as err:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_warning(
                        message=f"Unable to find patch panel port for {ids['src_device']}: {ids['src_port']} to connect to Circuit {ids['dst_device']} {err}"
                    )
                return None
            except OrmCircuit.DoesNotExist as err:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_warning(message=f"Unable to find Circuit {ids['dst_device']} {err}")
                return None
        if attrs["dst_type"] == "interface":
            try:
                circuit = OrmCircuit.objects.get(cid=ids["src_device"])
                _intf = OrmInterface.objects.get(device__name=ids["dst_device"], name=ids["dst_port"])
            except OrmInterface.DoesNotExist as err:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_warning(
                        message=f"Unable to find destination port for {ids['dst_device']}: {ids['dst_port']} to connect to Circuit {ids['src_device']} {err}"
                    )
                return None
            except OrmCircuit.DoesNotExist as err:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_warning(message=f"Unable to find Circuit {ids['dst_device']} {err}")
                return None
        elif attrs["dst_type"] == "patch panel":
            try:
                circuit = OrmCircuit.objects.get(cid=ids["src_device"])
                _intf = OrmFrontPort.objects.get(device__name=ids["dst_device"], name=ids["dst_port"])
            except OrmFrontPort.DoesNotExist as err:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_warning(
                        message=f"Unable to find destination port for {ids['dst_device']}: {ids['dst_port']} to connect to Circuit {ids['src_device']} {err}"
                    )
                return None
            except OrmCircuit.DoesNotExist as err:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_warning(message=f"Unable to find Circuit {ids['dst_device']} {err}")
                return None
        if circuit and _intf:
            _ct = {
                "circuit": circuit,
                "site": _intf.device.site,
            }
        else:
            if diffsync.job.kwargs.get("debug"):
                diffsync.job.log_warning(message=f"Unable to find Circuit and Interface {ids}")
            return None
        if attrs["src_type"] == "circuit":
            _ct["term_side"] = "Z"
        if attrs["dst_type"] == "circuit":
            _ct["term_side"] = "A"
        try:
            circuit_term = OrmCT.objects.get(**_ct)
        except OrmCT.DoesNotExist:
            circuit_term = OrmCT(**_ct)
            circuit_term.port_speed = INTF_SPEED_MAP[_intf.type] if isinstance(_intf, OrmInterface) else None
            circuit_term.validated_save()
        if _intf and not _intf.cable and not circuit_term.cable:
            new_cable = OrmCable(
                termination_a_type=ContentType.objects.get(app_label="dcim", model="interface")
                if attrs["src_type"] == "interface"
                else ContentType.objects.get(app_label="dcim", model="frontport"),
                termination_a_id=_intf.id,
                termination_b_type=ContentType.objects.get(app_label="circuits", model="circuittermination"),
                termination_b_id=circuit_term.id,
                status=OrmStatus.objects.get(name="Connected"),
                color=nautobot.get_random_color(),
            )
            return new_cable
        else:
            return None

    def get_device_connections(self, diffsync, ids) -> Optional[OrmCable]:
        """Method to create a Cable between two Devices.

        Args:
            diffsync (obj): DiffSync job used for logging.
            ids (dict): Identifying attributes for the object.

        Returns:
            Optional[OrmCable]: If the Interfaces are found and a cable is created, returns Cable else None.
        """
        _src_port, _dst_port = None, None
        try:
            if ids.get("src_port_mac") and ids["src_port_mac"] != ids.get("dst_port_mac"):
                _src_port = OrmInterface.objects.get(mac_address=ids["src_port_mac"])
        except (OrmInterface.DoesNotExist, OrmInterface.MultipleObjectsReturned):
            try:
                _src_port = OrmInterface.objects.get(device__name=ids["src_device"], name=ids["src_port"])
            except OrmInterface.DoesNotExist as err:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_warning(
                        message=f"Unable to find source port for {ids['src_device']}: {ids['src_port']} {ids['src_port_mac']} {err}"
                    )
                return None
        try:
            if ids.get("dst_port_mac") and ids["dst_port_mac"] != ids.get("src_port_mac"):
                _dst_port = OrmInterface.objects.get(mac_address=ids["dst_port_mac"])
        except (OrmInterface.DoesNotExist, OrmInterface.MultipleObjectsReturned):
            try:
                _dst_port = OrmInterface.objects.get(device__name=ids["dst_device"], name=ids["dst_port"])
            except OrmInterface.DoesNotExist:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_warning(
                        message=f"Unable to find destination port for {ids['dst_device']}: {ids['dst_port']} {ids['dst_port_mac']}"
                    )
                return None
        if (_src_port and not _src_port.cable) and (_dst_port and not _dst_port.cable):
            new_cable = OrmCable(
                termination_a_type=ContentType.objects.get(app_label="dcim", model="interface"),
                termination_a_id=_src_port.id,
                termination_b_type=ContentType.objects.get(app_label="dcim", model="interface"),
                termination_b_id=_dst_port.id,
                status=OrmStatus.objects.get(name="Connected"),
                color=nautobot.get_random_color(),
            )
            return new_cable
        else:
            return None

    def delete(self):
        """Delete Cable object from Nautobot."""
        if PLUGIN_CFG.get("delete_on_sync"):
            super().delete()
            if self.diffsync.job.kwargs.get("debug"):
                self.diffsync.job.log_info(message=f"Deleting Cable {self.get_identifiers()} UUID: {self.uuid}")
            _conn = OrmCable.objects.get(id=self.uuid)
            _conn.delete()
        return self
