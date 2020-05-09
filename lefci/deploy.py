import subprocess
import os
import jinja2


class CommandException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args)


class ConfigException(CommandException):
    def __init__(self, *args, **kwargs):
        CommandException.__init__(self, *args, **kwargs)


def transform_config(config):
    module_path = os.path.dirname(__file__)
    template_path = os.path.join(module_path, 'templates')
    template_loader = jinja2.FileSystemLoader(searchpath=template_path)
    template_environment = jinja2.Environment(loader=template_loader)
    template = template_environment.get_template('syslog-ng.conf.jinja')
    return template.render(config.encode())


def create_syslog_config(config, filepath):
    syslog_config = transform_config(config)
    with open(filepath, 'w') as syslog_file:
        syslog_file.write(syslog_config)


def run_command(command, shell=False):
    proc = subprocess.run(command,
                          shell=shell,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          universal_newlines=True,
                          preexec_fn=os.setsid,
                          )
    output = proc.stdout
    if proc.returncode != 0:
        output = f'{output}\n{proc.stderr}'
        raise CommandException(output)
    return output


def ssh(command, server, key_file='/home/syslog-admin/.ssh/deploy_key', user='syslog-admin'):
    ssh_command = [f"ssh -i {key_file} -o StrictHostKeyChecking=no {user}@{server} '{command}'"]
    return run_command(ssh_command, shell=True)


def send_file(filepath, server, key_file='/home/syslog-admin/.ssh/deploy_key', user='syslog-admin'):
    command = f"/usr/bin/scp -i {key_file} -o StrictHostKeyChecking=no '{filepath}' {user}@{server}:"
    return run_command(command, shell=True)


def deploy_config(filepath, server, key_file='/home/syslog-admin/.ssh/deploy_key'):
    file_name = os.path.basename(filepath)
    send_file(filepath, server, key_file)
    ssh(f'syslog-ng -f {file_name} -s', server, key_file)
    ssh('mv running-config.conf running-config.conf.bak', server, key_file)
    ssh(f'mv {file_name} running-config.conf', server, key_file)
    ssh('sudo systemctl restart syslog-ng.service', server, key_file)


def deploy(config, server):
    file_name = 'deploy.conf'
    file_path = os.path.join('/tmp', file_name)
    create_syslog_config(config, file_path)
    deploy_config(file_path, server)
