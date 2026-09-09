# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

# MAGIC %%configure
# MAGIC {
# MAGIC   "defaultLakehouse": {
# MAGIC     "name": "HWC_GovernedData",
# MAGIC     "id": "cdc07f07-d187-4e40-9476-63e6d715272b",
# MAGIC     "workspaceId": "e170d021-0223-4e2a-8dfa-c0bc70930bd0"
# MAGIC   }
# MAGIC }

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

entity_id = ""
decision = ""
approver = ""

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "tags": [
# META     "parameters"
# META   ]
# META }

# CELL ********************

import json
import re
import uuid
from datetime import datetime, timezone

from notebookutils import mssparkutils
from pyspark.sql.types import StringType, StructField, StructType, TimestampType


normalized_entity_id = str(entity_id).strip().upper()
normalized_decision = str(decision).strip().upper()
normalized_approver = str(approver).strip()

if not re.fullmatch(r"HWC-\d+", normalized_entity_id):
    raise ValueError("entity_id must match HWC-<number>.")
if normalized_decision not in {"APPROVED", "REJECTED"}:
    raise ValueError("decision must be APPROVED or REJECTED.")
if not normalized_approver:
    raise ValueError("approver is required.")

entity_exists = (
    spark.table("exception_tracking")
    .where(f"entity_id = '{normalized_entity_id}'")
    .limit(1)
    .count()
)
if not entity_exists:
    raise ValueError(f"No exception record found for {normalized_entity_id}.")

schema = StructType(
    [
        StructField("approval_id", StringType(), False),
        StructField("entity_id", StringType(), False),
        StructField("decision", StringType(), False),
        StructField("approver", StringType(), False),
        StructField("decided_at_utc", TimestampType(), False),
        StructField("channel", StringType(), False),
    ]
)
approval_id = str(uuid.uuid4())
decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
approval = spark.createDataFrame(
    [
        (
            approval_id,
            normalized_entity_id,
            normalized_decision,
            normalized_approver,
            decided_at,
            "HWC governed operations UI",
        )
    ],
    schema,
)
approval.write.format("delta").mode("append").saveAsTable("action_approvals")

mssparkutils.notebook.exit(
    json.dumps(
        {
            "approval_id": approval_id,
            "entity_id": normalized_entity_id,
            "decision": normalized_decision,
            "approver": normalized_approver,
            "decided_at_utc": decided_at.isoformat() + "Z",
        }
    )
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }