"""Unit tests for the Device42 DiffSync adapter class."""
import json
import uuid
from unittest.mock import MagicMock
from django.test import override_settings
from django.contrib.contenttypes.models import ContentType
from nautobot.utilities.testing import TransactionTestCase
from nautobot.extras.models import Job, JobResult
from parameterized import parameterized
from nautobot_ssot_device42.diffsync.adapters.device42 import Device42Adapter, get_circuit_status
from nautobot_ssot_device42.jobs import Device42DataSource


def load_json(path):
    """Load a json file."""
    with open(path, encoding="utf-8") as file:
        return json.loads(file.read())


BUILDING_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_buildings_recv.json")
ROOM_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_rooms_recv.json")
RACK_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_racks_recv.json")
VENDOR_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_vendors_recv.json")
HARDWARE_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_hardware_models_recv.json")
VRFGROUP_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_vrfgroups_recv.json")
VLAN_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_vlans_with_location.json")
SUBNET_DEFAULT_CFS_FIXTURE = load_json(
    "./nautobot_ssot_device42/tests/fixtures/get_subnet_default_custom_fields_recv.json"
)
SUBNET_CFS_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_subnet_custom_fields_recv.json")
SUBNET_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_subnets.json")
DEVICE_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_devices_recv.json")
CLUSTER_MEMBER_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_cluster_members_recv.json")


class Device42AdapterTestCase(TransactionTestCase):
    """Test the Device42Adapter class."""

    databases = ("default", "job_logs")

    def setUp(self):
        """Method to initialize test case."""
        # Create a mock client
        self.d42_client = MagicMock()
        self.d42_client.get_buildings.return_value = BUILDING_FIXTURE
        self.d42_client.get_rooms.return_value = ROOM_FIXTURE
        self.d42_client.get_racks.return_value = RACK_FIXTURE
        self.d42_client.get_vendors.return_value = VENDOR_FIXTURE
        self.d42_client.get_hardware_models.return_value = HARDWARE_FIXTURE
        self.d42_client.get_vrfgroups.return_value = VRFGROUP_FIXTURE
        self.d42_client.get_vlans_with_location.return_value = VLAN_FIXTURE
        self.d42_client.get_subnet_default_custom_fields.return_value = SUBNET_DEFAULT_CFS_FIXTURE
        self.d42_client.get_subnet_custom_fields.return_value = SUBNET_CFS_FIXTURE
        self.d42_client.get_subnets.return_value = SUBNET_FIXTURE
        self.d42_client.get_devices.return_value = DEVICE_FIXTURE
        self.d42_client.get_cluster_members.return_value = CLUSTER_MEMBER_FIXTURE

        self.job = Device42DataSource()
        self.job.job_result = JobResult.objects.create(
            name=self.job.class_path, obj_type=ContentType.objects.get_for_model(Job), user=None, job_id=uuid.uuid4()
        )
        self.device42 = Device42Adapter(job=self.job, sync=None, client=self.d42_client)
        self.device42.d42_building_sitecode_map = {"AUS": "Austin", "LAX": "Los Angeles"}

    @override_settings(PLUGINS_CONFIG={"nautobot_ssot_device42": {"customer_is_facility": True}})
    def test_data_loading(self):
        """Test the load() function."""

        self.device42.load_buildings()
        self.assertEqual(
            {site["name"] for site in BUILDING_FIXTURE},
            {site.get_unique_id() for site in self.device42.get_all("building")},
        )
        self.device42.load_rooms()
        self.assertEqual(
            {f"{room['name']}__{room['building']}" for room in ROOM_FIXTURE},
            {room.get_unique_id() for room in self.device42.get_all("room")},
        )
        self.device42.load_racks()
        self.assertEqual(
            {f"{rack['name']}__{rack['building']}__{rack['room']}" for rack in RACK_FIXTURE},
            {rack.get_unique_id() for rack in self.device42.get_all("rack")},
        )
        self.device42.load_vendors()
        self.assertEqual(
            {vendor["name"] for vendor in VENDOR_FIXTURE},
            {vendor.get_unique_id() for vendor in self.device42.get_all("vendor")},
        )
        self.device42.load_hardware_models()
        self.assertEqual(
            {model["name"] for model in HARDWARE_FIXTURE},
            {model.get_unique_id() for model in self.device42.get_all("hardware")},
        )
        self.device42.load_vrfgroups()
        self.assertEqual(
            {vrf["name"] for vrf in VRFGROUP_FIXTURE},
            {vrf.get_unique_id() for vrf in self.device42.get_all("vrf")},
        )
        self.device42.load_vlans()
        self.assertEqual(
            {f"{vlan['vid']}__{self.device42.d42_building_sitecode_map[vlan['customer']]}" for vlan in VLAN_FIXTURE},
            {vlan.get_unique_id() for vlan in self.device42.get_all("vlan")},
        )
        self.device42.load_subnets()
        self.assertEqual(
            {f"{net['network']}__{net['mask_bits']}__{net['vrf']}" for net in SUBNET_FIXTURE},
            {net.get_unique_id() for net in self.device42.get_all("subnet")},
        )
        self.device42.load_devices_and_clusters()
        self.assertEqual(
            {dev["name"] for dev in DEVICE_FIXTURE},
            {dev.get_unique_id() for dev in self.device42.get_all("device")},
        )

    statuses = [
        ("Production", "Production", "Active"),
        ("Provisioning", "Provisioning", "Provisioning"),
        ("Canceled", "Canceled", "Deprovisioning"),
        ("Decommissioned", "Decommissioned", "Decommissioned"),
        ("Ordered", "Ordered", "Offline"),
    ]

    @parameterized.expand(statuses, skip_on_empty=True)
    def test_get_circuit_status(self, name, sent, received):  # pylint: disable=unused-argument
        """Test get_circuit_status success."""
        self.assertEqual(get_circuit_status(sent), received)

    def test_filter_ports(self):
        """Method to test filter_ports success."""
        vlan_ports = load_json("./nautobot_ssot_device42/tests/fixtures/ports_with_vlans.json")
        no_vlan_ports = load_json("./nautobot_ssot_device42/tests/fixtures/ports_wo_vlans.json")
        merged_ports = load_json("./nautobot_ssot_device42/tests/fixtures/merged_ports.json")
        result = self.device42.filter_ports(vlan_ports, no_vlan_ports)
        self.assertEqual(merged_ports, result)
