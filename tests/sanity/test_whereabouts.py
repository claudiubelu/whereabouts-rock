#
# Copyright 2024 Canonical, Ltd.
#

from k8s_test_harness.util import docker_util, env_util

ROCK_EXPECTED_FILES = [
    "/host",
    "/install-cni.sh",
    "/ip-control-loop",
    "/whereabouts",
]


def _test_whereabouts_rock(image_version, expected_files):
    """Test Whereabouts rock."""
    rock = env_util.get_build_meta_info_for_rock_version(
        "whereabouts", image_version, "amd64"
    )
    image = rock.image

    # check rock filesystem
    docker_util.ensure_image_contains_paths_bare(image, expected_files)

    # check binary name and version.
    version = docker_util.get_image_version(image)
    process = docker_util.run_in_docker(image, ["/whereabouts", "version"])
    output = process.stderr
    assert "whereabouts" in output and version in output

    # check other binary. It expects KUBERNETES_SERVICE_HOST to be defined.
    process = docker_util.run_in_docker(image, ["/ip-control-loop"], False)
    assert "KUBERNETES_SERVICE_HOST" in process.stderr

    # check script. It expects serviceaccount token to exist.
    process = docker_util.run_in_docker(image, ["bash", "-x", "/install-cni.sh"], False)
    assert (
        "cat: /var/run/secrets/kubernetes.io/serviceaccount/token: No such file or directory"
        in process.stderr
    )

    # whereabouts:0.5.4 also has a /ip-reconciler
    if version == "0.5.4":
        process = docker_util.run_in_docker(image, ["/ip-reconciler"], False)
        expected_message = "failed to instantiate the Kubernetes client"
        assert expected_message in process.stderr


def test_whereabouts_rock_0_6_3():
    _test_whereabouts_rock("0.6.3", ROCK_EXPECTED_FILES)


def test_whereabouts_rock_0_6_1():
    _test_whereabouts_rock("0.6.1", ROCK_EXPECTED_FILES)


def test_whereabouts_rock_0_5_4():
    _test_whereabouts_rock("0.5.4", ROCK_EXPECTED_FILES + ["/ip-reconciler"])
