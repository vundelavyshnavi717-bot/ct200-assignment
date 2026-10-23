#!/usr/bin/env bash
set -e
curl -X POST 'http://localhost:8000/documents/ingest?path=data/ct200_manual_v1.pdf'
curl -X POST 'http://localhost:8000/documents/ingest?path=data/ct200_manual_v2.pdf'
curl 'http://localhost:8000/documents/sections'
curl 'http://localhost:8000/search?q=Battery'
# Use IDs returned by /documents/sections to create a selection, then:
# curl -X POST localhost:8000/selections -H 'content-type: application/json' -d '{"name":"safety","node_ids":[1,2]}'
# curl -X POST localhost:8000/generations -H 'content-type: application/json' -d '{"selection_id":1}'
# Re-fetch /generations/{id}; stale=true and reasons expose v1 -> v2 impact.
