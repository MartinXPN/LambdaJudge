import os
import pickle

from models import SubmissionRequest, SubmissionResult
from services import check_code


def run_code_lambda(event, context):
    print('Event:', type(event), event)
    print('Context:', context)

    if isinstance(event, bytes):
        event = pickle.loads(event)
    request = SubmissionRequest.from_dict(event)
    print('ALl the params:', request)

    # Clear the data so that the sensitive information does not propagate to subprocesses
    encryption_key = os.environb.pop(b'ENCRYPTION_KEY') if 'ENCRYPTION_KEY' in os.environ else None
    print('encryption key:', encryption_key)

    results: SubmissionResult = check_code(**request.__dict__, encryption_key=encryption_key)
    if encryption_key:  # Lambda can be reused => keep the state unchanged
        os.environb[b'ENCRYPTION_KEY'] = encryption_key
    return results.to_json()
