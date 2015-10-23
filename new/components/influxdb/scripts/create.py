import importlib
import os
import time

from cloudify import ctx

utils_path = ctx.download_resource('components/utils.py', os.getcwd)
utils = importlib.import_module(utils_path)


config_path = "components/influxdb/config"


influxdb_source_url = ctx.node.properties['influxdb_rpm_source_url']
influxdb_endpoint_ip = ctx.node.properties['influxdb_endpoint_ip']
# currently, cannot be changed due to the webui not allowing to configure it.
influxdb_endpoint_port = '8086'

influxdb_user = 'influxdb'
influxdb_group = 'influxdb'
influxdb_home = '/opt/influxdb'
influxdb_log_path = '/var/log/cloudify/influxdb'


def configure_influxdb(host, port):
    db_user = "root"
    db_pass = "root"
    db_name = "cloudify"

    ctx.logger.info('Creating InfluxDB Database...')
    utils.run('sudo curl --show-error --silent --retry 5 '
              '"http://{0}:{1}/db?u={2}&p={3}" '
              '-d "{\"name\": \"{4}\"}"'.format(
                  host, port, db_user, db_pass, db_name))
    # result = $(curl --show-error --silent --retry 5 "http://${INFLUXDB_HOST}:${INFLUXDB_PORT}/cluster_admins?u=${DB_USER}&p=${DB_PASS}")
    # ctx.logger.info('InfluxDB creation test: {0}'.format(result))


def install_influxdb():
    ctx.logger.info('Installing InfluxDB...')
    utils.set_selinux_permissive

    utils.copy_notice('influxdb')
    utils.create_dir(influxdb_home)
    utils.create_dir(influxdb_log_path)

    utils.yum_install(influxdb_source_url)

    ctx.logger.info('Deploying InfluxDB config.toml...')
    utils.deploy_blueprint_resource(
        '{0}/config.toml'.format(config_path),
        '{0}/shared/config.toml'.format(influxdb_home))

    ctx.logger.info('Fixing user permissions...')
    utils.chown(influxdb_user, influxdb_group, influxdb_home)
    utils.chown(influxdb_user, influxdb_group, influxdb_log_path)

    utils.configure_systemd_service('influxdb')


if influxdb_endpoint_ip:
    ctx.logger.info('External InfluxDB Endpoint IP provided: {0}'.format(
        influxdb_endpoint_ip))
    time.sleep(5)
    utils.wait_for_port(influxdb_endpoint_port, influxdb_endpoint_ip)
    configure_influxdb(influxdb_endpoint_ip, influxdb_endpoint_port)
else:
    influxdb_endpoint_ip = ctx.instance.host_ip
    install_influxdb()

    ctx.logger.info('Starting InfluxDB Service...')
    utils.start_systemd_service('cloudify-influxdb')

    utils.wait_for_port(influxdb_endpoint_port, influxdb_endpoint_ip)
    configure_influxdb(influxdb_endpoint_ip, influxdb_endpoint_port)

    ctx.logger.info('Stopping InfluxDB Service...')
    utils.stop_systemd_service('cloudify-influxdb')


ctx.instance.runtime_properties['influxdb_endpoint_ip'] = influxdb_endpoint_ip
