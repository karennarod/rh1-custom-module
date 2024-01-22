#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from ansible.module_utils.basic import AnsibleModule
from minio import Minio
from minio.commonconfig import CopySource
from minio.error import (InvalidResponseError, S3Error)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: object

short_description: This is my test module

version_added: "1.0.0"

description: This is my longer description explaining my test module.

options:
    name:
        description: This is the msg to send to the test module.
        required: true
        type: str
    new:
        description:
            - Control to demo if the result of this module is changed or not.
            - Parameter description can be a list as well.
        required: false
        type: bool

author:
    - Karenna Rodriguez (@ykarennarod)
'''

EXAMPLES = r'''
# Upload an object to a bucket
- name: Upload an object
  rh1.minio.object:
    bucket: rh1_bucket
    object: rh1_object.txt
    mode: put
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
msg:
    description: The output msg that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''

def fput_object(module, client, bucket, object, src):
    """
    Put MinIO object of unknown size in specified bucket.

    Args:
      - module: Ansible module instance.
      - client: MinIO client instance.
      - bucket: Name of the MinIO bucket.
      - objec: Name of the MinIO object.
      - src: Content to be uploaded. 

    Returns:
      - Tuple: (success: bool, error_msg: str)
    """
    try:
        client.fput_object(bucket, object, src)
        return True, f'MinIO object {object} uploaded to {bucket} successfully.'
    except InvalidResponseError as e: 
        return False, str(e)

def fget_object(module, client, bucket, object, dest):
    # Get MinIO object from specified bucket.
    try:
        client.fget_object(bucket, object, dest)
        return True, f'MinIO object {object} retrieved successfully.'
    except InvalidResponseError as e:
        return False, None, str(e)

def remove_object(module, client, bucket, object):
    try: 
        client.remove_object(bucket, object)
        return True, f'MinIO object {object} removed successfully.'
    except InvalidResponseError as e:
        return False, str(e)

def list_object(module, client, bucket):
    try: 
        objects = [obj.object_name for obj in client.list_objects(bucket)]
        return True, f'Existing MinIO objects in {bucket}: {objects}'
    except InvalidResponseError as e: 
        return False, str(e)

def copy_object(module, client, bucket, object, src_bucket, src_object):
    try: 
        client.copy_object(bucket, object, CopySource(src_bucket, src_object))
        return True, f'MinIO object {src_object} copied to {object} successfully.'
    except (InvalidResponseError, S3Error) as e: 
        return False, str(e)

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        bucket=dict(type='str', required=True),
        object=dict(type='str', required=False),
        src=dict(type='str', required=False), 
        src_bucket=dict(type='str', required=False), 
        src_object=dict(type='str', required=False), 
        dest=dict(type='str', required=False), 
        mode=dict(type='str', choices=['get','put', 'copy', 'list', 'remove', 'stat', 'fget', 'fput'], required=True),
        access_key=dict(type='str', required=True),
        secret_key=dict(type='str', required=True),
        endpoint=dict(type='str', required=True),
    )

    result = dict(
        changed=False,
        msg=""
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
    
    client = Minio(
        module.params['endpoint'],
        access_key=module.params['access_key'],
        secret_key=module.params['secret_key'],
    )

    if module.check_mode:
        result['changed'] = True
        module.exit_json(**result)

    if module.params['mode'] == "remove": 
        success, msg = remove_object(
            module=module,
            client=client,
            bucket=module.params['bucket'], 
            object=module.params['object']
        )
        result['msg'] = msg

    elif module.params['mode'] == "fput": 
        success, msg = fput_object(
            module=module,
            client=client,
            bucket=module.params['bucket'], 
            object=module.params['object'], 
            src=module.params['src']
        )
        result['msg'] = msg
    
    elif module.params['mode'] == "fget": 
        success, msg = fget_object(
            module=module,
            client=client,
            bucket=module.params['bucket'], 
            object=module.params['object'], 
            dest=module.params['dest']
        )
        result['msg'] = msg

    elif module.params['mode'] == "list": 
        success, msg = list_object(
            module=module,
            client=client,
            bucket=module.params['bucket'], 
        )
        result['msg'] = msg
    
    elif module.params['mode'] == "copy": 
        success, msg = copy_object(
            module=module,
            client=client,
            bucket=module.params['bucket'], 
            object=module.params['object'], 
            src_bucket=module.params['src_bucket'], 
            src_object=module.params['src_object'], 
        )
        result['msg'] = msg

    elif module.params['mode'] == "stat": 
        success, msg = stat_object(
            module=module,
            client=client,
            bucket=module.params['bucket'], 
            object=module.params['object'], 
        )
        result['msg'] = msg

    # Register success or failure 
    if success:
        result['changed'] = True
    else:
        result['msg'] = f"Failed to perform MinIO operation: {msg}"
        module.fail_json(**result)
        
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()