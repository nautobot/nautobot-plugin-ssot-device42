"""DiffSyncModel DCIM subclasses for Nautobot Device42 data sync."""

import re
from decimal import Decimal
from typing import Optional
from uuid import UUID

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
from nautobot.extras.models import CustomField, RelationshipAssociation
from nautobot.extras.models import Status as OrmStatus
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
        def_site_status = diffsync.status_map[slugify(DEFAULTS.get("site_status"))]
        new_site = OrmSite(
            name=ids["name"],
            slug=slugify(ids["name"]),
            status_id=def_site_status,
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
        diffsync.objects_to_create["sites"].append(new_site)
        diffsync.site_map[slugify(ids["name"])] = new_site.id
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
            site_id=diffsync.site_map[slugify(ids["building"])],
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
        diffsync.objects_to_create["rooms"].append(new_rg)
        if slugify(ids["building"]) not in diffsync.room_map:
            diffsync.room_map[slugify(ids["building"])] = {}
        diffsync.room_map[slugify(ids["building"])][slugify(ids["name"])] = new_rg.id
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
        _site = diffsync.site_map[slugify(ids["building"])]
        _rg = diffsync.room_map[slugify(ids["building"])][slugify(ids["room"])]
        new_rack = OrmRack(
            name=ids["name"],
            site_id=_site,
            group_id=_rg,
            status_id=diffsync.status_map[slugify(DEFAULTS.get("rack_status"))],
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
        diffsync.objects_to_create["racks"].append(new_rack)
        if slugify(ids["building"]) not in diffsync.rack_map:
            diffsync.rack_map[slugify(ids["building"])] = {}
        if slugify(ids["room"]) not in diffsync.rack_map[slugify(ids["building"])]:
            diffsync.rack_map[slugify(ids["building"])][slugify(ids["room"])] = {}
        diffsync.rack_map[slugify(ids["building"])][slugify(ids["room"])][ids["name"]] = new_rack.id
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
            diffsync.vendor_map[slugify(ids["name"])]
        except KeyError:
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
            diffsync.objects_to_create["vendors"].append(new_manu)
            diffsync.vendor_map[slugify(ids["name"])] = new_manu.id
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
            diffsync.devicetype_map[slugify(ids["name"])]
        except KeyError:
            new_dt = OrmDeviceType(
                model=ids["name"],
                slug=slugify(ids["name"]),
                manufacturer_id=diffsync.vendor_map[slugify(attrs["manufacturer"])],
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
            diffsync.objects_to_create["devicetypes"].append(new_dt)
            diffsync.devicetype_map[slugify(ids["name"])] = new_dt.id
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
        diffsync.objects_to_create["clusters"].append(new_vc)
        diffsync.cluster_map[ids["name"]] = new_vc.id
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
        """Get Site ID from Building name."""
        try:
            _site = diffsync.site_map[slugify(attrs["building"])]
            return _site
        except KeyError:
            if diffsync.job.kwargs.get("debug"):
                diffsync.job.log_debug(message=f"Unable to find Site {attrs['building']}.")
        return None

    @classmethod
    def create(cls, diffsync, ids, attrs):  # pylint: disable=inconsistent-return-statements
        """Create Device object in Nautobot."""
        if attrs["in_service"]:
            _status = diffsync.status_map["active"]
        else:
            _status = diffsync.status_map["offline"]
        if diffsync.job.kwargs.get("debug"):
            diffsync.job.log_debug(message=f"Creating device {ids['name']}.")
        if attrs.get("tags") and len(attrs["tags"]) > 0:
            _role = nautobot.verify_device_role(
                diffsync=diffsync, role_name=device42.find_device_role_from_tags(tag_list=attrs["tags"])
            )
        else:
            _role = nautobot.verify_device_role(diffsync=diffsync, role_name=DEFAULTS.get("device_role"))
        try:
            _dt = diffsync.devicetype_map[slugify(attrs["hardware"])]
        except KeyError:
            if diffsync.job.kwargs.get("debug"):
                diffsync.job.log_debug(message=f"Unable to find DeviceType {attrs['hardware']} - {_dt}.")
            return None
        _site = cls._get_site(diffsync, ids, attrs)
        if not _site:
            diffsync.job.log_debug(message=f"Can't create {ids['name']} as unable to determine Site.")
            return None
        new_device = OrmDevice(
            name=ids["name"][:64],
            status_id=_status,
            site_id=_site,
            device_type_id=_dt,
            device_role_id=_role,
            serial=attrs["serial_no"] if attrs.get("serial_no") else "",
        )
        if attrs.get("rack"):
            new_device.rack_id = diffsync.rack_map[slugify(attrs["building"])][slugify(attrs["room"])][attrs["rack"]]
            new_device.position = int(attrs["rack_position"]) if attrs["rack_position"] else None
            new_device.face = attrs["rack_orientation"] if attrs["rack_orientation"] else "front"
        if attrs.get("os"):
            devicetype = diffsync.get(NautobotHardware, attrs["hardware"])
            new_device.platform_id = nautobot.verify_platform(
                diffsync=diffsync,
                platform_name=attrs["os"],
                manu=diffsync.vendor_map[slugify(devicetype.manufacturer)],
            )
        if attrs.get("os_version"):
            if LIFECYCLE_MGMT and attrs.get("os"):
                manu_id = None
                for dt in diffsync.objects_to_create["devicetypes"]:
                    if dt.model == attrs["hardware"]:
                        manu_id = dt.manufacturer_id
                if manu_id:
                    soft_lcm = cls._add_software_lcm(
                        diffsync=diffsync, os=attrs["os"], version=attrs["os_version"], manufacturer=manu_id
                    )
                    cls._assign_version_to_device(diffsync=diffsync, device=new_device.id, software_lcm=soft_lcm)
            else:
                attrs["custom_fields"].append({"key": "OS Version", "value": attrs["os_version"]})
        if attrs.get("cluster_host"):
            try:
                _vc = diffsync.cluster_map[attrs["cluster_host"]]
                new_device.virtual_chassis_id = _vc
                if attrs.get("master_device") and attrs["master_device"]:
                    for vc in diffsync.objects_to_create["clusters"]:
                        if vc.name == attrs["cluster_host"]:
                            vc.master = new_device
            except KeyError:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_warning(message=f"Unable to find VC {attrs['cluster_host']}")
        if attrs.get("vc_position"):
            new_device.vc_position = attrs["vc_position"]
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
        diffsync.objects_to_create["devices"].append(new_device)
        diffsync.device_map[ids["name"]] = new_device.id
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Device object in Nautobot."""
        _dev = OrmDevice.objects.get(id=self.uuid)
        if self.diffsync.job.kwargs.get("debug"):
            self.diffsync.log_debug(message=f"Updating Device {self.name} in {_dev.site} with {attrs}")
        if attrs.get("building"):
            site_id = None
            try:
                site_id = OrmSite.objects.get(name=attrs["building"])
            except OrmSite.DoesNotExist:
                for site in self.diffsync.objects_to_create["sites"]:
                    if site.slug == attrs["building"]:
                        site.validated_save()
                        self.diffsync.objects_to_create["sites"].remove(site)
                        site_id = self._get_site(diffsync=self.diffsync, building=attrs["building"])
            if site_id:
                _dev.site_id = site_id
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
            for new_dt in self.diffsync.objects_to_create["devicetypes"]:
                if new_dt.model == attrs["hardware"]:
                    new_dt.validated_save()
                    self.diffsync.objects_to_create["devicetypes"].pop(new_dt)
            _dev.device_type_id = self.diffsync.devicetype_map[slugify(attrs["hardware"])]
        if attrs.get("os"):
            if attrs.get("hardware"):
                _hardware = self.diffsync.get(NautobotHardware, attrs["hardware"])
            else:
                _hardware = self.diffsync.get(NautobotHardware, self.hardware)
            _dev.platform_id = nautobot.verify_platform(
                diffsync=self.diffsync,
                platform_name=attrs["os"],
                manu=self.diffsync.vendor_map[slugify(_hardware.manufacturer)],
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
                soft_lcm = self._add_software_lcm(
                    diffsync=self.diffsync,
                    os=_os,
                    version=attrs["os_version"],
                    manufacturer=_dev.device_type.manufacturer.id,
                )
                self._assign_version_to_device(diffsync=self.diffsync, device=self.uuid, software_lcm=soft_lcm)
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
            if attrs.get("tags") and len(attrs["tags"]) > 0:
                _dev.role = nautobot.verify_device_role(
                    diffsync=self.diffsync, role_name=device42.find_device_role_from_tags(tag_list=attrs["tags"])
                )
            else:
                _dev.role = nautobot.verify_device_role(diffsync=self.diffsync, role_name=DEFAULTS.get("device_role"))
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
                _vc = self.diffsync.cluster_map[_clus_host]
                _dev.virtual_chassis_id = _vc
                if attrs.get("master_device"):
                    for vc in self.diffsync.objects_to_create["clusters"]:
                        if vc.name == attrs["cluster_host"]:
                            vc.master = _dev
            except KeyError:
                if self.diffsync.job.kwargs.get("debug"):
                    self.diffsync.job.log_warning(message=f"Unable to find VC {attrs['cluster_host']}")
        if attrs.get("vc_position"):
            _dev.vc_position = attrs["vc_position"]
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
    def _add_software_lcm(diffsync: object, os: str, version: str, manufacturer: UUID):
        """Add OS Version as SoftwareLCM if Device Lifecycle Plugin found."""
        _platform = nautobot.verify_platform(diffsync=diffsync, platform_name=os, manu=manufacturer)
        try:
            os_ver = diffsync.softwarelcm_map[os][version]
        except KeyError:
            os_ver = SoftwareLCM(
                device_platform_id=_platform,
                version=version,
            )
            diffsync.objects_to_create["softwarelcms"].append(os_ver)
            if os not in diffsync.softwarelcm_map:
                diffsync.softwarelcm_map[os] = {}
            diffsync.softwarelcm_map[os][version] = os_ver.id
            os_ver = os_ver.id
        return os_ver

    @staticmethod
    def _assign_version_to_device(diffsync, device, software_lcm):
        """Add Relationship between Device and SoftwareLCM."""
        new_assoc = RelationshipAssociation(
            relationship_id=diffsync.relationship_map["Software on Device"],
            source_type=ContentType.objects.get_for_model(SoftwareLCM),
            source_id=software_lcm,
            destination_type=ContentType.objects.get_for_model(OrmDevice),
            destination_id=device,
        )
        diffsync.objects_to_create["relationshipasscs"].append(new_assoc)


class NautobotPort(Port):
    """Nautobot Port model."""

    def find_site(self, diffsync, site_id: UUID):
        """Find Site name using it's UUID."""
        for site, obj_id in diffsync.site_map.items():
            if obj_id == site_id:
                return site

    @classmethod
    def create(cls, diffsync, ids, attrs):  # pylint: disable=inconsistent-return-statements
        """Create Interface object in Nautobot."""
        if ids.get("device"):
            try:
                _dev = diffsync.device_map[ids["device"]]
            except KeyError:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_warning(
                        message=f"Attempting to create {ids['name']} for {ids['device']} failed as {ids['device']} doesn't exist."
                    )
                return None
            new_intf = OrmInterface(
                name=ids["name"],
                device_id=_dev,
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
            if attrs.get("vlans"):
                site_name = None
                for dev in diffsync.objects_to_create["devices"]:
                    if dev.name == ids["device"]:
                        site_name = cls.find_site(cls, diffsync=diffsync, site_id=dev.site_id)
                if not site_name:
                    site_name = "global"
                if attrs["mode"] == "access" and len(attrs["vlans"]) == 1:
                    _vlan = attrs["vlans"][0]
                    try:
                        new_intf.untagged_vlan_id = diffsync.vlan_map[slugify(site_name)][str(_vlan["vlan_id"])]
                    except KeyError:
                        if diffsync.job.kwargs.get("debug"):
                            diffsync.job.log_warning(
                                message=f"Unable to find access VLAN {_vlan['vlan_id']} in {site_name}."
                            )
                else:
                    for _vlan in attrs["vlans"]:
                        try:
                            tagged_vlan = diffsync.vlan_map[slugify(site_name)][str(_vlan["vlan_id"])]
                            if tagged_vlan:
                                new_intf.tagged_vlans.add(tagged_vlan)
                        except KeyError:
                            if diffsync.job.kwargs.get("debug"):
                                diffsync.job.log_warning(
                                    message=f"Unable to find trunked VLAN {_vlan['vlan_id']} in {site_name}."
                                )
            diffsync.objects_to_create["ports"].append(new_intf)
            if ids["device"] not in diffsync.port_map:
                diffsync.port_map[ids["device"]] = {}
            diffsync.port_map[ids["device"]][ids["name"]] = new_intf.id
            return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

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
            if attrs.get("device"):
                _device = attrs["device"]
            else:
                _device = self.device
            site_name = None
            for dev in self.diffsync.objects_to_create["devices"]:
                if dev.name == _device:
                    site_name = self.find_site(diffsync=self.diffsync, site_id=dev.site_id)
            if not site_name:
                site_name = "global"
            if _mode == "access" and len(attrs["vlans"]) == 1:
                _vlan = attrs["vlans"][0]
                try:
                    _port.untagged_vlan_id = self.diffsync.vlan_map[slugify(site_name)][str(_vlan["vlan_id"])]
                except KeyError:
                    if self.diffsync.job.kwargs.get("debug"):
                        self.diffsync.job.log_warning(
                            message=f"Unable to find VLAN {_vlan['vlan_name']} {_vlan['vlan_id']} in {site_name}."
                        )
            else:
                for _vlan in attrs["vlans"]:
                    try:
                        tagged_vlan = self.diffsync.vlan_map[slugify(site_name)][str(_vlan["vlan_id"])]
                        if tagged_vlan:
                            _port.tagged_vlans.add(tagged_vlan)
                    except KeyError:
                        if self.diffsync.job.kwargs.get("debug"):
                            self.diffsync.job.log_warning(
                                message=f"Unable to find VLAN {_vlan['vlan_name']} {_vlan['vlan_id']} in {site_name}."
                            )
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
            diffsync.objects_to_create["cables"].append(new_cable)
            if ids["src_device"] not in diffsync.cable_map:
                diffsync.cable_map[ids["src_device"]] = {}
            if ids["dst_device"] not in diffsync.cable_map:
                diffsync.cable_map[ids["dst_device"]] = {}
            diffsync.cable_map[ids["src_device"]][ids["src_port"]] = new_cable.id
            diffsync.cable_map[ids["dst_device"]][ids["dst_port"]] = new_cable.id
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
                _intf = diffsync.port_map[ids["src_device"]][ids["src_port"]]
                circuit = diffsync.circuit_map[ids["dst_device"]]
            except KeyError:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_warning(
                        message=f"Unable to find source port for {ids['src_device']}: {ids['src_port']} to connect to Circuit {ids['dst_device']}"
                    )
                return None
        elif attrs["src_type"] == "patch panel":
            try:
                _intf = OrmFrontPort.objects.get(device__name=ids["src_device"], name=ids["src_port"])
                circuit = diffsync.circuit_map[ids["dst_device"]]
            except KeyError:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_warning(
                        message=f"Unable to find patch panel port for {ids['src_device']}: {ids['src_port']} to connect to Circuit {ids['dst_device']}"
                    )
                return None
        if attrs["dst_type"] == "interface":
            try:
                circuit = diffsync.circuit_map[ids["src_device"]]
                _intf = diffsync.port_map[ids["dst_device"]][ids["dst_port"]]
            except KeyError:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_warning(
                        message=f"Unable to find destination port for {ids['dst_device']}: {ids['dst_port']} to connect to Circuit {ids['src_device']}"
                    )
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
            _src_port = diffsync.port_map[ids["src_device"]][ids["src_port"]]
        except KeyError:
            if diffsync.job.kwargs.get("debug"):
                diffsync.job.log_warning(
                    message=f"Unable to find source port for {ids['src_device']}: {ids['src_port']} {ids['src_port_mac']}"
                )
            return None
        try:
            _dst_port = diffsync.port_map[ids["dst_device"]][ids["dst_port"]]
        except KeyError:
            if diffsync.job.kwargs.get("debug"):
                diffsync.job.log_warning(
                    message=f"Unable to find destination port for {ids['dst_device']}: {ids['dst_port']} {ids['dst_port_mac']}"
                )
            return None
        if _src_port and _dst_port:
            new_cable = OrmCable(
                termination_a_type=ContentType.objects.get(app_label="dcim", model="interface"),
                termination_a_id=_src_port,
                termination_b_type=ContentType.objects.get(app_label="dcim", model="interface"),
                termination_b_id=_dst_port,
                status_id=diffsync.status_map["connected"],
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
