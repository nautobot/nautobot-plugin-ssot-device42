# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## v1.7.0 (2023-06-07)

### Fix

* 🔧 Setting default settings for all required settings. ([`c99bcbc`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/c99bcbcb42071598b693b352a8b115060bda4ba4))
* 🐛 Validate using Device ID instead of name ([`e8ebe04`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/e8ebe04700332694ef9daa379a9da21dc44b3120))

### Documentation

* 📄 Add Apache 2.0 license ([`83d0ceb`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/83d0cebbdfca6ad25b6f20d89d69cb1d92559c0d))
* 📝 Add log about skipping cluster if ignore_tag found. ([`4504336`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/45043368e753598bdfa5bccf63c133e219585586))

## v1.6.0 (2023-05-19)
### Feature
* ✨ Set Master device OS version to same as first device in stack. ([`8a8fa07`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/8a8fa07736ac99bc439854a0f99196513a5b9a5b))

### Fix
* 🐛 Ensure Hardware Model name doesn't have trailing dash. ([`674a75d`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/674a75d88b8887b022ed4a957191be13d632fa88))
* 🐛 Correct creationg of tags list for IPAddress so it doesn't result in None. ([`f3386c1`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/f3386c1b4937b7e34aa763bdd210d737a0e07ba3))
* 🐛 Correct how to pull version from RelationshipAssociation for DLC App ([`dac6c9b`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/dac6c9b34b3d28349e42ce1cdd4626110be45d1a))
* 🐛 Correct CustomFields create/update to ensure name & slug use underscore and not dashes. ([`58a0888`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/58a088824d098f0f07d612b145c5f8f54700247e))
* 🐛 Use getattr, not hasattr ([`aa59fe9`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/aa59fe9d0c92d2f777c6afc254563155f20b0cea))
* 🐛 Use attrs device value for finding Interface and logging when updating Device for IPAddr. ([`5dded08`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/5dded08c6f784a15538bea61d13e7e788dd6dd24))
* 🐛 Add exception handling for ValidationError in IPAddress updates. ([`47311fc`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/47311fc4f5af1c0d59f373744f3bd110cc7ddd71))
* 🐛 Add check for IPAddress being assigned before setting primary on Device. ([`7affe2c`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/7affe2cb1cc8a1014717e917506461c1bd489157))
* 🐛 Do validated save when changing Interface to ensure done for primary update. ([`7cb7ef1`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/7cb7ef196bc45e9c3e7c084dbce9b5659744edee))
* 🐛 Add step to unassign primary IP if update has a device change. ([`110572e`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/110572e292cd1614d24e8dcea2d76758a390b812))
* 🐛 Add check for version defined when assigning master device a version ([`2853dae`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/2853daee6940ac4169c8ba858e805d008102225b))
* 🐛 Correct var used in log statement ([`6d7ab67`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/6d7ab6798d8646f0dc4b3565c57ea05402f5a82f))
* Save IPAddress when updating device/intf. ([`9d61025`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/9d61025d1e90b3c49169e57afd4360e6ca276654))
* 🐛 Update IPAddress primary update to update immediately instead of at end of Job. ([`4ffd8de`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/4ffd8de5876490366f88334ef8170afaecc3c453))
* Correct var to pop is vlan, not the ID ([`d56ca3b`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/d56ca3b69f65621bcc6b30fc8714b996c510ad2a))
* ♻️ Redo how newly created VLANs on Ports are handled. ([`920e788`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/920e78852e35679abc80b6fcbdf87b8614e12276))
* 🐛 Ensure tags are pulled in query for ports with VLANs. ([`0137004`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/0137004aa50c692517fc91691a716ee4b0e47d91))
* 🐛 Set default role_color to empty string instead of None for typing ([`ba3ca96`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/ba3ca963142a62b12de671d1c6245ef977558ad3))
* 🐛 Don't slugify CustomField name, specify slug of name. Simplify method. ([`27174e7`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/27174e7fe1d985d379d664501a68345568ad6ee9))
* Ensure MTU of 1500 is used as default to match Nautobot. ([`19fa7c7`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/19fa7c7a1478a6c604476b7f239d41f88f490804))
* 🐛 Correct port status to decommissioning, also handle port with only up_admin. ([`c408a3b`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/c408a3b845cd06e5afa934f3ecaa5cfd416b97e5))
* 🐛 Ensure that IP Address is assigned to device to mark as primary. ([`8426b07`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/8426b07ebc819b2c8032a7c65b1898d6f4cc54ab))
* ♻️ Change VLAN tagging to occur in sync_complete. ([`ffc1c1a`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/ffc1c1af870500307d190a091356c565b17ab150))
* 🐛 Change tagged VLAN assignment to set with list of VLANs. ([`6367d9d`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/6367d9de97907aa751060a31dcd735daae9f694f))
* Ensure site_name is slug form everywhere so everything aligns ([`9be1ea7`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/9be1ea70b3cf555e34353a6c272f0ebd1d1df492))
* 🐛 Add check if VLAN was added to objects_to_create and do validated_save so port update works. ([`c45c8b9`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/c45c8b92669e6d509ddb8bb266fa7788369083cd))
* 🐛 Add check for VLAN loaded and if not, load one to ensure there's one to be tagged. ([`21363cc`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/21363cc7716cc804c0a98c8dac0c777595055b1d))

