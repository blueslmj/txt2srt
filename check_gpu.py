#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU检查工具 - 快速检测GPU是否可用
"""

import sys

def check_gpu():
    """检查GPU配置"""
    print("=" * 60)
    print("🔍 GPU 检测工具")
    print("=" * 60)
    print()
    
    # 检查PyTorch
    try:
        import torch
        print("✅ PyTorch 已安装")
        print(f"   版本: {torch.__version__}")
    except ImportError:
        print("❌ PyTorch 未安装")
        print("   请先运行: setup.bat")
        return False
    
    print()
    print("-" * 60)
    print("GPU 信息:")
    print("-" * 60)
    
    # 检查CUDA
    cuda_available = torch.cuda.is_available()
    
    if cuda_available:
        print(f"✅ GPU 可用！")
        print(f"   CUDA 版本: {torch.version.cuda}")
        print(f"   GPU 数量: {torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            print(f"\n   GPU {i}:")
            print(f"   - 名称: {torch.cuda.get_device_name(i)}")
            
            # 获取显存信息
            props = torch.cuda.get_device_properties(i)
            total_memory = props.total_memory / (1024**3)  # 转换为GB
            print(f"   - 显存: {total_memory:.1f} GB")
            print(f"   - 计算能力: {props.major}.{props.minor}")
        
        print()
        print("🚀 性能测试:")
        print("-" * 60)
        
        # 详细的性能测试
        try:
            import time
            
            # 测试1: 小矩阵（GPU开销大）
            print("测试 1/3: 小矩阵乘法 (1000x1000)...")
            x_cpu = torch.randn(1000, 1000)
            x_gpu = x_cpu.cuda()
            
            start = time.time()
            for _ in range(50):
                y = torch.matmul(x_cpu, x_cpu)
            cpu_time1 = time.time() - start
            
            torch.cuda.synchronize()
            start = time.time()
            for _ in range(50):
                y = torch.matmul(x_gpu, x_gpu)
            torch.cuda.synchronize()
            gpu_time1 = time.time() - start
            
            speedup1 = cpu_time1 / gpu_time1
            print(f"   CPU: {cpu_time1:.3f}秒 | GPU: {gpu_time1:.3f}秒 | 加速: {speedup1:.1f}x")
            
            # 测试2: 大矩阵（GPU优势明显）
            print("\n测试 2/3: 大矩阵乘法 (3000x3000)...")
            x_cpu = torch.randn(3000, 3000)
            x_gpu = x_cpu.cuda()
            
            start = time.time()
            for _ in range(10):
                y = torch.matmul(x_cpu, x_cpu)
            cpu_time2 = time.time() - start
            
            torch.cuda.synchronize()
            start = time.time()
            for _ in range(10):
                y = torch.matmul(x_gpu, x_gpu)
            torch.cuda.synchronize()
            gpu_time2 = time.time() - start
            
            speedup2 = cpu_time2 / gpu_time2
            print(f"   CPU: {cpu_time2:.3f}秒 | GPU: {gpu_time2:.3f}秒 | 加速: {speedup2:.1f}x")
            
            # 测试3: 卷积操作（模拟Whisper计算）
            print("\n测试 3/3: 卷积计算 (模拟Whisper)...")
            x_cpu = torch.randn(16, 3, 224, 224)
            x_gpu = x_cpu.cuda()
            conv = torch.nn.Conv2d(3, 64, 3, padding=1)
            conv_gpu = conv.cuda()
            
            start = time.time()
            for _ in range(20):
                y = conv(x_cpu)
            cpu_time3 = time.time() - start
            
            torch.cuda.synchronize()
            start = time.time()
            for _ in range(20):
                y = conv_gpu(x_gpu)
            torch.cuda.synchronize()
            gpu_time3 = time.time() - start
            
            speedup3 = cpu_time3 / gpu_time3
            print(f"   CPU: {cpu_time3:.3f}秒 | GPU: {gpu_time3:.3f}秒 | 加速: {speedup3:.1f}x")
            
            # 综合评估
            avg_speedup = (speedup1 + speedup2 + speedup3) / 3
            print()
            print("=" * 60)
            print(f"📊 平均加速比: {avg_speedup:.1f}x")
            print("=" * 60)
            
            if avg_speedup > 10:
                print("✅ 优秀！GPU配置完美，Whisper处理会非常快！")
                print("   预计10分钟音频处理时间: 20-40秒")
            elif avg_speedup > 5:
                print("✅ 良好！GPU工作正常，会有明显加速效果")
                print("   预计10分钟音频处理时间: 40秒-1分钟")
            elif avg_speedup > 2:
                print("⚠️ 一般：GPU可用但加速有限")
                print("   可能原因:")
                print("   1. 集成显卡或较老的GPU")
                print("   2. GPU驱动需要更新")
                print("   3. CUDA版本不匹配")
                print("   预计10分钟音频处理时间: 1-3分钟")
            else:
                print("❌ 差：GPU加速效果不明显")
                print("   可能原因:")
                print("   1. 使用的是集成显卡（Intel/AMD集显）")
                print("   2. GPU驱动严重过期")
                print("   3. PyTorch GPU版本安装不正确")
                print("   建议:")
                print("   - 检查是否有独立NVIDIA显卡")
                print("   - 运行 nvidia-smi 查看GPU状态")
                print("   - 重新安装PyTorch GPU版本")
                print("   预计10分钟音频处理时间: 5-10分钟（接近CPU）")
            
            # 显示GPU详细信息
            print()
            print("💡 GPU详细信息:")
            props = torch.cuda.get_device_properties(0)
            compute_capability = f"{props.major}.{props.minor}"
            print(f"   计算能力: {compute_capability}")
            
            if props.major < 6:
                print("   ⚠️ 较老的GPU架构，建议升级硬件")
            elif props.major < 7:
                print("   ✅ GPU架构可用，性能一般")
            else:
                print("   ✅ 现代GPU架构，性能良好")
                
        except Exception as e:
            print(f"⚠️ 性能测试失败: {e}")
            import traceback
            print("\n详细错误信息:")
            traceback.print_exc()
        
        print()
        print("=" * 60)
        print("✅ 结论: GPU 已正确配置，程序会自动使用GPU加速")
        print("=" * 60)
        return True
        
    else:
        print("❌ GPU 不可用")
        print()
        
        # 检查PyTorch版本
        if "+cu" in torch.__version__:
            print("   PyTorch GPU版本已安装，但GPU不可用")
            print("   可能原因:")
            print("   1. 没有NVIDIA显卡")
            print("   2. NVIDIA驱动未安装")
            print("   3. CUDA版本不匹配")
            print()
            print("   请运行: nvidia-smi")
            print("   查看GPU是否被系统识别")
        else:
            print("   当前是 PyTorch CPU版本")
            print()
            print("   如需GPU加速，请:")
            print("   1. 确认有NVIDIA显卡")
            print("   2. 安装NVIDIA驱动")
            print("   3. 重新安装PyTorch GPU版本")
            print()
            print("   详细步骤请查看: GPU_SETUP.md")
        
        print()
        print("=" * 60)
        print("⚠️ 结论: 将使用CPU处理（速度较慢）")
        print("=" * 60)
        return False


def main():
    """主函数"""
    has_gpu = check_gpu()
    
    print()
    print("📖 相关文档:")
    print("   - GPU设置指南: GPU_SETUP.md")
    print("   - 项目文档: README.md")
    print()
    
    if not has_gpu:
        print("💡 提示: 没有GPU也可以使用，只是速度会慢一些")
        print("   建议使用较小的模型（tiny, base）")
    
    print()


if __name__ == "__main__":
    main()

