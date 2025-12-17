#!/usr/bin/env python3
"""测试图片 API"""
import requests

r = requests.get(
    'http://localhost:8000/api/chat/media/image',
    params={
        'account': 'wxid_v4mbduwqtzpt22',
        'md5': '8753fcd3b1f8c4470b53551e13c5fbc1',
        'username': 'wxid_qmzc7q0xfm0j22'
    }
)
print(f'Status: {r.status_code}')
print(f'Content-Type: {r.headers.get("content-type")}')
print(f'Content-Length: {len(r.content)}')
if r.status_code != 200:
    print(f'Response: {r.text[:500]}')
