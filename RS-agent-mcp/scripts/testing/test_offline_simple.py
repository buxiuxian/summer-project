#!/usr/bin/env python3
import os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2', local_files_only=True)
    embedding = model.encode("测试文本")
    print(f"✅ 离线加载成功，维度: {len(embedding)}")
except Exception as e:
    print(f"❌ 离线加载失败: {e}") 