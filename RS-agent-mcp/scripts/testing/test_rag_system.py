#!/usr/bin/env python3
"""
RAG向量数据库系统测试脚本
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.rag.knowledge_base import knowledge_manager, add_document_to_knowledge_base

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_embedding_model():
    """测试嵌入模型加载"""
    print("🔍 测试1: 嵌入模型加载")
    try:
        model = knowledge_manager._get_embedding_model()
        print(f"✅ 嵌入模型加载成功: {model}")
        print(f"   模型维度: {model.get_sentence_embedding_dimension()}")
        
        # 测试编码功能
        test_texts = ["微波遥感", "土壤湿度", "后向散射系数"]
        embeddings = model.encode(test_texts)
        print(f"   测试编码结果: {embeddings.shape}")
        
        return True
    except Exception as e:
        print(f"❌ 嵌入模型加载失败: {str(e)}")
        return False

def test_vector_index():
    """测试向量索引"""
    print("\n🔍 测试2: 向量索引状态")
    try:
        if knowledge_manager.faiss_index is None:
            print("❌ FAISS索引未初始化")
            return False
        
        total_docs = knowledge_manager.faiss_index.ntotal
        print(f"✅ FAISS索引状态正常")
        print(f"   索引中的文档块数量: {total_docs}")
        print(f"   文档映射数量: {len(knowledge_manager.doc_mapping)}")
        
        return True
    except Exception as e:
        print(f"❌ 向量索引测试失败: {str(e)}")
        return False

def test_knowledge_query():
    """测试知识查询"""
    print("\n🔍 测试3: 知识查询功能")
    try:
        # 测试查询
        test_queries = [
            [{"keyword": "微波遥感", "weight": 1.0}],
            [{"keyword": "土壤湿度", "weight": 1.0}],
            [{"keyword": "后向散射系数", "weight": 1.0}],
            [{"keyword": "VHF频段", "weight": 1.0}],
            [{"keyword": "介电常数", "weight": 1.0}]
        ]
        
        for i, keywords in enumerate(test_queries):
            print(f"\n   查询 {i+1}: {keywords[0]['keyword']}")
            result = knowledge_manager.query_knowledge(keywords, top_k=2)
            
            if result and len(result) > 100:
                print(f"   ✅ 查询成功，结果长度: {len(result)} 字符")
                print(f"   📄 内容预览: {result[:200]}...")
            else:
                print(f"   ⚠️ 查询结果为空或过短")
        
        return True
    except Exception as e:
        print(f"❌ 知识查询测试失败: {str(e)}")
        return False

def test_document_addition():
    """测试文档添加功能"""
    print("\n🔍 测试4: 文档添加功能")
    try:
        test_document = """
=== 测试文档：SAR土壤湿度监测 ===

合成孔径雷达（SAR）在土壤湿度监测中的应用：

1. SAR系统优势：
   - 高空间分辨率（1-100m）
   - 全天候工作能力
   - 多极化观测能力
   - 穿透云层能力

2. 土壤湿度反演原理：
   - 基于后向散射机制
   - 利用介电常数差异
   - 考虑地表粗糙度影响
   - 植被效应校正

3. 关键技术参数：
   - 工作频段：L、C、X波段
   - 极化方式：HH、VV、HV、VH
   - 入射角：20-70度
   - 空间分辨率：1-100m

这是一个测试文档，用于验证系统的文档添加和检索功能。
        """
        
        # 记录添加前的文档数量
        before_count = knowledge_manager.faiss_index.ntotal if knowledge_manager.faiss_index else 0
        
        # 添加测试文档
        success = add_document_to_knowledge_base(test_document, "test_sar_document.txt")
        
        if success:
            after_count = knowledge_manager.faiss_index.ntotal if knowledge_manager.faiss_index else 0
            print(f"✅ 文档添加成功")
            print(f"   添加前文档块数量: {before_count}")
            print(f"   添加后文档块数量: {after_count}")
            print(f"   新增文档块数量: {after_count - before_count}")
            
            # 测试新添加文档的查询
            print("\n   测试新添加文档的查询:")
            keywords = [{"keyword": "SAR", "weight": 1.0}]
            result = knowledge_manager.query_knowledge(keywords, top_k=3)
            
            if "SAR" in result or "合成孔径雷达" in result:
                print("   ✅ 新添加文档可以被成功检索")
            else:
                print("   ⚠️ 新添加文档检索结果不包含预期内容")
                
            return True
        else:
            print("❌ 文档添加失败")
            return False
            
    except Exception as e:
        print(f"❌ 文档添加测试失败: {str(e)}")
        return False

def test_knowledge_sources():
    """测试知识源文件"""
    print("\n🔍 测试5: 知识源文件检查")
    try:
        sources_path = Path("file_storage/converted")
        
        if not sources_path.exists():
            print("❌ 知识源目录不存在")
            return False
        
        txt_files = list(sources_path.glob("*.txt"))
        print(f"✅ 知识源目录存在")
        print(f"   找到 {len(txt_files)} 个txt文件:")
        
        for file_path in txt_files:
            try:
                file_size = file_path.stat().st_size
                print(f"   📄 {file_path.name} ({file_size} bytes)")
            except Exception as e:
                print(f"   ❌ 读取文件信息失败 {file_path.name}: {str(e)}")
        
        return True
    except Exception as e:
        print(f"❌ 知识源文件检查失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始RAG向量数据库系统测试\n")
    
    test_results = []
    
    # 运行所有测试
    test_results.append(("嵌入模型加载", test_embedding_model()))
    test_results.append(("向量索引状态", test_vector_index()))
    test_results.append(("知识源文件", test_knowledge_sources()))
    test_results.append(("知识查询功能", test_knowledge_query()))
    test_results.append(("文档添加功能", test_document_addition()))
    
    # 输出测试总结
    print("\n" + "="*50)
    print("📊 测试结果总结")
    print("="*50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！RAG向量数据库系统运行正常")
        return True
    else:
        print("⚠️ 部分测试失败，请检查系统配置")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n用户中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生未预期错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 