### Documentation
* 🧑‍💻 Add logging statement if IPAddress to be marked primary shows unassigned. ([`09bd75e`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/09bd75e96a75b53a82cfc91020b948fb4d769b2b))
* ♻️ Redo logs to show device name or address in failure instead of UUID. ([`1c3bd36`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/1c3bd361d91bffbc805ac2245d52fedb74695252))
* 🚨 Add err to log statement ([`b180262`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/b1802620d11d27531fecadf6df9f405c84a93696))
* 🔊 Move logs about being unable to find port from behind debug. ([`57689c6`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/57689c6e6a025c75be50fccd974f2d502c0ec32d))
* 🔊 Correct log to use subnet object for full CIDR being deleted. ([`6370642`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/637064205b7cd9528a5805fead59bc24858182b9))
* 🔊 Remove debug check for log of skipping device for DNS queries. ([`371d48e`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/371d48e00cfa982f376d057d6f7d6cbf0b2a2f8d))
* 🧑‍💻 Add additional logging during DNS check process. ([`70e57f3`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/70e57f3fbbc9ab30158212cff694297054d81d39))
* 📝 Fix docstring ([`2819ed4`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/2819ed4e9ed0893ea8982dbbbc542b7ae1c3dcb5))
* 🧑‍💻 Add some logging so user is aware Port is being updated. ([`44f4836`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/44f48369678faaad5a8bb8c250f438abda4c76f4))
* 📝 Fix project name in links ([`46656a3`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/46656a3a7581de43db16c9cef1057b5a52d46200))
* 📝 Fix links for CHANGELOG ([`5860377`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/5860377d7c104b6ad2524ef1ab6875a0de235c4c))

### Performance
* ⚡️ Adding select_related to Nautobot load functions to improve speed of pulling data. ([`53b9190`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/53b919040a809389959f7c38664f811e5bd2fe98))

## v1.5.1 (2023-03-31)

### Fix

* Use base model instead of Nautobot to avoid circular import ([`ddf0711`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/ddf07119cfdfc523744ea7f124ee10ada5995bfa))
* Correct get to use NautobotDevice ([`ee59ebe`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/ee59ebea6423ad9e10d993706c3c2fd9605c1d35))
* Ensure latitude/longitude are float and not Decimal ([`74e2d77`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/74e2d77bf3f3d2314f9a26ea4b488fbc89d8c94d))
* Correct vars in update log message ([`c280247`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/c280247ec68a9f4836d52ff17238e154deef7554))
* Don't look for site if slug is global ([`b7e9006`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/b7e9006bb883014ad6a0a44ac2a9b7e89f0ff4fc))
* Ensure all VLANs attribute are list for diff ([`bd6ec33`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/bd6ec33271a05d80f9e7ba8d1c86dddab6c7f3e9))
* 🐛 Correct port update method for VLAN tagging to use verify_vlan method ([`a2cc368`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/a2cc368400b20908c6e1d54194c91b1e53ac0fc2))
* Use empty list instead of None ([`98d95b3`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/98d95b3c7c976c99161d2bbd784f0bb936d8cbf0))
* 🐛 VLANs attribute can't be set, must be list to be serializable ([`97a0052`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/97a0052afc138cef7344126f1a5326d173cf629d))
* 🐛 Add tags to VLAN model ([`acffb9b`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/acffb9bde980b2632b6ac40cb5c86e8a427cf2f1))
* ♻️ Change get_random_color to use f-string ([`77eb6c9`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/77eb6c9bc553a353ee2cda3e20b718a1ea6fc4a1))

### Documentation

* 📝 Add log for declaring end of Sync in post_run ([`054932e`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/054932ec2e9b974e25906f3e11aed55363612585))

## v1.5.0 (2023-03-09)

### Feature

* ✨ Add bulk_import toggle to Job and update sync_complete to do bulk if toggled else individual. ([`950469c`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/950469cc28bf07aa5d3dd516d0af63dcc090ddb2))
* ✨ Make a method for updating tags on all tagged objects, update all models to use ([`c8d12bc`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/c8d12bc180e208248f10fe81e0c3d2f77a95ceae))
* ✨ Add port hwaddress to get_ip_addrs query. ([`10b7722`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/10b7722bdf6b415c5c87bd9a255732f562a6cab9))

### Fix

