"""Unit tests for the Device42 DiffSync adapter class."""
import json
import uuid
from unittest.mock import MagicMock, patch
from diffsync.exceptions import ObjectNotFound
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from nautobot.utilities.testing import TransactionTestCase
from nautobot.extras.models import Job, JobResult
from parameterized import parameterized
from nautobot_ssot_device42.diffsync.adapters.device42 import (
    Device42Adapter,
    get_dns_a_record,
    get_circuit_status,
    get_site_from_mapping,
)
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
PORTS_W_VLANS_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_ports_with_vlans_recv.json")
PORTS_WO_VLANS_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_ports_wo_vlans_recv.json")
PORT_CUSTOM_FIELDS = load_json("./nautobot_ssot_device42/tests/fixtures/get_port_custom_fields_recv.json")


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
        self.d42_client.get_ports_with_vlans.return_value = PORTS_W_VLANS_FIXTURE
        self.d42_client.get_ports_wo_vlans.return_value = PORTS_WO_VLANS_FIXTURE
        self.d42_client.get_port_custom_fields.return_value = PORT_CUSTOM_FIELDS

        self.job = Device42DataSource()
        self.job.log_info = MagicMock()
        self.job.log_warning = MagicMock()
        self.job.job_result = JobResult.objects.create(
            name=self.job.class_path, obj_type=ContentType.objects.get_for_model(Job), user=None, job_id=uuid.uuid4()
        )
        self.device42 = Device42Adapter(job=self.job, sync=None, client=self.d42_client)
        self.mock_device = MagicMock()
        self.mock_device.name = "cluster1 - Switch 1"
        self.mock_device.os_version = "1.0"
        self.cluster_dev = MagicMock()
        self.cluster_dev.name = "cluster1"
        self.master_dev = MagicMock()
        self.master_dev.name = "cluster1"
        self.master_dev.os_version = ""

    @patch(
        "nautobot_ssot_device42.diffsync.adapters.device42.PLUGIN_CFG",
        {"customer_is_facility": True},
    )
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
            {
                f"{vlan['vid']}__{slugify(self.device42.d42_building_sitecode_map[vlan['customer']])}"
                for vlan in VLAN_FIXTURE
            },
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
        self.device42.load_ports()
        self.assertEqual(
            {f"{port['device_name']}__{port['port_name']}" for port in PORTS_WO_VLANS_FIXTURE},
            {port.get_unique_id() for port in self.device42.get_all("port")},
        )

    def test_assign_version_to_master_devices_with_valid_os_version(self):
        """Validate functionality of the assign_version_to_master_devices() function with valid os_version."""
        self.device42.device42_clusters = {"cluster1": {"members": [self.mock_device]}}
        self.device42.get_all = MagicMock()
        self.device42.get_all.return_value = [self.cluster_dev]

        self.device42.get = MagicMock()
        self.device42.get.side_effect = [self.mock_device, self.master_dev]

        self.device42.assign_version_to_master_devices()

        self.assertEqual(self.master_dev.os_version, "1.0")
        self.job.log_info.assert_called_once_with(message="Assigning 1.0 version to cluster1.")

    def test_assign_version_to_master_devices_with_blank_os_version(self):
        """Validate functionality of the assign_version_to_master_devices() function with blank os_version."""
        self.mock_device.os_version = ""
        self.device42.device42_clusters = {"cluster1": {"members": [self.mock_device]}}

        self.device42.get_all = MagicMock()
        self.device42.get_all.return_value = [self.cluster_dev]

        self.device42.get = MagicMock()
        self.device42.get.side_effect = [self.mock_device, self.master_dev]

        self.device42.assign_version_to_master_devices()

        self.assertEqual(self.master_dev.os_version, "")
        self.job.log_info.assert_called_once_with(
            message="Software version for cluster1 - Switch 1 is blank so will not assign version to cluster1."
        )

    def test_assign_version_to_master_devices_with_missing_cluster_host(self):
        """Validate functionality of the assign_version_to_master_devices() function with missing cluster host in device42_clusters."""
        self.device42.get_all = MagicMock()
        self.device42.get_all.return_value = [self.cluster_dev]

        self.device42.get = MagicMock()
        self.device42.get.return_value = KeyError

        self.device42.assign_version_to_master_devices()
        self.job.log_warning.assert_called_once_with(
            message="Unable to find cluster host in device42_clusters dictionary. 'cluster1'"
        )

    def test_assign_version_to_master_devices_with_missing_master_device(self):
        """Validate functionality of the assign_version_to_master_devices() function with missing master device."""
        self.device42.device42_clusters = {"cluster1": {"members": [self.mock_device]}}
        self.device42.get_all = MagicMock()
        self.device42.get_all.return_value = [self.cluster_dev]

        self.device42.get = MagicMock()
        self.device42.get.side_effect = [self.mock_device, ObjectNotFound]

        self.device42.assign_version_to_master_devices()
        self.job.log_warning.assert_called_once_with(
            message="Unable to find VC Master Device cluster1 to assign version."
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

    @patch(
        "nautobot_ssot_device42.diffsync.adapters.device42.PLUGIN_CFG",
        {"hostname_mapping": [{"^aus.+|AUS.+": "austin"}]},
    )
    def test_get_site_from_mapping(self):
        """Test the get_site_from_mapping method."""
        expected = "austin"
        self.assertEqual(get_site_from_mapping(device_name="aus.test.com"), expected)

    @patch(
        "nautobot_ssot_device42.diffsync.adapters.device42.PLUGIN_CFG",
        {"hostname_mapping": [{"^aus.+|AUS.+": "austin"}]},
    )
    def test_get_site_from_mapping_missing_site(self):
        """Test the get_site_from_mapping method with missing site."""
        expected = ""
        self.assertEqual(get_site_from_mapping(device_name="dfw.test.com"), expected)

    @patch("nautobot_ssot_device42.diffsync.adapters.device42.is_fqdn_resolvable", return_value=True)
    @patch("nautobot_ssot_device42.diffsync.adapters.device42.fqdn_to_ip", return_value="192.168.0.1")
    def test_get_dns_a_record_success(self, mock_fqdn_to_ip, mock_is_fqdn_resolvable):
        """Test the get_dns_a_record method success."""
        result = get_dns_a_record("example.com")
        mock_is_fqdn_resolvable.assert_called_once_with("example.com")
        mock_fqdn_to_ip.assert_called_once_with("example.com")
        self.assertEqual(result, "192.168.0.1")

    @patch("nautobot_ssot_device42.diffsync.adapters.device42.is_fqdn_resolvable", return_value=False)
    @patch("nautobot_ssot_device42.diffsync.adapters.device42.fqdn_to_ip")
    def test_get_dns_a_record_failure(self, mock_fqdn_to_ip, mock_is_fqdn_resolvable):
        """Test the get_dns_a_record method failure."""
        result = get_dns_a_record("invalid-hostname")
        mock_is_fqdn_resolvable.assert_called_once_with("invalid-hostname")
        mock_fqdn_to_ip.assert_not_called()
        self.assertFalse(result)

    @patch(
        "nautobot_ssot_device42.diffsync.adapters.device42.PLUGIN_CFG",
        {"hostname_mapping": [{"^nyc.+|NYC.+": "new-york-city"}]},
    )
    def test_get_building_for_device_from_mapping(self):
        """Test the get_building_for_device method using site_mapping."""
        mock_dev_record = {"name": "nyc.test.com"}
        expected = "new-york-city"
        self.assertEqual(self.device42.get_building_for_device(dev_record=mock_dev_record), expected)

    def test_get_building_for_device_from_device_record(self):
        """Test the get_building_for_device method from device record."""
        mock_dev_record = {"name": "la.test.com", "building": "los-angeles"}
        expected = "los-angeles"
        self.assertEqual(self.device42.get_building_for_device(dev_record=mock_dev_record), expected)

    def test_get_building_for_device_missing_building(self):
        """Test the get_building_for_device method with missing building."""
        mock_dev_record = {"name": "la.test.com", "building": None}
        expected = ""
        self.assertEqual(self.device42.get_building_for_device(dev_record=mock_dev_record), expected)

    def test_filter_ports(self):
        """Method to test filter_ports success."""
        vlan_ports = load_json("./nautobot_ssot_device42/tests/fixtures/ports_with_vlans.json")
        no_vlan_ports = load_json("./nautobot_ssot_device42/tests/fixtures/ports_wo_vlans.json")
        merged_ports = load_json("./nautobot_ssot_device42/tests/fixtures/merged_ports.json")
        result = self.device42.filter_ports(vlan_ports, no_vlan_ports)
        self.assertEqual(merged_ports, result)

    @patch("nautobot_ssot_device42.diffsync.adapters.device42.get_dns_a_record")
    @patch("nautobot_ssot_device42.diffsync.adapters.device42.Device42Adapter.find_ipaddr")
    @patch("nautobot_ssot_device42.diffsync.adapters.device42.Device42Adapter.get_management_intf")
    @patch("nautobot_ssot_device42.diffsync.adapters.device42.Device42Adapter.add_management_interface")
    @patch("nautobot_ssot_device42.diffsync.adapters.device42.Device42Adapter.add_ipaddr")
    def test_set_primary_from_dns_with_valid_fqdn(  # pylint: disable=too-many-arguments
        self, mock_add_ipaddr, mock_add_mgmt_intf, mock_get_mgmt_intf, mock_find_ipaddr, mock_dns_a_record
    ):
        """Method to test the set_primary_from_dns functionality with valid FQDN."""
        mock_dns_a_record.return_value = "10.0.0.1"
        mock_find_ipaddr.return_value = False
        mock_mgmt_interface = MagicMock(name="mgmt_intf")
        mock_mgmt_interface.name = "eth0"
        mock_get_mgmt_intf.return_value = mock_mgmt_interface
        mock_add_mgmt_intf.return_value = mock_mgmt_interface
        mock_ip = MagicMock()
        mock_add_ipaddr.return_value = mock_ip
        dev_name = "router.test-example.com"
        self.device42.set_primary_from_dns(dev_name)

        mock_dns_a_record.assert_called_once_with(dev_name=dev_name)
        mock_find_ipaddr.assert_called_once_with(address="10.0.0.1")
        mock_get_mgmt_intf.assert_called_once_with(dev_name=dev_name)
        mock_add_mgmt_intf.assert_not_called()
        mock_add_ipaddr.assert_called_once_with(address="10.0.0.1/32", dev_name=dev_name, interface="eth0")
        self.assertEqual(mock_ip.device, "router.test-example.com")
        self.assertEqual(mock_ip.interface, "eth0")
        self.assertTrue(mock_ip.primary)

    @patch("nautobot_ssot_device42.diffsync.adapters.device42.get_dns_a_record")
    @patch("nautobot_ssot_device42.diffsync.adapters.device42.Device42Adapter.find_ipaddr")
    @patch("nautobot_ssot_device42.diffsync.adapters.device42.Device42Adapter.get_management_intf")
    @patch("nautobot_ssot_device42.diffsync.adapters.device42.Device42Adapter.add_management_interface")
    @patch("nautobot_ssot_device42.diffsync.adapters.device42.Device42Adapter.add_ipaddr")
    def test_set_primary_from_dns_with_invalid_fqdn(  # pylint: disable=too-many-arguments
        self, mock_add_ipaddr, mock_add_mgmt_intf, mock_get_mgmt_intf, mock_find_ipaddr, mock_dns_a_record
    ):
        """Method to test the set_primary_from_dns functionality with invalid FQDN."""
        mock_dns_a_record.return_value = ""
        dev_name = "router.test-example.com"
        self.job.log_warning = MagicMock()
        self.device42.set_primary_from_dns(dev_name=dev_name)

        mock_dns_a_record.assert_called_once_with(dev_name=dev_name)
        mock_find_ipaddr.assert_not_called()
        mock_get_mgmt_intf.assert_not_called()
        mock_add_mgmt_intf.assert_not_called()
        mock_add_ipaddr.assert_not_called()
        self.job.log_warning.assert_called_once()
