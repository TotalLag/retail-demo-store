import boto3
import time
from flask import current_app
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')

def get_init_status_table():
    """Get the initialization status table."""
    return dynamodb.Table(current_app.config['DDB_TABLE_INIT_STATUS'])

def update_status(init_id: str, status: str, message: str = None):
    """Update initialization status in DynamoDB."""
    try:
        item = {
            'service_name': 'products',
            'init_id': init_id,
            'status': status,
            'timestamp': int(time.time())
        }
        if message:
            item['message'] = message

        get_init_status_table().put_item(Item=item)
        current_app.logger.info(f"Status updated: {status} ({init_id})")
        return True
    except ClientError as e:
        current_app.logger.error(f"Failed to update status: {str(e)}")
        return False

def get_latest_status():
    """Get the latest initialization status."""
    try:
        response = get_init_status_table().query(
            KeyConditionExpression='service_name = :svc',
            ExpressionAttributeValues={':svc': 'products'},
            ScanIndexForward=False,  # Get most recent first
            Limit=1
        )
        items = response.get('Items', [])
        if items:
            return items[0]
        return {'status': 'UNKNOWN'}
    except ClientError as e:
        current_app.logger.error(f"Failed to get status: {str(e)}")
        return {'status': 'ERROR', 'message': str(e)}

def check_db_connection():
    """Verify DynamoDB connectivity."""
    try:
        # Try to access both products and status tables
        products_table = dynamodb.Table(current_app.config['DDB_TABLE_PRODUCTS'])
        products_table.get_item(Key={'id': 'test'})
        
        status_table = get_init_status_table()
        status_table.get_item(Key={
            'service_name': 'products',
            'init_id': 'test'
        })
        return True
    except ClientError as e:
        current_app.logger.error(f"Database connection check failed: {str(e)}")
        return False
