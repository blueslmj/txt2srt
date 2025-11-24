#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU诊断工具 - 深度检查GPU配置问题
"""

import sys


def diagnose_gpu():
    """深度诊断GPU配置"""
    print("=" * 70)
    print("🔬 GPU 深度诊断工具")
    print("=" * 70)
    print()
    
    # 1. 检查PyTorch
    print("📦 1/7: 检查 PyTorch 安装...")
    print("-" * 70)
    try:
        import torch
        print(f"✅ PyTorch 版本: {torch.__version__}")
        
        # 检查是否是GPU版本
        if "+cu" in torch.__version__:
            cuda_ver = torch.__version__.split("+cu")[1]
            print(f"✅ GPU版本 (CUDA {cuda_ver})")
        elif "+cpu" in torch.__version__:
            print("❌ 这是CPU版本！")
            print("   需要重新安装GPU版本")
            print("   参考: GPU_SETUP.md")
            return False
        else:
            print("⚠️ 无法确定是CPU还是GPU版本")
    except ImportError:
        print("❌ PyTorch 未安装")
        return False
    
    print()
    
    # 2. 检查CUDA可用性
    print("🎮 2/7: 检查 CUDA 可用性...")
    print("-" * 70)
    cuda_available = torch.cuda.is_available()
    print(f"CUDA 可用: {'✅ 是' if cuda_available else '❌ 否'}")
    
    if not cuda_available:
        print()
        print("❌ CUDA不可用的可能原因:")
        print("   1. 没有NVIDIA独立显卡")
        print("   2. NVIDIA驱动未安装或过期")
        print("   3. CUDA工具包版本不匹配")
        print()
        print("📋 诊断步骤:")
        print("   1. 打开设备管理器，查看是否有NVIDIA显卡")
        print("   2. 运行命令: nvidia-smi")
        print("   3. 如果nvidia-smi无法运行，需要安装/更新驱动")
        return False
    
    print(f"CUDA 版本: {torch.version.cuda}")
    print(f"cuDNN 版本: {torch.backends.cudnn.version()}")
    print()
    
    # 3. 检查GPU硬件
    print("💻 3/7: 检查 GPU 硬件信息...")
    print("-" * 70)
    
    device_count = torch.cuda.device_count()
    print(f"GPU 数量: {device_count}")
    
    for i in range(device_count):
        print(f"\n🎯 GPU {i}:")
        props = torch.cuda.get_device_properties(i)
        
        print(f"   名称: {torch.cuda.get_device_name(i)}")
        print(f"   显存: {props.total_memory / (1024**3):.2f} GB")
        print(f"   计算能力: {props.major}.{props.minor}")
        print(f"   多处理器: {props.multi_processor_count}")
        
        # 评估GPU等级
        if "RTX 40" in torch.cuda.get_device_name(i):
            print("   等级: ⭐⭐⭐⭐⭐ 旗舰级（最强）")
        elif "RTX 30" in torch.cuda.get_device_name(i):
            print("   等级: ⭐⭐⭐⭐ 高端")
        elif "RTX 20" in torch.cuda.get_device_name(i) or "GTX 16" in torch.cuda.get_device_name(i):
            print("   等级: ⭐⭐⭐ 中高端")
        elif "GTX 10" in torch.cuda.get_device_name(i):
            print("   等级: ⭐⭐ 中端（较老）")
        elif "MX" in torch.cuda.get_device_name(i) or "Intel" in torch.cuda.get_device_name(i):
            print("   等级: ⭐ 入门级/集成显卡")
            print("   ⚠️ 性能有限，加速效果可能不明显")
        
        # 检查显存
        if props.total_memory / (1024**3) < 2:
            print("   ⚠️ 显存较小，可能影响处理大模型")
        elif props.total_memory / (1024**3) < 4:
            print("   ✅ 显存充足，适合小模型（tiny, base）")
        else:
            print("   ✅ 显存充足，可运行大模型（medium, large）")
    
    print()
    
    # 4. 检查NVIDIA驱动
    print("🔧 4/7: 检查 NVIDIA 驱动...")
    print("-" * 70)
    
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            driver_version = result.stdout.strip()
            print(f"✅ 驱动版本: {driver_version}")
            
            # 简单的版本检查
            try:
                major_ver = int(driver_version.split('.')[0])
                if major_ver >= 520:
                    print("   ✅ 驱动版本较新，性能良好")
                elif major_ver >= 470:
                    print("   ✅ 驱动版本可用")
                else:
                    print("   ⚠️ 驱动版本较老，建议更新")
            except:
                pass
        else:
            print("⚠️ 无法获取驱动版本")
    except FileNotFoundError:
        print("❌ nvidia-smi 未找到")
        print("   NVIDIA驱动可能未正确安装")
    except Exception as e:
        print(f"⚠️ 检查驱动时出错: {e}")
    
    print()
    
    # 5. 检查显存使用情况
    print("💾 5/7: 检查显存使用情况...")
    print("-" * 70)
    
    for i in range(device_count):
        torch.cuda.set_device(i)
        allocated = torch.cuda.memory_allocated(i) / (1024**3)
        reserved = torch.cuda.memory_reserved(i) / (1024**3)
        total = torch.cuda.get_device_properties(i).total_memory / (1024**3)
        
        print(f"GPU {i}:")
        print(f"   已分配: {allocated:.2f} GB")
        print(f"   已保留: {reserved:.2f} GB")
        print(f"   总计: {total:.2f} GB")
        print(f"   可用: {total - allocated:.2f} GB")
        
        if (total - allocated) < 1:
            print("   ⚠️ 显存不足，可能影响性能")
        else:
            print("   ✅ 显存充足")
    
    print()
    
    # 6. 测试基本GPU操作
    print("🧪 6/7: 测试基本 GPU 操作...")
    print("-" * 70)
    
    try:
        # 测试简单操作
        x = torch.randn(100, 100).cuda()
        y = torch.randn(100, 100).cuda()
        z = torch.matmul(x, y)
        torch.cuda.synchronize()
        print("✅ 基本GPU计算正常")
        
        # 测试数据传输速度
        import time
        
        # CPU -> GPU
        x_cpu = torch.randn(1000, 1000)
        start = time.time()
        for _ in range(100):
            x_gpu = x_cpu.cuda()
            torch.cuda.synchronize()
        transfer_time = time.time() - start
        print(f"✅ 数据传输速度: {transfer_time:.3f}秒 (100次传输)")
        
        if transfer_time > 1.0:
            print("   ⚠️ 数据传输较慢，可能是PCIe带宽限制")
        
    except Exception as e:
        print(f"❌ GPU操作测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 7. 综合建议
    print("💡 7/7: 综合建议")
    print("-" * 70)
    
    # 检查GPU型号
    gpu_name = torch.cuda.get_device_name(0)
    props = torch.cuda.get_device_properties(0)
    
    print("\n🎯 性能评估:")
    
    # 评分系统
    score = 0
    
    # 显存评分
    vram_gb = props.total_memory / (1024**3)
    if vram_gb >= 8:
        score += 30
        print("✅ 显存充足 (+30分)")
    elif vram_gb >= 4:
        score += 20
        print("✅ 显存够用 (+20分)")
    else:
        score += 10
        print("⚠️ 显存较少 (+10分)")
    
    # 计算能力评分
    if props.major >= 8:
        score += 40
        print("✅ 最新架构 (+40分)")
    elif props.major >= 7:
        score += 30
        print("✅ 现代架构 (+30分)")
    elif props.major >= 6:
        score += 20
        print("✅ 可用架构 (+20分)")
    else:
        score += 10
        print("⚠️ 较老架构 (+10分)")
    
    # 型号评分
    if "RTX 40" in gpu_name or "RTX 30" in gpu_name:
        score += 30
        print("✅ 高端GPU (+30分)")
    elif "RTX 20" in gpu_name or "GTX 16" in gpu_name:
        score += 20
        print("✅ 中高端GPU (+20分)")
    elif "GTX 10" in gpu_name:
        score += 15
        print("✅ 中端GPU (+15分)")
    else:
        score += 5
        print("⚠️ 入门级GPU (+5分)")
    
    print()
    print(f"📊 总分: {score}/100")
    print()
    
    if score >= 80:
        print("🌟 优秀配置！")
        print("   预期加速比: 20-50x")
        print("   10分钟音频处理时间: 15-30秒")
        print("   推荐模型: medium, large")
    elif score >= 60:
        print("✅ 良好配置")
        print("   预期加速比: 10-20x")
        print("   10分钟音频处理时间: 30-60秒")
        print("   推荐模型: base, small")
    elif score >= 40:
        print("⚠️ 基本可用")
        print("   预期加速比: 3-10x")
        print("   10分钟音频处理时间: 1-3分钟")
        print("   推荐模型: tiny, base")
    else:
        print("❌ 性能有限")
        print("   预期加速比: <3x")
        print("   10分钟音频处理时间: 3-8分钟")
        print("   推荐: 考虑使用CPU或升级GPU")
    
    print()
    print("=" * 70)
    print("诊断完成！")
    print("=" * 70)
    
    return True


def main():
    """主函数"""
    success = diagnose_gpu()
    
    if not success:
        print()
        print("🔗 参考文档:")
        print("   GPU配置指南: GPU_SETUP.md")
        print("   问题排查: https://pytorch.org/get-started/locally/")
    
    print()


if __name__ == "__main__":
    main()

