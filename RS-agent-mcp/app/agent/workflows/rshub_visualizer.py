"""
RSHub可视化组件 - 提取自原始rshub_workflow.py的绘图功能
"""

import io
import logging
import os
from typing import List, Optional, Dict, Any

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端

logger = logging.getLogger(__name__)


class RSHubVisualizer:
    """RSHub可视化器"""
    
    @staticmethod
    async def generate_plots(token: str, project_name: str, tasks: List[Dict],
                           scenario_info: Dict, model_name: str, data_dicts: List[Dict],
                           output_path: Optional[str] = None) -> List[str]:
        """生成结果图表并保存到temp目录"""
        from rshub.load_file import load_file
        
        # 清理并创建temp目录
        await RSHubVisualizer._cleanup_temp_directory()
        
        plot_files = []
        
        try:
            if scenario_info['name'] == 'veg':
                # 植被场景绘图逻辑
                plot_buffer = await RSHubVisualizer._plot_vegetation(token, project_name, tasks, data_dicts)
                if plot_buffer:
                    filename = f"vegetation_tb_{project_name}.png"
                    file_path = await RSHubVisualizer._save_plot_to_temp(plot_buffer, filename)
                    if file_path:
                        plot_files.append(file_path)
                        
            elif scenario_info['name'] == 'snow':
                # 雪地场景绘图逻辑
                plot_buffers = await RSHubVisualizer._plot_snow(token, project_name, tasks, data_dicts, model_name)
                if plot_buffers:
                    for i, plot_buffer in enumerate(plot_buffers):
                        if plot_buffer:
                            # 根据主动/被动模式确定文件名
                            if i == 0:  # 第一个图表（通常是被动模式）
                                filename = f"snow_tb_{project_name}.png"
                            else:  # 第二个图表（主动模式）
                                filename = f"snow_bs_{project_name}.png"
                            
                            file_path = await RSHubVisualizer._save_plot_to_temp(plot_buffer, filename)
                            if file_path:
                                plot_files.append(file_path)
                        
            elif scenario_info['name'] == 'soil':
                # 土壤场景绘图逻辑
                plot_buffer = await RSHubVisualizer._plot_soil(token, project_name, tasks, data_dicts)
                if plot_buffer:
                    filename = f"soil_bs_{project_name}.png"
                    file_path = await RSHubVisualizer._save_plot_to_temp(plot_buffer, filename)
                    if file_path:
                        plot_files.append(file_path)
        
        except Exception as e:
            logger.error(f"生成图表失败: {str(e)}")
        
        return plot_files
    
    @staticmethod
    async def _save_plot_to_temp(plot_buffer: io.BytesIO, filename: str) -> Optional[str]:
        """将图表保存到temp目录"""
        try:
            # 确保temp目录存在
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            # 生成完整文件路径
            file_path = os.path.join(temp_dir, filename)
            
            # 保存图片内容
            plot_buffer.seek(0)
            content = plot_buffer.read()
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"图表已保存到temp目录: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"保存图表到temp目录失败: {str(e)}")
            return None
    
    @staticmethod
    async def _cleanup_temp_directory():
        """清理temp目录中的文件"""
        try:
            temp_dir = "temp"
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.info(f"已清理临时文件: {file_path}")
            else:
                os.makedirs(temp_dir, exist_ok=True)
                logger.info("已创建temp目录")
        except Exception as e:
            logger.error(f"清理temp目录失败: {str(e)}")
    
    @staticmethod
    async def _plot_vegetation(token: str, project_name: str, tasks: List[Dict],
                              data_dicts: List[Dict]) -> Optional[io.BytesIO]:
        """植被场景绘图"""
        try:
            from rshub.load_file import load_file
            import io
            
            # 获取频率（从data字典中提取）
            fGHz = data_dicts[0].get('fGHz', 1.41)
            
            # 控制图片尺寸：宽度小于300像素
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(1, 1, 1)
            
            # 为每个任务加载数据并绘图
            for i, task in enumerate(tasks):
                data = load_file(token, project_name, task['name'], fGHz, 'veg', 'tb')
                data_loaded = data.load_outputs()
                
                TU_all = data_loaded['TU_all']
                theta_obs = data_loaded['theta_obs']
                
                # 绘制V和H极化
                label_prefix = f"Task{i+1}" if len(tasks) > 1 else ""
                ax.plot(theta_obs[0,:], TU_all[0,:], label=f'{label_prefix} V')
                ax.plot(theta_obs[0,:], TU_all[1,:], label=f'{label_prefix} H')
            
            ax.set_xlabel('Observation Angle θ(°)', fontsize=10)
            ax.set_ylabel('Brightness Temperature TB(K)', fontsize=10)
            ax.set_title('Vegetation Brightness Temperature', fontsize=12)
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
            
            # 保存到内存缓冲区，控制图片尺寸：宽度约700像素，高度约560像素
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=70, bbox_inches='tight')
            plt.close()
            
            return buffer
            
        except Exception as e:
            logger.error(f"植被场景绘图失败: {str(e)}")
            return None
    
    @staticmethod
    async def _plot_snow(token: str, project_name: str, tasks: List[Dict],
                        data_dicts: List[Dict], model_name: str) -> Optional[List[io.BytesIO]]:
        """雪地场景绘图"""
        try:
            from rshub.load_file import load_file
            import io
            
            # 安全获取频率和角度，支持嵌套参数结构
            data_dict = data_dicts[0]
            logger.info(f"绘图参数字典键: {list(data_dict.keys())}")
            
            # 获取频率
            fGHz_raw = data_dict.get('fGHz', [17.2])
            if isinstance(fGHz_raw, list):
                fGHz = fGHz_raw[0] if fGHz_raw else 17.2
            else:
                fGHz = fGHz_raw
            
            # 获取角度
            angles = data_dict.get('angle', list(range(0, 70, 5)))
            if not isinstance(angles, list):
                angles = [angles]
            
            logger.info(f"绘图使用参数: fGHz={fGHz}, angles={angles}")
            
            # 分别处理主动和被动模式
            has_active = any(task['output_var'] == 'bs' for task in tasks)
            has_passive = any(task['output_var'] == 'tb' for task in tasks)
            
            plot_buffers = []
            
            if has_passive:
                # 被动模式（亮温）
                TB_v = []
                TB_h = []
                
                passive_task = next(task for task in tasks if task['output_var'] == 'tb')
                logger.info(f"处理被动模式任务: {passive_task['name']}")
                
                for angle in angles:
                    try:
                        logger.info(f"加载数据: angle={angle}, fGHz={fGHz}")
                        data = load_file(token, project_name, passive_task['name'], fGHz, 'snow', 'tb', angle)
                        data_passive = data.load_outputs()
                        
                        # 安全访问数据
                        if data_passive is None:
                            logger.error(f"角度{angle}的数据加载失败，返回None")
                            continue
                        
                        if 'Tb_v0' not in data_passive or 'Tb_h0' not in data_passive:
                            logger.error(f"角度{angle}的数据中缺少Tb_v0或Tb_h0字段: {list(data_passive.keys())}")
                            continue
                        
                        # 安全获取数值
                        tb_v_data = data_passive['Tb_v0']
                        tb_h_data = data_passive['Tb_h0']
                        
                        if tb_v_data is None or tb_h_data is None:
                            logger.error(f"角度{angle}的亮温数据为None")
                            continue
                        
                        # 确保数据是二维数组并有正确的形状
                        if hasattr(tb_v_data, 'shape') and len(tb_v_data.shape) >= 2:
                            TB_v.append(tb_v_data[0,0])
                            TB_h.append(tb_h_data[0,0])
                        else:
                            logger.warning(f"角度{angle}的数据形状异常: tb_v_shape={getattr(tb_v_data, 'shape', 'No shape')}")
                            # 尝试直接使用数值
                            TB_v.append(float(tb_v_data) if tb_v_data is not None else 0)
                            TB_h.append(float(tb_h_data) if tb_h_data is not None else 0)
                            
                    except Exception as e:
                        logger.error(f"处理角度{angle}时出错: {str(e)}")
                        continue
                
                # 检查是否有有效数据
                if not TB_v or not TB_h:
                    logger.error("没有有效的亮温数据用于绘图")
                    return None
                    
                # 确保角度和数据数量匹配
                valid_angles = angles[:len(TB_v)]
                logger.info(f"有效数据点数量: {len(TB_v)}, 角度: {valid_angles}")
                
                # 控制图片尺寸：宽度约700像素，高度约560像素
                fig1 = plt.figure(figsize=(10, 8))
                ax1 = fig1.add_subplot(1, 1, 1)
                ax1.plot(valid_angles, TB_v, 'b-', linewidth=2, label='V')
                ax1.plot(valid_angles, TB_h, 'r-', linewidth=2, label='H')
                ax1.set_xlabel('Observation Angle θ(°)', fontsize=10)
                ax1.set_ylabel('Brightness Temperature TB(K)', fontsize=10)
                ax1.set_title(f'Snow Brightness Temperature ({MODEL_NAMES[model_name]})', fontsize=12)
                ax1.legend(fontsize=8)
                ax1.grid(True, alpha=0.3)
                
                buffer1 = io.BytesIO()
                plt.savefig(buffer1, format='png', dpi=70, bbox_inches='tight')
                plt.close()
                plot_buffers.append(buffer1)
            
            if has_active:
                # 主动模式（后向散射）
                backscatter_vv = []
                backscatter_vh = []
                
                active_task = next(task for task in tasks if task['output_var'] == 'bs')
                logger.info(f"处理主动模式任务: {active_task['name']}")
                
                for angle in angles:
                    try:
                        data = load_file(token, project_name, active_task['name'], fGHz, 'snow', 'bs', angle)
                        data_active = data.load_outputs()
                        
                        # 安全访问数据
                        if data_active is None:
                            logger.error(f"角度{angle}的主动模式数据加载失败")
                            continue
                        
                        if 'vvdb' not in data_active or 'vhdb' not in data_active:
                            logger.error(f"角度{angle}的数据中缺少vvdb或vhdb字段: {list(data_active.keys())}")
                            continue
                        
                        # 安全获取数值
                        vv_data = data_active['vvdb']
                        vh_data = data_active['vhdb']
                        
                        if hasattr(vv_data, 'shape') and len(vv_data.shape) >= 2:
                            backscatter_vv.append(vv_data[0,0])
                            backscatter_vh.append(vh_data[0,0])
                        else:
                            backscatter_vv.append(float(vv_data) if vv_data is not None else 0)
                            backscatter_vh.append(float(vh_data) if vh_data is not None else 0)
                            
                    except Exception as e:
                        logger.error(f"处理主动模式角度{angle}时出错: {str(e)}")
                        continue
                
                # 检查是否有有效数据
                if not backscatter_vv or not backscatter_vh:
                    logger.error("没有有效的后向散射数据用于绘图")
                    return plot_buffers if plot_buffers else None
                    
                # 确保角度和数据数量匹配
                valid_angles = angles[:len(backscatter_vv)]
                
                # 控制图片尺寸：宽度约700像素，高度约560像素
                fig2 = plt.figure(figsize=(10, 8))
                ax2 = fig2.add_subplot(1, 1, 1)
                ax2.plot(valid_angles, backscatter_vh, 'b-', linewidth=2, label='VH')
                ax2.plot(valid_angles, backscatter_vv, 'r-', linewidth=2, label='VV')
                ax2.set_xlabel('Observation Angle θ(°)', fontsize=10)
                ax2.set_ylabel('Backscatter (dB)', fontsize=10)
                ax2.set_title(f'Snow Backscatter ({MODEL_NAMES[model_name]})', fontsize=12)
                ax2.legend(fontsize=8)
                ax2.grid(True, alpha=0.3)
                
                buffer2 = io.BytesIO()
                plt.savefig(buffer2, format='png', dpi=70, bbox_inches='tight')
                plt.close()
                plot_buffers.append(buffer2)
            
            return plot_buffers if plot_buffers else None
            
        except Exception as e:
            logger.error(f"雪地场景绘图失败: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    async def _plot_soil(token: str, project_name: str, tasks: List[Dict],
                        data_dicts: List[Dict]) -> Optional[io.BytesIO]:
        """土壤场景绘图"""
        try:
            from rshub.load_file import load_file
            import io
            
            # 安全获取参数，支持展平结构
            data_dict = data_dicts[0]
            logger.info(f"土壤绘图参数字典键: {list(data_dict.keys())}")
            
            # 获取频率
            fGHz_raw = data_dict.get('fGHz', [1.26])
            if isinstance(fGHz_raw, list):
                fGHz = fGHz_raw[0] if fGHz_raw else 1.26
            else:
                fGHz = fGHz_raw
            
            # 从参数字典中获取角度（支持angle和theta_i_deg）
            angles = data_dict.get('theta_i_deg', data_dict.get('angle', [10, 20, 30, 40, 50, 60]))
            if not isinstance(angles, list):
                angles = [angles]
            
            logger.info(f"从参数字典获取的角度: {angles}")
            
            logger.info(f"土壤绘图使用参数: fGHz={fGHz}, angles={angles}")
            
            # 土壤场景同时计算主动和被动，但我们展示主动结果
            backscatter_results = []
            
            for angle in angles:
                try:
                    logger.info(f"加载土壤数据: angle={angle}, fGHz={fGHz}")
                    
                    # 添加更详细的调试信息
                    logger.info(f"load_file参数: token={token[:10]}..., project={project_name}, task={tasks[0]['name']}, fGHz={fGHz}, scenario='soil', output='bs', angle={angle}")
                    
                    data = load_file(token, project_name, tasks[0]['name'], fGHz, 'soil', 'bs', angle)
                    
                    # 检查data对象本身
                    if data is None:
                        logger.error(f"角度{angle}的load_file返回None")
                        continue
                        
                    data_active = data.load_outputs()
                    
                    # 安全检查数据是否加载成功
                    if data_active is None:
                        logger.error(f"角度{angle}的土壤数据加载失败，返回None")
                        continue
                    
                    logger.info(f"土壤数据键: {list(data_active.keys()) if isinstance(data_active, dict) else type(data_active)}")
                    
                    # 安全获取后向散射结果
                    HH = data_active.get('HH', 0) if isinstance(data_active, dict) else 0
                    VV = data_active.get('VV', 0) if isinstance(data_active, dict) else 0  
                    HV = data_active.get('HV', 0) if isinstance(data_active, dict) else 0
                    VH = data_active.get('VH', 0) if isinstance(data_active, dict) else 0
                    
                    # 确保数值是有效的
                    def safe_float(value, default=0.0):
                        try:
                            if value is None:
                                return default
                            if hasattr(value, 'shape'):  # numpy数组
                                return float(value.flat[0]) if value.size > 0 else default
                            return float(value)
                        except (ValueError, TypeError):
                            return default
                    
                    HH_val = safe_float(HH)
                    VV_val = safe_float(VV)
                    HV_val = safe_float(HV)
                    VH_val = safe_float(VH)
                    
                    logger.info(f"角度{angle}: HH={HH_val}, VV={VV_val}, HV={HV_val}, VH={VH_val}")
                    
                    backscatter_results.append({
                        'angle': angle,
                        'HH': HH_val,
                        'VV': VV_val,
                        'HV': HV_val,
                        'VH': VH_val
                    })
                    
                except Exception as e:
                    logger.error(f"处理土壤角度{angle}时出错: {str(e)}")
                    continue
            
            # 检查是否有有效数据
            if not backscatter_results:
                logger.error("没有有效的土壤后向散射数据用于绘图")
                return None
            
            logger.info(f"有效土壤数据点数量: {len(backscatter_results)}")
            
            # 绘制后向散射图，控制图片尺寸：宽度约700像素，高度约560像素
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(1, 1, 1)
            
            angles_plot = [r['angle'] for r in backscatter_results]
            HH_plot = [r['HH'] for r in backscatter_results]
            VV_plot = [r['VV'] for r in backscatter_results]
            HV_plot = [r['HV'] for r in backscatter_results]
            VH_plot = [r['VH'] for r in backscatter_results]
            
            # 根据数据点数量选择合适的绘图方式
            if len(angles_plot) == 1:
                # 只有一个数据点时，使用散点图标记
                ax.scatter(angles_plot, VV_plot, color='b', s=100, marker='o', label='VV', zorder=5)
                ax.scatter(angles_plot, HH_plot, color='r', s=100, marker='s', label='HH', zorder=5)
                ax.scatter(angles_plot, HV_plot, color='g', s=100, marker='^', label='HV', zorder=5)
                ax.scatter(angles_plot, VH_plot, color='m', s=100, marker='v', label='VH', zorder=5)
                
                # 添加文字标注显示具体数值
                for i, (angle, vv, hh, hv, vh) in enumerate(zip(angles_plot, VV_plot, HH_plot, HV_plot, VH_plot)):
                    ax.text(angle + 1, vv, f'{vv:.1f}', fontsize=8, ha='left')
                    ax.text(angle + 1, hh, f'{hh:.1f}', fontsize=8, ha='left')
                    ax.text(angle + 1, hv, f'{hv:.1f}', fontsize=8, ha='left')
                    ax.text(angle + 1, vh, f'{vh:.1f}', fontsize=8, ha='left')
            else:
                # 多个数据点时，使用线图
                ax.plot(angles_plot, VV_plot, 'b-', linewidth=2, label='VV')
                ax.plot(angles_plot, HH_plot, 'r-', linewidth=2, label='HH')
                ax.plot(angles_plot, HV_plot, 'g--', linewidth=2, label='HV')
                ax.plot(angles_plot, VH_plot, 'm--', linewidth=2, label='VH')
            
            ax.set_xlabel('Incident Angle (°)', fontsize=10)
            ax.set_ylabel('Backscatter (dB)', fontsize=10)
            ax.set_title('Soil Surface Backscatter (AIEM)', fontsize=12)
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
            
            # 保存到内存缓冲区，控制图片尺寸：宽度约700像素，高度约560像素
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=70, bbox_inches='tight')
            plt.close()
            
            logger.info("土壤场景绘图完成")
            return buffer
            
        except Exception as e:
            logger.error(f"土壤场景绘图失败: {str(e)}", exc_info=True)
            return None


# 为了向后兼容，保留模型名称映射
MODEL_NAMES = {
    'qms': 'DMRT-QMS',
    'bic': 'DMRT-BIC',
    'aiem': 'AIEM',
    'rt': 'VPRT'
}