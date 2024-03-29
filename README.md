# Nautobot Device42 Sync

A plugin for [Nautobot](https://github.com/nautobot/nautobot).

## Installation

The plugin is available as a Python package in pypi and can be installed with pip

```shell
pip install nautobot-ssot-device42
```

> The plugin is compatible with Nautobot 1.1.0 and higher

To ensure Nautobot Device42 Sync is automatically re-installed during future upgrades, create a file named `local_requirements.txt` (if not already existing) in the Nautobot root directory (alongside `requirements.txt`) and list the `nautobot-ssot-device42` package:

```no-highlight
# echo nautobot-ssot-device42 >> local_requirements.txt
```

Once installed, the plugin needs to be enabled in your `nautobot_configuration.py`

```python
# In your configuration.py
PLUGINS = ["nautobot_ssot", "nautobot_ssot_device42"]

PLUGINS_CONFIG = {
  "nautobot_ssot_device42": {
    "device42_host": os.getenv("DEVICE42_HOST", ""),
    "device42_username": os.getenv("DEVICE42_USERNAME", ""),
    "device42_password": os.getenv("DEVICE42_PASSWORD", ""),
    "verify_ssl": False,
    "defaults": {
        "site_status": "Active",
        "rack_status": "Active",
        "device_role": "Unknown",
    },
    "delete_on_sync": False,
    "use_dns": False,
    "customer_is_facility": False,
    "facility_prepend": "sitecode-",
    "role_prepend": "nautobot-",
    "ignore_tag": "",
    "hostname_mapping": [],
  }
}
```

The plugin behavior can be controlled with the following list of settings

- *device42_host* - This defines the FQDN of the Device42 instance you wish to connect to, including the protocol, ie `https://device42.example.com`.
- *device42_username* - This defines the username of the account used to connect to the Device42 API endpoint.
- *device42_password* - This defines the password of the account used to connect to the Device42 API endpoint.
- *verify_ssl* - This denotes whether SSL validation of the Device42 endpoint should be enabled or not. This is helpful in cases where you have a self-signed certificate in use for a test instance.
*defaults* - These are intended to be options to customize what a particular object attribute will be set to if the information is unable to be obtained from Device42. These allow you to specify a default Site or Rack status along with the default Device role.
- *delete_on_sync* - This option prevents objects from being deleted from Nautobot during a synchronization. This is handy if your Device42 data fluctuates a lot and you wish to control what is removed from Nautobot. This means objects will only be added, never deleted when set to False.
- *use_dns* - This option enables the DNS resolution of Device's for assigning primary IP addresses. When True, there will be an additional process of performing DNS queries for each Device in the sync and if an A record is found, will be assigned as primary IP for the Device. It will attempt to use the interface for the IP based upon data from Device42 but will create a Management interface and assign the IP to it if an interface can't be determined.
- *customer_is_facility* - This option is for when you are utilizing the Customer field in Device42 to denote the site code, or facility, for the Site that the particular object resides in.
- *facility_prepend* - This defines the string that is expected on a Tag when determining a Building's site code. If a Building has a Tag that starts with `sitecode-` it will assume the remaining Tag is the facility code.
- *role_prepend* - Like the `facility_prepend` option, this defines the string on a Tag that defines a Device's role. If a Device has a Tag that starts with `nautobot-` it will assume the remaining string is the name of the Device's role, such as `access-switch` for example.
- *ignore_tag* - This option allows you to define a Tag string that when found on a Device will exempt it from the sync. This is helpful for cases where you want to ensure certain Devices aren't imported.
- *hostname_mapping* - This option allows you to define a mapping of a regex pattern that defines a Device's hostname and which Site the Device should be assigned. This is helpful if the location information for Devices in Device42 is inaccurate and your Device's are named with the Site name or code in it. For example, if you have Device's called `DFW-access-switch`, you could map that as `^DFW.+: dallas` where `dallas` is the slug form for your Site name.

## Usage

Once the plugin is installed and configured, you will be able to perform a data import from Device42. From the Nautobot SSoT Dashboard view (`/plugins/ssot/`), Device42 will show as a Data Source.

![Dashboard View](./docs/images/dashboard.png)

From the Dashboard, you can also view more information about the App by clicking on the Device42 link and see the Detail view. This view will show the mappings of Device42 objects to Nautobot objects, the sync history, and other configuration details for the App:

![Detail View](./docs/images/detail-view.png)

To start the synchronization, simply click the `Sync Now` button on the Dashboard to start the Job.

Running this Job will redirect you to a `Nautobot Job Result` view.

![JobResult View](./docs/images/jobresult.png)

Once the Job has finished you can access the `SSoT Sync Details` page to see detailed information about the data that was synchronized from Device42 and the outcome of the sync Job.

![SSoT Sync Details](./docs/images/ssot-sync-details.png)

### API

TODO

## Contributing

Pull requests are welcomed and automatically built and tested against multiple version of Python and multiple version of Nautobot through TravisCI.

The project is packaged with a light development environment based on `docker-compose` to help with the local development of the project and to run the tests within TravisCI.

The project is following Network to Code software development guideline and is leveraging:

- Black, Pylint, Bandit and pydocstyle for Python linting and formatting.
- Django unit test to ensure the plugin is working properly.

### Development Environment

The development environment can be used in 2 ways. First, with a local poetry environment if you wish to develop outside of Docker with the caveat of using external services provided by Docker for PostgresQL and Redis. Second, all services are spun up using Docker and a local mount so you can develop locally, but Nautobot is spun up within the Docker container.

Below is a quick start guide if you're already familiar with the development environment provided, but if you're not familiar, please read the [Getting Started Guide](GETTING_STARTED.md).

#### Invoke

The [PyInvoke](http://www.pyinvoke.org/) library is used to provide some helper commands based on the environment.  There are a few configuration parameters which can be passed to PyInvoke to override the default configuration:

* `nautobot_ver`: the version of Nautobot to use as a base for any built docker containers (default: 1.0.3)
* `project_name`: the default docker compose project name (default: nautobot_ssot_device42)
* `python_ver`: the version of Python to use as a base for any built docker containers (default: 3.6)
* `local`: a boolean flag indicating if invoke tasks should be run on the host or inside the docker containers (default: False, commands will be run in docker containers)
* `compose_dir`: the full path to a directory containing the project compose files
* `compose_files`: a list of compose files applied in order (see [Multiple Compose files](https://docs.docker.com/compose/extends/#multiple-compose-files) for more information)

Using **PyInvoke** these configuration options can be overridden using [several methods](http://docs.pyinvoke.org/en/stable/concepts/configuration.html).  Perhaps the simplest is simply setting an environment variable `INVOKE_NAUTOBOT_SSOT_DEVICE42_VARIABLE_NAME` where `VARIABLE_NAME` is the variable you are trying to override.  The only exception is `compose_files`, because it is a list it must be overridden in a yaml file.  There is an example `invoke.yml` (`invoke.example.yml`) in this directory which can be used as a starting point.

#### Local Poetry Development Environment

1. Copy `development/creds.example.env` to `development/creds.env` (This file will be ignored by Git and Docker)
2. Uncomment the `POSTGRES_HOST`, `REDIS_HOST`, and `NAUTOBOT_ROOT` variables in `development/creds.env`
3. Create an `invoke.yml` file with the following contents at the root of the repo (you can also `cp invoke.example.yml invoke.yml` and edit as necessary):

```yaml
---
nautobot_ssot_device42:
  local: true
  compose_files:
    - "docker-compose.requirements.yml"
```

3. Run the following commands:

```shell
poetry shell
poetry install --extras nautobot
export $(cat development/dev.env | xargs)
export $(cat development/creds.env | xargs) 
invoke start && sleep 5
nautobot-server migrate
```

> If you want to develop on the latest develop branch of Nautobot, run the following command: `poetry add --optional git+https://github.com/nautobot/nautobot@develop`. After the `@` symbol must match either a branch or a tag.

4. You can now run nautobot-server commands as you would from the [Nautobot documentation](https://nautobot.readthedocs.io/en/latest/) for example to start the development server:

```shell
nautobot-server runserver 0.0.0.0:8080 --insecure
```

Nautobot server can now be accessed at [http://localhost:8080](http://localhost:8080).

It is typically recommended to launch the Nautobot **runserver** command in a separate shell so you can keep developing and manage the webserver separately.

#### Docker Development Environment

This project is managed by [Python Poetry](https://python-poetry.org/) and has a few requirements to setup your development environment:

1. Install Poetry, see the [Poetry Documentation](https://python-poetry.org/docs/#installation) for your operating system.
2. Install Docker, see the [Docker documentation](https://docs.docker.com/get-docker/) for your operating system.

Once you have Poetry and Docker installed you can run the following commands to install all other development dependencies in an isolated python virtual environment:

```shell
poetry shell
poetry install
invoke start
```

Nautobot server can now be accessed at [http://localhost:8080](http://localhost:8080).

To either stop or destroy the development environment use the following options.

- **invoke stop** - Stop the containers, but keep all underlying systems intact
- **invoke destroy** - Stop and remove all containers, volumes, etc. (This results in data loss due to the volume being deleted)

### CLI Helper Commands

The project is coming with a CLI helper based on [invoke](http://www.pyinvoke.org/) to help setup the development environment. The commands are listed below in 3 categories `dev environment`, `utility` and `testing`.

Each command can be executed with `invoke <command>`. Environment variables `INVOKE_NAUTOBOT_SSOT_DEVICE42_PYTHON_VER` and `INVOKE_NAUTOBOT_SSOT_DEVICE42_NAUTOBOT_VER` may be specified to override the default versions. Each command also has its own help `invoke <command> --help`

#### Docker dev environment

```no-highlight
  build            Build all docker images.
  debug            Start Nautobot and its dependencies in debug mode.
  destroy          Destroy all containers and volumes.
  restart          Restart Nautobot and its dependencies.
  start            Start Nautobot and its dependencies in detached mode.
  stop             Stop Nautobot and its dependencies.
```

#### Utility

```no-highlight
  cli              Launch a bash shell inside the running Nautobot container.
  create-user      Create a new user in django (default: admin), will prompt for password.
  makemigrations   Run Make Migration in Django.
  nbshell          Launch a nbshell session.
```

#### Testing

```no-highlight
  bandit           Run bandit to validate basic static code security analysis.
  black            Run black to check that Python files adhere to its style standards.
  flake8           This will run flake8 for the specified name and Python version.
  pydocstyle       Run pydocstyle to validate docstring formatting adheres to NTC defined standards.
  pylint           Run pylint code analysis.
  tests            Run all tests for this plugin.
  unittest         Run Django unit tests for the plugin.
```

### Project Documentation

Project documentation is generated by [mkdocs](https://www.mkdocs.org/) from the documentation located in the docs folder.  You can configure [readthedocs.io](https://readthedocs.io/) to point at this folder in your repo.  For development purposes a `docker-compose.docs.yml` is also included.  A container hosting the docs will be started using the invoke commands on [http://localhost:8001](http://localhost:8001), as changes are saved the docs will be automatically reloaded.

## Questions

For any questions or comments, please check the [FAQ](FAQ.md) first and feel free to swing by the [Network to Code slack channel](https://networktocode.slack.com/) (channel #networktocode).
Sign up [here](http://slack.networktocode.com/)

## Screenshots

TODO
