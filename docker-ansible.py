#!/usr/bin/env python
#
# The MIT License (MIT)
# 
# Copyright (c) 2013 Cove Schneider
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

DOCUMENTATION = '''
---
module: docker
short_description: manage docker containers
description:
     - manage the life cycle of docker containers. This module has a dependency on the docker-py python module.
version_added: "0.1"
options:
  count:
    description:
      - number of containers to launch on this host
    required: False
    default: 1
    aliases: []
  image:
    description:
       - image to use for this operation
    required: true
    default: null
    aliases: []
  command:
    description:
       - command to run, or validate is running, in a container
    required: true
    default: null
    aliases: []
  ports:
    description:
      - private to public port mapping specification (see PortSpecs in the Docker manual)
    required: false
    default: null
    aliases: []
  volumes:
    description:
      - volume(s) to mount on the container
    required: false
    default: null
    aliases: []
  volumes_from:
    description:
      - shared volume(s) from another container
    required: false
    default: null
    aliases: []
  memory_limit:
    description:
      - RAM allocated to container
    required: false
    default: null
    aliases: []
    default: 256MB
  memory_swap:
    description:
      - Virtual memory swap space allocated to container
    required: false
    default: 0
    aliases: []
  docker_url:
    description:
      - URL of docker deamon to issue commands to
    required: false
    default: http://127.0.0.1:4243
    aliases: []
  username:
    description:
      - username
    required: false
    default: null
    aliases: []
  password:
    description:
      - password
    required: false
    default: null
    aliases: []
  hostname:
    description:
      - Container hostname
    required: false
    default: null
    aliases: []
  env:
    description:
      - Set environment variables
    required: false
    default: null
    aliases: []
  dns:
    description:
      - Set custom DNS servers for the container
    required: false
    default: null
    aliases: []
  detach:
    description:
      - Enable detached mode on start up, leaves container running in background
    required: false
    default: true
    aliases: []
  state:
    description:
      - Set the state of the container
    required: false
    default: present
    choices: [ "present", "absent", "kill", "restart" ]
    aliases: []
author: Cove Schneider
'''

EXAMPLES = '''
# Basic provisioning example, will start a container on each docker host in the group
# and out put hello world.
action:
    module: docker 
    image: base
    command: while [ 1 ]; do /bin/echo hello world; sleep 1; done

# Provisions a custom container running tomcat on each host in the group, mapping port 8080
# from the container directly to the docker host (i.e. with out NAT'ing the port). 
action: 
    module: docker 
    memory_limit: 1G
    image: cove/tomcat7
    command: service start tomcat7
    ports: :8080

# Stops all containers running tomcat from the previous example.
action: 
    module: docker
    state: absent
    image: cove/tomcat7
    command: service start tomcat7

# Start 5 containers on each docker host using the docker remote API only.
local_action:
    module: docker
    image: cove/tomcat7
    command: service start tomcat7
    docker_url: http://$inventory_hostname:4342
    count: 5

# To access docker container details in a subsequent tasks, such as which port 8080 was mapped to:
action:
    module: shell
    command: echo Mapped port 8080 to ${DockerContainers[0].NetworkSettings.PortMapping.8080}

# Sample playbook
- name: ansible + docker playbook
  hosts: web
  user: root
  tasks:
  - name: run tomcat servers
    action: docker image=cove/tomcat7 command=/start-tomcat.sh ports=8080 count=5
  - name: echo ports
    action: shell echo Mapped to ${inventory_hostname}:${item.NetworkSettings.PortMapping.8080} >> /tmp/file.out
    with_items: $DockerContainers 
'''

try:
    import sys
    import json
    import docker.client
    from urlparse import urlparse
except ImportError, e:
    print "failed=True msg='failed to import python module: %s'" % e
    sys.exit(1)

def _human_to_bytes(number):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

    if isinstance(number, int):
        return number
    if number[-1] == suffixes[0] and number[-2].isdigit():
        return number[:-1]

    i = 1
    for each in suffixes[1:]:
        if number[-len(each):] == suffixes[i]:
            return int(number[:-len(each)]) * (1024 ** i)
        i = i + 1

    print "failed=True msg='Could not convert %s to integer'" % (number)
    sys.exit(1)
            
def _ansible_facts(container_list):
    return {"DockerContainers": container_list}

