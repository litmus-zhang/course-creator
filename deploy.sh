#!/bin/bash

adk deploy gke \
    --project trans-engine-441323-b5  \
    --cluster_name deepstack-june-2026 \
    --region us-central1 \
    --with_ui \
    --log_level info \
    .