"""Tests of Nautobot utility methods."""
from uuid import UUID
from unittest.mock import MagicMock, patch
from django.contrib.contenttypes.models import ContentType
from nautobot.utilities.testing import TransactionTestCase
from nautobot.dcim.models import Manufacturer, Site, Region
from nautobot.extras.choices import CustomFieldTypeChoices
from nautobot.extras.models import CustomField, Status
from nautobot_ssot_device42.utils.nautobot import (
    verify_platform,
    determine_vc_position,
    update_custom_fields,
)


class TestNautobotUtils(TransactionTestCase):
    """Test Nautobot utility methods."""

    databases = ("default", "job_logs")

    def setUp(self):
        """Setup shared test objects."""
        super().setUp()
        self.status_active = Status.objects.get(name="Active")
        self.cisco_manu, _ = Manufacturer.objects.get_or_create(name="Cisco")
        self.site = Site.objects.create(name="Test Site", slug="test-site", status=self.status_active)
        self.dsync = MagicMock()
        self.dsync.platform_map = {}
        self.dsync.vlan_map = {}
        self.dsync.site_map = {}
        self.dsync.status_map = {}
        self.dsync.objects_to_create = {"platforms": [], "vlans": []}
        self.dsync.site_map["test-site"] = self.site.id
        self.dsync.status_map["active"] = self.status_active.id

    def test_lifecycle_mgmt_available(self):
        """Validate that the DLC App module is available."""
        with patch("nautobot_device_lifecycle_mgmt.models.SoftwareLCM"):
            from nautobot_device_lifecycle_mgmt.models import (  # noqa: F401 # pylint: disable=import-outside-toplevel, unused-import
                SoftwareLCM,
            )
            from nautobot_ssot_device42.utils.nautobot import (  # noqa: F401 # pylint: disable=import-outside-toplevel, unused-import
                LIFECYCLE_MGMT,
            )

            self.assertTrue(LIFECYCLE_MGMT)

    def test_verify_platform_ios(self):
        """Test the verify_platform method with IOS."""
        platform = verify_platform(diffsync=self.dsync, platform_name="cisco_ios", manu=self.cisco_manu.id)
        self.assertEqual(type(platform), UUID)
        self.assertEqual(self.dsync.objects_to_create["platforms"][0].name, "cisco.ios.ios")
        self.assertEqual(self.dsync.objects_to_create["platforms"][0].slug, "cisco_ios")
        self.assertEqual(self.dsync.objects_to_create["platforms"][0].napalm_driver, "ios")

    def test_verify_platform_iosxr(self):
        """Test the verify_platform method with IOS-XR."""
        platform = verify_platform(diffsync=self.dsync, platform_name="cisco_xr", manu=self.cisco_manu.id)
        self.assertEqual(type(platform), UUID)
        self.assertEqual(self.dsync.objects_to_create["platforms"][0].name, "cisco.iosxr.iosxr")
        self.assertEqual(self.dsync.objects_to_create["platforms"][0].slug, "cisco_xr")
        self.assertEqual(self.dsync.objects_to_create["platforms"][0].napalm_driver, "iosxr")

    def test_verify_platform_junos(self):
        """Test the verify_platform method with JunOS."""
        juniper_manu, _ = Manufacturer.objects.get_or_create(name="Juniper")
        platform = verify_platform(diffsync=self.dsync, platform_name="juniper_junos", manu=juniper_manu.id)
        self.assertEqual(type(platform), UUID)
        self.assertEqual(self.dsync.objects_to_create["platforms"][0].name, "junipernetworks.junos.junos")
        self.assertEqual(self.dsync.objects_to_create["platforms"][0].slug, "juniper_junos")
        self.assertEqual(self.dsync.objects_to_create["platforms"][0].napalm_driver, "junos")

    def test_verify_platform_f5(self):
        """Test the verify_platform method with F5 BIG-IP."""
        f5_manu, _ = Manufacturer.objects.get_or_create(name="F5")
        platform = verify_platform(diffsync=self.dsync, platform_name="f5_tmsh", manu=f5_manu.id)
        self.assertEqual(type(platform), UUID)
        self.assertEqual(self.dsync.objects_to_create["platforms"][0].name, "f5_tmsh")
        self.assertEqual(self.dsync.objects_to_create["platforms"][0].slug, "f5_tmsh")
        self.assertEqual(self.dsync.objects_to_create["platforms"][0].napalm_driver, "f5_tmsh")

    def test_determine_vc_position(self):
        vc_map = {
            "switch_vc_example": {
                "members": [
                    "switch_vc_example - Switch 1",
                    "switch_vc_example - Switch 2",
                ],
            },
            "node_vc_example": {
                "members": [
                    "node_vc_example - node0",
                    "node_vc_example - node1",
                    "node_vc_example - node2",
                ],
            },
            "firewall_pair_example": {
                "members": ["firewall - FTX123456AB", "firewall - FTX234567AB"],
            },
        }
        sw1_pos = determine_vc_position(
            vc_map=vc_map, virtual_chassis="switch_vc_example", device_name="switch_vc_example - Switch 1"
        )
        self.assertEqual(sw1_pos, 2)
        sw2_pos = determine_vc_position(
            vc_map=vc_map, virtual_chassis="switch_vc_example", device_name="switch_vc_example - Switch 2"
        )
        self.assertEqual(sw2_pos, 3)
        node3_pos = determine_vc_position(
            vc_map=vc_map, virtual_chassis="node_vc_example", device_name="node_vc_example - node2"
        )
        self.assertEqual(node3_pos, 4)
        fw_pos = determine_vc_position(
            vc_map=vc_map, virtual_chassis="firewall_pair_example", device_name="firewall - FTX123456AB"
        )
        self.assertEqual(fw_pos, 2)

    def test_update_custom_fields_add_cf(self):
        """Test the update_custom_fields method adds a CustomField."""
        test_site = Site.objects.create(name="Test", slug="test")
        self.assertEqual(len(test_site.get_custom_fields()), 0)
        mock_cfs = {
            "Test Custom Field": {"key": "Test Custom Field", "value": None, "notes": None},
        }
        update_custom_fields(new_cfields=mock_cfs, update_obj=test_site)
        self.assertEqual(len(test_site.get_custom_fields()), 1)
        self.assertEqual(test_site.custom_field_data["test-custom-field"], None)

    def test_update_custom_fields_remove_cf(self):
        """Test the update_custom_fields method removes a CustomField."""
        test_region = Region.objects.create(name="Test", slug="test")
        _cf_dict = {
            "name": "department",
            "type": CustomFieldTypeChoices.TYPE_TEXT,
            "label": "Department",
        }
        field, _ = CustomField.objects.get_or_create(name=_cf_dict["name"], defaults=_cf_dict)
        field.content_types.add(ContentType.objects.get_for_model(Region).id)
        test_region.custom_field_data.update({_cf_dict["name"]: "IT"})
        mock_cfs = {
            "Test Custom Field": {"key": "Test Custom Field", "value": None, "notes": None},
        }
        update_custom_fields(new_cfields=mock_cfs, update_obj=test_region)
        test_region.refresh_from_db()
        self.assertFalse(
            test_region.custom_field_data.get("department"), "department should not exist in the dictionary"
        )

    def test_update_custom_fields_updates_cf(self):
        """Test the update_custom_fields method updates a CustomField."""
        test_region = Region.objects.create(name="Test", slug="test")
        _cf_dict = {
            "name": "department",
            "type": CustomFieldTypeChoices.TYPE_TEXT,
            "label": "Department",
        }
        field, _ = CustomField.objects.get_or_create(name=_cf_dict["name"], defaults=_cf_dict)
        field.content_types.add(ContentType.objects.get_for_model(Region).id)
        mock_cfs = {
            "Department": {"key": "Department", "value": "IT", "notes": None},
        }
        update_custom_fields(new_cfields=mock_cfs, update_obj=test_region)
        self.assertEqual(test_region.custom_field_data["department"], "IT")
