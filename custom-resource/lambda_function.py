from crhelper import CfnResource
import json
import boto3

helper = CfnResource()

kinesis_analytics = boto3.client('kinesisanalytics')
cloudfront = boto3.client('cloudfront')

@helper.delete
def no_op(_, __):
    pass

# Start the Kinesis Analytics App
def start_kda_app(event):
    try:
        application_name = event['ResourceProperties']['ApplicationName']
        application_status = kinesis_analytics.describe_application(
            ApplicationName = application_name
        )
        if(application_status['ApplicationDetail']['ApplicationStatus'] == 'READY'):
            print('Application is ready, starting...')
            response = kinesis_analytics.start_application(
                ApplicationName = application_name,
                InputConfigurations = [
                    {
                        'Id': '1.1',
                        'InputStartingPositionConfiguration': {
                            'InputStartingPosition': 'NOW'
                        }
                    }
                ]
            )
        else:
            print('KDA app is not ready, current status is {}'.format(application_status['ApplicationDetail']['ApplicationStatus']))
    except Exception as e:
        print(e)
        helper.init_failure(e)

# Create CloudFront Real-time Logs Configuration
def create_realtime_logs_configuration(event):
    role_arn = event['ResourceProperties']['RoleArn']
    stream_arn = event['ResourceProperties']['StreamArn']
    stack_name = event['ResourceProperties']['StackName']
    sampling_rate = int(event['ResourceProperties']['SamplingRate'])
    fields = []
    data = {}
    try:
        with open('cf_realtime_log_fields_sample.json') as f:
            data = json.load(f)
            print(json.dumps(data))

        for field, field_type in data['cf_realtime_log_fields'].items():
            fields.append(field)

        print('fields: ' + json.dumps(fields))
        response = cloudfront.create_realtime_log_config(
            EndPoints=[
                {
                    'StreamType': 'Kinesis',
                    'KinesisStreamConfig': {
                        'RoleARN': role_arn,
                        'StreamARN': stream_arn
                    }
                }
            ],
            Fields=fields,
            Name=stack_name,
            SamplingRate=sampling_rate
        )
        print(response)
    except Exception as e:
        print(e)
        helper.init_failure(e)

@helper.create
@helper.update
def create(event, context):
    print('event: ' + json.dumps(event))
    if(event['ResourceType'] == 'Custom::StartKinesisAnalytics'):
        print('Custom::StartKinesisAnalytics')
        start_kda_app(event)
    elif(event['ResourceType'] == 'Custom::CloudFrontRealTimeLogsConfig'):
        print('Custom::CloudFrontRealTimeLogsConfig')
        create_realtime_logs_configuration(event)
    else:
        pass

def lambda_handler(event, context):
    helper(event, context)