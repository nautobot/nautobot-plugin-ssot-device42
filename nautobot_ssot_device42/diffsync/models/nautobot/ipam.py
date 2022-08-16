"""DiffSyncModel IPAM subclasses for Nautobot Device42 data sync."""

import re
from diffsync.exceptions import ObjectAlreadyExists
from django.contrib.contenttypes.models import ContentType
from django.forms import ValidationError
from django.utils.text import slugify
from nautobot.dcim.models import Device as OrmDevice
from nautobot.dcim.models import Interface as OrmInterface
from nautobot.dcim.models import Site as OrmSite
from nautobot.extras.choices import CustomFieldTypeChoices
from nautobot.extras.models import CustomField
from nautobot.extras.models import Status as OrmStatus
from nautobot.ipam.models import VLAN as OrmVLAN
from nautobot.ipam.models import VRF as OrmVRF
from nautobot.ipam.models import IPAddress as OrmIPAddress
from nautobot.ipam.models import Prefix as OrmPrefix
from nautobot_ssot_device42.constant import PLUGIN_CFG
from nautobot_ssot_device42.diffsync.models.base.ipam import VLAN, IPAddress, Subnet, VRFGroup
from nautobot_ssot_device42.utils import nautobot


class NautobotVRFGroup(VRFGroup):
    """Nautobot VRFGroup model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create VRF object in Nautobot."""
        _vrf = OrmVRF(name=ids["name"], description=attrs["description"])
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
                _vrf.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(OrmVRF).id)
                _vrf.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _vrf.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update VRF object in Nautobot."""
        _vrf = OrmVRF.objects.get(id=self.uuid)
        if attrs.get("description"):
            _vrf.description = attrs["description"]
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
                _vrf.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(OrmVRF).id)
                _vrf.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _vrf.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete VRF object from Nautobot.

        Because VRF has a direct relationship with many other objects it can't be deleted before anything else.
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        if PLUGIN_CFG.get("delete_on_sync"):
            super().delete()
            if self.diffsync.job.kwargs.get("debug"):
                self.diffsync.job.log_warning(message=f"VRF {self.name} will be deleted.")
            vrf = OrmVRF.objects.get(id=self.uuid)
            self.diffsync.objects_to_delete["vrf"].append(vrf)  # pylint: disable=protected-access
        return self


class NautobotSubnet(Subnet):
    """Nautobot Subnet model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Prefix object in Nautobot."""
        _pf = OrmPrefix(
            prefix=f"{ids['network']}/{ids['mask_bits']}",
            vrf=OrmVRF.objects.get(name=ids["vrf"]),
            description=attrs["description"],
            status=OrmStatus.objects.get(name="Active"),
        )
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
                _pf.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(OrmPrefix).id)
                _pf.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _pf.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Prefix object in Nautobot."""
        _pf = OrmPrefix.objects.get(id=self.uuid)
        if attrs.get("description"):
            _pf.description = attrs["description"]
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
                _pf.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(OrmPrefix).id)
                _pf.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _pf.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Subnet object from Nautobot.

        Because Subnet has a direct relationship with many other objects it can't be deleted before anything else.
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        if PLUGIN_CFG.get("delete_on_sync"):
            super().delete()
            if self.diffsync.job.kwargs.get("debug"):
                self.diffsync.job.log_debug(message=f"Subnet {self.network} will be deleted.")
            subnet = OrmPrefix.objects.get(id=self.uuid)
            self.diffsync.objects_to_delete["subnet"].append(subnet)  # pylint: disable=protected-access
        return self


