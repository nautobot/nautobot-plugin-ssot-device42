"""Tests of Device42 utility methods."""

import json
import responses
from nautobot.utilities.testing import TestCase
from parameterized import parameterized
from nautobot_ssot_device42.utils import device42


def load_json(path):
    """Load a json file."""
    with open(path, encoding="utf-8") as file:
        return json.loads(file.read())


class TestUtilsDevice42(TestCase):
    """Test Device42 util methods."""

    def test_merge_offset_dicts(self):
        first_dict = {"total_count": 10, "limit": 2, "offset": 2, "Objects": ["a", "b"]}
        second_dict = {"total_count": 10, "limit": 2, "offset": 4, "Objects": ["c", "d"]}
        result_dict = {"total_count": 10, "limit": 2, "offset": 4, "Objects": ["a", "b", "c", "d"]}
        self.assertEqual(device42.merge_offset_dicts(orig_dict=first_dict, offset_dict=second_dict), result_dict)

    def test_get_intf_type_eth_intf(self):
        # test physical Ethernet interfaces
        eth_intf = {
            "port_name": "GigabitEthernet0/1",
            "port_type": "physical",
            "discovered_type": "ethernetCsmacd",
            "port_speed": "1.0 Gbps",
        }
        self.assertEqual(device42.get_intf_type(intf_record=eth_intf), "1000base-t")

    def test_get_intf_type_fc_intf(self):
        # test physical FiberChannel interfaces
        fc_intf = {
            "port_name": "FC0/1",
            "port_type": "physical",
            "discovered_type": "fibreChannel",
            "port_speed": "1.0 Gbps",
        }
        self.assertEqual(device42.get_intf_type(intf_record=fc_intf), "1gfc-sfp")

    def test_get_intf_type_unknown_phy_intf(self):
        # test physical interfaces that don't have a discovered_type of Ethernet or FiberChannel
        unknown_phy_intf_speed = {
            "port_name": "Ethernet0/1",
            "port_type": "physical",
            "discovered_type": "Unknown",
            "port_speed": "1.0 Gbps",
        }
        self.assertEqual(device42.get_intf_type(intf_record=unknown_phy_intf_speed), "1000base-t")

    def test_get_intf_type_gigabit_ethernet_intf(self):
        # test physical interface that's discovered as gigabitEthernet
        gigabit_ethernet_intf = {
            "port_name": "Vethernet100",
            "port_type": "physical",
            "discovered_type": "gigabitEthernet",
            "port_speed": "0",
        }
        self.assertEqual(device42.get_intf_type(intf_record=gigabit_ethernet_intf), "1000base-t")

    def test_get_intf_type_dot11_intf(self):
        # test physical interface discoverd as dot11a/b
        dot11_intf = {
            "port_name": "01:23:45:67:89:AB.0",
            "port_type": "physical",
            "discovered_type": "dot11b",
            "port_speed": None,
        }
        self.assertEqual(device42.get_intf_type(intf_record=dot11_intf), "ieee802.11a")

    def test_get_intf_type_ad_lag_intf(self):
        # test 802.3ad lag logical interface
        ad_lag_intf = {
            "port_name": "port-channel100",
            "port_type": "logical",
            "discovered_type": "ieee8023adLag",
            "port_speed": "100 Mbps",
        }
        self.assertEqual(device42.get_intf_type(intf_record=ad_lag_intf), "lag")

    def test_get_intf_type_lacp_intf(self):
        # test lacp logical interface
        lacp_intf = {
            "port_name": "Internal_Trunk",
            "port_type": "logical",
            "discovered_type": "lacp",
            "port_speed": "40 Gbps",
        }
        self.assertEqual(device42.get_intf_type(intf_record=lacp_intf), "lag")

    def test_get_intf_type_virtual_intf(self):
        # test "virtual" logical interface
        virtual_intf = {
            "port_name": "Vlan100",
            "port_type": "logical",
            "discovered_type": "propVirtual",
            "port_speed": "1.0 Gbps",
        }
        self.assertEqual(device42.get_intf_type(intf_record=virtual_intf), "virtual")

    def test_get_intf_type_port_channel_intf(self):
        # test Port-Channel logical interface
        port_channel_intf = {
            "port_name": "port-channel100",
            "port_type": "logical",
            "discovered_type": "propVirtual",
            "port_speed": "20 Gbps",
        }
        self.assertEqual(device42.get_intf_type(intf_record=port_channel_intf), "lag")

    netmiko_platforms = [
        ("asa", "asa", "cisco_asa"),
        ("ios", "ios", "cisco_ios"),
        ("iosxe", "iosxe", "cisco_ios"),
        ("nxos", "nxos", "cisco_nxos"),
        ("junos", "junos", "juniper_junos"),
    ]

    @parameterized.expand(netmiko_platforms, skip_on_empty=True)
    def test_get_netmiko_platform(self, name, sent, received):  # pylint: disable=unused-argument
        self.assertEqual(device42.get_netmiko_platform(sent), received)

    def test_find_device_role_from_tags(self):
        tags = [
            "core-router",
            "nautobot-core-router",
        ]
        self.assertEqual(device42.find_device_role_from_tags(tag_list=tags), "core-router")

    def test_get_facility(self):
        tags = ["core-router", "nautobot-core-router", "sitecode-DFW"]
        self.assertEqual(device42.get_facility(tags=tags), "DFW")