* 🐛 Make Half Depth default for patch panel hardware to match Nautobot ([`5c54d64`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/5c54d645dfa1ea7089103b0131192f4579720995))
* 🐛 Don't document IPs on Devices that aren't imported. ([`6c2085d`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/6c2085db90a23039c1716af779fd52c7ff97d817))
* 🐛 Ensure that CustomFields are updated and not just new ones. ([`f511f5a`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/f511f5ae6ae741e1ea86682df7b064bf8544c960))
* ♻️ Move VRF, VLAN, and Prefix creation to happen before clusters & devices ([`ed18f2a`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/ed18f2a2b2c02c89bfac539451ca021e94468048))
* Corrections for new IP Address to ensure diff lines up ([`9d3bd82`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/9d3bd82277231b71b8a28378d417b8da269a18b9))
* Set defaults for part_number and custom_fields for Patch Panel hardware ([`3af050c`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/3af050cdcc81324b5e57ff433b776dee7cbe45e7))
* Correct key name to custom_fields ([`ca58477`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/ca584778ab7d3811b7e63007820d4c0ec0d00e4a))
* It's supposed to be a tuple dummy! ([`cab12ed`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/cab12edeb8fe714654cb92d1beb94b327e6231ea))
* 🐛 Fix variable name to not conflict with method name ([`aa8d9d6`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/aa8d9d6b4fc76c52e32bf97af0e67483d69cf309))
* Add handling for potentially missing VC or device ([`114961d`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/114961d906031af819d22c1d1d485e1a5f9b58da))
* Ensure part_number lines up in diff ([`06c74ad`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/06c74adf69c5c5bfb61783c83ffdc7f5e7795ef6))
* Use kwargs for dry_run ([`e82a5db`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/e82a5db8712086558f94f872190bf25aa988aee2))
* Should use dry_run, not commit ([`6345081`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/63450810c1f5967ec45739f36f6b5b6366d00ec6))
* Try to ensure that new VC position isn't used ([`2a1440d`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/2a1440daf6bc57482f4bf9b3138c882964bafe04))
* Ensure VC position is set if new VC set ([`f9aaa23`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/f9aaa23c5e16df18c71abbc939cf065d0c0c8d0b))
* Handle changing rack but not room ([`e042d72`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/e042d7296bd057333aa5924c680960d77e115305))
* Ensure part number lines up in diff ([`3dc6bb0`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/3dc6bb0638631ca61a97e3e338771a145e68bdd6))
* Only have sync happen if not a dry-run ([`e81b164`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/e81b16400848d71b8b5ef1c6d260d8349cb67653))
* 🐛 Make sync happen outside normal Job so it's not atomic ([`08b070c`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/08b070cde54df4f76a63f123e7cd824b421300a0))
* 🐛 Correct key for objects_to_create to rooms when checking to create RackGroups. ([`3a1833f`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/3a1833f03f950c684c698074713bd2d05dd97c97))
* Reduce batch sizes to 50 so we aren't overwhelming DB ([`e91515d`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/e91515de51b35fb4f4d18dae8d555ce3d35dbe2a))
* Remove unnecessary passing to method ([`f655a88`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/f655a88dab1ba6d13883829d9a021dc33480f61b))
* Correct port CustomField reference ([`448e7a6`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/448e7a60be8262930a0f2535cce0fa93dee8fbdc))
* 🐛 Update all CRUD ops to work with new CF format. Also fixed all the tests to use new dict format. ([`418f117`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/418f11740720d73ada108fdae39984b4c86d5e02))
* Add update for role if it's Unknown and tags ([`b07f3b9`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/b07f3b97ed806fcdedca33ccc67c8ef9bb3d907b))
* ♻️ Redo verify_platform method to create Platforms correctly and add tests validating. ([`10204cc`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/10204cc150c6fa7bb69df5696a4aa426121a0b69))
* ♻️ Redo verify_platform to handle IOSXR and other Cisco platforms. ([`cffa58b`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/cffa58b5eea1f2997c438b3a491d06fae2bdb136))
* 🔊 Correct DeviceType log to use model instead of name. ([`0f4e3af`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/0f4e3af74005d8119de3999622b4a1a3a01d5526))
* ⏪️ Revert var back to not have id attribute as unneeded. ([`9f82d33`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/9f82d33348b424f9739dfd6fb59fc64e5cc1b45e))
* 🐛 Corect assigned_object_type and id for updating IPAddress interface ([`a21aa27`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/a21aa274f12601cc64e7243263e5598d13951601))

### Documentation

* 📝 Make log statement more informative for IPs on clusters ([`5ba43fd`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/5ba43fd646293e86c5c92fc1b0d1fcda6d9d17fb))
* 🧑‍💻 Improve logging so user knows what's happening during Job execution. ([`123ae56`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/123ae568bd52034bf4f581b3001cde473dc24f1f))
* 🧑‍💻 Tweak the logging to be more informational for user. ([`91a3a83`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/91a3a838054d4b2bb49b3cc2cd27e80a8742c5f9))
* 🔊 Improve logging for CRUD ops so it no longer looks like the Job has hung if not in debug. ([`040b022`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/040b022316024d842c77f6cad76aa77b21db21fc))

### Performance

* 🔥 Remove members as cluster attribute. ([`e611f0f`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/e611f0fcfdf15e97408b742917213625097bd19f))

## v1.4.10 (2022-12-07)

### Fix