class NautobotIPAddress(IPAddress):
    """Nautobot IP Address model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create IP Address object in Nautobot."""
        if "/32" in ids["address"] and attrs.get("primary"):
            _pf = OrmPrefix.objects.net_contains(ids["address"])
            # the last Prefix is the most specific and is assumed the one the IP address resides in
            if len(_pf) > 1:
                _range = _pf[len(_pf) - 1]
                _netmask = _range.prefix_length
            else:
                # for the edge case where the DNS answer doesn't reside in a pre-existing Prefix
                _netmask = "32"
            _address = re.sub(r"\/32", f"/{_netmask}", ids["address"])
        else:
            _address = ids["address"]
        _ip = OrmIPAddress(
            address=_address,
            vrf=OrmVRF.objects.get(name=ids["vrf"]) if ids.get("vrf") else None,
            status=OrmStatus.objects.get(name="Active")
            if not attrs.get("available")
            else OrmStatus.objects.get(name="Reserved"),
            description=attrs["label"] if attrs.get("label") else "",
        )
        if attrs.get("device") and attrs.get("interface"):
            try:
                intf = OrmInterface.objects.get(device__name=attrs["device"], name=attrs["interface"])
                _ip.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                _ip.assigned_object_id = intf.id
            except OrmInterface.DoesNotExist as err:
                if diffsync.job.debug:
                    diffsync.job.log_debug(
                        message=f"Unable to find Interface {attrs['interface']} for {attrs['device']}. {err}",
                    )
        if attrs.get("interface"):
            if re.search(r"[Ll]oopback", attrs["interface"]):
                _ip.role = "loopback"
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
                _ip.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(OrmIPAddress).id)
                _ip.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _ip.validated_save()

        # Define regex match for Management interface (ex Management/Mgmt/mgmt/management)
        mgmt = r"^[mM]anagement|^[mM]gmt"

        if attrs.get("device"):
            try:
                _dev = OrmDevice.objects.get(name=attrs["device"])
                # If the Interface is defined, see if it matches regex and the IP is marked primary
                if attrs.get("interface"):
                    if attrs.get("primary"):
                        _intf = OrmInterface.objects.get(name=attrs["interface"], device__name=attrs["device"])
                        nautobot.set_primary_ip_and_mgmt(_ip, _dev, _intf)
                    elif re.search(mgmt, attrs["interface"].strip()) and attrs.get("primary"):
                        _intf = OrmInterface.objects.get(name=attrs["interface"], device__name=attrs["device"])
                        nautobot.set_primary_ip_and_mgmt(_ip, _dev, _intf)
                # else check the label to see if it matches
                elif attrs.get("label"):
                    if re.search(mgmt, attrs["label"]):
                        _intf = nautobot.get_or_create_mgmt_intf(intf_name=attrs["label"], dev=_dev)
                        _ip.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                        _ip.assigned_object_id = _intf.id
                        _ip.validated_save()
                        nautobot.set_primary_ip_and_mgmt(_ip, _dev, _intf)
            except OrmDevice.DoesNotExist:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_debug(message=f"Unable to find Device {attrs['device']} for {_ip.address}.")
                pass
            except OrmInterface.DoesNotExist:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_debug(
                        message=f"Unable to find Interface {attrs['interface']} for device {attrs['device']} for {_ip.address}."
                    )
                pass
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update IPAddress object in Nautobot."""
        try:
            _ipaddr = OrmIPAddress.objects.get(id=self.uuid)
        except OrmIPAddress.DoesNotExist:
            if self.diffsync.job.kwargs.get("debug"):
                self.diffsync.job.log_debug(
                    message="IP Address passed to update but can't be found. This shouldn't happen. Why is this happening?!?!"
                )
            return
        if attrs.get("available"):
            _ipaddr.status = (
                OrmStatus.objects.get(name="Active")
                if not attrs["available"]
                else OrmStatus.objects.get(name="Reserved")
            )
        if attrs.get("label"):
            _ipaddr.description = attrs["label"]
        if (attrs.get("device") and attrs["device"] != "") and (attrs.get("interface") and attrs["interface"] != ""):
            _device = attrs["device"]
            try:
                intf = OrmInterface.objects.get(device__name=_device, name=attrs["interface"])
                _ipaddr.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                _ipaddr.assigned_object_id = intf.id
            except OrmInterface.DoesNotExist as err:
                if self.diffsync.job.kwargs.get("debug"):
                    self.diffsync.job.log_debug(
                        message=f"Unable to find Interface {attrs['interface']} for {attrs['device']}. {err}"
                    )
        elif attrs.get("device") and attrs["device"] == "":
            try:
                intf = OrmInterface.objects.get(device=_ipaddr.assigned_object.device, name=self.interface)
                _ipaddr.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                _ipaddr.assigned_object_id = intf.id
                if hasattr(_ipaddr, "primary_ip4_for"):
                    _dev = OrmDevice.objects.get(name=_ipaddr.primary_ip4_for)
                    _dev.primary_ip4 = None
                elif hasattr(_ipaddr, "primary_ip6_for"):
                    _dev = OrmDevice.objects.get(name=_ipaddr.primary_ip6_for)
                    _dev.primary_ip6 = None
                _dev.validated_save()
            except OrmInterface.DoesNotExist as err:
                if self.diffsync.job.kwargs.get("debug"):
                    self.diffsync.job.log_debug(
                        message=f"Unable to find Interface {attrs['interface']} for {str(_ipaddr.assigned_object.device)} {err}"
                    )
        elif attrs.get("interface") and attrs["interface"] == "":
            try:
                intf = OrmInterface.objects.get(name=self.interface, device__name=attrs["device"])
                _ipaddr.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                _ipaddr.assigned_object_id = intf.id
            except OrmInterface.DoesNotExist as err:
                if self.diffsync.job.kwargs.get("debug"):
                    self.diffsync.job.log_debug(
                        message=f"Unable to find Interface {self.interface} for {attrs['device']}. {err}"
                    )
        elif attrs.get("device") and attrs["device"] != "":
            try:
                intf = OrmInterface.objects.get(name=self.label, device__name=attrs["device"])
                _ipaddr.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                _ipaddr.assigned_object_id = intf.id
            except OrmInterface.DoesNotExist as err:
                if self.diffsync.job.kwargs.get("debug"):
                    self.diffsync.job.log_debug(
                        message=f"Unable to find Interface {self.interface} for {attrs['device']} with label {self.label}. {err}"
                    )
        if attrs.get("primary") and attrs["primary"] is not None:
            dev, _device, intf, _intf = None, False, None, False
            try:
                if attrs.get("device") and attrs["device"] != "":
                    dev = attrs["device"]
                else:
                    dev = self.device
                _device = OrmDevice.objects.get(name=dev)
            except OrmDevice.DoesNotExist as err:
                print(f"Unable to find Device {dev} {err}")
            if attrs.get("interface") and attrs["interface"] != "":
                intf = attrs["interface"]
            elif self.interface != "":
                intf = self.interface
            elif attrs.get("label") and attrs["label"] != "":
                intf = attrs["label"]
            elif self.label != "":
                intf = self.label
            if _device and intf:
                try:
                    _intf = OrmInterface.objects.get(name=intf, device=_device)
                    nautobot.set_primary_ip_and_mgmt(ipaddr=_ipaddr, dev=_device, intf=_intf)
                except OrmInterface.DoesNotExist as err:
                    print(f"Unable to find Interface {intf} for Device {_device.name} {err}")
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
                _ipaddr.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(OrmIPAddress).id)
                _ipaddr.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        try:
            _ipaddr.validated_save()
            return super().update(attrs)
        except ValidationError as err:
            print(f"Unable to update IP Address {self.address} with {attrs} {err}")
            return None

    def delete(self):
        """Delete IPAddress object from Nautobot.

        Because IPAddress has a direct relationship with many other objects it can't be deleted before anything else.
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        if PLUGIN_CFG.get("delete_on_sync"):
            super().delete()
            if self.diffsync.job.kwargs.get("debug"):
                self.diffsync.job.log_debug(message=f"IP Address {self.address} will be deleted. {self}")
            ipaddr = OrmIPAddress.objects.get(id=self.uuid)
            self.diffsync.objects_to_delete["ipaddr"].append(ipaddr)  # pylint: disable=protected-access
        return self


