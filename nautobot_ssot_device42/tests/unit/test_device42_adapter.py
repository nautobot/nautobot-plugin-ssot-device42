"""Unit tests for the IPFabric DiffSync adapter class."""
import json
import uuid
from unittest.mock import MagicMock, patch

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from nautobot.extras.models import Job, JobResult

from nautobot_ssot_device42.diffsync.from_d42.device42 import Device42Adapter
from nautobot_ssot_device42.jobs import Device42DataSource


def load_json(path):
    """Load a json file."""
    with open(path, encoding="utf-8") as file:
        return json.loads(file.read())


BUILDING_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_buildings_recv.json")
ROOM_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_rooms_recv.json")
RACK_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_racks_recv.json")


@patch("nautobot.extras.models.models.JOB_LOGS", None)
class Device42AdapterTestCase(TestCase):
    """Test the Device42Adapter class."""

    def test_data_loading(self):
        """Test the load() function."""

        # Create a mock client
        d42_client = MagicMock()
        d42_client.get_buildings.return_value = BUILDING_FIXTURE
        d42_client.get_rooms.return_value = ROOM_FIXTURE
        d42_client.get_racks.return_value = RACK_FIXTURE

        job = Device42DataSource()
        job.job_result = JobResult.objects.create(
            name=job.class_path, obj_type=ContentType.objects.get_for_model(Job), user=None, job_id=uuid.uuid4()
        )
        device42 = Device42Adapter(job=job, sync=None, client=d42_client)
        device42.load_buildings()
        self.assertEqual(
            {site["name"] for site in BUILDING_FIXTURE},
            {site.get_unique_id() for site in device42.get_all("building")},
        )
        device42.load_rooms()
        self.assertEqual(
            {f"{room['name']}__{room['building']}" for room in ROOM_FIXTURE},
            {room.get_unique_id() for room in device42.get_all("room")},
        )
        device42.load_racks()
        self.assertEqual(
            {f"{rack['name']}__{rack['building']}__{rack['room']}" for rack in RACK_FIXTURE},
            {rack.get_unique_id() for rack in device42.get_all("rack")},
        )

    def test_filter_ports(self):
        """Method to test filter_ports success."""
        vlan_ports = load_json("./nautobot_ssot_device42/tests/fixtures/ports_with_vlans.json")
        no_vlan_ports = load_json("./nautobot_ssot_device42/tests/fixtures/ports_wo_vlans.json")
        merged_ports = load_json("./nautobot_ssot_device42/tests/fixtures/merged_ports.json")
        result = self.device42.filter_ports(vlan_ports, no_vlan_ports)
        self.assertEqual(merged_ports, result)
