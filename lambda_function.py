
import json
import boto3
import hashlib

from boto3.dynamodb.conditions import Key, Attr

# DynamoDBへの接続
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table("pass_api_dynamo")
# 返り値用の変数
returnValue = {}

# ユーザー検索関数
def search_user(partitionKey):
    queryData = table.query(
        IndexName='attribute-index', KeyConditionExpression = Key("partition").eq(partitionKey) & Key("attribute").eq("user")
    )
    items=queryData['Items']
    if not items:
        return None
    else:
        return items

# パスワード検索関数
def search_password(partitionKey, sortKey):
    queryData = table.query(
        KeyConditionExpression = Key("partition").eq(partitionKey) & Key("sort").eq(sortKey)
    )
    
    items=queryData['Items']
    if not items:
        return None
    else:
        return items

# パスワード一覧の取得関数
def get_passwords(partitionKey):
    sort_pass = "password"
    queryData = table.scan(
        FilterExpression = Key("partition").eq(partitionKey) & Attr("attribute").eq(sort_pass)
    )
    
    items=queryData['Items']
    if not items:
        return None
    else:
        return items
    
    
# ユーザーレコード追加・更新関数
def user_put(partitionKey, sortKey, user_pass):
    putResponse = table.put_item(
        Item={
            'partition': partitionKey,
            'sort': sortKey,
            'user_pass': user_pass,
            'attribute': 'user'
        }
    )
    if putResponse['ResponseMetadata']['HTTPStatusCode'] != 200:
        print(putResponse)
    else:
        print('PUT Successed.')
    return putResponse

# パスワードレコード追加・更新関数
def pass_put(partitionKey, sortKey, password):
    putResponse = table.put_item(
        Item={
            'partition': partitionKey,
            'sort': sortKey,
            'password': password,
            'attribute': "password"
        }
    )
    if putResponse['ResponseMetadata']['HTTPStatusCode'] != 200:
        print(putResponse)
    else:
        print('PUT Successed.')
    return putResponse



# パスワード削除関数
def password_delete(partitionKey, sortKey):
    delResponse = table.delete_item(
        Key={
           'partition': partitionKey,
           'sort': sortKey
       }
    )
    if delResponse['ResponseMetadata']['HTTPStatusCode'] != 200:
        print(delResponse)
    else:
        print('DEL Successed.')
    return delResponse
    

