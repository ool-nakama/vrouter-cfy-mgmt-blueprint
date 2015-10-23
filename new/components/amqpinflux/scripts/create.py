import importlib
import os

from cloudify import ctx
from cloudify.state import ctx_parameters as inputs

utils_path = ctx.download_resource('components/utils.py', os.getcwd)
utils = importlib.import_module(utils_path)


amqpinflux_rpm_source_url = ctx.node.properties['amqpinflux_rpm_source_url']
amqpinflux_source_url = ctx.node.properties['amqpinflux_module_source_url']
ctx.instance.runtime_properties['influxdb_endpoint_ip'] = \
    inputs['influxdb_endpoint_ip']

amqpinflux_home = "/opt/amqpinflux"
amqpinflux_user = "amqpinflux"
amqpinflux_group = "amqpinflux"
amqpinflux_virtualenv_dir = "${AMQPINFLUX_HOME}/env"


ctx.logger.info("Installing AQMPInflux...")
utils.set_selinux_permissive()
utils.copy_notice('amqpinflux')
utils.create_dir(amqpinflux_home)
utils.yum_install(amqpinflux_rpm_source_url)

if amqpinflux_source_url:
    utils.install_module(amqpinflux_source_url, amqpinflux_virtualenv_dir)

utils.create_service_user(amqpinflux_user, amqpinflux_home)
ctx.logger.info("Fixing permissions...")
utils.run('sudo chown -R {0}:{1} {2}'.format(
    amqpinflux_user, amqpinflux_group, amqpinflux_home))
utils.configure_systemd_service('amqpinflux')
