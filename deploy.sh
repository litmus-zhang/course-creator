#!/bin/bash

adk deploy gke \
    --project deepstack-june-2026 \
    --cluster_name deepstack-june-2026 \
    --region us-central1 \
    --with_ui \
    --log_level info \
    .