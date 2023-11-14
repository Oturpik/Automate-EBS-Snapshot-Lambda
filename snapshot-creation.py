import boto3
import collections
import datetime

ec = boto3.client('ec2')

def lambda_handler(event, context):
    reservations = ec.describe_instances(
        Filters=[
            {'Name': 'tag-key', 'Values': ['backup', 'Backup']},
        ]
    ).get('Reservations', [])

    instances = sum(
        [
            [i for i in r['Instances']]
            for r in reservations
        ], [])

    print(f"Found {len(instances)} instances that need backing up")

    to_tag = collections.defaultdict(list)

    for instance in instances:
        try:
            retention_days = [
                int(t.get('Value')) for t in instance['Tags']
                if t['Key'] == 'Retention'][0]
        except IndexError:
            retention_days = 10

        for dev in instance['BlockDeviceMappings']:
            if dev.get('Ebs', None) is None:
                continue
            vol_id = dev['Ebs']['VolumeId']
            print(f"Found EBS volume {vol_id} on instance {instance['InstanceId']}")

            snap = ec.create_snapshot(
                VolumeId=vol_id,
            )

            to_tag[retention_days].append(snap['SnapshotId'])

            print(f"Retaining snapshot {snap['SnapshotId']} of volume {vol_id} from instance {instance['InstanceId']} for {retention_days} days")

    for retention_days in to_tag.keys():
        delete_date = datetime.date.today() + datetime.timedelta(days=retention_days)
        delete_fmt = delete_date.strftime('%Y-%m-%d')
        print(f"Will delete {len(to_tag[retention_days])} snapshots on {delete_fmt}")
        ec.create_tags(
            Resources=to_tag[retention_days],
            Tags=[
                {'Key': 'DeleteOn', 'Value': delete_fmt},
                {'Key': 'Name', 'Value': "LIVE-BACKUP"}
            ]
        )