def main():
    module = AnsibleModule(
        argument_spec = dict(
            count           = dict(default=1),
            image           = dict(required=True),
            command         = dict(required=True),
            ports           = dict(),
            volumes         = dict(default={}),
            volumes_from    = dict(default=str("")),
            memory_limit    = dict(default=_human_to_bytes("256MB")),
            memory_swap     = dict(default=0),
            docker_url      = dict(default='http://127.0.0.1:4243'),
            user            = dict(default=""),
            password        = dict(),
            hostname        = dict(default=""),
            env             = dict(),
            dns             = dict(),
            detach          = dict(default=True),
            state           = dict(default='present', choices=['absent', 'present', 'stop', 'kill', 'restart']),
            debug           = dict(default=False)
        )
    )
    count        = int(module.params.get('count'))
    image        = module.params.get('image')
    command      = module.params.get('command')
    ports        = module.params.get('ports')
    volumes      = module.params.get('volumes')
    volumes_from = module.params.get('volumes_from')
    memory_limit = _human_to_bytes(module.params.get('memory_limit'))
    memory_swap  = module.params.get('memory_swap')
    docker_url   = urlparse(module.params.get('docker_url'))
    user         = module.params.get('user')
    password     = module.params.get('password')
    hostname     = module.params.get('hostname')
    env          = module.params.get('env')
    dns          = module.params.get('dns')
    detach       = module.params.get('detach')
    state        = module.params.get('state')
    debug        = module.params.get('debug')

    failed = False
    changed = False
    container_summary  = []
    running_containers = []
    running_count = 0
    msg = None

    # connect to docker server
    if docker_url.port == None:
        docker_url = urlparse(docker_url.geturl() + ":4243")
    if docker_url.scheme == '':
        docker_url = urlparse("http://" + docker_url.geturl())
    docker_client = docker.Client(base_url=docker_url.geturl())

    # don't support older versions
    docker_info = docker_client.info()
    if docker_info['Version'] < "0.3.3":
        module.fail_json(changed=changed, msg="Minimum Docker version required is 0.3.3")
 
    # determine which images/commands are running already
    for each in docker_client.containers():
        if each["Image"].split(":")[0] == image.split(":")[0] and each["Command"].strip() == command.strip():
            details = docker_client.inspect_container(each['Id'])
            running_containers.append(details)
            running_count = running_count + 1

    delta     = count - running_count
    restarted = 0
    started   = 0
    stopped   = 0
    killed    = 0

    # start/stop images
    if state == "present":
        params = {'image':        image,
                  'command':      command,
                  'ports':        ports,
                  'volumes':      volumes,
                  'volumes_from': volumes_from,
                  'mem_limit':    memory_limit,
                  'environment':  env,
                  'dns':          dns,
                  'hostname':     hostname,
                  'detach':       detach,}

        containers = []
 
        # start more containers if we don't have enough
        if delta > 0:
            try:
                containers = [docker_client.create_container(**params) for _ in range(delta)]
                changed = True
            except ValueError:
                docker_client.pull(image)
                changed = True
                containers = [docker_client.create_container(**params) for _ in range(delta)]
    
            docker_client.start(*[i['Id'] for i in containers])
            details = [docker_client.inspect_container(i['Id']) for i in containers]
            for each in details:
                running_containers.append(details)
                container_summary.append(details)
                if each["State"]["Running"] == True:
                    started = started + 1

        # stop containers if we have too many
        elif delta < 0:
            docker_client.stop(*[i['Id'] for i in running_containers[0:abs(delta)]])
            changed = True

            try:
                docker_client.wait(*[i['Id'] for i in running_containers[0:abs(delta)]])
            except ValueError:
                pass

            details = [docker_client.inspect_container(i['Id']) for i in running_containers[0:abs(delta)]]
            for each in details:
                running_containers = [i for i in running_containers if i['Id'] != each['Id']]
                if each["State"]["Running"] == False:
                    stopped = stopped + 1
            docker_client.remove_container(*[i['Id'] for i in details])
            container_summary = running_containers

    # stop and remove containers
    elif state == "absent":
        docker_client.stop(*[i['Id'] for i in running_containers])
        changed = True

        try:
            docker_client.wait(*[i['Id'] for i in running_containers])
        except ValueError:
            pass

        details = [docker_client.inspect_container(i['Id']) for i in running_containers[0:delta]]
        for each in details:
            container_summary.append(details)
            if each["State"]["Running"] == False:
                stopped = stopped + 1
        docker_client.remove_container(*[i['Id'] for i in details])

    # stop containers
    elif state == "stop":
        docker_client.stop(*[i['Id'] for i in running_containers])
        changed = True

        try:
            docker_client.wait(*[i['Id'] for i in running_containers])
        except ValueError:
            pass

        details = [docker_client.inspect_container(i['Id']) for i in running_containers[0:delta]]
        for each in details:
            container_summary.append(details)
            if each["State"]["Running"] == False:
                stopped = stopped + 1

    # kill containers    
    elif state == "kill":
        docker_client.kill(*[i['Id'] for i in running_containers])
        changed = True

        try:
            docker_client.wait(*[i['Id'] for i in running_containers])
        except ValueError:
            pass

        details = [docker_client.inspect_container(i['Id']) for i in running_containers[0:delta]]
        for each in details:
            container_summary.append(details)
            if each["State"]["Running"] == False:
                killed = killed + 1
        docker_client.remove_container(*[i['Id'] for i in details])

    # restart containers    
    elif state == "restart":
        docker_client.restart(*[i['Id'] for i in running_containers])
        changed = True

        details = [docker_client.inspect_container(i['Id']) for i in running_containers[0:delta]]
        for each in details:
            container_summary.append(details)
            if each["State"]["Running"] == True:
                restarted = restarted + 1

        msg = "Started %d, stopped %d, killed %d, restarted %d container(s) running image %s with command %s" %\
                (started, stopped, killed, restarted, image, command)

    module.exit_json(failed=failed, changed=changed, msg=msg, ansible_facts=_ansible_facts(container_summary))

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()
