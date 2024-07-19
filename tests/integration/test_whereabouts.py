#
# Copyright 2024 Canonical, Ltd.
#

import logging
from pathlib import Path

from k8s_test_harness import harness
from k8s_test_harness.util import env_util, k8s_util

LOG = logging.getLogger(__name__)

DIR = Path(__file__).absolute().parent
MANIFESTS_DIR = DIR / ".." / "templates"


def _get_whereabouts_helm_cmd():
    whereabouts_rock = env_util.get_build_meta_info_for_rock_version(
        "whereabouts", "0.6.3", "amd64"
    )
    rock_image = whereabouts_rock.image

    # This helm chart requires the registry to be separated from the image.
    registry = "docker.io"
    parts = rock_image.split("/")
    if len(parts) > 1:
        registry = parts[0]
        rock_image = parts[1]

    images = [
        k8s_util.HelmImage(rock_image),
    ]

    return k8s_util.get_helm_install_command(
        "whereabouts",
        "oci://registry-1.docker.io/bitnamicharts/whereabouts",
        "whereabouts",
        images=images,
        set_configs=[f"image.registry={registry}"],
    )


def test_integration_whereabouts(module_instance: harness.Instance):
    # We also need multus in order to test out whereabouts.
    # It should become Available if everything is fine with it.
    helm_cmd = k8s_util.get_helm_install_command(
        "multus", "oci://registry-1.docker.io/bitnamicharts/multus-cni"
    )
    module_instance.exec(helm_cmd)
    k8s_util.wait_for_daemonset(module_instance, "multus-multus-cni", "kube-system")

    module_instance.exec(_get_whereabouts_helm_cmd())
    k8s_util.wait_for_daemonset(module_instance, "whereabouts", "whereabouts")

    # Create a NetworkAttachmentDefinition and a deployment requiring it.
    for filename in ["whereabouts-net-definition.yaml", "deployment.yaml"]:
        manifest = MANIFESTS_DIR / filename
        module_instance.exec(
            ["k8s", "kubectl", "apply", "-f", "-"],
            input=Path(manifest).read_bytes(),
        )

    k8s_util.wait_for_deployment(module_instance, "netshoot-deployment")
