#!/bin/bash

adk deploy gke \
    --project deepstack-june-2026 \
    --cluster_name course-creator-cluster \
    --region us-east1 \
    --with_ui \
    --log_level info \
    .