import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Annotated

import boto3
import typer
from botocore.exceptions import ClientError

from .logging import configure_logging

app = typer.Typer()


def _snapshot_ids_from_ami(image) -> Sequence[str]:
    snapshot_ids = []

    for mapping in image.get("BlockDeviceMappings", []):
        ebs = mapping.get("Ebs")
        if ebs and "SnapshotId" in ebs:
            snapshot_ids.append(ebs["SnapshotId"])

    return snapshot_ids


@app.command(name="run")
def run_cleanup(
    region: Annotated[str, typer.Option(help="AWS region")],
    name_prefix: Annotated[str, typer.Option(help="AMI name prefix")],
    min_age_days: Annotated[
        int,
        typer.Option(help="Minimum number of days old to be considered for cleanup"),
    ],
    dry_run: Annotated[bool, typer.Option(help="dry run")] = False,
    verbose: Annotated[bool, typer.Option(help="be noisy")] = False,
):
    configure_logging(verbose)
    logger = logging.getLogger(__name__)

    if min_age_days <= 0:
        raise RuntimeError("--min-age-days must be > 0")

    ec2 = boto3.client("ec2", region_name=region)

    filters = [{"Name": "name", "Values": [f"{name_prefix}*"]}]
    response = ec2.describe_images(Owners=["self"], Filters=filters)

    images = response.get("Images", [])

    cutoff = datetime.now(UTC).timestamp() - (min_age_days * 86400)
    candidates = []
    for candidate in images:
        created = datetime.strptime(candidate["CreationDate"], "%Y-%m-%dT%H:%M:%S.%f%z")
        if created.timestamp() <= cutoff:
            candidates.append(candidate)

    if not candidates:
        logger.info("No images found.")
        return 0

    if dry_run:
        image_details = "".join(
            f"  - {c['ImageId']}: {c['Name']}\n" for c in candidates
        )
        logger.info(f"Found {len(candidates)} images to cleanup: \n{image_details}")
        return 0

    for image in candidates:
        image_id = image["ImageId"]

        snapshot_ids = _snapshot_ids_from_ami(image)

        try:
            ec2.deregister_image(ImageId=image_id)
            logger.info(f"Unregistered {image_id}.")
        except ClientError as e:
            logger.error(f"Failed to unregister {image_id}: {e}")
            return 1

        for snapshot_id in snapshot_ids:
            try:
                ec2.delete_snapshot(SnapshotId=snapshot_id)
                logger.info(f"Deleted snapshot {snapshot_id}.")
            except ClientError as e:
                logger.error(f"Failed to delete {snapshot_id}: {e}")
                return 1

    return 0
