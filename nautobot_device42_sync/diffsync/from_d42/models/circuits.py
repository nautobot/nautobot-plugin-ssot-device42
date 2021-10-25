"""DiffSyncModel DCIM subclasses for Nautobot Device42 data sync."""

from typing import Optional, List
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from diffsync import DiffSyncModel
from nautobot.dcim.models import Cable as NautobotCable
from nautobot.circuits.models import Provider as NautobotProvider
from nautobot.circuits.models import Circuit as NautobotCircuit
from nautobot.circuits.models import CircuitTermination as NautobotCT
from nautobot.dcim.models import Device as NautobotDevice
from nautobot.dcim.models import Interface as NautobotInterface
from nautobot.extras.models import Status as NautobotStatus
from nautobot_device42_sync.constant import INTF_SPEED_MAP
from nautobot_device42_sync.diffsync import nbutils
from nautobot_device42_sync.diffsync import d42utils
from netutils.bandwidth import name_to_kbits


class Provider(DiffSyncModel):
    """Device42 Provider model."""

    _modelname = "provider"
    _identifiers = ("name",)
    _attributes = ("notes", "vendor_url", "vendor_acct", "contact_info", "vendor_contact1", "vendor_contact2")
    _children = {}

    name: str
    notes: Optional[str]
    vendor_url: Optional[str]
    vendor_acct: Optional[str]
    contact_info: Optional[str]
    vendor_contact1: Optional[str]
    vendor_contact2: Optional[str]
    tags: Optional[List[str]]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Provider object in Nautobot."""
        try:
            _provider = NautobotProvider.objects.get(name=ids["name"])
        except NautobotProvider.DoesNotExist:
            _provider = NautobotProvider(
                name=ids["name"],
                slug=slugify(ids["name"]),
                account=attrs["vendor_acct"] if attrs.get("vendor_acct") else "",
                portal_url=attrs["vendor_url"] if attrs.get("vendor_url") else "",
                noc_contact=attrs["vendor_contact1"] if attrs.get("vendor_contact1") else "",
                admin_contact=attrs["vendor_contact2"] if attrs.get("vendor_contact2") else "",
                comments=attrs["notes"] if attrs.get("notes") else "",
            )
            if attrs.get("tags"):
                for _tag in nbutils.get_tags(attrs["tags"]):
                    _provider.tags.add(_tag)
            _provider.validated_save()
            return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Provider object in Nautobot."""
        _prov = NautobotProvider.objects.get(name=self.name)
        if attrs.get("notes"):
            _prov.comments = attrs["notes"]
        if attrs.get("vendor_url"):
            _prov.portal_url = attrs["vendor_url"]
        if attrs.get("vendor_acct"):
            _prov.account = attrs["vendor_acct"]
        if attrs.get("vendor_contact1"):
            _prov.noc_contact = attrs["vendor_contact1"]
        if attrs.get("vendor_contact2"):
            _prov.admin_contact = attrs["vendor_contact2"]
        _prov.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Provider object from Nautobot.

        Because Provider has a direct relationship with Circuits it can't be deleted before them.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"Provider {self.name} will be deleted.")
        super().delete()
        provider = NautobotProvider.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["provider"].append(provider)  # pylint: disable=protected-access
        return self