* 🐛 Set Nautobot minimum version to 1.4.0 for Interface Status support ([`c3d6305`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/c3d6305f626f3895bf2b1db55edf985b95442165))
* 🐛 Set Nautobot minimum version to 1.4.0 for Interface Status support ([`c93ac16`](https://github.com/networktocode-llc/cu-zest-ssot-device42/commit/c93ac16deb46316329143616c2b84db65af8953e))

## v1.4.9 (2022-10-05)

### Fix

* 🐛 Add handling for instance of new device passed to assign version ([`e014c0f`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/e014c0f48a05f019ef6d824d7bbba33abd10ddac))

## v1.4.8 (2022-10-05)

### Fix

* 🐛 Correct version assignment/removal with DLC plugin ([`62eac46`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/62eac46669509164ee6ef8d2a9437b5e8775dddf))

## v1.4.7 (2022-10-05)

### Fix

* ♻️ Redo how OS version is updated for Devices ([`cf889b3`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/cf889b306bd2f8a3c66274008f2fa079177424fa))

### Performance

* ♻️ Use status_map in Device update to reduce db queries ([`49b48cf`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/49b48cf789ce4ae07a66caf08002a37030205f8b))
* 🔥 Remove hardware determination in update as not used ([`e5ff85d`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/e5ff85d7d2962dbe32cf510670fb88391e4e2e93))

## v1.4.6 (2022-10-04)

### Fix

* 🐛 Redo how VC position is updated, find if another dev is in position ([`181ec39`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/181ec39f70a4736a74ba914760eff1f488bdefd4))

## v1.4.5 (2022-10-04)

### Fix

* Add check for slot in rack_elevations ([`7440a97`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/7440a97ad34508e715923fb7126d4b0793b366a2))

## v1.4.4 (2022-10-04)

### Fix

* Don't set description to None for IPAddress ([`6400ab7`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/6400ab7ac7218fce7a705b77fd7468bcfc64b727))

## v1.4.3 (2022-10-04)

### Fix

* 🐛 Correct rack_position determination ([`befc6a0`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/befc6a06a40d74f55356bfd98bdf4e5a88305168))
* 🐛 Correct update of device assigned to IP ([`c8f06bc`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/c8f06bc74dc968269289b6b9bbd9683ba243e44a))

## v1.4.2 (2022-10-04)

### Fix

* 🐛 Correct key for device name, add catch for no Device assigned ([`4b57882`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/4b578828a00e7bc955e915d18d7e0d5f4eb878a8))

## v1.4.1 (2022-10-04)

### Fix

* ⏪️ Restore the netport_pk in DOQL query for ports ([`d7e09fd`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/d7e09fd477e3c456da85625deca96e033f210789))

## v1.4.0 (2022-10-04)

### Feature

* ✨ Update port queries to include second device ([`0335835`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/0335835313e1fa522445b428b448c8e0e7356747))

### Fix

* 🐛 Correct debug message for device name ([`5c99c42`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/5c99c42268e4eca37d4724ab5fc86e8ddfca1611))

## v1.3.12 (2022-10-03)

### Fix

* Verify device is in port map before assigning ID ([`1d960e3`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/1d960e39f034293e019da23282eb4813f423d0f8))

## v1.3.11 (2022-10-03)

### Fix

* 🐛 Fix IPAddr moving interface in update function ([`9d5ed98`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/9d5ed9854a009ad7c154849a3fc17f76842ab5e9))

## v1.3.10 (2022-10-03)

### Fix

* 🐛 Ensure device found before trying to save ([`dab7cc8`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/dab7cc89721d5c74a83d8c42a8964907740e36bc))

## v1.3.9 (2022-10-03)

### Fix

* Handle None for tags ([`ec3fff3`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/ec3fff34749bd315069dc0f6c1b6976745135d3c))

## v1.3.8 (2022-10-03)

### Fix

* Add handling for None being passed ([`c5e9184`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/c5e9184a19e0e9de9a9d99c59fdb1285c9aeae1d))

## v1.3.7 (2022-09-30)

### Fix

* Validate rack_position var for dev position ([`f4626f4`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/f4626f4acd21d7a45b43ca24d05ccd926ba6df71))

## v1.3.6 (2022-09-29)

### Fix

* Ensure part number isn't null ([`4138e64`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/4138e64b1c2ea3b67f7fde53c66f0e6b35e6d8a8))

## v1.3.5 (2022-09-29)

### Fix

* ⏪️ Revert custom_field to be a get ([`8631b6f`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/8631b6fb99e20b3eeba1771e0c4bf5e6157a6019))

## v1.3.4 (2022-09-29)

### Fix

* 🐛 Fix tag updates so they're added/removed properly ([`03ff4fc`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/03ff4fcf18441450b614b38c96cd4edf3120a005))

## v1.3.3 (2022-09-28)

### Fix

* 🐛 Add Status attribute to mgmt interface ([`0bb9070`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/0bb907005b09ceb9a2438fa46211f113676b1535))

## v1.3.2 (2022-09-28)

### Fix

* 🐛 Add check for up on port to handle virtual ports ([`36c8d8c`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/36c8d8c205713e70f450f19799f04bf119d2beff))

## v1.3.1 (2022-09-28)

### Fix

* Correct var to be _device_name ([`3f361ca`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/3f361cac2d51156918b043ba537992769253243d))

## v1.3.0 (2022-09-28)

### Feature

* ✨ Add Status to Ports ([`3d76bfd`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/3d76bfd809a47a0a744a074104050fdc912b59bc))

### Fix

* 🐛 Correct get of Device to use variable ([`cf6bf80`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/cf6bf802f1be9ad3c6e3c88fc3403022bae5c379))

## v1.2.8 (2022-09-27)

### Fix

* Correct import for DiffSyncFlags ([`89e77ef`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/89e77efa402a7df7dfc331cd77811bf8b8848778))

## v1.2.7 (2022-09-27)

### Fix

* 🐛 Correct label attr to be defined even if field missing for diff ([`3a8a3cb`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/3a8a3cbdc2466b647055b070e78b25d43034e6a5))
* 🐛 Ensure updates to device are saved ([`86758d9`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/86758d9bcc837a250a586afe13f1b75937ff23c8))

## v1.2.6 (2022-09-26)

### Fix

* 🐛 Add handling for IP showing assigned but non-existant Interface ([`7da3a69`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/7da3a69998b8545702d65c7c1b579e50aa4941f8))

## v1.2.5 (2022-09-26)

### Fix

* Check that queryset has a version ([`b8428f0`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/b8428f052bfc829bd5e21f6747f2182381d3696e))

### Documentation

* 📝 Add debug logging for deleting devices ([`6125600`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/6125600857a0cd651077607a55282ca4d7ac3791))

## v1.2.4 (2022-09-26)

### Fix

* 🐛 Ensure only one version assigned to Device ([`65dde96`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/65dde968bf8db1311be4df8696337b66dde81c8c))

## v1.2.3 (2022-09-23)

### Fix

* Many Fixes and Features for Bulk Create/Update/Delete ([`6c9ed94`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/6c9ed94a90af2f421c04595bce1914ede5c8fbae))

## v1.2.2 (2022-05-06)

### Fix

* :bug: Ensure port name is only 64 characters ([`36aff90`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/36aff9046eda0d4d171eb7b22dc5125143b3aac5))

### Documentation

* Fix docstring ([`2f6913c`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/2f6913c01d85112cb44d19846a851e643d553965))

## v1.2.1 (2022-02-23)

### Fix

* :bug: Fix deleting RackGroup and tweak delete logging ([`2a38589`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/2a385898f89c73028721942b0c438283e91d0ed3))

## v1.2.0 (2022-01-20)

### Feature

* :sparkles: Add links for Device42 data mapping to D42 objects ([`1e37f53`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/1e37f53e59f7b216adba70a7107bccea08c8b265))

### Fix

* :bug: Add ValidationError handling for IP Address updates ([`7c17ec0`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/7c17ec0f0bf04c3f539e4c610d0c92df04ef93b4))
* :bug: Add handling for only device attribute passed for update ([`40bea3e`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/40bea3e9712b0e00658e0da3b0cc733c717d7116))
* :bug: Handle validation errors for device updates ([`cfe4e69`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/cfe4e697b437b78ef87e8e7aa65a47407838d1b0))
* :bug: Remove redundant device save and tweak debug output ([`cf7b63d`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/cf7b63df89631652d5df5a1a980b988080cba6d3))

### Documentation

* :memo: Update documentation on Devices and D42 support ([`f608c28`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/f608c286b83efac7e47e393bdb371247d1516854))

## v1.1.1 (2022-01-14)

### Fix

* :bug: Fix path for Device42 logo ([`c36c5f8`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/c36c5f8d678a16c397013fea86cc5845bfa39244))
* :bug: Ensure that hardware model names are sanitized ([`4f6c3c4`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/4f6c3c4c6b67d4397a9b0428e245ad08dfb3a13b))

### Documentation

* :memo: Add usage information and sample detail view ([`261a4b8`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/261a4b8545950329c00bef1f6b548de0cce39680))
* :memo: Update README with plugin setting details and fix nautobot_config example ([`6b2d3a7`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/6b2d3a7d65d9ee40e9d6c6cfb1d8a1b28755cc27))

## v1.1.0 (2022-01-14)

### Feature

* :sparkles: Correct data mappings for plugin to reflect all objects that are imported ([`4a701a4`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/4a701a452bd2f64fa428fb8605d2a8a03dcb97c5))

### Fix

* :bug: Ensure all logging uses message attr ([`81976b6`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/81976b6c1e1516536455d494ac01b1a83ddc43fa))
* :bug: Add handling for duplicate MAC addresses ([`8c886c6`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/8c886c67204795452c5bbbfe9e91a213f72a9cc7))
* :bug: Ensure debug defaults to False. ([`2497cc1`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/2497cc166dcfcbb49c8a45e885e59316bf510d1a))
* :bug: Catch ValidationErrors when creating a new Device. ([`e9a608a`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/e9a608a9d14ef6cd1965c376c0fed5e5f76bab82))
* :bug: Fix port_speed trying to be set with FrontPort type ([`92985ea`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/92985eadcbb22bb3d1fe935aa5c6f907e871d488))

## [v1.0.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/tags/v1.0.0) -  (2022-01-13)

The plugin is officially in a stable, production-ready state!

## [v0.15.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/tags/v0.15.0) -  (2022-01-13)

### Feature

* :sparkles: Add method for get_hardware_models along with tests for importing into adapter and loading data from D42 ([`03df0fa`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/03df0fad5fa692255fa458905fb549ad68c76961))
* :sparkles: Add plugin setting to prevent deletion of objects during sync. ([`12256eb`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/12256eb1929a0c4e8893d96299850c871ecfe355))
* :sparkles: Add method get_vendors along with tests to validate functionality ([`23de09d`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/23de09d1eb9556aac973079dd5b5142725bca9ae))
* :sparkles: Add support for importing Patch Panels from Assets along with the Front/Rear ports. ([`b831cea`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/b831cea1f266c044deccbbf65125cb3196441913))
* :sparkles: Add method to get Racks mapped to their primary key and test validating it ([`b3552fe`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/b3552fe55ee7f7f59d531876eaa5ca8e61ac18aa))
* :sparkles: Add method to make mapping of Customer to their primary key ([`3cbc90e`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/3cbc90e2568c437634c6d5093d61d03b414e1344))
* :sparkles: Add method to get Rooms mapped to their primary keys for reference ([`bdad3cb`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/bdad3cb07cc23994960c8e3286a2df45a943e841))
* :sparkles: Add a method and tests to get Buildings mapped to their primary key ([`427580a`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/427580a5b9ef7ceefea14e4171d6bef1e0a761e6))
* :sparkles: Add method to obtain patch panels and create dict with PK as key ([`e8d5440`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/e8d544071998addbbcc39df4227188c8f158b943))

### Fix

* :bug: Handle duplicate IP Addresses being imported from Device42 ([`7e00d6f`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/7e00d6f49a3e5b2531e0bb5bf989cd0658b8661a))
* :bug: Add handling for ValidationErrors in case they occur ([`332de8b`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/332de8b4bc2a5c0fbd1fb0bb31e76dab28e02994))
* :bug: Fix issue where multiple devices are assigned to same U position in a Rack. ([`c70d8c3`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/c70d8c3e2b3ee7b77c18b6ef839ff91fdec53610))
* :bug: Fix the get_patch_panels DOQL query ([`27319d6`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/27319d6290a0b2f12ad4abce422fced094a7580c))
* :bug: Fix check for debug logging ([`982dc12`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/982dc12f4db8d773ab185222f3e2ca20519f05fc))
* :rotating_light: Add null attributes to object creations to address pydantic warning ([`dd37942`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/dd379428209f6061e5a1c1140ffa8ea784d02f93))
* :bug: Prevent duplicate ports from being loaded. ([`1e56f23`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/1e56f23e1508a695efbb4102a392543e7a9712a6))
* :bug: Use UUID to find VRF to delete ([`188d7e5`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/188d7e518d9d6cb86be87ac9ec6355361308caf7))
* :bug: Remove get_circuit_status call when setting Circuit status in update ([`46e1c2c`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/46e1c2c3a128b240c36863c4842544041e5e6a33))
* :bug: Make objects_to_delete a public variable and make it a defaultdict ([`024bc1b`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/024bc1bce3a8fd7c0e0f24d887172a4361597a68))
* :bug: Remove object from logging statements ([`db4b1b4`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/db4b1b4ec470813be9b7e06754fd20366b3213a7))
* :bug: Fix verbose debug logging ([`e7c541c`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/e7c541c5c6e437b698b8059db6511961913be66a))
* :bug: Add rack position for patch panel model and update test to include it ([`4878d5c`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/4878d5ced79626f86c5e91c8e9caf274bfb62cfd))

### Documentation

* :memo: Fix link for 0.13.1 documentation in CHANGELOG ([`8ab1f96`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/8ab1f96789690effeeeb0ddcef8a7c8816cd1864))
* :memo: Add documentation on requirements for Subnets and Telco Circuit imports ([`67b6b30`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/67b6b304a5a5c32fbfb426ce969f6d3e80d61edc))
* :memo: Remove mention of verbose_debug setting in docs ([`a03dcb3`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/a03dcb332fcaf45a08e2991a9e81030c373357a1))
* :memo: Correct docstring for circuit models ([`aac72ac`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/aac72aca88f8225e1bfebad6f853e05682ca9da2))

## [v0.14.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/tags/v0.14.0) -  (2021-12-20)

### Feature

* :zap: Add UUID attribute to all models for the Nautobot Data Target. ([`07c8a40`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/07c8a408efc1615536077f66680cd5a5b0dec267))

### Fix

* :bug: Tweak device import to ignore those where a Building can't be found. ([`a59fd82`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/a59fd82d18ed25a678455492e7134a9d8eac9cc4))
* :bug: Include VRF when trying to find IP Address for update ([`a164592`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/a164592a8dd959e5dc54027a887d84c026482338))
* :bug: Fix infinite loop ([`6c5d2e5`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/6c5d2e525b6d8a19ab38d1c9f8ba40739303d917))
* :bug: Tweak find_ipaddr and set_primary_from_dns methods to have IP Address returned once found. ([`b3f62db`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/b3f62db91262236fb4df18a656f103c52cfaa43a))
* :bug: Fix infinite loop when looking for IP in VRF ([`4d792eb`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/4d792eb573dfc65bbc3bad9054e3c0d675792cfe))
* :bug: Update IP Address delete to handle multiple results ([`e8478be`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/e8478bec62155ddc24b74c5e831df0a5a15d181d))
* :bug: Rewrite find_ipaddr to check VRFs ([`a6592b8`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/a6592b8613b6fce58090692364cd1720592d41b1))
* :bug: Subnet/IPAddress delete methods updated to look for vrf__name ([`d53badf`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/d53badf904cd4f4cf82d8e3f0fcc971507fed314))
* :bug: Add VRF as identifier to IP Address ([`20a1fa0`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/20a1fa0a0e247882688445c88afd12991e5fe3d5))
* :bug: Ensure all logging sends to message. ([`874db65`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/874db650278d278f0b84fa933169dec40cc25658))

## [v0.13.1](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/tags/v0.13.1) -  (2021-12-15)

<small>[Compare with v0.13.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/compare/v0.13.0...v0.13.1)</small>

### Testing

* Added unittests for Device42 util methods.

## [v0.13.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/tags/v0.13.0) - 2021-12-09

<small>[Compare with v0.12.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/compare/v0.12.0...v0.13.0)</small>

### Feature

* :sparkles: Add support for Device Lifecycle Management plugin for software version tracking. ([`e578f0e`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/e578f0e9886ffd451dc9bbe7455a1dd1664e43f5))
* :heavy_plus_sign: Start adding support for Device Lifecycle plugin ([`e6806df`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/e6806df829cc3fbfeb33f2b389161cf619703f5a))

### Fix

* :bug: Change Port deletion to standard method instead of delayed. ([`056c117`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/056c1178135d117e7b9dcf7bda0fe17c68b13e81))
* :bug: Update find_ipaddr method to allow for IPv6 and all subnets in IPv4. ([`3e10fb0`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/3e10fb0c0ae26597820bb59e31299d7f8c9c7437))
* :bug: Add provider to _objects_to_delete dict ([`09a3aad`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/09a3aaddb24a2759f8110bd3fce8be20abbd3008))
* :bug: Update Circuit processing to handle Circuits/Connections without terminations. ([`000d0e7`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/000d0e7bb80d07652cda6b1b958fc73c59069006))
* :bug: Validate VLAN PK is in vlan_map ([`c31cede`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/c31cede201435c7b2bb40ee02ed4d0ca81231303))
* :bug: Ensure that the object is always returned for accurate logs. ([`d16dbba`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/d16dbbaeb10618c3fcdae3278ca3fb2aae59bca8))
* :bug: Validate Circuit has termination when loading ([`8f6d7d3`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/8f6d7d34c38b75b4e0fd873baaf3a91e1f6a76f8))
* :bug: Ensure that logs are sent in message. ([`6de3553`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/6de355338a5c5d5cbe55082b83d6ca4dd054d95e))
* :bug: Fix APs being processed as FQDNs. ([`469123e`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/469123ec4dc046b34829d86d2fb958837fece7bd))
* :bug: Provider account number is limited to 30 characters. ([`4183a65`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/4183a65f89bd93f8f1a09129c0ba2d79b9ac01ce))
* :bug: Fix the a/z side connections to Device Ports ([`545ec66`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/545ec6680b046000a7df79bf538435d2c9f6699d))
* :bug: Ensure that the first spot is reserved for master device in VC ([`b5d7884`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/b5d7884eab6b79deea6186724b9a0c7ea5ab8ceb))

### Documentation

* :memo: Correct name of project in docstring ([`8090ecb`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/8090ecb0f51f99daf554af5808636468430930ae))

### Performance

* :white_check_mark: Add test for get_vlans_with_location method ([`6e5714a`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/6e5714a269bb625a1f3f4fbd36a9022128b2f1f4))

## [v0.12.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/tags/v0.12.0) - 2021-11-09

<small>[Compare with v0.11.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/compare/v0.11.0...v0.12.0)</small>

### Feature

* :sparkles: Add `ignore_tag` feature to allow Devices to not be imported based on a Tag. ([`0bbca1f`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/0bbca1f4e179a6b5fc8e494a690a992e1118ed1d))

### Fix

* :bug: Fix catch for AP hosts. ([`495238e`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/495238e48897ed8402c00f73fc5578efbb9ae408))
* :bug: Should have used continue instead of break. ([`2d8a6b0`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/2d8a6b06bcc847f2cc13b66a61455b91f9a8b4bb))
* :bug: Handle case where IP is assigned as primary to another device. ([`dfd113f`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/dfd113f7b9473a4d03c95829effc887debd7f8aa))
* :bug: Correct job logging to come from diffsync object in models. ([`92871c0`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/92871c03c1b8533d7e9efed441340619ec35102a))

### Documentation

* :memo: Add documentation for `ignore_tag` feature. ([`3ab83d6`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/3ab83d688a6d4bf236ba0aeb1cc403d4d318b99a))

## [v0.11.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/tags/v0.11.0) - 2021-11-06

<small>[Compare with v0.10.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/compare/v0.10.0...v0.11.0)</small>

### Feature

* :sparkles: Add Custom Diff class to control order of operations. ([`0da4ff0`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/0da4ff07a8d039f1913a2c166bf29313ba729f32))
* :sparkles: Add method to find a site mapping from settings. ([`70f9a93`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/70f9a9369e705e3998073e18f9532a1738b6ff21))

### Fix

* :bug: Handle edge cases where device has A record for non-existent Subnet. ([`8fcfeb3`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/8fcfeb36082d3cae291240f5cbafa310c7b49cbc))

### Documentation

* :memo: Improve documentation in README and add information to RTD index ([`e9281ab`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/e9281abb6f21f374b82aef8d877427ecb89d4e3f))
* :memo: Improve typing and docstrings for some methods. ([`6058a95`](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/6058a953a81128e9ebadf617d19dfa013cece5d5))

## [v0.10.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/tags/v0.10.0) - 2021-11-03

<small>[Compare with v0.9.3](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/compare/v0.9.3...v0.10.0)</small>

### Bug Fixes

* :bug: correct logging to be from diffsync. ([afb3b62](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/afb3b62c8896f665d97f37bb611ff73864794271) by Justin Drew - Network To Code).

* :bug: return sorted customfields. ([4f8066f](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/4f8066f57f520f9ccf597fbaecba49e7b3b8745e) by Justin Drew - Network To Code).
* :bug: missed exception var, has been added. ([d8ac88d](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/d8ac88d8355bd6adb8f231dca58faf608ccf62e4) by Justin Drew - Network To Code).
* :bug: check for dns answer matching primary ip needs str. ([87bf1cd](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/87bf1cdea2381731c8a8a22cd9f10ae76f7dac90) by Justin Drew - Network To Code).
* :bug: ensure customfields are sorted on both sides. ([d4be4a9](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/d4be4a9e96cc98fe00b885aed6ea24ea3909b982) by Justin Drew - Network To Code).
* :bug: remove `contact_info` attribute from provider. ([22887cf](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/22887cfbe6ad7fb0959fee092ad577d41df79937) by Justin Drew - Network To Code).
* :bug: validate it's dest port and device match, not source for z side. ([a40c0dd](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/a40c0dd3eb08446379188a738429e3f05bbd1c8f) by Justin Drew - Network To Code).
* :bug: corrected circuittermination to have circuit object passed. ([fe61e5a](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/fe61e5a316ef6c51c2ae0766cb831cd36dbfa7fd) by Justin Drew - Network To Code).
* :bug: correct exception to be nautobotvlan instead of site. ([9796647](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/9796647f74ea243248cd92d261040a94cc4f34ac) by Justin Drew - Network To Code).
* :bug: change `cid` finally. ([5049d8c](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/5049d8cf35a1f892a61e0531f09bd096c6cc1143) by Justin Drew - Network To Code).

### Features

* :sparkles: add methods to get default customfields for ports and subnets. ([6acf222](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/6acf2225eecdabb9112fbb213fb41dec7f7be59e) by Justin Drew - Network To Code).

* :sparkles: handle case for ip addr where device changes. ([7d0ba67](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/7d0ba672964f14ce690534683c75fd5bd860a236) by Justin Drew - Network To Code).

## [v0.9.3](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/tags/v0.9.3) - 2021-11-01

<small>[Compare with v0.9.2](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/compare/v0.9.2...v0.9.3)</small>

### Bug Fixes

* :rewind: revert attribute for circuit object to use cid. ([d856e3e](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/d856e3eeb084f65b4fcd83774ffeab20c510b5b8) by Justin Drew - Network To Code).

## [v0.9.2](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/tags/v0.9.2) - 2021-11-01

<small>[Compare with v0.9.1](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/compare/v0.9.1...v0.9.2)</small>

### Bug Fixes

* :bug: correct attribute from `cid` to `circuit_id` for circuitterminations ([134943d](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/134943d00116c1bb9f66cb6a40d846a8c71e656f) by Justin Drew - Network To Code).

## [v0.9.1](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/tags/v0.9.1) - 2021-11-01

<small>[Compare with v0.6.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/compare/v0.6.0...v0.9.1)</small>

### Features

* Add circuit terminations to devices in create ([ed908b0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/ed908b0321e71969ca076f83b15a49fcb39bbcc7) by Justin Drew - Network To Code).

* Add telco circuits ([e1c0386](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/e1c03862aeb2e584bfd49996b5349ff4561574fa) by Justin Drew - Network To Code).
* Add custom fields ([e52bb0d](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/e52bb0d2faa4170e207a288c3e7b6e74e3ae7818) by Justin Drew - Network To Code).
* Add cables ([f1c9791](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/f1c9791b9b8b1e63f52e04d002e62732be27af20) by Justin Drew - Network To Code).
* Add vlans and trunks ([8b58eb4](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/8b58eb4f8cb33c7887ee4822f63656da4db51e66) by Justin Drew - Network To Code).
* Add facility ([df64403](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/df644032d836fb9a935713e0f60cab19d1730d3f) by Justin Drew - Network To Code).
* Add device roles ([5f4a488](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/5f4a4880c38e48cb9c5d8550ba0096f06b1d2510) by Justin Drew - Network To Code).
* Add tags ([929ef2b](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/929ef2b75195b8db11894cd69bc4b2a450cebd69) by Justin Drew - Network To Code).

### Bug Fixes

* :bug: fix customfields not being added to ipaddress ([36a1dad](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/36a1dadfedd6d0f3a45364757cd0e00b7ad8118c) by Justin Drew - Network To Code).

* Fix tests ([d224c76](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/d224c768bdcb3802b9243ea0236e6e1ad10dde1c) by Justin Drew - Network To Code).
* Fix diffs ([5b5e8fe](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/5b5e8fe5a4a400771be8dc5c6c1bc039481daeb1) by Justin Drew - Network To Code).
* Fix model updates ([51bae7e](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/51bae7e43aff2af6557315987b03e0132ccad0b2) by Justin Drew - Network To Code).
* Fix platform ([81da171](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/81da171a683c7f211b4d0d0200ee778bfa10ca84) by Justin Drew - Network To Code).
* Fix ip assignment ([53c8e70](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/53c8e70a197067ca62dd1e9abc62ec8c4cb02946) by Justin Drew - Network To Code).
* Fix vrf to use obj, not name ([9877ff2](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/9877ff25af995722490f56749f822f4b2b612d53) by Justin Drew).

## [v0.6.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/tags/v0.6.0) - 2021-08-27

<small>[Compare with v0.4.1](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/compare/v0.4.1...v0.6.0)</small>

### Added

* Add ip addresses ([afdcaae](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/afdcaae2b202978fc71ab082d1933cf79c27868c) by Justin Drew - Network To Code).

* Add prefixes ([9fe3086](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/9fe3086e959e1b198c572f6a5b8856ee73d50dac) by Justin Drew - Network To Code).
* Add vrfs ([8ccaf12](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/8ccaf128a62d2125c4fa34b5ab425af2b2aaf925) by Justin Drew - Network To Code).
* Add ports ([9873430](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/9873430a23bac50cf3d6b1451163e43602051b67) by Justin Drew - Network To Code).

## [v0.4.1](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/tags/v0.4.1) - 2021-08-17

<small>[Compare with v0.3.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/compare/v0.3.0...v0.4.1)</small>

### Added

* Add clusters and devices ([116b741](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/116b741747e7f0d4f77b5ab78f703e5e934a8f5e) by Justin Drew - Network To Code).

* Add vendors ([860f9fc](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/860f9fc5bc8df502bc1d61db300bb9f1a0ca241e) by Justin Drew).
* Add racks ([13e92fa](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/13e92fa1f6a644c2728a9eaa6382e40d263c73e9) by Justin Drew - Network To Code).

## [v0.3.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/tags/v0.3.0) - 2021-07-28

<small>[Compare with v0.2.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/compare/v0.2.0...v0.3.0)</small>

### Added

* Add site sync support ([4c6ac8f](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/commit/4c6ac8f2e516f9311daa1e7441b834e53793644d) by Justin Drew - Network To Code).

## [v0.2.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/tags/v0.2.0) - 2021-07-15

<small>[Compare with v0.1.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/compare/v0.1.0...v0.2.0)</small>

## [v0.1.0](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/tags/v0.1.0) - 2021-07-15

<small>[Compare with first commit](https://github.com/networktocode-llc/nautobot-plugin-ssot-device42/compare/41ddaf01ba6afd1d8f91be6264e634f6c37428fb...v0.1.0)</small>
