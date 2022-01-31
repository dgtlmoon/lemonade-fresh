#!/usr/bin/python3


# Yaml loaders and dumpers
from ruamel.yaml.main import \
    round_trip_load as yaml_load, \
    round_trip_dump as yaml_dump

# Yaml commentary
from ruamel.yaml.comments import \
    CommentedMap as OrderedDict, \
    CommentedSeq as OrderedList

# For manual creation of tokens
from ruamel.yaml.tokens import CommentToken
from ruamel.yaml.error import CommentMark

# Globals
# Number of spaces for an indent
INDENTATION = 2
# Used to reset comment objects
tsRESET_COMMENT_LIST = [None, [], None, None]


def rebuild_docker_compose(PaidInstance, path_to_docker_compose_file="../data"):
    services={}
    instances = PaidInstance.query.filter(PaidInstance.is_active == True)
    volumes_names=[]
    for instance in instances:
        volume_name="paid_instance_{}-data".format(instance.instance_name)
        volumes_names.append(volume_name)
        services["paid_instance_" + instance.instance_name] = OrderedDict({
            # it will be listening on 5000 by default
            "image": instance.instance_image,
            "networks": ["provisioner_net"],
            "environment": ["USE_X_SETTINGS=1", "SALTED_PASS={}".format(instance.salted_pass),"WEBDRIVER_URL=http://browser-chrome:4444/wd/hub"],
            "hostname": instance.instance_name,
            "volumes": [volume_name + ':/datastore'],
            "restart": "unless-stopped",

            # Multiple containers, use same port numner, thats ok
            # "ports": [ "80:80" ],
            # "expose": [80]
        })

    instances_list = OrderedDict({
        "version": "2",
        "services": services,
        "volumes": {},
        "networks": OrderedDict({
            "provisioner_net": None
        })
    })
    for v in volumes_names:
        instances_list["volumes"][v]=None

    with open("{}/docker-compose-paid-instances.yml".format(path_to_docker_compose_file), "w") as f:
        f.write(yaml_dump(instances_list))