class Circuit(DiffSyncModel):
    """Device42 TelcoCircuit model."""

    _modelname = "circuit"
    _identifiers = (
        "circuit_id",
        "provider",
    )
    _attributes = (
        "notes",
        "type",
        "status",
        "install_date",
        "origin_int",
        "origin_dev",
        "endpoint_int",
        "endpoint_dev",
        "bandwidth",
        "tags",
    )
    _children = {}
    circuit_id: str
    provider: str
    notes: Optional[str]
    type: str
    status: str
    install_date: Optional[str]
    origin_int: Optional[str]
    origin_dev: Optional[str]
    endpoint_int: Optional[str]
    endpoint_dev: Optional[str]
    bandwidth: Optional[str]
    tags: Optional[List[str]]

    @staticmethod
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

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Circuit object in Nautobot."""
        try:
            NautobotCircuit.objects.get(cid=ids["circuit_id"])
        except NautobotCircuit.DoesNotExist:
            _circuit = NautobotCircuit(
                cid=ids["circuit_id"],
                provider=NautobotProvider.objects.get(name=ids["provider"]),
                type=d42utils.verify_circuit_type(attrs["type"]),
                status=NautobotStatus.objects.get(name=cls.get_circuit_status(attrs["status"])),
                install_date=attrs["install_date"] if attrs.get("install_date") else None,
                commit_rate=name_to_kbits(attrs["bandwidth"]) if attrs.get("bandwidth") else None,
                comments=attrs["notes"] if attrs.get("notes") else "",
            )
            if attrs.get("origin_int") and attrs.get("origin_dev"):
                cls.connect_circuit_to_device(
                    intf=attrs["origin_int"], dev=attrs["origin_dev"], term_side="A", circuit=_circuit
                )
            if attrs.get("endpoint_int") and attrs.get("endpoint_dev"):
                cls.connect_circuit_to_device(
                    intf=attrs["endpoint_int"], dev=attrs["endpoint_dev"], term_side="Z", circuit=_circuit
                )
            if attrs.get("tags"):
                for _tag in nbutils.get_tags(attrs["tags"]):
                    _circuit.tags.add(_tag)
            _circuit.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Circuit object in Nautobot."""
        _circuit = NautobotCircuit.objects.get(cid=self.circuit_id)
        if attrs.get("notes"):
            _circuit.comments = attrs["notes"]
        if attrs.get("type"):
            _circuit.type = d42utils.verify_circuit_type(attrs["type"])
        if attrs.get("status"):
            _circuit.status = NautobotStatus.objects.get(name=self.get_circuit_status(attrs["status"]))
        if attrs.get("install_date"):
            _circuit.install_date = attrs["install_date"]
        if attrs.get("bandwidth"):
            _circuit.commit_rate = name_to_kbits(attrs["bandwidth"])
        if attrs.get("origin_int") and attrs.get("origin_dev"):
            self.connect_circuit_to_device(
                intf=attrs["origin_int"], dev=attrs["origin_dev"], term_side="A", circuit=_circuit
            )
        if attrs.get("endpoint_int") and attrs.get("endpoint_dev"):
            self.connect_circuit_to_device(
                intf=attrs["endpoint_int"], dev=attrs["endpoint_dev"], term_side="Z", circuit=_circuit
            )
        _circuit.validated_save()
        return super().update(attrs)

    def connect_circuit_to_device(self, intf: str, dev: str, term_side: str, circuit: NautobotCircuit):
        """Method to handle Circuit Termination to a Device.

        Args:
            intf (str): Interface of Device to connect Circuit Termination.
            dev (str): [description]
            term_side (str): [description]
            circuit (NautobotCircuit): [description]
        """
        try:
            _intf = NautobotInterface.objects.get(name=intf, device=NautobotDevice.objects.get(name=dev))
            origin_term = NautobotCT(
                circuit=circuit,
                term_side=term_side,
                site=_intf.device.site,
                port_speed=INTF_SPEED_MAP[_intf.type],
            )
            origin_term.validated_save()
            if _intf and not _intf.cable and not origin_term.cable:
                new_cable = NautobotCable(
                    termination_a_type=ContentType.objects.get(app_label="dcim", model="interface"),
                    termination_a_id=_intf.id,
                    termination_b_type=ContentType.objects.get(app_label="circuits", model="circuittermination"),
                    termination_b_id=origin_term.id,
                    status=NautobotStatus.objects.get(name="Connected"),
                    color=nbutils.get_random_color(),
                )
                new_cable.validated_save()
        except NautobotDevice.DoesNotExist as err:
            print(f"Unable to find {dev} {err}")
        except NautobotInterface.DoesNotExist as err:
            print(f"Unable to find {intf} {dev} {err}")

    def delete(self):
        """Delete Provider object from Nautobot.

        Because Provider has a direct relationship with Circuits it can't be deleted before them.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"Circuit {self.circuit_id} will be deleted.")
        circuit = NautobotCircuit.objects.get(cid=self.get_identifiers()["circuit_id"])
        circuit.delete()
        super().delete()
        return self