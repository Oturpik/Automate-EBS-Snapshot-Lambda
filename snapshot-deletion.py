import boto3
import re
import datetime

ec = boto3.client('ec2')
iam = boto3.client('iam')

def lambda_handler(event, context):
    account_ids = []

    try:
        # Get your AWS account ID by using the get_caller_identity method
        account_ids.append(boto3.client('sts').get_caller_identity().get('Account'))
    except Exception as e:
        # If an exception occurs, log it, but don't raise it.
        print(f"Error while fetching the account ID: {str(e)}")

    delete_on = datetime.date.today().strftime('%Y-%m-%d')
    filters = [
        {'Name': 'tag-key', 'Values': ['DeleteOn']},
        {'Name': 'tag-value', 'Values': [delete_on]},
    ]

    try:
        snapshot_response = ec.describe_snapshots(OwnerIds=account_ids, Filters=filters)
    except Exception as e:
        print(f"Error while describing snapshots: {str(e)}")

    for snap in snapshot_response['Snapshots']:
        try:
            print(f"Deleting snapshot {snap['SnapshotId']}")
            ec.delete_snapshot(SnapshotId=snap['SnapshotId'])
        except Exception as e:
            print(f"Error while deleting snapshot {snap['SnapshotId']}: {str(e)}")
