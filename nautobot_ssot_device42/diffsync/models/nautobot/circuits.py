"""DiffSyncModel Circuit subclasses for Nautobot Device42 data sync."""

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from nautobot.circuits.models import Circuit as OrmCircuit
from nautobot.circuits.models import CircuitTermination as OrmCT
from nautobot.circuits.models import Provider as OrmProvider
from nautobot.dcim.models import Cable as OrmCable
from nautobot.dcim.models import Device as OrmDevice
from nautobot.dcim.models import Interface as OrmInterface
from nautobot.extras.models import Status as OrmStatus
from nautobot_ssot_device42.constant import INTF_SPEED_MAP, PLUGIN_CFG
from nautobot_ssot_device42.diffsync.models.base.circuits import Circuit, Provider
from nautobot_ssot_device42.utils import nautobot


class NautobotProvider(Provider):
    """Nautobot Provider model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Provider object in Nautobot."""
        try:
            _provider = OrmProvider.objects.get(name=ids["name"])
        except OrmProvider.DoesNotExist:
            _provider = OrmProvider(
                name=ids["name"],
                slug=slugify(ids["name"]),
                account=attrs["vendor_acct"] if attrs.get("vendor_acct") else "",
                portal_url=attrs["vendor_url"] if attrs.get("vendor_url") else "",
                noc_contact=attrs["vendor_contact1"] if attrs.get("vendor_contact1") else "",
                admin_contact=attrs["vendor_contact2"] if attrs.get("vendor_contact2") else "",
                comments=attrs["notes"] if attrs.get("notes") else "",
            )
            if attrs.get("tags"):
                for _tag in nautobot.get_tags(attrs["tags"]):
                    _provider.tags.add(_tag)
            try:
                _provider.validated_save()
                return super().create(ids=ids, diffsync=diffsync, attrs=attrs)
            except ValidationError as err:
                if diffsync.job.kwargs.get("debug"):
                    diffsync.job.log_warning(message=f"Unable to create {ids['name']} provider. {err}")
                return None

    def update(self, attrs):
        """Update Provider object in Nautobot."""
        _prov = OrmProvider.objects.get(id=self.uuid)
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
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        if PLUGIN_CFG.get("delete_on_sync"):
            self.diffsync.job.log_warning(message=f"Provider {self.name} will be deleted.")
            super().delete()
            provider = OrmProvider.objects.get(id=self.uuid)
            self.diffsync.objects_to_delete["provider"].append(provider)  # pylint: disable=protected-access
        return self


class NautobotCircuit(Circuit):
    """Nautobot TelcoCircuit model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Circuit object in Nautobot."""
        try:
            OrmCircuit.objects.get(cid=ids["circuit_id"])
        except OrmCircuit.DoesNotExist:
            _circuit = OrmCircuit(
                cid=ids["circuit_id"],
                provider=OrmProvider.objects.get(name=ids["provider"]),
                type=nautobot.verify_circuit_type(attrs["type"]),
                status=OrmStatus.objects.get(name=attrs["status"]),
                install_date=attrs["install_date"] if attrs.get("install_date") else None,
                commit_rate=attrs["bandwidth"] if attrs.get("bandwidth") else None,
                comments=attrs["notes"] if attrs.get("notes") else "",
            )
            if attrs.get("tags"):
                for _tag in nautobot.get_tags(attrs["tags"]):
                    _circuit.tags.add(_tag)
            _circuit.validated_save()
            if attrs.get("origin_int") and attrs.get("origin_dev"):
                cls.connect_circuit_to_device(
                    intf=attrs["origin_int"], dev=attrs["origin_dev"], term_side="A", circuit=_circuit
                )
            if attrs.get("endpoint_int") and attrs.get("endpoint_dev"):
                cls.connect_circuit_to_device(
                    intf=attrs["endpoint_int"], dev=attrs["endpoint_dev"], term_side="Z", circuit=_circuit
                )
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Circuit object in Nautobot."""
        _circuit = OrmCircuit.objects.get(id=self.uuid)
        if attrs.get("notes"):
            _circuit.comments = attrs["notes"]
        if attrs.get("type"):
            _circuit.type = nautobot.verify_circuit_type(attrs["type"])
        if attrs.get("status"):
            _circuit.status = OrmStatus.objects.get(name=attrs["status"])
        if attrs.get("install_date"):
            _circuit.install_date = attrs["install_date"]
        if attrs.get("bandwidth"):
            _circuit.commit_rate = attrs["bandwidth"]
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

    @staticmethod
    def connect_circuit_to_device(intf: str, dev: str, term_side: str, circuit: OrmCircuit):
        """Method to handle Circuit Termination to a Device.

        Args:
            intf (str): Interface of Device to connect Circuit Termination.
            dev (str): Device with respective interface to connect Circuit to.
            term_side (str): Which side of the CircuitTermination this connection is on, A or Z.
            circuit (OrmCircuit): The actual Circuit object that the CircuitTermination is connecting to.
        """
        try:
            _intf = OrmInterface.objects.get(name=intf, device=OrmDevice.objects.get(name=dev))
            try:
                _term = OrmCT.objects.get(circuit=circuit, term_side=term_side)
            except OrmCT.DoesNotExist:
                _term = OrmCT(
                    circuit=circuit,
                    term_side=term_side,
                    site=_intf.device.site,
                    port_speed=INTF_SPEED_MAP[_intf.type],
                )
                _term.validated_save()
            if _intf and not _intf.cable and not _term.cable:
                new_cable = OrmCable(
                    termination_a_type=ContentType.objects.get(app_label="dcim", model="interface"),
                    termination_a_id=_intf.id,
                    termination_b_type=ContentType.objects.get(app_label="circuits", model="circuittermination"),
                    termination_b_id=_term.id,
                    status=OrmStatus.objects.get(name="Connected"),
                    color=nautobot.get_random_color(),
                )
                new_cable.validated_save()
        except OrmDevice.DoesNotExist as err:
            print(f"Unable to find {dev} {err}")
        except OrmInterface.DoesNotExist as err:
            print(f"Unable to find {intf} {dev} {err}")

    def delete(self):
        """Delete Provider object from Nautobot.

        Because Provider has a direct relationship with Circuits it can't be deleted before them.
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        if PLUGIN_CFG.get("delete_on_sync"):
            self.diffsync.job.log_warning(message=f"Circuit {self.circuit_id} will be deleted.")
            super().delete()
            circuit = OrmCircuit.objects.get(id=self.uuid)
            self.diffsync.objects_to_delete["circuit"].append(circuit)  # pylint: disable=protected-access
        return self