class NautobotVLAN(VLAN):
    """Nautobot VLAN model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create VLAN object in Nautobot."""
        _site = None
        if ids["building"] != "Unknown":
            try:
                _site = OrmSite.objects.get(name=ids["building"])
            except OrmSite.DoesNotExist as err:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_debug(message=f"Unable to find Site {ids['building']}. {err}")
        try:
            _vlan = OrmVLAN.objects.get(name=ids["name"], vid=ids["vlan_id"], site=_site)
        except OrmVLAN.DoesNotExist:
            _vlan = OrmVLAN(
                name=ids["name"],
                vid=ids["vlan_id"],
                description=attrs["description"],
                status=OrmStatus.objects.get(name="Active"),
            )
        if _site:
            _vlan.site = _site
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(OrmVLAN).id)
                _vlan.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        try:
            _vlan.validated_save()
        except ObjectAlreadyExists as err:
            if diffsync.job.kwargs.get("debug"):
                diffsync.job.log_debug(message=f"{ids['name']} already exists. {err}")
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update VLAN object in Nautobot."""
        _vlan = OrmVLAN.objects.get(id=self.uuid)
        if attrs.get("description"):
            self.description = attrs["description"]
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(OrmVLAN).id)
                _vlan.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _vlan.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete VLAN object from Nautobot.

        Because VLAN has a direct relationship with many other objects it can't be deleted before anything else.
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        if PLUGIN_CFG.get("delete_on_sync"):
            super().delete()
            if self.diffsync.job.kwargs.get("debug"):
                self.diffsync.job.log_debug(message=f"VLAN {self.name} {self.vlan_id} {self.building} will be deleted.")
            vlan = OrmVLAN.objects.get(id=self.uuid)
            self.diffsync.objects_to_delete["vlan"].append(vlan)  # pylint: disable=protected-access
        return self