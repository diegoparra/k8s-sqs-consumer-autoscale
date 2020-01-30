import os
import logging
import boto3
from time import sleep, time
from kubernetes import client, config
from slack_webhook import Slack


import settings


last_scale_up_time = time()
last_scale_down_time = time()

def post_slack(url, message):
    slack = Slack(url=url)
    slack.post(text=message)

def message_count(sqs_queue_url):
    try:
        client = boto3.client('sqs')
        response = client.get_queue_attributes(
                    QueueUrl=sqs_queue_url,
                    AttributeNames=['ApproximateNumberOfMessages']
                )
                
        return(int(response['Attributes']['ApproximateNumberOfMessages']))
    except:
        return "Couldn't get SQS messages from AWS"



def active_pool(last_scale_up):
    global last_scale_up_time
    global last_scale_down_time
    logging.info("Starting pooling")
    print("Starting pooling")
    print(last_scale_up_time)
    print(last_scale_down_time)
    print("\n")

    messages = message_count(settings.SQS_QUEUE_URL)
    if messages >= 2000:
        post_slack(settings.SLACK_URL, "There are more than 2000 messages to this queue")

    now = time()
    if int(messages) >= int(settings.SCALE_UP_MESSAGES):
        if int(now) - int(last_scale_up) > int(settings.SCALE_UP_COOL_DOWN):
            logging.info("Calling scale up")
            print("Calling scale up")
            print("\n")
            print("Last scale up: {}".format(last_scale_up_time))
            print("\n")
            scale_up()
            last_scale_up_time = now
        else:
            logging.debug("Waiting for scale up cooldown")
            print("Waiting for scale up cooldown")
            print("\n") 

    
    if int(messages) <= int(settings.SCALE_DOWN_MESSAGES):
        if int(now) - int(last_scale_down_time) > int(settings.SCALE_DOWN_COOL_DOWN):
            logging.info("Calling scale down")
            print("Calling scale down")
            print("\n")
            print("Last scale down: {}".format(last_scale_down_time))
            print("\n")
        
            scale_down()
            last_scale_down_time = now
        else:
            logging.debug("Waiting for scale down cooldown")
            print("Waiting for scale down cooldown")
            print("\n")
    
    print("Waiting next pooling execution...")

    print("\n")
    logging.info("Waiting next pooling execution...")
    sleep(int(settings.POOL_PERIOD))

def scale_up():
    print("Starting scaling up checkup")
    print("\n")
    max_pods = settings.MAX_PODS
    current_replicas = get_replicas(settings.DEPLOYMENT_NAME, settings.NAMESPACE)
    if current_replicas < int(max_pods):
        replicas = current_replicas + 1
        print("Increasing number of replicas to: {}".format(replicas))
        print("\n")
        deployment_manager(settings.DEPLOYMENT_NAME, replicas, settings.NAMESPACE)
    else:
        logging.debug("Reached out the max number of containers")
        print("Reached out the max number of containers")
        print("\n")


def scale_down():
    print("Starting scaling down checkup")
    print("\n")
    min_pods = settings.MIN_PODS
    current_replicas = get_replicas(settings.DEPLOYMENT_NAME, settings.NAMESPACE)
    if current_replicas > int(min_pods):
        replicas = current_replicas - 1
        print("Decreasing number of replicas to: {}".format(replicas))
        print("\n")
        deployment_manager(settings.DEPLOYMENT_NAME, replicas, settings.NAMESPACE)
    else:
        logging.debug("Reached out the min number of containers")
        print("Reached out the min number of containers")
        print("\n")

def deployment_manager(name, replicas, namespace):
    logging.info("Changing replica size to {}".format(replicas))
    config.load_kube_config()
    k8s_apps_v1 = client.AppsV1Api()
    body = {'spec': {'replicas': replicas}}
    resp = k8s_apps_v1.patch_namespaced_deployment(
        body=body, namespace=namespace, name=name)
    logging.debug("Deployment updated. status='%s'" % str(resp.status))
    print("Deployment updated. status='%s'" % str(resp.status))

def get_replicas(name, namespace):
    config.load_kube_config()
    k8s_apps_v1 = client.AppsV1Api()
    api_response = k8s_apps_v1.read_namespaced_deployment(name, namespace)
    return api_response.status.replicas


def main():
    global last_scale_up_time
    global last_scale_down_time
    
    while True:
        active_pool(last_scale_up = last_scale_up_time)
            
        
if __name__ == '__main__':
    main()