# 実際の処理部分
def lambda_handler(event, context):
    print("Received event: " + json.dumps(event))
    OperationType = event['OperationType']

    # 送信されたデータの、OperationTypeで分岐
    try:
        # フロントから渡された、DynamoDBのパーティションキー、ソートキーを取得
        PartitionKey = event['Keys']['partition']
        SortKey = event['Keys']['sort']

        # ========================
        # ユーザーを取得する場合
        # ========================
        if OperationType == 'QUERY':
            return search_user(PartitionKey)
            
        # ========================
        # ユーザーを登録する場合
        # ========================
        elif OperationType == 'PUTUSER':
            # 入力メールアドレスのユーザーをDynamoDBから取得
            user_source = search_user(PartitionKey)
            # 同じメールアドレスが登録されていなければ、ユーザー登録
            if user_source is None:
                User_pass = hashlib.sha256(event['Keys']['user_pass'].encode('utf-8')).hexdigest()
                return user_put(PartitionKey, PartitionKey, User_pass)
            
        
        # ========================
        # パスワードを登録する場合
        # ========================
        elif OperationType == 'PUTPASS':
            # 入力メールアドレスのユーザーをDynamoDBから取得
            user_source = search_user(PartitionKey)
            # 同じメールアドレスが登録されていなければ、エラーを返す
            if user_source is None:
                returnValue["flag"] = "error"
                return json.dumps(returnValue, ensure_ascii=False)
            # ユーザーが存在する場合
            else:
                # テーブルから取得したパスワード
                user_pass = user_source[0]["user_pass"]
                # フロントから送信されたパスワード
                entered_pass = hashlib.sha256(event['Keys']['user_pass'].encode('utf-8')).hexdigest()
                
                # パスワードが合致する場合
                if user_pass == entered_pass:
                    
                    # 同名サービスが登録されているか確認
                    check_service = search_password(PartitionKey, SortKey)
                    # 同名が未登録 ＝ OK
                    if check_service is None:
                        EncryptPassword = event['Keys']['encrypt_password']
                        pass_put(PartitionKey, SortKey, EncryptPassword)
                        returnValue['flag'] = 'success'
                        returnValue['mail'] = PartitionKey
                        returnValue['pass'] = event['Keys']['user_pass']
                        returnValue['passwords'] = get_passwords(PartitionKey)

                        
                        return json.dumps(returnValue, ensure_ascii=False)

                    # 同名が登録済み ＝ NG
                    else:
                        returnValue['flag'] = 'isset'
                        returnValue['mail'] = PartitionKey
                        returnValue['pass'] = event['Keys']['user_pass']
                        return json.dumps(returnValue, ensure_ascii=False)
                    
                # パスワード合致しない場合
                else:
                    returnValue['flag'] = 'miss'
                    returnValue['mail'] = PartitionKey
                    returnValue['pass'] = event['Keys']['user_pass']
                    returnValue['passwords'] = get_passwords(PartitionKey)
                    return json.dumps(returnValue, ensure_ascii=False)
        
        # ========================
        # パスワードを削除する場合
        # ========================
        elif OperationType == 'DELETE':

            # DynamoDBから取得したユーザー情報
            user_source = search_user(PartitionKey)
            
            # 同名サービスが登録されているか確認
            check_service = search_password(PartitionKey, SortKey)
            # 同名が未登録 ＝ NG
            if check_service is None:
                returnValue['flag'] = 'delete_miss'
                returnValue['mail'] = PartitionKey
                returnValue['pass'] = event['Keys']['user_pass']
                returnValue['passwords'] = get_passwords(PartitionKey)
                return json.dumps(returnValue, ensure_ascii=False)
            # 同名が登録済み ＝ OK
            else:
                # 送信されたパスワードがあってるかチェック
                # DynamoDBから取得したユーザーパスワード
                user_pass = user_source[0]["user_pass"]
                # フロントから送信されたパスワード
                entered_pass = hashlib.sha256(event['Keys']['user_pass'].encode('utf-8')).hexdigest()

                # パスワード合致
                if user_pass == entered_pass:
                    response = password_delete(PartitionKey, SortKey)
                    returnValue['flag'] = 'deleted'
                    returnValue['mail'] = PartitionKey
                    returnValue['pass'] = event['Keys']['user_pass']
                    returnValue['passwords'] = get_passwords(PartitionKey)
                    return json.dumps(returnValue, ensure_ascii=False)
                # パスワード合致しない
                else:
                    returnValue['flag'] = 'deletemiss'
                    returnValue['mail'] = PartitionKey
                    returnValue['pass'] = event['Keys']['user_pass']
                    
                    return json.dumps(returnValue, ensure_ascii=False)
                
        # ========================
        # ログイン時の処理
        # ========================
        elif OperationType == 'LOGIN':
            
            # DynamoDBから取得したユーザー情報
            user_source = search_user(PartitionKey)
            if user_source is None:
                returnValue['flag'] = 'new'
                returnValue['mail'] = PartitionKey
                returnValue['pass'] = event['Keys']['user_pass']
                returnValue['passwords'] = []
                return json.dumps(returnValue, ensure_ascii=False)
            else:
                # DynamoDBから取得したユーザーパスワード
                user_pass = user_source[0]["user_pass"]
                # フロントから送信されたパスワード
                entered_pass = hashlib.sha256(event['Keys']['user_pass'].encode('utf-8')).hexdigest()
                
                # パスワード合致
                if user_pass == entered_pass:
                    returnValue['flag'] = 'registered'
                    returnValue['mail'] = PartitionKey
                    returnValue['pass'] = event['Keys']['user_pass']
                    returnValue['passwords'] = get_passwords(PartitionKey)
                    
                    return json.dumps(returnValue, ensure_ascii=False)
                # パスワード合致しない
                else:
                    returnValue['flag'] = 'miss'
                    returnValue['mail'] = PartitionKey
                    returnValue['pass'] = event['Keys']['user_pass']
                    returnValue['passwords'] = []
                    
                    return json.dumps(returnValue, ensure_ascii=False)


    except Exception as e:
        print("Error Exception.")
        print(e)