class TestDevice42Api(TestCase):
    """Test Base Device42 API Client and Calls."""

    def setUp(self):
        """Setup Device42API instance."""
        self.uri = "https://device42.testexample.com"
        self.username = "testuser"
        self.password = "testpassword"
        self.verify = False
        self.dev42 = device42.Device42API(self.uri, self.username, self.password, self.verify)

    def test_validate_url(self):
        """Test validate_url success."""
        validate_url = self.dev42.validate_url("api_endpoint")
        self.assertEqual(validate_url, "https://device42.testexample.com/api_endpoint")

    def test_validate_url_missing_extra_slash(self):
        """Test validate_url success with missing '/'."""
        # Instantiate a new object, to test additional logic for missing'/':
        self.uri = "https://device42.testexample.com"
        self.dev42 = device42.Device42API(self.uri, self.username, self.password, self.verify)
        validate_url = self.dev42.validate_url("api_endpoint")
        self.assertEqual(validate_url, "https://device42.testexample.com/api_endpoint")

    def test_validate_url_verify_true(self):
        """Test validate_url success with verify true."""
        # Instantiate a new object, to test additional logic for verify True
        self.dev42 = device42.Device42API(self.uri, self.username, self.password, verify=True)
        validate_url = self.dev42.validate_url("api_endpoint")
        self.assertEqual(validate_url, "https://device42.testexample.com/api_endpoint")

    @responses.activate
    def test_get_cluster_members(self):
        """Test get_cluster_members success."""
        test_query = load_json("./nautobot_ssot_device42/tests/fixtures/get_cluster_members_sent.json")
        responses.add(
            responses.GET,
            "https://device42.testexample.com/services/data/v1.0/query/?query=SELECT+m.name+as+cluster%2C+string_agg%28d.name%2C+%27%253B+%27%29+as+members%2C+h.name+as+hardware%2C+d.network_device%2C+d.os_name+as+os%2C+b.name+as+customer%2C+d.tags+FROM+view_device_v1+m+JOIN+view_devices_in_cluster_v1+c+ON+c.parent_device_fk+%3D+m.device_pk+JOIN+view_device_v1+d+ON+d.device_pk+%3D+c.child_device_fk+JOIN+view_hardware_v1+h+ON+h.hardware_pk+%3D+d.hardware_fk+JOIN+view_customer_v1+b+ON+b.customer_pk+%3D+d.customer_fk+WHERE+m.type+like+%27%25cluster%25%27+GROUP+BY+m.name%2C+h.name%2C+d.network_device%2C+d.os_name%2C+b.name%2C+d.tags&output_type=json&_paging=1&_return_as_object=1&_max_results=1000",
            json=test_query,
            status=200,
        )
        expected = load_json("./nautobot_ssot_device42/tests/fixtures/get_cluster_members_recv.json")
        response = self.dev42.get_cluster_members()
        self.assertEqual(response, expected)
        self.assertTrue(len(responses.calls) == 1)
        self.assertTrue(
            responses.calls[0].request.url
            == "https://device42.testexample.com/services/data/v1.0/query/?query=SELECT+m.name+as+cluster%2C+string_agg%28d.name%2C+%27%253B+%27%29+as+members%2C+h.name+as+hardware%2C+d.network_device%2C+d.os_name+as+os%2C+b.name+as+customer%2C+d.tags+FROM+view_device_v1+m+JOIN+view_devices_in_cluster_v1+c+ON+c.parent_device_fk+%3D+m.device_pk+JOIN+view_device_v1+d+ON+d.device_pk+%3D+c.child_device_fk+JOIN+view_hardware_v1+h+ON+h.hardware_pk+%3D+d.hardware_fk+JOIN+view_customer_v1+b+ON+b.customer_pk+%3D+d.customer_fk+WHERE+m.type+like+%27%25cluster%25%27+GROUP+BY+m.name%2C+h.name%2C+d.network_device%2C+d.os_name%2C+b.name%2C+d.tags&output_type=json&_paging=1&_return_as_object=1&_max_results=1000"
        )
        # print(responses.calls[0].response.text)
        # self.assertTrue(
        #     responses.calls[0].response.text
        #     == [
        #         {
        #             "cluster": "corea.testcluster.com",
        #             "members": "corea.testcluster.com - Switch 2%3B corea.testcluster.com - Switch 1",
        #             "hardware": "Nexus 9000V",
        #             "network_device": True,
        #             "os": "nxos",
        #             "customer": "DFW",
        #             "tags": "",
        #         }
        #     ]
        # )

    @responses.activate
    def test_get_ports_with_vlans(self):
        """Test get_ports_with_vlans success."""
        test_query = load_json("./nautobot_ssot_device42/tests/fixtures/get_ports_with_vlans_sent.json")
        responses.add(
            responses.GET,
            "https://device42.testexample.com/services/data/v1.0/query/?query=SELECT array_agg( distinct concat (v.vlan_pk)) AS vlan_pks, n.port AS port_name, n.description, n.up, n.up_admin, n.discovered_type, n.hwaddress, n.port_type, n.port_speed, n.mtu, d.name AS device_name FROM view_vlan_v1 v LEFT JOIN view_vlan_on_netport_v1 vn ON vn.vlan_fk = v.vlan_pk LEFT JOIN view_netport_v1 n ON n.netport_pk = vn.netport_fk LEFT JOIN view_device_v1 d ON d.device_pk = n.device_fk WHERE n.port is not null GROUP BY n.port, n.description, n.up, n.up_admin, n.discovered_type, n.hwaddress, n.port_type, n.port_speed, n.mtu, d.name&output_type=json&_paging=1&_return_as_object=1&_max_results=1000",
            json=test_query,
            status=200,
        )
        expected = load_json("./nautobot_ssot_device42/tests/fixtures/get_ports_with_vlans_recv.json")
        response = self.dev42.get_ports_with_vlans()
        self.assertEqual(response, expected)
        self.assertTrue(len(responses.calls) == 1)

    @responses.activate
    def test_get_ports_wo_vlans(self):
        """Test get_ports_wo_vlans success."""
        test_query = load_json("./nautobot_ssot_device42/tests/fixtures/get_ports_wo_vlans_sent.json")
        responses.add(
            responses.GET,
            "https://device42.testexample.com/services/data/v1.0/query/?query=SELECT m.port as port_name, m.description, m.up_admin, m.discovered_type, m.hwaddress, m.port_type, m.port_speed, m.mtu, m.tags, d.name as device_name FROM view_netport_v1 m JOIN view_device_v1 d on d.device_pk = m.device_fk WHERE m.port is not null GROUP BY m.port, m.description, m.up_admin, m.discovered_type, m.hwaddress, m.port_type, m.port_speed, m.mtu, m.tags, d.name&output_type=json&_paging=1&_return_as_object=1&_max_results=1000",
            json=test_query,
            status=200,
        )
        expected = load_json("./nautobot_ssot_device42/tests/fixtures/get_ports_wo_vlans_recv.json")
        response = self.dev42.get_ports_wo_vlans()
        self.assertEqual(response, expected)
        self.assertTrue(len(responses.calls) == 1)

    @responses.activate
    def test_get_port_default_custom_fields(self):
        """Test get_port_default_custom_fields success."""
        test_query = [
            {"key": "Software Version", "value": "10R.2D.2", "notes": None},
            {"key": "EOL Date", "value": "12/31/2999", "notes": None},
        ]
        responses.add(
            responses.GET,
            "https://device42.testexample.com/services/data/v1.0/query/?query=SELECT cf.key, cf.value, cf.notes FROM view_netport_custom_fields_v1 cf&output_type=json&_paging=1&_return_as_object=1&_max_results=1000",
            json=test_query,
            status=200,
        )
        expected = [
            {"key": "EOL Date", "value": None, "notes": None},
            {"key": "Software Version", "value": None, "notes": None},
        ]
        response = self.dev42.get_port_default_custom_fields()
        self.assertEqual(response, expected)
        self.assertTrue(len(responses.calls) == 1)

    @responses.activate
    def test_get_port_custom_fields(self):
        """Test get_port_custom_fields success."""
        test_query = load_json("./nautobot_ssot_device42/tests/fixtures/get_port_custom_fields_sent.json")
        responses.add(
            responses.GET,
            "https://device42.testexample.com/services/data/v1.0/query/?query=SELECT cf.key, cf.value, cf.notes, np.port as port_name, d.name as device_name FROM view_netport_custom_fields_v1 cf LEFT JOIN view_netport_v1 np ON np.netport_pk = cf.netport_fk LEFT JOIN view_device_v1 d ON d.device_pk = np.device_fk&output_type=json&_paging=1&_return_as_object=1&_max_results=1000",
            json=test_query,
            status=200,
        )
        expected = load_json("./nautobot_ssot_device42/tests/fixtures/get_port_custom_fields_recv.json")
        response = self.dev42.get_port_custom_fields()
        self.assertEqual(response, expected)
        self.assertTrue(len(responses.calls) == 1)
