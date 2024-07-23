from hamcrest import assert_that, equal_to
from dsmlp.app.config import GPU_LABEL
from dsmlp.app.validator import Validator
from src.dsmlp.app.types import *
from typing import List


def gen_request(gpu_req: int = 0, gpu_lim: int = 0, low_priority: bool = False, uid: str = "705ab4f5-6393-11e8-b7cc-42010a800002", course: str = None,
                run_as_user: int = None, run_as_group: int = None, fs_group: int = None, supplemental_groups: List[int] = None, username: str = None, has_container: bool = True,
                container_override: List[Container] = None, init_containers: List[Container] = None) -> Request:
    
    # add default username is user10 unless specified during testing
    if username is None:
        username = 'user10'
        
    res_req = None
    if gpu_req > 0:
        if res_req is None:
            res_req = ResourceRequirements()

        res_req.requests = {GPU_LABEL: gpu_req}

    if gpu_lim > 0:
        if res_req is None:
            res_req = ResourceRequirements()

        res_req.limits = {GPU_LABEL: gpu_lim}

    p_class = None
    if low_priority:
        p_class = "low"

    labels = {}
    if course is not None:
        labels["dsmlp/course"] = course

    metadata = None
    if labels != {}:
        metadata = ObjectMeta(labels=labels)

    sec_context = None
    if run_as_user is not None or run_as_group is not None or fs_group is not None or supplemental_groups is not None:
        sec_context = PodSecurityContext(
            runAsUser=run_as_user, runAsGroup=run_as_group, fsGroup=fs_group, supplementalGroups=supplemental_groups)

    containers = []
    if has_container:
        c = Container(resources=res_req)

        if run_as_user is not None or run_as_group is not None:
            c.securityContext = SecurityContext(runAsUser=run_as_user,
                                                runAsGroup=run_as_group)

        containers.append(c)

    if container_override is not None:
        containers = container_override

    request = Request(
        uid=uid,
        namespace=username,
        object=Object(
            metadata=metadata,
            spec=PodSpec(
                containers=containers,
                priorityClassName=p_class,
                securityContext=sec_context,
                initContainers=init_containers
            )
        ),
        userInfo=UserInfo(username=username)
    )

    return request


def try_val_with_component(validator: Validator, json, expected: bool, message: str = None):
    try:
        response = validator.validate_pod(json)
        if not expected:
            raise AssertionError(f"Expected exception but got {response}")
    except Exception as e:
        if expected:
            raise AssertionError(f"Expected no exception but got {e}")
        assert_that(e.message, equal_to(message))
