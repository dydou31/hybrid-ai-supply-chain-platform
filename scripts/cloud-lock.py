#!/usr/bin/env python3

import argparse
import os
import signal
import subprocess
import time
import uuid

import boto3
from botocore.exceptions import ClientError

TABLE_NAME = "hybrid-ai-cloud-lock"
LOCK_ID = os.environ.get("CLOUD_LOCK_ID", "cloud-operation")
REGION = "eu-west-3"


def acquire_lock(dynamodb, owner, lease_seconds=120):
    now = int(time.time())
    expires_at = now + lease_seconds

    try:
        dynamodb.put_item(
            TableName=TABLE_NAME,
            Item={
                "LockID": {"S": LOCK_ID},
                "Owner": {"S": owner},
                "ExpiresAt": {"N": str(expires_at)},
            },
            ConditionExpression=(
                "attribute_not_exists(LockID) OR ExpiresAt < :now"
            ),
            ExpressionAttributeValues={
                ":now": {"N": str(now)},
            },
        )
        print(f"LOCK ACQUIRED owner={owner}", flush=True)
        return True

    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print("LOCK BUSY", flush=True)
            return False
        raise



def renew_lock(dynamodb, owner, lease_seconds=120):
    now = int(time.time())
    expires_at = now + lease_seconds

    try:
        dynamodb.update_item(
            TableName=TABLE_NAME,
            Key={"LockID": {"S": LOCK_ID}},
            UpdateExpression="SET ExpiresAt = :expires",
            ConditionExpression="#owner = :owner AND ExpiresAt > :now",
            ExpressionAttributeNames={
                "#owner": "Owner",
            },
            ExpressionAttributeValues={
                ":owner": {"S": owner},
                ":now": {"N": str(now)},
                ":expires": {"N": str(expires_at)},
            },
        )
        print(f"LOCK RENEWED owner={owner}", flush=True)
        return True

    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print("LOCK RENEWAL FAILED", flush=True)
            return False
        raise


def release_lock(dynamodb, owner):
    try:
        dynamodb.delete_item(
            TableName=TABLE_NAME,
            Key={"LockID": {"S": LOCK_ID}},
            ConditionExpression="#owner = :owner",
            ExpressionAttributeNames={
                "#owner": "Owner",
            },
            ExpressionAttributeValues={
                ":owner": {"S": owner},
            },
        )
        print(f"LOCK RELEASED owner={owner}", flush=True)
        return True

    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print("LOCK NOT OWNED", flush=True)
            return False
        raise



class CloudLock:
    def __init__(self, dynamodb, lease_seconds=120, interval=30):
        import threading

        self.dynamodb = dynamodb
        self.owner = str(uuid.uuid4())
        self.lease_seconds = lease_seconds
        self.interval = interval
        self.stop_event = threading.Event()
        self.thread = None
        self.acquired = False
        self.lost = False
        self.last_renewal_error = None

    def acquire(self):
        import threading

        if not acquire_lock(
            self.dynamodb, self.owner, self.lease_seconds
        ):
            return False

        self.acquired = True
        self.thread = threading.Thread(
            target=self._renew_loop,
            daemon=True,
        )
        self.thread.start()
        return True

    def _renew_loop(self):
        while not self.stop_event.wait(self.interval):
            try:
                if not renew_lock(
                    self.dynamodb,
                    self.owner,
                    self.lease_seconds,
                ):
                    self.last_renewal_error = "Lock expired or ownership lost"
                    self.lost = True
                    self.stop_event.set()
                    return
            except Exception as exc:
                self.last_renewal_error = str(exc)
                print(f"LOCK RENEWAL ERROR: {exc}", flush=True)
                self.lost = True
                self.stop_event.set()
                return

    def run(self, command):
        if not self.acquired or self.lost:
            raise RuntimeError("Verrou DynamoDB absent ou perdu")

        process = subprocess.Popen(
            command,
            start_new_session=True,
        )

        try:
            while True:
                if self.lost:
                    print("❌ Verrou perdu : arrêt du processus.", flush=True)
                    os.killpg(process.pid, signal.SIGTERM)

                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()

                    raise RuntimeError(
                        f"Verrou DynamoDB perdu : {self.last_renewal_error}"
                    )

                try:
                    returncode = process.wait(timeout=0.5)
                    if self.lost:
                        raise RuntimeError("Verrou perdu pendant l'exécution")
                    if returncode != 0:
                        raise subprocess.CalledProcessError(returncode, command)
                    return returncode

                except subprocess.TimeoutExpired:
                    continue

        except BaseException:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            raise

    def release(self):
        self.stop_event.set()

        if self.thread is not None:
            self.thread.join()

        if self.acquired:
            self.acquired = False
            return release_lock(self.dynamodb, self.owner)

        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["test", "run"])
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    session = boto3.Session(region_name=REGION)
    dynamodb = session.client("dynamodb")

    if args.action == "run":
        command = args.command

        if command and command[0] == "--":
            command = command[1:]

        if not command:
            parser.error("Une commande est obligatoire après run --")

        lock = CloudLock(
            dynamodb,
            interval=int(os.environ.get("CLOUD_LOCK_INTERVAL", "30")),
        )

        if not lock.acquire():
            raise SystemExit("❌ Opération refusée : verrou CLOUD occupé")

        try:
            try:
                lock.run(command)
                print("✅ Commande exécutée sous verrou DynamoDB")
            except subprocess.CalledProcessError as exc:
                raise SystemExit(exc.returncode) from None
        finally:
            if not lock.release():
                print("⚠️ Verrou non libéré : vérifier DynamoDB", flush=True)

        return

    if args.action == "test":
        owner = str(uuid.uuid4())

        if not acquire_lock(dynamodb, owner):
            raise SystemExit(1)

        try:
            print("LOCK TEST OK")
        finally:
            if not release_lock(dynamodb, owner):
                raise SystemExit("ERROR: lock release failed")


if __name__ == "__main__":
    main()
