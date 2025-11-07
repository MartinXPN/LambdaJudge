
def handler(event, context):
    """
    Bouncer that takes the request and forwards it to the generator lambda
    """
    print('Event:', type(event), event)
    print('Context:', context)

    return {
        'statusCode': 200,
        'body': '{}',
    }
